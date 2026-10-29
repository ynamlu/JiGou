// 分析过程草稿：按账号保存，刷新或重新进入后可恢复未完成的问卷/对话。
import { defineStore } from 'pinia'
import { useChatStore } from './chat'
import { useQuestionnaireStore } from './questionnaire'
import { getSession } from '../api/client'

function draftKey() {
  return 'jg_analysis_draft:' + (getSession().username || 'guest')
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(draftKey())
    if (!raw) return null
    const d = JSON.parse(raw)
    return d && d.mode ? d : null
  } catch {
    return null
  }
}


export const useAnalysisStore = defineStore('analysis', {
  state: () => ({
    mode: '' 
  }),

  getters: {
    active: (s) => s.mode !== ''
  },

  actions: {
    start(mode) {
      this.mode = mode
    },

    
    saveDraft() {
      if (!this.mode) {
        localStorage.removeItem(draftKey())
        return
      }
      const chat = useChatStore()
      const quiz = useQuestionnaireStore()
      const draft = {
        mode: this.mode,
        sessionId: chat.sessionId,
        quiz: {
          answered: quiz.answered,
          current: quiz.current,
          finished: quiz.finished,
          summary: quiz.summary
        },
        chat: { messages: chat.messages.filter((m) => m.done) },
        savedAt: Date.now()
      }
      try {
        localStorage.setItem(draftKey(), JSON.stringify(draft))
      } catch {
        
      }
    },

    
    restoreDraft() {
      const draft = loadDraft()
      if (!draft) return false
      const chat = useChatStore()
      const quiz = useQuestionnaireStore()
      this.mode = draft.mode
      if (draft.sessionId) chat.sessionId = draft.sessionId
      if (draft.quiz) {
        quiz.started = true
        quiz.sessionId = draft.sessionId || quiz.sessionId
        quiz.answered = draft.quiz.answered || []
        quiz.current = draft.quiz.current || null
        quiz.finished = !!draft.quiz.finished
        quiz.summary = draft.quiz.summary || ''
      }
      if (draft.chat && Array.isArray(draft.chat.messages) && draft.chat.messages.length) {
        chat.messages = draft.chat.messages
      }
      return true
    },

    
    abandon() {
      this.mode = ''
      try {
        localStorage.removeItem(draftKey())
      } catch {
        
      }
    }
  }
})
