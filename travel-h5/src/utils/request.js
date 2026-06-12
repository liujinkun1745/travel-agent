import axios from 'axios'
import { showToast } from 'vant'

const request = axios.create({
  baseURL: '/api',
  timeout: 120000 // 2 分钟，给 AI 响应足够时间
})

// 响应拦截器 - 统一错误处理
request.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code && data.code !== 200) {
      showToast(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (error) => {
    const message = error.response?.data?.message || error.message || '网络错误'
    showToast(message)
    return Promise.reject(error)
  }
)

export default request
