import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 聊天状态管理
 */
export const useChatStore = defineStore('chat', () => {
  // 消息列表
  const messages = ref([])

  // 是否正在流式接收
  const isStreaming = ref(false)

  // 用户信息（同步到对话页）
  const userAvatar = ref('https://img.yzcdn.cn/vant/cat.jpeg')
  const userName = ref('游客')

  // 会话 ID：当前聊天会话唯一标识，用于服务端记忆多轮对话
  const sessionId = ref('chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9))

  // 收藏的消息
  const favorites = ref(loadFavorites())

  // 添���消息
  let _msgSeq = 0
  function addMessage(role, content) {
    messages.value.push({
      id: Date.now() + '_' + (_msgSeq++),
      role,
      content,
      timestamp: Date.now()
    })
  }

  // 追加 AI 消息内容（流式更新）
  function appendToLastMessage(content) {
    const lastIdx = messages.value.length - 1
    const last = messages.value[lastIdx]
    if (last && last.role === 'ai') {
      // 替换整个对象以明确触发 Vue 响应式更新
      messages.value[lastIdx] = {
        ...last,
        content: last.content + content
      }
    }
  }

  // 清空消息
  function clearMessages() {
    messages.value = []
  }

  // 收藏消息
  function toggleFavorite(message) {
    const index = favorites.value.findIndex(f => f.id === message.id)
    if (index > -1) {
      favorites.value.splice(index, 1)
    } else {
      favorites.value.push({ ...message, favoritedAt: Date.now() })
    }
    saveFavorites()
  }

  function isFavorited(messageId) {
    return favorites.value.some(f => f.id === messageId)
  }

  function loadFavorites() {
    try {
      const stored = localStorage.getItem('travel_favorites')
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  }

  function saveFavorites() {
    localStorage.setItem('travel_favorites', JSON.stringify(favorites.value))
  }

  return {
    messages,
    isStreaming,
    userAvatar,
    userName,
    sessionId,
    favorites,
    addMessage,
    appendToLastMessage,
    clearMessages,
    toggleFavorite,
    isFavorited
  }
})
