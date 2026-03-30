/**
 * Shared HTTP base URL and uni.request wrapper for API modules.
 * Resolves with the full response (statusCode, data, etc.); callers decide success.
 */
export const API_BASE_URL = 'http://localhost:8000'

/**
 * @param {Object} options - uni.request options; url may be relative
 * @returns {Promise<{ statusCode: number, data: any, header?: object }>}
 */
export function request(options) {
  const rawUrl = options.url || ''
  const url = rawUrl.startsWith('http')
    ? rawUrl
    : `${API_BASE_URL}${rawUrl.startsWith('/') ? '' : '/'}${rawUrl}`
  return new Promise((resolve, reject) => {
    uni.request({
      ...options,
      url,
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })
}
