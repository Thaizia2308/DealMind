// Backend base URL comes from VITE_API_URL (set in .env / your hosting dashboard).
// Empty = same origin ("/api/..."), which the Vite dev server proxies to the local backend.
export const API_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status = 0, code = '') {
    super(message)
    this.status = status
    this.code = code
  }
}

function formatDetail(detail) {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  return JSON.stringify(detail)
}

async function request(path, { method = 'GET', body } = {}) {
  let res
  try {
    res = await fetch(`${API_URL}/api${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(
      `Cannot reach the DealMind backend${API_URL ? ` at ${API_URL}` : ''}. Make sure it is running and VITE_API_URL is correct.`,
      0,
      'network',
    )
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(formatDetail(data?.detail) || res.statusText, res.status, data?.code || '')
  return data
}

export const api = {
  health: () => request('/health'),
  memoryStatus: () => request('/memory/status'),
  listCustomers: () => request('/customers'),
  createCustomer: (b) => request('/customers', { method: 'POST', body: b }),
  deleteCustomer: (id) => request(`/customers/${id}`, { method: 'DELETE' }),
  listInteractions: (id) => request(`/customers/${id}/interactions`),
  addInteraction: (id, b) => request(`/customers/${id}/interactions`, { method: 'POST', body: b }),
  retryInteraction: (iid) => request(`/interactions/${iid}/retry`, { method: 'POST' }),
  recall: (id, query) => request(`/customers/${id}/memory/recall`, { method: 'POST', body: { query } }),
  ask: (id, question) => request(`/customers/${id}/ask`, { method: 'POST', body: { question } }),
  prepare: (id, b) => request(`/customers/${id}/prepare`, { method: 'POST', body: b }),
  followup: (id, b) => request(`/customers/${id}/followup`, { method: 'POST', body: b }),
  demoScript: () => request('/demo/script'),
  demoCustomer: () => request('/demo/customer', { method: 'POST' }),
}
