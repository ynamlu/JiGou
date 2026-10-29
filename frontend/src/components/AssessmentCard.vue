<script setup>
import { computed } from 'vue'

const props = defineProps({
  assessment: { type: Object, default: null }
})

const DIM_LABELS = {
  form: '产品形态',
  users: '目标用户',
  features: '核心功能',
  cost: '预算',
  time: '上线时间',
  compliance: '合规资质'
}

const RISK_META = {
  high: { label: '高风险', color: '#dc2626', bg: '#fee2e2' },
  medium: { label: '中风险', color: '#b45309', bg: '#fef3c7' },
  low: { label: '低风险', color: '#059669', bg: '#d1fae5' }
}

const a = computed(() => props.assessment || null)
const score = computed(() => {
  const s = a.value ? Number(a.value.score) : 0
  return Number.isFinite(s) ? Math.min(100, Math.max(0, Math.round(s))) : 0
})


const R = 40
const CIRC = 2 * Math.PI * R
const dash = computed(() => (score.value / 100) * CIRC)

const scoreColor = computed(() => {
  if (score.value >= 80) return '#059669'
  if (score.value >= 60) return '#4f46e5'
  if (score.value >= 40) return '#b45309'
  return '#dc2626'
})

const dims = computed(() => {
  const d = (a.value && a.value.dimensions) || {}
  return Object.keys(DIM_LABELS).map((k) => ({
    key: k,
    label: DIM_LABELS[k],
    value: Math.min(100, Math.max(0, Number(d[k]) || 0))
  }))
})

const risks = computed(() => (a.value && a.value.risks) || [])

function riskMeta(level) {
  return RISK_META[level] || RISK_META.medium
}
</script>

<template>
  <div v-if="a" class="assessment">
    <div class="score-row">
      <div class="ring-wrap">
        <svg viewBox="0 0 100 100" class="ring">
          <circle class="ring-bg" cx="50" cy="50" :r="R" />
          <circle
            class="ring-fg"
            cx="50"
            cy="50"
            :r="R"
            :stroke="scoreColor"
            :stroke-dasharray="`${dash} ${CIRC}`"
          />
        </svg>
        <div class="ring-num" :style="{ color: scoreColor }">
          {{ score }}
        </div>
      </div>
      <div class="score-meta">
        <div class="score-title">需求成熟度</div>
        <p class="score-summary">{{ a.summary }}</p>
      </div>
    </div>

    <div class="dims">
      <div v-for="d in dims" :key="d.key" class="dim">
        <div class="dim-head">
          <span class="dim-label">{{ d.label }}</span>
          <span class="dim-val">{{ d.value }}</span>
        </div>
        <div class="dim-track">
          <div
            class="dim-fill"
            :class="d.value >= 80 ? 'good' : d.value >= 40 ? 'mid' : 'bad'"
            :style="{ width: d.value + '%' }"
          ></div>
        </div>
      </div>
    </div>

    <div v-if="risks.length" class="risks">
      <div class="risks-title">需要留意的风险</div>
      <div v-for="(r, i) in risks" :key="i" class="risk">
        <span class="risk-tag" :style="{ background: riskMeta(r.level).bg, color: riskMeta(r.level).color }">
          {{ riskMeta(r.level).label }}
        </span>
        <div class="risk-body">
          <div class="risk-title">{{ r.title }}</div>
          <div class="risk-reason">{{ r.reason }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.assessment {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.score-row {
  display: flex;
  align-items: center;
  gap: 18px;
}

.ring-wrap {
  position: relative;
  width: 108px;
  height: 108px;
  flex: none;
}

.ring {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: var(--line);
  stroke-width: 10;
}

.ring-fg {
  fill: none;
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}

.ring-num {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-size: 30px;
  font-weight: 750;
}

.score-meta {
  flex: 1;
  min-width: 0;
}

.score-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 4px;
}

.score-summary {
  margin: 0;
  font-size: 13px;
  color: var(--ink-2);
  line-height: 1.6;
}

.dims {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dim-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.dim-label {
  font-size: 12.5px;
  color: var(--ink-2);
}

.dim-val {
  font-size: 12.5px;
  font-weight: 650;
  color: var(--ink);
}

.dim-track {
  height: 6px;
  border-radius: 999px;
  background: var(--bg);
  overflow: hidden;
}

.dim-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.5s ease;
}

.dim-fill.good {
  background: #059669;
}

.dim-fill.mid {
  background: #4f46e5;
}

.dim-fill.bad {
  background: #dc2626;
}

.risks {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.risks-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
}

.risk {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.risk-tag {
  flex: none;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 650;
  margin-top: 2px;
}

.risk-body {
  flex: 1;
  min-width: 0;
}

.risk-title {
  font-size: 13.5px;
  font-weight: 650;
  color: var(--ink);
}

.risk-reason {
  font-size: 12.5px;
  color: var(--ink-2);
  line-height: 1.6;
}
</style>
