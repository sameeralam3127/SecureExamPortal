import { useState } from 'react'

import { GOOGLE_CLIENT_ID } from '../lib/constants.js'

function AlertMessage({ message }) {
  if (!message) return null
  return (
    <p className="alert-message" role="status" aria-live="polite">
      {message}
    </p>
  )
}

export default function AuthView({
  route,
  onNavigate,
  message,
  onLogin,
  onRegister,
  onForgotPassword,
  onResetPassword,
}) {
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [registerForm, setRegisterForm] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
  })
  const [showForgot, setShowForgot] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [resetPassword, setResetPassword] = useState('')

  if (route === '/reset-password') {
    return (
      <main className="login-shell">
        <section className="login-card">
          <div className="brand-mark">
            <span className="brand-icon">S</span>
            <span>Secure Exam Portal</span>
          </div>
          <h1>Choose a new password</h1>
          <p>Enter a new password for your account.</p>
          <form
            className="form-stack"
            onSubmit={(event) => {
              event.preventDefault()
              onResetPassword(resetPassword)
            }}
          >
            <label htmlFor="reset-password">New password</label>
            <input
              id="reset-password"
              type="password"
              value={resetPassword}
              onChange={(event) => setResetPassword(event.target.value)}
              placeholder="New password (min 8 chars, letters and numbers)"
              autoComplete="new-password"
              required
              minLength={8}
            />
            <AlertMessage message={message} />
            <button className="action-btn blue" type="submit">
              Update password
            </button>
          </form>
          <button className="ghost-btn" type="button" onClick={() => onNavigate('/login')}>
            Back to login
          </button>
        </section>
      </main>
    )
  }

  const isRegister = route === '/register'

  return (
    <main className="login-shell">
      <aside className="login-hero" aria-hidden="true">
        <div className="hero-kicker">Trusted assessment workspace</div>
        <h1>Secure exams, calmer operations.</h1>
        <p>
          Run assignments, monitor completion, and give students a focused testing experience.
        </p>
        <div className="hero-stats">
          <span>Live autosave</span>
          <span>Role dashboards</span>
          <span>Bulk setup</span>
        </div>
      </aside>
      <section className="login-card">
        <div className="brand-mark">
          <span className="brand-icon">S</span>
          <span>Secure Exam Portal</span>
        </div>
        <div className="auth-tab-row">
          <button
            type="button"
            className={!isRegister ? 'auth-tab active' : 'auth-tab'}
            onClick={() => onNavigate('/login')}
          >
            Login
          </button>
          <button
            type="button"
            className={isRegister ? 'auth-tab active' : 'auth-tab'}
            onClick={() => onNavigate('/register')}
          >
            Register
          </button>
        </div>

        {isRegister ? (
          <>
            <h1>Create student account</h1>
            <p>Register and you will be redirected to the student dashboard.</p>
            <form
              className="form-stack"
              onSubmit={(event) => {
                event.preventDefault()
                onRegister(registerForm, () =>
                  setRegisterForm({ full_name: '', username: '', email: '', password: '' }),
                )
              }}
            >
              <input
                value={registerForm.full_name}
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, full_name: event.target.value }))
                }
                placeholder="Full name"
                aria-label="Full name"
                autoComplete="name"
                required
              />
              <input
                value={registerForm.username}
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, username: event.target.value }))
                }
                placeholder="Username"
                aria-label="Username"
                autoComplete="username"
                required
              />
              <input
                type="email"
                value={registerForm.email}
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, email: event.target.value }))
                }
                placeholder="Email"
                aria-label="Email address"
                autoComplete="email"
                required
              />
              <input
                type="password"
                value={registerForm.password}
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, password: event.target.value }))
                }
                placeholder="Password (min 8 chars, letters and numbers)"
                aria-label="Password"
                autoComplete="new-password"
                required
                minLength={8}
              />
              <AlertMessage message={message} />
              <button className="action-btn blue" type="submit">
                Create Account
              </button>
            </form>
          </>
        ) : (
          <>
            <h1>Login to continue</h1>
            <p>Use your portal credentials or Google sign-in.</p>
            <form
              className="form-stack"
              onSubmit={(event) => {
                event.preventDefault()
                onLogin(loginForm)
              }}
            >
              <input
                value={loginForm.username}
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, username: event.target.value }))
                }
                placeholder="Username"
                aria-label="Username"
                autoComplete="username"
                required
              />
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, password: event.target.value }))
                }
                placeholder="Password"
                aria-label="Password"
                autoComplete="current-password"
                required
              />
              <AlertMessage message={message} />
              <button className="action-btn blue" type="submit">
                Login
              </button>
            </form>
            <button
              className="ghost-btn"
              type="button"
              onClick={() => setShowForgot((current) => !current)}
              aria-expanded={showForgot}
            >
              Forgot password?
            </button>
            {showForgot ? (
              <form
                className="form-stack"
                onSubmit={(event) => {
                  event.preventDefault()
                  onForgotPassword(forgotEmail, () => {
                    setForgotEmail('')
                    setShowForgot(false)
                  })
                }}
              >
                <label htmlFor="forgot-email">Account email</label>
                <input
                  id="forgot-email"
                  type="email"
                  value={forgotEmail}
                  onChange={(event) => setForgotEmail(event.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  required
                />
                <button className="action-btn green" type="submit">
                  Send reset link
                </button>
              </form>
            ) : null}
            <div className="google-login-wrap">
              {GOOGLE_CLIENT_ID ? (
                <div id="googleSignInButton" />
              ) : (
                <p className="google-disabled">
                  Add <code>VITE_GOOGLE_CLIENT_ID</code> to enable Google login.
                </p>
              )}
            </div>
          </>
        )}
      </section>
    </main>
  )
}
