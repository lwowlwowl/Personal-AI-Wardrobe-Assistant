/**
 * 衣柜与后端联调 API 模块
 * 集中管理认证、衣物、模特照片等接口，便于复用与维护
 */

const API_BASE_URL = 'http://localhost:8000'

/**
 * 封装 uni.request，返回完整 response（含 statusCode、data）供调用端判断
 * @param {Object} options - uni.request 的 options
 * @returns {Promise<{ statusCode, data }>}
 */
function request(options) {
  const url = options.url.startsWith('http') ? options.url : `${API_BASE_URL}${options.url.startsWith('/') ? '' : '/'}${options.url}`
  return new Promise((resolve, reject) => {
    uni.request({
      ...options,
      url,
      success: (res) => resolve(res),
      fail: (err) => reject(err)
    })
  })
}

// ============ 健康检查 ============

/**
 * 后端健康检查
 * @returns {Promise<{ statusCode, data }>}
 */
export function healthCheck() {
  return request({ url: '/api/health', method: 'GET' })
}

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

// ============ 衣物 (Clothing) ============

/**
 * 获取衣物列表（分页、筛选、排序）
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
 * 上传衣物（图片 + 表单字段）
 * @param {Object} opts
 * @param {string} opts.token
 * @param {string} opts.filePath - 本地暂存图片路径（uni.chooseImage 返回）
 * @param {Object} opts.formData - { name, category, color, season, brand, tags, description, price, purchase_date }
 * @returns {Promise<{ statusCode, data }>}
 */
export function uploadClothing(opts) {
  const { token, filePath, formData } = opts || {}
  const url = `${API_BASE_URL}/api/clothing/upload?token=${encodeURIComponent(token || '')}`
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url,
      filePath,
      name: 'file',
      formData: {
        name: formData?.name ?? '',
        category: formData?.category ?? '',
        color: formData?.color ?? '',
        season: formData?.season ?? '',
        brand: formData?.brand ?? '',
        tags: formData?.tags ?? '',
        description: formData?.description ?? '',
        price: formData?.price ?? '',
        purchase_date: formData?.purchase_date ?? ''
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
 * 删除衣物
 * @param {string} token
 * @param {number} clothingId
 * @returns {Promise<{ statusCode, data }>}
 */
export function deleteClothing(token, clothingId) {
  const qs = new URLSearchParams({ token }).toString()
  return request({ url: `/api/clothing/${clothingId}?${qs}`, method: 'DELETE' })
}

/**
 * 更新衣物（可选字段）
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

// ============ 模特照片 (Model Photos) ============

/**
 * 获取模特照片列表
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
 * 上传模特照片
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
 * 删除模特照片（软删除或硬删除）
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
 * 设为主要模特照片
 * @param {string} token
 * @param {number} photoId
 * @returns {Promise<{ statusCode, data }>}
 */
export function setModelPhotoPrimary(token, photoId) {
  const qs = new URLSearchParams({ token }).toString()
  return request({ url: `/api/model-photos/${photoId}/set-primary?${qs}`, method: 'POST' })
}

/**
 * 更新模特照片信息
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

export { API_BASE_URL }
