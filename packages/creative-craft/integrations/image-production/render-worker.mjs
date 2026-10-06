import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import satori from 'satori';
import { Resvg } from '@resvg/resvg-js';
import sharp from 'sharp';
import { readProject, candidateDocument } from './project.mjs';
import { checkTextWidths } from './font.mjs';

export async function compose(project) {
  const { document: doc, root, font } = project;
  checkTextWidths(font, doc.objects.filter(object => object.visible && object.kind === 'text'));
  // Encode only rasters that visible objects draw; history keeps every asset bound.
  const images = new Map();
  for (const object of doc.objects) {
    if (!object.visible || object.kind !== 'image' || images.has(object.asset_id)) continue;
    const asset = doc.assets.find(asset => asset.id === object.asset_id);
    images.set(asset.id, `data:image/png;base64,${(await fs.readFile(path.join(root, asset.render_file))).toString('base64')}`);
  }
  const measurements = new Map();
  const children = doc.objects.filter(object => object.visible).map(object => {
    const style = { display: 'flex', position: 'absolute', left: object.x, top: object.y, width: object.width, height: object.height, opacity: object.opacity };
    if (object.kind === 'image') return { type: 'img', props: { src: images.get(object.asset_id), style: { ...style, objectFit: object.fit } } };
    if (object.kind === 'rect') return { type: 'div', props: { style: { ...style, backgroundColor: object.color, borderRadius: object.radius } } };
    // Measure natural text height rather than clipping it into the declared box.
    // Satori outlines the bound font, so SVG/PNG never use a host font fallback.
    const { height, ...textStyle } = style;
    return { type: 'div', props: { id: `text-${object.id}`, style: { ...textStyle, fontFamily: doc.font.family, fontWeight: 400,
      fontSize: object.font_size, lineHeight: object.line_height, color: object.color, flexDirection: 'column' },
      // Explicit lines must remain independent blocks: Satori's break-all
      // wrapping otherwise collapses newlines even with pre-wrap.
      children: object.text.split('\n').map(line => ({ type: 'div', props: { style: { display: 'flex', width: object.width,
        minHeight: object.font_size * object.line_height, whiteSpace: 'pre-wrap', wordBreak: 'break-all', textAlign: object.align,
        justifyContent: { left: 'flex-start', center: 'center', right: 'flex-end' }[object.align] }, children: line || ' ' } })) } };
  });
  const svg = await satori({ type: 'div', props: { style: { display: 'flex', position: 'relative', width: doc.canvas.width, height: doc.canvas.height, backgroundColor: doc.canvas.background }, children } }, {
    width: doc.canvas.width, height: doc.canvas.height,
    embedFont: true, fonts: [{ name: doc.font.family, data: font, weight: 400, style: 'normal' }],
    onNodeDetected: node => { if (node.props?.id?.startsWith('text-')) measurements.set(node.props.id.slice(5), { width: node.width, height: node.height }); },
  });
  for (const object of doc.objects.filter(object => object.visible && object.kind === 'text')) {
    const size = measurements.get(object.id);
    if (!size || size.height > object.height + 0.5 || size.width > object.width + 0.5) throw new Error(`Text overflow: ${object.id}`);
  }
  return { svg, text_measurements: Object.fromEntries(measurements) };
}

async function main() {
  const [root, revision, expected, output, previewMax, candidateId, candidateSha] = process.argv.slice(2);
  const project = await readProject(root, { revision: Number(revision) });
  if (project.sha256 !== expected) throw new Error('Revision changed before rendering');
  if (candidateId) {
    const prepared = await candidateDocument(root, project, candidateId);
    if (prepared.entry.sha256 !== candidateSha) throw new Error('Candidate changed before rendering');
    project.document = prepared.document;
  }
  const { svg, text_measurements } = await compose(project);
  let png = Buffer.from(new Resvg(svg, { font: { loadSystemFonts: false } }).render().asPng());
  if (previewMax !== '0') png = await sharp(png).resize({ width: Number(previewMax), height: Number(previewMax), fit: 'inside', withoutEnlargement: true }).png({ compressionLevel: 9 }).toBuffer();
  const metadata = await sharp(png).metadata();
  await fs.writeFile(path.join(output, 'image.svg'), svg, { flag: 'wx' });
  await fs.writeFile(path.join(output, 'image.png'), png, { flag: 'wx' });
  console.log(JSON.stringify({ width: metadata.width, height: metadata.height, text_measurements }));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main().catch(error => { console.error(error.message); process.exitCode = 1; });
