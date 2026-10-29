<!-- 我的图纸：从当前账号的本地归档中读取报告列表。 -->
<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useArchiveStore } from '../stores/archive'
import { useUserStore } from '../stores/user'

const router = useRouter()
const archive = useArchiveStore()
const user = useUserStore()

onMounted(() => {
  archive.load()
})
</script>

<template>
  <div class="history-page">
    <header class="app-header">
      <button type="button" class="icon-btn" @click="router.push('/')">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 5l-7 7 7 7" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <div class="titles">
        <h1>我的图纸</h1>
        <p>{{ user.username }} · {{ archive.items.length }} 份 · 仅保存在本机</p>
      </div>
    </header>

    <div class="history-body">
      <div v-if="!archive.items.length" class="empty-state">
        <svg viewBox="0 0 120 120" width="110" height="110" fill="none">
          <rect x="30" y="26" width="60" height="46" rx="12" fill="#eef0ff" />
          <circle cx="48" cy="49" r="6" fill="#4f46e5" />
          <circle cx="72" cy="49" r="6" fill="#4f46e5" />
          <rect x="44" y="78" width="32" height="14" rx="7" fill="#dfe2ff" />
          <rect x="52" y="92" width="16" height="6" rx="3" fill="#c9cdf5" />
          <circle cx="60" cy="16" r="4" fill="#c9cdf5" />
          <path d="M60 20v6" stroke="#c9cdf5" stroke-width="3" stroke-linecap="round" />
        </svg>
        <p class="empty-text">快去创建你的第一份需求图纸吧</p>
        <button type="button" class="empty-btn" @click="router.push('/')">去创建</button>
      </div>

      <div v-else class="doc-list">
        <button
          v-for="item in archive.items"
          :key="item.id"
          type="button"
          class="doc-item card"
          @click="router.push(`/doc/${item.id}`)"
        >
          <div class="doc-item-top">
            <p class="doc-item-title">{{ item.title }}</p>
            <span class="doc-badge">已生成</span>
          </div>
          <p class="doc-item-meta">{{ item.created_at }}</p>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.icon-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #fff;
  flex: none;
}

.icon-btn:active {
  background: rgba(255, 255, 255, 0.2);
}

.history-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0 10px;
}

.empty-text {
  font-size: 14px;
  color: var(--ink-2);
  margin: 14px 0 16px;
}

.empty-btn {
  height: 40px;
  padding: 0 24px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
  font-weight: 600;
}

.doc-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.doc-item {
  padding: 14px 16px;
  text-align: left;
  transition: transform 0.15s;
}

.doc-item:active {
  transform: scale(0.98);
}

.doc-item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.doc-badge {
  margin-top: 2px;
}

.doc-item-title {
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #e9f7f2;
  color: #0d7a63;
  flex: none;
}

.doc-item-meta {
  font-size: 12px;
  color: var(--ink-3);
  margin-top: 6px;
}

/* ================= 2026 视觉升级 ================= */
.history-body {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 24px 20px 92px;
}

.doc-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px;
}

.doc-item {
  padding: 18px;
  border-radius: 18px;
  transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s;
}

.doc-item:hover {
  transform: translateY(-3px);
  border-color: rgba(79, 70, 229, 0.32);
  box-shadow: var(--shadow-lg);
}

.doc-item-title {
  font-size: 15.5px;
  font-weight: 600;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  white-space: normal;
  line-height: 1.5;
}

.doc-badge {
  background: linear-gradient(135deg, #e9f7f2, #e6f6ff);
}

.empty-state {
  padding: 72px 0;
}

.empty-text {
  font-size: 14.5px;
  color: var(--ink-2);
}

.empty-btn {
  background: var(--grad);
  box-shadow: 0 14px 26px -14px rgba(79, 70, 229, 0.85);
}

@media (max-width: 760px) {
  .history-body {
    padding: 16px 12px 84px;
  }

  .doc-list {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}
</style>
