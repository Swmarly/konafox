/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

export const KONAFOX_PALETTE = {
  labelId: "waterfox-onboarding-color-default-label",
  swatch: "linear-gradient(135deg, #8994da, #4d568f)",
  light: {
    frame: "#d7dcf4",
    toolbar: "#f7f6fa",
    toolbar_text: "#303858",
    tab_background_text: "#303858",
    tab_selected: "#e8ecfa",
    toolbar_field: "#ffffff",
    toolbar_field_text: "#303858",
    toolbar_field_border_focus: "#4d568f",
    tab_line: "#747ccb",
    icons_attention: "#4d568f",
    ntp_background: "#f7f6fa",
    ntp_text: "#303858",
  },
  dark: {
    frame: "#22263f",
    toolbar: "#292e4c",
    toolbar_text: "#e8ecfa",
    tab_background_text: "#e8ecfa",
    tab_selected: "#444d7c",
    toolbar_field: "#1e223a",
    toolbar_field_text: "#e8ecfa",
    toolbar_field_border_focus: "#b7ace2",
    tab_line: "#b7ace2",
    icons_attention: "#b7ace2",
    ntp_background: "#22263f",
    ntp_text: "#e8ecfa",
  },
  images: {
    light: {
      theme_frame: { "linear-gradient": "105deg, #d7dcf4, #b7ace2" },
    },
    dark: {
      theme_frame: { "linear-gradient": "105deg, #22263f, #353d68" },
    },
  },
};
