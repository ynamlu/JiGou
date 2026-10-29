<script setup>
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import logo from '../assets/logo.png'

const router = useRouter()
const route = useRoute()
const user = useUserStore()
</script>

<template>
  <header class="app-header">
    <div class="logo"><img :src="logo" alt="极构" /></div>
    <div class="titles">
      <h1>极构</h1>
      <p>AI 需求诊断顾问 · 数据只留在本机</p>
    </div>
    <nav class="top-nav">
      <router-link class="nav-link" :class="{ active: route.path === '/' }" to="/">需求分析</router-link>
      <router-link class="nav-link" :class="{ active: route.path === '/templates' }" to="/templates">模板库</router-link>
      <router-link class="nav-link" :class="{ active: route.path === '/history' }" to="/history">我的图纸</router-link>
    </nav>
    <button class="user-chip" type="button" aria-label="个人中心" @click="router.push('/profile')">
      <span class="avatar">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
          <circle cx="12" cy="8" r="3.4" />
          <path d="M5 20c0-3.4 3.1-5.2 7-5.2s7 1.8 7 5.2" />
        </svg>
      </span>
      <span class="uname">{{ user.username }}</span>
    </button>
    <button class="icon-btn mobile-only" aria-label="我的图纸" @click="router.push('/history')">
      <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M7 3h7l4 4v14H7z" stroke-linejoin="round" />
        <path d="M14 3v4h4" stroke-linejoin="round" />
      </svg>
    </button>
  </header>
</template>

<style scoped>
.mobile-only {
  display: none;
}

.app-header .mobile-only {
  display: none;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px 5px 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.24);
  color: #fff;
  flex: none;
  transition: background 0.18s, transform 0.18s;
}

.user-chip:hover {
  background: rgba(255, 255, 255, 0.26);
  transform: translateY(-1px);
}

.user-chip .avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: #fff;
  color: #4338ca;
  font-size: 11px;
  font-weight: 750;
  letter-spacing: 0.2px;
}

.user-chip .uname {
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12.5px;
  font-weight: 600;
}

@media (max-width: 899px) {
  .app-header .mobile-only {
    display: inline-flex;
  }
}

@media (max-width: 760px) {
  .user-chip {
    padding: 4px;
    background: transparent;
    border-color: transparent;
  }

  .user-chip .uname {
    display: none;
  }

  .user-chip .avatar {
    width: 32px;
    height: 32px;
    font-size: 11px;
  }
}
</style>
