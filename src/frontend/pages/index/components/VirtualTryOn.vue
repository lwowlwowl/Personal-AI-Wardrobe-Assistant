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
				<!-- Shimmer 加载动画覆盖层 -->
				<view class="shimmer-overlay" v-if="isLoading">
					<view class="shimmer"></view>
				</view>
				
				<!-- 加载中的占位内容 -->
				<view class="preview-icon" v-if="isLoading">
					<image src="/static/icons/icon-image-upload.svg" mode="aspectFit" class="icon-result-placeholder"></image>
				</view>
				
				<!-- 生成结果（当有结果时显示） -->
				<view v-else class="result-content">
					<!-- 如果有结果图片则显示，否则显示占位符 -->
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
			// 计算需要滚动的距离
			const scrollHeight = element.scrollHeight || 0
			const clientHeight = element.clientHeight || 0
			const scrollTop = scrollHeight - clientHeight
			
			// 滚动速度控制参数
			const scrollDuration = 500 // 滚动总时长（毫秒），可以调整这个值来控制滚动速度
			const scrollSteps = 30 // 滚动步数，步数越多滚动越平滑但可能越慢
			const stepInterval = scrollDuration / scrollSteps // 每步间隔时间
			
			// 平滑滚动
			if (element.scrollTo) {
				element.scrollTo({
					top: scrollTop,
					behavior: 'smooth' // 浏览器默认平滑滚动，速度由浏览器控制
				})
			} else {
				// 备用方案：自定义平滑滚动
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
				}, stepInterval) // 根据总时长和步数计算间隔
			}
		}
	}, 200) // 滚动开始前的延迟（毫秒），确保 DOM 已更新
}

const canGenerate = computed(() => {
	return personImg.value && clothingImg.value
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

// 拖拽进入/悬停：激活高亮
const handleDragOver = (event, type) => {
	draggingTarget.value = type
}

// 拖拽离开：取消高亮
const handleDragLeave = (event, type) => {
	if (draggingTarget.value === type) {
		draggingTarget.value = null
	}
}

// 核心：处理放置
const handleDrop = (event, type) => {
	if (requireLogin()) return
	draggingTarget.value = null // 重置 UI
	
	// 暴力获取 files，兼容各种 event 结构
	const files = event.dataTransfer?.files || event.originalEvent?.dataTransfer?.files
	
	console.log('Drop triggered:', type, files) // 调试日志，如果没反应请看控制台
	
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
			uni.showToast({
				title: 'Please drop an image file',
				icon: 'none'
			})
		}
	}
}

const removeImage = (type) => {
	if (type === 'person') {
		personImg.value = ''
	} else {
		clothingImg.value = ''
	}
	// 如果两个图片都被删除，隐藏结果区域并重置加载状态
	if (!personImg.value && !clothingImg.value) {
		showResult.value = false
		isLoading.value = false
		resultImg.value = '' // 清除结果图片
	}
}

const handleGenerate = () => {
	if (requireLogin()) return
	if (!canGenerate.value) {
		return
	}
	
	// 展开结果区域
	showResult.value = true
	// 开始加载
	isLoading.value = true
	
	// 启用滚动并立即滚动到底部（点击按钮后）
	enableScrollAndScrollToBottom()
	
	// TODO: 调用后端 API 生成虚拟试穿结果
	console.log('Generating try-on with:', {
		person: personImg.value,
		clothing: clothingImg.value
	})
	
	uni.showToast({
		title: 'Generating...',
		icon: 'loading',
		duration: 4000
	})
	
	// 这里应该调用实际的生成 API
	// 示例：
	// uni.request({
	//   url: 'your-api-endpoint/generate',
	//   method: 'POST',
	//   data: {
	//     personImg: personImg.value,
	//     clothingImg: clothingImg.value
	//   },
	//   success: (res) => {
	//     // 处理生成结果
	//     isLoading.value = false
	//     // 可以在这里更新结果区域的图片
	//     // resultImg.value = res.data.data.resultImageUrl
	//   },
	//   fail: () => {
	//     isLoading.value = false
	//   }
	// })
	
	// 模拟加载过程（实际使用时应该删除这段）
	setTimeout(() => {
		isLoading.value = false
		// 模拟生成结果（实际使用时应该从 API 响应中获取）
		// resultImg.value = 'https://example.com/generated-image.jpg'
	}, 6000)
}
</script>

