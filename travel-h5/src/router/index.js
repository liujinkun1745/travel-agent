import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { title: '智能旅游助手' }
  },
  {
    path: '/detail',
    name: 'Detail',
    component: () => import('../views/Detail.vue'),
    meta: { title: '行程规划' }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/Chat.vue'),
    meta: { title: 'AI 对话' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/Profile.vue'),
    meta: { title: '我的' }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 设置页面标题
router.afterEach((to) => {
  document.title = to.meta.title || '智能旅游助手'
})

export default router
