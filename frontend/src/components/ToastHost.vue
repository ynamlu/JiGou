<script setup>
import { toasts } from '../utils/toast'
</script>

<template>
  <div class="toast-host">
    <transition-group name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast-item"
        :class="toast.type || 'info'"
      >
        <span class="toast-icon">
          <!-- 成功图标 -->
          <svg v-if="toast.type === 'success'" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <!-- 错误图标 -->
          <svg v-else-if="toast.type === 'error'" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          <!-- 警告图标 -->
          <svg v-else-if="toast.type === 'warning'" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <!-- 信息/默认图标 -->
          <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        </span>
        <span class="toast-text">{{ toast.message }}</span>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed;
  top: 72px;
  left: 0;
  right: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  pointer-events: none;
  z-index: 999;
}

.toast-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 380px;
  padding: 8px 16px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.92);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 13.5px;
  box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.toast-icon {
  flex: none;
  display: flex;
  align-items: center;
}

.toast-item.success {
  background: rgba(6, 78, 59, 0.94);
  border-color: rgba(52, 211, 153, 0.35);
  color: #ecfdf5;
}
.toast-item.success .toast-icon {
  color: #34d399;
}

.toast-item.error {
  background: rgba(127, 29, 29, 0.94);
  border-color: rgba(248, 113, 113, 0.35);
  color: #fef2f2;
}
.toast-item.error .toast-icon {
  color: #f87171;
}

.toast-item.warning {
  background: rgba(120, 53, 15, 0.94);
  border-color: rgba(251, 191, 36, 0.35);
  color: #fffbeb;
}
.toast-item.warning .toast-icon {
  color: #fbbf24;
}

.toast-item.info .toast-icon {
  color: #818cf8;
}

.toast-text {
  line-height: 1.45;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.22s, transform 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.96);
}
</style>
