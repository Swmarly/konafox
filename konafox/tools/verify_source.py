# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import io
import re
import struct
import sys
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python/mozbuild"))
from mozbuild.preprocessor import Preprocessor


def preprocess(path, defines, marker="#"):
    output = io.StringIO()
    processor = Preprocessor(defines=defines, marker=marker)
    processor.out = output
    processor.do_filter("substitution")
    processor.do_include(str(path))
    return output.getvalue()


def main():
    for brand in ("KonaFox", "Waterfox"):
        metadata = preprocess(
            ROOT / "browser/app/module.ver",
            {
                "MOZ_APP_DISPLAYNAME": brand,
                "MOZ_APP_VERSION": "153.1.0",
                "MOZ_APP_WINVERSION": "153,1,0,0",
            },
            "%",
        )
        assert f"WIN32_MODULE_PRODUCTNAME={brand}" in metadata
        expected = (
            "KonaFox Private Project" if brand == "KonaFox" else "BrowserWorks Ltd"
        )
        assert f"WIN32_MODULE_COMPANYNAME={expected}" in metadata
        if brand == "KonaFox":
            assert "Waterfox is a Trademark" not in metadata
        resource = preprocess(
            ROOT / "browser/app/splash.rc",
            {
                "MOZ_APP_DISPLAYNAME": brand,
            },
            "%",
        )
        assert ("1 RT_MANIFEST KONAFOX_MANIFEST" in resource) == (brand == "KonaFox")

    for manifest in (ROOT / "konafox/jar.mn", ROOT / "konafox/branding/content/jar.mn"):
        for line in manifest.read_text().splitlines():
            match = re.match(r"\s*\*?\s*(content/\S+)(?:\s+\(([^)]+)\))?\s*$", line)
            if not match:
                continue
            destination, source = match.groups()
            source = source or Path(destination).name
            assert list(manifest.parent.glob(source)), (
                f"Missing resource: {manifest}: {source}"
            )

    about = preprocess(
        ROOT / "konafox/content/aboutKonaFox.html",
        {
            "KONAFOX_VERSION": "0.1.0",
            "KONAFOX_WATERFOX_VERSION": "153.1.0esr",
            "KONAFOX_GECKO_VERSION": "153.1.0",
            "KONAFOX_TARGET": "x86_64-pc-windows-msvc",
        },
    )
    assert "@KONAFOX_" not in about
    assert "<script" not in about
    ftl = (ROOT / "konafox/branding/locales/en-US/konafox.ftl").read_text()
    for identifier in re.findall(r'data-l10n-id="([^"]+)"', about):
        assert re.search(rf"^{re.escape(identifier)} =", ftl, re.M), identifier

    for file in (ROOT / "konafox").rglob("*.svg"):
        ElementTree.parse(file)
    package_manifest = (ROOT / "browser/installer/package-manifest.in").read_text()
    for file in (ROOT / "konafox/branding/pref").glob("*.js"):
        assert f"@RESPATH@/browser/@PREF_DIR@/{file.name}" in package_manifest, (
            f"Branding preference file is missing from the package manifest: {file.name}"
        )
    original = (ROOT / "browser/app/waterfox.exe.manifest").read_text()
    manifest = (ROOT / "konafox/branding/konafox.exe.manifest").read_text()
    assert manifest == original.replace('name="Waterfox"', 'name="KonaFox"').replace(
        "<description>Waterfox</description>", "<description>KonaFox</description>"
    ), "Executable manifest must preserve upstream privileges and mitigations"

    for file in (ROOT / "konafox/branding").glob("*.ico"):
        data = file.read_bytes()
        reserved, kind, count = struct.unpack_from("<HHH", data)
        assert (reserved, kind, count) == (0, 1, 7), file
        sizes = set()
        for index in range(count):
            width, height, _, _, planes, bits, length, offset = struct.unpack_from(
                "<BBBBHHII", data, 6 + 16 * index
            )
            width, height = width or 256, height or 256
            assert (planes, bits) == (1, 32)
            assert offset + length <= len(data)
            assert data[offset : offset + 8] == b"\x89PNG\r\n\x1a\n"
            assert struct.unpack_from(">II", data, offset + 16) == (width, height)
            sizes.add(width)
        assert sizes == {16, 24, 32, 48, 64, 128, 256}, file
    for name, dimensions in (
        ("wizHeader.bmp", (150, 57)),
        ("wizHeaderRTL.bmp", (150, 57)),
        ("wizWatermark.bmp", (164, 314)),
    ):
        data = (ROOT / "konafox/branding" / name).read_bytes()
        assert data[:2] == b"BM"
        assert struct.unpack_from("<ii", data, 18) == dimensions
        assert struct.unpack_from("<H", data, 28)[0] == 24

    for file in (ROOT / "konafox").rglob("moz.build"):
        compile(file.read_text(), str(file), "exec")
    print(
        "PASS: branding preprocessing, JAR assets, localization references, manifests, ICO frames, installer BMPs, moz.build syntax"
    )


if __name__ == "__main__":
    main()
