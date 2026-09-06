# KonaFox validation record

Validation date: 2026-09-05. Base revision: `fd6662f3abfe`.

## Release workflow and native updates

Release checks finalized on 2026-09-06. Targeted Mach Ruff, Ruff-format,
Fluent and ESLint checks report zero errors and warnings. Prettier, PowerShell
parsing, shell syntax and source validation passed. Preference preprocessing
confirmed KonaFox's update URL and preserved Waterfox's original branch.

On 2026-09-06, the approved Windows runner was registered and GitHub reported
`KonaFox-DESKTOP-QQLGN8Q` online, idle, running version 2.337.0 with the required
`self-hosted`, `Windows`, `X64` and `konafox` labels. Its console confirmed
`Listening for Jobs`. The workflow is active and the signing secret exists.
Registration and connectivity do not constitute a successful release build.

The additional `konafox/build/mozconfig.release.windows` configuration completed
successfully (`artifacts/konafox-release-configure.log`). Its generated settings
confirm `MOZ_UPDATER=1`, `MOZ_VERIFY_MAR_SIGNATURE=1`, `konafox-release` for both
the update and accepted MAR channels, and no disabled Authenticode checks. The
updater's generated build rules consume KonaFox's public DER certificate.

All five focused release tests passed: valid signing, tamper rejection, wrong-key
and version rejection, unsigned archive rejection, feed advancement/retry rules,
and XML hash/size/URL consistency. A small harness compiled the repository's
actual Windows MAR reader and verifier with Clang 22 and the configured SDK:
valid signatures returned 0; a wrong key and a changed signature each returned 1
(`artifacts/native-mar-check.log`). This checks native cryptographic compatibility.

The release workflow also requires native `signmar.exe` verification and a
headless launch of the packaged browser before publishing. These workflow gates
have not run yet. A complete installer build and a two-release client upgrade
remain unverified. See `KONAFOX_RELEASE.md` for setup and release operation.

## Completed checks

- `python konafox/tools/verify_source.py`: passed. Uses Mozilla's preprocessor
  for both Waterfox and KonaFox executable metadata/resource branches and the
  About page; checks JAR assets, Fluent references, manifest parity, PNG-backed
  ICO frames, installer BMP dimensions, and `moz.build` Python syntax.
- `node --test konafox/tests/palette.test.cjs`: all three tests passed. Exercises
  the actual Waterfox palette manager with external services stubbed, confirms
  the baseline palette and installed theme choices remain available, and checks
  main text/surface contrast at 4.5:1 or better.
- Targeted Mach ESLint, Stylelint, Ruff, Ruff-format, Fluent and test-manifest
  checks: zero errors and zero warnings. License, whitespace, file-permission
  and Trojan-source checks also passed after building Mozilla's `mozcheck`
  helper with the verified SDK/linker settings.
  The earlier all-linter attempt was blocked by missing tools; it is not recorded
  as a successful full lint run.
- `git diff --check`: passed.
- Static accessibility review: no remaining actionable findings after fixes.
  Forced-colors review passed all 12 applicable checklist items. This is source
  review, not a screen-reader or Windows High Contrast runtime test.
- Generated logo, private icon and installer watermark were visually inspected.
  The localized About page was previewed in Chromium with inherited design
  tokens, including a 480-pixel viewport with no horizontal overflow. This
  validates the static presentation only, not Gecko chrome loading.

## Windows environment and baseline

The untouched baseline could not initially configure because Python/MozillaBuild
were absent. Implementation proceeded with that limitation documented, as the
brief permits. MozillaBuild 4.2.1, Clang 22.1.8, matching WASI resources, Rust
1.97.1, and Mach-managed Windows SDK/build dependencies have since been installed.
The locale submodule is initialized at Waterfox's recorded revision.

The Waterfox-branded baseline wrapper revealed native Windows issues in the
inherited development configuration: GNU-mode `clang.exe` was rejected for the
MSVC target, and locale/WASI paths remained in MSYS form. KonaFox's own
wrappers select `clang-cl`, expose its linker directory, and convert the locale
paths with `cygpath`. No compiler checks or security mechanisms were bypassed.

The build was also retried outside the agent sandbox because it could not read
some downloaded tool directories. An automatic approval-review usage limit
interrupted a later retry; that was an execution-service limitation rather than
a compiler diagnostic.

The baseline configured successfully after these environment corrections and
compiled native code for about 24 minutes before the usage interruption stopped
the command. The last log entry is at 23:45 in `dom/media/mp3`; no successful
completion or final compiler failure is recorded. No build process remains
running. KonaFox's separate configuration and build-file
generation also completed successfully. Its generated configuration confirms
the KonaFox basename, display name and profile, `konafox` executable name,
`private.konafox` distribution and `konafox-private` channel, with the inherited
Firefox compatibility application ID. Profile/distribution selection uses
Waterfox's implied project options, as this tree rejects a mozconfig profile
override. Neither a successful full baseline nor a successful KonaFox build is
claimed yet. The requested wrap-up stops short of starting another long build.
Build logs and local dependency downloads live in ignored `artifacts/`.

To resume, use the prepared PowerShell environment in `KONAFOX_BUILD.md`, set
`MOZCONFIG=konafox/build/mozconfig.waterfox`, and run `mach build` again. Existing
object files are preserved for the incremental continuation. Once that succeeds,
launch the baseline, select `konafox/build/mozconfig.windows`, and build, test,
package and exercise the KonaFox installer using the documented commands.

## Runtime acceptance still required

After a successful KonaFox build, run the browser test manifest at
`konafox/components/test/browser/browser.toml`, then the manual checklist in
`KONAFOX_UPDATE_GUIDE.md`. In particular, verify native About-page localization and
content principal, normal browsing and Waterfox features, installed extensions,
new-tab wallpapers, light/dark/forced-colors appearance, keyboard navigation,
screen-reader behavior, separate profiles and installation paths, and full
installer installation/uninstallation alongside Waterfox and Firefox.

Artwork remains intentionally provisional and replaceable. See `ASSETS.md`.
