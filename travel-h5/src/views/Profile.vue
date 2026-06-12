<template>
  <div class="page-container profile-container">
    <van-nav-bar title="我的" />

    <!-- 用户信息区域 -->
    <div class="user-info">
      <van-image
        :src="authStore.user?.avatar || chatStore.userAvatar"
        round
        class="avatar"
      />
      <div class="user-details">
        <h2 class="user-name">
          {{ authStore.user?.nickname || authStore.user?.username || '游客' }}
        </h2>
        <p class="user-desc">欢迎使用智能旅游助手</p>
      </div>
    </div>

    <!-- 功能菜单 -->
    <div class="menu-section">
      <h3 class="menu-title">我的服务</h3>
      <van-cell-group>
        <van-cell
          title="我的收藏"
          is-link
          icon="star-o"
          @click="$router.push('/favorites')"
        />
        <van-cell
          title="关于我们"
          is-link
          icon="info-o"
          @click="aboutDialogVisible = true"
        />
      </van-cell-group>
    </div>

    <!-- 退出登录 -->
    <div class="logout-section">
      <van-button type="default" block round @click="handleLogout">
        退出登录
      </van-button>
    </div>

    <!-- 关于我们弹窗 -->
    <van-dialog
      v-model:show="aboutDialogVisible"
      title="关于我们"
      show-cancel-button
    >
      <div class="about-content">
        <p>智能旅游助手 v1.0.0</p>
        <p class="mt-2">基于 AI 技术的智能旅游规划平台</p>
        <p class="mt-2">为您提供个性化的旅游行程推荐和实时旅游咨询服务</p>
        <p class="mt-4 text-center">© 2024 智能旅游助手</p>
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { showToast } from 'vant'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const chatStore = useChatStore()
const authStore = useAuthStore()

const aboutDialogVisible = ref(false)

function handleLogout() {
  authStore.logout()
  showToast('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.profile-container {
  padding-bottom: 50px;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 30px 20px;
  background: linear-gradient(135deg, #1989fa 0%, #36cbcb 100%);
  color: white;
}

.avatar {
  width: 80px;
  height: 80px;
  border: 3px solid rgba(255, 255, 255, 0.3);
}

.user-details {
  margin-left: 20px;
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 5px;
}

.user-desc {
  font-size: 14px;
  opacity: 0.9;
}

.menu-section {
  background-color: white;
  border-radius: 12px;
  margin: 15px 10px 0;
  overflow: hidden;
}

.menu-title {
  font-size: 14px;
  color: #646566;
  padding: 12px 15px;
  border-bottom: 1px solid #f0f0f0;
}

.logout-section {
  margin: 30px 16px 0;
}

.logout-section .van-button {
  color: #ee0a24 !important;
  border-color: #ee0a24 !important;
}

.about-content {
  text-align: center;
  line-height: 1.6;
}

.mt-2 {
  margin-top: 8px;
}

.mt-4 {
  margin-top: 16px;
}

.text-center {
  text-align: center;
}
</style>
