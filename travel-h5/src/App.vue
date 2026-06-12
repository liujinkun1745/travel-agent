<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
  <van-tabbar
    v-if="showTabbar"
    :model-value="active"
    route
    :fixed="true"
    :safe-area-inset-bottom="true"
    class="app-tabbar"
  >
    <van-tabbar-item to="/" icon="home-o">首页</van-tabbar-item>
    <van-tabbar-item to="/chat" icon="chat-o">对话</van-tabbar-item>
    <van-tabbar-item to="/profile" icon="user-o">我的</van-tabbar-item>
  </van-tabbar>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 详情页不显示底部导航
const showTabbar = computed(() => route.path !== '/detail')

const active = computed(() => {
  const path = route.path
  if (path === '/') return 0
  if (path === '/chat') return 1
  if (path === '/profile') return 2
  return 0
})
</script>

<style>
/* 页面切换淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 底部导航：手机端满宽，桌面端居中 */
.app-tabbar {
  max-width: 480px;
  width: 100%;
  left: 0;
  right: 0;
  margin: 0 auto;
}
</style>
