/**
 * 用户与认证相关 API
 * 当前用户资料、头像、密码等，与衣柜（衣物/模特照）无关
 */

import { request, API_BASE_URL } from './wardrobe.js'

export { API_BASE_URL }

// ============ 认证 ============

/**
 * 验证 JWT token 是否有效
 * @param {string} token
 * @returns {Promise<{ statusCode, data }>}
 */
export function authVerify(token) {
  return request({
    url: '/api/auth/verify',
    method: 'GET',
    data: { token }
  })
}

// ============ 当前用户 (users/me) ============

/**
 * 获取当前登录用户信息（含头像、邮箱等）
 * @param {string} token
 * @returns {Promise<{ statusCode, data }>} data: { id, username, email, full_name, avatar_url, is_active, created_at }
 */
export function getUsersMe(token) {
  const qs = token ? `?token=${encodeURIComponent(token)}` : ''
  return request({ url: `/api/users/me${qs}`, method: 'GET' })
}

/**
 * 上传用户头像
 * @param {Object} opts
 * @param {string} opts.token
 * @param {string} opts.filePath - 本地图片路径（uni.chooseImage 返回）
 * @returns {Promise<{ statusCode, data }>} data 为更新后的用户信息
 */
export function uploadUserAvatar(opts) {
  const { token, filePath } = opts || {}
  const url = `${API_BASE_URL}/api/users/me/avatar?token=${encodeURIComponent(token || '')}`
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url,
      filePath,
      name: 'file',
      success: (res) => {
        try {
          const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          resolve({ statusCode: res.statusCode, data })
        } catch (e) {
          resolve({ statusCode: res.statusCode, data: res.data })
        }
      },
      fail: reject
    })
  })
}

/**
 * 更新当前用户资料（用户名、邮箱等）
 * @param {string} token
 * @param {Object} data - { username?, email?, full_name?, avatar_url? }
 * @returns {Promise<{ statusCode, data }>}
 */
export function updateUsersMe(token, data) {
  const qs = token ? `?token=${encodeURIComponent(token)}` : ''
  return request({
    url: `/api/users/me${qs}`,
    method: 'PATCH',
    data: JSON.stringify(data || {}),
    header: { 'Content-Type': 'application/json' }
  })
}

/**
 * 修改当前用户密码
 * @param {string} token
 * @param {string} currentPassword
 * @param {string} newPassword
 * @returns {Promise<{ statusCode, data }>}
 */
export function changePassword(token, currentPassword, newPassword) {
  const qs = token ? `?token=${encodeURIComponent(token)}` : ''
  return request({
    url: `/api/users/me/password${qs}`,
    method: 'PATCH',
    data: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    header: { 'Content-Type': 'application/json' }
  })
}
