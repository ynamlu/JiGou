<!-- 主流程：模式选择 → 问卷/自由对话 → 生成报告。 -->
<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { api } from '../api'
import { useChatStore } from '../stores/chat'
import { useQuestionnaireStore, multiToText } from '../stores/questionnaire'
import { useArchiveStore } from '../stores/archive'
import { useAnalysisStore } from '../stores/analysis'
import AppHeader from '../components/AppHeader.vue'
import BottomNav from '../components/BottomNav.vue'
import ChatBubble from '../components/ChatBubble.vue'
import DocCard from '../components/DocCard.vue'
import InspirationChips from '../components/InspirationChips.vue'
import QuestionCard from '../components/QuestionCard.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import { showToast } from '../utils/toast'
import logo from '../assets/logo.png'

const router = useRouter()
const route = useRoute()
const chat = useChatStore()
const quiz = useQuestionnaireStore()
const archive = useArchiveStore()
const analysis = useAnalysisStore()
const { mode } = storeToRefs(analysis) 

const modeChoice = ref(false) 
const confirmMode = ref(null) 
const answer = ref('') 
const note = ref('') 
const noteOpen = ref(false) 
const genLoading = ref(false)
let chatAbortController = null

const showExitConfirm = ref(false) 
let pendingPath = null 

const freeInput = ref('')
const freeRef = ref(null)
const chatMainRef = ref(null)

const canNext = computed(() => !quiz.busy && (answer.value || '').trim() !== '')
const canGenerate = computed(
  () =>
    !chat.busy &&
    !genLoading.value &&
    (quiz.answered.length > 0 || (answer.value || '').trim() !== '' || chat.messages.length > 1)
)
const progressWidth = computed(() => {
  const target = 8 
  return Math.min(100, Math.round((quiz.answered.length / target) * 100)) + '%'
})

const chips = [
  '我想做个奶茶店点单小程序，顾客扫码点餐付款，店里能看订单',
  '我只想做一个能管理会员的系统',
  '我也说不清，就有一堆聊天记录'
]

async function startAnalysis() {
  if (chat.busy) return
  modeChoice.value = true
}

function askMode(m) {
  confirmMode.value = m
}

function confirmStart() {
  const m = confirmMode.value
  confirmMode.value = null
  startMode(m)
}

function startMode(m) {
  modeChoice.value = false
  if (m === 'quiz') {
    quiz.start(chat.sessionId)
    answer.value = ''
    note.value = ''
    noteOpen.value = false
    analysis.start('quiz')
  } else {
    analysis.start('chat')
  }
  analysis.saveDraft()
}

async function goNext() {
  if (!canNext.value) return
  try {
    await quiz.submit(answer.value, note.value)
    answer.value = ''
    note.value = ''
    noteOpen.value = false
    analysis.saveDraft()
  } catch (e) {
    showToast(e.message || '出题失败，请重试', 'error')
  }
}

async function continueAsk() {
  try {
    await quiz.continueAsk()
    answer.value = ''
    note.value = ''
    noteOpen.value = false
    analysis.saveDraft()
  } catch (e) {
    showToast(e.message || '出题失败，请重试', 'error')
  }
}

function goBack() {
  quiz.back()
  answer.value = (quiz.current && quiz.current._prevAnswer) || ''
  note.value = (quiz.current && quiz.current._prevNote) || ''
  noteOpen.value = !!(quiz.current && quiz.current._prevNote)
  analysis.saveDraft()
}

function collectAnswers() {
  
  const list = quiz.answered.map((a) => ({
    question: a.question,
    answer: multiToText(a.answer, a.type),
    note: a.note || ''
  }))
  const cur = quiz.current
  const val = (answer.value || '').trim()
  if (cur && val)
    list.push({
      question: cur.question,
      answer: multiToText(val, cur.type),
      note: (note.value || '').trim()
    })
  return list
}

