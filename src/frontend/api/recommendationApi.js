/**
 * 推荐 AI 与后端 AIwardrobe 联调 API
 * 约定见 backend/AIwardrobe/README.md、RecommendationAI/RECOMMENDATION_AI.md
 */

const API_BASE_URL = 'http://localhost:8000'

function request(options) {
  const url = options.url.startsWith('http') ? options.url : `${API_BASE_URL}${options.url.startsWith('/') ? '' : '/'}${options.url}`
  return new Promise((resolve, reject) => {
    uni.request({
      ...options,
      url,
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })
}

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
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const json = JSON.parse(line.slice(6))
            if (json.type === 'delta' && json.content) fullContent += json.content
            if (json.type === 'error') throw new Error(json.message || 'Stream error')
          } catch (e) {
            if (e instanceof SyntaxError) continue
            throw e
          }
        }
      }
    }
    return { content: fullContent.trim() }
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
    const msg = (res.data && (res.data.detail || res.data.message)) || '天气请求失败'
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  })
}

export { API_BASE_URL, WEATHER_THROTTLE_MS }
