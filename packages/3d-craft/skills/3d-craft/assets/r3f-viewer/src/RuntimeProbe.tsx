import { useCallback, useEffect, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import type { WebGLRenderer } from 'three'
import {
  currentSnapshot,
  noteResourceSample,
  publishSnapshot,
  resetResourceSamples,
  type PerformanceProfileSnapshot,
  type PerformanceProfileStatus,
  type RendererMetrics,
  type SceneFacts,
  type ViewerStatus,
} from './observability'

export const PERFORMANCE_WARMUP_MS = 3_000
export const PERFORMANCE_SAMPLE_MS = 10_000
export const RESOURCE_SETTLE_FRAMES = 6

interface MutablePerformanceProfile {
  status: PerformanceProfileStatus
  startedAt: number | null
  sampleStartedAt: number | null
  completedAt: number | null
  sampleFrames: number[]
  lastSampleFrame: number | null
  viewport: [number, number]
  dpr: number
  rendererPeak: RendererMetrics
  invalidReason: string | null
}

interface RuntimeProbeProps {
  assetUrl: string
  assetSha256: string
  facts: SceneFacts
  status: ViewerStatus
  error: string
}

function emptyRendererMetrics(): RendererMetrics {
  return { calls: 0, triangles: 0, geometries: 0, textures: 0 }
}

function createIdleProfile(): MutablePerformanceProfile {
  return {
    status: 'idle',
    startedAt: null,
    sampleStartedAt: null,
    completedAt: null,
    sampleFrames: [],
    lastSampleFrame: null,
    viewport: [0, 0],
    dpr: 0,
    rendererPeak: emptyRendererMetrics(),
    invalidReason: null,
  }
}

function readRendererMetrics(gl: WebGLRenderer): RendererMetrics {
  return {
    calls: gl.info.render.calls,
    triangles: gl.info.render.triangles,
    geometries: gl.info.memory.geometries,
    textures: gl.info.memory.textures,
  }
}

function readPageViewport(): { viewport: [number, number]; dpr: number } {
  return {
    viewport: [window.innerWidth, window.innerHeight],
    dpr: window.devicePixelRatio,
  }
}

function percentile(values: number[], fraction: number): number | null {
  if (!values.length) return null
  const sorted = [...values].sort((a, b) => a - b)
  return sorted[Math.max(0, Math.ceil(sorted.length * fraction) - 1)]
}

function activeProfile(status: PerformanceProfileStatus): boolean {
  return status === 'warming' || status === 'sampling'
}

function freezeProfile(profile: MutablePerformanceProfile): Readonly<PerformanceProfileSnapshot> {
  return Object.freeze({
    status: profile.status,
    source: 'viewer-observability' as const,
    warmup_ms: PERFORMANCE_WARMUP_MS,
    sample_ms: PERFORMANCE_SAMPLE_MS,
    started_at_ms: profile.startedAt,
    sample_started_at_ms: profile.sampleStartedAt,
    completed_at_ms: profile.completedAt,
    sample_count: profile.sampleFrames.length,
    viewport: Object.freeze([...profile.viewport]) as readonly [number, number],
    device_pixel_ratio: profile.dpr,
    visibility_state: document.visibilityState,
    frame_p50_ms: percentile(profile.sampleFrames, 0.5),
    frame_p95_ms: percentile(profile.sampleFrames, 0.95),
    renderer_peak: Object.freeze({ ...profile.rendererPeak }),
    invalid_reason: profile.invalidReason,
  })
}

function invalidateProfile(profile: MutablePerformanceProfile, reason: string, now: number): boolean {
  if (!activeProfile(profile.status)) return false
  profile.status = 'invalid'
  profile.completedAt = now
  profile.invalidReason = reason
  return true
}

export function RuntimeProbe({ assetUrl, assetSha256, facts, status, error }: RuntimeProbeProps) {
  const { camera, gl, size, viewport } = useThree()
  const rollingFrames = useRef<number[]>([])
  const lastFrame = useRef<number | null>(null)
  const frameCount = useRef(currentSnapshot()?.raf.frame_count ?? 0)
  const lastPublish = useRef(0)
  const profile = useRef<MutablePerformanceProfile>(createIdleProfile())
  const statusRef = useRef(status)
  const settledReadyFrames = useRef(0)
  const sampledMount = useRef(currentSnapshot()?.lifecycle.mounts ?? 0)
  const lastResourceMetrics = useRef<{ geometries: number; textures: number } | null>(null)
  statusRef.current = status

  const publishRuntimeSnapshot = useCallback((now: number) => {
    const renderer = readRendererMetrics(gl)
    publishSnapshot({
      status: statusRef.current,
      asset: Object.freeze({ url: assetUrl, sha256: assetSha256 }),
      viewport: Object.freeze({ width: size.width, height: size.height, dpr: viewport.dpr }),
      scene: Object.freeze({
        ...facts,
        dimensions: Object.freeze([...facts.dimensions]) as unknown as [number, number, number],
        nodeNames: Object.freeze([...facts.nodeNames]) as unknown as string[],
        materialNames: Object.freeze([...facts.materialNames]) as unknown as string[],
        camera_position: Object.freeze(camera.position.toArray()) as unknown as [number, number, number],
      }),
      renderer: Object.freeze(renderer),
      raf: Object.freeze({
        status: 'running',
        frame_count: frameCount.current,
        last_frame_at_ms: lastFrame.current ?? now,
        frame_p50_ms: percentile(rollingFrames.current, 0.5),
        frame_p95_ms: percentile(rollingFrames.current, 0.95),
      }),
      performance_profile: freezeProfile(profile.current),
      error: error ? Object.freeze({ message: error }) : null,
    })
  }, [assetSha256, assetUrl, camera, error, facts, gl, size.height, size.width, viewport.dpr])

  useEffect(() => {
    const current = profile.current
    if (status !== 'ready' && invalidateProfile(current, `viewer status changed to ${status}`, performance.now())) {
      publishRuntimeSnapshot(performance.now())
    }
  }, [publishRuntimeSnapshot, status])

  useEffect(() => {
    if (!(import.meta.env.DEV || import.meta.env.MODE === 'test')) return
    const startPerformanceProfile = () => {
      const now = performance.now()
      const next = createIdleProfile()
      const page = readPageViewport()
      next.startedAt = now
      next.viewport = page.viewport
      next.dpr = page.dpr
      if (statusRef.current !== 'ready') {
        next.status = 'invalid'
        next.completedAt = now
        next.invalidReason = `viewer status is ${statusRef.current}`
      } else if (document.visibilityState !== 'visible') {
        next.status = 'invalid'
        next.completedAt = now
        next.invalidReason = `document visibility is ${document.visibilityState}`
      } else {
        next.status = 'warming'
      }
      profile.current = next
      publishRuntimeSnapshot(now)
    }
    const resetResources = () => {
      settledReadyFrames.current = 0
      sampledMount.current = currentSnapshot()?.lifecycle.mounts ?? sampledMount.current
      lastResourceMetrics.current = null
      resetResourceSamples()
      publishRuntimeSnapshot(performance.now())
    }
    const handleVisibility = () => {
      const now = performance.now()
      if (document.visibilityState !== 'visible' && invalidateProfile(
        profile.current,
        `document visibility changed to ${document.visibilityState}`,
        now,
      )) {
        publishRuntimeSnapshot(now)
      }
    }
    window.addEventListener('3d-craft:test-performance-start', startPerformanceProfile)
    window.addEventListener('3d-craft:test-resource-samples-reset', resetResources)
    document.addEventListener('visibilitychange', handleVisibility)
    return () => {
      window.removeEventListener('3d-craft:test-performance-start', startPerformanceProfile)
      window.removeEventListener('3d-craft:test-resource-samples-reset', resetResources)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [publishRuntimeSnapshot, size.height, size.width, viewport.dpr])

  useFrame(() => {
    const now = performance.now()
    const renderer = readRendererMetrics(gl)
    frameCount.current += 1
    if (lastFrame.current !== null) {
      rollingFrames.current.push(now - lastFrame.current)
      if (rollingFrames.current.length > 720) rollingFrames.current.shift()
    }
    lastFrame.current = now

    if (statusRef.current === 'ready') {
      const mounts = currentSnapshot()?.lifecycle.mounts ?? 0
      if (mounts !== sampledMount.current) {
        sampledMount.current = mounts
        settledReadyFrames.current = 0
        lastResourceMetrics.current = null
      }
      const resourcesUnchanged = lastResourceMetrics.current?.geometries === renderer.geometries
        && lastResourceMetrics.current?.textures === renderer.textures
      settledReadyFrames.current = resourcesUnchanged ? settledReadyFrames.current + 1 : 1
      lastResourceMetrics.current = { geometries: renderer.geometries, textures: renderer.textures }
      if (settledReadyFrames.current >= RESOURCE_SETTLE_FRAMES) noteResourceSample(renderer, now)
    } else {
      settledReadyFrames.current = 0
      lastResourceMetrics.current = null
    }

    const current = profile.current
    let publishImmediately = false
    if (activeProfile(current.status)) {
      const page = readPageViewport()
      const viewportChanged = current.viewport[0] !== page.viewport[0]
        || current.viewport[1] !== page.viewport[1]
        || current.dpr !== page.dpr
      if (document.visibilityState !== 'visible') {
        publishImmediately = invalidateProfile(current, `document visibility is ${document.visibilityState}`, now)
      } else if (statusRef.current !== 'ready') {
        publishImmediately = invalidateProfile(current, `viewer status is ${statusRef.current}`, now)
      } else if (viewportChanged) {
        publishImmediately = invalidateProfile(current, 'viewport or device pixel ratio changed during profiling', now)
      } else if (current.status === 'warming' && current.startedAt !== null && now - current.startedAt >= PERFORMANCE_WARMUP_MS) {
        current.status = 'sampling'
        current.sampleStartedAt = now
        current.lastSampleFrame = now
        current.rendererPeak = renderer
        publishImmediately = true
      } else if (current.status === 'sampling' && current.sampleStartedAt !== null) {
        if (current.lastSampleFrame !== null) current.sampleFrames.push(now - current.lastSampleFrame)
        current.lastSampleFrame = now
        current.rendererPeak = {
          calls: Math.max(current.rendererPeak.calls, renderer.calls),
          triangles: Math.max(current.rendererPeak.triangles, renderer.triangles),
          geometries: Math.max(current.rendererPeak.geometries, renderer.geometries),
          textures: Math.max(current.rendererPeak.textures, renderer.textures),
        }
        if (now - current.sampleStartedAt >= PERFORMANCE_SAMPLE_MS && current.sampleFrames.length > 0) {
          current.status = 'complete'
          current.completedAt = now
          publishImmediately = true
        }
      }
    }

    if (!publishImmediately && now - lastPublish.current < 250) return
    lastPublish.current = now
    publishRuntimeSnapshot(now)
  })

  return null
}
