import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      '/login': 'http://127.0.0.1:5001',
      '/logout': 'http://127.0.0.1:5001',
      '/session': 'http://127.0.0.1:5001',
      '/warehouse': 'http://127.0.0.1:5001',
      '/requests': 'http://127.0.0.1:5001',
    },
  },
})
