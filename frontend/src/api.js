import { clearSession, session } from './session'

const baseURL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

const fieldNames = {
  name: '商品名称',
  sku: '商品编码',
  category: '分类',
  price: '价格',
  stock: '库存',
  status: '状态',
  description: '商品描述',
}

async function request(path, { body, headers = {}, ...options } = {}) {
  const token = session.value?.token
  if (token) headers.Authorization = `Bearer ${token}`
  if (body && !(body instanceof URLSearchParams)) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(body)
  }
  let response
  try {
    response = await fetch(`${baseURL}/api${path}`, {
      ...options,
      headers,
      body,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new ApiError('无法连接服务，请确认后端已启动后重试。', 0)
  }
  if (response.status === 204) return null
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 401 && token) clearSession(true)
    let message = data.detail || '操作失败，请稍后重试。'
    if (Array.isArray(message)) {
      message = message
        .map((item) => `${fieldNames[item.loc.at(-1)] || '输入内容'}格式不正确`)
        .join('；')
    }
    throw new ApiError(
      typeof message === 'string' ? message : '操作失败，请稍后重试。',
      response.status,
    )
  }
  return data
}

export const authApi = {
  login: (username, password) =>
    request('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({ username, password }),
    }),
  me: () => request('/auth/me'),
}

export const productApi = {
  list: (params, signal) => {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== '' && value != null) query.set(key, value)
    })
    return request(`/products?${query}`, { signal })
  },
  stats: () => request('/products/stats'),
  get: (id) => request(`/products/${id}`),
  create: (body) => request('/products', { method: 'POST', body }),
  update: (id, body) => request(`/products/${id}`, { method: 'PUT', body }),
  remove: (id) => request(`/products/${id}`, { method: 'DELETE' }),
}
