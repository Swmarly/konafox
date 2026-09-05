/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

add_task(async function about_page_is_unprivileged_and_branded() {
  const module = Cc[
    "@mozilla.org/network/protocol/about;1?what=konafox"
  ].getService(Ci.nsIAboutModule);
  const flags = module.getURIFlags(Services.io.newURI("about:konafox"));
  Assert.ok(flags & Ci.nsIAboutModule.URI_SAFE_FOR_UNTRUSTED_CONTENT);
  Assert.ok(flags & Ci.nsIAboutModule.URI_MUST_LOAD_IN_CHILD);

  await BrowserTestUtils.withNewTab("about:konafox", async browser => {
    await SpecialPowers.spawn(browser, [], async () => {
      await content.document.l10n.ready;
      Assert.ok(!content.document.nodePrincipal.isSystemPrincipal);
      Assert.ok(content.document.title.includes("KonaFox"));
      Assert.equal(
        content.document.getElementById("konafox-version").textContent,
        "0.1.0"
      );
      Assert.ok(
        !content.document
          .getElementById("waterfox-version")
          .textContent.includes("@")
      );
    });
  });
});

add_task(async function product_identity_and_theme() {
  Assert.equal(Services.appinfo.name, "KonaFox");
  Assert.equal(Services.appinfo.ID, "{ec8030f7-c20a-464f-9b0e-13a3a9e97384}");
  const { WaterfoxThemeColors } = ChromeUtils.importESModule(
    "resource:///modules/WaterfoxThemeColors.sys.mjs"
  );
  const light = WaterfoxThemeColors.buildThemeData("light", "default");
  Assert.equal(light.theme.colors.toolbar, "#f7f6fa");
  Assert.ok(WaterfoxThemeColors.hasSelection());
});
