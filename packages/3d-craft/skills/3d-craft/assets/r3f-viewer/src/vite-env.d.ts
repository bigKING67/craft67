/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ASSET_URL?: string
  readonly VITE_ASSET_SHA256?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
