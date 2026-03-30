/**
 * User and authentication APIs.
 * Covers profile/avatar/password; unrelated to wardrobe item/model-photo APIs.
 */

import { request, API_BASE_URL } from './wardrobe.js'

export { API_BASE_URL }

// ============ Authentication ============

/**
 * Login: POST /api/auth/login
 * Request body follows schemas.UserLogin: username, password, remember.
 * @param {{ username: string, password: string, remember?: boolean }} body
 * @returns {Promise<{ statusCode: number, data: any }>}
 */
export function loginAuth(body) {
  const { username, password, remember = false } = body || {}
  return request({
    url: '/api/auth/login',
    method: 'POST',
    data: JSON.stringify({
      username,
      password,
      remember: remember === true
    }),
    header: {
      'Content-Type': 'application/json',
      Accept: 'application/json'
    }
  })
}

/**
 * Register: POST /api/auth/register
 * Request body follows schemas.UserCreate: username, email, password, confirm_password.
 * @param {{ username: string, email: string, password: string, confirm_password: string }} body
 * @returns {Promise<{ statusCode: number, data: any }>}
 */
export function registerAuth(body) {
  const { username, email, password, confirm_password } = body || {}
  return request({
    url: '/api/auth/register',
    method: 'POST',
    data: JSON.stringify({
      username,
      email,
      password,
      confirm_password
    }),
    header: { 'Content-Type': 'application/json' },
    timeout: 10000
  })
}

/**
 * Reset password by identity: match email + username for same account, then reset
 * (POST /api/auth/reset-password-by-identity).
 * @param {{ email: string, username: string, new_password: string, confirm_password: string }} body
 * @returns {Promise<{ statusCode: number, data: any }>}
 */
export function resetPasswordByIdentity(body) {
  const { email, username, new_password, confirm_password } = body || {}
  return request({
    url: '/api/auth/reset-password-by-identity',
    method: 'POST',
    data: JSON.stringify({
      email,
      username,
      new_password,
      confirm_password
    }),
    header: { 'Content-Type': 'application/json' },
    timeout: 15000
  })
}

/**
 * Verify whether JWT token is valid.
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

// ============ Current User (users/me) ============

/**
 * Get current signed-in user info (including avatar/email/etc).
 * @param {string} token
 * @returns {Promise<{ statusCode, data }>} data: { id, username, email, full_name, avatar_url, is_active, created_at }
 */
export function getUsersMe(token) {
  const qs = token ? `?token=${encodeURIComponent(token)}` : ''
  return request({ url: `/api/users/me${qs}`, method: 'GET' })
}

/**
 * Upload user avatar.
 * @param {Object} opts
 * @param {string} opts.token
 * @param {string} opts.filePath - Local image path (from uni.chooseImage).
 * @returns {Promise<{ statusCode, data }>} data is the updated user info.
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
 * Update current user profile (username, email, etc).
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
 * Change current user's password.
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
