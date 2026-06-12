<template>
  <div class="page-container login-page">
    <van-nav-bar title="注册" left-text="返回" left-arrow @click-left="$router.back()" />

    <div class="card" style="margin-top: 16px">
      <van-field
        v-model="username"
        label="用户名"
        placeholder="请输入用户名"
      />
      <van-field
        v-model="password"
        type="password"
        label="密码"
        placeholder="请输入密码"
      />
      <van-field
        v-model="confirmPassword"
        type="password"
        label="确认密码"
        placeholder="请再次输入密码"
      />

      <van-button
        type="primary"
        block
        round
        :loading="loading"
        class="common-button primary-button"
        style="margin-top: 20px"
        @click="handleRegister"
      >
        注册
      </van-button>

      <div class="login-links">
        <span @click="$router.push('/login')">已有账号？去登录</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'

const router = useRouter()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function handleRegister() {
  if (!username.value || !password.value) {
    showToast('请填写用户名和密码')
    return
  }
  if (password.value !== confirmPassword.value) {
    showToast('两次密码不一致')
    return
  }
  loading.value = true
  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })
    const data = await res.json()
    if (data.code === 200) {
      showToast('注册成功')
      router.push('/login')
    } else {
      showToast(data.message || '注册失败')
    }
  } catch (e) {
    showToast('网络错误')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  padding: 0 16px;
}

.login-links {
  text-align: center;
  margin-top: 16px;
  font-size: 14px;
  color: #1989fa;
  cursor: pointer;
}
</style>
