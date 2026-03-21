<template>
  <view class="virtual-tryon-container">
   <view class="upload-section">
    <view class="upload-item">
     <text class="upload-title">Person Model</text>

     <div
      class="upload-zone"
      :class="{ 'dragging': draggingTarget === 'person' }"
      v-if="!personImg"
      @click="uploadImage('person')"
      @drop.prevent="handleDrop($event, 'person')"
      @dragover.prevent="handleDragOver($event, 'person')"
      @dragleave.prevent="handleDragLeave($event, 'person')"
      @dragenter.prevent
     >
      <view class="upload-icon">
       <image src="/static/icons/icon-image-upload.svg" mode="aspectFit" class="icon-upload-img"></image>
      </view>
      <view class="upload-text">
       <text class="upload-link">Click to upload</text>
       <text class="upload-hint">or drag and drop</text>
      </view>
      <text class="upload-format">JPG, PNG vertical preferred</text>
     </div>

     <view class="preview-box" v-else>
      <image :src="personImg" mode="aspectFill" class="blur-bg"></image>
      <view class="overlay-dim"></view>
      <image :src="personImg" mode="aspectFit" class="main-img"></image>
      <view class="remove-btn" @click.stop="removeImage('person')">
       <image src="/static/icons/icon-close.svg" mode="aspectFit" class="icon-close-img"></image>
      </view>
     </view>
    </view>

    <view class="upload-item">
     <text class="upload-title">Try-On Clothing</text>

     <div
      class="upload-zone"
      :class="{ 'dragging': draggingTarget === 'clothing' }"
      v-if="!clothingImg"
      @click="uploadImage('clothing')"
      @drop.prevent="handleDrop($event, 'clothing')"
      @dragover.prevent="handleDragOver($event, 'clothing')"
      @dragleave.prevent="handleDragLeave($event, 'clothing')"
      @dragenter.prevent
     >
      <view class="upload-icon">
       <image src="/static/icons/icon-image-upload.svg" mode="aspectFit" class="icon-upload-img"></image>
      </view>
      <view class="upload-text">
       <text class="upload-link">Click to upload</text>
       <text class="upload-hint">or drag and drop</text>
      </view>
      <text class="upload-format">JPG, PNG flat lay preferred</text>
     </div>

     <view class="preview-box" v-else>
      <image :src="clothingImg" mode="aspectFill" class="blur-bg"></image>
      <view class="overlay-dim"></view>
      <image :src="clothingImg" mode="aspectFit" class="main-img"></image>
      <view class="remove-btn" @click.stop="removeImage('clothing')">
       <image src="/static/icons/icon-close.svg" mode="aspectFit" class="icon-close-img"></image>
      </view>
     </view>
    </view>
   </view>

   <view v-if="parsedOutfitQueue.length > 0" class="outfit-order-panel">
    <text class="outfit-order-title">Try-on order</text>
    <text class="outfit-order-sub">Garments are applied one at a time; each result becomes the model for the next step.</text>
    <view class="outfit-order-list">
     <view
      v-for="(step, si) in parsedOutfitQueue"
      :key="si"
      class="outfit-order-row"
      :class="{
       'is-done': outfitStepState(si).done,
       'is-current': outfitStepState(si).current,
       'is-pending': outfitStepState(si).pending
      }"
     >
      <text class="outfit-order-idx">{{ si + 1 }}</text>
      <view class="outfit-order-thumb-wrap">
       <image
        v-if="step.image"
        :src="step.image"
        mode="aspectFill"
        class="outfit-order-thumb"
       />
       <view v-else class="outfit-order-thumb outfit-order-thumb--empty">
        <text class="outfit-order-thumb-ph">—</text>
       </view>
      </view>
      <view class="outfit-order-main">
       <text class="outfit-order-label">{{ step.label }}</text>
       <text v-if="outfitStepState(si).current" class="outfit-order-badge">In progress</text>
      </view>
      <text v-if="outfitStepState(si).done" class="outfit-order-check">✓</text>
      <text v-else-if="outfitStepState(si).pending" class="outfit-order-pending">···</text>
     </view>
    </view>
   </view>

   <view class="action-section">
    <view v-if="outfitProgressText" class="pipeline-hint">
     <text class="pipeline-hint-text">{{ outfitProgressText }}</text>
    </view>
    <button
     class="generate-btn"
     :disabled="!canGenerate"
     :class="{'active': canGenerate}"
     @click="handleGenerate"
    >
     <span class="sparkle-icon" v-if="canGenerate">✨</span>
     Generate
    </button>
   </view>

   <view class="preview-section" :class="{ 'expanded': showResult }">
    <view class="section-header">
     <text class="preview-title">Generation Result</text>
    </view>

    <view class="preview-zone result-zone" :class="{ 'loading': isLoading }" ref="resultZoneRef">
     <view class="shimmer-overlay" v-if="isLoading">
      <view class="shimmer"></view>
     </view>

     <view class="preview-icon" v-if="isLoading">
      <image src="/static/icons/icon-image-upload.svg" mode="aspectFit" class="icon-result-placeholder"></image>
     </view>

     <view v-else class="result-content">
      <image v-if="resultImg" :src="resultImg" mode="aspectFit" class="result-image"></image>
      <view v-else class="preview-icon">
       <image src="/static/icons/icon-image-upload.svg" mode="aspectFit" class="icon-result-placeholder"></image>
      </view>
     </view>
    </view>
   </view>
  </view>
