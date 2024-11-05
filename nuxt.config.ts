// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],
  
  build: {
    transpile: ['@ffmpeg/ffmpeg', '@ffmpeg/util']
  },

  vite: {
    define: {
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV)
    },
    optimizeDeps: {
      include: ['@ffmpeg/ffmpeg', '@ffmpeg/util']
    },
    resolve: {
      mainFields: ['browser', 'module', 'main']
    },
    server: {
      headers: {
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "cross-origin"
      }
    }
  },

  nitro: {
    routeRules: {
      '/**': {
        headers: {
          'Cross-Origin-Embedder-Policy': 'require-corp',
          'Cross-Origin-Opener-Policy': 'same-origin',
          'Cross-Origin-Resource-Policy': 'cross-origin'
        }
      }
    }
  },

  pages: false,
  layouts: false,
  compatibilityDate: '2024-04-03',
  devtools: { enabled: true }
});