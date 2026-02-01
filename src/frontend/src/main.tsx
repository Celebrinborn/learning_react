import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from './hooks/useAuth'
import { setupTelemetry } from './telemetry'
import './index.css'
import App from './App.tsx'

// Initialize OpenTelemetry before React render
setupTelemetry()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
