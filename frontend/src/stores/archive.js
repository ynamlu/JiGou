// 报告归档：按账号存在 localStorage，键名 jg_archive:<手机号>，切换账号互不影响。
import { defineStore } from 'pinia'
import { getSession } from '../api/client'

const STORAGE_PREFIX = 'jg_archive:'

function storageKey() {
  return STORAGE_PREFIX + (getSession().username || 'guest')
}

function nowText() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

function loadItems() {
  try {
    return JSON.parse(localStorage.getItem(storageKey())) || []
  } catch {
    return []
  }
}

function saveItems(items) {
  localStorage.setItem(storageKey(), JSON.stringify(items))
}


export const useArchiveStore = defineStore('archive', {
  state: () => ({
    items: []
  }),

  actions: {
    load() {
      this.items = loadItems()
    },

    add(document, confirmItems, assessment) {
      const title =
        (String(document || '').match(/^#\s+(.+)$/m) || [])[1] || '需求诊断报告'
      const item = {
        id: 'doc-' + Date.now(),
        title,
        document,
        confirmItems: Array.isArray(confirmItems) ? confirmItems : [],
        assessment: assessment || null,
        deliverables: null, 
        abPlan: null, 
        acceptance: null, 
        versions: [], 
        created_at: nowText()
      }
      this.items.unshift(item)
      saveItems(this.items)
      return item
    },

    
    setAcceptance(id, info) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.acceptance = info || null
      if (info && info.version) {
        const snap = {
          version: info.version,
          doc_hash: info.doc_hash,
          accepted_at: info.accepted_at,
          diff: info.diff || ''
        }
        const i = item.versions.findIndex((v) => v.version === snap.version)
        if (i >= 0) item.versions[i] = snap
        else item.versions.push(snap)
        item.versions.sort((a, b) => a.version - b.version)
      }
      saveItems(this.items)
    },

    setAssessment(id, assessment) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.assessment = assessment || null
      saveItems(this.items)
    },

    setDeliverables(id, d) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.deliverables = d || null
      saveItems(this.items)
    },

    setAbPlan(id, p) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.abPlan = p || null
      saveItems(this.items)
    },

    
    updateDocument(id, document, confirmItems, assessment) {
      const item = this.items.find((it) => it.id === id)
      if (!item) return
      item.document = document
      if (confirmItems !== undefined) item.confirmItems = Array.isArray(confirmItems) ? confirmItems : []
      if (assessment !== undefined) item.assessment = assessment || null
      saveItems(this.items)
    },

    remove(id) {
      const idx = this.items.findIndex((it) => it.id === id)
      if (idx >= 0) {
        this.items.splice(idx, 1)
        saveItems(this.items)
        return true
      }
      return false
    },

    rename(id, newTitle) {
      const item = this.items.find((it) => it.id === id)
      if (item && String(newTitle || '').trim()) {
        item.title = String(newTitle).trim()
        saveItems(this.items)
        return true
      }
      return false
    },

    getById(id) {
      return this.items.find((item) => item.id === id)
    }
  }
})
