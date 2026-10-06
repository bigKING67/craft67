import { useCallback, useEffect, useState } from 'react'
import type { SceneFacts, ViewerStatus } from './observability'
import { ProfileOrchestrator } from './ProfileOrchestrator'
import './styles.css'

type AssetSceneComponent = typeof import('./AssetScene')['AssetScene']

const assetUrl = import.meta.env.VITE_ASSET_URL || '/asset.glb'
const assetSha256 = import.meta.env.VITE_ASSET_SHA256 || 'unverified'
const assetName = import.meta.env.VITE_ASSET_NAME || '3D asset'
const assetDescription = import.meta.env.VITE_ASSET_DESCRIPTION || 'Product or prop candidate for evidence-backed Blender-to-web delivery.'
const forcedReducedMotion = new URLSearchParams(window.location.search).get('motion') === 'reduce'

function formatMillimeters(value: number): string {
  return value ? `${Math.round(value * 1000)} mm` : '—'
}

export default function App() {
  const [status, setStatus] = useState<ViewerStatus>('loading')
  const [error, setError] = useState('')
  const [facts, setFacts] = useState<SceneFacts>({ objects: 0, meshes: 0, materials: 0, dimensions: [0, 0, 0], nodeNames: [], materialNames: [] })
  const [reducedMotion, setReducedMotion] = useState(false)
  const [SceneRenderer, setSceneRenderer] = useState<AssetSceneComponent | null>(null)

  const handleStatus = useCallback((next: ViewerStatus, detail = '') => {
    setStatus(next)
    setError(detail)
  }, [])
  const handleFacts = useCallback((next: SceneFacts) => setFacts(next), [])

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReducedMotion(forcedReducedMotion || media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    let active = true
    import('./AssetScene')
      .then(({ AssetScene }) => {
        if (active) setSceneRenderer(() => AssetScene)
      })
      .catch((reason: unknown) => {
        if (!active) return
        const detail = reason instanceof Error ? reason.message : String(reason)
        handleStatus('error', `The 3D runtime could not be loaded: ${detail}`)
      })
    return () => {
      active = false
    }
  }, [handleStatus])

  const resetCamera = () => window.dispatchEvent(new Event('3d-craft:reset-camera'))

  return (
    <main className="viewer-shell">
      <ProfileOrchestrator />
      <aside className="evidence-rail" aria-label="Asset evidence summary">
        <div>
          <p className="eyebrow">3D-Craft / V0.1</p>
          <h1>{assetName}</h1>
          <p className="lede">{assetDescription}</p>
        </div>

        <section className="status-block" aria-live="polite">
          <div className={`status-chip status-${status}`}>
            <span aria-hidden="true" />
            {status}
          </div>
          <p>
            {status === 'loading' && 'Loading and inspecting asset.glb…'}
            {status === 'ready' && 'Asset loaded. Orbit, zoom, or reset the camera.'}
            {status === 'context-lost' && 'GPU context interrupted. Interaction is paused while the canvas waits to recover.'}
            {status === 'restoring' && 'GPU context restored. Rebuilding renderer resources and checking scene readiness…'}
            {status === 'error' && 'The GLB could not be displayed. Check the asset URL and console evidence.'}
          </p>
          {status === 'error' && error && <code className="error-copy">{error}</code>}
        </section>

        <dl className="metric-list">
          <div><dt>Objects</dt><dd>{facts.objects || '—'}</dd></div>
          <div><dt>Meshes</dt><dd>{facts.meshes || '—'}</dd></div>
          <div><dt>Materials</dt><dd>{facts.materials || '—'}</dd></div>
          <div><dt>Width</dt><dd>{formatMillimeters(facts.dimensions[0])}</dd></div>
          <div><dt>Depth</dt><dd>{formatMillimeters(facts.dimensions[1])}</dd></div>
          <div><dt>Height</dt><dd>{formatMillimeters(facts.dimensions[2])}</dd></div>
        </dl>

        <div className="asset-id">
          <span>Asset</span>
          <code title={assetSha256}>{assetSha256 === 'unverified' ? assetUrl : assetSha256.slice(0, 12)}</code>
        </div>
      </aside>

      <section className="viewport-panel" aria-label="Interactive 3D asset viewport">
        <div className="viewport-meta">
          <span>GLB / R3F 9.7 / THREE r185</span>
          <span>{reducedMotion ? 'Reduced motion' : 'Live orbit'}</span>
        </div>
        <div className="canvas-wrap">
          {SceneRenderer && (
            <SceneRenderer
              assetUrl={assetUrl}
              assetSha256={assetSha256}
              reducedMotion={reducedMotion}
              onStatus={handleStatus}
              onFacts={handleFacts}
            />
          )}
          {status === 'loading' && <div className="loading-mark" aria-hidden="true" />}
          {(status === 'context-lost' || status === 'restoring') && (
            <div className="context-notice" aria-hidden="true">
              <strong>{status === 'context-lost' ? 'Rendering interrupted' : 'Restoring 3D scene'}</strong>
              <span>{status === 'context-lost' ? 'Camera controls are paused.' : 'Controls resume after a healthy frame.'}</span>
            </div>
          )}
          <button className="reset-camera" type="button" onClick={resetCamera} disabled={status !== 'ready'}>
            Reset camera
          </button>
          <p className="interaction-hint">Drag to orbit · Scroll to zoom</p>
        </div>
      </section>
    </main>
  )
}
