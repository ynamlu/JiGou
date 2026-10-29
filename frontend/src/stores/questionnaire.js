// 问卷状态：当前题目、已答记录与收尾状态；提交失败会回滚上一题。
import { defineStore } from 'pinia'
import { api } from '../api'


const SEED_QUESTION = {
  question: '先说说：你想做一个什么样的东西？',
  type: 'text',
  options: [],
  hint: '一句话或几个词都行，比如「奶茶店扫码点单」「管理会员的系统」，也可以点下面快速选一个',
  quick: ['微信小程序', '手机 App', '网站 / 官网', '内部管理系统', '我还说不清']
}


export function multiToText(answer, type) {
  if (type !== 'multi') return answer
  try {
    const arr = JSON.parse(answer)
    return Array.isArray(arr) ? arr.join('、') : answer
  } catch {
    return answer
  }
}


export const useQuestionnaireStore = defineStore('questionnaire', {
  state: () => ({
    started: false,
    sessionId: '',
    current: null,
    answered: [],
    busy: false,
    error: '',
    finished: false, 
    summary: '' 
  }),

  getters: {
    
    step: (s) => s.answered.length + 1,
    canBack: (s) => s.answered.length > 0,
    hasAnswer: (s) => s.answered.length > 0
  },

  actions: {
    start(sessionId) {
      this.sessionId = sessionId || this.sessionId
      this.started = true
      this.answered = []
      this.current = { ...SEED_QUESTION, quick: [...SEED_QUESTION.quick] }
      this.busy = false
      this.error = ''
      this.finished = false
      this.summary = ''
    },

    
    async submit(answer, note) {
      const q = this.current
      this.answered.push({
        question: q.question,
        type: q.type,
        options: q.options || [],
        hint: q.hint || '',
        answer,
        note: (note || '').trim()
      })
      this.busy = true
      this.error = ''
      try {
        const payload = this.answered.map((a) => ({
          question: a.question,
          answer: multiToText(a.answer, a.type),
          note: a.note || ''
        }))
        const data = await api.nextQuestion(this.sessionId, payload)
        if (data.done) {
          
          this.finished = true
          this.summary = data.summary || ''
          this.current = null
        } else {
          this.finished = false
          this.summary = ''
          this.current = data.question || {
            question: '关于这个项目，你还有什么想补充的？',
            type: 'text',
            options: [],
            hint: ''
          }
        }
        return this.current
      } catch (e) {
        
        this.answered.pop()
        this.error = e.message || '出题失败'
        throw e
      } finally {
        this.busy = false
      }
    },

    
    back() {
      if (!this.canBack) return
      this.finished = false
      this.summary = ''
      const last = this.answered.pop()
      this.current = {
        question: last.question,
        type: last.type || 'text',
        options: last.options || [],
        hint: last.hint || '',
        _prevAnswer: last.answer,
        _prevNote: last.note || ''
      }
    },

    
    async continueAsk() {
      this.busy = true
      this.error = ''
      try {
        const payload = this.answered.map((a) => ({
          question: a.question,
          answer: multiToText(a.answer, a.type),
          note: a.note || ''
        }))
        const data = await api.nextQuestion(this.sessionId, payload, true)
        this.finished = false
        this.summary = ''
        this.current = data.question || {
          question: '关于这个项目，你还有什么想补充的？',
          type: 'text',
          options: [],
          hint: ''
        }
        return this.current
      } catch (e) {
        this.error = e.message || '出题失败'
        throw e
      } finally {
        this.busy = false
      }
    },

    reset() {
      this.started = false
      this.current = null
      this.answered = []
      this.busy = false
      this.error = ''
      this.finished = false
      this.summary = ''
    }
  }
})