async function generate() {
  if (!canGenerate.value) return
  genLoading.value = true
  try {
    const data = await api.generateDoc(chat.sessionId, collectAnswers())
    archive.add(data.document, data.confirm_items, data.assessment)
    showToast('文档已保存，可在「我的图纸」中查看', 'success')
    resetToStart()
  } catch (e) {
    showToast(e.message || '文档生成失败', 'error')
  } finally {
    genLoading.value = false
  }
}

function resetToStart() {
  analysis.abandon()
  quiz.reset()
  chat.resetSession()
  answer.value = ''
  note.value = ''
  noteOpen.value = false
  freeInput.value = ''
  modeChoice.value = false
}

function abandonAnalysis() {
  analysis.abandon()
  quiz.reset()
  chat.resetSession()
  answer.value = ''
  note.value = ''
  noteOpen.value = false
  freeInput.value = ''
  modeChoice.value = false
}

function openAbandon() {
  pendingPath = null
  showExitConfirm.value = true
}

function continueAnalysis() {
  showExitConfirm.value = false
  pendingPath = null
}

function confirmExit() {
  const target = pendingPath
  showExitConfirm.value = false
  pendingPath = null
  abandonAnalysis()
  if (target) router.push(target)
}

function scrollChatBottom() {
  nextTick(() => {
    const el = chatMainRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function resizeFree() {
  const el = freeRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 100) + 'px'
}

function onFreeKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendFree()
  }
}

function stopGeneration() {
  if (chatAbortController) {
    chatAbortController.abort()
    chatAbortController = null
  }
}

async function sendFree() {
  const value = freeInput.value.trim()
  if (!value || chat.busy) return
  chat.busy = true
  chatAbortController = new AbortController()
  chat.messages.push({ role: 'user', content: value, done: true })
  chat.messages.push({
    role: 'assistant',
    content: '',
    status: '',
    statusDone: false,
    thinking: true,
    done: false
  })
  const bubble = chat.messages[chat.messages.length - 1]
  freeInput.value = ''
  resizeFree()
  scrollChatBottom()

  let answerText = ''
  try {
    // 后端用 NDJSON 推事件：思考提示、工具调用状态、正文增量、结束/错误。
    await api.chatStream(
      value,
      chat.sessionId,
      (event) => {
        if (event.type === 'tool_start') {
          bubble.status = '正在检索知识库…'
          bubble.statusDone = false
        } else if (event.type === 'thinking') {
          bubble.thinking = true
          if (!bubble.status) bubble.status = '正在思考…'
        } else if (event.type === 'tool_args') {
          const q = event.args && event.args.query
          if (q) bubble.status = `检索「${q}」`
        } else if (event.type === 'tool_end') {
          bubble.status = '已检索知识库'
          bubble.statusDone = true
        } else if (event.type === 'token') {
          bubble.thinking = false
          answerText += event.content || ''
          bubble.content = answerText
        } else if (event.type === 'done') {
          answerText = event.content || answerText
          bubble.content = answerText
        } else if (event.type === 'error') {
          bubble.thinking = false
          answerText += (answerText ? '\n\n' : '') + '> ' + (event.content || '服务端出错')
          bubble.content = answerText
        }
      },
      chatAbortController.signal
    )
  } catch (e) {
    bubble.thinking = false
    if (e.name === 'AbortError') {
      answerText += (answerText ? '\n\n' : '') + '> ⏸ *已停止生成*'
      bubble.content = answerText
    } else {
      answerText +=
        (answerText ? '\n\n' : '') + `> 请求失败：${e.message}（检查后端是否在运行）`
      bubble.content = answerText
    }
  } finally {
    chatAbortController = null
  }

  bubble.thinking = false
  bubble.done = true
  if (bubble.status) bubble.statusDone = true
  if (!String(bubble.content || '').trim()) bubble.content = '（没有收到内容，请重试）'
  if (analysis.active) analysis.saveDraft()
  chat.busy = false
  scrollChatBottom()
}

onBeforeUnmount(() => {
  stopGeneration()
})

