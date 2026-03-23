/**
 * Virtual try-on: upload images + ComfyUI generation (POST /api/virtual-try-on/*)
 */
import { API_BASE_URL } from '@/utils/request.js'

function parseUniError(err, fallback = 'Network error') {
  if (!err) return fallback
  if (err instanceof Error && err.message) return err.message
  if (typeof err === 'string') return err
  const msg = err.errMsg || err.message || err.msg || ''
  const status = err.statusCode != null ? ` (status ${err.statusCode})` : ''
  return msg ? `${msg}${status}` : fallback
}

/** 从 FastAPI / 本项目 JSON 取出错误文案 */
function extractBackendMessage(data) {
  if (!data || typeof data !== 'object') return ''
  if (typeof data.message === 'string' && data.message.trim()) return data.message.trim()
  const d = data.detail
  if (typeof d === 'string' && d.trim()) return d.trim()
  if (Array.isArray(d) && d.length) {
    return d
      .map((x) => (typeof x === 'object' && x?.msg ? x.msg : String(x)))
      .filter(Boolean)
      .join('; ')
  }
  return ''
}

/**
 * 解析 upload / upload-from-storage 的 JSON 响应，成功返回 ComfyUI 文件名
 */
function parseVirtualTryUploadResponse(res, imageType) {
  let payload = res.data
  if (typeof payload === 'string') {
    try {
      payload = JSON.parse(payload || '{}')
    } catch {
      const code = res.statusCode
      if (code === 503 || code === 502) {
        throw new Error(
          `上传失败：服务不可用 (HTTP ${code})。请确认 ComfyUI 已启动且 COMFYUI_SERVER 地址正确`
        )
      }
      throw new Error(`上传响应无效 (${imageType})：HTTP ${res.statusCode}`)
    }
  }
  const data = payload || {}
  const httpOk = res.statusCode >= 200 && res.statusCode < 300
  const backendMsg = extractBackendMessage(data)
  if (httpOk && data.success) {
    const name = data.filename || data.data?.filename
    if (!name || String(name).trim() === '') {
      throw new Error(`Upload OK but missing filename (${imageType})`)
    }
    return name
  }
  if (backendMsg) throw new Error(backendMsg)
  throw new Error(`上传失败 (${imageType})：HTTP ${res.statusCode || 'unknown'}`)
}

function joinBaseUrl(path) {
  const base = String(API_BASE_URL || '').replace(/\/$/, '')
  const p = path.startsWith('/') ? path : `/${path}`
  return `${base}${p}`
}

/** 与后端 file_service.UPLOAD_URL_PREFIX 对应的公开路径前缀 */
const SERVER_UPLOAD_PATH_PREFIX = '/Personal-AI-Wardrobe-Assistant/uploads'

function isPlaceholderImageUrl(src) {
  if (!src || typeof src !== 'string') return true
  return src.includes('placehold.co') || src.includes('placeholder')
}

function normalizeImageRefForStorage(src) {
  const s = String(src).trim()
  const base = String(API_BASE_URL || '').replace(/\/$/, '')
  if (base && s.startsWith(base)) {
    return s.slice(base.length) || s
  }
  return s
}

function isServerStoredImageRef(src) {
  if (!src || typeof src !== 'string') return false
  const s = src.trim()
  const base = String(API_BASE_URL || '').replace(/\/$/, '')
  if (s.startsWith(`${base}${SERVER_UPLOAD_PATH_PREFIX}`)) return true
  if (s.startsWith(SERVER_UPLOAD_PATH_PREFIX)) return true
  return false
}

/**
 * 衣柜/模特图已在后端 uploads：走 JSON 由后端读文件再传 ComfyUI，避免 uni.downloadFile 失败。
 */
