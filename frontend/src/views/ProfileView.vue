<!-- 个人中心：账号信息、修改密码、注销账号与退出登录。 -->
<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import AppHeader from '../components/AppHeader.vue'
import BottomNav from '../components/BottomNav.vue'
import { showToast } from '../utils/toast'

const router = useRouter()
const user = useUserStore()

onMounted(() => {
  user.fetchMe().catch(() => {})
})

const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const pwdError = ref('')
const changing = ref(false)

const pwdRulesOk = computed(() => {
  const p = newPassword.value
  const kinds = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((r) => r.test(p)).length
  return p.length >= 8 && kinds >= 3
})

async function changePassword() {
  if (changing.value) return
  pwdError.value = ''
  if (!oldPassword.value) {
    pwdError.value = '请输入旧密码'
    return
  }
  if (!pwdRulesOk.value) {
    pwdError.value = '新密码至少 8 位，且包含大写/小写/数字/符号中的至少三种'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    pwdError.value = '两次输入的新密码不一致'
    return
  }
  changing.value = true
  try {
    await user.changePassword(oldPassword.value, newPassword.value)
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    showToast('密码已修改')
  } catch (e) {
    pwdError.value = e.message || '修改密码失败'
  } finally {
    changing.value = false
  }
}

const deletePassword = ref('')
const delError = ref('')
const deleting = ref(false)

async function removeAccount() {
  if (deleting.value) return
  delError.value = ''
  if (!deletePassword.value) {
    delError.value = '请输入密码以确认注销'
    return
  }
  if (!window.confirm('注销后账号与验收记录将永久删除，确定继续吗？')) return
  deleting.value = true
  const name = user.username
  try {
    await user.deleteAccount(deletePassword.value)
    localStorage.removeItem('jg_archive:' + name)
    localStorage.removeItem('jg_analysis_draft:' + name)
    showToast('账号已注销')
    router.replace('/login')
  } catch (e) {
    delError.value = e.message || '注销失败'
  } finally {
    deleting.value = false
  }
}

async function logout() {
  await user.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="profile-page">
    <AppHeader />

    <main class="profile-body">
      <section class="panel account-card">
        <div class="avatar">
          <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="12" cy="8" r="3.4" />
            <path d="M5 20c0-3.4 3.1-5.2 7-5.2s7 1.8 7 5.2" />
          </svg>
        </div>
        <div class="account-meta">
          <h2>{{ user.username }}</h2>
          <p>注册时间：{{ user.createdAt || '—' }}</p>
        </div>
        <button type="button" class="ghost-btn" @click="logout">退出登录</button>
      </section>

      <section class="panel">
        <h3>修改密码</h3>
        <p class="hint">修改后当前登录仍然有效，下次请使用新密码登录。</p>
        <div class="field-grid">
          <label class="field">
            <span>旧密码</span>
            <input v-model="oldPassword" type="password" autocomplete="current-password" placeholder="当前密码" />
          </label>
          <label class="field">
            <span>新密码</span>
            <input v-model="newPassword" type="password" autocomplete="new-password" placeholder="至少 8 位，三种字符组合" />
          </label>
          <label class="field">
            <span>确认新密码</span>
            <input v-model="confirmPassword" type="password" autocomplete="new-password" placeholder="再输入一次新密码" />
          </label>
        </div>
        <p v-if="pwdError" class="form-error">{{ pwdError }}</p>
        <button type="button" class="primary-btn" :disabled="changing" @click="changePassword">
          <span v-if="changing" class="spin"></span>
          <span v-else>保存新密码</span>
        </button>
      </section>

      <section class="panel danger">
        <h3>注销账号</h3>
        <p class="hint">
          注销会永久删除该账号、登录凭证与全部验收记录，无法恢复。浏览器里的报告草稿也会随账号失效。
        </p>
        <div class="danger-row">
          <input v-model="deletePassword" type="password" autocomplete="current-password" placeholder="输入密码以确认" />
          <button type="button" class="danger-btn" :disabled="deleting" @click="removeAccount">
            <span v-if="deleting" class="spin"></span>
            <span v-else>注销账号</span>
          </button>
        </div>
        <p v-if="delError" class="form-error">{{ delError }}</p>
      </section>
    </main>

    <BottomNav />
  </div>
</template>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
}