onBeforeRouteLeave((to) => {
  if (!analysis.active) return true
  pendingPath = to.fullPath
  showExitConfirm.value = true
  return false
})

onMounted(async () => {
  archive.load()
  analysis.restoreDraft() 
  await chat.init()

  if (route.query.prompt) {
    const promptText = String(route.query.prompt)
    startMode('chat')
    freeInput.value = promptText
    router.replace({ path: '/', query: {} })
    await nextTick()
    resizeFree()
    if (freeRef.value) {
      freeRef.value.focus()
    }
  }
})
</script>

<template>
  <div class="chat-page">
    <AppHeader />

    
    <main v-if="mode === ''" class="main landing" :class="{ choosing: modeChoice }">
      <section class="hero">
        <span class="eyebrow"><i></i>AI 需求诊断 · 本地运行</span>
        <h1>把「我想做个系统」<br /><em>变成一份可执行的需求报告</em></h1>
        <p class="hero-sub">
          说不清需求、看不懂报价？用 12 篇软件开发知识库，帮你判断已经想清楚了什么、
          还缺什么、哪些需要拍板，再给出可以直接拿去谈开发的材料。
        </p>
        <ul class="hero-points">
          <li><span class="tick">✓</span>问卷或对话，几分钟问清关键信息</li>
          <li><span class="tick">✓</span>诊断报告 + 待确认清单 + 六维成熟度评分</li>
          <li><span class="tick">✓</span>PRD、询价清单、成本工期与 A/B 方案</li>
        </ul>
        <div class="hero-stats">
          <div><b>12</b><span>知识库文档</span></div>
          <div><b>6</b><span>评估维度</span></div>
          <div><b>3</b><span>交付物</span></div>
        </div>
      </section>

      <section class="start-entry card">
        <div class="start-icon"><img :src="logo" alt="极构" /></div>
        <span class="start-kicker">开始一次诊断</span>
        <h2>你现在更想怎么聊？</h2>
        <p>
          不确定也没关系，两种方式随时可以换。
        </p>

        <template v-if="!modeChoice">
          <button type="button" class="start-btn" :disabled="chat.busy" @click="startAnalysis">
            开始需求分析
          </button>
          <p class="start-note">已登录 · 报告与验收记录按账号保存</p>
        </template>
        <template v-else>
          <div class="mode-pick">
            <button type="button" class="mode-btn" @click="askMode('quiz')">
              <span class="mode-ico">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="5" y="4" width="14" height="17" rx="2.5" />
                  <path d="M9 4.5V3h6v1.5M9 10h6M9 14h6M9 18h3" />
                </svg>
              </span>
              <span class="mode-body">
                <span class="mode-title">按问卷答题</span>
                <span class="mode-desc">选择题 + 填空题，一题一屏；每道题都能补充你的想法</span>
              </span>
              <span class="mode-arrow">→</span>
            </button>
            <button type="button" class="mode-btn" @click="askMode('chat')">
              <span class="mode-ico">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 12a8 8 0 0 1-8 8H8l-4 3v-5.5A8 8 0 1 1 21 12z" />
                  <path d="M8.5 11h7M8.5 14.5h4" />
                </svg>
              </span>
              <span class="mode-body">
                <span class="mode-title">自由对话</span>
                <span class="mode-desc">像聊天一样直接说，适合已经有比较明确的想法</span>
              </span>
              <span class="mode-arrow">→</span>
            </button>
          </div>
        </template>
      </section>
    </main>

    
    <main v-else-if="mode === 'quiz'" class="main">
        <div v-if="!quiz.finished" class="progress-row">
          <div class="progress-bar"><div class="progress-fill" :style="{ width: progressWidth }"></div></div>
          <span class="progress-label">第 {{ quiz.step }} 题 · 已答 {{ quiz.answered.length }} 题</span>
          <button type="button" class="abandon-link" @click="openAbandon">放弃</button>
        </div>

        <div class="qwrap card">
          <template v-if="quiz.finished">
            <div class="finish-card">
              <div class="finish-icon">✅</div>
              <h3>信息收集得差不多了</h3>
              <p class="finish-summary">{{ quiz.summary }}</p>
              <div class="quiz-nav">
                <button type="button" class="nav-btn" :disabled="quiz.busy" @click="continueAsk">
                  再补充几点
                </button>
                <button type="button" class="nav-btn primary" :disabled="genLoading" @click="generate">
                  <span v-if="genLoading" class="spin"></span>
                  <span v-else>生成需求报告</span>
                </button>
              </div>
              <button type="button" class="abandon-link center" @click="openAbandon">放弃本次分析</button>
            </div>
          </template>
          <template v-else>
            <QuestionCard v-model="answer" :question="quiz.current" />

            <button type="button" class="note-toggle" :class="{ on: noteOpen }" @click="noteOpen = !noteOpen">
              <span>💡 补充说明</span>
              <span v-if="(note || '').trim()" class="note-badge">已填写</span>
            </button>
            <div v-if="noteOpen" class="note-box">
              <textarea
                v-model="note"
                rows="3"
                placeholder="如果你突然有些想法，写在这里，我会据此调整后面的提问（比如：预算已经定了、想先做个简单的试试）"
              ></textarea>
            </div>

            <div class="quiz-nav">
              <button type="button" class="nav-btn" :disabled="!quiz.canBack" @click="goBack">
                上一题
              </button>
              <button type="button" class="nav-btn primary" :disabled="!canNext" @click="goNext">
                <span v-if="quiz.busy" class="spin"></span>
                <span v-else>下一题</span>
              </button>
            </div>
          </template>
        </div>

        <button v-if="!quiz.finished" type="button" class="gen-btn" :disabled="!canGenerate" @click="generate">
          <span v-if="genLoading" class="spin"></span>
          <span v-else>生成需求报告</span>
        </button>
      </main>

      
      <main v-else ref="chatMainRef" class="main chat-main">
        <button type="button" class="abandon-link chat-abandon" @click="openAbandon">放弃本次分析</button>
        <template v-for="(m, i) in chat.messages" :key="i">
          <DocCard v-if="m.role === 'doc'" :document="m.document" :doc-id="m.docId" />
          <ChatBubble
            v-else
            :role="m.role"
            :content="m.content"
            :status="m.status"
            :status-done="m.statusDone"
            :thinking="m.thinking"
            :streaming="m.role === 'assistant' && !m.done && !m.thinking && !!m.content"
          />
        </template>

        <InspirationChips v-if="chat.messages.length === 1" :items="chips" @pick="(t) => { freeInput = t; sendFree() }" />

        <button type="button" class="gen-btn" :disabled="!canGenerate" @click="generate">
          <span v-if="genLoading" class="spin"></span>
          <span v-else>生成需求报告</span>
        </button>

        <div class="composer">
          <textarea
            ref="freeRef"
            v-model="freeInput"
            rows="1"
            :disabled="chat.busy"
            placeholder="说说你的想法…"
            title="Enter 发送，Shift+Enter 换行"
            @keydown="onFreeKey"
            @input="resizeFree"
          ></textarea>
          <button
            v-if="chat.busy"
            type="button"
            class="stop-btn"
            title="停止生成"
            @click="stopGeneration"
          >
            <span class="stop-icon">■</span>
            <span class="stop-text">停止</span>
          </button>
          <button
            v-else
            type="button"
            class="send"
            :disabled="chat.busy || !freeInput.trim()"
            @click="sendFree"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2">
              <path d="M12 19V5M5 12l7-7 7 7" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </main>

    
    <ConfirmModal
      :visible="!!confirmMode"
      title="开始需求分析"
      content="选择一种方式开始：问卷适合还说不清楚的人，自由对话适合已经有想法的人。"
      confirm-text="确定"
      cancel-text="取消"
      @confirm="confirmStart"
      @cancel="confirmMode = null"
    />

    <ConfirmModal
      :visible="showExitConfirm"
      title="放弃本次分析？"
      content="本次需求分析尚未生成文档，放弃后本次进度将被清空。"
      :confirm-text="pendingPath ? '放弃并离开' : '放弃本次分析'"
      cancel-text="继续分析"
      :danger="true"
      @confirm="confirmExit"
      @cancel="continueAnalysis"
    />

    <BottomNav />
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.main {
  flex: 1;
  overflow-y: auto;
  padding: 18px 16px 20px;
  scroll-behavior: smooth;
}

