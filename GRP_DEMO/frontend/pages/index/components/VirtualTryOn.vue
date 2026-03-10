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

   <view class="action-section">
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
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
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
  }
})

const personImg = ref('')
const clothingImg = ref('')
const personImgName = ref('') // 存储上传到ComfyUI的人物图片名称
const clothingImgName = ref('') // 存储上传到ComfyUI的服装图片名称

// cloth：與原本一致
watch(() => props.initialClothingImage, (url) => {
  if (url) clothingImg.value = url
}, { immediate: true })

// model/person：完全比照 cloth
watch(() => props.initialPersonImage, (url) => {
  if (url) personImg.value = url
}, { immediate: true })

onMounted(() => {
  if (props.initialClothingImage) clothingImg.value = props.initialClothingImage
  if (props.initialPersonImage) personImg.value = props.initialPersonImage
})

const resultImg = ref('') // 存储生成的结果图片
const draggingTarget = ref(null) // 用于控制拖拽时的 UI 高亮
const showResult = ref(false) // 控制结果区域的显示/隐藏
const isLoading = ref(false) // 控制加载状态
const resultZoneRef = ref(null) // 结果区域的引用

// --- 核心：Token 获取与清洗 ---
// 解决 "Not enough segments" 的关键：去除可能存在的双引号和空格
const getCleanToken = () => {
  // 1. 尝试所有常见的键名
  let t1 = uni.getStorageSync('token')
  let t2 = uni.getStorageSync('auth_token')
  let userInfo = uni.getStorageSync('user_info')

  // 2. 如果藏在 user_info 对象里面，把它挖出来
  let t3 = ''
  if (userInfo && typeof userInfo === 'object' && userInfo.token) {
    t3 = userInfo.token
  }

  // 3. 兜底：防止 uni API 抽风，直接找原生浏览器的缓存
  let t4 = ''
  let t5 = ''
  if (typeof window !== 'undefined') {
    t4 = localStorage.getItem('token') || ''
    t5 = localStorage.getItem('auth_token') || ''
  }

  // 4. 谁有值就用谁
  let rawToken = t1 || t2 || t3 || t4 || t5 || ''

  // 5. 如果不小心是个对象格式，强行转字符串
  if (typeof rawToken === 'object') {
    rawToken = rawToken.token || rawToken.access_token || ''
  }

  // 6. 剥除所有双引号和首尾空格
  return String(rawToken).trim().replace(/^"|"$/g, '')
}

// 启用滚动并滚动到底部
const enableScrollAndScrollToBottom = () => {
  if (!props.mainContentRef || !props.mainContentRef.value) {
   // 如果父组件没有传递 ref，尝试直接查找
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

// 启用滚动
const enableScroll = (element) => {
  if (element) {
   element.style.overflowY = 'auto'
  }
}

// 滚动到底部
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
  return personImg.value && clothingImg.value
})

const uploadImage = (type) => {
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

// --- 核心：修改后的上传逻辑 ---
const uploadImageToComfyUI = (filePath, type) => {
  return new Promise((resolve, reject) => {
   const token = getCleanToken() // 获取清洗后的 Token
   if (!token) {
     reject(new Error('请先登录'))
     return
   }

   uni.uploadFile({
    url: 'http://127.0.0.1:8000/api/virtual-try-on/upload-image',
    filePath: filePath,
    name: 'file', // 🚨 关键：后端 FastAPI 通常接收名为 'file' 的参数
    formData: {
     'image_type': type,
     'token': token // 必须确保 token 也传过去
    },
    success: (res) => {
     try {
      // uni.uploadFile 返回的是字符串，需要手动 JSON.parse
      const data = JSON.parse(res.data)
      console.log('Upload Result:', data)
      
      if (data.success) {
       // 💡 适配后端返回结构：如果是 data.filename 或 data.data.filename
       resolve(data.filename || data.data?.filename)
      } else {
       reject(new Error(data.message || '上传失败'))
      }
     } catch (e) {
      reject(new Error('服务器响应格式错误'))
     }
    },
    fail: (err) => {
     console.error('Upload IO Error:', err)
     reject(new Error('网络连接失败'))
    }
   })
  })
}

// --- 核心：修改后的生成逻辑 ---
const handleGenerate = async () => {
  if (!canGenerate.value) {
   return
  }

  showResult.value = true
  isLoading.value = true
  resultImg.value = ''
  enableScrollAndScrollToBottom()

  uni.showToast({ title: 'Uploading images...', icon: 'loading', duration: 2000 })

  try {
   const token = getCleanToken()

   // 1. 上传图片到后端
   if (!personImgName.value || personImg.value.includes('blob:')) {
    personImgName.value = await uploadImageToComfyUI(personImg.value, 'person')
   }

   if (!clothingImgName.value || clothingImg.value.includes('blob:')) {
    clothingImgName.value = await uploadImageToComfyUI(clothingImg.value, 'clothing')
   }

   uni.showToast({ title: 'Generating...', icon: 'loading', duration: 4000 })

uni.request({
    url: 'http://127.0.0.1:8000/api/virtual-try-on/generate',
    method: 'POST',
    header: { 'content-type': 'application/json' }, // 改回默认的 JSON 格式
    data: {
     person_image: personImgName.value,
     clothing_image: clothingImgName.value,
     token: token,
     model_type: '2509'
    },
    // 🚨 注意：这里删除了 responseType: 'arraybuffer'
    success: (res) => {
     console.log('API Response:', res.data) // 在控制台打印后端到底回了什么
     isLoading.value = false

     // 按照你的后端原始格式进行解析
     if (res.statusCode === 200 && res.data && res.data.success) {
      // 成功获取到图片的 URL 或 Base64
      resultImg.value = res.data.data.result_image
      uni.showToast({ title: 'Generation completed!', icon: 'success' })
     } else {
      uni.showToast({ title: res.data?.message || 'Generation failed', icon: 'none' })
     }
    },
    fail: (err) => {
     console.error('API Error:', err)
     isLoading.value = false
     uni.showToast({ title: 'Network error', icon: 'none' })
    }
   })

  } catch (error) {
   console.error('Process Error:', error)
   isLoading.value = false
   uni.showToast({ title: error.message || 'Process failed', icon: 'none' })
  }
}
</script>

<style scoped>
/* 保持原有布局样式 */
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

.action-section {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 10rpx 0;
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