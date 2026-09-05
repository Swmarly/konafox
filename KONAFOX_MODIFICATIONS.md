# KonaFox modification map

## Implementation plan and maintenance boundary

1. Inspect the Waterfox tree and attempt its unchanged Windows baseline.
2. Use existing build/branding/profile options for a minimally rebranded product.
3. Add isolated icons and replaceable art, then extend Waterfox's palette and
   stylesheet loaders without replacing its UX or new-tab application.
4. Add an unprivileged, script-free native `about:konafox` page.
5. Check resource wiring, metadata, contrast, build/package behavior, and record
   evidence separately from unverified runtime acceptance.

Initial base: `fd6662f3abfe` (`docs(readme): rewrite the README for Waterfox`).
Upstream is `https://github.com/BrowserWorks/waterfox.git`; the locale gitlink is
`b70da340323b889a0aeecec30691136d045039cc`. The source reports `153.1.0` /
`153.1.0esr`; these are source version values, not an invented Waterfox marketing
release number. KonaFox's customization version is independently `0.1.0`.

## KonaFox-owned files

| Directory             | Purpose                                                                                                                    |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `konafox/build/`      | Thin Waterfox-derived configurations, separate object directories                                                          |
| `konafox/branding/`   | Standard Mozilla branding directory: localized product strings, Windows resources, NSIS assets and presentation-only prefs |
| `konafox/assets/`     | Editable SVG masters; see `konafox/ASSETS.md`                                                                              |
| `konafox/theme/`      | Scoped browser/new-tab/private/onboarding decoration                                                                       |
| `konafox/components/` | Palette, about-page registration, native browser tests                                                                     |
| `konafox/content/`    | Script-free localized about-page markup and CSS                                                                            |
| `konafox/tools/`      | Asset generation and source validation                                                                                     |
| `konafox/tests/`      | Standalone theme-manager and contrast checks                                                                               |
| Root `KONAFOX_*.md`   | Build, change inventory, and update procedures                                                                             |

## Every intentionally modified upstream file

| File                                                             | Change and dependency                                                                                                                          | Merge risk                       |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `.mozconfig`                                                     | Sources KonaFox's fragment instead of Waterfox's directly; makes local builds KonaFox by default                                               | Low: one include                 |
| `README.md`                                                      | Introduces KonaFox and links the maintenance documents; retains Waterfox attribution/resources                                                 | Low: introductory section        |
| `waterfox/build/mozconfig.common`                                | Makes four product options overrideable with lowercase shell variables; defaults stay Waterfox                                                 | Low: branding option block       |
| `waterfox/moz.configure`                                         | Selects KonaFox's profile and distribution through the required implied options; other product basenames retain Waterfox's values              | Low: product selector            |
| `waterfox/browser/moz.build`                                     | Includes `/konafox` only for `MOZ_APP_NAME=konafox`                                                                                            | Low: conditional directory       |
| `waterfox/browser/components/theme/WaterfoxStyles.sys.mjs`       | Registers two scoped KonaFox sheets only for this product                                                                                      | Low: startup hook                |
| `waterfox/browser/components/theme/WaterfoxThemeColors.sys.mjs`  | Replaces the default palette from a separate module; makes it active on a fresh KonaFox profile; retains all other colors and installed themes | Medium: theme manager API        |
| `waterfox/browser/components/onboarding/content/onboarding.html` | Removes a hardcoded Waterfox alt name from a decorative wordmark, beside the localized welcome heading                                         | Low: one attribute               |
| `browser/app/moz.build`                                          | Supplies the KonaFox executable-manifest resource path                                                                                         | Low: Windows resource definition |
| `browser/app/splash.rc`                                          | Conditionally embeds the branded manifest; all security/compatibility manifest entries stay inherited                                          | Low: resource hook               |
| `browser/app/module.ver`                                         | Uses the existing `%` preprocessor to select KonaFox EXE company/copyright/trademark fields; Waterfox branch retained                          | Low: metadata block              |
| `browser/installer/windows/moz.build`                            | Exposes application basename to the installer preprocessor                                                                                     | Low: one definition              |
| `browser/installer/windows/nsis/defines.nsi.in`                  | Uses configured basename for product/registry/DDE names                                                                                        | Low: four names                  |
| `browser/installer/windows/nsis/installer.nsi`                   | Namespaces the legacy current-version write by product instead of writing Waterfox's value                                                     | Low: two registry paths          |
| `browser/installer/windows/nsis/uninstaller.nsi`                 | Writes KonaFox's uninstall marker instead of Waterfox's                                                                                        | Low: one registry path           |

Update this table whenever another upstream file is changed. No code in the
locale submodule is edited. Generated `artifacts/` and `obj-*` files are not part
of the customization layer.

## Deliberately inherited identifiers and behavior

- `MOZ_APP_ID={ec8030f7-c20a-464f-9b0e-13a3a9e97384}` and the Firefox UA preserve
  extension/site compatibility. They are not profile or install-directory IDs.
- Internal vendor `BrowserWorks` stays inherited because upstream shell and
  installer integration use that registry namespace. Its product subkeys now
  resolve to KonaFox. Visible EXE/installer company metadata is separately branded.
- Native `MozillaWindowClass` and related classes remain unchanged for driver
  and assistive-technology compatibility. The inherited installer window-class
  constants are not repurposed as a new native-window implementation.
- The `WaterfoxHTML/PDF/URL-<installation hash>` handler identifiers remain
  inherited together with their runtime consumers. The installation hash and
  KonaFox-specific path distinguish installs. Validate coexistence before daily use.
- Waterfox's `waterfox-dynamic-theme@browserworks.org`, theme preferences, browser
  styles, feature names, support links, and attribution remain where they identify
  the actual inherited implementation. No global product-name replacement is used.
- Normal new-tab search, history-backed shortcuts, user wallpapers, private page
  controls, menus, sidebar behavior, extension APIs, security and privacy settings
  remain Waterfox's. The artwork preference only affects decorative styling.

## Tradeoffs

The About page displays build-time source version and target data and links to
`about:support` for live build details. This avoids granting the page system
privileges or adding a privileged actor solely to display metadata.

The new default colors go through Waterfox's existing theme manager. Central
High Contrast handling stays in `toolkit/modules/LightweightThemeConsumer.sys.mjs`;
KonaFox's extra decoration is gated out of forced colors.

Artwork is explicitly provisional. Final supplied Konata art can replace SVG
masters or generated outputs without touching browser behavior. Windows x64 and
the full NSIS installer are the supported target; macOS bundles, Linux packaging,
MSIX signing/identity, download stubs and automatic updates are not implemented.

See `konafox/VALIDATION.md` for tested versus untested layers.
