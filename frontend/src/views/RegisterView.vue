<!-- 注册页：校验手机号与密码强度，注册成功后自动登录。 -->
<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import logo from '../assets/logo.png'

const router = useRouter()
const user = useUserStore()

const username = ref('')
const password = ref('')
const confirm = ref('')
const error = ref('')
const loading = ref(false)

const rules = computed(() => {
  const p = password.value
  const kinds = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(p)).length
  return [
    { label: '至少 8 位', ok: p.length >= 8 },
    { label: '包含大写 / 小写 / 数字 / 符号中的至少三种', ok: p.length > 0 && kinds >= 3 }
  ]
})

function validate() {
  if (!/^1[3-9]\d{9}$/.test(username.value.trim())) return '请输入 11 位手机号'
  if (!rules.value.every((r) => r.ok)) return '密码强度不符合要求'
  if (password.value !== confirm.value) return '两次输入的密码不一致'
  return ''
}

async function submit() {
  if (loading.value) return
  error.value = validate()
  if (error.value) return
  loading.value = true
  try {
    await user.register(username.value.trim(), password.value)
    await user.login(username.value.trim(), password.value)
    router.replace('/')
  } catch (e) {
    error.value = e.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <section class="auth-brand">
      <div class="brand-logo"><img :src="logo" alt="极构" /></div>
      <h1>创建账号<br /><em>开始一次需求诊断</em></h1>
      <p>账号只保存在本机数据库里，用来区分你的报告与验收记录，不会上传到任何第三方。</p>
      <ul class="brand-points">
        <li>每个账号独立的报告与历史图纸</li>
        <li>验收记录按账号隔离、版本可追溯</li>
        <li>本地运行，数据不离开这台电脑</li>
      </ul>
    </section>

    <section class="auth-card card">
      <div class="card-head">
        <span class="kicker">新用户</span>
        <h2>注册</h2>
        <p>使用手机号创建账号，立即开始。</p>
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
            autocomplete="new-password"
            placeholder="设置登录密码"
          />
        </label>
        <ul class="rules">
          <li v-for="r in rules" :key="r.label" :class="{ ok: r.ok }">
            <span class="dot"></span>{{ r.label }}
          </li>
        </ul>
        <label class="field">
          <span>确认密码</span>
          <input
            v-model="confirm"
            type="password"
            autocomplete="new-password"
            placeholder="再输入一次密码"
          />
        </label>

        <p v-if="error" class="form-error">{{ error }}</p>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="spin"></span>
          <span v-else>注册并登录</span>
        </button>
      </form>

      <p class="switch">
        已经有账号？<router-link to="/login">去登录</router-link>
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
  font-size: 38px;
  line-height: 1.28;
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
  max-width: 450px;
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
  padding: 30px 30px 24px;
  border-radius: 22px;
  box-shadow: var(--shadow-lg);
  animation: fadeUp 0.55s 0.05s ease both;
}

.card-head {
  margin-bottom: 20px;
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
  margin-bottom: 14px;
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

.rules {
  list-style: none;
  margin: -2px 0 14px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rules li {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  color: var(--ink-3);
}

.rules .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #cbd5e1;
  flex: none;
}

.rules li.ok {
  color: var(--success);
}

.rules li.ok .dot {
  background: var(--success);
}

.form-error {
  margin: 0 0 12px;
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
  margin-top: 2px;
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
  margin: 16px 0 0;
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
    gap: 22px;
    max-width: 480px;
    padding: 22px 16px 40px;
    align-content: start;
  }

  .auth-brand {
    text-align: center;
  }

  .brand-logo {
    margin: 4px auto 14px;
  }

  .auth-brand h1 {
    font-size: 28px;
  }

  .auth-brand > p {
    margin: 0 auto;
    font-size: 13.5px;
  }

  .brand-points {
    display: none;
  }

  .auth-card {
    padding: 24px 20px 20px;
    border-radius: 18px;
  }
}
</style>