.main.center {
  display: flex;
  align-items: center;
  justify-content: center;
}


.progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #4f46e5, #0ea5a4);
  transition: width 0.3s;
}

.progress-label {
  font-size: 12.5px;
  color: var(--ink-3);
  white-space: nowrap;
}

.abandon-link {
  flex: none;
  font-size: 12.5px;
  padding: 4px 10px;
  border-radius: 999px;
  background: transparent;
  border: 1px solid var(--line);
  color: var(--ink-3);
}

.abandon-link:active {
  background: var(--bg);
}

.abandon-link.center {
  display: block;
  margin: 14px auto 0;
}

.chat-abandon {
  align-self: flex-start;
}


.qwrap {
  padding: 22px 18px;
  margin-bottom: 14px;
}

.quiz-nav {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.nav-btn {
  flex: 1;
  height: 46px;
  border-radius: 13px;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--ink-2);
  font-size: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.18s;
}

.nav-btn.primary {
  flex: 1.4;
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
  font-weight: 600;
}

.nav-btn.primary:hover:not(:disabled) {
  background: #4338ca;
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


.gen-btn {
  width: 100%;
  height: 50px;
  border-radius: 14px;
  background: var(--card);
  border: 1px solid var(--accent);
  color: var(--accent);
  font-size: 15px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.18s;
}

.gen-btn:hover:not(:disabled) {
  background: var(--accent);
  color: #fff;
}

.gen-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.gen-btn .left {
  font-size: 12px;
  color: var(--ink-3);
  font-weight: 400;
}

.gen-btn:hover .left {
  color: rgba(255, 255, 255, 0.85);
}

.gen-btn .left b {
  color: var(--accent);
  font-weight: 650;
}

.gen-btn:hover .left b {
  color: #fff;
}


.chat-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.composer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 9px 9px 9px 16px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 18px;
  box-shadow: var(--shadow);
  margin-top: auto;
  transition: border-color 0.18s;
}