</template>

<script setup>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import {
  getCleanAuthToken,
  uploadVirtualTryOnImage,
  generateVirtualTryOn
} from '@/api/virtualTryOnApi.js'

const props = defineProps({
  isLoggedIn: { type: Boolean, default: false },
  mainContentRef: {
   type: Object,
   default: null
  },
  initialClothingImage: {
   type: String,
   default: null
  },
  initialPersonImage: {
   type: String,
   default: null
  },
  /** Multi-step outfit: each result becomes the next person image; backend still one pair per request */
  initialOutfitQueue: {
   type: Array,
   default: () => []
  }
})

function requireLogin() {
  if (!props.isLoggedIn) {
    uni.showToast({ title: 'Please log in first', icon: 'none' })
    return true
  }
  return false
}

const personImg = ref('')
const clothingImg = ref('')
const personImgName = ref('')
const clothingImgName = ref('')

watch(() => props.initialClothingImage, (url) => {
  if (url) clothingImg.value = url
}, { immediate: true })

watch(() => props.initialPersonImage, (url) => {
  if (url) personImg.value = url
}, { immediate: true })

const resultImg = ref('')
const draggingTarget = ref(null)
const showResult = ref(false)
const isLoading = ref(false)
const resultZoneRef = ref(null)
const outfitProgressText = ref('')
const isPipelineRunning = ref(false)
/** -1 = idle; 0..n-1 = current step; n = all steps finished (show all ✓) */
const outfitPipelineStepIndex = ref(-1)

function parseOutfitQueueProp(raw) {
  if (!Array.isArray(raw) || raw.length === 0) return []
  return raw
   .map((e, i) => {
    if (typeof e === 'string') {
     return { image: e, label: `Garment ${i + 1}` }
    }
    const image = e?.image || e?.url || ''
    const label = String(e?.label || '').trim() || `Step ${i + 1}`
    return image ? { image, label } : null
   })
   .filter(Boolean)
}

const parsedOutfitQueue = computed(() => parseOutfitQueueProp(props.initialOutfitQueue))

function outfitStepState(si) {
  const n = parsedOutfitQueue.value.length
  const idx = outfitPipelineStepIndex.value
  if (n === 0) return { done: false, current: false, pending: true }
  if (idx < 0) return { done: false, current: false, pending: true }
  if (idx >= n) return { done: true, current: false, pending: false }
  if (si < idx) return { done: true, current: false, pending: false }
  if (si === idx && isPipelineRunning.value) return { done: false, current: true, pending: false }
  return { done: false, current: false, pending: true }
}

watch(
  () => props.initialOutfitQueue,
  () => {
   if (parseOutfitQueueProp(props.initialOutfitQueue).length === 0) {
    outfitPipelineStepIndex.value = -1
   }
  },
  { deep: true }
)

// Scroll parent panel and snap to bottom after generation
const enableScrollAndScrollToBottom = () => {
  if (!props.mainContentRef || !props.mainContentRef.value) {
   // Fallback when parent ref is missing (H5)
   const mainContent = document.querySelector('.main-content')
   if (mainContent) {
    enableScroll(mainContent)
    scrollToBottom(mainContent)
   }
   return
  }

  const mainContent = props.mainContentRef.value
  enableScroll(mainContent)
  scrollToBottom(mainContent)
}

