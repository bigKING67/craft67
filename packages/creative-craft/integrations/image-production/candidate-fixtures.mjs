// Synthetic, local-only candidate inputs and explicit grayscale masks.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

export async function candidateFixtures(directory) {
  await fs.mkdir(directory);
  const width = 1000, height = 1000;
  const background = (color, clutter = true) => `<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000"><defs><radialGradient id="g"><stop stop-color="#fff9f0"/><stop offset="1" stop-color="${color}"/></radialGradient></defs><rect width="1000" height="1000" fill="url(#g)"/><circle cx="850" cy="550" r="290" fill="#cbaaa0" opacity=".12"/>${clutter ? '<path d="M900 856Q923 817 940 835Q943 853 915 869Z" fill="#788674"/><path d="M916 853Q884 836 888 820Q911 815 923 845Z" fill="#9aab8f"/>' : ''}</svg>`;
  const backgrounds = [];
  for (const [index, color] of ['#edd9ce', '#d9e3ee', '#e4e4c9'].entries()) {
    const file = path.join(directory, `background-${index + 1}.png`);
    await fs.writeFile(file, await sharp(Buffer.from(background(color))).png().toBuffer(), { flag: 'wx' }); backgrounds.push(file);
  }
  const clean = path.join(directory, 'clean-background.png');
  await fs.writeFile(clean, await sharp(Buffer.from(background('#edd9ce', false))).png().toBuffer(), { flag: 'wx' });
  const generation = Buffer.alloc(width * height), protection = Buffer.alloc(width * height), blend = Buffer.alloc(width * height);
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
    const pixel = y * width + x;
    if (x >= 840 && x < 980 && y >= 760 && y < 920) generation[pixel] = 255;
    if ((x >= 580 && x < 920 && y >= 254 && y < 802) || (x >= 710 && x < 890 && y >= 64 && y < 128)) protection[pixel] = 255;
    const distance = Math.hypot(x - 915, y - 845);
    blend[pixel] = Math.round(Math.max(0, Math.min(1, (65 - distance) / 10)) * 255);
    if (!generation[pixel]) blend[pixel] = 0;
  }
  const masks = {};
  for (const [key, data] of Object.entries({ generation_mask: generation, protection_mask: protection, blend_mask: blend })) {
    masks[key] = path.join(directory, `${key}.png`);
    await fs.writeFile(masks[key], await sharp(data, { raw: { width, height, channels: 1 } }).toColourspace('b-w').png().toBuffer(), { flag: 'wx' });
  }
  return { backgrounds, clean, edit: { context: { x: 820, y: 740, width: 180, height: 180 }, ...masks } };
}