function requestUploadFromStorage(imageRef, imageType, token) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}/api/virtual-try-on/upload-from-storage`,
      method: 'POST',
      header: { 'content-type': 'application/json' },
      data: {
        image_ref: normalizeImageRefForStorage(imageRef),
        token,
        image_type: imageType
      },
      success: (res) => {
        try {
          resolve(parseVirtualTryUploadResponse(res, imageType))
        } catch (e) {
          reject(e instanceof Error ? e : new Error(String(e)))
        }
      },
      fail: (err) =>
        reject(new Error(`上传失败 (${imageType})：${parseUniError(err)}`))
    })
  })
}

/**
 * 与 wardrobeMedia.resolveWardrobeImageUrl 对齐：无协议、无前缀的 uploads/xxx 也视为 API 静态资源。
 */
function normalizeToDownloadUrl(s) {
  const t = String(s).trim()
  if (
    /^https?:\/\//i.test(t) ||
    t.startsWith('//') ||
    t.startsWith('data:') ||
    t.startsWith('blob:')
  ) {
    return t.startsWith('//') ? `https:${t}` : t
  }
  if (t.startsWith('/')) return joinBaseUrl(t)
  if (/^uploads\//i.test(t) || /^static\//i.test(t)) return joinBaseUrl(`/${t}`)
  return t
}

function getUserDataPath() {
  try {
    if (typeof uni !== 'undefined' && uni.env && uni.env.USER_DATA_PATH) {
      return uni.env.USER_DATA_PATH
    }
  } catch (_) {}
  try {
    if (typeof wx !== 'undefined' && wx.env && wx.env.USER_DATA_PATH) {
      return wx.env.USER_DATA_PATH
    }
  } catch (_) {}
  return ''
}

function downloadToTempFile(url) {
  const fullUrl = normalizeToDownloadUrl(url)
  if (!/^https?:\/\//i.test(fullUrl)) {
    return Promise.reject(
      new Error(`Cannot download image (invalid URL): ${String(url).slice(0, 80)}`)
    )
  }
  return new Promise((resolve, reject) => {
    uni.downloadFile({
      url: fullUrl,
      success: (res) => {
        if (res.statusCode === 200 && res.tempFilePath) {
          resolve(res.tempFilePath)
          return
        }
        let serverHint = ''
        const raw = res.data
        if (typeof raw === 'string' && raw.trim().startsWith('{')) {
          try {
            const j = JSON.parse(raw)
            serverHint = extractBackendMessage(j)
          } catch (_) {}
        }
        const code = res.statusCode
        if (serverHint) {
          reject(new Error(serverHint))
          return
        }
        if (code === 503 || code === 502 || code === 504) {
          reject(
            new Error(
              `服务暂时不可用 (HTTP ${code})。请确认后端与 ComfyUI 已启动，且 API 地址 (${API_BASE_URL}) 正确`
            )
          )
          return
        }
        reject(
          new Error(
            `无法下载图片 (HTTP ${code})。请检查图片网址、网络或 CORS；若仅 ComfyUI 未开，请先启动 ComfyUI 再试`
          )
        )
      },
      fail: (err) => {
        const base = parseUniError(err, '无法下载图片')
        reject(
          new Error(
            `${base}。若后端/ComfyUI 未启动或 API 地址错误，也会无法加载图片`
          )
        )
      }
    })
  })
}

/**
 * data URL -> 临时文件（小程序 / App 等无法直接用 blob/data 上传时）
 */
function dataUrlToTempFilePath(dataUrl) {
  const m = dataUrl.match(/^data:(.*?);base64,([\s\S]*)$/)
  if (!m) {
    return Promise.reject(new Error('Invalid data URL'))
  }
  const mime = m[1] || 'image/png'
  const b64 = m[2]
  const ext = mime.includes('png')
    ? 'png'
    : mime.includes('jpeg') || mime.includes('jpg')
      ? 'jpg'
      : 'png'

  const userPath = getUserDataPath()
  const fs = typeof uni.getFileSystemManager === 'function' ? uni.getFileSystemManager() : null

  if (fs && userPath) {
    const filePath = `${userPath}/vto_${Date.now()}_${Math.random().toString(36).slice(2, 10)}.${ext}`
    return new Promise((resolve, reject) => {
      fs.writeFile({
        filePath,
        data: b64,
        encoding: 'base64',
        success: () => resolve(filePath),
        fail: (e) => reject(new Error(parseUniError(e, 'write temp file failed')))
      })
    })
  }

  // H5：uni-h5 的 uploadFile 内部会对 data URL 走 base64ToFile，可直接传回
  return Promise.resolve(dataUrl)
}

/**
 * blob URL -> 临时文件；无文件系统时返回原 blob URL（H5 由 uni 内部 xhr 拉 blob）
 */
function blobUrlToTempFilePath(blobUrl) {
  const userPath = getUserDataPath()
  const fs = typeof uni.getFileSystemManager === 'function' ? uni.getFileSystemManager() : null

  if (typeof fetch !== 'function') {
    return Promise.resolve(blobUrl)
  }

  return fetch(blobUrl)
    .then((r) => r.blob())
    .then(
      (blob) =>
        new Promise((resolve, reject) => {
          const reader = new FileReader()
          reader.onloadend = () => {
            const dataUrl = reader.result
            if (typeof dataUrl !== 'string') {
              reject(new Error('blob read failed'))
              return
            }
            if (fs && userPath) {
              dataUrlToTempFilePath(dataUrl).then(resolve).catch(reject)
            } else {
              resolve(dataUrl)
            }
          }
          reader.onerror = () => reject(new Error('blob read failed'))
          reader.readAsDataURL(blob)
        })
    )
}

/**
 * 将任意图片引用转成 uni.uploadFile 可用的本地路径或 H5 支持的 data/blob URL。
 * 解决：http(s) 远端图、站点相对路径、上一轮试穿产生的 data:、blob: 导致 uploadFile:fail file error。
 */
function resolveLocalFilePathForUpload(src) {
  if (!src || typeof src !== 'string') {
    return Promise.reject(new Error('Invalid image source'))
  }
  const s = src.trim()
  if (isPlaceholderImageUrl(s)) {
    return Promise.reject(
      new Error('图片为占位或无效，请上传实拍图或在衣柜设置有效默认模特')
    )
  }

  if (/^https?:\/\//i.test(s)) {
    return downloadToTempFile(s)
  }
  if (s.startsWith('//')) {
    return downloadToTempFile(`https:${s}`)
  }
  // 站点相对 /uploads/... 或 uploads/...（无前缀）
  if (
    (s.startsWith('/') && !s.startsWith('//')) ||
    /^uploads\//i.test(s) ||
    /^static\//i.test(s)
  ) {
    return downloadToTempFile(s)
  }

  if (s.startsWith('data:')) {
    return dataUrlToTempFilePath(s)
  }
  if (s.startsWith('blob:')) {
    return blobUrlToTempFilePath(s)
  }

  // wxfile://、本地临时路径等
  return Promise.resolve(s)
}

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
    if (isServerStoredImageRef(filePath)) {
      requestUploadFromStorage(filePath, imageType, token).then(resolve).catch(reject)
      return
    }

    resolveLocalFilePathForUpload(filePath)
      .then((localPath) => {
        uni.uploadFile({
          url: `${API_BASE_URL}/api/virtual-try-on/upload-image`,
          filePath: localPath,
          name: 'file',
          formData: {
            image_type: imageType,
            token
          },
          success: (res) => {
            try {
              resolve(parseVirtualTryUploadResponse(res, imageType))
            } catch (e) {
              reject(e instanceof Error ? e : new Error(String(e)))
            }
          },
          fail: (err) => {
            reject(
              new Error(
                `上传失败 (${imageType})：${parseUniError(err)}。若 ComfyUI 未启动，请先启动后再试`
              )
            )
          }
        })
      })
      .catch(reject)
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
        let payload = res.data
        if (typeof payload === 'string') {
          try {
            payload = JSON.parse(payload)
          } catch {
            reject(
              new Error(
                `Generation returned non-JSON (HTTP ${res.statusCode}). Is the API URL correct?`
              )
            )
            return
          }
        }
        if (
          res.statusCode === 200 &&
          payload?.success &&
          payload?.data?.result_image
        ) {
          const nbytes = payload?.data?.image_size_bytes
          if (typeof nbytes === 'number') {
            console.log('[virtualTryOnApi] image_size_bytes', nbytes)
          }
          resolve(payload.data.result_image)
        } else {
          const backendMsg = extractBackendMessage(payload)
          reject(
            new Error(
              backendMsg ||
                `生成失败 (HTTP ${res.statusCode})`
            )
          )
        }
      },
      fail: (err) => reject(new Error(`Generation request failed: ${parseUniError(err)}`))
    })
  })
}
