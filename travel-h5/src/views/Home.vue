<template>
  <div class="page-container">
    <van-nav-bar title="智能旅游助手" :fixed="true" />

    <div class="page-content" style="padding-top: 56px">
      <!-- 规划表单 -->
      <div class="card">
        <h2 class="section-title">规划你的旅行</h2>

        <div class="city-field-wrapper">
          <van-field
            v-model="form.city"
            label="目的地"
            placeholder="输入城市名称（如：张家界、黄山）"
            @focus="onCityFocus"
            @input="onCityInput"
            @blur="onCityBlur"
          />
          <!-- 城市联想下拉框 -->
          <div class="city-suggestions" v-show="showSuggestions && suggestions.length > 0">
            <div
              v-for="city in suggestions"
              :key="city"
              class="suggestion-item"
              @mousedown.prevent="selectSuggestion(city)"
            >
              {{ city }}
            </div>
          </div>
        </div>

        <van-field
          v-model.number="form.budget"
          type="number"
          label="预算"
          placeholder="请输入预算（元）"
        >
          <template #extra>元</template>
        </van-field>

        <van-field
          v-model.number="form.days"
          type="digit"
          label="天数"
          placeholder="请输入旅行天数"
        >
          <template #extra>天</template>
        </van-field>

        <van-button
          type="primary"
          block
          round
          :disabled="showProgress"
          :loading="showProgress"
          loading-text="规划中..."
          class="common-button primary-button"
          style="margin-top: 16px"
          @click="handleSubmit"
        >
          开始规划
        </van-button>
      </div>

      <!-- 热门目的地（动态轮换） -->
      <div class="card">
        <h2 class="section-title">热门目的地</h2>
        <div class="city-grid" :key="rotateKey">
          <div
            v-for="(city, idx) in hotCities"
            :key="city"
            class="city-card"
            :style="{ animation: `fade-in-up 0.45s ease forwards ${idx * 0.08}s` }"
            @click="selectCity(city)"
          >
            <span class="city-name">{{ city }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 规划进度遮罩 -->
    <van-overlay :show="showProgress" class="progress-overlay" :duration="0.3">
      <div class="progress-card">
        <div class="progress-icon">✈️</div>
        <div class="progress-title">正在为你规划行程</div>
        <div class="progress-message">{{ progressMessage }}</div>
        <!-- 三点跳动 -->
        <div class="progress-dots">
          <span
            v-for="i in 3"
            :key="i"
            class="dot"
            :style="{ animationDelay: (i - 1) * 0.2 + 's' }"
          ></span>
        </div>
        <!-- 彩虹进度条 -->
        <div class="progress-bar-track">
          <div class="progress-bar-fill"></div>
        </div>
      </div>
    </van-overlay>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'

const router = useRouter()

// 支持的城市列表（含省会和热门旅游城市，约 120 个）
const cities = [
  '北京', '上海', '广州', '深圳', '成都', '杭州', '西安', '重庆',
  '南京', '武汉', '苏州', '长沙', '天津', '郑州', '济南', '青岛',
  '大连', '沈阳', '哈尔滨', '长春', '福州', '厦门', '南昌', '合肥',
  '昆明', '贵阳', '南宁', '桂林', '海口', '三亚', '丽江', '大理',
  '兰州', '乌鲁木齐', '拉萨', '呼和浩特', '太原', '石家庄',
  // 热门旅游城市
  '张家界', '黄山', '九寨沟', '敦煌', '张家口', '秦皇岛', '承德',
  '洛阳', '开封', '泰山', '曲阜', '蓬莱', '威海', '烟台',
  '凤凰', '岳阳', '衡山', '婺源', '景德镇', '庐山', '井冈山',
  '黄龙', '峨眉山', '乐山', '稻城', '色达', '都江堰', '青城山',
  '香格里拉', '西双版纳', '腾冲', '泸沽湖', '梅里雪山',
  '阳朔', '北海', '涠洲岛', '德天瀑布',
  '延安', '华山', '壶口瀑布',
  '嘉峪关', '张掖', '天水',
  '西宁', '青海湖', '茶卡盐湖',
  '银川', '中卫', '沙坡头',
  '喀纳斯', '吐鲁番', '伊犁',
  '漠河', '雪乡', '长白山', '镜泊湖',
  '呼伦贝尔', '满洲里', '阿尔山', '锡林郭勒',
  '黄果树', '荔波', '梵净山', '千户苗寨', '镇远',
  '武当山', '神农架', '恩施', '宜昌',
  '五台山', '平遥', '大同', '壶口',
  '宏村', '西递',
  '南浔', '乌镇', '周庄', '同里', '西塘',
  '三亚湾', '亚龙湾', '蜈支洲岛',
  '鼓浪屿', '武夷山', '土楼',
  '霞浦', '太姥山',
]

// 动态热门城市（6 个，每 5 秒轮换）
const hotCities = ref([])
const rotateKey = ref(0)
let rotateTimer = null

function rotateHotCities() {
  const pool = cities.filter(c => c.length <= 5)
  const shuffled = [...pool].sort(() => Math.random() - 0.5)
  hotCities.value = shuffled.slice(0, 6)
  rotateKey.value++ // 触发 grid key 变更，重置入场动画
}

onMounted(() => {
  rotateHotCities()
  rotateTimer = setInterval(rotateHotCities, 5000)
})

onUnmounted(() => {
  if (rotateTimer) clearInterval(rotateTimer)
})

const showProgress = ref(false)
const progressMessage = ref('正在连接服务...')
const showSuggestions = ref(false)
const form = reactive({
  city: '',
  budget: null,
  days: null
})

// 根据输入内容过滤联想城市（最多 8 条）
const suggestions = computed(() => {
  const keyword = form.city.trim()
  if (!keyword) return cities.slice(0, 8)
  return cities.filter(c => c.includes(keyword)).slice(0, 8)
})

// 城市字段获得焦点 → 显示联想
function onCityFocus() {
  showSuggestions.value = true
}

// 输入城市 → 显示联想
function onCityInput() {
  showSuggestions.value = true
}

// 失去焦点 → 延迟隐藏（让 mousedown 有机会触发）
let blurTimer = null
function onCityBlur() {
  blurTimer = setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

// 从联想列表中选择城市
function selectSuggestion(city) {
  form.city = city
  showSuggestions.value = false
  if (blurTimer) clearTimeout(blurTimer)
}

// 从热门城市中选择
function selectCity(city) {
  form.city = city
  showSuggestions.value = false
}

async function handleSubmit() {
  if (!form.city) {
    showToast('请选择目的地城市')
    return
  }
  if (!form.budget || form.budget < 100) {
    showToast('预算不能低于100元')
    return
  }
  if (!form.days || form.days < 1 || form.days > 30) {
    showToast('天数需在1-30天之间')
    return
  }

  // 显示进度遮罩
  showProgress.value = true
  progressMessage.value = '正在连接服务...'

  try {
    const response = await fetch('/api/travel/recommend/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ' + localStorage.getItem('token')
      },
      body: JSON.stringify({
        city: form.city,
        budget: form.budget,
        days: form.days
      })
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
            if (data.type === 'progress' && data.content) {
              progressMessage.value = data.content
            } else if (data.type === 'result' && data.data) {
              // 规划完成，存储结果并跳转
              sessionStorage.setItem('travelPlan', JSON.stringify(data.data))
              showProgress.value = false
              router.push('/detail')
              return
            } else if (data.type === 'error') {
              showToast('规划失败: ' + (data.error || data.message || '未知错误'))
              showProgress.value = false
              return
            }
          } catch (e) {
            console.warn('SSE 解析失败:', trimmed.substring(0, 80), e.message)
          }
        }
      }
    }
  } catch (error) {
    console.error('规划请求失败:', error)
    showToast('规划失败: ' + (error.message || '网络错误'))
  } finally {
    showProgress.value = false
  }
}
</script>

