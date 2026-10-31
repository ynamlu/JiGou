<script setup>
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

function isActive(path) {
  if (path === '/') return route.path === '/'
  if (path === '/history') return route.path === '/history' || route.path.startsWith('/doc/')
  return route.path.startsWith(path)
}

function go(path) {
  if (route.path !== path) router.push(path)
}
</script>

<template>
  <nav class="bottom-nav">
    <button
      type="button"
      class="nav-item"
      :class="{ active: isActive('/') }"
      @click="go('/')"
    >
      <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        <path d="M8 9h8M8 13h5" />
      </svg>
      <span>需求分析</span>
    </button>

    <button
      type="button"
      class="nav-item"
      :class="{ active: isActive('/templates') }"
      @click="go('/templates')"
    >
      <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </svg>
      <span>模板案例</span>
    </button>

    <button
      type="button"
      class="nav-item"
      :class="{ active: isActive('/history') }"
      @click="go('/history')"
    >
      <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
      <span>我的图纸</span>
    </button>

    <button
      type="button"
      class="nav-item"
      :class="{ active: isActive('/profile') }"
      @click="go('/profile')"
    >
      <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
      <span>个人中心</span>
    </button>
  </nav>
</template>

<style scoped>
.bottom-nav {
  flex: none;
  display: flex;
  background: #fff;
  border-top: 1px solid var(--line);
  box-shadow: 0 -2px 12px rgba(26, 31, 54, 0.05);
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 20;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 8px 0 7px;
  color: var(--ink-3);
  font-size: 11px;
  transition: color 0.15s;
}

.nav-item span {
  line-height: 1;
}

.nav-item.active {
  color: var(--accent);
  font-weight: 600;
}

@media (min-width: 900px) {
  .bottom-nav {
    display: none;
  }
}

@media (max-width: 899px) {
  .bottom-nav {
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(18px);
    box-shadow: 0 -12px 30px -18px rgba(30, 41, 90, 0.35);
  }

  .nav-item {
    padding: 9px 0 8px;
  }
}
</style>
