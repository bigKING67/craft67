import test from 'node:test';import assert from 'node:assert/strict';import * as fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';import sharp from 'sharp';
import {cropPhoto} from '../photo-crop.mjs';import {sha256} from '../../local-production/content-store.mjs';
async function fixture(t){const dir=await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()),'crop-授权 '));t.after(()=>fs.rm(dir,{recursive:true,force:true}));const source=path.join(dir,'source.png');const bytes=Buffer.from(Array.from({length:24*16*4},(_,i)=>(i*13)%256));await sharp(bytes,{raw:{width:24,height:16,channels:4}}).png().toFile(source);return {dir,input:{source,source_sha256:sha256(await fs.readFile(source)),crop:{left:3,top:2,width:12,height:10},authorization:{user_approved:true,context:'User explicitly approved this rectangle'}}};}
test('dry-run writes nothing and crop preserves alpha and original bytes with bound receipt',async t=>{
 const {dir,input}=await fixture(t),output=path.join(dir,'crop');const dry=await cropPhoto(output,input,{dryRun:true});await assert.rejects(fs.stat(output),{code:'ENOENT'});
 const result=await cropPhoto(output,input);assert.deepEqual(result.receipt,dry.receipt);assert.deepEqual(await fs.readFile(path.join(output,'original.png')),await fs.readFile(input.source));
 const expected=await sharp(input.source).extract(input.crop).ensureAlpha().raw().toBuffer();assert.deepEqual(await sharp(path.join(output,'cropped.png')).ensureAlpha().raw().toBuffer(),expected);
 assert.equal(sha256(expected),result.receipt.qa.retained_rgba_sha256);assert.equal(result.receipt.qa.product_completeness,'UNVERIFIED');
 assert.equal(sha256(await fs.readFile(path.join(output,'cropped.png'))),result.receipt.result.sha256);
});
test('authorization, identity, bounds, unknown fields, symlinks and existing output fail closed',async t=>{
 const {dir,input}=await fixture(t);const cases=[{authorization:{user_approved:false,context:'no'}},{authorization:undefined},{source_sha256:'0'.repeat(64)},{crop:{left:23,top:0,width:2,height:2}},{crop:{left:0.5,top:0,width:1,height:1}},{crop:{left:0,top:0,width:0,height:1}},{crop:{left:-1,top:0,width:1,height:1}},{crop:{...input.crop,scale:2}}];
 for(const [i,patch] of cases.entries())for(const dryRun of [true,false]){const output=path.join(dir,`bad-${i}-${dryRun}`);await assert.rejects(cropPhoto(output,{...input,...patch},{dryRun}));await assert.rejects(fs.stat(output),{code:'ENOENT'});}
 const link=path.join(dir,'link.png');await fs.symlink(input.source,link);await assert.rejects(cropPhoto(path.join(dir,'linked'),{...input,source:link}),/Symlink/);
 const output=path.join(dir,'existing');await fs.mkdir(output);await fs.writeFile(path.join(output,'keep'),'keep');for(const dryRun of [true,false])await assert.rejects(cropPhoto(output,input,{dryRun}),/already exists/);assert.equal(await fs.readFile(path.join(output,'keep'),'utf8'),'keep');assert.equal(sha256(await fs.readFile(input.source)),input.source_sha256);
});
test('coordinates bind to EXIF-oriented source and can include its bottom/right edge',async t=>{
 const {dir,input}=await fixture(t);const source=path.join(dir,'oriented.jpg');await sharp(input.source).removeAlpha().withMetadata({orientation:6}).jpeg().toFile(source);
 const normalized=await sharp(source).rotate().toColourspace('srgb').png().toBuffer();const meta=await sharp(normalized).metadata();assert.equal(meta.width,16);assert.equal(meta.height,24);
 const crop={left:8,top:14,width:8,height:10},output=path.join(dir,'oriented');const result=await cropPhoto(output,{...input,source,source_sha256:sha256(await fs.readFile(source)),crop});
 assert.equal(result.receipt.source.width,16);assert.equal(result.receipt.source.height,24);assert.deepEqual(await sharp(path.join(output,'cropped.png')).ensureAlpha().raw().toBuffer(),await sharp(normalized).extract(crop).ensureAlpha().raw().toBuffer());
});