.composer:focus-within {
  border-color: var(--accent);
}

.composer textarea {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  background: transparent;
  font: inherit;
  color: var(--ink);
  max-height: 100px;
  padding: 7px 0;
  line-height: 1.6;
}

.composer textarea::placeholder {
  color: var(--ink-3);
}

.send {
  flex: none;
  width: 40px;
  height: 40px;
  border-radius: 13px;
  border: none;
  cursor: pointer;
  background: var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  transition: all 0.18s;
}

.send:hover {
  background: #4338ca;
}

.send:disabled {
  background: #c7cbe0;
  cursor: not-allowed;
}

.stop-btn {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 40px;
  padding: 0 14px;
  border-radius: 13px;
  background: #fee2e2;
  color: #dc2626;
  border: 1px solid #fecaca;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  transition: all 0.18s;
  box-shadow: 0 4px 12px -4px rgba(220, 38, 38, 0.35);
}

.stop-btn:hover {
  background: #fecaca;
  color: #b91c1c;
  transform: translateY(-1px);
}

.stop-icon {
  font-size: 11px;
  line-height: 1;
}


.start-entry {
  max-width: 440px;
  padding: 30px 24px;
  text-align: center;
}

.start-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 12px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  overflow: hidden;
}

.start-icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 6px;
}

.start-entry h2 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
}

.start-entry p {
  margin: 0 0 20px;
  font-size: 13.5px;
  color: var(--ink-2);
  line-height: 1.7;
}

