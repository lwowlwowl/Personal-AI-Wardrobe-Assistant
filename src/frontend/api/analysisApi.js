/**
 * 衣柜分析 API：趋势、概览、分类分布、闲置率、最常穿、颜色/风格统计、闲置明细
 * 与 backend /api/analysis/* 对接
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
 * 发起分析 API 请求（GET，参数与 token 放在 query）
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

/** 供其他模块（如日历、记录穿着）取得 token */
export { getToken }

// ---------- 分析接口 ----------

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

/** GET /api/analysis/weekly-activity — 本周总穿戴次数、环比趋势、每日分布、分类统计（主面板与 Activity Report 共用） */
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
