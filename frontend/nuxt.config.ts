// nuxt.config.ts
export default defineNuxtConfig({
  ssr: false,
  devtools: { enabled: true },
  pages: true,
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_API_BASE || 'http://127.0.0.1:8000/api',
    },
  },
  // optional: avoids Nuxt fetching the app manifest in dev
  experimental: {
    appManifest: false,
  },
})

