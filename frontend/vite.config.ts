import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    host: '0.0.0.0',
    port: 5173,
    hmr: {
      port: 5173,
    },
    // Allow external hosts (for Sealos and other cloud platforms)
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '0.0.0.0',
      'ltmngjwnkxwe.usw.sealos.io',
      // Allow all subdomains of sealos.io
      '.sealos.io',
      // Allow any host (use cautiously in development only)
      'all',
      '.orkapodavid.top'
    ],
  },
  // Ensure environment variables are properly loaded
  envPrefix: 'VITE_',
})
