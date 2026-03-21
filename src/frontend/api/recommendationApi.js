/**
 * 推荐 AI 与后端 AIwardrobe 联调 API
 * 约定见 backend/AIwardrobe/README.md、RecommendationAI/RECOMMENDATION_AI.md
 */

import { API_BASE_URL, request } from '@/utils/request.js'

export { API_BASE_URL }

/**
 * 推荐 AI 对话接口（流式），对接后端 POST /api/ai/chat/stream
 * @param {string} query - 用户输入文本
 * @param {Array<{role: string, content: string}>} history - 历史对话（可选），格式 [{ role: 'user'|'ai', content: '...' }]
 * @returns {Promise<{ content: string }>} 累积后的完整回复
 */
export function chatRecommendation(query, history = []) {
  const token = uni.getStorageSync('auth_token') || ''
  const url = token
    ? `${API_BASE_URL}/api/ai/chat/stream?token=${encodeURIComponent(token)}`
    : `${API_BASE_URL}/api/ai/chat/stream`
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, history })
  }).then(async (res) => {
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      const msg = errData.detail || errData.message || `HTTP ${res.status}`
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullContent = ''
    let finalMessage = null

    function processLine(line) {
      if (!line.startsWith('data: ')) return
      try {
        const json = JSON.parse(line.slice(6))
        if (json.type === 'delta' && json.content) fullContent += json.content
        if (json.type === 'final' && json.message) finalMessage = json.message
        if (json.type === 'error') throw new Error(json.message || 'Stream error')
      } catch (e) {
        if (e instanceof SyntaxError) return
        throw e
      }
    }

    while (true) {
      const { done, value } = await reader.read()
      if (value) {
        buffer += decoder.decode(value, { stream: true })
      }
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        processLine(line)
      }
      if (done) {
        // 流结束：处理剩余 buffer（final 事件常在最后一块，必须解析）
        if (buffer.trim()) processLine(buffer)
        break
      }
    }

    if (finalMessage) return finalMessage
    const trimmed = fullContent.trim()
    // 若未收到 final 事件但累积内容是 JSON（含 recommendations/plan），解析后返回结构化消息，供前端按结构优先渲染
    if (trimmed.startsWith('{')) {
      try {
        const parsed = JSON.parse(trimmed)
        if (parsed && typeof parsed === 'object') {
          return {
            role: 'ai',
            rawText: trimmed,
            content: parsed.content || '',
            recommendations: parsed.recommendations || [],
            plan: parsed.plan || null,
            locale: parsed.locale || 'en',
            renderType: (parsed.plan && parsed.plan.days && parsed.plan.days.length) ? 'plan' : (Array.isArray(parsed.recommendations) && parsed.recommendations.length) ? 'recommendation' : 'text'
          }
        }
      } catch (_) {}
    }
    return { content: trimmed }
  })
}

export function getSuggestions() {
  const token = uni.getStorageSync('auth_token') || ''
  if (!token) return Promise.reject(new Error('Please sign in first'))
  const url = `${API_BASE_URL}/api/ai/suggestions?token=${encodeURIComponent(token)}`
  return request({ url, method: 'GET' }).then(res => {
    if (res.statusCode === 200 && res.data && res.data.success) {
      return res.data.data || []
    }
    throw new Error((res.data && (res.data.detail || res.data.message)) || 'Failed to fetch suggestions')
  })
}

export function updateSuggestion(slot, payload) {
  const token = uni.getStorageSync('auth_token') || ''
  if (!token) return Promise.reject(new Error('Please sign in first'))
  const url = `${API_BASE_URL}/api/ai/suggestions/${slot}?token=${encodeURIComponent(token)}`
  return request({ url, method: 'PUT', data: payload }).then(res => {
    if (res.statusCode === 200 && res.data && res.data.success) {
      return res.data.data
    }
    throw new Error((res.data && (res.data.detail || res.data.message)) || 'Failed to update suggestion')
  })
}

/**
 * ========== 天气 API / GeoAPI 触发规律总结 ==========
 *
 * 【谁在何时触发】
 * 只有用户「进入 / 回到推荐 AI 页面」时，前端才会可能请求后端 GET /api/weather/now。
 * 没有定时、没有后台轮询。
 *
 * 【前端】（本文件 + RecommendationAI.vue）
 * - 触发时机：RecommendationAI 挂载时（onMounted）取经纬度并调用 getWeatherNow。
 * - 仅做 throttle（默认 60s）：60s 内重复调用不重复发请求，直接返回上次结果；超过 60s 再请求后端。
 * - 实时性由后端天气 TTL 决定，前端不再做 30 分钟缓存。
 *
 * 【后端】收到 /api/weather/now?lat=&lon= 后：
 * - GeoAPI：缓存 key = round(lat,3), round(lon,3)，TTL = 30 分钟。
 * - 天气 API：缓存 key = location_id，TTL = 30 分钟。
 * - 是否重新请求外部 API 由后端 TTL 决定。
 */
