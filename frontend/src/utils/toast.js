import { reactive } from 'vue'

export const toasts = reactive([])

let seed = 0

/**
 * 全局统一轻提示
 * @param {string} message 提示文本
 * @param {'info' | 'success' | 'error' | 'warning' | number} type 提示类型或展示时长（毫秒）
 * @param {number} duration 展示时长（毫秒）
 */
export function showToast(message, type = 'info', duration = 2400) {
  let toastType = type
  let toastDuration = duration

  if (typeof type === 'number') {
    toastDuration = type
    toastType = 'info'
  }

  const item = { id: ++seed, message, type: toastType }
  toasts.push(item)
  setTimeout(() => {
    const index = toasts.findIndex((t) => t.id === item.id)
    if (index > -1) toasts.splice(index, 1)
  }, toastDuration)
}
