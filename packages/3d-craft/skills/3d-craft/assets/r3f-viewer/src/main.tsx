import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

const container = document.getElementById('root')
if (!container) throw new Error('3D-Craft viewer root element is missing')

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
