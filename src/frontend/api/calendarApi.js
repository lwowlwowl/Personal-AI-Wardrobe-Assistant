/**
 * 日历穿搭记录模块 API
 * 约定见 frontend/pages/index/components/MyCalendar/MY_CALENDAR.md
 * - GET /api/calendar/outfits
 * - POST /api/calendar/outfits
 */

import { API_BASE_URL, request } from './wardrobe.js'

/**
 * 获取指定月份的穿搭记录
 * @param {Object} params
 * @param {string} params.token - JWT token（query 传递）
 * @param {number} params.year  - 年份，如 2025
 * @param {number} params.month - 月份，1-12
 * @returns {Promise<{ statusCode, data }>}
 */
export function getCalendarOutfits(params) {
  const { token, year, month } = params || {}
  const query = new URLSearchParams()
  if (token) query.set('token', token)
  if (year != null) query.set('year', year)
  if (month != null) query.set('month', month)
  const qs = query.toString()
  return request({
    url: `/api/calendar/outfits${qs ? '?' + qs : ''}`,
    method: 'GET'
  })
}

/**
 * 保存 / 更新 / 删除某天的穿搭记录（全量覆盖）
 * - items 为空数组时表示删除该日期记录
 * @param {Object} payload
 * @param {string} payload.token - JWT token（query 传递）
 * @param {string} payload.date  - 日期（YYYY-MM-DD）
 * @param {Array}  payload.items - 单品数组（可为空）
 * @returns {Promise<{ statusCode, data }>}
 */
export function saveCalendarOutfits(payload) {
  const { token, date, items } = payload || {}
  const qs = new URLSearchParams()
  if (token) qs.set('token', token)
  return request({
    url: `/api/calendar/outfits?${qs.toString()}`,
    method: 'POST',
    data: {
      date,
      items: Array.isArray(items) ? items : []
    },
    header: {
      'Content-Type': 'application/json'
    }
  })
}

export { API_BASE_URL }