.profile-body {
  flex: 1;
  overflow-y: auto;
  width: 100%;
  max-width: 820px;
  margin: 0 auto;
  padding: 22px 20px 90px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: var(--shadow);
  padding: 24px;
}

.account-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  flex: none;
  display: grid;
  place-items: center;
  background: var(--grad);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
  box-shadow: 0 12px 24px -14px rgba(79, 70, 229, 0.9);
}

.account-meta {
  flex: 1;
  min-width: 0;
}

.account-meta h2 {
  margin: 0 0 3px;
  font-size: 19px;
  letter-spacing: -0.2px;
}

.account-meta p {
  margin: 0;
  font-size: 12.5px;
  color: var(--ink-3);
}

.ghost-btn {
  flex: none;
  height: 38px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: #fbfcff;
  color: var(--ink-2);
  font-size: 13px;
  font-weight: 600;
  transition: all 0.16s;
}

.ghost-btn:hover {
  border-color: rgba(79, 70, 229, 0.4);
  color: var(--accent);
  background: var(--accent-soft);
}

.panel h3 {
  margin: 0 0 6px;
  font-size: 17px;
  letter-spacing: -0.2px;
}

.hint {
  margin: 0 0 18px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--ink-2);
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 4px;
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
  height: 44px;
  padding: 0 13px;
  border-radius: 11px;
  border: 1.5px solid var(--line);
  background: #fbfcff;
  font-size: 14px;
  transition: border-color 0.16s, box-shadow 0.16s, background 0.16s;
}

.field input:focus {
  border-color: rgba(79, 70, 229, 0.55);
  background: #fff;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.08);
}

.primary-btn {
  height: 44px;
  margin-top: 14px;
  padding: 0 22px;
  border-radius: 12px;
  background: var(--grad);
  color: #fff;
  font-size: 14px;
  font-weight: 650;
  box-shadow: 0 14px 26px -16px rgba(79, 70, 229, 0.9);
}

.primary-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.danger {
  border-color: #fde2e4;
  background: linear-gradient(180deg, #fff, #fffafa);
}

.danger h3 {
  color: #be123c;
}

.danger-row {
  display: flex;
  gap: 10px;
}

.danger-row input {
  flex: 1;
  height: 44px;
  padding: 0 13px;
  border-radius: 11px;
  border: 1.5px solid #fecdd3;
  background: #fff;
  font-size: 14px;
}

.danger-row input:focus {
  border-color: #fb7185;
  box-shadow: 0 0 0 4px rgba(225, 29, 72, 0.08);
}

.danger-btn {
  flex: none;
  height: 44px;
  padding: 0 20px;
  border-radius: 12px;
  background: #e11d48;
  color: #fff;
  font-size: 14px;
  font-weight: 650;
}

.danger-btn:disabled {
  opacity: 0.65;
}

.form-error {
  margin: 10px 0 0;
  padding: 9px 12px;
  border-radius: 10px;
  background: #fff1f2;
  border: 1px solid #fecdd3;
  color: #be123c;
  font-size: 12.5px;
  line-height: 1.6;
}

@media (max-width: 760px) {
  .profile-body {
    padding: 16px 12px 84px;
  }

  .panel {
    padding: 18px 16px;
    border-radius: 16px;
  }

  .account-card {
    flex-wrap: wrap;
  }

  .ghost-btn {
    width: 100%;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }

  .danger-row {
    flex-direction: column;
  }

  .danger-btn {
    width: 100%;
  }
}
</style>
