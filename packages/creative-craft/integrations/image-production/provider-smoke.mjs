import * as fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomUUID } from 'node:crypto';
import assert from 'node:assert/strict';
import sharp from 'sharp';
import { demoInput } from './fixtures.mjs';
import { createProject, readProject, editBatch, encode } from './project.mjs';
import { executeProvider, checkProvider } from './provider.mjs';
import { acceptCandidate, compareCandidate } from './candidates.mjs';
import { renderProject } from './render.mjs';

// Never run in CI or by default: this script makes two authorized image POSTs.
if (process.argv.slice(2).join(' ') !== '--live') throw new Error('Live Provider smoke requires --live; makes at most two client POSTs, no retries');
const repository = fileURLToPath(new URL('../../', import.meta.url));
const parent = path.join(repository, 'dist'); await fs.mkdir(parent, { recursive: true });
const output = path.join(parent, `image-p1c-${new Date().toISOString().slice(0,10)}-${randomUUID().slice(0,8)}`); await fs.mkdir(output);
console.log(JSON.stringify({ phase: 'start', output, client_post_limit: 2 }));
const credentials = path.join(process.env.HOME, '.codex');
const configBefore = await fs.readFile(path.join(credentials, 'config.toml')), authBefore = await fs.readFile(path.join(credentials, 'auth.json'));
const root = path.join(output, 'project'); const events = [];
const save = (name, value) => fs.writeFile(path.join(output, name), encode(value));
const report = { status: 'PARTIAL', output, project: root, fixture: 'Real model output with synthetic product/logo and deliberate test leaf; no real product or Owner approval', provider_model: 'gpt-image-2.5-sunburst', events,
  actual_cost: 'UNVERIFIED', independent_agent: 'UNVERIFIED', pi_host: 'UNVERIFIED', visual_quality: 'UNVERIFIED' };
