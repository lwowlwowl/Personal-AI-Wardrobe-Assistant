/**
 * Wardrobe image URL helpers + H5 probe (used by WardrobeView).
 * Keeps DOM/Image logic out of the Vue file; imported from wardrobe-centric API layer.
 */

import { API_BASE_URL } from '@/utils/request.js'

const PLACEHOLDER =
  'https://placehold.co/400x500/f5f0e6/8c7b60?text=No+Image'

/**
 * Placeholder image for list display (do not use for flows that upload to ComfyUI).
 */
export function isPlaceholderWardrobeUrl(imageUrl) {
  if (imageUrl == null || imageUrl === '') return true
  const s = String(imageUrl)
  return s.includes('placehold.co') || s.includes('placeholder')
}

/**
 * Normalize image path from API into full URL (relative path -> absolute URL based on base).
 */
export function resolveWardrobeImageUrl(imageUrl, baseUrl = API_BASE_URL) {
  if (imageUrl == null || imageUrl === '') return PLACEHOLDER
  const s = String(imageUrl)
  if (
    s.startsWith('http://') ||
    s.startsWith('https://') ||
    s.startsWith('data:') ||
    s.startsWith('blob:')
  ) {
    return s
  }
  const base = String(baseUrl || '').replace(/\/$/, '')
  if (s.startsWith('/')) return `${base}${s}`
  return `${base}/${s}`
}

export function isApiResourceNotFoundText(text) {
  const t = String(text || '')
  const lower = t.toLowerCase()
  return (
    t.includes('不存在') ||
    lower.includes('not found') ||
    lower.includes('does not exist') ||
    lower.includes("doesn't exist")
  )
}

/** Delete response already returned 404 or body says resource missing (zh/en). */
export function isClothingDeleteNotFoundResponse(response, error) {
  if (response) {
    if (response.statusCode === 404) return true
    const d = response.data
    if (d && (isApiResourceNotFoundText(d.detail) || isApiResourceNotFoundText(d.message))) {
      return true
    }
  }
  if (error) {
    if (error.statusCode === 404) return true
    const errMsg = String(error?.message || error?.errMsg || error?.detail || '')
    if (isApiResourceNotFoundText(errMsg)) return true
  }
  return false
}

function pushUnique(arr, u) {
  if (u && !arr.includes(u)) arr.push(u)
}

export function buildClothingImageProbeCandidates(item, baseUrl = API_BASE_URL) {
  const candidates = []
  pushUnique(candidates, item.image)
  if (item.image && item.image.startsWith('/')) {
    pushUnique(candidates, `${baseUrl}${item.image}`)
  }
  if (item._rawImageUrl && item._rawImageUrl !== item.image) {
    pushUnique(candidates, item._rawImageUrl)
    if (item._rawImageUrl.startsWith('/')) {
      pushUnique(candidates, `${baseUrl}${item._rawImageUrl}`)
    }
  }
  if (item.image) {
    if (item.image.includes('?')) {
      pushUnique(candidates, `${item.image.split('?')[0]}?t=${Date.now()}`)
    } else {
      pushUnique(candidates, `${item.image}?t=${Date.now()}`)
    }
  }
  return candidates
}

/** H5: return whether image URL loads (best-effort; non-H5 may skip probe). */
export function probeImageUrlAsync(url, timeoutMs = 5000) {
  if (typeof Image === 'undefined') return Promise.resolve(true)
  return new Promise((resolve) => {
    const img = new Image()
    const timeout = setTimeout(() => {
      img.onload = img.onerror = null
      resolve(false)
    }, timeoutMs)
    img.onload = () => {
      clearTimeout(timeout)
      resolve(true)
    }
    img.onerror = () => {
      clearTimeout(timeout)
      resolve(false)
    }
    img.src = url
  })
}

export async function pickWorkingClothingImageUrl(item, baseUrl = API_BASE_URL) {
  const candidates = buildClothingImageProbeCandidates(item, baseUrl)
  for (const candidate of candidates) {
    if (await probeImageUrlAsync(candidate)) return candidate
  }
  return item.image
}

export async function applyClothingImageUrlFixes(items, baseUrl = API_BASE_URL) {
  const fixedItems = []
  for (const item of items) {
    const fixedItem = { ...item }
    if (item._needsFix || (item.image && item.image.startsWith('/'))) {
      const fixedUrl = await pickWorkingClothingImageUrl(item, baseUrl)
      if (fixedUrl !== item.image) {
        fixedItem.image = fixedUrl
        fixedItem._wasFixed = true
        fixedItem._originalImage = item.image
      }
    }
    fixedItems.push(fixedItem)
  }
  return fixedItems
}
