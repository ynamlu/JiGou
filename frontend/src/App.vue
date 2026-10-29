<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ToastHost from './components/ToastHost.vue'
import { useUserStore } from './stores/user'
import { setUnauthorizedHandler } from './api/client'

const router = useRouter()
const user = useUserStore()

setUnauthorizedHandler(() => {
  user.reset()
  if (router.currentRoute.value.name !== 'login') {
    router.replace({ name: 'login' })
  }
})

onMounted(() => {
  // 有本地登录态时校验一次；token 失效会触发上面的统一处理
  if (user.isLoggedIn) {
    user.fetchMe().catch(() => {})
  }
})
</script>

<template>
  <router-view v-slot="{ Component }">
    <component :is="Component" />
  </router-view>
  <ToastHost />
</template>
