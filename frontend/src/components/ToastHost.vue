<script setup>
import { toasts } from '../utils/toast'
</script>

<template>
  <div class="toast-host">
    <transition-group name="toast">
      <div v-for="toast in toasts" :key="toast.id" class="toast-item">
        {{ toast.message }}
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
  max-width: 320px;
  padding: 9px 16px;
  border-radius: 999px;
  background: rgba(26, 31, 54, 0.88);
  color: #fff;
  font-size: 13px;
  text-align: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
