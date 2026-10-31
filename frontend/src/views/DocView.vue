<!-- 报告详情：正文、待确认项验收、成熟度评分、交付物、版本与导出。 -->
<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import html2canvas from 'html2canvas'
import { api } from '../api'
import { useArchiveStore } from '../stores/archive'
import { saveImageFile, savePdfFile, saveTextFile } from '../utils/export'
import { showToast } from '../utils/toast'
import MarkdownDoc from '../components/MarkdownDoc.vue'
import AssessmentCard from '../components/AssessmentCard.vue'
import DeliverablesCard from '../components/DeliverablesCard.vue'
import AbPlanCard from '../components/AbPlanCard.vue'

const route = useRoute()
const router = useRouter()
const archive = useArchiveStore()
archive.load()

const item = computed(() => archive.getById(route.params.id))
const docRef = ref(null)
const exporting = ref(false)


const confirmItems = computed(() => (item.value && item.value.confirmItems) || [])
const acceptance = computed(() => (item.value && item.value.acceptance) || null)

const KIND_LABEL = { ambiguous: '描述模糊', missing: '信息缺失', conflict: '说法矛盾' }
const DECISION_LABEL = { confirmed: '已确认', na: '不涉及', note: '补充说明' }
const DECISIONS = [
  { key: 'confirmed', label: '已确认' },
  { key: 'na', label: '不涉及' },
  { key: 'note', label: '补充说明' }
]

const decisions = ref([])
watch(confirmItems, () => {
  decisions.value = confirmItems.value.map(() => ({ decision: '', note: '' }))
}, { immediate: true })

const decidedCount = computed(
  () => decisions.value.filter((d) => !!d.decision).length
)
const decisionPercent = computed(() => {
  if (!confirmItems.value.length) return 0
  return Math.round((decidedCount.value / confirmItems.value.length) * 100)
})

function markAllConfirmed() {
  decisions.value.forEach((d) => {
    if (!d.decision) {
      d.decision = 'confirmed'
    }
  })
}

const allDecided = computed(
  () => decisions.value.length > 0 && decisions.value.every((d) => d.decision)
)
const accepting = ref(false)

function kindLabel(k) {
  return KIND_LABEL[k] || '待确认'
}

function decisionText(d) {
  return DECISION_LABEL[d] || d || '未填写'
}

async function confirmAccept() {
  if (!item.value || accepting.value || !allDecided.value) return
  accepting.value = true
  try {
    const resolutions = confirmItems.value.map((it, i) => ({
      title: it.title,
      detail: it.detail,
      kind: it.kind,
      decision: decisions.value[i].decision,
      note: (decisions.value[i].note || '').trim()
    }))
    const result = await api.accept(item.value.document, confirmItems.value, resolutions, item.value.id)
    archive.setAcceptance(item.value.id, result)
    showToast('验收完成，凭证已生成', 'success')
  } catch (e) {
    showToast(e.message || '验收失败，请重试', 'error')
  } finally {
    accepting.value = false
  }
}


const assessment = computed(() => (item.value && item.value.assessment) || null)
const scoring = ref(false)

async function loadAssessment() {
  if (!item.value || scoring.value || assessment.value) return
  scoring.value = true
  try {
    const a = await api.assessment(item.value.document)
    archive.setAssessment(item.value.id, a && Object.keys(a).length ? a : null)
  } catch (e) {
    showToast(e.message || '评分生成失败', 'error')
  } finally {
    scoring.value = false
  }
}


const deliverables = computed(() => (item.value && item.value.deliverables) || null)
const dLoading = ref(false)

async function loadDeliverables() {
  if (!item.value || dLoading.value || deliverables.value) return
  dLoading.value = true
  try {
    const d = await api.deliverables(item.value.document)
    archive.setDeliverables(item.value.id, d || null)
  } catch (e) {
    showToast(e.message || '生成交付物失败', 'error')
  } finally {
    dLoading.value = false
  }
}


const abPlan = computed(() => (item.value && item.value.abPlan) || null)
const abLoading = ref(false)

async function loadAbPlan() {
  if (!item.value || abLoading.value || abPlan.value) return
  abLoading.value = true
  try {
    const p = await api.abPlan(item.value.document)
    archive.setAbPlan(item.value.id, p && (p.plan_a || p.plan_b) ? p : null)
  } catch (e) {
    showToast(e.message || '生成方案失败', 'error')
  } finally {
    abLoading.value = false
  }
}


