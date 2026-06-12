<template>
  <div class="page-container">
    <van-nav-bar title="我的收藏" left-text="返回" left-arrow @click-left="$router.back()" />
    <div class="page-content">
      <van-empty v-if="favorites.length === 0 && !loading" description="暂无收藏" />
      <div v-for="fav in favorites" :key="fav.id" class="card favorite-card">
        <div class="fav-question">
          <span class="label">Q:</span> {{ fav.question }}
        </div>
        <div class="fav-answer" :class="{ expanded: expandedIds.has(fav.id) }">
          <span class="label">A:</span>
          <div class="markdown-body" v-html="renderMd(fav.answer)"></div>
        </div>
        <div class="fav-footer">
          <span v-if="fav.answer && fav.answer.length > 120"
                class="expand-btn" @click="toggleExpand(fav.id)">
            {{ expandedIds.has(fav.id) ? '收起 ▲' : '展开 ▼' }}
          </span>
          <span class="fav-time">{{ fav.createdAt?.substring(0, 10) }}</span>
          <van-button size="small" type="danger" plain @click="removeFavorite(fav.id)">
            删除
          </van-button>
        </div>
      </div>
      <van-loading v-if="loading" class="loading-container" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showToast } from 'vant'
import { marked } from 'marked'

function sanitize(html) {
  return html
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<script\b[^>]*\/>/gi, '')
    .replace(/\son\w+\s*=\s*"[^"]*"/gi, '')
}

const favorites = ref([])
const loading = ref(false)
const expandedIds = ref(new Set())

function renderMd(text) {
  if (!text) return ''
  return sanitize(marked.parse(text))
}

function toggleExpand(id) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
  // 触发响应式
  expandedIds.value = new Set(expandedIds.value)
}

async function loadFavorites() {
  loading.value = true
  try {
    const res = await fetch('/api/favorites', {
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    })
    const data = await res.json()
    if (data.code === 200) {
      favorites.value = data.data
    }
  } catch (e) {
    showToast('加载失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

async function removeFavorite(id) {
  try {
    const res = await fetch('/api/favorites/' + id, {
      method: 'DELETE',
      headers: { Authorization: 'Bearer ' + localStorage.getItem('token') }
    })
    const data = await res.json()
    if (data.code === 200) {
      showToast('已删除')
      favorites.value = favorites.value.filter(f => f.id !== id)
    }
  } catch (e) {
    showToast('删除失败: ' + e.message)
  }
}

onMounted(loadFavorites)
</script>

<style scoped>
.favorite-card {
  margin-bottom: 12px;
}

.fav-question {
  font-size: 14px;
  color: #1989fa;
  margin-bottom: 8px;
  line-height: 1.5;
}

.fav-answer {
  font-size: 14px;
  color: #323233;
  line-height: 1.5;
}

.fav-answer:not(.expanded) {
  max-height: 72px;
  overflow: hidden;
}

.label {
  font-weight: 600;
  margin-right: 4px;
}

.expand-btn {
  font-size: 13px;
  color: #1989fa;
  cursor: pointer;
  user-select: none;
}

.fav-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #f5f5f5;
  gap: 8px;
}

.fav-time {
  font-size: 12px;
  color: #999;
  flex: 1;
}

/* Markdown 表格样式 */
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
  font-size: 12px;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 4px 8px;
  text-align: left;
}
.markdown-body :deep(th) { background: #e8e8e8; font-weight: 600; }
.markdown-body :deep(code) { background: rgba(0,0,0,0.06); padding: 1px 5px; border-radius: 3px; font-size: 12px; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { padding-left: 18px; }
.markdown-body :deep(p) { margin: 4px 0; }
</style>
