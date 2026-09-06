#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def main():
    root = Path(__file__).resolve().parents[2]
    public = root / "konafox/release/update-cert.der"
    private = root / "artifacts/konafox-signing/update-key.pem"
    if public.exists() or private.exists():
        raise SystemExit("A signing identity already exists; refusing to replace it.")
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "KonaFox MAR Signing")])
    now = datetime.datetime.now(datetime.timezone.utc)
    certificate = (
        x509
        .CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=365 * 25))
        .sign(key, hashes.SHA384())
    )
    private.parent.mkdir(parents=True, exist_ok=True)
    with private.open("xb") as stream:
        stream.write(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
    with public.open("xb") as stream:
        stream.write(certificate.public_bytes(serialization.Encoding.DER))
    print(f"Public certificate: {public}")
    print(f"Private key (keep private and back up): {private}")


if __name__ == "__main__":
    main()
