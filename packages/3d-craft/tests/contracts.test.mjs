import assert from 'node:assert/strict'
import Ajv2020 from 'ajv/dist/2020.js'
import addFormats from 'ajv-formats'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

test('all seven schemas validate complete contracts and reject nested drift', async () => {
  const names = ['run.v1.schema.json', 'scene.v1.schema.json', 'asset.v1.schema.json', 'validation.v1.schema.json', 'browser-runtime.v1.schema.json', 'browser-runtime-draft.v1.schema.json', 'web-profile-observation.v1.schema.json']
  const schemas = await Promise.all(names.map(async (name) => JSON.parse(await readFile(path.join(root, 'skills/3d-craft/schemas', name), 'utf8'))))
  assert.equal(new Set(schemas.map((schema) => schema.$id)).size, 7)
  const ajv = new Ajv2020({ allErrors: true, strict: true })
  addFormats(ajv)
  for (const schema of schemas) {
    assert.equal(schema.additionalProperties, false)
    ajv.addSchema(schema)
  }
  const scene = JSON.parse(await readFile(path.join(root, 'evals/coffee-grinder/scene.json'), 'utf8'))
  const validateScene = ajv.getSchema('https://3d-craft.local/schemas/scene.v1.schema.json')
  assert.equal(validateScene(scene), true, JSON.stringify(validateScene.errors))

  const hash = 'a'.repeat(64)
  const route = {
    schema: '3d-craft.route.v1',
    target: 'blender',
    intent: 'validate',
    profile: 'prop',
    quality_tier: 'draft',
    authoring_mode: 'native',
    evidence_level: 'static',
    selected_references: ['authority-and-evidence.md', 'repair-and-security.md', 'blender-production.md'],
    required_capabilities: ['blender.version', 'blender.inspect'],
    hard_gates: ['authority', 'reproduction', 'scene_integrity', 'identity', 'delivery'],
    unsupported_in_v0_1: ['reference-image-reconstruction', 'character-production', 'complex-animation-and-simulation', 'games', 'webgpu', 'external-ai-3d-generation'],
  }
  const run = {
    schema: '3d-craft.run.v1',
    run_id: 'fixture-0001',
    project_key: 'fixture',
    created_at: '2026-09-02T00:00:00Z',
    input_hashes: { scene_contract: hash },
    route,
    capabilities: { 'blender.version': 'available', 'blender.inspect': 'available' },
    versions: { '3d-craft': '0.1.0' },
    stages: route.hard_gates.map((id) => ({ id, status: 'pending' })),
    repairs: [],
    evidence: [{ kind: 'blend-inspection', path: 'evidence/blend-inspection.json' }],
    unverified: [],
  }
  const asset = {
    schema: '3d-craft.asset.v1',
    authority: 'native',
    source: { path: '/tmp/source.blend', sha256: hash, bytes: 1 },
    derived: [{ path: '/tmp/asset.blend', sha256: hash, bytes: 1 }],
    tool_versions: { blender: '5.2.1' },
    licenses: [{ subject: 'fixture', license: 'MIT', source: 'original' }],
    gltf_summary: { nodes: 0, meshes: 0, primitives: 0, materials: 0, textures: 0, animations: 0, triangles: 0, extensions: [] },
  }
  const validation = {
    schema: '3d-craft.validation.v1',
    candidate_sha256: hash,
    status: 'PASS',
    gates: [{ id: 'authority', status: 'PASS', evidence: ['run.json'], note: 'bound' }],
    evidence: ['run.json'],
    issues: [],
    repairs: [],
    delivery: { files: [{ path: '/tmp/asset.blend', sha256: hash, bytes: 1 }], commands: ['validate'], unverified: [] },
  }
  for (const [id, document] of [
    ['https://3d-craft.local/schemas/run.v1.schema.json', run],
    ['https://3d-craft.local/schemas/asset.v1.schema.json', asset],
    ['https://3d-craft.local/schemas/validation.v1.schema.json', validation],
  ]) {
    const validate = ajv.getSchema(id)
    assert.equal(validate(document), true, JSON.stringify(validate.errors))
  }

  const browser = {
    schema: '3d-craft.browser-runtime.v1',
    status: 'ready',
    runtime: 'browser67',
    console_errors: 0,
    asset: { sha256: hash, bytes: 3, url: '/asset.glb' },
    network: { status: 'PASS', bytes: 3, sha256: hash },
    raf: { delta: 10 },
    metrics: { draw_calls: 1, textures: 0, frame_p50_ms: 7, frame_p95_ms: 8, geometries: 2, triangles: 3 },
    performance_profile: {
      test_status: 'PASS',
      source: 'viewer-observability',
      warmup_ms: 3000,
      sample_ms: 10000,
      started_at_ms: 100,
      sample_started_at_ms: 3100,
      completed_at_ms: 13100,
      sample_count: 600,
      viewport: [1440, 900],
      device_pixel_ratio: 1,
      visibility_state: 'visible',
      frame_p50_ms: 7,
      frame_p95_ms: 8,
      renderer_peak: { draw_calls: 1, triangles: 3, geometries: 2, textures: 0 },
    },
    lifecycle: {
      remount_test_status: 'PASS',
      ready_after_clean_reload: true,
      context_loss: {
        test_status: 'PASS',
        supported: true,
        losses: 1,
        restores: 1,
        ready_after_restore: true,
        raf_resumed_after_restore: true,
      },
      resource_stability: {
        test_status: 'PASS',
        source: 'viewer-observability',
        cycles: 3,
        samples: [
          { mounts: 1, disposes: 0, geometries: 2, textures: 0, captured_at_ms: 14000 },
          { mounts: 2, disposes: 1, geometries: 2, textures: 0, captured_at_ms: 15000 },
          { mounts: 3, disposes: 2, geometries: 2, textures: 0, captured_at_ms: 16000 },
          { mounts: 4, disposes: 3, geometries: 2, textures: 0, captured_at_ms: 17000 },
        ],
        geometry_delta: 0,
        texture_delta: 0,
      },
    },
    cross_runtime: { required_node_coverage_percent: 100, bbox_drift_percent: 0.1 },
    desktop_screenshot: { path: '/tmp/desktop.png', sha256: hash, bytes: 1, visual_review: 'PASS' },
    responsive_layout: { status: 'PASS', horizontal_overflow: false },
    warnings: [],
    unverified: [],
  }
  const validateBrowser = ajv.getSchema('https://3d-craft.local/schemas/browser-runtime.v1.schema.json')
  assert.equal(validateBrowser(browser), true, JSON.stringify(validateBrowser.errors))
  const contradictoryContextRecovery = structuredClone(browser)
  contradictoryContextRecovery.lifecycle.context_loss.restores = 0
  assert.equal(validateBrowser(contradictoryContextRecovery), false)
  const hiddenPerformanceProfile = structuredClone(browser)
  hiddenPerformanceProfile.performance_profile.visibility_state = 'hidden'
  assert.equal(validateBrowser(hiddenPerformanceProfile), false)
  const shortResourceProfile = structuredClone(browser)
  shortResourceProfile.lifecycle.resource_stability.cycles = 2
  assert.equal(validateBrowser(shortResourceProfile), false)
  const negativeResourceDelta = structuredClone(browser)
  negativeResourceDelta.lifecycle.resource_stability.geometry_delta = -1
  assert.equal(validateBrowser(negativeResourceDelta), false)
  browser.runtime = 'generic-browser'
  assert.equal(validateBrowser(browser), false)
  const blockedBrowser = structuredClone(browser)
  blockedBrowser.runtime = 'browser67'
  blockedBrowser.status = 'BLOCKED'
  blockedBrowser.page_status = 'ready'
  blockedBrowser.blocker = 'browser.capture timed out'
  delete blockedBrowser.desktop_screenshot
  assert.equal(validateBrowser(blockedBrowser), true, JSON.stringify(validateBrowser.errors))

  const browserDraft = {
    schema: '3d-craft.browser-runtime-draft.v1',
    status: 'ready',
    asset_url: '/asset.glb',
    console_errors: 0,
    network: { status: 'PASS', bytes: 3, sha256: hash },
    raf: { delta: 10 },
    metrics: { draw_calls: 1, textures: 0, frame_p50_ms: 7, frame_p95_ms: 8, geometries: 2, triangles: 3 },
    performance_profile: {
      test_status: 'PASS',
      source: 'viewer-observability',
      warmup_ms: 3000,
      sample_ms: 10000,
      started_at_ms: 100,
      sample_started_at_ms: 3100,
      completed_at_ms: 13100,
      sample_count: 600,
      viewport: [1440, 900],
      device_pixel_ratio: 1,
      visibility_state: 'visible',
      frame_p50_ms: 7,
      frame_p95_ms: 8,
      renderer_peak: { draw_calls: 1, triangles: 3, geometries: 2, textures: 0 },
    },
    lifecycle: {
      remount_test_status: 'PASS',
      ready_after_clean_reload: true,
      context_loss: {
        test_status: 'PASS',
        supported: true,
        losses: 1,
        restores: 1,
        ready_after_restore: true,
        raf_resumed_after_restore: true,
      },
      resource_stability: {
        test_status: 'PASS',
        source: 'viewer-observability',
        cycles: 3,
        samples: [
          { mounts: 1, disposes: 0, geometries: 2, textures: 0, captured_at_ms: 14000 },
          { mounts: 2, disposes: 1, geometries: 2, textures: 0, captured_at_ms: 15000 },
          { mounts: 3, disposes: 2, geometries: 2, textures: 0, captured_at_ms: 16000 },
          { mounts: 4, disposes: 3, geometries: 2, textures: 0, captured_at_ms: 17000 },
        ],
        geometry_delta: 0,
        texture_delta: 0,
      },
    },
    cross_runtime: { required_node_coverage_percent: 100, bbox_drift_percent: 0.1 },
    desktop_screenshot: {
      source_path: '/tmp/browser67-desktop.png',
      css_viewport: [1440, 900],
      device_pixel_ratio: 1,
      capture_target: 'viewport',
      visibility_state: 'visible',
      horizontal_overflow: false,
      visual_review: 'PASS',
    },
    responsive_layout: { status: 'PASS', horizontal_overflow: false },
    warnings: [],
    unverified: [],
  }
  const validateBrowserDraft = ajv.getSchema('https://3d-craft.local/schemas/browser-runtime-draft.v1.schema.json')
  assert.equal(validateBrowserDraft(browserDraft), true, JSON.stringify(validateBrowserDraft.errors))
  browserDraft.desktop_screenshot.visibility_state = 'hidden'
  assert.equal(validateBrowserDraft(browserDraft), false)

  const profileObservation = {
    schema: '3d-craft.web-profile-observation.v1',
    status: 'PASS',
    source: 'viewer-observability',
    asset: { url: '/asset.glb', sha256: hash },
    page: { visibility_state: 'visible', viewport: [1440, 900], device_pixel_ratio: 1 },
    metrics: structuredClone(browser.metrics),
    performance_profile: structuredClone(browser.performance_profile),
    resource_stability: structuredClone(browser.lifecycle.resource_stability),
  }
  const validateProfileObservation = ajv.getSchema('https://3d-craft.local/schemas/web-profile-observation.v1.schema.json')
  assert.equal(validateProfileObservation(profileObservation), true, JSON.stringify(validateProfileObservation.errors))
  const hiddenProfileObservation = structuredClone(profileObservation)
  hiddenProfileObservation.page.visibility_state = 'hidden'
  assert.equal(validateProfileObservation(hiddenProfileObservation), false)
  const nestedFailedProfileObservation = structuredClone(profileObservation)
  nestedFailedProfileObservation.resource_stability = {
    test_status: 'FAIL',
    reason: 'resource counters did not settle',
  }
  assert.equal(validateProfileObservation(nestedFailedProfileObservation), false)
  const failedProfileObservation = {
    schema: '3d-craft.web-profile-observation.v1',
    status: 'FAIL',
    source: 'viewer-observability',
    reason: 'document visibility changed to hidden',
  }
  assert.equal(validateProfileObservation(failedProfileObservation), true, JSON.stringify(validateProfileObservation.errors))
  delete failedProfileObservation.reason
  assert.equal(validateProfileObservation(failedProfileObservation), false)

  const linkedBrowserDraft = structuredClone(browserDraft)
  linkedBrowserDraft.desktop_screenshot.visibility_state = 'visible'
  delete linkedBrowserDraft.metrics
  delete linkedBrowserDraft.performance_profile
  delete linkedBrowserDraft.lifecycle.resource_stability
  linkedBrowserDraft.profile_observation_path = '/tmp/web-profile-observation.json'
  assert.equal(validateBrowserDraft(linkedBrowserDraft), true, JSON.stringify(validateBrowserDraft.errors))
  linkedBrowserDraft.metrics = structuredClone(profileObservation.metrics)
  assert.equal(validateBrowserDraft(linkedBrowserDraft), false)

  const driftedScene = structuredClone(scene)
  driftedScene.runtime.credential = 'must-not-be-accepted'
  assert.equal(validateScene(driftedScene), false)

  const customOrigin = structuredClone(scene)
  customOrigin.origin_policy = 'declared-custom'
  assert.equal(validateScene(customOrigin), false)
  customOrigin.framing_center = [0, 0, 0.16]
  assert.equal(validateScene(customOrigin), true, JSON.stringify(validateScene.errors))
})

