import { OrbitControls } from '@react-three/drei'
import { Canvas, useThree } from '@react-three/fiber'
import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from 'react'
import {
  Box3,
  Color,
  Group,
  Material,
  MathUtils,
  Mesh,
  Object3D,
  SRGBColorSpace,
  Texture,
  Vector3,
  WebGLRenderer,
} from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import {
  noteContextHealthy,
  noteContextLost,
  noteContextRestoring,
  noteContextTestSupport,
  noteDispose,
  noteMount,
  type ContextStatus,
  type SceneFacts,
  type ViewerStatus,
} from './observability'
import { RuntimeProbe } from './RuntimeProbe'

interface AssetSceneProps {
  assetUrl: string
  assetSha256: string
  reducedMotion: boolean
  onStatus: (status: ViewerStatus, detail?: string) => void
  onFacts: (facts: SceneFacts) => void
}

type AssetStatus = Extract<ViewerStatus, 'loading' | 'ready' | 'error'>

const DISPLAY_MAX_DIMENSION_METERS = 0.32
const CAMERA_TARGET = new Vector3(0, 0.15, 0)
const CAMERA_POSITION = new Vector3(0.48, 0.34, 0.56)
const COMPACT_CAMERA_ASPECT = 0.8
const COMPACT_CAMERA_DISTANCE_SCALE = 1.65

function ResponsiveCamera({ controls }: { controls: RefObject<OrbitControlsImpl | null> }) {
  const { camera, size } = useThree()
  const compact = size.width / Math.max(size.height, 1) < COMPACT_CAMERA_ASPECT

  const resetCamera = useCallback(() => {
    const distanceScale = compact ? COMPACT_CAMERA_DISTANCE_SCALE : 1
    camera.position
      .copy(CAMERA_POSITION)
      .sub(CAMERA_TARGET)
      .multiplyScalar(distanceScale)
      .add(CAMERA_TARGET)
    camera.lookAt(CAMERA_TARGET)
    camera.updateMatrixWorld()
    controls.current?.target.copy(CAMERA_TARGET)
    controls.current?.update()
  }, [camera, compact, controls])

  useEffect(() => resetCamera(), [resetCamera])

  useEffect(() => {
    window.addEventListener('3d-craft:reset-camera', resetCamera)
    return () => window.removeEventListener('3d-craft:reset-camera', resetCamera)
  }, [resetCamera])

  return null
}

function disposeObject(root: Object3D): void {
  const disposedMaterials = new Set<Material>()
  const disposedTextures = new Set<Texture>()
  root.traverse((child) => {
    if (!(child instanceof Mesh)) return
    child.geometry.dispose()
    const materials = Array.isArray(child.material) ? child.material : [child.material]
    for (const material of materials) {
      if (disposedMaterials.has(material)) continue
      disposedMaterials.add(material)
      for (const value of Object.values(material)) {
        if (value && typeof value === 'object' && 'isTexture' in value && (value as Texture).isTexture) {
          const texture = value as Texture
          if (!disposedTextures.has(texture)) {
            disposedTextures.add(texture)
            texture.dispose()
          }
        }
      }
      material.dispose()
    }
  })
  noteDispose()
}

function LoadedAsset({ assetUrl, onStatus, onFacts }: {
  assetUrl: string
  onStatus: (status: AssetStatus, detail?: string) => void
  onFacts: (facts: SceneFacts) => void
}) {
  const [root, setRoot] = useState<Group | null>(null)

  useEffect(() => {
    let cancelled = false
    let loadedRoot: Group | null = null
    setRoot(null)
    onStatus('loading')
    const loader = new GLTFLoader()
    loader.load(
      assetUrl,
      (gltf) => {
        if (cancelled) {
          disposeObject(gltf.scene)
          return
        }
        const bounds = new Box3().setFromObject(gltf.scene)
        const size = bounds.getSize(new Vector3())
        const center = bounds.getCenter(new Vector3())
        const maximumDimension = Math.max(size.x, size.y, size.z)
        if (!Number.isFinite(maximumDimension) || maximumDimension <= 0) {
          disposeObject(gltf.scene)
          onStatus('error', 'The GLB has no finite renderable bounds.')
          return
        }
        const displayScale = DISPLAY_MAX_DIMENSION_METERS / maximumDimension
        const displayRoot = new Group()
        displayRoot.name = '3D_Craft_Display_Root'
        displayRoot.add(gltf.scene)
        displayRoot.scale.setScalar(displayScale)
        displayRoot.position.copy(center).multiplyScalar(-displayScale)
        displayRoot.position.y += size.y * displayScale / 2
        let objects = 0
        let meshes = 0
        const nodeNames = new Set<string>()
        const materials = new Set<Material>()
        gltf.scene.traverse((child) => {
          objects += 1
          if (child !== gltf.scene && child.name) nodeNames.add(child.name)
          if (child instanceof Mesh) {
            meshes += 1
            child.castShadow = false
            child.receiveShadow = false
            const owned = Array.isArray(child.material) ? child.material : [child.material]
            owned.forEach((material) => materials.add(material))
          }
        })
        onFacts({
          objects,
          meshes,
          materials: materials.size,
          dimensions: [size.x, size.z, size.y],
          nodeNames: [...nodeNames].sort(),
          materialNames: [...materials].map((material) => material.name).filter(Boolean).sort(),
        })
        loadedRoot = displayRoot
        noteMount()
        setRoot(loadedRoot)
        onStatus('ready')
      },
      undefined,
      (error) => {
        if (!cancelled) onStatus('error', error instanceof Error ? error.message : String(error))
      },
    )
    return () => {
      cancelled = true
      if (loadedRoot) disposeObject(loadedRoot)
    }
  }, [assetUrl, onFacts, onStatus])

  return root ? <primitive object={root} /> : null
}

