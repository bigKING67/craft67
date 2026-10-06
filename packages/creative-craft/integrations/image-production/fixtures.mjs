// Synthetic local assets for acceptance only; these are not a real product,
// licensed brand assets, or evidence of an image-model call.
import * as fs from 'node:fs/promises';
import path from 'node:path';
import sharp from 'sharp';

export async function demoInput(directory) {
  await fs.mkdir(directory);
  const sources = {
    background: '<svg width="1000" height="1000" xmlns="http://www.w3.org/2000/svg"><defs><radialGradient id="g"><stop stop-color="#faf7e9"/><stop offset="1" stop-color="#e4e8dc"/></radialGradient></defs><rect width="1000" height="1000" fill="url(#g)"/><circle cx="850" cy="550" r="300" fill="#d2dcca" opacity=".4"/></svg>',
    product: '<svg width="360" height="580" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g"><stop stop-color="#576b58"/><stop offset=".35" stop-color="#a1b293"/><stop offset=".72" stop-color="#839c7e"/><stop offset="1" stop-color="#486249"/></linearGradient></defs><ellipse cx="180" cy="562" rx="122" ry="12" fill="#687963" opacity=".16"/><rect x="105" y="20" width="148" height="36" rx="8" fill="#263d30"/><rect x="244" y="20" width="64" height="23" rx="6" fill="#263d30"/><rect x="155" y="52" width="50" height="70" fill="#b8b5a0"/><rect x="100" y="104" width="160" height="48" rx="14" fill="#263d30"/><path d="M100 135 Q65 154 65 205 V525 Q65 554 100 554 H260 Q295 554 295 525 V205 Q295 154 260 135Z" fill="url(#g)"/><rect x="75" y="165" width="16" height="350" rx="8" fill="#d5e0c9" opacity=".25"/><rect x="83" y="276" width="194" height="164" rx="2" fill="#eeeedd"/><path d="M145 316H215 M131 344H229 M151 376H209 M159 399H201" stroke="#4b6350" stroke-width="5"/></svg>',
    logo: '<svg width="180" height="64" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="178" height="62" rx="31" fill="#263d30"/><path d="M35 23H55V41H35Z M73 23H93V41H73Z M111 23H145V41H111Z" fill="#edf0dc"/></svg>',
  };
  const assets = [];
  for (const [id, svg] of Object.entries(sources)) {
    const source = path.join(directory, `${id}.png`);
    await fs.writeFile(source, await sharp(Buffer.from(svg)).png().toBuffer(), { flag: 'wx' });
    assets.push({ id, source });
  }
  const common = (id, kind, x, y, width, height, locked = false) => ({ id, kind, locked, visible: true, x, y, width, height, opacity: 1 });
  const text = (id, content, x, y, width, height, size, color) => ({ ...common(id, 'text', x, y, width, height), text: content, font_size: size, color, align: 'left', line_height: 1.25 });
  return { project_id: 'spring-poster', title: '图片工程 P0 合成测试海报', canvas: { width: 1000, height: 1000, background: '#e4e8dc' }, assets,
    objects: [
      { ...common('background', 'image', 0, 0, 1000, 1000), asset_id: 'background', fit: 'cover' },
      { ...common('logo', 'image', 710, 64, 180, 64, true), asset_id: 'logo', fit: 'contain' },
      text('eyebrow', 'CRAFT LAB / 2026', 70, 74, 600, 32, 22, '#526452'),
      text('headline', '春日焕新\n轻盈日常', 70, 202, 480, 220, 72, '#263d30'),
      text('description', '把清新，留在每一天。', 75, 445, 460, 48, 29, '#526452'),
      text('price', '¥129', 75, 590, 440, 90, 64, '#263d30'),
      text('note', '春日限定 · 300 mL', 78, 708, 460, 40, 24, '#526452'),
      { ...common('product', 'image', 580, 254, 340, 548), asset_id: 'product', fit: 'contain' },
      text('footer', '本图为工程验收用合成素材，非真实商品广告。', 70, 919, 820, 40, 18, '#526452'),
    ] };
}
