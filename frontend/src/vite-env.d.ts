/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the Second Look API, for example https://api.example.org. Empty means same origin. */
  readonly VITE_API_BASE_URL?: string;
}
