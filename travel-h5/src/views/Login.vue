<template>
  <div class="page-container login-page">
    <div class="login-header">
      <h1>🧳 智能旅游助手</h1>
      <p>登录后享受个性化旅游规划</p>
    </div>

    <div class="card login-card">
      <van-field
        v-model="username"
        label="用户名"
        placeholder="请输入用户名"
        @keypress="onEnter"
      />
      <van-field
        v-model="password"
        type="password"
        label="密码"
        placeholder="请输入密码"
        @keypress="onEnter"
      />

      <van-button
        type="primary"
        block
        round
        :loading="loading"
        class="common-button primary-button"
        style="margin-top: 20px"
        @click="handleLogin"
      >
        登录
      </van-button>

      <div class="login-links">
        <span @click="$router.push('/register')">没有账号？去注册</span>
      </div>

      <!-- 测试用户快捷登录 -->
      <div class="quick-login">
        <div class="quick-title">快捷体验</div>
        <van-button
          type="default"
          block
          plain
          @click="quickLogin('demo', 'demo123')"
        >
          测试用户：demo / demo123
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function doLogin(u, p) {
  loading.value = true
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: u, password: p })
    })
    const data = await res.json()
    if (data.code === 200) {
      authStore.setAuth(data.data.token, {
        userId: data.data.userId,
        username: data.data.username,
        nickname: data.data.nickname,
        avatar: data.data.avatar
      })
      showToast('登录成功')
      router.push('/')
    } else {
      showToast(data.message || '登录失败')
    }
  } catch (e) {
    showToast('网络错误')
  } finally {
    loading.value = false
  }
}

function handleLogin() {
  if (!username.value || !password.value) {
    showToast('请填写用户名和密码')
    return
  }
  doLogin(username.value, password.value)
}

function quickLogin(u, p) {
  username.value = u
  password.value = p
}

function onEnter(e) {
  if (e.key === 'Enter') handleLogin()
}
</script>

<style scoped>
.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 28px;
  color: #323233;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 14px;
  color: #999;
}

.login-card {
  width: 100%;
  padding-bottom: 24px;
}

.login-links {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #1989fa;
  cursor: pointer;
}

.quick-login {
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.quick-title {
  text-align: center;
  font-size: 13px;
  color: #999;
  margin-bottom: 12px;
}
</style>