function ContextLifecycle({ onStatus, resumedStatus }: {
  onStatus: (status: ContextStatus) => void
  resumedStatus: AssetStatus
}) {
  const { gl, invalidate } = useThree()

  useEffect(() => {
    const canvas = gl.domElement
    const context = gl.getContext()
    const testSupported = Boolean(context.getExtension('WEBGL_lose_context'))
    let restoreGeneration = 0
    noteContextTestSupport(testSupported)

    const handleLost = (event: Event) => {
      event.preventDefault()
      restoreGeneration += 1
      noteContextLost()
      onStatus('lost')
    }
    const handleRestored = () => {
      const generation = ++restoreGeneration
      noteContextRestoring()
      onStatus('restoring')
      // Three registers its restore listener before this component. A microtask
      // observes that completed reset without depending on background-throttled RAF.
      queueMicrotask(() => {
        if (generation !== restoreGeneration || context.isContextLost()) return
        invalidate()
        noteContextHealthy(resumedStatus)
        onStatus('healthy')
      })
    }
    const forceLoss = () => gl.forceContextLoss()
    const forceRestore = () => gl.forceContextRestore()

    canvas.addEventListener('webglcontextlost', handleLost)
    canvas.addEventListener('webglcontextrestored', handleRestored)
    if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
      window.addEventListener('3d-craft:test-context-loss', forceLoss)
      window.addEventListener('3d-craft:test-context-restore', forceRestore)
    }
    return () => {
      restoreGeneration += 1
      canvas.removeEventListener('webglcontextlost', handleLost)
      canvas.removeEventListener('webglcontextrestored', handleRestored)
      window.removeEventListener('3d-craft:test-context-loss', forceLoss)
      window.removeEventListener('3d-craft:test-context-restore', forceRestore)
    }
  }, [gl, invalidate, onStatus, resumedStatus])

  return null
}

export function AssetScene({ assetUrl, assetSha256, reducedMotion, onStatus, onFacts }: AssetSceneProps) {
  const controls = useRef<OrbitControlsImpl>(null)
  const [assetGeneration, setAssetGeneration] = useState(0)
  const [assetStatus, setAssetStatus] = useState<AssetStatus>('loading')
  const [contextStatus, setContextStatus] = useState<ContextStatus>('healthy')
  const [error, setError] = useState('')
  const [facts, setFacts] = useState<SceneFacts>({ objects: 0, meshes: 0, materials: 0, dimensions: [0, 0, 0], nodeNames: [], materialNames: [] })
  const callbacks = useMemo(() => ({
    status: (next: AssetStatus, detail = '') => {
      setAssetStatus(next)
      setError(detail)
    },
    facts: (next: SceneFacts) => {
      setFacts(next)
      onFacts(next)
    },
  }), [onFacts])
  const status: ViewerStatus = contextStatus === 'lost'
    ? 'context-lost'
    : contextStatus === 'restoring'
      ? 'restoring'
      : assetStatus

  useEffect(() => {
    const detail = status === 'context-lost'
      ? 'The WebGL context was interrupted. Interaction is paused until the GPU context is restored.'
      : status === 'restoring'
        ? 'The WebGL context returned. Rebuilding renderer resources and resuming the scene…'
        : error
    onStatus(status, detail)
  }, [error, onStatus, status])

  useEffect(() => {
    if (!(import.meta.env.DEV || import.meta.env.MODE === 'test')) return
    const remountAsset = () => setAssetGeneration((value) => value + 1)
    window.addEventListener('3d-craft:test-remount', remountAsset)
    return () => window.removeEventListener('3d-craft:test-remount', remountAsset)
  }, [])

  return (
    <Canvas
      dpr={[1, 2]}
      camera={{ position: [0.48, 0.34, 0.56], fov: 32, near: 0.01, far: 100 }}
      gl={(parameters) => {
        const renderer = new WebGLRenderer({ ...parameters, antialias: true, powerPreference: 'high-performance' })
        renderer.outputColorSpace = SRGBColorSpace
        renderer.setClearColor(new Color('#e9e7e1'))
        return renderer
      }}
    >
      <ContextLifecycle onStatus={setContextStatus} resumedStatus={assetStatus} />
      <ResponsiveCamera controls={controls} />
      <ambientLight intensity={1.25} />
      <directionalLight position={[1.8, 2.4, 1.2]} intensity={3.2} />
      <directionalLight position={[-1.2, 0.8, -1.4]} intensity={1.1} />
      <group rotation={[0, MathUtils.degToRad(18), 0]}>
        <LoadedAsset key={assetGeneration} assetUrl={assetUrl} onStatus={callbacks.status} onFacts={callbacks.facts} />
      </group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.002, 0]}>
        <planeGeometry args={[3, 3]} />
        <meshStandardMaterial color="#dedcd5" roughness={0.96} />
      </mesh>
      <gridHelper args={[2.4, 24, '#b8b7b0', '#d2d0c9']} position={[0, 0.0005, 0]} />
      <OrbitControls
        ref={controls}
        makeDefault
        enabled={status === 'ready'}
        enableDamping={!reducedMotion}
        dampingFactor={0.07}
        autoRotate={!reducedMotion && status === 'ready'}
        autoRotateSpeed={0.35}
        minDistance={0.35}
        maxDistance={1.8}
        minPolarAngle={Math.PI * 0.18}
        maxPolarAngle={Math.PI * 0.54}
        target={[0, 0.15, 0]}
      />
      <RuntimeProbe assetUrl={assetUrl} assetSha256={assetSha256} facts={facts} status={status} error={error} />
    </Canvas>
  )
}
