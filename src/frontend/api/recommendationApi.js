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
 * 推荐 AI 对话接口，对接后端 POST /api/chat
 * @param {string} query - 用户输入文本
 * @returns {Promise<{ content?: string, recommendations?: Array }>}
 */
export function chatRecommendation(query) {
  return request({
    url: '/api/chat',
    method: 'POST',
    data: { query },
    header: { 'Content-Type': 'application/json' }
  }).then(res => {
    if (res.statusCode === 200) return res.data || {}
    const msg = (res.data && (res.data.detail || res.data.message)) || '请求失败'
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
  })
}

export { API_BASE_URL }
