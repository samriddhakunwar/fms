import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy the API through the dev server so the browser only ever talks to
    // one origin: no CORS preflight, no cross-port cookies, and no chance of
    // the request resolving to ::1 while Django only listens on 127.0.0.1.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
