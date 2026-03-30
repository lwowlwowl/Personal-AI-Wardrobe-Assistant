/**
 * Wardrobe-to-backend integration API module.
 * Includes clothing/model-photo endpoints. User/auth endpoints are in userApi.js.
 */

import { API_BASE_URL, request } from '@/utils/request.js'

export { API_BASE_URL, request }

// ============ Health Check ============

/**
 * Backend health check.
 * @returns {Promise<{ statusCode, data }>}
 */
export function healthCheck() {
  return request({ url: '/api/health', method: 'GET' })
}

// ============ Clothing ============

/**
 * Get clothing list (pagination, filters, sorting).
 * @param {Object} params
 * @param {string} params.token
 * @param {number} [params.page=1]
 * @param {number} [params.page_size=20]
 * @param {string} [params.order_by=created_at]
 * @param {boolean} [params.order_desc=true]
 * @param {string} [params.category]
 * @param {string} [params.season]
 * @param {string} [params.color]
 * @param {string} [params.search]
 * @returns {Promise<{ statusCode, data }>}
 */
export function getClothingList(params) {
  const { token, page = 1, page_size = 20, order_by = 'created_at', order_desc = true, category, season, color, brand, is_favorite, search } = params || {}
  const query = new URLSearchParams()
  if (token) query.set('token', token)
  if (page != null) query.set('page', page)
  if (page_size != null) query.set('page_size', page_size)
  if (order_by != null) query.set('order_by', order_by)
  if (order_desc != null) query.set('order_desc', order_desc)
  if (category != null) query.set('category', category)
  if (season != null) query.set('season', season)
  if (color != null) query.set('color', color)
  if (brand != null) query.set('brand', brand)
  if (is_favorite != null) query.set('is_favorite', is_favorite)
  if (search != null) query.set('search', search)
  const qs = query.toString()
  return request({ url: `/api/clothing${qs ? '?' + qs : ''}`, method: 'GET' })
}

/**
 * Upload clothing (image + form fields).
 * @param {Object} opts
 * @param {string} opts.token
 * @param {string} [opts.filePath] - Local temp image path (uni.chooseImage or blob URL).
 * @param {File} [opts.file] - File object from browser drag/drop; mutually exclusive with filePath.
 * @param {Object} opts.formData - { name, category, subcategory, color, season, brand, tags, description, price, purchase_date }
 * @returns {Promise<{ statusCode, data }>}
 */
export function uploadClothing(opts) {
  const { token, filePath, file, formData } = opts || {}
  const url = `${API_BASE_URL}/api/clothing/upload?token=${encodeURIComponent(token || '')}`

  const formPayload = {
    name: formData?.name ?? '',
    category: formData?.category ?? '',
    subcategory: formData?.subcategory ?? '',
    color: formData?.color ?? '',
    season: formData?.season ?? '',
    brand: formData?.brand ?? '',
    tags: formData?.tags ?? '',
    description: formData?.description ?? '',
    price: formData?.price ?? '',
    purchase_date: formData?.purchase_date ?? ''
  }

  // Drag/drop and similar flows: upload via FormData + fetch when File/Blob exists.
  if (file != null && (file instanceof File || file instanceof Blob)) {
    const fd = new FormData()
    if (file instanceof File) {
      fd.append('file', file)
    } else {
      fd.append('file', file, file.name || 'image.jpg')
    }
    Object.entries(formPayload).forEach(([k, v]) => fd.append(k, String(v)))
    return fetch(url, { method: 'POST', body: fd })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}))
        return { statusCode: res.status, data }
      })
  }

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url,
      filePath,
      name: 'file',
      formData: formPayload,
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
 * Delete clothing.
 * @param {string} token
 * @param {number} clothingId
 * @returns {Promise<{ statusCode, data }>}
 */
export function deleteClothing(token, clothingId) {
  const qs = new URLSearchParams({ token }).toString()
  return request({ url: `/api/clothing/${clothingId}?${qs}`, method: 'DELETE' })
}

