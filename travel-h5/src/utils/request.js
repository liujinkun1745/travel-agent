import axios from 'axios'
import { showToast } from 'vant'

const request = axios.create({
  baseURL: '/api',
  timeout: 120000 // 2 分钟，给 AI 响应足够时间
})

// 请求拦截器 — 注入 JWT token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = 'Bearer ' + token
    }
    return config
  },
  (error) => Promise.reject(error)
)

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
    // 401 → 跳转登录页
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.hash = '#/login'
      showToast('请先登录')
      return Promise.reject(error)
    }
    const message = error.response?.data?.message || error.message || '网络错误'
    showToast(message)
    return Promise.reject(error)
  }
)

export default request
