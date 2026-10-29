import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { viteSingleFile } from 'vite-plugin-singlefile'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget =
    process.env.VITE_API_TARGET || env.VITE_API_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue(), viteSingleFile()],
    server: {
      host: true,
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: 'dist',
      assetsInlineLimit: 100000000,
      cssCodeSplit: false
    }
  }
})
