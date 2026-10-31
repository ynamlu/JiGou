<script setup>
defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: '' },
  content: { type: String, default: '' },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
  danger: { type: Boolean, default: false }
})

const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <transition name="modal-fade">
    <div v-if="visible" class="modal-mask" @click.self="emit('cancel')">
      <div class="modal-card card">
        <h3 v-if="title">{{ title }}</h3>
        <p v-if="content">{{ content }}</p>
        <slot></slot>
        <div class="modal-actions">
          <button type="button" class="btn-cancel" @click="emit('cancel')">
            {{ cancelText }}
          </button>
          <button
            type="button"
            class="btn-confirm"
            :class="{ danger }"
            @click="emit('confirm')"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
  display: grid;
  place-items: center;
  padding: 16px;
}

.modal-card {
  max-width: 420px;
  width: 100%;
  padding: 24px;
  border-radius: 18px;
  background: #fff;
  box-shadow: var(--shadow-lg);
  animation: popIn 0.24s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes popIn {
  from {
    transform: scale(0.92);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.modal-card h3 {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: 750;
  color: #101a34;
}

.modal-card p {
  margin: 0 0 20px;
  font-size: 14px;
  color: var(--ink-2);
  line-height: 1.6;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-cancel {
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  background: var(--bg);
  border: 1px solid var(--line);
  color: var(--ink-2);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.16s ease;
}

.btn-cancel:hover {
  background: #eef2f6;
}

.btn-confirm {
  height: 40px;
  padding: 0 18px;
  border-radius: 12px;
  background: var(--grad);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 10px 20px -8px rgba(79, 70, 229, 0.85);
  transition: all 0.16s ease;
}

.btn-confirm:hover {
  filter: brightness(1.06);
  transform: translateY(-1px);
}

.btn-confirm.danger {
  background: #dc2626;
  box-shadow: 0 10px 20px -8px rgba(220, 38, 38, 0.85);
}

.btn-confirm.danger:hover {
  background: #b91c1c;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
