/**
 * Wardrobe analytics API: trend, summary, category distribution, idle rate,
 * most worn items, color/style stats, and idle-item detail.
 * Integrated with backend /api/analysis/*.
 */

import { API_BASE_URL, request } from '@/utils/request.js'

function getToken() {
  const keys = ['auth_token', 'token', 'access_token', 'userToken']
  for (const key of keys) {
    try {
      const value = uni.getStorageSync(key)
      if (value && typeof value === 'string' && value.length > 10) return value
    } catch (e) {}
  }
  return null
}

/**
 * Send analytics API request (GET, with params + token in query).
 */
export async function apiRequest(path, params = {}) {
  const token = getToken()
  const query = new URLSearchParams({ ...params, token: token || '' })
  const qs = query.toString()
  const rel = `${path.startsWith('/') ? path : `/${path}`}${qs ? `?${qs}` : ''}`
  try {
    const res = await request({
      url: rel,
      method: 'GET',
      header: { 'Content-Type': 'application/json' },
      timeout: 10000
    })
    if (res.statusCode === 200) return res.data
    if (res.statusCode === 401) {
      uni.showToast({ title: 'Session expired. Please sign in again.', icon: 'none' })
      return null
    }
    return null
  } catch (err) {
    console.error('Analysis API request error:', err)
    return null
  }
}

export function isLoggedIn() {
  return !!getToken()
}

/** Export token getter for other modules (e.g. calendar, wear records). */
export { getToken }

// ---------- Analytics Endpoints ----------

/** GET /api/analysis/total-items/trend?view_by=yearly|monthly|daily */
export function getTrend(viewBy = 'yearly') {
  return apiRequest('/api/analysis/total-items/trend', { view_by: viewBy })
}

/** GET /api/analysis/total-items/summary */
export function getSummary() {
  return apiRequest('/api/analysis/total-items/summary')
}

/** GET /api/analysis/total-items/category-distribution */
export function getCategoryDistribution() {
  return apiRequest('/api/analysis/total-items/category-distribution')
}

/** GET /api/analysis/idle-rate?days=30 */
export function getIdleRate(days = 30) {
  return apiRequest('/api/analysis/idle-rate', { days })
}

/** GET /api/analysis/top-color */
export function getTopColor() {
  return apiRequest('/api/analysis/top-color')
}

/** GET /api/analysis/top-style */
export function getTopStyle() {
  return apiRequest('/api/analysis/top-style')
}

/** GET /api/analysis/most-worn?time_range=yearly|monthly|daily&limit=5 */
export function getMostWorn(timeRange = 'yearly', limit = 5) {
  return apiRequest('/api/analysis/most-worn', { time_range: timeRange, limit })
}

/** GET /api/analysis/weekly-activity — weekly total wears, WoW trend, daily distribution, category stats (used by main panel + Activity Report). */
export function getWeeklyActivity() {
  return apiRequest('/api/analysis/weekly-activity')
}

/** GET /api/analysis/idle-items/detail?page=1&page_size=20&time_filter=&season_filter= */
export function getIdleItemsDetail(params = {}) {
  const { page = 1, pageSize = 20, timeFilter = null, seasonFilter = null } = params
  const q = { page, page_size: pageSize }
  if (timeFilter && timeFilter !== 'all') q.time_filter = timeFilter
  if (seasonFilter && seasonFilter !== 'all') q.season_filter = seasonFilter
  return apiRequest('/api/analysis/idle-items/detail', q)
}

/** GET /api/analysis/suggested-additions?limit=3 */
export function getSuggestedAdditions(limit = 3) {
  return apiRequest('/api/analysis/suggested-additions', { limit })
}

export { API_BASE_URL }
