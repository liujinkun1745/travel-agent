<template>
  <div class="chat-bubble" :class="messageClass">
    <div class="bubble-content">
      <div class="message-text" v-if="message.role === 'user'">{{ message.content }}</div>
      <div class="message-text markdown-body" v-else v-html="renderedContent"></div>
    </div>
    <div class="bubble-footer" v-if="showTime || message.role === 'ai'">
      <span class="message-time" v-if="showTime">{{ formatTime }}</span>
      <span v-if="message.role === 'ai' && message.content && !isStreaming"
            class="fav-btn" @click="$emit('favorite', message)">⭐ 收藏</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  message: { type: Object, required: true },
  isStreaming: { type: Boolean, default: false }
})

defineEmits(['favorite'])

const messageClass = computed(() => {
  return props.message.role === 'user' ? 'user-message' : 'ai-message'
})

const showTime = computed(() => {
  return props.message.timestamp && props.message.content
})

const formatTime = computed(() => {
  if (!props.message.timestamp) return ''
  const date = new Date(props.message.timestamp)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
})

// 简易 HTML 安全过滤（移除 script 标签和事件处理器）
function sanitizeHtml(html) {
  return html
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<script\b[^>]*\/>/gi, '')
    .replace(/\son\w+\s*=\s*"[^"]*"/gi, '')
    .replace(/\son\w+\s*=\s*'[^']*'/gi, '')
    .replace(/<iframe\b[^>]*>[\s\S]*?<\/iframe>/gi, '')
}

// AI 消息渲染为 markdown HTML
const renderedContent = computed(() => {
  if (props.message.role === 'user') return ''
  if (!props.message.content) return ''
  return sanitizeHtml(marked.parse(props.message.content))
})
</script>

<style scoped>
.chat-bubble {
  display: flex;
  flex-direction: column;
  max-width: 80%;
}

.user-message {
  align-self: flex-end;
  align-items: flex-end;
}

.ai-message {
  align-self: flex-start;
  align-items: flex-start;
}

.bubble-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.5;
  word-break: break-word;
}

.user-message .bubble-content {
  background: #1989fa;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.ai-message .bubble-content {
  background: #fff;
  color: #323233;
  border: 1px solid #ebedf0;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.bubble-footer {
  display: flex;
  align-items: center;
  width: 100%;
  margin-top: 4px;
  padding: 0 4px;
}

.message-time {
  font-size: 11px;
  color: #999;
}

.fav-btn {
  font-size: 11px;
  color: #bbb;
  cursor: pointer;
  transition: color 0.2s;
  user-select: none;
  margin-left: auto;
}

.fav-btn:hover {
  color: #ff976a;
}

/* 预留：typing 动画样式，目前未在模板中使用 */
.typing {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ===== Markdown 渲染样式 ===== */
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 13px;
  overflow-x: auto;
  display: block;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 6px 10px;
  text-align: left;
  white-space: nowrap;
}

.markdown-body :deep(th) {
  background: #e8e8e8;
  font-weight: 600;
}

.markdown-body :deep(tr:nth-child(even)) {
  background: #fafafa;
}

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Menlo', 'Consolas', monospace;
  font-size: 13px;
}

.markdown-body :deep(pre) {
  background: #f0f0f0;
  border-radius: 8px;
  padding: 12px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}

.markdown-body :deep(li) {
  margin-bottom: 2px;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid #1989fa;
  padding-left: 12px;
  color: #666;
  margin: 8px 0;
}

.markdown-body :deep(a) {
  color: #1989fa;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 8px 0 4px;
  font-weight: 600;
}

.markdown-body :deep(h1) { font-size: 18px; }
.markdown-body :deep(h2) { font-size: 16px; }
.markdown-body :deep(h3) { font-size: 15px; }

.markdown-body :deep(p) {
  margin: 4px 0;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #eee;
  margin: 12px 0;
}
</style>