/**
 * Update clothing (optional fields).
 * @param {string} token
 * @param {number} clothingId
 * @param {Object} updateData - { name, category, color, season, brand, tags, description, price, purchase_date, is_favorite }
 * @returns {Promise<{ statusCode, data }>}
 */
export function updateClothing(token, clothingId, updateData) {
  const qs = new URLSearchParams({ token }).toString()
  const body = new URLSearchParams()
  Object.entries(updateData || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null) body.append(k, String(v))
  })
  return request({
    url: `/api/clothing/${clothingId}?${qs}`,
    method: 'PUT',
    data: body.toString(),
    header: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

// ============ Model Photos ============

/**
 * Get model photo list.
 * @param {Object} params
 * @param {string} params.token
 * @param {number} [params.page=1]
 * @param {number} [params.page_size=20]
 * @param {boolean} [params.is_active=true]
 * @returns {Promise<{ statusCode, data }>}
 */
export function getModelPhotos(params) {
  const { token, page = 1, page_size = 20, is_active = true } = params || {}
  const query = new URLSearchParams()
  if (token) query.set('token', token)
  if (page != null) query.set('page', page)
  if (page_size != null) query.set('page_size', page_size)
  if (is_active != null) query.set('is_active', is_active)
  const qs = query.toString()
  return request({ url: `/api/model-photos${qs ? '?' + qs : ''}`, method: 'GET' })
}

/**
 * Get current user's primary model photo (default portrait for virtual try-on).
 * @param {string} token
 * @returns {Promise<{ statusCode, data }>}
 */
export function getPrimaryModelPhoto(token) {
  const qs = new URLSearchParams()
  if (token) qs.set('token', token)
  return request({ url: `/api/model-photos/primary?${qs.toString()}`, method: 'GET' })
}

/**
 * Upload model photo.
 * @param {Object} opts
 * @param {string} opts.token
 * @param {string} opts.filePath
 * @param {Object} opts.formData - { photo_name, description, is_primary }
 * @returns {Promise<{ statusCode, data }>}
 */
export function uploadModelPhoto(opts) {
  const { token, filePath, formData } = opts || {}
  const url = `${API_BASE_URL}/api/model-photos/upload?token=${encodeURIComponent(token || '')}`
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url,
      filePath,
      name: 'file',
      formData: {
        photo_name: formData?.photo_name ?? '',
        description: formData?.description ?? '',
        is_primary: formData?.is_primary === true ? 'true' : 'false'
      },
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
 * Delete model photo (soft delete or hard delete).
 * @param {string} token
 * @param {number} photoId
 * @param {boolean} [hardDelete=false]
 * @returns {Promise<{ statusCode, data }>}
 */
export function deleteModelPhoto(token, photoId, hardDelete = false) {
  const query = new URLSearchParams({ token, hard_delete: hardDelete ? 'true' : 'false' }).toString()
  return request({ url: `/api/model-photos/${photoId}?${query}`, method: 'DELETE' })
}

/**
 * Set as primary model photo.
 * @param {string} token
 * @param {number} photoId
 * @returns {Promise<{ statusCode, data }>}
 */
export function setModelPhotoPrimary(token, photoId) {
  const qs = new URLSearchParams({ token }).toString()
  return request({ url: `/api/model-photos/${photoId}/set-primary?${qs}`, method: 'POST' })
}

/**
 * Update model photo metadata.
 * @param {string} token
 * @param {number} photoId
 * @param {Object} updateData - { photo_name, description, is_primary }
 * @returns {Promise<{ statusCode, data }>}
 */
export function updateModelPhoto(token, photoId, updateData) {
  const qs = new URLSearchParams({ token }).toString()
  const body = new URLSearchParams()
  Object.entries(updateData || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null) body.append(k, v === true ? 'true' : v === false ? 'false' : String(v))
  })
  return request({
    url: `/api/model-photos/${photoId}?${qs}`,
    method: 'PUT',
    data: body.toString(),
    header: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

// Image URL normalization + H5 probe (Wardrobe UI)
export {
  resolveWardrobeImageUrl,
  applyClothingImageUrlFixes,
  isClothingDeleteNotFoundResponse,
  isPlaceholderWardrobeUrl
} from './wardrobeMedia.js'
