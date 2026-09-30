export const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function request(path, options = {}) {
  const {headers: optionHeaders = {}, ...restOptions} = options

  const response = await fetch(`${API}${path}`, {
    ...restOptions,
    headers: {
      'Content-Type': 'application/json',
      ...optionHeaders,
    },
  })

  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed')
  }
  return data
}

// Admin order actions used by the dashboard.
export function updateOrderStatus(orderId, nextStatus, adminKey) {
  return request(`/orders/${orderId}/status`, {
    method: 'PATCH',
    headers: {'X-Admin-Key': adminKey},
    body: JSON.stringify({status: nextStatus}),
  })
}

export function deleteOrder(orderId, adminKey) {
  return request(`/orders/${orderId}`, {
    method: 'DELETE',
    headers: {'X-Admin-Key': adminKey},
  })
}
