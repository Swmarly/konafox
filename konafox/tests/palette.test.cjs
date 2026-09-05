/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

const root = path.resolve(__dirname, "../..");
const paletteSource = fs.readFileSync(
  path.join(root, "konafox/components/KonaFoxPalette.sys.mjs"),
  "utf8"
);
const palette = vm.runInNewContext(
  `${paletteSource.replace("export const", "const")}; KONAFOX_PALETTE`
);
const managerSource = fs.readFileSync(
  path.join(
    root,
    "waterfox/browser/components/theme/WaterfoxThemeColors.sys.mjs"
  ),
  "utf8"
);

function manager(product, activeTheme = "default-theme@mozilla.org") {
  return vm.runInNewContext(
    `${managerSource.replaceAll("export const", "const")}; WaterfoxThemeColors`,
    {
      ChromeUtils: {
        defineESModuleGetters(lazy) {
          lazy.LightweightThemeManager = {
            themeDataFrom: (light, dark) => ({ theme: light, darkTheme: dark }),
          };
        },
        importESModule: () => ({ KONAFOX_PALETTE: palette }),
      },
      Services: {
        appinfo: { name: product },
        io: { newURI: value => value },
        prefs: {
          prefHasUserValue: () => false,
          getStringPref: (name, fallback) =>
            name === "extensions.activeThemeID" ? activeTheme : fallback,
        },
      },
    }
  );
}

function contrast(a, b) {
  const luminance = value => {
    const channels = value
      .slice(1)
      .match(/../g)
      .map(hex => {
        const s = parseInt(hex, 16) / 255;
        return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
      });
    return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  };
  const x = luminance(a);
  const y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}

test("KonaFox is the default palette without forcing a user theme preference", () => {
  const konafox = manager("KonaFox");
  assert.equal(konafox.hasSelection(), true);
  assert.equal(
    konafox.buildThemeData("light", "default").theme.colors.toolbar,
    "#f7f6fa"
  );
  assert.equal(
    konafox.buildThemeData("dark", "default").theme.colors.toolbar,
    "#292e4c"
  );
  assert.equal(manager("Waterfox").hasSelection(), false);
  assert.equal(
    manager("Waterfox").buildThemeData("light", "default").theme.colors.toolbar,
    "#f7fbff"
  );
});

test("Waterfox color choices and installed extension themes remain available", () => {
  assert.equal(
    manager("KonaFox").colors.length,
    manager("Waterfox").colors.length
  );
  assert.equal(
    manager("KonaFox").buildThemeData("light", "smoke").theme.colors.toolbar,
    manager("Waterfox").buildThemeData("light", "smoke").theme.colors.toolbar
  );
  assert.equal(
    manager("KonaFox", "user-theme@example.org").shouldApply(),
    false
  );
});

test("every main text/surface combination meets 4.5:1 contrast", () => {
  for (const variant of ["light", "dark"]) {
    const colors = palette[variant];
    for (const [foreground, background] of [
      ["toolbar_text", "toolbar"],
      ["tab_background_text", "frame"],
      ["tab_background_text", "tab_selected"],
      ["toolbar_field_text", "toolbar_field"],
      ["ntp_text", "ntp_background"],
    ]) {
      assert.ok(
        contrast(colors[foreground], colors[background]) >= 4.5,
        `${variant}: ${foreground}/${background}`
      );
    }
  }
});