<style scoped>
/* 保持原有布局样式 */
.virtual-tryon-container {
	width: 100%;
	min-height: 100%; /* 改为 min-height，允许内容超出 */
	display: flex;
	flex-direction: column;
	padding: 100rpx 100rpx 50rpx 100rpx;
	gap: 100rpx;
	box-sizing: border-box;
	/* 移除 overflow-y，让父容器处理滚动 */
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
	isolation: isolate; /* 创建层叠上下文 */
}

/* 装饰性背景数字 */
.upload-item::before {
	content: "01"; /* 第一个区域用 01 */
	position: absolute;
	top: -100rpx;
	left: -64rpx;
	font-size: 200rpx;
	font-family: 'Didot', serif;
	color: rgba(0,0,0,0.03); /* 极淡 */
	z-index: -1;
	pointer-events: none;
	line-height: 1;
	white-space: nowrap;
}

.upload-item:nth-child(2)::before {
	content: "02"; /* 第二个区域用 02 */
}

.upload-title, .preview-title {
	font-size: 34rpx;
	font-weight: 500;
	color: #1D1D1F;
	font-family: "Didot", serif;
}

/* Upload Zone */
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
	height: 1400rpx; /* 竖版：高度大于宽度 */
	/* 关键：确保 div 也遵循 flexbox 布局 */
	box-sizing: border-box; 
}

.upload-zone:hover {
	border-color: #8C7B60;
	background-color: #FDFBF7;
}

/* 拖拽时的高亮样式 */
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

/* Preview Box */
.preview-box {
	position: relative;
	width: 100%;
	height: 1400rpx; /* 竖版：高度大于宽度 */
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
	/* 禁用状态下的样式 */
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

/* 结果区域 - 默认折叠 */
.preview-section {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	width: 100%;
	/* 默认隐藏：高度为0，透明度为0，溢出隐藏 */
	max-height: 0;
	opacity: 0;
	overflow: hidden;
	/* 平滑过渡动画 */
	transition: max-height 0.6s cubic-bezier(0.4, 0, 0.2, 1), 
	            opacity 0.5s ease 0.1s,
	            margin-top 0.5s ease;
	margin-top: 0;
}

/* 展开状态 */
.preview-section.expanded {
	max-height: none; /* 允许内容自然扩展，不限制高度 */
	opacity: 1;
	margin-top: 20rpx;
}

.section-header {
	margin-bottom: 20rpx;
	/* 标题也需要淡入动画 */
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
	min-height: 1650rpx; /* 竖版：最小高度，可根据内容扩展 */
	margin: 0 auto; /* 水平居中 */
	border: 2rpx solid #E5E5EA;
	border-radius: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #FFF;
	box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.02);
	/* 结果区域内容也需要淡入 */
	opacity: 0;
	transform: translateY(20rpx);
	transition: opacity 0.5s ease 0.3s, transform 0.5s ease 0.3s;
	position: relative;
	overflow: hidden; /* 确保 shimmer 不会溢出 */
}

.preview-section.expanded .result-zone {
	opacity: 1;
	transform: translateY(0);
}

/* 加载状态下的样式 */
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

/* Shimmer 覆盖层 */
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

/* Shimmer 光影效果 */
.shimmer {
	position: absolute;
	top: 0;
	left: -100%;
	width: 50%; /* 光影宽度 */
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
	transform: skewX(-25deg); /* 倾斜角度，让光影更有动感 */
	filter: blur(20rpx); /* 添加模糊效果，让光影更柔和 */
}

/* Shimmer 动画：从左扫到右 */
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
		left: 150%; /* 完全移出视野 */
		opacity: 0;
	}
}

/* 加载中的图标样式 */
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

/* 结果内容 */
.result-content {
	width: 100%;
	min-height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 20rpx;
	box-sizing: border-box;
}

/* 结果图片样式 */
.result-image {
	width: 100%;
	max-width: 100%;
	height: auto;
	max-height: none;
	object-fit: contain;
	display: block;
}
</style>