.start-btn {
  width: 100%;
  height: 46px;
  border-radius: 13px;
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  transition: background 0.18s;
}

.start-btn:hover {
  background: #4338ca;
}

.start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}


.mode-pick {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 16px;
  border-radius: 14px;
  background: var(--card);
  border: 1.5px solid var(--line);
  color: var(--ink);
  text-align: left;
  transition: all 0.16s;
}

.mode-btn:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.mode-title {
  font-size: 16px;
  font-weight: 700;
}

.mode-desc {
  font-size: 12.5px;
  color: var(--ink-2);
  line-height: 1.6;
}


.note-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 8px 14px;
  border-radius: 999px;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--ink-2);
  font-size: 13.5px;
  transition: all 0.16s;
}

.note-toggle.on {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-soft);
}

.note-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--accent);
  color: #fff;
}

.note-box {
  margin-top: 10px;
}

.note-box textarea {
  width: 100%;
  min-height: 76px;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--card);
  border: 1.5px solid var(--line);
  color: var(--ink);
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.16s;
}

.note-box textarea:focus {
  border-color: var(--accent);
}


.finish-card {
  text-align: center;
}

.finish-icon {
  width: 56px;
  height: 56px;
  margin: 6px auto 12px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 28px;
  background: var(--accent-soft);
}

.finish-card h3 {
  margin: 0 0 10px;
  font-size: 17px;
  font-weight: 700;
}

.finish-summary {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--ink-2);
  line-height: 1.7;
  text-align: left;
  white-space: pre-wrap;
}


.chat-main .gen-btn {
  margin-top: auto;
}

.chat-main .composer {
  margin-top: 10px;
}


.confirm-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 24px;
}

.confirm-card {
  width: 100%;
  max-width: 360px;
  padding: 24px 20px;
  text-align: center;
}

.confirm-card h3 {
  margin: 0 0 10px;
  font-size: 17px;
  font-weight: 700;
}

.confirm-card p {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--ink-2);
  line-height: 1.6;
}

.confirm-card p b {
  color: var(--accent);
}

.confirm-actions {
  display: flex;
  gap: 10px;
}

.confirm-actions .nav-btn {
  flex: 1;
}

@media (max-width: 640px) {
  .main {
    padding: 14px 12px 16px;
  }

  .tabs {
    padding: 10px 12px 0;
  }

  .qwrap {
    padding: 18px 14px;
  }
}

/* ================= 2026 视觉升级 ================= */
.main {
  padding: 22px 20px 26px;
}

.landing {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
  align-items: center;
  align-content: center;
  gap: 52px;
  width: 100%;
  max-width: 1060px;
  margin: 0 auto;
  padding: 46px 26px 40px;
}

.hero {
  animation: fadeUp 0.5s ease both;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-sm);
  font-size: 12.5px;
  font-weight: 650;
  color: #4338ca;
  letter-spacing: 0.2px;
  backdrop-filter: blur(8px);
}

.eyebrow i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--success);
  animation: pulse 2.2s ease infinite;
}

.hero h1 {
  margin: 18px 0 14px;
  font-size: 42px;
  line-height: 1.3;
  letter-spacing: -0.6px;
  font-weight: 800;
  color: #101a34;
}

.hero h1 em {
  font-style: normal;
  background: var(--grad);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-sub {
  margin: 0;
  max-width: 530px;
  font-size: 15px;
  line-height: 1.85;
  color: var(--ink-2);
}

.hero-points {
  list-style: none;
  margin: 22px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 11px;
}

.hero-points li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  color: #334155;
}

.tick {
  flex: none;
  width: 20px;
  height: 20px;
  margin-top: 3px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  background: var(--grad);
  box-shadow: 0 6px 12px -6px rgba(79, 70, 229, 0.8);
}

.hero-stats {
  display: flex;
  gap: 34px;
  margin-top: 30px;
  padding-top: 22px;
  border-top: 1px dashed var(--line-strong);
}

.hero-stats div {
  display: flex;
  flex-direction: column;
}