const enableScroll = (element) => {
  if (element) {
   element.style.overflowY = 'auto'
  }
}

const scrollToBottom = (element) => {
  setTimeout(() => {
   if (element) {
    const scrollHeight = element.scrollHeight || 0
    const clientHeight = element.clientHeight || 0
    const scrollTop = scrollHeight - clientHeight

    const scrollDuration = 500
    const scrollSteps = 30
    const stepInterval = scrollDuration / scrollSteps

    if (element.scrollTo) {
     element.scrollTo({
      top: scrollTop,
      behavior: 'smooth'
     })
    } else {
     let currentScroll = element.scrollTop || 0
     const step = (scrollTop - currentScroll) / scrollSteps
     const timer = setInterval(() => {
      currentScroll += step
      if ((step > 0 && currentScroll >= scrollTop) || (step < 0 && currentScroll <= scrollTop)) {
       element.scrollTop = scrollTop
       clearInterval(timer)
      } else {
       element.scrollTop = currentScroll
      }
     }, stepInterval)
    }
   }
  }, 200)
}

const canGenerate = computed(() => {
  return !!(personImg.value && clothingImg.value && !isPipelineRunning.value)
})

const uploadImage = (type) => {
  if (requireLogin()) return
  uni.chooseImage({
   count: 1,
   sizeType: ['original', 'compressed'],
   sourceType: ['album', 'camera'],
   success: (res) => {
    const tempFilePath = res.tempFilePaths[0]
    if (type === 'person') {
     personImg.value = tempFilePath
    } else {
     clothingImg.value = tempFilePath
    }
   }
  })
}

const handleDragOver = (event, type) => {
  draggingTarget.value = type
}

const handleDragLeave = (event, type) => {
  if (draggingTarget.value === type) {
   draggingTarget.value = null
  }
}

const handleDrop = (event, type) => {
  if (requireLogin()) return
  draggingTarget.value = null
  const files = event.dataTransfer?.files || event.originalEvent?.dataTransfer?.files

  if (files && files.length > 0) {
   const file = files[0]
   if (file.type && file.type.startsWith('image/')) {
    const url = URL.createObjectURL(file)
    if (type === 'person') {
     personImg.value = url
    } else {
     clothingImg.value = url
    }
   } else {
    uni.showToast({ title: 'Please drop an image file', icon: 'none' })
   }
  }
}

const removeImage = (type) => {
  if (type === 'person') {
   personImg.value = ''
   personImgName.value = ''
  } else {
   clothingImg.value = ''
   clothingImgName.value = ''
  }
  if (!personImg.value && !clothingImg.value) {
   showResult.value = false
   isLoading.value = false
   resultImg.value = ''
  }
}

function dataUrlToBlobUrl(dataUrl) {
  if (!dataUrl || typeof dataUrl !== 'string' || !dataUrl.startsWith('data:')) {
   throw new Error('Invalid data URL')
  }
  const comma = dataUrl.indexOf(',')
  const header = dataUrl.slice(0, comma)
  const b64 = dataUrl.slice(comma + 1)
  const mimeMatch = header.match(/data:(.*?);/)
  const mime = mimeMatch ? mimeMatch[1] : 'image/png'
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  const blob = new Blob([bytes], { type: mime })
  return URL.createObjectURL(blob)
}

function ensureUploadablePath(src, revokeList) {
  if (!src) throw new Error('Missing image')
  if (typeof src === 'string' && src.startsWith('data:')) {
   const u = dataUrlToBlobUrl(src)
   if (Array.isArray(revokeList)) revokeList.push(u)
   return u
  }
  return src
}

