#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import configparser
import hashlib
import json
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from mardor.reader import MarReader
from mardor.signing import sign_hash
from mardor.writer import add_signature_block

REPOSITORY = "Swmarly/konafox"
CHANNEL = "konafox-release"
MAX_MAR_SIZE = 524288000
CERTIFICATE = Path(__file__).with_name("update-cert.der")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def public_key(certificate=CERTIFICATE):
    key = x509.load_der_x509_certificate(certificate.read_bytes()).public_key()
    require(
        isinstance(key, rsa.RSAPublicKey) and key.key_size == 4096,
        "Expected RSA-4096 certificate",
    )
    return key.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )


def signing_key(certificate=CERTIFICATE):
    data = os.environ.get("KONAFOX_MAR_PRIVATE_KEY", "").encode()
    require(data, "Set the KONAFOX_MAR_PRIVATE_KEY repository secret before releasing")
    key = serialization.load_pem_private_key(data, password=None)
    require(
        isinstance(key, rsa.RSAPrivateKey) and key.key_size == 4096,
        "Expected RSA-4096 signing key",
    )
    actual = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    require(
        actual == public_key(certificate),
        "Signing key does not match the certificate embedded in KonaFox",
    )
    return data


def version_tuple(version):
    require(
        re.fullmatch(r"\d+(?:\.\d+){1,3}(?:esr)?", version),
        "Only stable source versions can use this release channel",
    )
    numbers = tuple(int(part) for part in version.removesuffix("esr").split("."))
    return numbers + (0,) * (4 - len(numbers))


def describe(install, build_id, commit):
    for name in (
        "konafox.exe",
        "updater.exe",
        "precomplete",
        "application.ini",
        "update-settings.ini",
    ):
        require((install / name).is_file(), f"Incomplete package: missing {name}")
    config = configparser.ConfigParser()
    config.read(install / "application.ini", encoding="utf-8")
    app = config["App"]
    require(app["Name"] == "KonaFox", "Refusing to publish a non-KonaFox package")
    require(
        re.fullmatch(r"\d{14}", build_id) and app["BuildID"] == build_id,
        "Package build ID differs from this workflow run",
    )
    require(re.fullmatch(r"[0-9a-f]{40}", commit), "Invalid source revision")
    version_tuple(app["Version"])
    config.read(install / "update-settings.ini", encoding="utf-8")
    require(
        config["Settings"]["ACCEPTED_MAR_CHANNEL_IDS"] == CHANNEL,
        "Wrong MAR channel in package",
    )
    channel_prefs = (install / "defaults/pref/channel-prefs.js").read_text(
        encoding="utf-8"
    )
    require(f'"{CHANNEL}"' in channel_prefs, "Wrong browser update channel")
    return {
        "appVersion": app["Version"],
        "displayVersion": f"{app['Version']} ({build_id})",
        "buildID": build_id,
        "commit": commit,
        "channel": CHANNEL,
        "repository": REPOSITORY,
        "tag": f"konafox-{app['Version']}-{build_id}",
    }


def verify_mar(path, version, certificate=CERTIFICATE):
    require(
        0 < path.stat().st_size <= MAX_MAR_SIZE,
        "MAR exceeds the native updater's 500 MB limit",
    )
    with path.open("rb") as stream, MarReader(stream) as archive:
        require(not archive.get_errors(), "Malformed MAR archive")
        require(
            archive.productinfo == (version, CHANNEL),
            "MAR product version or channel mismatch",
        )
        require(
            archive.signature_type == "sha384"
            and archive.mardata.signatures.count == 1,
            "Expected one SHA-384 signature",
        )
        require(
            archive.verify(public_key(certificate)), "MAR signature verification failed"
        )


def sign_mar(unsigned, output, version, certificate=CERTIFICATE):
    key = signing_key(certificate)
    require(unsigned.resolve() != output.resolve(), "Input and output MAR must differ")
    require(unsigned.stat().st_size <= MAX_MAR_SIZE - 520, "Unsigned MAR is too large")
    with unsigned.open("rb") as source, tempfile.TemporaryFile("w+b") as temporary:
        add_signature_block(source, temporary, "sha384")
        temporary.seek(0)
        with MarReader(temporary) as archive:
            require(
                archive.productinfo == (version, CHANNEL),
                "Unsigned MAR metadata mismatch",
            )
            digest = archive.calculate_hashes()[0][1]
        signature = sign_hash(key, digest, "sha384")
    with unsigned.open("rb") as source, output.open("w+b") as target:
        add_signature_block(source, target, "sha384", signature)
    verify_mar(output, version, certificate)


def sha512(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha512").hexdigest()


def write_metadata(directory, info):
    prefix = f"KonaFox-{info['appVersion']}-{info['buildID']}-win64"
    assets = [
        directory / f"{prefix}{suffix}" for suffix in (".exe", ".zip", ".complete.mar")
    ]
    require(
        all(path.is_file() and path.stat().st_size for path in assets),
        "Missing or empty release asset",
    )
    mar = assets[-1]
    verify_mar(mar, info["appVersion"])
    info["assets"] = {
        path.name: {"size": path.stat().st_size, "sha512": sha512(path)}
        for path in assets
    }
    info["certificateSHA256"] = hashlib.sha256(CERTIFICATE.read_bytes()).hexdigest()
    release_url = f"https://github.com/{REPOSITORY}/releases/tag/{info['tag']}"
    updates = ET.Element("updates")
    update = ET.SubElement(
        updates,
        "update",
        {
            "type": "minor",
            "name": f"KonaFox {info['displayVersion']}",
            "displayVersion": info["displayVersion"],
            "appVersion": info["appVersion"],
            "buildID": info["buildID"],
            "detailsURL": release_url,
        },
    )
    ET.SubElement(
        update,
        "patch",
        {
            "type": "complete",
            "URL": f"https://github.com/{REPOSITORY}/releases/download/{info['tag']}/{mar.name}",
            "hashFunction": "SHA512",
            "hashValue": info["assets"][mar.name]["sha512"],
            "size": str(mar.stat().st_size),
        },
    )
    ET.indent(updates)
    ET.ElementTree(updates).write(
        directory / "update.xml", encoding="utf-8", xml_declaration=True
    )
    (directory / "release.json").write_text(
        json.dumps(info, indent=2) + "\n", encoding="utf-8"
    )
    sums = assets + [directory / "update.xml", directory / "release.json"]
    (directory / "SHA512SUMS").write_text(
        "".join(f"{sha512(path)}  {path.name}\n" for path in sums), encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("check-key", "describe", "sign", "metadata")
    )
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    if args.command == "check-key":
        signing_key()
        print("Signing key matches the embedded certificate")
    elif args.command == "describe":
        install, build_id, commit = args.paths
        print(json.dumps(describe(Path(install), build_id, commit)))
    elif args.command == "sign":
        unsigned, output, version = args.paths
        sign_mar(Path(unsigned), Path(output), version)
    elif args.command == "metadata":
        directory, info = args.paths
        write_metadata(
            Path(directory), json.loads(Path(info).read_text(encoding="utf-8-sig"))
        )


if __name__ == "__main__":
    main()
