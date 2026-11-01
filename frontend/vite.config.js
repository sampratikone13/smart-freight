import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      },
      '/batch_predict': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      },
      '/college-labs': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      },
      '/health': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      },
      '/dashboard/export_csv': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      }
    }
  }
})

