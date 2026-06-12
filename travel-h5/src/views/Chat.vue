<template>
  <div class="page-container chat-page">
    <van-nav-bar title="AI 对话" :fixed="true" :placeholder="true">
      <template #left>
        <van-icon name="clock-o" size="22" @click="openHistory" />
      </template>
      <template #right>
        <van-icon name="add-o" size="22" @click="startNewSession" />
      </template>
    </van-nav-bar>

    <!-- 空状态 -->
    <div class="chat-container" v-if="chatStore.messages.length === 0 && !chatStore.isStreaming">
      <div class="chat-empty">
        <div class="empty-icon">💬</div>
        <p class="empty-text">有什么旅游问题，尽管问我</p>
        <div class="quick-questions" :key="quickPage">
          <div
            v-for="(q, idx) in displayedQuestions"
            :key="q"
            class="quick-card"
            :style="{ animationDelay: idx * 0.06 + 's' }"
            @click="sendMessage(q)"
          >
            <span class="quick-text">{{ q }}</span>
          </div>
          <div class="quick-dots">
            <span v-for="i in quickPages" :key="i"
                  class="quick-dot" :class="{ active: i === quickPage }"
                  @click="quickPage = i"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-container" v-else ref="messageList" id="message-list">
      <div class="message-list">
        <template v-for="msg in chatStore.messages" :key="msg.id">
          <ChatBubble :message="msg" :is-streaming="chatStore.isStreaming" @favorite="addFavorite" />
        </template>

        <!-- 流式接收指示器 -->
        <div v-if="chatStore.isStreaming" class="streaming-indicator">
          <van-loading size="16" type="spinner" />
          <span>AI 正在思考中</span>
        </div>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="chat-input-area">
      <div class="input-row">
        <input
          v-model="inputMessage"
          class="chat-input"
          placeholder="输入你的问题..."
          @keydown="onKeyDown"
          :disabled="chatStore.isStreaming"
          autocomplete="off"
        />
        <button
          class="send-btn"
          :disabled="!inputMessage.trim() || chatStore.isStreaming"
          @click="sendMessage()"
        >
          发送
        </button>
      </div>
    </div>

    <!-- 历史会话弹窗 -->
    <van-popup v-model:show="showHistory" position="right" :style="{ width: '80%', height: '100%' }">
      <div class="history-panel">
        <h3>历史会话</h3>
        <van-button size="small" type="primary" block @click="startNewSession" style="margin-bottom: 12px">
          新建对话
        </van-button>
        <van-loading v-if="historyLoading" class="loading-container" />
        <van-empty v-if="!historyLoading && sessions.length === 0" description="暂无历史会话" />
        <div v-for="s in sessions" :key="s.sessionId" class="history-item"
             @click="loadSession(s.sessionId)">
          <div class="history-text">{{ s.lastMessage }}</div>
          <div class="history-time">{{ s.lastTime?.substring(0, 16) }}</div>
          <span class="history-del" @click.stop="deleteSession(s.sessionId)">✕</span>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { showToast } from 'vant'
import ChatBubble from '../components/ChatBubble.vue'

const chatStore = useChatStore()
const inputMessage = ref('')
const messageList = ref(null)

// 快捷问题列表
const quickQuestions = [
  '🏯 北京三日游攻略',
  '🐼 成都必去景点推荐',
  '🌃 上海有哪些特色美食',
  '🏛️ 西安兵马俑怎么玩',
  '🌊 三亚适合几月份去',
  '🏔️ 丽江大理自由行路线',
  '🍜 重庆火锅哪家好',
  '🎒 一个人旅行注意事项',
]

// 快捷提问分页（每页 4 个，自动轮换）
const PAGE_SIZE = 4
const quickPage = ref(1)
const quickPages = Math.ceil(quickQuestions.length / PAGE_SIZE)
const displayedQuestions = computed(() => {
  const start = (quickPage.value - 1) * PAGE_SIZE
  return quickQuestions.slice(start, start + PAGE_SIZE)
})
let quickTimer = null
onMounted(() => {
  loadSessions()
  quickTimer = setInterval(() => {
    quickPage.value = quickPage.value >= quickPages ? 1 : quickPage.value + 1
  }, 4000)
  const context = sessionStorage.getItem('chatContext')
  if (context) {
    sessionStorage.removeItem('chatContext')
    sendMessage(context)
  }
})
onUnmounted(() => {
  if (quickTimer) clearInterval(quickTimer)
})

// 历史会话
const showHistory = ref(false)
const historyLoading = ref(false)
const sessions = ref([])

async function loadSessions() {
  historyLoading.value = true
  try {
    const res = await fetch('/api/chat/sessions', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    })
    const data = await res.json()
    if (data.code === 200) sessions.value = data.data
  } catch (e) { /* ignore */ }
  finally { historyLoading.value = false }
}

async function loadSession(sessionId) {
  chatStore.clearMessages()
  chatStore.sessionId = sessionId
  try {
    const res = await fetch('/api/chat/sessions/' + sessionId + '/messages', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    })
    const data = await res.json()
    if (data.code === 200 && data.data.length > 0) {
      data.data.forEach(m => {
        chatStore.addMessage(m.role, m.content)
      })
    }
  } catch (e) { showToast('加载历史失败') }
  showHistory.value = false
}

function openHistory() {
  loadSessions()
  showHistory.value = true
}

async function deleteSession(sessionId) {
  try {
    await fetch('/api/chat/sessions/' + sessionId, {
      method: 'DELETE',
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    })
    // 如果删的是当前会话，开启新对话
    if (chatStore.sessionId === sessionId) {
      startNewSession()
    }
    loadSessions()
  } catch (e) { showToast('删除失败') }
}

