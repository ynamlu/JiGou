<!-- 登录页：手机号 + 密码，成功后回到 redirect 参数指定的页面。 -->
<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import logo from '../assets/logo.png'

const router = useRouter()
const route = useRoute()
const user = useUserStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

function validate() {
  if (!/^1[3-9]\d{9}$/.test(username.value.trim())) {
    return '请输入 11 位手机号'
  }
  if (!password.value) return '请输入密码'
  return ''
}

async function submit() {
  if (loading.value) return
  error.value = validate()
  if (error.value) return
  loading.value = true
  try {
    await user.login(username.value.trim(), password.value)
    router.replace(route.query.redirect || '/')
  } catch (e) {
    error.value = e.message || '登录失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <section class="auth-brand">
      <div class="brand-logo"><img :src="logo" alt="极构" /></div>
      <h1>极构<br /><em>需求诊断顾问</em></h1>
      <p>把「我想做个系统」，变成一份能直接拿去开发、询价、立项的需求报告。</p>
      <ul class="brand-points">
        <li>12 篇软件开发知识库驱动</li>
        <li>六维需求成熟度评估</li>
        <li>PRD / 询价清单 / 成本工期一次生成</li>
      </ul>
    </section>

    <section class="auth-card card">
      <div class="card-head">
        <span class="kicker">欢迎回来</span>
        <h2>登录</h2>
        <p>登录后继续你的需求诊断与历史图纸。</p>
      </div>

      <form @submit.prevent="submit">
        <label class="field">
          <span>手机号</span>
          <input
            v-model="username"
            type="tel"
            inputmode="numeric"
            maxlength="11"
            autocomplete="username"
            placeholder="11 位手机号"
          />
        </label>
        <label class="field">
          <span>密码</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
          />
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="spin"></span>
          <span v-else>登录</span>
        </button>
      </form>

      <p class="switch">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </p>
    </section>
  </div>
</template>

<style scoped>
.auth-page {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 420px;
  align-items: center;
  gap: 56px;
  width: 100%;
  max-width: 1080px;
  margin: 0 auto;
  padding: 40px 26px;
  overflow-y: auto;
}

.auth-brand {
  color: var(--ink);
  animation: fadeUp 0.5s ease both;
}

.brand-logo {
  width: 60px;
  height: 60px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  display: grid;
  place-items: center;
  overflow: hidden;
  margin-bottom: 22px;
}

.brand-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 7px;
}

.auth-brand h1 {
  margin: 0 0 16px;
  font-size: 40px;
  line-height: 1.25;
  letter-spacing: -0.6px;
  font-weight: 800;
}

.auth-brand h1 em {
  font-style: normal;
  background: var(--grad);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.auth-brand > p {
  margin: 0;
  max-width: 440px;
  font-size: 15px;
  line-height: 1.85;
  color: var(--ink-2);
}

.brand-points {
  list-style: none;
  margin: 26px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.brand-points li {
  position: relative;
  padding-left: 22px;
  font-size: 13.5px;
  color: #334155;
}

.brand-points li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 7px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--grad);
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.12);
}

.auth-card {
  width: 100%;
  padding: 32px 30px 26px;
  border-radius: 22px;
  box-shadow: var(--shadow-lg);
  animation: fadeUp 0.55s 0.05s ease both;
}

.card-head {
  margin-bottom: 22px;
}

.kicker {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--accent);
  text-transform: uppercase;
}

.card-head h2 {
  margin: 0 0 6px;
  font-size: 25px;
  letter-spacing: -0.4px;
}

.card-head p {
  margin: 0;
  font-size: 13px;
  color: var(--ink-2);
}

.field {
  display: block;
  margin-bottom: 16px;
}

.field span {
  display: block;
  margin-bottom: 7px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink-2);
}

.field input {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1.5px solid var(--line);
  background: #fbfcff;
  font-size: 14.5px;
  transition: border-color 0.16s, box-shadow 0.16s, background 0.16s;
}

.field input:focus {
  border-color: rgba(79, 70, 229, 0.55);
  background: #fff;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.08);
}

.form-error {
  margin: -4px 0 14px;
  padding: 9px 12px;
  border-radius: 10px;
  background: #fff1f2;
  border: 1px solid #fecdd3;
  color: #be123c;
  font-size: 12.5px;
  line-height: 1.6;
}

.submit-btn {
  width: 100%;
  height: 48px;
  margin-top: 4px;
  border-radius: 13px;
  background: var(--grad);
  color: #fff;
  font-size: 15px;
  font-weight: 650;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 16px 30px -16px rgba(79, 70, 229, 0.9);
  transition: filter 0.18s, transform 0.18s;
}

.submit-btn:hover:not(:disabled) {
  filter: brightness(1.06);
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.switch {
  margin: 18px 0 0;
  text-align: center;
  font-size: 13px;
  color: var(--ink-3);
}

.switch a {
  color: var(--accent);
  font-weight: 600;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (max-width: 980px) {
  .auth-page {
    grid-template-columns: 1fr;
    gap: 24px;
    max-width: 480px;
    padding: 24px 16px 40px;
    align-content: start;
  }

  .auth-brand {
    text-align: center;
  }

  .brand-logo {
    margin: 6px auto 16px;
  }

  .auth-brand h1 {
    font-size: 30px;
  }

  .auth-brand > p {
    margin: 0 auto;
    font-size: 13.5px;
  }

  .brand-points {
    display: none;
  }

  .auth-card {
    padding: 26px 20px 22px;
    border-radius: 18px;
  }
}
</style>
