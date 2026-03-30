/**
 * Calendar outfit-record API module.
 * - GET /api/calendar/outfits
 * - POST /api/calendar/outfits
 * Contract: src/docs/api/my_calendar_api.md
 */

import { API_BASE_URL, request } from './wardrobe.js'

/**
 * Get outfit records for a specific month.
 * @param {Object} params
 * @param {string} params.token - JWT token (passed via query).
 * @param {number} params.year  - Year, e.g. 2025.
 * @param {number} params.month - Month, 1-12.
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
 * Save / update / delete one day's outfit record (full replace).
 * - Empty items array means delete that date's record.
 * @param {Object} payload
 * @param {string} payload.token - JWT token (passed via query).
 * @param {string} payload.date  - Date (YYYY-MM-DD).
 * @param {Array}  payload.items - Clothing-item array (can be empty).
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