function startNewSession() {
  chatStore.clearMessages()
  chatStore.sessionId = 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  showHistory.value = false
}

// 收藏
async function addFavorite(msg) {
  // 找到对应的用户问题
  const messages = chatStore.messages
  const idx = messages.findIndex(m => m.id === msg.id)
  const question = idx > 0 && messages[idx - 1].role === 'user' ? messages[idx - 1].content : ''
  try {
    const res = await fetch('/api/favorites', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + localStorage.getItem('token')
      },
      body: JSON.stringify({ question, answer: msg.content })
    })
    const data = await res.json()
    if (data.code === 200) showToast('已收藏')
  } catch (e) { showToast('收藏失败') }
}

// 滚动到底部
async function scrollToBottom() {
  await nextTick()
  const el = messageList.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

// 发送消息
async function sendMessage(msg) {
  const text = (msg || inputMessage.value).trim()
  if (!text || chatStore.isStreaming) return

  inputMessage.value = ''

  // 添加用户消息
  chatStore.addMessage('user', text)
  chatStore.isStreaming = true
  await scrollToBottom()

  // 添加空的 AI 消息占位
  chatStore.addMessage('ai', '')
  await scrollToBottom()

  // AbortController 防止 SSE 连接无限挂起（120 秒超时）
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 120000)

  try {
    const response = await fetch('/api/travel/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + localStorage.getItem('token')
      },
      body: JSON.stringify({ message: text, sessionId: chatStore.sessionId }),
      signal: controller.signal
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => '')
      throw new Error('请求失败: ' + response.status + ' ' + errorText)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    let streamEnded = false
    while (!streamEnded) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // 解析 SSE 数据（按行分割，兼容 \r\n 和 \n）
      const lines = buffer.split(/\r?\n/)
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || trimmed.startsWith('event:')) continue

        if (trimmed.startsWith('data:')) {
          const jsonStr = trimmed.substring(5).trim()
          if (!jsonStr) continue

          try {
            const data = JSON.parse(jsonStr)
            if (data.type === 'chunk' && data.content) {
              chatStore.appendToLastMessage(data.content)
              await scrollToBottom()
            } else if (data.type === 'done') {
              streamEnded = true
            } else if (data.type === 'error') {
              chatStore.appendToLastMessage('\n\n[错误] ' + (data.error || '未知错误'))
              streamEnded = true
            }
          } catch (e) {
            // SSE 行 JSON 解析失败，跳过
            console.warn('SSE 解析失败:', trimmed.substring(0, 80), e.message)
          }
        }
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      chatStore.appendToLastMessage('\n\n[请求超时] AI 响应时间过长，请重试')
    } else {
      console.error('对话请求失败:', error)
      chatStore.appendToLastMessage('\n\n[网络错误] ' + (error.message || '未知错误'))
    }
  } finally {
    clearTimeout(timeoutId)
    chatStore.isStreaming = false
    await scrollToBottom()
  }
}

// 回车发送
function onKeyDown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-bottom: 50px;
}

/* 固定导航栏对齐页面宽度 */
.chat-page :deep(.van-nav-bar) {
  max-width: 480px;
  margin: 0 auto;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 60px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 12px;
}

.empty-text {
  color: #999;
  font-size: 15px;
  margin-bottom: 28px;
}

/* 快捷提问卡片 */
.quick-questions {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 0 4px;
}

.quick-card {
  padding: 12px 10px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #ebedf0;
  cursor: pointer;
  transition: all 0.2s ease;
  animation: fade-in-up 0.35s ease forwards;
  opacity: 0;
  text-align: center;
}

.quick-card:active {
  background: #f0f8ff;
  border-color: #1989fa;
  transform: scale(0.97);
}

.quick-text {
  font-size: 13px;
  color: #323233;
  line-height: 1.4;
}

/* 快捷提问分页圆点 */
.quick-dots {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 4px;
}

.quick-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ddd;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-dot.active {
  background: #1989fa;
  width: 16px;
  border-radius: 3px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  color: #999;
  font-size: 14px;
}

/* 输入区域 */
.chat-input-area {
  position: fixed;
  bottom: 50px;
  left: max(0px, calc((100% - 480px) / 2));
  right: max(0px, calc((100% - 480px) / 2));
  background: #fff;
  padding: 10px 12px;
  padding-bottom: max(10px, env(safe-area-inset-bottom));
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.06);
  border-radius: 16px 16px 0 0;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-input {
  flex: 1;
  height: 38px;
  padding: 0 14px;
  border: 1.5px solid #e0e0e0;
  border-radius: 19px;
  font-size: 14px;
  outline: none;
  background: #f5f5f5;
  transition: border-color 0.2s, background 0.2s;
  color: #323233;
}

.chat-input:focus {
  border-color: #1989fa;
  background: #fff;
}

.chat-input::placeholder {
  color: #bbb;
}

.chat-input:disabled {
  opacity: 0.5;
}

.send-btn {
  flex-shrink: 0;
  height: 38px;
  padding: 0 18px;
  border: none;
  border-radius: 19px;
  background: #1989fa;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.1s;
}

.send-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.send-btn:not(:disabled):active {
  transform: scale(0.95);
  opacity: 0.8;
}

/* 历史会话面板 */
.history-panel {
  padding: 16px;
}

.history-panel h3 {
  font-size: 18px;
  margin-bottom: 16px;
}

.history-item {
  padding: 14px 12px;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  position: relative;
}

.history-item:hover {
  background: #f7f8fa;
}

.history-del {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  font-size: 12px;
  color: #ccc;
  border-radius: 50%;
  background: #f5f5f5;
  transition: all 0.2s;
}

.history-del:hover {
  color: #fff;
  background: #ee0a24;
}

.history-text {
  font-size: 14px;
  color: #323233;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>