async function runOutfitPipeline() {
  const q = parsedOutfitQueue.value
  if (!q.length) return
  if (isPipelineRunning.value) return
  if (!props.isLoggedIn) return

  isPipelineRunning.value = true
  outfitProgressText.value = ''
  outfitPipelineStepIndex.value = 0
  enableScrollAndScrollToBottom()

  const token = getCleanAuthToken()
  if (!token) {
   uni.showToast({ title: 'Please log in first', icon: 'none' })
   isPipelineRunning.value = false
   outfitPipelineStepIndex.value = -1
   return
  }

  let personSrc = props.initialPersonImage || personImg.value
  if (!personSrc) {
   uni.showToast({ title: 'Set a default model in My Wardrobe or upload a person photo', icon: 'none' })
   isPipelineRunning.value = false
   outfitPipelineStepIndex.value = -1
   return
  }

  showResult.value = true
  isLoading.value = true
  resultImg.value = ''

  const blobUrlsToRevoke = []

  try {
   for (let i = 0; i < q.length; i++) {
    outfitPipelineStepIndex.value = i
    const step = q[i]
    outfitProgressText.value = `Step ${i + 1} of ${q.length}: ${step.label}`

    const clothSrc = step.image
    if (!clothSrc) continue

    personImg.value = personSrc
    clothingImg.value = clothSrc
    personImgName.value = ''
    clothingImgName.value = ''

    await nextTick()

    const personPath = ensureUploadablePath(personSrc, blobUrlsToRevoke)
    const clothPath = ensureUploadablePath(clothSrc, blobUrlsToRevoke)

    const personName = await uploadVirtualTryOnImage(personPath, 'person')
    const clothName = await uploadVirtualTryOnImage(clothPath, 'clothing')

    const resultDataUrl = await generateVirtualTryOn({
     person_image: personName,
     clothing_image: clothName,
     token,
     model_type: '2509'
    })

    resultImg.value = resultDataUrl
    personSrc = resultDataUrl
   }

   personImg.value = personSrc
   clothingImg.value = ''
   personImgName.value = ''
   clothingImgName.value = ''

   outfitPipelineStepIndex.value = q.length
   uni.showToast({ title: 'Full outfit complete!', icon: 'success' })
  } catch (e) {
   console.error('[VirtualTryOn] outfit pipeline', e)
   uni.showToast({ title: e?.message || 'Outfit try-on failed', icon: 'none' })
   outfitPipelineStepIndex.value = -1
  } finally {
   blobUrlsToRevoke.forEach((u) => {
    try { URL.revokeObjectURL(u) } catch (_) {}
   })
   isLoading.value = false
   outfitProgressText.value = ''
   isPipelineRunning.value = false
  }
}

watch(
  () => [props.initialOutfitQueue, props.initialPersonImage, props.isLoggedIn],
  () => {
   if (parsedOutfitQueue.value.length === 0) return
   if (!props.isLoggedIn) return
   nextTick(() => runOutfitPipeline())
  },
  { immediate: true, deep: true }
)

onBeforeUnmount(() => {
  outfitProgressText.value = ''
  isPipelineRunning.value = false
  outfitPipelineStepIndex.value = -1
})

const handleGenerate = async () => {
  if (requireLogin()) return
  if (isPipelineRunning.value) return
  if (!canGenerate.value) {
   return
  }

  showResult.value = true
  isLoading.value = true
  resultImg.value = ''
  enableScrollAndScrollToBottom()

  uni.showToast({ title: 'Uploading images...', icon: 'loading', duration: 2000 })

  try {
   const token = getCleanAuthToken()
   if (!token) {
    uni.showToast({ title: 'Please log in first', icon: 'none' })
    return
   }

   if (!personImgName.value || personImg.value.includes('blob:')) {
    personImgName.value = await uploadVirtualTryOnImage(personImg.value, 'person')
   }

   if (!clothingImgName.value || clothingImg.value.includes('blob:')) {
    clothingImgName.value = await uploadVirtualTryOnImage(clothingImg.value, 'clothing')
   }

   uni.showToast({ title: 'Generating...', icon: 'loading', duration: 4000 })

   const resultDataUrl = await generateVirtualTryOn({
    person_image: personImgName.value,
    clothing_image: clothingImgName.value,
    token,
    model_type: '2509'
   })

   resultImg.value = resultDataUrl
   uni.showToast({ title: 'Generation completed!', icon: 'success' })
  } catch (error) {
   console.error('Process Error:', error)
   uni.showToast({ title: error?.message || 'Process failed', icon: 'none' })
  } finally {
   isLoading.value = false
  }
}
</script>

<style scoped>
.virtual-tryon-container {
  width: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  padding: 100rpx 100rpx 50rpx 100rpx;
  gap: 100rpx;
  box-sizing: border-box;
}

.upload-section {
  display: flex;
  gap: 90rpx;
  width: 100%;
}

.upload-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  position: relative;
  isolation: isolate;
}

