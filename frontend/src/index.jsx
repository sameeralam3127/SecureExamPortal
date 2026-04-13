import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App.jsx'
import './index.css'

function FrontendIndex() {
  const [route, setRoute] = useState(window.location.pathname || '/login')

  useEffect(() => {
    const syncRoute = () => setRoute(window.location.pathname || '/login')
    window.addEventListener('popstate', syncRoute)
    return () => window.removeEventListener('popstate', syncRoute)
  }, [])

  const navigate = (path) => {
    window.history.pushState({}, '', path)
    setRoute(path)
  }

  return <App route={route} onNavigate={navigate} />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <FrontendIndex />
  </StrictMode>,
)
