/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

const fs = require("node:fs/promises");
const path = require("node:path");
const sharp = require("sharp");

const root = path.resolve(__dirname, "..");
const branding = path.join(root, "branding");
const sizes = [16, 22, 24, 32, 48, 64, 128, 256];

async function writeIcon(
  name,
  source,
  iconSizes = [16, 24, 32, 48, 64, 128, 256]
) {
  const images = await Promise.all(
    iconSizes.map(size => sharp(source).resize(size, size).png().toBuffer())
  );
  const header = Buffer.alloc(6 + 16 * images.length);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(images.length, 4);
  let offset = header.length;
  images.forEach((image, index) => {
    const entry = 6 + index * 16;
    header[entry] = header[entry + 1] = iconSizes[index] % 256;
    header.writeUInt16LE(1, entry + 4);
    header.writeUInt16LE(32, entry + 6);
    header.writeUInt32LE(image.length, entry + 8);
    header.writeUInt32LE(offset, entry + 12);
    offset += image.length;
  });
  await fs.writeFile(
    path.join(branding, name),
    Buffer.concat([header, ...images])
  );
}

async function bitmap(name, source, width, height, flop = false) {
  let pipeline = sharp(source)
    .resize(width, height)
    .flatten({ background: "#f7f6fa" });
  if (flop) {
    pipeline = pipeline.flop();
  }
  const { data, info } = await pipeline
    .removeAlpha()
    .raw()
    .toBuffer({ resolveWithObject: true });
  const stride = (width * 3 + 3) & ~3;
  const result = Buffer.alloc(54 + stride * height);
  result.write("BM");
  result.writeUInt32LE(result.length, 2);
  result.writeUInt32LE(54, 10);
  result.writeUInt32LE(40, 14);
  result.writeInt32LE(width, 18);
  result.writeInt32LE(height, 22);
  result.writeUInt16LE(1, 26);
  result.writeUInt16LE(24, 28);
  result.writeUInt32LE(stride * height, 34);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const src = (y * width + x) * info.channels;
      const dst = 54 + (height - 1 - y) * stride + x * 3;
      result[dst] = data[src + 2];
      result[dst + 1] = data[src + 1];
      result[dst + 2] = data[src];
    }
  }
  await fs.writeFile(path.join(branding, name), result);
}

async function main() {
  const logo = await fs.readFile(path.join(root, "assets/logo.svg"));
  const privateLogo = await fs.readFile(
    path.join(root, "assets/private-logo.svg")
  );
  const document = await fs.readFile(
    path.join(root, "assets/document-pdf.svg")
  );
  const installer = await fs.readFile(path.join(root, "assets/installer.svg"));
  for (const size of sizes) {
    await sharp(logo)
      .resize(size, size)
      .png()
      .toFile(path.join(branding, `default${size}.png`));
  }
  for (const [name, source] of [
    ["firefox.ico", logo],
    ["firefox64.ico", logo],
    ["document.ico", logo],
    ["document_pdf.ico", document],
    ["newtab.ico", logo],
    ["newwindow.ico", logo],
    ["pbmode.ico", privateLogo],
  ]) {
    await writeIcon(name, source);
  }
  for (const [name, source, size] of [
    ["content/about.png", logo, 256],
    ["content/about-logo.png", logo, 192],
    ["content/about-logo@2x.png", logo, 384],
    ["content/about-logo-private.png", privateLogo, 128],
    ["content/about-logo-private@2x.png", privateLogo, 256],
    ["VisualElements_70.png", logo, 70],
    ["VisualElements_150.png", logo, 150],
    ["PrivateBrowsing_70.png", privateLogo, 70],
    ["PrivateBrowsing_150.png", privateLogo, 150],
  ]) {
    await sharp(source)
      .resize(size, size)
      .png()
      .toFile(path.join(branding, name));
  }
  const header = Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="150" height="57"><rect width="150" height="57" fill="#f7f6fa"/><image x="95" y="4" width="49" height="49" href="data:image/svg+xml;base64,${logo.toString("base64")}"/></svg>`
  );
  await bitmap("wizHeader.bmp", header, 150, 57);
  await bitmap("wizHeaderRTL.bmp", header, 150, 57, true);
  await bitmap("wizWatermark.bmp", installer, 164, 314);
  await sharp(installer)
    .resize(640, 480, { fit: "cover" })
    .jpeg()
    .toFile(path.join(branding, "stubinstaller/bgstub.jpg"));
  console.log(
    "Generated KonaFox PNG, Windows ICO, and installer BMP/JPEG assets."
  );
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