.upload-item::before {
  content: "01";
  position: absolute;
  top: -100rpx;
  left: -64rpx;
  font-size: 200rpx;
  font-family: 'Didot', serif;
  color: rgba(0,0,0,0.03);
  z-index: -1;
  pointer-events: none;
  line-height: 1;
  white-space: nowrap;
}

.upload-item:nth-child(2)::before {
  content: "02";
}

.upload-title, .preview-title {
  font-size: 34rpx;
  font-weight: 500;
  color: #1D1D1F;
  font-family: "Didot", serif;
}

.upload-zone {
  border: 2rpx dashed #D1D1D1;
  border-radius: 20rpx;
  padding: 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: #FFFFFF;
  width: 100%;
  height: 1400rpx;
  box-sizing: border-box;
}

.upload-zone:hover {
  border-color: #8C7B60;
  background-color: #FDFBF7;
}

.upload-zone.dragging {
  border-color: #007AFF;
  background-color: #F0F8FF;
  transform: scale(0.99);
}

.upload-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  pointer-events: none;
}

.upload-icon {
  pointer-events: none;
}

.icon-upload-img {
  width: 48px;
  height: 48px;
  display: block;
}
.icon-close-img {
  width: 16px;
  height: 16px;
  display: block;
}
.icon-result-placeholder {
  width: 80px;
  height: 80px;
  display: block;
}

.upload-link {
  font-size: 28rpx;
  color: #007AFF;
  font-weight: 500;
}

.upload-hint, .upload-format {
  font-size: 24rpx;
  color: #999;
}

.preview-box {
  position: relative;
  width: 100%;
  height: 1400rpx;
  border-radius: 20rpx;
  overflow: hidden;
  background-color: #F5F5F7;
  border: 2rpx solid rgba(0,0,0,0.05);
}

.blur-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  filter: blur(20px);
  transform: scale(1.1);
  opacity: 0.6;
}

.overlay-dim {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
}

.main-img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.remove-btn {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  width: 48rpx;
  height: 48rpx;
  background-color: rgba(0,0,0,0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10;
  transition: background 0.2s;
}
.remove-btn:hover {
  background-color: rgba(0,0,0,0.8);
}

.outfit-order-panel {
  width: 100%;
  max-width: 100%;
  padding: 32rpx 40rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(157, 139, 112, 0.2);
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.04);
  box-sizing: border-box;
}

.outfit-order-title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: #1D1D1F;
  font-family: "Didot", serif;
  margin-bottom: 12rpx;
}

.outfit-order-sub {
  display: block;
  font-size: 24rpx;
  color: #6B6B6B;
  line-height: 1.5;
  margin-bottom: 28rpx;
}

.outfit-order-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.outfit-order-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  border-radius: 16rpx;
  border: 1px solid rgba(0, 0, 0, 0.06);
  background: #FAFAF8;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.outfit-order-row.is-pending {
  opacity: 0.65;
}

.outfit-order-row.is-current {
  background: rgba(157, 139, 112, 0.12);
  border-color: rgba(157, 139, 112, 0.45);
  opacity: 1;
}

.outfit-order-row.is-done {
  background: rgba(76, 175, 80, 0.06);
  border-color: rgba(76, 175, 80, 0.25);
  opacity: 1;
}

.outfit-order-idx {
  flex-shrink: 0;
  width: 48rpx;
  height: 48rpx;
  line-height: 48rpx;
  text-align: center;
  font-size: 24rpx;
  font-weight: 700;
  color: #5a4b35;
  background: rgba(157, 139, 112, 0.15);
  border-radius: 50%;
}

.outfit-order-thumb-wrap {
  flex-shrink: 0;
  width: 112rpx;
  height: 112rpx;
  border-radius: 16rpx;
  overflow: hidden;
  background: #F0EEEA;
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.outfit-order-thumb {
  width: 112rpx;
  height: 112rpx;
  display: block;
}

.outfit-order-thumb--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.outfit-order-thumb-ph {
  font-size: 28rpx;
  color: #C4C4C4;
}

.outfit-order-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.outfit-order-label {
  font-size: 26rpx;
  font-weight: 600;
  color: #2C2C2E;
  line-height: 1.4;
  word-break: break-word;
}

.outfit-order-badge {
  font-size: 22rpx;
  font-weight: 600;
  color: #9D8B70;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.outfit-order-check {
  flex-shrink: 0;
  font-size: 32rpx;
  color: #2e7d32;
  font-weight: 700;
  width: 40rpx;
  text-align: center;
}

.outfit-order-pending {
  flex-shrink: 0;
  font-size: 24rpx;
  color: #C4C4C4;
  width: 40rpx;
  text-align: center;
  letter-spacing: 2rpx;
}

.action-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24rpx;
  padding: 10rpx 0;
}

