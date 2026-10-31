<script setup>
import { computed, ref } from 'vue'
import MarkdownDoc from './MarkdownDoc.vue'
import { saveTextFile } from '../utils/export'
import { showToast } from '../utils/toast'

const props = defineProps({
  deliverables: { type: Object, default: null },
  docTitle: { type: String, default: '需求诊断报告' }
})

const dTab = ref('prd')
const D_TABS = [
  { key: 'prd', label: '规格说明书' },
  { key: 'rfp', label: '询价清单' },
  { key: 'estimate', label: '成本工期' }
]
const D_NAMES = { prd: '需求规格说明书', rfp: '开发询价清单', estimate: '成本工期估算' }

const activeContent = computed(() => {
  return (props.deliverables && props.deliverables[dTab.value]) || ''
})

function exportActive() {
  const content = activeContent.value
  if (!content) return
  const mode = saveTextFile(`${props.docTitle}-${D_NAMES[dTab.value]}.md`, content)
  showToast(mode === 'native' ? '已保存到「下载」目录' : `${D_NAMES[dTab.value]}已导出`, 'success')
}
</script>

<template>
  <div v-if="deliverables" class="deliverables-wrap">
    <div class="tabs">
      <button
        v-for="t in D_TABS"
        :key="t.key"
        type="button"
        class="tab"
        :class="{ on: dTab === t.key }"
        @click="dTab = t.key"
      >
        {{ t.label }}
      </button>
    </div>
    <div class="deliverable-body">
      <MarkdownDoc v-if="activeContent" :source="activeContent" />
      <p v-else class="empty-tip">暂无内容</p>
    </div>
    <button type="button" class="btn-main" @click="exportActive">
      导出「{{ D_NAMES[dTab] }}」
    </button>
  </div>
</template>

<style scoped>
.deliverables-wrap {
  display: flex;
  flex-direction: column;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--line);
  padding-bottom: 10px;
  overflow-x: auto;
}

.tab {
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--ink-2);
  background: var(--bg);
  border: 1px solid var(--line);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.16s ease;
}

.tab:hover {
  background: var(--accent-soft);
  color: var(--accent);
}

.tab.on {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  box-shadow: 0 4px 12px -3px rgba(79, 70, 229, 0.6);
}

.deliverable-body {
  margin-bottom: 16px;
  min-height: 120px;
}

.empty-tip {
  color: var(--ink-3);
  font-size: 14px;
  padding: 24px 0;
  text-align: center;
}

.btn-main {
  width: 100%;
  height: 44px;
  border-radius: 13px;
  background: var(--grad);
  color: #fff;
  font-size: 14.5px;
  font-weight: 650;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 10px 22px -10px rgba(79, 70, 229, 0.85);
  transition: transform 0.16s, filter 0.16s;
}

.btn-main:hover {
  filter: brightness(1.06);
  transform: translateY(-1px);
}
</style>
