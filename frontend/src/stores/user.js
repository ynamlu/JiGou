// 账号状态：登录、注册、登出，以及 localStorage 中的会话持久化。
import { defineStore } from 'pinia'
import { api } from '../api'
import { clearSession, getSession, setSession } from '../api/client'

export const useUserStore = defineStore('user', {
  state: () => {
    const session = getSession()
    return {
      username: session.username,
      token: session.token,
      createdAt: ''
    }
  },

  getters: {
    isLoggedIn: (state) => Boolean(state.token)
  },

  actions: {
    async register(username, password) {
      await api.register(username, password)
    },

    async login(username, password) {
      const data = await api.login(username, password)
      this.username = data.username || username
      this.token = data.token || ''
      setSession(this.username, this.token)
    },

    async fetchMe() {
      const data = await api.getMe()
      this.username = data.username || this.username
      this.createdAt = data.created_at || ''
      return data
    },

    async changePassword(oldPassword, newPassword) {
      await api.changePassword(oldPassword, newPassword)
    },

    async deleteAccount(password) {
      await api.deleteAccount(password)
      this.reset()
    },

    async logout() {
      try {
        await api.logout()
      } catch {
        
      }
      this.reset()
    },

    reset() {
      this.username = ''
      this.token = ''
      this.createdAt = ''
      clearSession()
    }
  }
})
