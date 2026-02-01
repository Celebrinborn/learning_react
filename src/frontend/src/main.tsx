import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from './hooks/useAuth'
import { setupTelemetry } from './telemetry'
import './index.css'
import App from './App.tsx'

// Initialize OpenTelemetry in the background (non-blocking)
setupTelemetry().catch(console.warn)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
