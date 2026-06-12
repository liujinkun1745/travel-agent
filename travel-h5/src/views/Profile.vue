<template>
  <div class="profile-container">
    <van-nav-bar title="我的" />

    <!-- 用户信息区域 -->
    <div class="user-info">
      <van-image
        :src="chatStore.userAvatar"
        round
        class="avatar"
        @click="showAvatarAction = true"
      />
      <div class="user-details">
        <h2 class="user-name" @click="showNicknameDialog = true">
          {{ chatStore.userName }}
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
          @click="showToast('功能开发中')"
        />
        <van-cell
          title="历史记录"
          is-link
          icon="clock-o"
          @click="showToast('功能开发中')"
        />
        <van-cell
          title="设置"
          is-link
          icon="setting-o"
          @click="showToast('功能开发中')"
        />
      </van-cell-group>
    </div>

    <!-- 关于 -->
    <div class="menu-section">
      <h3 class="menu-title">关于</h3>
      <van-cell-group>
        <van-cell
          title="关于我们"
          is-link
          @click="aboutDialogVisible = true"
        />
        <van-cell
          title="版本信息"
          value="v1.0.0"
        />
      </van-cell-group>
    </div>

    <!-- 头像上传弹窗 -->
    <van-action-sheet
      v-model:show="showAvatarAction"
      :actions="[
        { name: '拍照上传', value: 'camera' },
        { name: '从相册选择', value: 'album' }
      ]"
      @select="onAvatarAction"
      cancel-text="取消"
    />

    <!-- 昵称编辑弹窗 -->
    <van-dialog
      v-model:show="showNicknameDialog"
      title="修改昵称"
      show-cancel-button
      @confirm="onNicknameConfirm"
    >
      <div style="padding: 16px">
        <van-field
          v-model="nicknameInput"
          placeholder="请输入新昵称"
          :border="false"
        />
      </div>
    </van-dialog>

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
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()

// 头像上传
const showAvatarAction = ref(false)
function onAvatarAction(action) {
  showToast('请使用 App 或微信扫码打开以使用此功能')
  showAvatarAction.value = false
}

// 昵称编辑
const showNicknameDialog = ref(false)
const nicknameInput = ref('')
function onNicknameConfirm() {
  if (nicknameInput.value.trim()) {
    chatStore.userName = nicknameInput.value.trim()
    showToast('昵称已更新')
  }
  nicknameInput.value = ''
}

// 关于弹窗
const aboutDialogVisible = ref(false)
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
