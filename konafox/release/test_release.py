# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import release
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from mardor.writer import MarWriter
from publish import check_advancement


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "Ephemeral release test")
        ])
        now = datetime.datetime.now(datetime.timezone.utc)
        cls.certificate = (
            x509
            .CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(cls.key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=1))
            .sign(cls.key, hashes.SHA384())
        ).public_bytes(serialization.Encoding.DER)
        cls.pem = cls.key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cert = self.root / "cert.der"
        self.cert.write_bytes(self.certificate)
        self.unsigned = self.root / "unsigned.mar"
        self.signed = self.root / "signed.mar"
        with self.unsigned.open("w+b") as stream, MarWriter(
            stream, productversion="153.1.0", channel=release.CHANNEL
        ) as archive:
            archive.add_stream(
                iter([b'type "complete"\r\n']), "updatev3.manifest", "xz", 0o644
            )
            archive.add_stream(
                iter([b"example browser data"]), "application.ini", "xz", 0o644
            )

    def sign(self):
        with patch.dict(os.environ, KONAFOX_MAR_PRIVATE_KEY=self.pem):
            release.sign_mar(self.unsigned, self.signed, "153.1.0", self.cert)

    def test_signing_and_tamper_rejection(self):
        self.sign()
        release.verify_mar(self.signed, "153.1.0", self.cert)
        data = bytearray(self.signed.read_bytes())
        data[-30] ^= 1
        self.signed.write_bytes(data)
        with self.assertRaises((ValueError, OSError)):
            release.verify_mar(self.signed, "153.1.0", self.cert)

    def test_wrong_key_and_version_rejected(self):
        with patch.dict(os.environ, KONAFOX_MAR_PRIVATE_KEY=self.pem):
            with self.assertRaisesRegex(ValueError, "does not match"):
                release.signing_key()
            with self.assertRaisesRegex(ValueError, "metadata mismatch"):
                release.sign_mar(self.unsigned, self.signed, "153.2.0", self.cert)
        with patch.dict(os.environ, KONAFOX_MAR_PRIVATE_KEY=""):
            with self.assertRaisesRegex(ValueError, "repository secret"):
                release.signing_key(self.cert)

    def test_unsigned_mar_rejected(self):
        with self.assertRaisesRegex(ValueError, "signature"):
            release.verify_mar(self.unsigned, "153.1.0", self.cert)

    def test_feed_monotonicity_and_retry(self):
        old = {
            "certificateSHA256": "fixed",
            "appVersion": "153.1.0",
            "buildID": "20260905120000",
            "assets": {"a": "hash"},
        }
        check_advancement(old, old.copy())
        check_advancement(old, {**old, "buildID": "20260905120100"})
        for changes in (
            {"buildID": "20260905110000"},
            {"appVersion": "152.9.0"},
            {"certificateSHA256": "other"},
            {"assets": {"a": "different"}},
        ):
            with self.assertRaises(ValueError):
                check_advancement(old, {**old, **changes})

    def test_xml_matches_signed_asset(self):
        self.sign()
        info = {
            "appVersion": "153.1.0",
            "displayVersion": "153.1.0 (20260905120000)",
            "buildID": "20260905120000",
            "tag": "konafox-153.1.0-20260905120000",
        }
        prefix = "KonaFox-153.1.0-20260905120000-win64"
        mar = self.root / f"{prefix}.complete.mar"
        mar.write_bytes(self.signed.read_bytes())
        for suffix in (".exe", ".zip"):
            (self.root / f"{prefix}{suffix}").write_bytes(b"test fixture")
        native_verify = release.verify_mar
        with patch.object(release, "CERTIFICATE", self.cert), patch.object(
            release,
            "verify_mar",
            side_effect=lambda path, version: native_verify(path, version, self.cert),
        ):
            release.write_metadata(self.root, info)
        update = ET.parse(self.root / "update.xml").getroot()[0]
        self.assertEqual(update.attrib["buildID"], info["buildID"])
        self.assertEqual(update[0].attrib["hashValue"], release.sha512(mar))
        self.assertEqual(int(update[0].attrib["size"]), mar.stat().st_size)
        self.assertIn(f"/releases/download/{info['tag']}/", update[0].attrib["URL"])
        self.assertEqual(json.loads((self.root / "release.json").read_text()), info)


if __name__ == "__main__":
    unittest.main()
