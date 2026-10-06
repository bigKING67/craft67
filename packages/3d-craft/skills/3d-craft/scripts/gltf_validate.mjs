#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { access, readFile, writeFile, mkdir } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import * as validator from '../vendor/gltf-validator/module.mjs';

function parseArgs(argv) {
  const values = { input: null, output: null, doctor: false };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === '--doctor') values.doctor = true;
    else if (value === '--output') values.output = argv[++index];
    else if (!values.input) values.input = value;
    else throw new Error(`unexpected argument: ${value}`);
  }
  if (values.doctor) {
    if (values.input || values.output) throw new Error('--doctor cannot be combined with asset arguments');
    return values;
  }
  if (!values.input || !values.output) throw new Error('usage: gltf_validate.mjs <asset.glb> --output <report.json>');
  return values;
}

function parseGlb(buffer) {
  if (buffer.length < 20 || buffer.readUInt32LE(0) !== 0x46546c67) throw new Error('input is not a GLB file');
  const declaredLength = buffer.readUInt32LE(8);
  if (declaredLength !== buffer.length) throw new Error(`GLB length mismatch: header=${declaredLength}, bytes=${buffer.length}`);
  const jsonLength = buffer.readUInt32LE(12);
  const jsonType = buffer.readUInt32LE(16);
  if (jsonType !== 0x4e4f534a) throw new Error('first GLB chunk is not JSON');
  if (jsonLength % 4 !== 0 || 20 + jsonLength > buffer.length) throw new Error('invalid GLB JSON chunk length');
  return JSON.parse(buffer.subarray(20, 20 + jsonLength).toString('utf8').replace(/[\u0000\u0020]+$/g, ''));
}

function mat4Multiply(a, b) {
  const out = new Array(16).fill(0);
  for (let column = 0; column < 4; column += 1) {
    for (let row = 0; row < 4; row += 1) {
      for (let k = 0; k < 4; k += 1) out[column * 4 + row] += a[k * 4 + row] * b[column * 4 + k];
    }
  }
  return out;
}

function nodeMatrix(node) {
  if (node.matrix) return node.matrix;
  const [x, y, z, w] = node.rotation ?? [0, 0, 0, 1];
  const [sx, sy, sz] = node.scale ?? [1, 1, 1];
  const [tx, ty, tz] = node.translation ?? [0, 0, 0];
  const x2 = x + x, y2 = y + y, z2 = z + z;
  const xx = x * x2, xy = x * y2, xz = x * z2;
  const yy = y * y2, yz = y * z2, zz = z * z2;
  const wx = w * x2, wy = w * y2, wz = w * z2;
  return [
    (1 - (yy + zz)) * sx, (xy + wz) * sx, (xz - wy) * sx, 0,
    (xy - wz) * sy, (1 - (xx + zz)) * sy, (yz + wx) * sy, 0,
    (xz + wy) * sz, (yz - wx) * sz, (1 - (xx + yy)) * sz, 0,
    tx, ty, tz, 1,
  ];
}

function transformPoint(matrix, point) {
  const [x, y, z] = point;
  return [
    matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12],
    matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13],
    matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14],
  ];
}

