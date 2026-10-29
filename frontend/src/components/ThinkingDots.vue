<template>
  <span class="dots">
    <i></i>
    <i></i>
    <i></i>
  </span>
</template>

<style scoped>
.dots {
  display: inline-flex;
  gap: 4px;
  padding: 3px 0;
}

.dots i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ink-3);
  animation: blink 1.3s infinite;
}

.dots i:nth-child(2) {
  animation-delay: 0.18s;
}

.dots i:nth-child(3) {
  animation-delay: 0.36s;
}

@keyframes blink {
  0%,
  60%,
  100% {
    opacity: 0.25;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-3px);
  }
}
</style>
