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

/** Extract error message from FastAPI / project JSON payload. */
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
 * Parse JSON response for upload / upload-from-storage.
 * Returns ComfyUI filename on success.
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
          `Upload failed: service unavailable (HTTP ${code}). Please ensure ComfyUI is running and COMFYUI_SERVER is correct`
        )
      }
      throw new Error(`Invalid upload response (${imageType}): HTTP ${res.statusCode}`)
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
  throw new Error(`Upload failed (${imageType}): HTTP ${res.statusCode || 'unknown'}`)
}

function joinBaseUrl(path) {
  const base = String(API_BASE_URL || '').replace(/\/$/, '')
  const p = path.startsWith('/') ? path : `/${path}`
  return `${base}${p}`
}

/** Public path prefix aligned with backend file_service.UPLOAD_URL_PREFIX. */
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
 * Wardrobe/model image already stored in backend uploads:
 * call JSON endpoint so backend reads file and forwards to ComfyUI,
 * avoiding uni.downloadFile failures.
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
        reject(new Error(`Upload failed (${imageType}): ${parseUniError(err)}`))
    })
  })
}

/**
 * Keep behavior aligned with wardrobeMedia.resolveWardrobeImageUrl:
 * treat uploads/xxx without scheme/prefix as API static resources.
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
              `Service temporarily unavailable (HTTP ${code}). Please ensure backend and ComfyUI are running, and API URL (${API_BASE_URL}) is correct`
            )
          )
          return
        }
        reject(
          new Error(
            `Unable to download image (HTTP ${code}). Check image URL, network, or CORS; if ComfyUI is not running, start it and try again`
          )
        )
      },
      fail: (err) => {
        const base = parseUniError(err, 'Unable to download image')
        reject(
          new Error(
            `${base}. This can also happen if backend/ComfyUI is not running or the API URL is incorrect`
          )
        )
      }
    })
  })
}

/**
 * data URL -> temp file (for runtimes where blob/data cannot be uploaded directly).
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

  // H5: uni-h5 uploadFile internally converts data URL via base64ToFile; safe to return directly.
  return Promise.resolve(dataUrl)
}

/**
 * blob URL -> temp file; if no file system is available, return original blob URL
 * (H5 uses uni internal xhr to fetch blob).
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
 * Convert any image reference into a local path for uni.uploadFile,
 * or H5-compatible data/blob URL.
 * Handles http(s), site-relative paths, and data:/blob: values from previous try-on results.
 */
function resolveLocalFilePathForUpload(src) {
  if (!src || typeof src !== 'string') {
    return Promise.reject(new Error('Invalid image source'))
  }
  const s = src.trim()
  if (isPlaceholderImageUrl(s)) {
    return Promise.reject(
      new Error('Image is a placeholder or invalid. Please upload a real photo or set a valid default model in My Wardrobe')
    )
  }

  if (/^https?:\/\//i.test(s)) {
    return downloadToTempFile(s)
  }
  if (s.startsWith('//')) {
    return downloadToTempFile(`https:${s}`)
  }
  // Site-relative /uploads/... or uploads/... (no prefix).
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

  // wxfile:// and other local temp paths.
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
                `Upload failed (${imageType}): ${parseUniError(err)}. If ComfyUI is not running, start it and try again`
              )
            )
          }
        })
      })
      .catch(reject)
  })
}

function isPngMagic(u8) {
  return (
    u8 &&
    u8.length >= 8 &&
    u8[0] === 0x89 &&
    u8[1] === 0x50 &&
    u8[2] === 0x4e &&
    u8[3] === 0x47 &&
    u8[4] === 0x0d &&
    u8[5] === 0x0a &&
    u8[6] === 0x1a &&
    u8[7] === 0x0a
  )
}

/** Avoid String.fromCharCode.apply stack overflow on large images; prefer uni API. */
function arrayBufferToBase64DataUrl(ab) {
  if (typeof uni.arrayBufferToBase64 === 'function') {
    return `data:image/png;base64,${uni.arrayBufferToBase64(ab)}`
  }
  const u8 = new Uint8Array(ab)
  let binary = ''
  const chunk = 0x8000
  for (let i = 0; i < u8.length; i += chunk) {
    binary += String.fromCharCode.apply(null, u8.subarray(i, i + chunk))
  }
  return `data:image/png;base64,${btoa(binary)}`
}

/**
 * Aligned with frontend_yuchen: backend returns raw PNG on success, JSON on error.
 * Also compatible with legacy backend (JSON contains data.result_image base64).
 *
 * @param {{ person_image: string, clothing_image: string, token: string, model_type?: string }} body
 * @returns {Promise<string>} result_image (data URL)
 */
export function generateVirtualTryOn(body) {
  const { person_image, clothing_image, token, model_type = '2509' } = body
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}/api/virtual-try-on/generate`,
      method: 'POST',
      header: { 'content-type': 'application/json' },
      responseType: 'arraybuffer',
      data: {
        person_image,
        clothing_image,
        token,
        model_type
      },
      success: (res) => {
        const code = res.statusCode
        const raw = res.data
        if (raw == null) {
          reject(new Error('Generation returned empty body'))
          return
        }

        let ab
        if (raw instanceof ArrayBuffer) {
          ab = raw
        } else if (ArrayBuffer.isView(raw)) {
          ab = raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength)
        } else {
          reject(new Error('Unexpected response body type from generate API'))
          return
        }
        if (!ab || ab.byteLength === 0) {
          reject(new Error('Generation returned empty body'))
          return
        }

        const u8 = new Uint8Array(ab)

        if (code === 200 && isPngMagic(u8)) {
          console.log('[virtualTryOnApi] PNG bytes', u8.byteLength)
          resolve(arrayBufferToBase64DataUrl(ab))
          return
        }

        let text
        try {
          text = new TextDecoder('utf-8').decode(u8)
        } catch (e) {
          reject(new Error('Unable to decode server response'))
          return
        }

        let payload
        try {
          payload = JSON.parse(text)
        } catch {
          reject(
            new Error(
              `Generation returned non-JSON (HTTP ${code}). Is the API URL correct?`
            )
          )
          return
        }

        if (code === 200 && payload?.success && payload?.data?.result_image) {
          const nbytes = payload?.data?.image_size_bytes
          if (typeof nbytes === 'number') {
            console.log('[virtualTryOnApi] image_size_bytes', nbytes)
          }
          resolve(payload.data.result_image)
          return
        }

        const backendMsg = extractBackendMessage(payload)
        reject(
          new Error(backendMsg || `Generation failed (HTTP ${code})`)
        )
      },
      fail: (err) => reject(new Error(`Generation request failed: ${parseUniError(err)}`))
    })
  })
}