function semanticSummary(gltf, byteLength) {
  const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const bounds = { min: [Infinity, Infinity, Infinity], max: [-Infinity, -Infinity, -Infinity] };
  let primitives = 0;
  let triangles = 0;
  const meshNodes = [];
  const visited = new Set();
  function visit(nodeIndex, parentMatrix) {
    if (!Number.isInteger(nodeIndex) || nodeIndex < 0 || nodeIndex >= (gltf.nodes?.length ?? 0) || visited.has(nodeIndex)) return;
    visited.add(nodeIndex);
    const node = gltf.nodes?.[nodeIndex] ?? {};
    const world = mat4Multiply(parentMatrix, nodeMatrix(node));
    if (Number.isInteger(node.mesh)) {
      meshNodes.push(node.name ?? `node-${nodeIndex}`);
      const mesh = gltf.meshes?.[node.mesh];
      for (const primitive of mesh?.primitives ?? []) {
        primitives += 1;
        const count = Number.isInteger(primitive.indices)
          ? gltf.accessors?.[primitive.indices]?.count ?? 0
          : gltf.accessors?.[primitive.attributes?.POSITION]?.count ?? 0;
        const mode = primitive.mode ?? 4;
        if (mode === 4) triangles += Math.floor(count / 3);
        else if (mode === 5 || mode === 6) triangles += Math.max(0, count - 2);
        const accessor = gltf.accessors?.[primitive.attributes?.POSITION];
        if (!accessor?.min || !accessor?.max) continue;
        for (const x of [accessor.min[0], accessor.max[0]]) {
          for (const y of [accessor.min[1], accessor.max[1]]) {
            for (const z of [accessor.min[2], accessor.max[2]]) {
              const point = transformPoint(world, [x, y, z]);
              for (let axis = 0; axis < 3; axis += 1) {
                bounds.min[axis] = Math.min(bounds.min[axis], point[axis]);
                bounds.max[axis] = Math.max(bounds.max[axis], point[axis]);
              }
            }
          }
        }
      }
    }
    for (const child of node.children ?? []) visit(child, world);
  }
  const scene = gltf.scenes?.[gltf.scene ?? 0];
  for (const root of scene?.nodes ?? []) visit(root, identity);
  const finite = Number.isFinite(bounds.min[0]);
  const dimensions = finite ? bounds.max.map((value, index) => value - bounds.min[index]) : [0, 0, 0];
  const names = (gltf.nodes ?? []).map((node, index) => node.name ?? `node-${index}`);
  const materials = (gltf.materials ?? []).map((material, index) => material.name ?? `material-${index}`);
  const digestSource = JSON.stringify({ names: [...names].sort(), materials: [...materials].sort(), primitives, triangles, dimensions: dimensions.map((value) => Number(value.toFixed(6))) });
  return {
    bytes: byteLength,
    nodes: gltf.nodes?.length ?? 0,
    node_names: names,
    mesh_node_names: meshNodes,
    meshes: gltf.meshes?.length ?? 0,
    primitives,
    triangles,
    materials: gltf.materials?.length ?? 0,
    material_names: materials,
    textures: gltf.textures?.length ?? 0,
    images: gltf.images?.length ?? 0,
    animations: gltf.animations?.length ?? 0,
    extensions: gltf.extensionsUsed ?? [],
    required_extensions: gltf.extensionsRequired ?? [],
    bbox_min: finite ? bounds.min.map((value) => Number(value.toFixed(6))) : [0, 0, 0],
    bbox_max: finite ? bounds.max.map((value) => Number(value.toFixed(6))) : [0, 0, 0],
    dimensions: dimensions.map((value) => Number(value.toFixed(6))),
    semantic_sha256: createHash('sha256').update(digestSource).digest('hex'),
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.doctor) {
    process.stdout.write(`${JSON.stringify({ schema: '3d-craft.gltf-validator-doctor.v1', status: 'PASS', version: validator.version() })}\n`);
    return 0;
  }
  const input = path.resolve(args.input);
  const output = path.resolve(args.output);
  if (input === output) throw new Error('--output must not overwrite the input GLB');
  try {
    await access(output);
    throw new Error('validation output already exists; create a new run for a new candidate');
  } catch (error) {
    if (error?.code !== 'ENOENT') throw error;
  }
  const bytes = await readFile(input);
  const gltf = parseGlb(bytes);
  const validation = await validator.validateBytes(new Uint8Array(bytes), {
    uri: path.basename(input),
    maxIssues: 1000,
    writeTimestamp: false,
  });
  const report = {
    schema: '3d-craft.gltf-validation.v1',
    status: validation.issues.numErrors === 0 ? 'PASS' : 'FAIL',
    asset: { path: input, sha256: createHash('sha256').update(bytes).digest('hex') },
    validator: validation,
    semantic: semanticSummary(gltf, bytes.length),
  };
  await mkdir(path.dirname(output), { recursive: true });
  await writeFile(output, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
  process.stdout.write(`${JSON.stringify({ status: report.status, output, errors: validation.issues.numErrors, warnings: validation.issues.numWarnings, semantic: report.semantic })}\n`);
  return report.status === 'PASS' ? 0 : 2;
}

main().then((code) => { process.exitCode = code; }).catch((error) => {
  process.stderr.write(`3d-craft glTF validation failed: ${error.message}\n`);
  process.exitCode = 2;
});