.pipeline-hint {
  width: 100%;
  max-width: 720rpx;
  text-align: center;
  padding: 16rpx 24rpx;
  border-radius: 16rpx;
  background: rgba(157, 139, 112, 0.12);
  border: 1px solid rgba(157, 139, 112, 0.25);
}

.pipeline-hint-text {
  font-size: 28rpx;
  color: #5a4b35;
  font-weight: 600;
}

.generate-btn {
  background-color: #E5E5EA;
  color: #999;
  border: none;
  width: 300rpx;
  height: 88rpx;
  border-radius: 44rpx;
  font-size: 36rpx;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  gap: 12rpx;
  cursor: not-allowed;
  opacity: 0.6;
}

.generate-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.generate-btn.active {
  background-color: #9D8B70;
  color: #FFF;
  cursor: pointer;
  box-shadow: 0 8rpx 20rpx rgba(157, 139, 112, 0.3);
  transform: scale(1.02);
  opacity: 1;
}

.generate-btn.active:hover {
  background-color: #8C7B60;
  transform: scale(1.05);
  box-shadow: 0 10rpx 24rpx rgba(157, 139, 112, 0.4);
}

.generate-btn.active:active {
  transform: scale(0.98);
}

.sparkle-icon {
  font-size: 32rpx;
}

.preview-section {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  width: 100%;
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition: max-height 0.6s cubic-bezier(0.4, 0, 0.2, 1),
              opacity 0.5s ease 0.1s,
              margin-top 0.5s ease;
  margin-top: 0;
}

.preview-section.expanded {
  max-height: none;
  opacity: 1;
  margin-top: 20rpx;
}

.section-header {
  margin-bottom: 20rpx;
  opacity: 0;
  transform: translateY(-10rpx);
  transition: opacity 0.4s ease 0.2s, transform 0.4s ease 0.2s;
}

.preview-section.expanded .section-header {
  opacity: 1;
  transform: translateY(0);
}

.result-zone {
  width: 55%;
  min-height: 1650rpx;
  margin: 0 auto;
  border: 2rpx solid #E5E5EA;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #FFF;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02);
  opacity: 0;
  transform: translateY(20rpx);
  transition: opacity 0.5s ease 0.3s, transform 0.5s ease 0.3s;
  position: relative;
  overflow: hidden;
}

.preview-section.expanded .result-zone {
  opacity: 1;
  transform: translateY(0);
}

.result-zone.loading {
  background: linear-gradient(135deg, #F5F5F7 0%, #FAFAFA 25%, #F5F5F7 50%, #FAFAFA 75%, #F5F5F7 100%);
  background-size: 400% 400%;
  animation: background-shift 3s ease-in-out infinite;
}

@keyframes background-shift {
  0%, 100% {
   background-position: 0% 50%;
  }
  50% {
   background-position: 100% 50%;
  }
}

.shimmer-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
  z-index: 1;
}

.shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(
   90deg,
   transparent 0%,
   rgba(157, 139, 112, 0.1) 20%,
   rgba(255, 255, 255, 0.5) 50%,
   rgba(157, 139, 112, 0.1) 80%,
   transparent 100%
  );
  animation: shimmer-sweep 2.5s ease-in-out infinite;
  transform: skewX(-25deg);
  filter: blur(20rpx);
}

@keyframes shimmer-sweep {
  0% {
   left: -100%;
   opacity: 0;
  }
  10% {
   opacity: 1;
  }
  90% {
   opacity: 1;
  }
  100% {
   left: 150%;
   opacity: 0;
  }
}

.result-zone.loading .preview-icon {
  opacity: 0.5;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
   opacity: 0.5;
   transform: scale(1);
  }
  50% {
   opacity: 0.8;
   transform: scale(1.05);
  }
}

.result-content {
  width: 100%;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx;
  box-sizing: border-box;
}

.result-image {
  width: 100%;
  max-width: 100%;
  height: auto;
  max-height: none;
  object-fit: contain;
  display: block;
}
</style>