const versions = computed(() => (item.value && item.value.versions) || [])
const currentVersion = computed(() => {
  if (versions.value.length) return 'v' + versions.value[versions.value.length - 1].version
  return 'v1'
})
const showRevision = ref(false)
const revisionText = ref('')
const revising = ref(false)
const draft = ref(null) 
const acceptDrafting = ref(false)
const openDiff = ref(null) 

async function submitRevision() {
  if (!item.value || revising.value || !revisionText.value.trim()) return
  revising.value = true
  try {
    const r = await api.revision(item.value.document, revisionText.value.trim())
    draft.value = r || { document: '', confirm_items: [], assessment: null }
  } catch (e) {
    showToast(e.message || '生成新版本失败', 'error')
  } finally {
    revising.value = false
  }
}

async function acceptDraft() {
  if (!item.value || !draft.value || acceptDrafting.value) return
  acceptDrafting.value = true
  try {
    const result = await api.accept(
      draft.value.document,
      draft.value.confirm_items || [],
      [],
      item.value.id
    )
    archive.updateDocument(item.value.id, draft.value.document, draft.value.confirm_items, draft.value.assessment)
    archive.setAcceptance(item.value.id, result)
    draft.value = null
    revisionText.value = ''
    showRevision.value = false
    showToast(`已验收为新版本 ${currentVersion.value}`, 'success')
  } catch (e) {
    showToast(e.message || '验收失败，请重试', 'error')
  } finally {
    acceptDrafting.value = false
  }
}

function cancelDraft() {
  draft.value = null
  revisionText.value = ''
}


function voucherMarkdown(a) {
  const lines = []
  lines.push('# 需求诊断验收凭证')
  lines.push('')
  lines.push(`- 验收编号：${a.id}`)
  lines.push(`- 客户账号：${a.username}`)
  lines.push(`- 验收时间：${a.accepted_at}`)
  lines.push(`- 版本：v${a.version || 1}`)
  lines.push(`- 报告标题：${item.value ? item.value.title : ''}`)
  lines.push(`- 验收哈希（SHA-256）：${a.doc_hash}`)
  lines.push('')
  if (Array.isArray(a.resolutions) && a.resolutions.length) {
    lines.push('## 逐项确认结论')
    lines.push('')
    a.resolutions.forEach((r, i) => {
      const note = r.note ? `（${r.note}）` : ''
      lines.push(`${i + 1}. 【${kindLabel(r.kind)}】${r.title || r.detail} → ${decisionText(r.decision)}${note}`)
    })
    lines.push('')
  }
  if (a.diff) {
    lines.push('## 相对上一版本的变更')
    lines.push('')
    lines.push('```diff')
    lines.push(a.diff)
    lines.push('```')
    lines.push('')
  }
  lines.push('## 报告正文')
  lines.push('')
  lines.push(item.value ? item.value.document : '')
  return lines.join('\n')
}

function exportVoucher() {
  if (!acceptance.value || !item.value) return
  const mode = saveTextFile(`${item.value.title}-验收凭证.md`, voucherMarkdown(acceptance.value))
  showToast(mode === 'native' ? '已保存到「下载」目录' : '验收凭证已导出', 'success')
}

function exportMarkdown() {
  if (!item.value) return
  const mode = saveTextFile(`${item.value.title}.md`, item.value.document)
  showToast(mode === 'native' ? '已保存到「下载」目录' : 'MD 文件已导出', 'success')
}

async function exportImage() {
  if (exporting.value || !docRef.value || !item.value) return
  exporting.value = true
  try {
    // 2 倍分辨率渲染报告区域，导出后放大查看也不糊。
    const canvas = await html2canvas(docRef.value, {
      backgroundColor: '#f4f6fb',
      scale: 2,
      useCORS: true,
      windowWidth: docRef.value.scrollWidth
    })
    const dataUrl = canvas.toDataURL('image/png')
    const mode = saveImageFile(`${item.value.title}.png`, dataUrl)
    showToast(mode === 'native' ? '已保存到相册' : '长截图已导出', 'success')
  } catch {
    showToast('长截图生成失败，请重试', 'error')
  } finally {
    exporting.value = false
  }
}

