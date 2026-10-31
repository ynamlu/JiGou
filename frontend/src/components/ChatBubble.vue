<script setup>
import { computed, ref } from 'vue'
import { renderMarkdown } from '../utils/markdown'
import ThinkingDots from './ThinkingDots.vue'
import logo from '../assets/logo.png'

const props = defineProps({
  role: { type: String, default: 'assistant' },
  content: { type: String, default: '' },
  status: { type: String, default: '' },
  statusDone: { type: Boolean, default: false },
  thinking: { type: Boolean, default: false },
  streaming: { type: Boolean, default: false }
})

const html = computed(() => renderMarkdown(props.content))

const copied = ref(false)
let copyTimer = null

async function copyContent() {
  if (!props.content) return
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(props.content)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = props.content
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      textarea.remove()
    }
    copied.value = true
    clearTimeout(copyTimer)
    copyTimer = setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    
  }
}
</script>

<template>
  <div class="row" :class="role">
    <div class="avatar">
      <img v-if="role !== 'user'" :src="logo" alt="极构" />
      <span v-else>你</span>
    </div>
    <div class="bubble">
      <div v-if="status" class="toolbar" :class="{ done: statusDone }">
        <span v-if="!statusDone" class="spin"></span>
        <span class="q">{{ status }}</span>
      </div>

      <div v-if="content" class="md" v-html="html"></div>
      <ThinkingDots v-else-if="thinking" />

      <span v-if="streaming && content" class="cursor"></span>

      <div v-if="content && !thinking" class="bubble-actions">
        <button
          type="button"
          class="action-btn"
          :title="copied ? '已复制' : '复制内容'"
          @click="copyContent"
        >
          <svg v-if="!copied" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
          <svg v-else viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span>{{ copied ? '已复制' : '复制' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  gap: 11px;
  margin-bottom: 20px;
  animation: fade 0.35s ease both;
}

@keyframes fade {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  flex: none;
  display: grid;
  place-items: center;
  font-size: 15px;
  background: #fff;
  border: 1px solid var(--line);
  color: var(--accent);
  overflow: hidden;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 3px;
}

.row.user .avatar {
  background: #e8f7f6;
  color: var(--accent-2);
}

.bubble {
  max-width: min(78%, 720px);
  padding: 13px 17px;
  border-radius: 14px;
  background: var(--card);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  word-break: break-word;
}

.row.user .bubble {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  box-shadow: none;
}

.toolbar {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 9px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12.5px;
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px solid #dfe2ff;
}

.toolbar.done {
  background: #e9f7f2;
  color: #0d7a63;
  border-color: #cdeee4;
}

.md :deep(p) {
  margin: 0 0 9px;
}

.md :deep(> :last-child) {
  margin-bottom: 0;
}

.md :deep(h2),
.md :deep(h3) {
  margin: 15px 0 8px;
  font-size: 15.5px;
  font-weight: 650;
}

.md :deep(h2:first-child),
.md :deep(h3:first-child) {
  margin-top: 0;
}

.md :deep(strong) {
  font-weight: 650;
}

.md :deep(ul),
.md :deep(ol) {
  margin: 6px 0 10px;
  padding-left: 21px;
}

.md :deep(li) {
  margin: 3px 0;
}

.md :deep(code) {
  background: #f1f3f9;
  border-radius: 5px;
  padding: 1px 5px;
  font-size: 13px;
  font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
}

.row.user .md :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.md :deep(hr) {
  border: none;
  border-top: 1px solid var(--line);
  margin: 13px 0;
}

.row.user .md :deep(hr) {
  border-top-color: rgba(255, 255, 255, 0.3);
}

@media (max-width: 640px) {
  .row {
    gap: 8px;
    margin-bottom: 16px;
  }

  .avatar {
    width: 28px;
    height: 28px;
    border-radius: 9px;
    font-size: 13px;
  }

  .bubble {
    max-width: 85%;
    padding: 11px 14px;
  }
}

/* ================= 2026 视觉升级 ================= */
.bubble {
  border-radius: 16px;
  border-color: rgba(226, 232, 240, 0.9);
  background: #fff;
  box-shadow: 0 14px 30px -24px rgba(30, 41, 90, 0.5);
}

.row.user .bubble {
  background: var(--grad);
  border: none;
  box-shadow: 0 16px 30px -18px rgba(79, 70, 229, 0.85);
}

.avatar {
  border: none;
  box-shadow: 0 6px 14px -10px rgba(30, 41, 90, 0.6);
}

.row.user .avatar {
  background: linear-gradient(135deg, #e0f7f4, #dff1ff);
  color: #0f766e;
}

.toolbar {
  background: linear-gradient(135deg, #eef1ff, #eaf6ff);
  border-color: #e0e6ff;
}

.toolbar.done {
  background: linear-gradient(135deg, #e9f7f2, #e8f8ff);
}

.speak {
  background: #f8faff;
  border-color: rgba(226, 232, 240, 0.95);
}

.speak:hover {
  background: var(--accent-soft);
  border-color: rgba(79, 70, 229, 0.4);
}

.bubble-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px dashed rgba(226, 232, 240, 0.8);
}

.row.user .bubble-actions {
  border-top-color: rgba(255, 255, 255, 0.25);
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 11.5px;
  color: var(--ink-3);
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.16s ease;
}

.action-btn:hover {
  color: var(--accent);
  background: var(--accent-soft);
  border-color: rgba(79, 70, 229, 0.2);
}

.row.user .action-btn {
  color: rgba(255, 255, 255, 0.8);
}

.row.user .action-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.35);
}
</style>
