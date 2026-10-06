import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import sharp from 'sharp';
import {createPhotoProject} from '../project.mjs';
import {renderProject} from '../render.mjs';
async function fixture(t) {
 const dir=await fs.mkdtemp(path.join(await fs.realpath(os.tmpdir()),'craft-template-'));
 t.after(()=>fs.rm(dir,{recursive:true,force:true}));return dir;
}
test('both templates preserve differently shaped photos and dry-run predicts publication',async t=>{
 const dir=await fixture(t);
 for(const [template,width,height] of [['brand-detail',900,1100],['xiaohongshu-cover',1100,700]]){
  const source=path.join(dir,template+'.png');
  const bytes=Buffer.from(Array.from({length:width*height*3},(_,i)=>(i*17+Math.floor(i/113))%256));
  await sharp(bytes,{raw:{width,height,channels:3}}).png().toFile(source);
  const root=path.join(dir,template),brief={project_id:'template',source,headline:'让光停留，\n映见清透',brand:'GROLAND',template};
  const dry=await createPhotoProject(root,brief,{dryRun:true});await assert.rejects(fs.stat(root),{code:'ENOENT'});
  const result=await createPhotoProject(root,brief);assert.equal(result.sha256,dry.sha256);
  assert.equal(result.layout.template,template);assert.equal(result.layout.photo.scale,1);
  const photo=result.document.objects.find(o=>o.id==='photo');assert.equal(photo.locked,true);
  assert.equal(photo.x,Math.floor((result.document.canvas.width-width)/2));
  assert.equal(photo.y,result.layout.slot.y+Math.floor((result.layout.slot.height-height)/2));
  await renderProject(root,path.join(dir,template+'-export'));
  assert.deepEqual(await sharp(path.join(dir,template+'-export/image.png')).extract({left:photo.x,top:photo.y,width,height}).removeAlpha().raw().toBuffer(),bytes);
 }
});
test('invalid template, fit, copy and ratio fail before either dry-run or creation writes',async t=>{
 const dir=await fixture(t),source=path.join(dir,'photo.png');
 await sharp({create:{width:1254,height:1254,channels:3,background:'#dab549'}}).png().toFile(source);
 const base={project_id:'t',source,headline:'标题',brand:'GROLAND',template:'brand-detail'};
 const cases=[{template:null},{template:'missing'},{brand:''},{caption:'unsupported'},{canvas:{width:1600,height:1600}},{canvas:{width:800,height:1000}},{headline:'长'.repeat(2000)}];
 for(const [i,patch] of cases.entries())for(const dryRun of [true,false]){
  const root=path.join(dir,`invalid-${i}-${dryRun}`);
  await assert.rejects(createPhotoProject(root,{...base,...patch},{dryRun}));
  await assert.rejects(fs.stat(root),{code:'ENOENT'});
 }
 const missing={...base};delete missing.brand;await assert.rejects(createPhotoProject(path.join(dir,'missing'),missing),/brand/);
 const larger=await createPhotoProject(path.join(dir,'larger'),{...base,canvas:{width:1920,height:2400}},{dryRun:true});
 assert.equal(larger.document.canvas.width,1920);assert.equal(larger.layout.photo.width,1254);
});

test('explicit canvas background and reported photo edges; defaults unchanged',async t=>{
 const dir=await fixture(t),source=path.join(dir,'gradient.png'),width=700,height=600;
 // Vertical gradient #f6f6f6 -> #ffffff like a studio product shot.
 const bytes=Buffer.alloc(width*height*3);
 for(let y=0;y<height;y++){const v=246+Math.round(9*y/(height-1));bytes.fill(v,y*width*3,(y+1)*width*3);}
 await sharp(bytes,{raw:{width,height,channels:3}}).png().toFile(source);
 const base={project_id:'bg',source,headline:'轻透无瑕',brand:'CHANEL'};
 for(const template of ['brand-detail','xiaohongshu-cover',undefined]){
  const brief=template?{...base,template}:base;
  const plain=await createPhotoProject(path.join(dir,`plain-${template}`),brief,{dryRun:true});
  assert.equal(plain.document.canvas.background,template?'#f5f2eb':'#ffffff');
  const white=await createPhotoProject(path.join(dir,`white-${template}`),{...brief,background:'#ffffff'},{dryRun:true});
  assert.equal(white.document.canvas.background,'#ffffff');
  assert.deepEqual(white.layout.photo_edges.top,{mean:'#f6f6f6',spread:0});
  assert.deepEqual(white.layout.photo_edges.bottom,{mean:'#ffffff',spread:0});
  assert.equal(white.layout.photo_edges.left.spread,9);
 }
 await assert.rejects(createPhotoProject(path.join(dir,'bad'),{...base,background:'white'},{dryRun:true}),/#RRGGBB/);
});
