<script setup>
const props = defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['pick'])
</script>

<template>
  <div class="chips">
    <button
      v-for="item in props.items"
      :key="item"
      type="button"
      class="chip"
      @click="emit('pick', item)"
    >
      {{ item }}
    </button>
  </div>
</template>

<style scoped>
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 14px 0 8px 43px;
}

.chip {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 13px;
  color: var(--ink-2);
  cursor: pointer;
  text-align: left;
  max-width: 320px;
  transition: all 0.18s;
  box-shadow: 0 1px 2px rgba(26, 31, 54, 0.03);
}

.chip:hover {
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-1px);
}

@media (max-width: 640px) {
  .chips {
    gap: 8px;
    margin: 10px 0 6px;
  }

  .chip {
    width: 100%;
    max-width: none;
    padding: 12px 14px;
    font-size: 13.5px;
  }
}

/* ================= 2026 视觉升级 ================= */
.chip {
  background: #fbfcff;
  border-color: rgba(226, 232, 240, 0.95);
  border-radius: 14px;
  box-shadow: var(--shadow-sm);
}

.chip:hover {
  background: #fff;
  border-color: rgba(79, 70, 229, 0.45);
  box-shadow: var(--shadow);
}
</style>
