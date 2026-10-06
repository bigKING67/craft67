import { useEffect } from 'react'
import type {
  PerformanceProfileSnapshot,
  ResourceSample,
  ThreeDCraftSnapshot,
} from './observability'

const DEFAULT_RESOURCE_CYCLES = 3
const MIN_RESOURCE_CYCLES = 3
const MAX_RESOURCE_CYCLES = 7
const DEFAULT_TIMEOUT_MS = 60_000
const MIN_TIMEOUT_MS = 20_000
const MAX_TIMEOUT_MS = 120_000
const POLL_MS = 50
const SHA256_PATTERN = /^[a-f0-9]{64}$/

interface ProfileOptions {
  resource_cycles?: number
  timeout_ms?: number
}

interface ReceiptRendererMetrics {
  draw_calls: number
  triangles: number
  geometries: number
  textures: number
}

interface ReceiptPerformanceProfile {
  test_status: 'PASS'
  source: 'viewer-observability'
  warmup_ms: number
  sample_ms: number
  started_at_ms: number
  sample_started_at_ms: number
  completed_at_ms: number
  sample_count: number
  viewport: [number, number]
  device_pixel_ratio: number
  visibility_state: 'visible'
  frame_p50_ms: number
  frame_p95_ms: number
  renderer_peak: ReceiptRendererMetrics
}

interface ReceiptResourceStability {
  test_status: 'PASS'
  source: 'viewer-observability'
  cycles: number
  samples: ResourceSample[]
  geometry_delta: number
  texture_delta: number
}

interface PassingProfileObservation {
  schema: '3d-craft.web-profile-observation.v1'
  status: 'PASS'
  source: 'viewer-observability'
  asset: { url: string; sha256: string }
  page: {
    visibility_state: 'visible'
    viewport: [number, number]
    device_pixel_ratio: number
  }
  metrics: ReceiptRendererMetrics & { frame_p50_ms: number; frame_p95_ms: number }
  performance_profile: ReceiptPerformanceProfile
  resource_stability: ReceiptResourceStability
}

interface FailingProfileObservation {
  schema: '3d-craft.web-profile-observation.v1'
  status: 'FAIL'
  source: 'viewer-observability'
  reason: string
}

export type WebProfileObservation = Readonly<PassingProfileObservation | FailingProfileObservation>

interface ThreeDCraftTestControls {
  readonly schema: '3d-craft.web-profile-controls.v1'
  readonly runPerformanceAndResourceProfile: (
    options?: ProfileOptions,
  ) => Promise<WebProfileObservation>
}

declare global {
  interface Window {
    __THREE_D_CRAFT_TEST__?: ThreeDCraftTestControls
  }
}

function deepFreeze<T>(value: T): Readonly<T> {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const nested of Object.values(value)) deepFreeze(nested)
    Object.freeze(value)
  }
  return value
}

function fail(reason: string): WebProfileObservation {
  return deepFreeze({
    schema: '3d-craft.web-profile-observation.v1' as const,
    status: 'FAIL' as const,
    source: 'viewer-observability' as const,
    reason,
  })
}

function readReadySnapshot(): ThreeDCraftSnapshot {
  const snapshot = window.__THREE_D_CRAFT__
  if (!snapshot) throw new Error('viewer observability is unavailable')
  if (document.visibilityState !== 'visible') {
    throw new Error(`document visibility is ${document.visibilityState}`)
  }
  if (snapshot.status !== 'ready') throw new Error(`viewer status is ${snapshot.status}`)
  if (!SHA256_PATTERN.test(snapshot.asset.sha256)) {
    throw new Error('VITE_ASSET_SHA256 is not a verified SHA-256')
  }
  return snapshot
}

function normalizedOptions(options: ProfileOptions = {}): Required<ProfileOptions> {
  const resourceCycles = options.resource_cycles ?? DEFAULT_RESOURCE_CYCLES
  const timeoutMs = options.timeout_ms ?? DEFAULT_TIMEOUT_MS
  if (!Number.isInteger(resourceCycles) || resourceCycles < MIN_RESOURCE_CYCLES || resourceCycles > MAX_RESOURCE_CYCLES) {
    throw new Error(`resource_cycles must be an integer from ${MIN_RESOURCE_CYCLES} to ${MAX_RESOURCE_CYCLES}`)
  }
  if (!Number.isInteger(timeoutMs) || timeoutMs < MIN_TIMEOUT_MS || timeoutMs > MAX_TIMEOUT_MS) {
    throw new Error(`timeout_ms must be an integer from ${MIN_TIMEOUT_MS} to ${MAX_TIMEOUT_MS}`)
  }
  return { resource_cycles: resourceCycles, timeout_ms: timeoutMs }
}

async function waitForSnapshot(
  description: string,
  deadline: number,
  predicate: (snapshot: ThreeDCraftSnapshot) => boolean,
): Promise<ThreeDCraftSnapshot> {
  while (performance.now() <= deadline) {
    if (document.visibilityState !== 'visible') {
      throw new Error(`document visibility changed to ${document.visibilityState} while waiting for ${description}`)
    }
    const snapshot = window.__THREE_D_CRAFT__
    if (!snapshot) throw new Error('viewer observability disappeared during profiling')
    if (snapshot.status === 'error' || snapshot.status === 'context-lost' || snapshot.status === 'restoring') {
      throw new Error(`viewer status changed to ${snapshot.status} while waiting for ${description}`)
    }
    if (predicate(snapshot)) return snapshot
    await new Promise<void>((resolve) => window.setTimeout(resolve, POLL_MS))
  }
  throw new Error(`timed out waiting for ${description}`)
}

