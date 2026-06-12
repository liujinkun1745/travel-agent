<template>
  <div class="chat-page">
    <van-nav-bar title="AI 对话" :fixed="true" :placeholder="true" />

    <!-- 空状态 -->
    <div class="chat-container" v-if="chatStore.messages.length === 0 && !chatStore.isStreaming">
      <div class="chat-empty">
        <van-icon name="chat-o" size="64" color="#ccc" />
        <p style="color: #999; margin-top: 16px">有什么旅游问题，尽管问我</p>
        <div class="quick-questions">
          <p class="quick-title">快捷提问</p>
          <van-tag
            v-for="q in quickQuestions"
            :key="q"
            class="quick-tag"
            type="primary"
            size="medium"
            @click="sendMessage(q)"
          >
            {{ q }}
          </van-tag>
        </div>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-container" v-else ref="messageList" id="message-list">
      <div class="message-list">
        <ChatBubble
          v-for="msg in chatStore.messages"
          :key="msg.id"
          :message="msg"
        />

        <!-- 流式接收指示器 -->
        <div v-if="chatStore.isStreaming" class="streaming-indicator">
          <van-loading size="16" type="spinner" />
          <span>AI 正在思考中</span>
        </div>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="chat-input-area">
      <van-field
        v-model="inputMessage"
        :border="false"
        placeholder="输入你的问题..."
        @keypress="onKeyPress"
        :disabled="chatStore.isStreaming"
      >
        <template #button>
          <van-button
            size="small"
            type="primary"
            :disabled="!inputMessage.trim() || chatStore.isStreaming"
            @click="sendMessage()"
          >
            发送
          </van-button>
        </template>
      </van-field>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { showToast } from 'vant'
import ChatBubble from '../components/ChatBubble.vue'

const chatStore = useChatStore()
const inputMessage = ref('')
const messageList = ref(null)

// 快捷问题列表
const quickQuestions = [
  '北京有哪些必去的景点？',
  '上海美食推荐',
  '成都三日游攻略',
  '如何选择旅行保险？'
]

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

  try {
    const response = await fetch('/api/travel/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, sessionId: chatStore.sessionId })
    })

    if (!response.ok) {
      const errorText = await response.text().catch(() => '')
      throw new Error('请求失败: ' + response.status + ' ' + errorText)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
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
              // 流正常结束，无需额外处理
            } else if (data.type === 'error') {
              chatStore.appendToLastMessage('\n\n[错误] ' + (data.error || '未知错误'))
            }
          } catch (e) {
            // SSE 行 JSON 解析失败，跳过
            console.warn('SSE 解析失败:', trimmed.substring(0, 80), e.message)
          }
        }
      }
    }
  } catch (error) {
    console.error('对话请求失败:', error)
    chatStore.appendToLastMessage('\n\n[网络错误] ' + (error.message || '未知错误'))
  } finally {
    chatStore.isStreaming = false
    await scrollToBottom()
  }
}

// 回车发送
function onKeyPress(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// 从详情页跳转时自动发送上下文消息
onMounted(() => {
  const context = sessionStorage.getItem('chatContext')
  if (context) {
    sessionStorage.removeItem('chatContext')
    sendMessage(context)
  }
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-bottom: 50px; /* 为底部导航留空间 */
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

.quick-questions {
  margin-top: 32px;
  text-align: center;
}

.quick-title {
  font-size: 14px;
  color: #999;
  margin-bottom: 16px;
}

.quick-tag {
  margin: 8px;
  cursor: pointer;
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

.chat-input-area {
  position: fixed;
  bottom: 50px;
  left: 0;
  right: 0;
  background: #fff;
  padding: 8px 16px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
  max-width: 750px;
  margin: 0 auto;
}

.chat-input-area :deep(.van-field) {
  background: #f7f8fa;
  border-radius: 20px;
  padding: 8px 16px;
}
</style>