test('skill entrypoint separates explanation-only requests, route-applicable work, and failed-gate repair', async () => {
  const skill = await readFile(path.join(root, 'skills/3d-craft/SKILL.md'), 'utf8')
  const repair = await readFile(path.join(root, 'skills/3d-craft/references/repair-and-security.md'), 'utf8')
  assert.match(skill, /Explanation-only questions/)
  assert.match(skill, /Do not start the production loop/)
  assert.match(skill, /Run only the stages selected by the route/)
  assert.match(skill, /At the first failed hard gate, stop downstream\s+stages and completion claims/)
  assert.match(repair, /Rerun the failed evidence and every receipt invalidated/)
  assert.match(repair, /After three unsuccessful attempts/)
})

test('viewer pins the validated R3F stack, splits dependency chunks, and keeps observability development-only', async () => {
  const viewer = path.join(root, 'skills/3d-craft/assets/r3f-viewer')
  const packageJson = JSON.parse(await readFile(path.join(viewer, 'package.json'), 'utf8'))
  const packageLock = JSON.parse(await readFile(path.join(viewer, 'package-lock.json'), 'utf8'))
  assert.equal(packageJson.dependencies.react, '19.2.8')
  assert.equal(packageJson.dependencies['@react-three/fiber'], '9.7.0')
  assert.equal(packageJson.dependencies['@react-three/drei'], '10.7.8')
  assert.equal(packageJson.dependencies.three, '0.185.1')
  assert.deepEqual(packageLock.packages[''].dependencies, packageJson.dependencies)
  assert.deepEqual(packageLock.packages[''].devDependencies, packageJson.devDependencies)
  const observability = await readFile(path.join(viewer, 'src/observability.ts'), 'utf8')
  const assetScene = await readFile(path.join(viewer, 'src/AssetScene.tsx'), 'utf8')
  const runtimeProbe = await readFile(path.join(viewer, 'src/RuntimeProbe.tsx'), 'utf8')
  const profileOrchestrator = await readFile(path.join(viewer, 'src/ProfileOrchestrator.tsx'), 'utf8')
  const app = await readFile(path.join(viewer, 'src/App.tsx'), 'utf8')
  const viteConfig = await readFile(path.join(viewer, 'vite.config.ts'), 'utf8')
  const runtimeQa = await readFile(path.join(root, 'skills/3d-craft/references/web3d-runtime-qa.md'), 'utf8')
  assert.match(observability, /import\.meta\.env\.DEV/)
  assert.match(observability, /Object\.freeze/)
  assert.match(assetScene, /DISPLAY_MAX_DIMENSION_METERS/)
  assert.match(assetScene, /maximumDimension <= 0/)
  assert.match(assetScene, /displayRoot\.scale\.setScalar/)
  assert.match(assetScene, /const disposedTextures = new Set<Texture>/)
  assert.match(assetScene, /loadedRoot = displayRoot\s+noteMount\(\)/)
  assert.match(runtimeProbe, /nodeNames: Object\.freeze/)
  assert.match(runtimeProbe, /materialNames: Object\.freeze/)
  assert.match(assetScene, /webglcontextlost/)
  assert.match(assetScene, /webglcontextrestored/)
  assert.match(assetScene, /3d-craft:test-context-loss/)
  assert.match(assetScene, /queueMicrotask/)
  assert.match(assetScene, /enabled=\{status === 'ready'\}/)
  assert.match(assetScene, /key=\{assetGeneration\}/)
  assert.match(observability, /status: 'idle' \| 'running'/)
  assert.match(observability, /test_supported/)
  assert.match(observability, /resource_samples/)
  assert.match(runtimeProbe, /PERFORMANCE_WARMUP_MS = 3_000/)
  assert.match(runtimeProbe, /PERFORMANCE_SAMPLE_MS = 10_000/)
  assert.match(runtimeProbe, /RESOURCE_SETTLE_FRAMES = 6/)
  assert.match(runtimeProbe, /3d-craft:test-performance-start/)
  assert.match(runtimeProbe, /3d-craft:test-resource-samples-reset/)
  assert.match(runtimeProbe, /document\.visibilityState/)
  assert.match(runtimeProbe, /viewport or device pixel ratio changed during profiling/)
  assert.match(runtimeProbe, /mounts !== sampledMount\.current/)
  assert.match(profileOrchestrator, /__THREE_D_CRAFT_TEST__/)
  assert.match(profileOrchestrator, /runPerformanceAndResourceProfile/)
  assert.match(profileOrchestrator, /DEFAULT_RESOURCE_CYCLES = 3/)
  assert.match(profileOrchestrator, /3d-craft\.web-profile-observation\.v1/)
  assert.match(profileOrchestrator, /document\.visibilityState/)
  assert.match(profileOrchestrator, /VITE_ASSET_SHA256 is not a verified SHA-256/)
  assert.match(app, /motion.*reduce/)
  assert.match(app, /forcedReducedMotion \|\| media\.matches/)
  assert.match(app, /import\('\.\/AssetScene'\)/)
  assert.match(app, /The 3D runtime could not be loaded/)
  assert.match(app, /status === 'error' && error/)
  assert.match(viteConfig, /chunkSizeWarningLimit: 800/)
  for (const chunk of ['react-runtime', 'three-runtime', 'r3f-runtime', 'vendor']) {
    assert.match(viteConfig, new RegExp(`name: '${chunk}'`))
  }
  assert.match(runtimeQa, /readiness stimulus, not visual acceptance/)
  assert.match(runtimeQa, /visibilityState.*remains `hidden`/)
  assert.match(runtimeQa, /`INVALID SAMPLE`/)
  assert.match(runtimeQa, /absence in production is expected/)
  assert.match(runtimeQa, /Context-loss evidence/)
  assert.match(runtimeQa, /3d-craft:test-performance-start/)
  assert.match(runtimeQa, /3d-craft:test-resource-samples-reset/)
  assert.match(runtimeQa, /Old V0\.1 scenes without this nested budget remain readable/)
})
