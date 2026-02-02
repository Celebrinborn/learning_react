import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Map APP_ENV values to env file suffixes
const envFileMap: Record<string, string> = {
  dev: 'dev',
  development: 'dev',
  test: 'test',
  testing: 'test',
  prod: 'prod',
  production: 'prod',
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Check APP_ENV first, fall back to Vite's mode, default to prod
  const appEnv = process.env.APP_ENV?.toLowerCase() || 'prod'
  const envSuffix = envFileMap[appEnv] || 'prod'
  
  // Load the appropriate env file
  const env = loadEnv(envSuffix, process.cwd(), '')
  
  return {
    plugins: [react()],
    envDir: '.',
    // Use custom env file naming: .env.dev, .env.test, .env.prod
    define: {
      // Make APP_ENV available at build time
      'import.meta.env.VITE_APP_ENV': JSON.stringify(envSuffix),
    },
  }
})