try {
  const check = await checkProvider(); await save('provider-check.json', check);
  assert.ok(check.models.find(m=>m.model===report.provider_model)?.advertised);
  const input = await demoInput(path.join(output, 'source-assets'));
  const bg = input.assets.find(a=>a.id==='background');
  const resized = await sharp(bg.source).resize(1024,1024).png().toBuffer();
  bg.source = path.join(output,'background-1024.png'); await fs.writeFile(bg.source,resized);
  input.canvas.width = input.canvas.height = 1024;
  Object.assign(input.objects.find(o=>o.id==='background'),{width:1024,height:1024});
  const created = await createProject(root,input);
  const template=JSON.parse(await fs.readFile(path.join(repository,'skills/creative-craft/templates/image-job.json')));
  const job=structuredClone(template);
  Object.assign(job,{job_id:'live-background',provider_profile:'openai.gpt-image-2.5-sunburst.2026-09-08',declared_status:'ready',intended_use:'Warm studio background for synthetic product poster integration smoke'});
  job.rights={status:'CLEARED',notes:'Original synthetic fixtures and original generated background; technical acceptance only.'};
  job.prompt={scene:'A warm cream and pale peach sunlit studio product-photography backdrop with a matte tabletop; a subtle soft abstract arch in the upper-right background.',subject:'Empty background only, no product or object on the tabletop.',composition:'Square 1024x1024. Quiet empty left half for typeset Chinese copy. Unoccupied right center for a separate product object. Keep lower-right tabletop smooth.',lighting:'Soft diffuse daylight from upper left; gentle natural shadows.',materials_style:'Restrained photographic studio materials, subtle natural texture, muted warm colors.',exact_text:[],references:[],change:[],preserve:[],constraints:['Background asset only; do not draw the product, title, price or logo.'],exclude:['Letters','Numbers','Logos','Watermarks','Plants','Bottles']};
  const jobPath=path.join(output,'background-job.json');await save('background-job.json',job);
  const spec={job:jobPath,candidate_id:'live-warm',base_revision:1,target_id:'background',references:[],output_policy:'resize_to_target'};await save('background-run.json',spec);
  const dry=await executeProvider(root,spec,{dryRun:true});await save('background-dry-run.json',dry);
  console.log(JSON.stringify({phase:'background-request',model:report.provider_model,quality:job.canvas.quality,size:job.canvas.size}));
  const generated=await executeProvider(root,spec);events.push({phase:'background',outcome:generated.receipt.outcome,receipt:generated.candidate.candidate.execution,usage:generated.receipt.parameters.usage});
  assert.equal((await readProject(root)).sha256,created.sha256);
  await compareCandidate(root,'live-warm',path.join(output,'compare-background'));
  console.log(JSON.stringify({phase:'background-candidate',compare:path.join(output,'compare-background/comparison.png'),accepted:false}));
  // The automated smoke follows a declared fixture decision; visual approval is separate.
  await acceptCandidate(root,{candidate_id:'live-warm',base_revision:1,author:'system',summary:'Technical smoke accepts the generated fixture background; visual quality unverified'});
  await editBatch(root,{base_revision:2,author:'human',summary:'Simulated human changes price to 149',operations:[{type:'update_object',id:'price',patch:{text:'¥149'}}]});
  const current=await readProject(root),currentAsset=current.document.assets.find(a=>a.id===current.document.objects.find(o=>o.id==='background').asset_id);
  const mark=Buffer.from('<svg width="1024" height="1024"><ellipse cx="940" cy="860" rx="23" ry="12" fill="#6e8161" transform="rotate(-25 940 860)"/><ellipse cx="929" cy="844" rx="17" ry="8" fill="#94a889" transform="rotate(30 929 844)"/></svg>');
  const markedFile=path.join(output,'background-with-test-leaf.png');await sharp(path.join(root,currentAsset.render_file)).composite([{input:mark}]).png().toFile(markedFile);
  await editBatch(root,{base_revision:3,author:'system',summary:'Add a deliberate local test leaf for controlled API-edit acceptance',operations:[{type:'add_asset',asset:{id:'marked-background',source:markedFile}},{type:'update_object',id:'background',patch:{asset_id:'marked-background'}}]});
  const beforeEdit=await renderProject(root,path.join(output,'before-local-edit'));
  const pixels=1024*1024,generation=Buffer.alloc(pixels),protection=Buffer.alloc(pixels),blend=Buffer.alloc(pixels);
  for(let y=0;y<1024;y++)for(let x=0;x<1024;x++){
    const at=y*1024+x; const distance=Math.hypot(x-940,y-858);
    if(distance<65)generation[at]=255;
    if(distance<55)blend[at]=Math.round(255*Math.min(1,(55-distance)/10));
    if((x>=580&&x<920&&y>=254&&y<802)||(x>=710&&x<890&&y>=64&&y<128))protection[at]=255;
  }
  const edit={context:{x:0,y:0,width:1024,height:1024}};
  for(const [name,data]of Object.entries({generation_mask:generation,protection_mask:protection,blend_mask:blend})){
    edit[name]=path.join(output,`${name}.png`);await sharp(data,{raw:{width:1024,height:1024,channels:1}}).toColourspace('b-w').png().toFile(edit[name]);
  }
  const editJob=structuredClone(job);Object.assign(editJob,{job_id:'live-local-edit',task_type:'edit',asset_refs:['marked-background'],intended_use:'Remove deliberate lower-right test leaf from generated background, preserve all other content'});
  editJob.prompt.subject='Existing studio background';editJob.prompt.references=[{asset_id:'marked-background',role:'Current background to edit',preserve:['Lighting','Composition','All areas outside the local leaf']}];
  editJob.prompt.change=['Remove the small green test leaf in the lower-right around x=940, y=858 and reconstruct the smooth tabletop beneath it.'];editJob.prompt.preserve=['Keep background lighting, texture and composition.','Do not add product, letters, price or logo.'];
  await save('edit-job.json',editJob);
  const editSpec={job:path.join(output,'edit-job.json'),candidate_id:'live-remove-leaf',base_revision:4,target_id:'background',references:[{asset_id:'marked-background',source:markedFile}],edit,output_policy:'resize_to_target'};await save('edit-run.json',editSpec);
  console.log(JSON.stringify({phase:'edit-request',client_post_limit:2}));
  const edited=await executeProvider(root,editSpec);events.push({phase:'edit',outcome:edited.receipt.outcome,receipt:edited.candidate.candidate.execution,usage:edited.receipt.parameters.usage});
  assert.equal(edited.candidate.candidate.qa.protected_changed_pixels,0);assert.equal(edited.candidate.candidate.qa.outside_blend_changed_pixels,0);
  report.protection_qa=edited.candidate.candidate.qa;
  await compareCandidate(root,'live-remove-leaf',path.join(output,'compare-local-edit'));
  await acceptCandidate(root,{candidate_id:'live-remove-leaf',base_revision:4,author:'system',summary:'Technical smoke accepts bounded model edit; visual quality unverified'});
  const accepted=await renderProject(root,path.join(output,'accepted-local-edit'));
  await editBatch(root,{base_revision:5,author:'human',summary:'Undo local edit',operations:[{type:'revert_to',revision:4}]});
  const undo=await renderProject(root,path.join(output,'undo')),reopen=await renderProject(root,path.join(output,'reopen'));
  assert.equal(undo.receipt.outputs.png.sha256,beforeEdit.receipt.outputs.png.sha256);assert.equal(reopen.receipt.outputs.png.sha256,undo.receipt.outputs.png.sha256);
  const final=await readProject(root);assert.equal(final.document.objects.find(o=>o.id==='price').text,'¥149');
  for(const obj of created.document.objects.filter(o=>!['background','price'].includes(o.id)))assert.deepEqual(final.document.objects.find(o=>o.id===obj.id),obj);
  report.status='PASS_TECHNICAL';report.final_revision=final.document.revision;report.accepted_png=accepted.receipt.outputs.png;report.undo_reopen_png=undo.receipt.outputs.png;
}catch(error){
  report.failure={message:error.message,receipt_outcome:error.receipt?.outcome??null,receipt_directory:error.output??null};process.exitCode=1;
}finally{
  report.global_config_unchanged=(await fs.readFile(path.join(credentials,'config.toml'))).equals(configBefore);
  report.auth_unchanged=(await fs.readFile(path.join(credentials,'auth.json'))).equals(authBefore);
  await save('smoke-report.json',report);console.log(JSON.stringify(report,null,2));
}
