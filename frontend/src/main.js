import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'highlight.js/styles/github-dark.css'
import './assets/styles.css'

// 全局监听 Markdown 代码块复制按钮事件
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.copy-code-btn')
  if (!btn) return
  const pre = btn.closest('.code-block')
  if (!pre) return
  const codeEl = pre.querySelector('code')
  if (!codeEl) return

  const text = codeEl.innerText
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      ta.remove()
    }
    btn.textContent = '已复制'
    btn.classList.add('copied')
    setTimeout(() => {
      btn.textContent = '复制'
      btn.classList.remove('copied')
    }, 2000)
  } catch {
    btn.textContent = '复制失败'
    setTimeout(() => {
      btn.textContent = '复制'
    }, 2000)
  }
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')
