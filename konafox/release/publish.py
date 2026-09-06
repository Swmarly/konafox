#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from release import REPOSITORY, require, sha512, version_tuple, write_metadata

FEED_TAG = "konafox-updates"


def gh(*arguments, missing_ok=False):
    result = subprocess.run(
        ["gh", *arguments], text=True, capture_output=True, check=False
    )
    if result.returncode:
        if missing_ok and "HTTP 404" in result.stderr:
            return None
        raise RuntimeError(result.stderr)
    return result.stdout


def get_release(tag):
    result = gh("api", f"repos/{REPOSITORY}/releases/tags/{tag}", missing_ok=True)
    if result:
        return json.loads(result)
    pages = json.loads(
        gh("api", "--paginate", "--slurp", f"repos/{REPOSITORY}/releases?per_page=100")
    )
    return next(
        (item for page in pages for item in page if item["tag_name"] == tag), None
    )


def read_metadata(tag):
    with tempfile.TemporaryDirectory() as temporary:
        gh(
            "release",
            "download",
            tag,
            "--repo",
            REPOSITORY,
            "--pattern",
            "release.json",
            "--dir",
            temporary,
        )
        return json.loads((Path(temporary) / "release.json").read_text())


def check_advancement(previous, current):
    require(
        previous["certificateSHA256"] == current["certificateSHA256"],
        "Signing certificate changed; existing clients cannot trust this update",
    )
    require(
        version_tuple(current["appVersion"]) >= version_tuple(previous["appVersion"]),
        "Refusing an application version downgrade",
    )
    require(
        current["buildID"] >= previous["buildID"],
        "Refusing to move the update feed backwards",
    )
    if current["buildID"] == previous["buildID"]:
        require(
            previous == current,
            "A build ID cannot be reused for different release contents",
        )


def publish(directory):
    require(
        os.environ.get("GITHUB_REPOSITORY") == REPOSITORY,
        "This workflow is configured only for Swmarly/konafox",
    )
    original = json.loads((directory / "release.json").read_text())
    require(
        original["commit"] == os.environ["GITHUB_SHA"],
        "Artifacts came from a different source revision",
    )
    info = {
        key: value
        for key, value in original.items()
        if key not in ("assets", "certificateSHA256")
    }
    write_metadata(directory, info)
    require(
        info == original,
        "Artifact hashes or signing certificate changed after packaging",
    )
    feed = get_release(FEED_TAG)
    if feed:
        require(
            not feed.get("immutable", False),
            "The update-feed release must allow asset replacement",
        )
        if any(asset["name"] == "release.json" for asset in feed["assets"]):
            check_advancement(read_metadata(FEED_TAG), info)
    tag = info["tag"]
    release = get_release(tag)
    if release and not release["draft"]:
        require(
            read_metadata(tag) == info, "Published release differs from these artifacts"
        )
    else:
        if not release:
            notes = (
                "Windows x64. Download the .exe installer or extract the .zip into a writable folder. "
                "Release installations check for signed KonaFox updates while the browser is running; restart when prompted.\n\n"
                f"Source: {info['commit']}\nBuild: {info['buildID']}\n\n"
                "The installer is not Authenticode-signed. The .complete.mar is the signed automatic-update payload. "
                "SHA512SUMS lists the download checksums."
            )
            gh(
                "release",
                "create",
                tag,
                "--repo",
                REPOSITORY,
                "--target",
                info["commit"],
                "--draft",
                "--title",
                f"KonaFox {info['displayVersion']}",
                "--notes",
                notes,
            )
        files = [directory / name for name in info["assets"]] + [
            directory / name for name in ("update.xml", "release.json", "SHA512SUMS")
        ]
        gh(
            "release",
            "upload",
            tag,
            *map(str, files),
            "--repo",
            REPOSITORY,
            "--clobber",
        )
        uploaded = get_release(tag)
        require(
            uploaded is not None,
            "Uploaded release could not be found; rerun this publish job",
        )
        sizes = {asset["name"]: asset["size"] for asset in uploaded["assets"]}
        require(
            all(sizes.get(path.name) == path.stat().st_size for path in files),
            "Release asset upload is incomplete",
        )
        gh("release", "edit", tag, "--repo", REPOSITORY, "--draft=false", "--latest")
    if not feed:
        gh(
            "release",
            "create",
            FEED_TAG,
            "--repo",
            REPOSITORY,
            "--target",
            info["commit"],
            "--prerelease",
            "--latest=false",
            "--title",
            "KonaFox automatic update feed",
            "--notes",
            "Machine-readable stable update feed. Download installers from the numbered KonaFox releases.",
        )
    gh(
        "release",
        "upload",
        FEED_TAG,
        str(directory / "release.json"),
        str(directory / "update.xml"),
        "--repo",
        REPOSITORY,
        "--clobber",
    )
    with tempfile.TemporaryDirectory() as temporary:
        gh(
            "release",
            "download",
            FEED_TAG,
            "--repo",
            REPOSITORY,
            "--pattern",
            "update.xml",
            "--dir",
            temporary,
        )
        require(
            sha512(Path(temporary) / "update.xml") == sha512(directory / "update.xml"),
            "Published feed verification failed; rerun this publish job",
        )
    url = f"https://github.com/{REPOSITORY}/releases/tag/{tag}"
    print(url)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write(
                f"Published [KonaFox {info['displayVersion']}]({url}) and advanced the automatic update feed.\n"
            )


if __name__ == "__main__":
    publish(Path(sys.argv[1]))