const WEATHER_THROTTLE_MS = 60 * 1000
let _weatherThrottle = { at: 0, data: null }

/**
 * 根据经纬度获取当前天气（穿衣建议用）。60s 内重复调用返回上次结果，不重复请求后端。
 * @param {number} lat - 纬度
 * @param {number} lon - 经度
 * @returns {Promise<{ temp?: string, text?: string, windDesc?: string }>}
 */
export function getWeatherNow(lat, lon) {
  const now = Date.now()
  if (now - _weatherThrottle.at < WEATHER_THROTTLE_MS && _weatherThrottle.data != null) {
    return Promise.resolve(_weatherThrottle.data)
  }
  const token = uni.getStorageSync('auth_token') || ''
  let url = `${API_BASE_URL}/api/weather/now?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`
  if (token) {
    url += `&token=${encodeURIComponent(token)}`
  }
  return request({
    url,
    method: 'GET'
  }).then(res => {
    if (res.statusCode === 200) {
      const data = res.data || {}
      _weatherThrottle = { at: Date.now(), data }
      return data
    }
    const msg = (res.data && (res.data.detail || res.data.message)) || 'Weather request failed'
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  })
}

/**
 * 推荐 AI 对话持久化（Your conversations）：需登录后使用
 */

function getAuthToken() {
  return uni.getStorageSync('auth_token') || ''
}

/**
 * 获取当前用户的对话列表
 * @returns {Promise<{ data: Array<{ id: number, title: string, messages: Array }>, total: number }>}
 */
export function listConversations() {
  const token = getAuthToken()
  if (!token) return Promise.resolve({ data: [], total: 0 })
  const url = `${API_BASE_URL}/api/ai/conversations?token=${encodeURIComponent(token)}`
  return request({ url, method: 'GET' }).then(res => {
    if (res.statusCode === 200 && res.data && res.data.success) {
      return { data: res.data.data || [], total: res.data.total || 0 }
    }
    throw new Error((res.data && res.data.detail) || 'Failed to load conversations')
  })
}

/**
 * 创建一条对话
 * @param {Object} payload - { title?: string, messages?: Array }
 * @returns {Promise<{ id: number, title: string, messages: Array }>}
 */
export function createConversation(payload = {}) {
  const token = getAuthToken()
  if (!token) return Promise.reject(new Error('Please sign in first'))
  const url = `${API_BASE_URL}/api/ai/conversations?token=${encodeURIComponent(token)}`
  return request({
    url,
    method: 'POST',
    data: { title: payload.title || 'New conversation', messages: payload.messages || [] }
  }).then(res => {
    if (res.statusCode === 200 && res.data && res.data.success) {
      return res.data.data
    }
    throw new Error((res.data && res.data.detail) || 'Failed to create conversation')
  })
}

/**
 * 更新对话
 * @param {number|string} id - 对话 id
 * @param {Object} payload - { title?: string, messages?: Array }
 */
export function updateConversation(id, payload) {
  const token = getAuthToken()
  if (!token) return Promise.reject(new Error('Please sign in first'))
  const url = `${API_BASE_URL}/api/ai/conversations/${id}?token=${encodeURIComponent(token)}`
  const body = {}
  if (payload.title !== undefined) body.title = payload.title
  if (payload.messages !== undefined) body.messages = payload.messages
  return request({ url, method: 'PUT', data: body }).then(res => {
    if (res.statusCode === 200 && res.data && res.data.success) return res.data.data
    throw new Error((res.data && res.data.detail) || 'Failed to update conversation')
  })
}

/**
 * 删除对话
 * @param {number|string} id - 对话 id
 */
export function deleteConversation(id) {
  const token = getAuthToken()
  if (!token) return Promise.reject(new Error('Please sign in first'))
  const url = `${API_BASE_URL}/api/ai/conversations/${id}?token=${encodeURIComponent(token)}`
  return request({ url, method: 'DELETE' }).then(res => {
    if (res.statusCode === 200 && res.data && res.data.success) return
    throw new Error((res.data && res.data.detail) || 'Failed to delete conversation')
  })
}

