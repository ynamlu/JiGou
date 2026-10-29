<script setup>
import { ref, watch } from 'vue'
import { speechSupported, createSpeech } from '../utils/speech'

const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const multiSet = ref([])


const micSupported = speechSupported()
const listening = ref(false)
let rec = null

function toggleMic() {
  if (!micSupported) return
  if (rec) {
    rec.stop()
    rec = null
    listening.value = false
    return
  }
  rec = createSpeech({
    onText: (t) => emit('update:modelValue', t),
    onState: (s) => {
      listening.value = s
      if (!s) rec = null
    }
  })
  rec.start()
}


function parseMulti(v) {
  if (Array.isArray(v)) return [...v]
  if (!v) return []
  try {
    const arr = JSON.parse(v)
    return Array.isArray(arr) ? arr : [String(v)]
  } catch {
    
    return String(v).split('、').filter(Boolean)
  }
}

watch(
  () => [props.question, props.modelValue],
  ([q, v]) => {
    if (q && q.type === 'multi') {
      multiSet.value = parseMulti(v)
    }
  },
  { immediate: true }
)

const q = () => props.question || {}

function pick(opt) {
  emit('update:modelValue', opt)
}

function toggle(opt) {
  const s = new Set(multiSet.value)
  if (s.has(opt)) s.delete(opt)
  else s.add(opt)
  multiSet.value = [...s]
  
  emit('update:modelValue', multiSet.value.length ? JSON.stringify(multiSet.value) : '')
}

function onText(e) {
  emit('update:modelValue', e.target.value)
}

function onQuick(opt) {
  emit('update:modelValue', opt)
}
</script>

<template>
  <div class="qcard">
    <h2 class="q-title">{{ q().question }}</h2>
    <p v-if="q().hint" class="q-hint">{{ q().hint }}</p>

    
    <div v-if="q().type === 'single'" class="opts">
      <button
        v-for="opt in q().options"
        :key="opt"
        type="button"
        class="opt"
        :class="{ on: modelValue === opt }"
        @click="pick(opt)"
      >
        <span class="dot">{{ modelValue === opt ? '●' : '○' }}</span>
        <span class="opt-text">{{ opt }}</span>
      </button>
    </div>

    
    <div v-else-if="q().type === 'multi'" class="opts">
      <button
        v-for="opt in q().options"
        :key="opt"
        type="button"
        class="opt"
        :class="{ on: multiSet.includes(opt) }"
        @click="toggle(opt)"
      >
        <span class="check">{{ multiSet.includes(opt) ? '☑' : '☐' }}</span>
        <span class="opt-text">{{ opt }}</span>
      </button>
      <p class="multi-tip">可多选，选完直接点「下一题」</p>
    </div>

    
    <div v-else class="fill">
      <textarea
        :value="modelValue"
        rows="3"
        :placeholder="q().placeholder || '请在这里填写…'"
        @input="onText"
      ></textarea>
      <button
        v-if="micSupported"
        type="button"
        class="fill-mic"
        :class="{ on: listening }"
        @click="toggleMic"
      >
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 1a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
          <path d="M19 10v1a7 7 0 0 1-14 0v-1M12 18v4M8 22h8" />
        </svg>
        <span>{{ listening ? '正在聆听…' : '语音输入' }}</span>
      </button>
    </div>

    
    <div v-if="q().quick && q().quick.length" class="quick">
      <span class="quick-label">或快速选择：</span>
      <div class="quick-list">
        <button
          v-for="opt in q().quick"
          :key="opt"
          type="button"
          class="chip"
          :class="{ on: modelValue === opt }"
          @click="onQuick(opt)"
        >
          {{ opt }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.qcard {
  display: flex;
  flex-direction: column;
}

.q-title {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.5;
}

.q-hint {
  margin: 0 0 18px;
  font-size: 13.5px;
  color: var(--ink-2);
}

.opts {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.opt {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--card);
  border: 1.5px solid var(--line);
  color: var(--ink);
  text-align: left;
  transition: all 0.16s;
}

.opt:active {
  transform: scale(0.99);
}

.opt.on {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.dot,
.check {
  flex: none;
  font-size: 17px;
  color: var(--ink-3);
  width: 20px;
  text-align: center;
}

.opt.on .dot,
.opt.on .check {
  color: var(--accent);
}

.opt-text {
  font-size: 15px;
  line-height: 1.5;
}

.multi-tip {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--ink-3);
}

.fill textarea {
  width: 100%;
  min-height: 96px;
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--card);
  border: 1.5px solid var(--line);
  color: var(--ink);
  font-size: 15px;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.16s;
}

.fill textarea:focus {
  border-color: var(--accent);
}

.fill-mic {
  margin-top: 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--ink-2);
  font-size: 13px;
  transition: all 0.16s;
}

.fill-mic.on {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.quick {
  margin-top: 16px;
}

.quick-label {
  font-size: 12.5px;
  color: var(--ink-3);
}

.quick-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.chip {
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--card);
  border: 1px solid var(--line);
  color: var(--ink-2);
  font-size: 13.5px;
  transition: all 0.16s;
}

.chip.on {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
}

/* ================= 2026 视觉升级 ================= */
.q-title {
  font-size: 22px;
  letter-spacing: -0.3px;
  line-height: 1.45;
}

.q-hint {
  font-size: 13.5px;
  margin-bottom: 20px;
}

.opt {
  padding: 15px 16px;
  border-radius: 15px;
  border-color: rgba(226, 232, 240, 0.95);
  background: #fcfdff;
  transition: transform 0.16s, border-color 0.16s, background 0.16s, box-shadow 0.16s;
}

.opt:hover {
  transform: translateY(-1px);
  border-color: #c9cff7;
  background: #fff;
  box-shadow: var(--shadow-sm);
}

.opt.on {
  border-color: #8b8df0;
  background: linear-gradient(135deg, #eef1ff, #f5efff);
  box-shadow: 0 12px 24px -18px rgba(79, 70, 229, 0.9);
}

.dot,
.check {
  font-size: 18px;
}

.fill textarea {
  border-radius: 15px;
  border-color: rgba(226, 232, 240, 0.95);
  background: #fcfdff;
}

.fill textarea:focus {
  background: #fff;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.08);
}

.chip {
  background: #fbfcff;
  border-color: rgba(226, 232, 240, 0.95);
  padding: 9px 15px;
}

.chip:hover {
  border-color: rgba(79, 70, 229, 0.4);
  color: var(--accent);
  transform: translateY(-1px);
}

@media (max-width: 640px) {
  .q-title {
    font-size: 19px;
  }

  .opt {
    padding: 14px;
  }
}
</style>
