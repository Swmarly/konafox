# Replaceable KonaFox artwork

All current artwork is **temporary**. It is an original star/hair emblem and
Konata-inspired silhouette, not final supplied Konata character art. Replace
the assets below without editing browser logic. Keep the filenames stable.

## SVG source assets

SVGs should be self-contained, with a `viewBox`, no scripts, external resources,
embedded web fonts, or remote image references. Keep text out of decorative
artwork; visible UI text belongs in Fluent. SVG dimensions here are the working
canvas, not a maximum render resolution.

| Master under `konafox/assets/` | Canvas      | Use                                                                    |
| ------------------------------ | ----------- | ---------------------------------------------------------------------- |
| `logo.svg`                     | 256 x 256   | Main app/EXE/shortcut emblem, About/new-tab/first-run logo             |
| `private-logo.svg`             | 256 x 256   | Private browsing EXE/shortcut and private-page emblem                  |
| `wordmark.svg`                 | 420 x 88    | KonaFox wordmark on new-tab, private page, native About and onboarding |
| `newtab-character.svg`         | 360 x 480   | Transparent character artwork, bottom-right of default new-tab         |
| `newtab-background.svg`        | 1920 x 1080 | Subtle default new-tab background decoration                           |
| `private-background.svg`       | 1920 x 1080 | Transparent indigo private-page decoration                             |
| `about-background.svg`         | 800 x 480   | Packaged replacement slot for native About background artwork          |
| `toolbar.svg`                  | 500 x 50    | Small decorative details at the end of the tab strip                   |
| `document-pdf.svg`             | 32 x 32     | PDF document icon master                                               |
| `installer.svg`                | 164 x 314   | Full installer watermark master                                        |

The `about-background.svg` replacement slot is packaged but intentionally not
drawn behind About text by default. Add its use to the isolated About stylesheet
if final art is suitable. The native browser wordmark filenames still include
`firefox-wordmark.svg`; the JAR maps these compatibility paths to KonaFox art.

For raster character art, a self-contained SVG wrapper with an embedded PNG is
possible, or change the asset extension and its reference in the isolated CSS
and JAR together. Preserve transparency and test light/dark, small windows,
zoom, RTL and High Contrast. Do not include browser UI or a fake search field
inside a background image.

## Generated branding outputs

`konafox/tools/generate-assets.cjs` uses Node.js and `sharp` to render the SVG
masters. One-time setup and regeneration from the repository root:

```sh
npm install --prefix artifacts/konafox-tools --no-save sharp
NODE_PATH="$PWD/artifacts/konafox-tools/node_modules" node konafox/tools/generate-assets.cjs
python3 konafox/tools/verify_source.py
```

Generated files are committed so ordinary browser builds do not need Sharp.
Regeneration replaces the generated PNG/ICO/BMP/JPEG files in the branding
directory; commit supplied custom versions or keep a backup before running it.
It does not change any browser preference, SVG master, or manifest.

| Output under `konafox/branding/`                              | Format/sizes                                                              |
| ------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `default16/22/24/32/48/64/128/256.png`                        | RGBA PNG at the named square size                                         |
| `firefox.ico`, `firefox64.ico`                                | PNG-backed 32-bit ICO: 16, 24, 32, 48, 64, 128, 256 px                    |
| `newtab.ico`, `newwindow.ico`, `document.ico`                 | Same multi-size ICO format; currently use the main emblem                 |
| `pbmode.ico`                                                  | Same ICO sizes, private emblem                                            |
| `document_pdf.ico`                                            | Same ICO sizes, PDF emblem                                                |
| `content/about.png`                                           | 256 x 256 PNG                                                             |
| `content/about-logo.png`, `about-logo@2x.png`                 | 192 / 384 px PNG                                                          |
| `content/about-logo-private.png`, `about-logo-private@2x.png` | 128 / 256 px PNG                                                          |
| `VisualElements_70/150.png`, `PrivateBrowsing_70/150.png`     | 70 / 150 px PNG tile icons                                                |
| `wizHeader.bmp`, `wizHeaderRTL.bmp`                           | 150 x 57, 24-bit BMP; RTL mirrors decoration only                         |
| `wizWatermark.bmp`                                            | 164 x 314, 24-bit BMP                                                     |
| `stubinstaller/bgstub.jpg`                                    | 640 x 480 JPEG required by inherited packaging; download stub unsupported |

`konafox.exe.manifest` is executable metadata, not artwork. Its security and
compatibility settings must match `browser/app/waterfox.exe.manifest`; the source
checker enforces this except for the two product-name fields. The VisualElements
XML files refer to the normal packaged `browser/VisualElements/` locations.

## Theme controls

The palette lives in `components/KonaFoxPalette.sys.mjs`. Use Waterfox's normal
Appearance light/dark/system and color choices. Installed third-party themes
remain selectable. `konafox.artwork.enabled=false` hides the added tab-strip,
new-tab and private-page decoration; application identity/logos remain KonaFox.
User-selected new-tab wallpapers override KonaFox's decorative background.
