/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

/** Serves the script-free KonaFox information page with a content principal. */
export class AboutKonaFox {
  QueryInterface = ChromeUtils.generateQI(["nsIAboutModule"]);

  newChannel(uri, loadInfo) {
    const channel = Services.io.newChannelFromURIWithLoadInfo(
      Services.io.newURI("chrome://konafox/content/about/aboutKonaFox.html"),
      loadInfo
    );
    channel.originalURI = uri;
    channel.owner = null;
    return channel;
  }

  getURIFlags() {
    return (
      Ci.nsIAboutModule.URI_SAFE_FOR_UNTRUSTED_CONTENT |
      Ci.nsIAboutModule.URI_MUST_LOAD_IN_CHILD
    );
  }
}
