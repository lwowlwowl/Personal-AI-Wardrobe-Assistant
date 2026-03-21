/**
 * Virtual try-on: upload images + ComfyUI generation (POST /api/virtual-try-on/*)
 */
import { API_BASE_URL } from '@/utils/request.js'

/** Same storage keys as legacy VirtualTryOn; strips quotes for JWT */
export function getCleanAuthToken() {
  let t1 = uni.getStorageSync('token')
  let t2 = uni.getStorageSync('auth_token')
  let userInfo = uni.getStorageSync('user_info')

  let t3 = ''
  if (userInfo && typeof userInfo === 'object' && userInfo.token) {
    t3 = userInfo.token
  }

  let t4 = ''
  let t5 = ''
  if (typeof window !== 'undefined') {
    t4 = localStorage.getItem('token') || ''
    t5 = localStorage.getItem('auth_token') || ''
  }

  let rawToken = t1 || t2 || t3 || t4 || t5 || ''

  if (typeof rawToken === 'object') {
    rawToken = rawToken.token || rawToken.access_token || ''
  }

  return String(rawToken).trim().replace(/^"|"$/g, '')
}

/**
 * @param {string} filePath - local path or blob URL (uni.uploadFile)
 * @param {'person'|'clothing'} imageType
 * @returns {Promise<string>} server filename
 */
export function uploadVirtualTryOnImage(filePath, imageType) {
  return new Promise((resolve, reject) => {
    const token = getCleanAuthToken()
    if (!token) {
      reject(new Error('Please sign in first'))
      return
    }

    uni.uploadFile({
      url: `${API_BASE_URL}/api/virtual-try-on/upload-image`,
      filePath,
      name: 'file',
      formData: {
        image_type: imageType,
        token
      },
      success: (res) => {
        try {
          const data = JSON.parse(res.data)
          if (data.success) {
            resolve(data.filename || data.data?.filename)
          } else {
            reject(new Error(data.message || 'Upload failed'))
          }
        } catch (e) {
          reject(new Error('Invalid server response'))
        }
      },
      fail: (err) => {
        reject(err || new Error('Network error'))
      }
    })
  })
}

/**
 * @param {{ person_image: string, clothing_image: string, token: string, model_type?: string }} body
 * @returns {Promise<string>} result_image (URL or data URL)
 */
export function generateVirtualTryOn(body) {
  const { person_image, clothing_image, token, model_type = '2509' } = body
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}/api/virtual-try-on/generate`,
      method: 'POST',
      header: { 'content-type': 'application/json' },
      data: {
        person_image,
        clothing_image,
        token,
        model_type
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data?.success && res.data?.data?.result_image) {
          resolve(res.data.data.result_image)
        } else {
          reject(new Error(res.data?.message || 'Generation failed'))
        }
      },
      fail: (err) => reject(err || new Error('Network error'))
    })
  })
}
