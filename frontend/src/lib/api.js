import { API_BASE_URL } from './constants.js'

/**
 * Join the configured base with a request path without duplicating a shared
 * prefix. Request paths already start with `/api/v1/...`, so:
 *   base ""                       + "/api/v1/x" -> "/api/v1/x"        (same-origin)
 *   base "http://localhost:8001"  + "/api/v1/x" -> "http://localhost:8001/api/v1/x"
 *   base "/api"                   + "/api/v1/x" -> "/api/v1/x"        (no double /api)
 * The last case guards against a stale `VITE_API_BASE_URL=/api`, which would
 * otherwise produce `/api/api/v1/...` and 404.
 */
export function buildUrl(base, path) {
  if (!base) return path
  const trimmed = base.replace(/\/+$/, '')
  if (trimmed.startsWith('/') && path.startsWith(`${trimmed}/`)) {
    return path
  }
  return `${trimmed}${path}`
}

/**
 * Build an API client bound to a token getter. The getter is read on every
 * request so the client always sends the current session's bearer token.
 */
export function createApiClient(getToken) {
  return async function apiRequest(path, options = {}) {
    const token = typeof getToken === 'function' ? getToken() : getToken
    const response = await fetch(buildUrl(API_BASE_URL, path), {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {}),
      },
    })

    if (response.status === 204) {
      return {}
    }

    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(data.detail || 'Request failed')
    }
    return data
  }
}