async function exportPdf() {
  if (exporting.value || !item.value) return
  exporting.value = true
  try {
    
    const blob = await api.exportPdf(item.value.document)
    const mode = savePdfFile(`${item.value.title}.pdf`, blob)
    showToast(mode === 'native' ? '已保存到「下载」目录' : 'PDF 已导出', 'success')
  } catch (e) {
    showToast(e.message || 'PDF 导出失败，请重试', 'error')
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div class="doc-page">
    <header class="doc-header">
      <button type="button" class="icon-btn" @click="router.push('/')">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M15 5l-7 7 7 7" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
      <div class="doc-title">
        <h1>{{ item ? item.title : '需求诊断报告' }}</h1>
        <p v-if="item">{{ item.created_at }}</p>
      </div>
    </header>

    <div class="doc-body">
      <div v-if="!item" class="empty-tip">文档不存在或已删除</div>
      <template v-else>
        <div ref="docRef" class="doc-capture">
          <MarkdownDoc :source="item.document" />
        </div>

        
        <section v-if="confirmItems.length && !acceptance" class="section card">
          <div class="confirm-head-row">
            <div>
              <h2 class="sec-title">待确认事项</h2>
              <p class="sec-hint">
                生成报告时发现以下事项需要您确认或拍板，请逐项选择（只确认/补充，不重新生成报告）：
              </p>
            </div>
            <div class="confirm-tools">
              <span class="progress-pill" :class="{ all: allDecided }">
                已确认 {{ decidedCount }} / {{ confirmItems.length }}
              </span>
              <button
                v-if="!allDecided"
                type="button"
                class="batch-confirm-btn"
                @click="markAllConfirmed"
              >
                一键全部已确认
              </button>
            </div>
          </div>

          <div class="confirm-progress-track">
            <div class="confirm-progress-fill" :style="{ width: decisionPercent + '%' }"></div>
          </div>

          <div v-for="(it, i) in confirmItems" :key="i" class="confirm-item">
            <div class="item-head">
              <span class="kind-badge" :class="'kind-' + it.kind">{{ kindLabel(it.kind) }}</span>
              <span class="item-title">{{ it.title }}</span>
            </div>
            <p class="item-detail">{{ it.detail }}</p>
            <div class="decide-options">
              <button
                v-for="opt in DECISIONS"
                :key="opt.key"
                type="button"
                class="decide-btn"
                :class="{ on: decisions[i] && decisions[i].decision === opt.key }"
                @click="decisions[i].decision = opt.key"
              >
                {{ opt.label }}
              </button>
            </div>
            <textarea
              v-if="decisions[i] && decisions[i].decision === 'note'"
              v-model="decisions[i].note"
              rows="2"
              class="decide-note"
              placeholder="写下你的补充说明…"
            ></textarea>
          </div>
          <button
            type="button"
            class="btn-main"
            :disabled="!allDecided || accepting"
            @click="confirmAccept"
          >
            <span v-if="accepting" class="spin"></span>
            <span v-else-if="allDecided">确认验收</span>
            <span v-else>确认验收（还剩 {{ confirmItems.length - decidedCount }} 项待决定）</span>
          </button>
        </section>

        
        <section v-if="acceptance" class="section card">
          <h2 class="sec-title">验收凭证</h2>
          <div class="voucher">
            <div class="v-row"><span>验收编号</span><b>#{{ acceptance.id }}</b></div>
            <div class="v-row"><span>版本</span><b>{{ currentVersion }}</b></div>
            <div class="v-row"><span>验收账号</span><b>{{ acceptance.username }}</b></div>
            <div class="v-row"><span>验收时间</span><b>{{ acceptance.accepted_at }}</b></div>
            <div class="v-row"><span>验收哈希</span><b class="hash">{{ acceptance.doc_hash }}</b></div>
          </div>
          <div v-if="acceptance.resolutions && acceptance.resolutions.length" class="v-resolutions">
            <div v-for="(r, i) in acceptance.resolutions" :key="i" class="v-res">
              <span class="kind-badge" :class="'kind-' + r.kind">{{ kindLabel(r.kind) }}</span>
              <span class="v-res-title">{{ r.title || r.detail }}</span>
              <span class="v-res-decision">{{ decisionText(r.decision) }}</span>
              <span v-if="r.note" class="v-res-note">{{ r.note }}</span>
            </div>
          </div>
          <button type="button" class="btn-main" @click="exportVoucher">导出验收凭证</button>
        </section>

        
        <section class="section card">
          <h2 class="sec-title">需求成熟度诊断</h2>
          <AssessmentCard v-if="assessment" :assessment="assessment" />
          <div v-else class="lazy-wrap">
            <p class="sec-hint">生成一份成熟度评分 + 风险清单，一眼看清需求还想清了没。</p>
            <button type="button" class="btn-main" :disabled="scoring" @click="loadAssessment">
              <span v-if="scoring" class="spin"></span>
              <span v-else>生成需求成熟度评分</span>
            </button>
          </div>
        </section>

        
        <section class="section card">
          <h2 class="sec-title">可交付物</h2>
          <DeliverablesCard
            v-if="deliverables"
            :deliverables="deliverables"
            :doc-title="item ? item.title : '需求诊断报告'"
          />
          <div v-else class="lazy-wrap">
            <p class="sec-hint">
              生成三件能直接拿去谈开发的东西：需求规格说明书、询价清单、成本工期估算。
            </p>
            <button type="button" class="btn-main" :disabled="dLoading" @click="loadDeliverables">
              <span v-if="dLoading" class="spin"></span>
              <span v-else>生成三件套交付物</span>
            </button>
          </div>
        </section>

        
        <section class="section card">
          <h2 class="sec-title">方案对比</h2>
          <AbPlanCard v-if="abPlan" :plan="abPlan" />
          <div v-else class="lazy-wrap">
            <p class="sec-hint">给出「最小可行版」和「一步到位版」两套方案，帮您做决定。</p>
            <button type="button" class="btn-main" :disabled="abLoading" @click="loadAbPlan">
              <span v-if="abLoading" class="spin"></span>
              <span v-else>生成 A/B 方案对比</span>
            </button>
          </div>
        </section>

        
        <section class="section card">
          <h2 class="sec-title">版本与修订</h2>
          <p class="sec-hint">当前版本：<b>{{ currentVersion }}</b>。每次修订并验收都会生成新版本并记录变更。</p>

          <div v-if="versions.length" class="versions">
            <div v-for="v in versions" :key="v.version" class="version">
              <button type="button" class="version-row" @click="openDiff = openDiff === v.version ? null : v.version">
                <span class="version-tag">v{{ v.version }}</span>
                <span class="version-time">{{ v.accepted_at }}</span>
                <span class="version-toggle">{{ openDiff === v.version ? '收起' : '查看变更' }}</span>
              </button>
              <pre v-if="openDiff === v.version" class="diff">{{ v.diff || '（这是首个版本，无变更记录）' }}</pre>
            </div>
          </div>

          <template v-if="!draft">
            <template v-if="!showRevision">
              <button type="button" class="btn-ghost2" @click="showRevision = true">发起修订（生成新版本）</button>
            </template>
            <template v-else>
              <textarea
                v-model="revisionText"
                rows="3"
                class="decide-note"
                placeholder="写下要补充或修改的内容，例如：预算改成 8 万、上线时间提前到 11 月、再加一个后台管理功能…"
              ></textarea>
              <div class="rev-actions">
                <button type="button" class="btn-ghost2" @click="showRevision = false; revisionText = ''">取消</button>
                <button type="button" class="btn-main sm" :disabled="revising || !revisionText.trim()" @click="submitRevision">
                  <span v-if="revising" class="spin"></span>
                  <span v-else>生成新版本</span>
                </button>
              </div>
            </template>
          </template>

          
          <div v-if="draft" class="draft card">
            <div class="draft-head">
              <span class="draft-title">新版本草稿（v{{ versions.length + 1 }}）</span>
              <button type="button" class="draft-cancel" @click="cancelDraft">取消</button>
            </div>
            <div class="draft-body">
              <MarkdownDoc :source="draft.document" />
            </div>
            <button type="button" class="btn-main" :disabled="acceptDrafting" @click="acceptDraft">
              <span v-if="acceptDrafting" class="spin"></span>
              <span v-else>验收为新版本</span>
            </button>
          </div>
        </section>
      </template>
    </div>

    <div class="doc-footer">
      <button type="button" class="btn-ghost" :disabled="!item" @click="exportMarkdown">
        导出 MD
      </button>
      <button
        type="button"
        class="btn-ghost"
        :disabled="!item || exporting"
        @click="exportPdf"
      >
        <span v-if="exporting" class="spin"></span>
        <span v-else>导出 PDF</span>
      </button>
      <button
        type="button"
        class="btn-primary"
        :disabled="!item || exporting"
        @click="exportImage"
      >
        <span v-if="exporting" class="spin"></span>
        <span v-else>导出长截图</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.doc-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  padding-top: max(14px, env(safe-area-inset-top));
  background: var(--card);
  border-bottom: 1px solid var(--line);
  flex: none;
}

.icon-btn {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--ink);
  flex: none;
}