.hero-stats b {
  font-size: 25px;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: var(--grad);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  line-height: 1.2;
}

.hero-stats span {
  margin-top: 3px;
  font-size: 12px;
  color: var(--ink-3);
}

.start-entry {
  position: relative;
  width: 100%;
  max-width: 460px;
  padding: 30px 26px 24px;
  text-align: center;
  border-radius: 22px;
  border-color: rgba(226, 232, 240, 0.9);
  background: linear-gradient(180deg, #ffffff 0%, #fcfdff 100%);
  box-shadow: var(--shadow-lg);
  animation: fadeUp 0.55s 0.05s ease both;
  justify-self: center;
}

.start-entry::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(140deg, rgba(79, 70, 229, 0.4), rgba(14, 165, 233, 0.16), transparent 62%);
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

.start-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 14px;
  border-radius: 18px;
  box-shadow: 0 16px 30px -16px rgba(30, 41, 90, 0.45);
}

.start-kicker {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--accent);
  text-transform: uppercase;
}

.start-entry h2 {
  margin: 0 0 6px;
  font-size: 22px;
  letter-spacing: -0.3px;
}

.start-entry p {
  margin: 0 0 20px;
  font-size: 13.5px;
  color: var(--ink-2);
}

.start-note {
  margin: 12px 0 0 !important;
  font-size: 12px !important;
  color: var(--ink-3) !important;
}

.start-btn {
  height: 50px;
  border-radius: 14px;
  background: var(--grad);
  background-size: 160% 160%;
  font-size: 15.5px;
  font-weight: 650;
  box-shadow: 0 16px 30px -16px rgba(79, 70, 229, 0.85);
  transition: background-position 0.3s, transform 0.18s, box-shadow 0.18s;
}

.start-btn:hover:not(:disabled) {
  background-position: 100% 0;
  transform: translateY(-1px);
  box-shadow: 0 20px 34px -16px rgba(79, 70, 229, 0.9);
}

.mode-pick {
  gap: 11px;
}

.mode-btn {
  flex-direction: row;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: #fbfcff;
  border: 1.5px solid var(--line);
  text-align: left;
}

.mode-btn:hover {
  transform: translateY(-2px);
  background: #fff;
  border-color: rgba(79, 70, 229, 0.45);
  box-shadow: var(--shadow);
}

.mode-ico {
  flex: none;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  color: var(--accent);
}

.mode-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.mode-arrow {
  flex: none;
  color: var(--ink-3);
  font-size: 18px;
  transition: transform 0.18s, color 0.18s;
}

.mode-btn:hover .mode-arrow {
  color: var(--accent);
  transform: translateX(3px);
}

.mode-title {
  font-size: 15px;
}

.mode-desc {
  font-size: 12px;
}

/* ---- 对话 / 问卷 ---- */
.qwrap,
.progress-row,
.chat-main {
  width: 100%;
  max-width: 820px;
  margin-left: auto;
  margin-right: auto;
}

.qwrap {
  padding: 28px 26px;
  border-radius: 22px;
  box-shadow: var(--shadow-lg);
}

.progress-row {
  margin-bottom: 14px;
}

.progress-bar {
  height: 7px;
  background: #e8ebf7;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.06);
}

.progress-label {
  font-weight: 600;
  color: var(--ink-2);
}

.abandon-link {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
}

.quiz-nav {
  margin-top: 22px;
}

.nav-btn {
  height: 48px;
  border-radius: 14px;
  background: #f4f6fc;
  font-weight: 600;
}

.nav-btn.primary {
  background: var(--grad);
  border: none;
  box-shadow: 0 14px 26px -14px rgba(79, 70, 229, 0.8);
}

.nav-btn.primary:hover:not(:disabled) {
  filter: brightness(1.06);
}

.gen-btn {
  max-width: 820px;
  margin-left: auto;
  margin-right: auto;
  background: var(--grad);
  border: none;
  color: #fff;
  box-shadow: 0 18px 34px -20px rgba(79, 70, 229, 0.9);
}