function receiptProfile(profile: Readonly<PerformanceProfileSnapshot>): ReceiptPerformanceProfile {
  if (
    profile.status !== 'complete'
    || profile.started_at_ms === null
    || profile.sample_started_at_ms === null
    || profile.completed_at_ms === null
    || profile.frame_p50_ms === null
    || profile.frame_p95_ms === null
    || profile.visibility_state !== 'visible'
  ) {
    throw new Error(profile.invalid_reason || `performance profile ended in ${profile.status}`)
  }
  return {
    test_status: 'PASS',
    source: profile.source,
    warmup_ms: profile.warmup_ms,
    sample_ms: profile.sample_ms,
    started_at_ms: profile.started_at_ms,
    sample_started_at_ms: profile.sample_started_at_ms,
    completed_at_ms: profile.completed_at_ms,
    sample_count: profile.sample_count,
    viewport: [...profile.viewport],
    device_pixel_ratio: profile.device_pixel_ratio,
    visibility_state: 'visible',
    frame_p50_ms: profile.frame_p50_ms,
    frame_p95_ms: profile.frame_p95_ms,
    renderer_peak: {
      draw_calls: profile.renderer_peak.calls,
      triangles: profile.renderer_peak.triangles,
      geometries: profile.renderer_peak.geometries,
      textures: profile.renderer_peak.textures,
    },
  }
}

async function collectProfile(options?: ProfileOptions): Promise<WebProfileObservation> {
  try {
    const normalized = normalizedOptions(options)
    const deadline = performance.now() + normalized.timeout_ms
    const initial = readReadySnapshot()

    window.dispatchEvent(new Event('3d-craft:test-performance-start'))
    const profiled = await waitForSnapshot(
      'the explicit performance sample',
      deadline,
      (snapshot) => ['complete', 'invalid'].includes(snapshot.performance_profile.status),
    )
    const performanceProfile = receiptProfile(profiled.performance_profile)

    window.dispatchEvent(new Event('3d-craft:test-resource-samples-reset'))
    const baselineSnapshot = await waitForSnapshot(
      'the settled resource baseline',
      deadline,
      (snapshot) => snapshot.status === 'ready'
        && snapshot.lifecycle.resource_samples.length === 1
        && snapshot.lifecycle.resource_samples[0].mounts === snapshot.lifecycle.mounts,
    )
    let previous = baselineSnapshot.lifecycle.resource_samples[0]

    for (let cycle = 0; cycle < normalized.resource_cycles; cycle += 1) {
      window.dispatchEvent(new Event('3d-craft:test-remount'))
      const nextSnapshot = await waitForSnapshot(
        `settled resource reload ${cycle + 1}`,
        deadline,
        (snapshot) => {
          const samples = snapshot.lifecycle.resource_samples
          const next = samples.at(-1)
          return snapshot.status === 'ready'
            && samples.length === cycle + 2
            && Boolean(next)
            && next!.mounts === previous.mounts + 1
            && next!.disposes > previous.disposes
        },
      )
      previous = nextSnapshot.lifecycle.resource_samples.at(-1)!
    }

    const finalSnapshot = readReadySnapshot()
    const samples = finalSnapshot.lifecycle.resource_samples.map((sample) => ({ ...sample }))
    if (samples.length !== normalized.resource_cycles + 1) {
      throw new Error('resource sample count changed before closeout')
    }
    const baseline = samples[0]
    const final = samples.at(-1)!
    const geometryDelta = final.geometries - baseline.geometries
    const textureDelta = final.textures - baseline.textures
    if (geometryDelta < 0 || textureDelta < 0) {
      throw new Error('settled resource counters decreased; the observation is not comparable')
    }
    if (
      initial.asset.sha256 !== finalSnapshot.asset.sha256
      || initial.asset.url !== finalSnapshot.asset.url
    ) {
      throw new Error('asset identity changed during profiling')
    }

    const rendererPeak = performanceProfile.renderer_peak
    return deepFreeze({
      schema: '3d-craft.web-profile-observation.v1' as const,
      status: 'PASS' as const,
      source: 'viewer-observability' as const,
      asset: {
        url: finalSnapshot.asset.url,
        sha256: finalSnapshot.asset.sha256,
      },
      page: {
        visibility_state: 'visible' as const,
        viewport: [...performanceProfile.viewport] as [number, number],
        device_pixel_ratio: performanceProfile.device_pixel_ratio,
      },
      metrics: {
        ...rendererPeak,
        frame_p50_ms: performanceProfile.frame_p50_ms,
        frame_p95_ms: performanceProfile.frame_p95_ms,
      },
      performance_profile: performanceProfile,
      resource_stability: {
        test_status: 'PASS' as const,
        source: 'viewer-observability' as const,
        cycles: normalized.resource_cycles,
        samples,
        geometry_delta: geometryDelta,
        texture_delta: textureDelta,
      },
    })
  } catch (error) {
    return fail(error instanceof Error ? error.message : String(error))
  }
}

export function ProfileOrchestrator() {
  useEffect(() => {
    if (!(import.meta.env.DEV || import.meta.env.MODE === 'test')) return
    let running: Promise<WebProfileObservation> | null = null
    const controls: ThreeDCraftTestControls = Object.freeze({
      schema: '3d-craft.web-profile-controls.v1' as const,
      runPerformanceAndResourceProfile: (options?: ProfileOptions) => {
        if (!running) running = collectProfile(options).finally(() => { running = null })
        return running
      },
    })
    window.__THREE_D_CRAFT_TEST__ = controls
    return () => {
      if (window.__THREE_D_CRAFT_TEST__ === controls) delete window.__THREE_D_CRAFT_TEST__
    }
  }, [])

  return null
}
