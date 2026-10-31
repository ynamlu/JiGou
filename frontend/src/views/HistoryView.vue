<!-- 我的图纸：从当前账号的本地归档中读取报告列表，支持搜索、删除与状态徽章。 -->
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useArchiveStore } from '../stores/archive'
import { useUserStore } from '../stores/user'
import BottomNav from '../components/BottomNav.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import { showToast } from '../utils/toast'

const router = useRouter()
const archive = useArchiveStore()
const user = useUserStore()

const keyword = ref('')
const itemToDelete = ref(null)

onMounted(() => {
  archive.load()
})

const filteredItems = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return archive.items
  return archive.items.filter(
    (it) =>
      (it.title && it.title.toLowerCase().includes(kw)) ||
      (it.created_at && it.created_at.includes(kw))
  )
})

function askDelete(item) {
  itemToDelete.value = item
}

function cancelDelete() {
  itemToDelete.value = null
}

function confirmDelete() {
  if (!itemToDelete.value) return
  const title = itemToDelete.value.title
  archive.remove(itemToDelete.value.id)
  itemToDelete.value = null
  showToast(`已删除「${title}」`)
}
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
      <!-- 搜索栏（有图纸时展示） -->
      <div v-if="archive.items.length" class="search-box">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="7" />
          <path d="M21 21l-4.3-4.3" />
        </svg>
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索图纸标题或日期…"
        />
        <button v-if="keyword" type="button" class="clear" @click="keyword = ''">×</button>
      </div>

      <!-- 空状态 -->
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

      <!-- 搜索无结果 -->
      <div v-else-if="!filteredItems.length" class="empty-search">
        <p>没有找到与「{{ keyword }}」相关的图纸</p>
      </div>

      <!-- 图纸列表 -->
      <div v-else class="doc-list">
        <div
          v-for="item in filteredItems"
          :key="item.id"
          class="doc-item card"
          @click="router.push(`/doc/${item.id}`)"
        >
          <div class="doc-item-top">
            <p class="doc-item-title">{{ item.title }}</p>
            <button
              type="button"
              class="del-btn"
              title="删除图纸"
              @click.stop="askDelete(item)"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
            </button>
          </div>

          <div class="doc-item-badges">
            <span v-if="item.acceptance" class="doc-badge accepted">
              已验收 v{{ item.acceptance.version || (item.versions && item.versions.length ? item.versions[item.versions.length - 1].version : 1) }}
            </span>
            <span v-else class="doc-badge draft">草稿</span>

            <span v-if="item.assessment && item.assessment.score" class="doc-badge score">
              成熟度 {{ item.assessment.score }}分
            </span>

            <span v-if="item.deliverables" class="doc-badge deliv">
              已出交付物
            </span>
          </div>

          <p class="doc-item-meta">{{ item.created_at }}</p>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <ConfirmModal
      :visible="!!itemToDelete"
      title="确认删除图纸？"
      :content="itemToDelete ? `删除「${itemToDelete.title}」后将无法恢复，确认删除吗？` : ''"
      confirm-text="确认删除"
      cancel-text="取消"
      :danger="true"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />

    <BottomNav />
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
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px 88px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 14px;
  background: var(--card);
  border: 1px solid var(--line);
  margin-bottom: 16px;
  transition: border-color 0.16s, box-shadow 0.16s;
}

.search-box:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.08);
}

.search-box input {
  flex: 1;
  font-size: 14px;
  outline: none;
  border: none;
  background: transparent;
  color: var(--ink);
}

.search-box input::placeholder {
  color: var(--ink-3);
}

.search-box .clear {
  font-size: 18px;
  line-height: 1;
  color: var(--ink-3);
  padding: 2px 4px;
  cursor: pointer;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 72px 0 20px;
}

.empty-text {
  font-size: 14.5px;
  color: var(--ink-2);
  margin: 14px 0 16px;
}

.empty-btn {
  height: 40px;
  padding: 0 24px;
  border-radius: 999px;
  background: var(--grad);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 14px 26px -14px rgba(79, 70, 229, 0.85);
  transition: transform 0.16s;
}

.empty-btn:hover {
  transform: translateY(-1px);
}

.empty-search {
  text-align: center;
  padding: 60px 0;
  color: var(--ink-3);
  font-size: 14px;
}

.doc-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 14px;
}

.doc-item {
  padding: 18px;
  border-radius: 18px;
  cursor: pointer;
  text-align: left;
  transition: transform 0.18s, box-shadow 0.18s, border-color 0.18s;
  display: flex;
  flex-direction: column;
}

.doc-item:hover {
  transform: translateY(-3px);
  border-color: rgba(79, 70, 229, 0.32);
  box-shadow: var(--shadow-lg);
}

.doc-item:active {
  transform: scale(0.99);
}

.doc-item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.doc-item-title {
  font-size: 15.5px;
  font-weight: 600;
  color: #101a34;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
  flex: 1;
  margin: 0;
}

.del-btn {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-3);
  background: transparent;
  flex: none;
  cursor: pointer;
  transition: all 0.16s ease;
}

.del-btn:hover {
  color: #dc2626;
  background: #fee2e2;
}

.doc-item-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin: 10px 0 6px;
}

.doc-badge {
  font-size: 11.5px;
  padding: 2px 9px;
  border-radius: 999px;
  font-weight: 600;
  line-height: 1.5;
}

.doc-badge.accepted {
  background: #e6f6ee;
  color: #059669;
  border: 1px solid #bbf7d0;
}

.doc-badge.draft {
  background: #f1f5f9;
  color: #64748b;
  border: 1px solid #e2e8f0;
}

.doc-badge.score {
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px solid rgba(79, 70, 229, 0.2);
}

.doc-badge.deliv {
  background: #fdf2f8;
  color: #db2777;
  border: 1px solid #fbcfe8;
}

.doc-item-meta {
  font-size: 12px;
  color: var(--ink-3);
  margin: auto 0 0;
  padding-top: 6px;
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
