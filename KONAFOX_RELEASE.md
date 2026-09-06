# Building and publishing KonaFox releases

Use **Actions → KonaFox Release → Run workflow** on the repository's default
branch (`current`). Each successful run publishes a Windows x64 offline installer,
ZIP, signed complete MAR, `SHA512SUMS`, and build metadata. The release name includes
the source version and a UTC build ID, so rebuilding the same source version still
produces a distinct update. The workflow runs only when manually dispatched on
the default branch; it does not execute pull-request code on your runner.

## One-time setup

The signing secret is already configured in `Swmarly/konafox`. Step 3 below
documents how to restore it if needed. A Windows runner still needs to be connected.

1. Push the KonaFox changes, including `.github/workflows/konafox-release.yml`,
   onto `current`. GitHub only lists manual workflows present on the default
   branch. The upstream **Build** workflow still builds Waterfox; use **KonaFox
   Release** for this product.
2. Set up a Windows x64 GitHub Actions runner with the custom label `konafox` at
   [repository runner settings](https://github.com/Swmarly/konafox/settings/actions/runners/new).
   Use a dedicated checkout/work directory, separate from this working copy.
   Run it as your normal Windows account. Install PowerShell 7, Git with long-path
   support, MozillaBuild 4.2.1, Rustup, and Waterfox's Clang 22/WASI tools as
   described in `KONAFOX_BUILD.md`. Provision at least 32 GB RAM and 150 GB free
   disk space; the script requires 80 GB still free after checkout. Leave the
   machine online for builds. The workflow installs Rust 1.97.1 and runs Mach
   bootstrap without system changes to obtain the remaining build dependencies.
3. Add the repository Actions secret `KONAFOX_MAR_PRIVATE_KEY`, containing the
   full PEM private key from
   `I:\GitHub-Repos\konafox\artifacts\konafox-signing\update-key.pem` in this
   prepared checkout. Use [Actions secret settings](https://github.com/Swmarly/konafox/settings/secrets/actions)
   or an authenticated GitHub CLI:

   ```powershell
   Get-Content -Raw -LiteralPath 'I:\GitHub-Repos\konafox\artifacts\konafox-signing\update-key.pem' |
     gh secret set KONAFOX_MAR_PRIVATE_KEY --repo Swmarly/konafox
   ```

Only the public certificate, `konafox/release/update-cert.der`, belongs in Git.
Back up the private key privately: losing it prevents updating existing clients.
Do not regenerate it for each build. `keygen.py` created this identity once and
refuses to overwrite an existing identity. A fresh clone uses the same public
certificate and existing GitHub secret; it does not need to generate a key.

The previously prepared local Rust and Mach dependencies live under this
checkout's ignored `artifacts/`. To reuse them from a dedicated runner account
session, set these before launching the runner:

```powershell
$env:CARGO_HOME = 'I:\GitHub-Repos\konafox\artifacts\cargo'
$env:RUSTUP_HOME = 'I:\GitHub-Repos\konafox\artifacts\rustup'
$env:MOZBUILD_STATE_PATH = 'I:\GitHub-Repos\konafox\artifacts\mozbuild-state'
$env:PATH = "$env:CARGO_HOME\bin;$env:PATH"
```

Alternatively, provision a larger GitHub-hosted Windows runner with the same
tools and set the repository variable `KONAFOX_WINDOWS_RUNNER` to its label as a
JSON array, for example `["your-windows-runner-label"]`. A standard hosted runner
does not guarantee the disk space needed for this browser's source build.

## How client updates work

Release builds use `konafox/build/mozconfig.release.windows`, enable the native
updater, require MAR signature verification, embed KonaFox's public certificate,
and accept only the `konafox-release` MAR channel. Development builds retain
their disabled updater and `konafox-private` channel.

The native updater checks
`https://github.com/Swmarly/konafox/releases/download/konafox-updates/update.xml`.
The workflow publishes all files in a numbered release before changing that
feed to point at the new signed MAR. It rejects an older application version,
an older build ID, a changed signing identity, or different contents under the
same build ID. GitHub asset replacement can briefly make the feed unavailable;
the browser can retry its check. Keep the special `konafox-updates` prerelease
and its assets editable; do not enable immutable releases for this feed.

While the browser runs, normal automatic checks download available updates;
users restart to apply them. **Help → About KonaFox** also checks for updates.
Browser update settings and enterprise policies remain respected. The Windows
maintenance service and background update agent are disabled, so there are no
checks while the browser is closed, and a protected installation directory can
require a Windows elevation prompt. A ZIP extracted to a writable user folder
avoids that installation-directory requirement.

The MAR uses RSA-4096/SHA-384 signatures, and the XML also carries the archive's
SHA-512 checksum. This follows the native [Mozilla MAR format](https://firefox-source-docs.mozilla.org/toolkit/mozapps/update/docs/MarFiles.html)
using Mozilla Release Engineering's [MAR tooling](https://github.com/mozilla-releng/build-mar).
The workflow verifies the signature with both the Python MAR library and the
built Windows `signmar.exe` before publication. Installer Authenticode signing
is separate and is not configured; Windows may show an unknown-publisher prompt.

Existing development installations need one manual installation of a release
build to join the release channel. After that, subsequent workflow releases are
eligible for native updates. The workflow builds the source currently on the
default branch; it does not fetch or merge Waterfox security fixes automatically.
Follow `KONAFOX_UPDATE_GUIDE.md` to update the source, then run the release workflow.

## Checks and recovery

The build checks package identity, version, build ID, channel, required updater
files, and headless packaged-browser startup. A complete update must remain below
the native updater's 500 MB MAR limit. On failure, inspect the
`konafox-release-logs` Actions artifact. No update feed is changed by a build failure.

If publication fails after the numbered release is published, rerun the failed
**publish** job from the same run. Identical published metadata is accepted, so
the job can finish updating the feed. Run the entire workflow again for a fresh
build ID when rebuilding binaries. Do not reuse a build ID with changed files.

Before relying on unattended updates, make two successful releases and verify
that a disposable installation of the first updates to the second, preserves
its profile and extensions, and restarts successfully. Neither the full release
build nor this end-to-end upgrade has been completed locally yet.

To run the focused signing/feed tests:

```powershell
& C:\mozilla-build\python3\python.exe -m venv artifacts/release-venv
& artifacts/release-venv/Scripts/python.exe -m pip install -r konafox/release/requirements.txt
& artifacts/release-venv/Scripts/python.exe -m unittest discover -s konafox/release -p test_release.py -v
```
