/**
 * Recommendation AI API integration with backend AIwardrobe.
 * Contract docs: backend/AIwardrobe/README.md, RecommendationAI/RECOMMENDATION_AI.md
 */

import { API_BASE_URL, request } from '@/utils/request.js'
import { formatApiErrorMessage } from '@/utils/apiErrors.js'

export { API_BASE_URL }

/**
 * Recommendation AI streaming chat endpoint (POST /api/ai/chat/stream).
 * @param {string} query - User input text.
 * @param {Array<{role: string, content: string}>} history - Optional chat history, format: [{ role: 'user'|'ai', content: '...' }]
 * @returns {Promise<{ content: string }>} Final accumulated response.
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
      const msg = formatApiErrorMessage(
        errData,
        `Recommendation request failed (HTTP ${res.status}). Please try again.`
      )
      throw new Error(msg)
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
        // Stream ended: process remaining buffer (the final event is often in the last chunk).
        if (buffer.trim()) processLine(buffer)
        break
      }
    }

    if (finalMessage) return finalMessage
    let trimmed = fullContent.trim()
    if (trimmed.startsWith('```')) {
      trimmed = trimmed.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/m, '').trim()
    }
    // If no final event arrives but accumulated content is JSON (recommendations/plan), parse and return structured payload.
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
 * ========== Weather API / GeoAPI trigger behavior ==========
 *
 * Who triggers and when:
 * The frontend may call GET /api/weather/now only when users enter or return to the Recommendation AI page.
 * No timer and no background polling.
 *
 * Frontend side (this file + RecommendationAI.vue):
 * - Trigger point: RecommendationAI onMounted gets lat/lon and calls getWeatherNow.
 * - Throttle only (default 60s): repeated calls within 60s reuse last result, no new request.
 * - Freshness is controlled by backend weather TTL; frontend no longer caches for 30 minutes.
 *
 * Backend side after /api/weather/now?lat=&lon=:
 * - GeoAPI cache key = round(lat,3), round(lon,3), TTL = 30 minutes.
 * - Weather API cache key = location_id, TTL = 30 minutes.
 * - External API refresh is decided by backend TTL.
 */
const WEATHER_THROTTLE_MS = 60 * 1000
let _weatherThrottle = { at: 0, data: null }

/**
 * Get current weather by lat/lon (for outfit suggestions).
 * Repeated calls within 60s return the last result without requesting backend again.
 * @param {number} lat - Latitude.
 * @param {number} lon - Longitude.
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
 * Recommendation AI conversation persistence ("Your conversations"), requires login.
 */

export function getAuthToken() {
  return uni.getStorageSync('auth_token') || ''
}

/**
 * Get current user's conversation list.
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
 * Create one conversation.
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
 * Update conversation.
 * @param {number|string} id - Conversation id.
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
 * Delete conversation.
 * @param {number|string} id - Conversation id.
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

