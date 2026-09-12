export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { headers: {'Content-Type':'application/json', ...(options.headers || {})}, ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || 'Request failed')
  return data
}

