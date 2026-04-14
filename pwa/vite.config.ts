import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { execSync } from 'child_process'

const buildHash = (() => {
  try {
    return execSync('git rev-parse --short HEAD').toString().trim()
  } catch {
    return Date.now().toString(36)
  }
})()

export default defineConfig({
  plugins: [react()],
  base: '/app/',
  define: {
    __BUILD_HASH__: JSON.stringify(buildHash),
  },
})
