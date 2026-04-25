import { useEffect, useState } from 'react'

import App from './App.jsx'

export default function Root() {
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
