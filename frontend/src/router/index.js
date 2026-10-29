// 路由表与登录守卫：public 页面免登录，其余未登录统一跳转 /login。
import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { public: true }
  },
  { path: '/', name: 'chat', component: () => import('../views/ChatView.vue') },
  { path: '/templates', name: 'templates', component: () => import('../views/TemplateLibrary.vue') },
  { path: '/doc/:id', name: 'doc', component: () => import('../views/DocView.vue') },
  { path: '/history', name: 'history', component: () => import('../views/HistoryView.vue') },
  { path: '/profile', name: 'profile', component: () => import('../views/ProfileView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to) => {
  const user = useUserStore()
  if (!to.meta.public && !user.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.public && user.isLoggedIn) {
    return { name: 'chat' }
  }
  return true
})

export default router
