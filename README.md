# KonaFox

KonaFox is a private Konata Izumi / Lucky Star themed build of Waterfox, with
isolated branding, periwinkle/indigo chrome, replaceable artwork and a separate
Windows installation/profile identity. The underlying browser remains Waterfox.

- [Build and package KonaFox](KONAFOX_BUILD.md)
- [Customization map and compatibility decisions](KONAFOX_MODIFICATIONS.md)
- [Update from Waterfox](KONAFOX_UPDATE_GUIDE.md)
- [Replace the temporary artwork](konafox/ASSETS.md)
- [Validation status](konafox/VALIDATION.md)

## Waterfox base

Waterfox is a customisable browser based on Mozilla Firefox. This repository contains Mozilla platform code, Waterfox product code, branding, features, packaging, and release files.

## Building

Waterfox uses the Mozilla build system. The usual `./mach` entry points apply:

```sh
./mach bootstrap
./mach build
./mach package
./mach test --auto
```

## Contributing

Most Firefox development documentation still applies to this tree. Use the Firefox Source Docs for the shared Mozilla build system, testing tools, and platform code.

## Resources

- [Waterfox website](https://www.waterfox.net/)
- [Firefox Source Docs](https://firefox-source-docs.mozilla.org/)
