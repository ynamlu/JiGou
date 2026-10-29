// 对话状态：消息列表、会话 id、发送中标记。
import { defineStore } from 'pinia'
import { api } from '../api'
import { newSessionId } from '../api/client'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessionId: newSessionId(),
    messages: [],
    busy: false,
    initialized: false
  }),

  actions: {
    async init() {
      if (this.initialized) return
      this.initialized = true

      if (!this.messages.length) {
        let content = '你好，我是你的需求诊断顾问。先说说你想做的需求大概是什么？'
        try {
          const data = await api.getOpening()
          if (data && data.content) content = data.content
        } catch {
          
        }
        this.messages.push({ role: 'assistant', content, done: true, fresh: true })
      }
    },

    resetSession() {
      this.sessionId = newSessionId()
      this.messages = []
      this.initialized = false
      this.init()
    }
  }
})