.gen-btn:hover:not(:disabled) {
  background: var(--grad);
  filter: brightness(1.06);
}

.gen-btn:disabled {
  background: #e3e7f4;
  color: #9aa4ba;
  box-shadow: none;
  opacity: 1;
}

.chat-main {
  gap: 14px;
}

.chat-main .composer {
  position: sticky;
  bottom: 0;
  z-index: 8;
  margin-top: 8px;
  padding: 10px 10px 10px 16px;
  border-radius: 18px;
  border-color: rgba(226, 232, 240, 0.9);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(18px);
  box-shadow: 0 20px 44px -22px rgba(30, 41, 90, 0.4);
}

.composer:focus-within {
  border-color: rgba(79, 70, 229, 0.55);
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1), 0 20px 44px -22px rgba(30, 41, 90, 0.4);
}

.send {
  background: var(--grad);
  box-shadow: 0 10px 20px -10px rgba(79, 70, 229, 0.9);
}

.send:hover:not(:disabled) {
  filter: brightness(1.06);
}

.chat-abandon {
  align-self: flex-end;
  margin-bottom: 2px;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.16);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(16, 185, 129, 0.04);
  }
}

@media (max-width: 980px) {
  .landing {
    grid-template-columns: 1fr;
    align-content: start;
    gap: 30px;
    padding: 30px 20px 36px;
  }

  .hero {
    text-align: center;
  }

  .hero-sub {
    margin: 0 auto;
  }

  .hero-points {
    max-width: 520px;
    margin-left: auto;
    margin-right: auto;
    text-align: left;
  }

  .hero-stats {
    justify-content: center;
  }

  .start-entry {
    max-width: 520px;
  }
}

@media (max-width: 640px) {
  .main {
    padding: 14px 12px 18px;
  }

  .landing {
    padding: 18px 6px 26px;
    gap: 22px;
  }

  .hero h1 {
    margin-top: 14px;
    font-size: 29px;
    line-height: 1.35;
  }

  .hero-sub {
    font-size: 13.5px;
    line-height: 1.8;
  }

  .hero-points {
    margin-top: 16px;
    gap: 9px;
  }

  .hero-points li {
    font-size: 13px;
  }

  .hero-stats {
    gap: 24px;
    margin-top: 20px;
    padding-top: 16px;
  }

  .hero-stats b {
    font-size: 21px;
  }

  .start-entry {
    padding: 24px 18px 20px;
    border-radius: 18px;
  }

  .start-entry h2 {
    font-size: 19px;
  }

  .qwrap {
    padding: 20px 15px;
    border-radius: 18px;
  }

  .progress-row {
    margin-bottom: 10px;
  }

  .chat-main {
    gap: 12px;
  }

  .chat-main .composer {
    margin-top: 4px;
  }

  .hero-points,
  .hero-stats {
    display: none;
  }

  .hero-sub {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    font-size: 13px;
    line-height: 1.75;
  }

  .landing {
    gap: 16px;
    padding-top: 10px;
  }

  .start-entry {
    padding: 20px 16px 18px;
  }

  .start-icon {
    width: 52px;
    height: 52px;
    margin-bottom: 10px;
  }

  .landing.choosing .hero {
    display: none;
  }

  .landing.choosing {
    padding-top: 6px;
  }
}

@media (max-width: 380px) {
  .landing {
    gap: 12px;
    padding-top: 6px;
  }

  .hero h1 {
    margin: 12px 0 10px;
    font-size: 24px;
    line-height: 1.4;
  }

  .hero-sub {
    font-size: 12.5px;
  }

  .eyebrow {
    font-size: 11.5px;
    padding: 6px 12px;
  }

  .start-entry {
    padding: 16px 14px 14px;
  }

  .start-entry h2 {
    font-size: 18px;
  }

  .start-entry p {
    font-size: 12.5px;
  }

  .start-btn {
    height: 46px;
    font-size: 14.5px;
  }
}
</style>
