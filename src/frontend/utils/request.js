/**
 * 统一 HTTP 基址与 uni.request 封装，供各 api 模块复用。
 * 返回完整响应对象（含 statusCode、data），由调用方判断业务成功与否。
 */
export const API_BASE_URL = 'http://localhost:8000'

/**
 * @param {Object} options - uni.request 的 options，url 可为相对路径
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
