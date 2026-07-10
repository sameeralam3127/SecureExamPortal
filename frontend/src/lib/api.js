import { API_BASE_URL } from './constants.js'

/**
 * Build an API client bound to a token getter. The getter is read on every
 * request so the client always sends the current session's bearer token.
 */
export function createApiClient(getToken) {
  return async function apiRequest(path, options = {}) {
    const token = typeof getToken === 'function' ? getToken() : getToken
    const response = await fetch(`${API_BASE_URL}${path}`, {
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
