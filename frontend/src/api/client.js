// 登录态的本地存取，以及 401 时的全局通知（由 App.vue 注册处理函数）。
export const SESSION_KEY = 'jg_session'

export function getSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return { username: '', token: '' }
    const data = JSON.parse(raw)
    return { username: data.username || '', token: data.token || '' }
  } catch {
    return { username: '', token: '' }
  }
}

export function getToken() {
  return getSession().token
}

export function setSession(username, token) {
  localStorage.setItem(SESSION_KEY, JSON.stringify({ username, token }))
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY)
}

let unauthorizedHandler = null

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler
}

export function notifyUnauthorized() {
  if (unauthorizedHandler) unauthorizedHandler()
}

export function newSessionId() {
  return 'web-' + Math.random().toString(36).slice(2, 10)
}
