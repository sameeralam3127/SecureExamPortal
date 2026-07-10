import { useCallback, useEffect, useMemo, useState } from 'react'

import './App.css'
import AdminDashboard from './components/admin/AdminDashboard.jsx'
import AuthView from './components/AuthView.jsx'
import StudentDashboard from './components/student/StudentDashboard.jsx'
import { createApiClient } from './lib/api.js'
import { GOOGLE_CLIENT_ID } from './lib/constants.js'

const SESSION_KEY = 'secureExamSession'

function App({ route = '/login', onNavigate = () => {} }) {
  const [session, setSession] = useState(() => {
    const saved = localStorage.getItem(SESSION_KEY)
    return saved ? JSON.parse(saved) : null
  })
  const [message, setMessage] = useState('')

  const api = useMemo(() => createApiClient(() => session?.access_token), [session])

  const startSession = useCallback(
    (data) => {
      setSession(data)
      localStorage.setItem(SESSION_KEY, JSON.stringify(data))
      setMessage('')
    },
    [],
  )

  const handleLogin = useCallback(
    async (form) => {
      try {
        startSession(await api('/api/v1/auth/login', { method: 'POST', body: JSON.stringify(form) }))
      } catch (error) {
        setMessage(error.message)
      }
    },
    [api, startSession],
  )

  const handleRegister = useCallback(
    async (form, onDone) => {
      try {
        startSession(
          await api('/api/v1/auth/register', { method: 'POST', body: JSON.stringify(form) }),
        )
        onDone?.()
      } catch (error) {
        setMessage(error.message)
      }
    },
    [api, startSession],
  )

  const handleForgotPassword = useCallback(
    async (email, onDone) => {
      try {
        const data = await api('/api/v1/auth/password-reset/request', {
          method: 'POST',
          body: JSON.stringify({ email }),
        })
        setMessage(data.detail || 'If that account exists, a reset link has been sent.')
        onDone?.()
      } catch (error) {
        setMessage(error.message)
      }
    },
    [api],
  )

  const handleResetPassword = useCallback(
    async (newPassword) => {
      const token = new URLSearchParams(window.location.search).get('token') || ''
      try {
        const data = await api('/api/v1/auth/password-reset/confirm', {
          method: 'POST',
          body: JSON.stringify({ token, new_password: newPassword }),
        })
        setMessage(data.detail || 'Password updated. Please sign in.')
        onNavigate('/login')
      } catch (error) {
        setMessage(error.message)
      }
    },
    [api, onNavigate],
  )

  const logout = useCallback(async () => {
    try {
      await api('/api/v1/auth/logout', { method: 'POST' })
    } catch {
      // Ignore network/auth errors; local sign-out must always proceed.
    }
    setSession(null)
    localStorage.removeItem(SESSION_KEY)
    setMessage('')
    onNavigate('/login')
  }, [api, onNavigate])

  // Keep the address bar in sync with the signed-in role.
  useEffect(() => {
    if (!session) return
    onNavigate(session.user.role === 'admin' ? '/admin/dashboard' : '/student/dashboard')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session])

  // Render the Google Identity button on the login screen.
  useEffect(() => {
    if (session || route !== '/login' || !GOOGLE_CLIENT_ID) return undefined

    const tryInit = () => {
      if (!window.google?.accounts?.id) return false
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (response) => {
          try {
            startSession(
              await api('/api/v1/auth/google', {
                method: 'POST',
                body: JSON.stringify({ credential: response.credential }),
              }),
            )
          } catch (error) {
            setMessage(error.message)
          }
        },
      })
      const button = document.getElementById('googleSignInButton')
      if (!button) return false
      button.innerHTML = ''
      window.google.accounts.id.renderButton(button, {
        theme: 'outline',
        size: 'large',
        width: '320',
      })
      return true
    }

    if (tryInit()) return undefined
    const pollId = window.setInterval(() => {
      if (tryInit()) window.clearInterval(pollId)
    }, 300)
    const timeoutId = window.setTimeout(() => window.clearInterval(pollId), 5000)
    return () => {
      window.clearInterval(pollId)
      window.clearTimeout(timeoutId)
    }
  }, [session, route, api, startSession])

  if (!session || route === '/reset-password') {
    return (
      <AuthView
        route={route}
        onNavigate={onNavigate}
        message={message}
        onLogin={handleLogin}
        onRegister={handleRegister}
        onForgotPassword={handleForgotPassword}
        onResetPassword={handleResetPassword}
      />
    )
  }

  if (session.user.role === 'admin') {
    return <AdminDashboard api={api} message={message} setMessage={setMessage} onLogout={logout} />
  }

  return (
    <StudentDashboard
      api={api}
      user={session.user}
      message={message}
      setMessage={setMessage}
      onLogout={logout}
    />
  )
}

export default App