<style scoped>
/* 城市字段包装器（用于定位下拉框） */
.city-field-wrapper {
  position: relative;
}

/* 联想下拉框 */
.city-suggestions {
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  z-index: 999;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  max-height: 260px;
  overflow-y: auto;
  margin: 0 16px;
}

.suggestion-item {
  padding: 12px 16px;
  font-size: 15px;
  color: #323233;
  border-bottom: 1px solid #f5f5f5;
  cursor: pointer;
  transition: background 0.15s;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:active,
.suggestion-item:hover {
  background: #f0f8ff;
}

.city-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.city-card {
  background: linear-gradient(135deg, #1989fa, #36cbcb);
  border-radius: 8px;
  padding: 20px 12px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
  opacity: 0;
}

.city-card:active {
  transform: scale(0.95);
}

.city-name {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
}

/* 规划进度遮罩 */
.progress-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px 32px;
  width: min(280px, 70vw);
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

/* 脉动飞机图标 */
.progress-icon {
  font-size: 48px;
  animation: pulse 1.6s ease-in-out infinite;
}

.progress-title {
  margin-top: 16px;
  font-size: 17px;
  font-weight: 600;
  color: #323233;
}

.progress-message {
  margin-top: 10px;
  font-size: 14px;
  color: #999;
  min-height: 20px;
  word-break: break-all;
}

/* 三点跳动 */
.progress-dots {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-top: 10px;
}

.progress-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1989fa;
  animation: dot-bounce 1.4s ease-in-out infinite;
  opacity: 0.6;
}

/* 彩虹进度条 */
.progress-bar-track {
  margin-top: 20px;
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  position: absolute;
  top: 0;
  left: -50%;
  width: 50%;
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #1989fa, #36cbcb, #ff976a, #1989fa);
  animation: progress-sweep 2s linear infinite;
}

/* 城市卡片初始透明，由入场动画设为可见 */
.city-card {
  opacity: 0;
}
</style>
