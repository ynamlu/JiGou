<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { renderMarkdown } from '../utils/markdown'
import { saveTextFile } from '../utils/export'
import { showToast } from '../utils/toast'
import logo from '../assets/logo.png'

const props = defineProps({
  document: { type: String, default: '' },
  docId: { type: String, default: '' }
})

const router = useRouter()
const html = computed(() => renderMarkdown(props.document))

function view() {
  if (props.docId) router.push(`/doc/${props.docId}`)
}

function download() {
  const mode = saveTextFile('需求诊断报告.md', props.document)
  showToast(mode === 'native' ? '已保存到「下载」目录' : 'MD 文件已导出')
}
</script>

<template>
  <div class="row assistant">
    <div class="avatar"><img :src="logo" alt="极构" /></div>
    <div class="bubble doccard">
      <div class="doc-head">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M7 3h7l4 4v14H7z" stroke-linejoin="round" />
          <path d="M14 3v4h4" stroke-linejoin="round" />
          <path d="M10 12h5M10 16h5" stroke-linecap="round" />
        </svg>
        <span class="name">需求诊断报告</span>
        <button type="button" class="doc-view" @click="view">查看</button>
        <button type="button" class="doc-dl" @click="download">下载 .md</button>
      </div>
      <div class="md" v-html="html"></div>
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

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  flex: none;
  display: grid;
  place-items: center;
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

.bubble {
  max-width: min(78%, 720px);
  padding: 13px 17px;
  border-radius: 14px;
  background: #fbfbff;
  border: 1px dashed #c9cdf5;
  word-break: break-word;
}

.doc-head {
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
  color: var(--accent);
}

.doc-head .name {
  font-weight: 650;
  font-size: 14.5px;
  flex: 1;
  color: var(--ink);
}

.doc-view {
  font-size: 12.5px;
  padding: 6px 13px;
  border-radius: 999px;
  cursor: pointer;
  flex: none;
  background: var(--card);
  color: var(--accent);
  border: 1px solid var(--accent-soft);
  transition: background 0.18s;
}

.doc-view:hover {
  background: var(--accent-soft);
}

.doc-dl {
  font-size: 12.5px;
  padding: 6px 13px;
  border-radius: 999px;
  cursor: pointer;
  flex: none;
  background: var(--accent);
  color: #fff;
  border: none;
  transition: background 0.18s;
}

.doc-dl:hover {
  background: #4338ca;
}

.md :deep(p) {
  margin: 0 0 9px;
}

.md :deep(> :last-child) {
  margin-bottom: 0;
}

.md :deep(h1) {
  font-size: 16px;
  margin: 0 0 10px;
}

.md :deep(h2),
.md :deep(h3) {
  margin: 14px 0 8px;
  font-size: 15px;
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

.md :deep(hr) {
  border: none;
  border-top: 1px solid var(--line);
  margin: 13px 0;
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
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 18px;
  background: linear-gradient(180deg, #fbfcff, #ffffff);
  box-shadow: 0 18px 40px -30px rgba(30, 41, 90, 0.5);
}

.doc-head {
  padding-bottom: 12px;
  margin-bottom: 12px;
}

.doc-head .name {
  font-size: 15px;
  font-weight: 700;
}

.doc-view {
  background: var(--accent-soft);
  border-color: #e0e4ff;
}

.doc-dl {
  background: var(--grad);
  box-shadow: 0 8px 16px -10px rgba(79, 70, 229, 0.9);
}

.doc-dl:hover {
  background: var(--grad);
  filter: brightness(1.06);
}
</style>
