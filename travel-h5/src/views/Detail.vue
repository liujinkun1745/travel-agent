<template>
  <div class="page-container">
    <van-nav-bar title="行程规划" left-text="返回" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <!-- 加载中 -->
      <div v-if="!planData" class="loading-container">
        <van-loading size="40" vertical>正在生成行程...</van-loading>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="!planData.success" class="card error-card">
        <van-empty description="行程生成失败">
          <template #description>
            <p>{{ planData.error || '未知错误' }}</p>
          </template>
        </van-empty>
        <van-button type="primary" block @click="$router.back()">返回重试</van-button>
      </div>

      <!-- 行程内容 -->
      <template v-else>
        <!-- 行程概览 -->
        <div class="card overview-card">
          <div class="trip-header">
            <h2>{{ planData.city }}</h2>
            <span class="trip-budget">¥{{ planData.totalBudget }}</span>
          </div>
          <div class="trip-meta">
            <van-tag type="primary" size="medium">{{ planData.days }}天行程</van-tag>
          </div>
        </div>

        <!-- 每日行程 -->
        <div class="trip-collapse">
          <van-collapse v-model="activeDays" accordion>
            <van-collapse-item
              v-for="day in planData.dailyItinerary"
              :key="day.day"
              :name="day.day"
              :title="`第${day.day}天`"
            >
              <div class="day-schedule">
                <!-- 上午 -->
                <div class="schedule-section" v-if="day.morning">
                  <span class="section-label morning">上午</span>
                  <SpotItem :data="day.morning" />
                </div>
                <!-- 下午 -->
                <div class="schedule-section" v-if="day.afternoon">
                  <span class="section-label afternoon">下午</span>
                  <SpotItem :data="day.afternoon" />
                </div>
                <!-- 晚上 -->
                <div class="schedule-section" v-if="day.evening">
                  <span class="section-label evening">晚上</span>
                  <SpotItem :data="day.evening" />
                </div>
              </div>
            </van-collapse-item>
          </van-collapse>
        </div>

        <!-- 预算明细 -->
        <div class="card budget-card" v-if="planData.budgetBreakdown">
          <h3 class="section-title">预算明细</h3>
          <BudgetTable
            :data="planData.budgetBreakdown"
            :total="planData.totalBudget"
          />
        </div>

        <!-- 温馨提示 -->
        <div class="card tips-card" v-if="planData.tips && planData.tips.length">
          <h3 class="section-title">💡 温馨提示</h3>
          <ul class="tips-list">
            <li v-for="(tip, i) in planData.tips" :key="i">{{ tip }}</li>
          </ul>
        </div>

        <!-- 注意事项 -->
        <div class="card warnings-card" v-if="planData.warnings && planData.warnings.length">
          <h3 class="section-title">⚠️ 注意事项</h3>
          <ul class="warnings-list">
            <li v-for="(w, i) in planData.warnings" :key="i">{{ w }}</li>
          </ul>
        </div>
      </template>
    </div>

    <!-- 底部按钮 -->
    <div class="detail-footer" v-if="planData && planData.success">
      <van-button type="primary" block round @click="handleConsult">
        💬 咨询 AI 助手
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SpotItem from '../components/SpotItem.vue'
import BudgetTable from '../components/BudgetTable.vue'

const router = useRouter()

const planData = ref(null)
const activeDays = ref(1)

onMounted(() => {
  // 从 sessionStorage 获取行程数据
  const stored = sessionStorage.getItem('travelPlan')
  if (stored) {
    try {
      planData.value = JSON.parse(stored)
    } catch {
      planData.value = { success: false, error: '数据解析失败' }
    }
  } else {
    planData.value = { success: false, error: '未找到行程数据' }
  }
})

function handleConsult() {
  const { city, days, totalBudget } = planData.value
  // 拼接上下文消息，传递到对话页
  const context = `去${city}玩${days}天，预算${totalBudget}元，有什么推荐和注意事项？`
  sessionStorage.setItem('chatContext', context)
  router.push('/chat')
}
</script>

<style scoped>
.overview-card {
  margin-bottom: 16px;
}

.trip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trip-header h2 {
  font-size: 20px;
  color: #323233;
  margin: 0;
}

.trip-budget {
  font-size: 16px;
  color: #ee0a24;
  font-weight: 600;
}

.trip-meta {
  margin-top: 8px;
}

.trip-collapse {
  margin-bottom: 16px;
}

.day-schedule {
  padding: 8px 0;
}

.schedule-section {
  margin-bottom: 16px;
}

.schedule-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 8px;
}

.section-label.morning {
  background: #fff7e6;
  color: #fa8c16;
}

.section-label.afternoon {
  background: #e6f7ff;
  color: #1890ff;
}

.section-label.evening {
  background: #f6ffed;
  color: #52c41a;
}

.budget-card,
.tips-card,
.warnings-card {
  margin-bottom: 16px;
}

.tips-list,
.warnings-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tips-list li,
.warnings-list li {
  padding: 8px 0;
  color: #666;
  font-size: 14px;
  border-bottom: 1px solid #f5f5f5;
}

.tips-list li:last-child,
.warnings-list li:last-child {
  border-bottom: none;
}

.detail-footer {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
  max-width: 480px;
  width: 100%;
}

.error-card {
  text-align: center;
  padding: 40px 16px;
}
</style>
