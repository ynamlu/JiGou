import { reactive } from 'vue'

export const toasts = reactive([])

let seed = 0

export function showToast(message, duration = 2200) {
  const item = { id: ++seed, message }
  toasts.push(item)
  setTimeout(() => {
    const index = toasts.findIndex((t) => t.id === item.id)
    if (index > -1) toasts.splice(index, 1)
  }, duration)
}
