# Updating KonaFox from Waterfox

## Prepare and identify the update

Read `KONAFOX_MODIFICATIONS.md` and `konafox/VALIDATION.md`. Finish or commit your
current work and record the current tested KonaFox revision. Keep a backup of
your personal KonaFox profile with the browser closed; never use a normal
Waterfox/Firefox profile as a disposable test profile.

```sh
git status --short
git remote -v
git fetch upstream --tags
git remote show upstream
git branch -r
```

`upstream` must be `https://github.com/BrowserWorks/waterfox.git`. If it is absent,
add that exact remote. Select the **actual Waterfox branch or release tag** you
intend to follow; do not assume Mozilla's main branch or guess a Waterfox branch
name from older notes. Set `WATERFOX_REF` below to that verified ref.

```sh
WATERFOX_REF=upstream/REPLACE_WITH_VERIFIED_BRANCH
git log --oneline HEAD.."$WATERFOX_REF"
git diff --stat HEAD..."$WATERFOX_REF"
git diff HEAD..."$WATERFOX_REF" -- waterfox browser/app browser/installer/windows
git switch -c codex/waterfox-sync-YYYYMMDD
git merge --no-commit --no-ff "$WATERFOX_REF"
```

The placeholder branch name is intentional: replace it before running commands.
Use a unique date/suffix if the local synchronization branch already exists.

## Resolve conflicts deliberately

```sh
git diff --name-only --diff-filter=U
git diff --cc
```

For each conflict, inspect the upstream behavior, the KonaFox change map, and its
dependent files. Integrate the new upstream code first, then preserve or adapt
the small customization hook. Never resolve by blindly accepting `ours`/`theirs`
or deleting KonaFox changes. Do not reformat unrelated code. If the architecture
changed, prefer relocating the integration hook over forking an upstream module.

Check these connections explicitly:

1. Branding options and configure output still select KonaFox and its profile.
2. The conditional `/konafox` directory remains included and its resources package.
3. Waterfox's palette-manager API still consumes `KonaFoxPalette.sys.mjs`, handles
   fresh profiles, switches light/dark, and respects installed theme extensions.
4. New-tab CSS still matches the actual DOM and wallpaper classes. Keep native
   search/shortcuts and user-selected wallpapers working.
5. NSIS product names, uninstall markers, hash-based handlers, manifest resources,
   and VisualElements paths still agree with the executable and profile identity.
6. Refresh `konafox/branding/konafox.exe.manifest` from the updated upstream
   manifest, changing only its product name/description; preserve mitigations.
7. Compare upstream branding defaults with `konafox-branding.js`, bringing forward
   needed inherited timing/safety defaults without sending users to Waterfox binaries.

After the merge resolves the locale gitlink, initialize exactly that revision:

```sh
git -c 'url.https://github.com/.insteadOf=git@github.com:' submodule update --init --recursive
python3 konafox/tools/verify_source.py
node --test konafox/tests/palette.test.cjs
git diff --check
```

Update the modification map, source-version notes, and validation record.

## Build and acceptance

Follow `KONAFOX_BUILD.md`, including any new Waterfox toolchain requirements.
Build from source, run the native browser tests with `--headless`, package, and
build the full installer. Redirect lengthy command output into `artifacts/` and
inspect the saved logs. Do not treat static checks as a successful browser build.

Use a disposable Windows user account or VM with existing Waterfox and Firefox
installations for the following manual checks:

- KonaFox launches from `mach run`, its EXE, Start Menu and desktop shortcut.
- HTTPS sites, tabs, URL/search bar, settings, bookmarks, downloads and history work.
- Waterfox Nova/Proton/Photon, tree tabs, built-in blocking, sidebar and other
  features used by your profile still work.
- Install a normal compatible Firefox extension; enable a separate theme
  extension, switch back to default, and verify that both continue to work.
- Check light/dark/system themes, tab/loading/focus states, native menus,
  private windows/tabs, new-tab search/shortcuts, wallpaper selection, and the
  `konafox.artwork.enabled` toggle. Private browsing still reports the correct
  privacy state; no private history survives closing the last private window.
- Open `about:konafox`, About KonaFox and `about:support`; verify names, version
  values, icon assets, page links, and build metadata.
- Confirm `about:support` points to `%APPDATA%\KonaFox`, then make a bookmark in
  each browser and verify the others' normal profiles remain independent.
- With NVDA, verify the about-page title, headings, version labels and named links.
  Check Tab/Shift+Tab/Enter and visible focus. Check 200%/400% zoom and Windows
  increased text size; verify no clipping or lost content.
- Switch Windows contrast themes on/off while the browser is running. Text,
  borders, focus, selection and loading must remain visible; check Increase
  Contrast as well. Extra artwork must not obstruct system colors.
- Install the full package into KonaFox's own directory (normally
  `C:\Program Files\KonaFox`), verify taskbar/shortcut/default-browser identity,
  then uninstall it. Waterfox and Firefox files, shortcuts, registry ownership,
  profile data and normal launches must remain intact. Never run destructive
  coexistence checks against the only copy of personal browser data.

Record the exact revision, toolchain, package paths and outcomes in
`konafox/VALIDATION.md`. Mark failed/untested checks explicitly. Keep the last
known-good installer and profile backup until acceptance completes.

## Finish the synchronization

```sh
git status --short
git diff --cached --stat
git add <explicitly-reviewed-files>
git commit -m "KonaFox: synchronize with Waterfox <verified version/ref>"
```

Review the complete merge and docs before committing. Do not push or publish
unless requested. The inherited Waterfox release/signing workflows are not a
KonaFox release pipeline. A successful upstream fetch alone delivers no security
fixes to an installed browser: rebuild, validate and install the updated binary.
