import { computed, ref } from 'vue'

const STORAGE_KEY = 'goodstock-session'

function readSession() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) || 'null')
    return saved?.token && saved?.expiresAt > Date.now() ? saved : null
  } catch {
    return null
  }
}

// 学习示例使用 sessionStorage：刷新保留，关闭标签页清除。
// 前端状态只负责页面体验，真正的权限校验始终在后端完成。
export const session = ref(readSession())
export const sessionExpired = ref(false)
export const isAuthenticated = computed(() => Boolean(session.value))

export function saveSession(data) {
  sessionExpired.value = false
  session.value = {
    token: data.access_token,
    user: data.user,
    expiresAt: Date.now() + data.expires_in * 1000,
  }
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session.value))
}

export function clearSession(expired = false) {
  sessionExpired.value = expired
  sessionStorage.removeItem(STORAGE_KEY)
  session.value = null
}