.icon-btn:active {
  background: var(--accent-soft);
}

.doc-title {
  flex: 1;
  min-width: 0;
}

.doc-title h1 {
  font-size: 16px;
  font-weight: 650;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-title p {
  margin: 1px 0 0;
  font-size: 12px;
  color: var(--ink-3);
}

.doc-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 96px;
}

.empty-tip {
  text-align: center;
  font-size: 13px;
  color: var(--ink-3);
  padding: 40px 0;
}

.doc-footer {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 1080px;
  padding: 10px 16px calc(12px + env(safe-area-inset-bottom));
  background: var(--card);
  border-top: 1px solid var(--line);
  display: flex;
  gap: 10px;
}

.btn-ghost {
  flex: 1;
  height: 46px;
  border-radius: 14px;
  font-weight: 600;
  background: var(--accent-soft);
  color: var(--accent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-ghost:disabled {
  opacity: 0.5;
}

.btn-primary {
  flex: 1;
  height: 46px;
  border-radius: 14px;
  font-weight: 600;
  background: var(--accent);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-primary:disabled {
  background: #c7cbe0;
}


.section {
  margin-top: 16px;
  padding: 18px 16px;
}

.sec-title {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 700;
}

.sec-hint {
  margin: 0 0 16px;
  font-size: 12.5px;
  color: var(--ink-2);
  line-height: 1.6;
}

.sec-hint b {
  color: var(--accent);
}

.btn-main {
  width: 100%;
  height: 46px;
  margin-top: 14px;
  border-radius: 13px;
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: background 0.18s;
}

.btn-main.sm {
  flex: 1;
  margin-top: 0;
  height: 42px;
}

.btn-main:hover:not(:disabled) {
  background: #4338ca;
}

.btn-main:disabled {
  background: #c7cbe0;
  cursor: not-allowed;
}

.lazy-wrap .sec-hint {
  margin-bottom: 4px;
}

.confirm-head-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.confirm-tools {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 2px;
}

.progress-pill {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  background: var(--bg);
  color: var(--ink-2);
  border: 1px solid var(--line);
}

.progress-pill.all {
  background: #e6f6ee;
  color: #059669;
  border-color: #bbf7d0;
}

.batch-confirm-btn {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px solid rgba(79, 70, 229, 0.25);
  cursor: pointer;
  transition: all 0.16s ease;
}

.batch-confirm-btn:hover {
  background: var(--accent);
  color: #fff;
  transform: translateY(-1px);
}

.confirm-progress-track {
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
  margin-bottom: 16px;
}

.confirm-progress-fill {
  height: 100%;
  border-radius: 999px;
  background: var(--grad);
  transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.confirm-item {
  padding: 14px 0;
  border-top: 1px solid var(--line);
}

.confirm-item:first-of-type {
  border-top: none;
  padding-top: 4px;
}

.item-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.kind-badge {
  flex: none;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.kind-ambiguous {
  background: #fef3c7;
  color: #b45309;
}

.kind-missing {
  background: #fee2e2;
  color: #b91c1c;
}

.kind-conflict {
  background: #ede9fe;
  color: #6d28d9;
}

.item-title {
  font-size: 14.5px;
  font-weight: 650;
  color: var(--ink);
}

.item-detail {
  margin: 8px 0 12px;
  font-size: 13.5px;
  color: var(--ink-2);
  line-height: 1.65;
}

.decide-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.decide-btn {
  flex: 1;
  min-width: 80px;
  height: 38px;
  border-radius: 10px;
  background: var(--bg);
  border: 1.5px solid var(--line);
  color: var(--ink-2);
  font-size: 13px;
  transition: all 0.16s;
}

.decide-btn.on {
  background: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 650;
}

.decide-note {
  width: 100%;
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: var(--card);
  border: 1.5px solid var(--line);
  color: var(--ink);
  font-size: 13.5px;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.16s;
}

.decide-note:focus {
  border-color: var(--accent);
}


.voucher {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.v-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg);
  border-radius: 10px;
}

.v-row span {
  font-size: 12.5px;
  color: var(--ink-3);
  flex: none;
}

.v-row b {
  font-size: 13px;
  color: var(--ink);
  word-break: break-all;
  text-align: right;
}

.v-row b.hash {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  color: var(--accent);
}

.v-resolutions {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.v-res {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px 0;
  border-top: 1px solid var(--line);
}

.v-res-title {
  font-size: 13px;
  color: var(--ink);
  flex: 1;
  min-width: 0;
}

.v-res-decision {
  flex: none;
  font-size: 12px;
  font-weight: 650;
  color: var(--accent);
}

.v-res-note {
  width: 100%;
  font-size: 12px;
  color: var(--ink-2);
}

.versions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.version-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg);
  border-radius: 10px;
}

.version-tag {
  flex: none;
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
  background: var(--accent-soft);
  padding: 2px 9px;
  border-radius: 999px;
}

.version-time {
  flex: 1;
  font-size: 12.5px;
  color: var(--ink-2);
  text-align: left;
}

.version-toggle {
  flex: none;
  font-size: 12px;
  color: var(--ink-3);
}

.diff {
  margin: 8px 0 0;
  padding: 12px;
  border-radius: 10px;
  background: #0f172a;
  color: #e2e8f0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 11px;
  line-height: 1.55;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.btn-ghost2 {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.rev-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.rev-actions .btn-ghost2 {
  flex: 1;
}

.draft {
  margin-top: 14px;
  padding: 14px;
  border-style: dashed;
  border-color: var(--accent);
}

.draft-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.draft-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--accent);
}

.draft-cancel {
  font-size: 12.5px;
  color: var(--ink-3);
  padding: 4px 8px;
}

.draft-body {
  max-height: 360px;
  overflow-y: auto;
  padding: 12px;
  border-radius: 10px;
  background: var(--bg);
}

@media (max-width: 640px) {
  .doc-body {
    padding: 12px;
    padding-bottom: 96px;
  }
}

/* ================= 2026 视觉升级 ================= */
.doc-header {
  margin: 14px 4px 0;
  padding: 12px 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(16px);
  box-shadow: var(--shadow-sm);
}

.doc-title h1 {
  font-size: 17px;
  font-weight: 700;
}

.doc-body {
  width: 100%;
  max-width: 940px;
  margin: 0 auto;
  padding: 20px 20px 124px;
}

.doc-capture {
  padding: 32px 36px;
  border-radius: 22px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: #fff;
  box-shadow: var(--shadow);
}

.section {
  margin-top: 18px;
  padding: 24px 26px;
  border-radius: 20px;
  border-color: rgba(226, 232, 240, 0.9);
}

.sec-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 18px;
  letter-spacing: -0.2px;
}

.sec-title::before {
  content: '';
  width: 4px;
  height: 18px;
  border-radius: 999px;
  background: var(--grad);
  flex: none;
}

.sec-hint {
  font-size: 13px;
  line-height: 1.7;
}

.btn-main,
.btn-primary {
  background: var(--grad);
  box-shadow: 0 16px 30px -18px rgba(79, 70, 229, 0.9);
}

.btn-main:hover:not(:disabled),
.btn-primary:hover:not(:disabled) {
  background: var(--grad);
  filter: brightness(1.06);
}

.btn-main:disabled,
.btn-primary:disabled {
  background: #e3e7f4;
  color: #9aa4ba;
  box-shadow: none;
}

.btn-ghost {
  background: rgba(238, 241, 255, 0.9);
  border: 1px solid #e0e4ff;
}

.btn-ghost2 {
  background: rgba(238, 241, 255, 0.85);
  border: 1px solid #e0e4ff;
}

.doc-footer {
  max-width: 940px;
  padding: 10px 14px calc(12px + env(safe-area-inset-bottom));
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-bottom: none;
  border-radius: 18px 18px 0 0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(18px);
  box-shadow: 0 -18px 40px -28px rgba(30, 41, 90, 0.4);
}

.confirm-item {
  padding: 16px 0;
}

.voucher {
  border-radius: 14px;
}

.draft {
  border-radius: 16px;
}

@media (max-width: 760px) {
  .doc-header {
    margin: 8px 2px 0;
    padding: 10px 12px;
    border-radius: 14px;
  }

  .doc-title h1 {
    font-size: 15.5px;
  }

  .doc-body {
    padding: 12px 12px 108px;
  }

  .doc-capture {
    padding: 20px 16px;
    border-radius: 16px;
  }

  .section {
    padding: 18px 15px;
    border-radius: 16px;
  }

  .sec-title {
    font-size: 16.5px;
  }

  .doc-footer {
    width: calc(100% - 12px);
    border-radius: 16px 16px 0 0;
  }

  .btn-ghost,
  .btn-primary {
    height: 44px;
    font-size: 13.5px;
  }
}
</style>
