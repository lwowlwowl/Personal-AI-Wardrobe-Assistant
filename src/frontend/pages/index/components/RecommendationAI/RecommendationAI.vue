<!-- 推荐 AI 聊天组件：初始问候、多行输入、图片上传、用户/AI 消息展示 -->
<template>
	<view class="chat-container">
		<!-- 初始状态：问候语 + 标签 + 输入框在同一滚动列，输入框上伸时整体同步上移 -->
		<scroll-view 
			v-if="!hasSearched"
			class="initial-scroll"
			scroll-y
			:show-scrollbar="false"
		>
			<view class="initial-content">
				<view class="greeting-wrapper">
					<view class="robot-hero">
						<image src="/static/icons/icon-robot.svg" mode="aspectFit" class="icon-robot-hero"></image>
					</view>
					<view class="greeting-row">
						<text class="wave-emoji">👋</text>
						<text class="greeting-text">Hi! Good Afternoon</text>
					</view>
					<view class="weather-card" :class="{ ready: !loadingWeather }">
						<view class="weather-row">
							<text class="weather-info">Today {{ weatherTempDisplay }}{{ loadingWeather ? '' : '°C' }}</text>
							<text class="weather-divider">|</text>
							<text class="weather-info">{{ weatherTextDisplay }}</text>
							<text class="weather-divider">|</text>
							<text class="weather-info">{{ weatherWindDisplay }}</text>
							<text class="weather-divider">|</text>
							<text class="weather-info">Ideal for a Light Jacket</text>
						</view>
					</view>
				</view>
				<view class="input-container input-in-flow">
					<view class="search-bar">
						<div 
							class="search-bar-drop-zone"
							:class="{ 'drag-over': isDragOverInput }"
							@drop.prevent="handleDropImage"
							@dragover.prevent="handleDragOverInput"
							@dragleave.prevent="handleDragLeaveInput"
							@dragenter.prevent
						>
						<!-- 图片预览区：在输入行上方，仍属于输入框内部 -->
						<view v-if="uploadedImages.length > 0" class="input-thumb-row">
							<scroll-view class="input-thumb-wrap" scroll-x :show-scrollbar="false">
								<view class="input-thumb-list">
									<view v-for="(url, idx) in uploadedImages" :key="idx" class="input-thumb-pill">
										<image :src="url" mode="aspectFill" class="input-thumb-img" @click="previewImageAt(idx)"></image>
										<view class="input-thumb-remove" @click.stop="removeUploadedImageAt(idx)">
											<image src="/static/icons/icon-close.svg" mode="aspectFit" class="icon-close-small"></image>
										</view>
									</view>
								</view>
							</scroll-view>
						</view>
						<!-- 输入行：+ | 文字 | 发送 -->
						<view class="search-input-row">
							<view class="search-icon-left" @click="handleAdd">
								<image src="/static/icons/icon-plus.svg" mode="aspectFit" class="icon-search-btn"></image>
							</view>
							<textarea 
								class="search-input search-textarea"
								v-model="searchQuery"
								placeholder="Ask me anything!"
								placeholder-class="search-placeholder"
								:maxlength="-1"
								:auto-height="true"
								@keydown.enter.exact.prevent="handleSearch"
								@confirm="handleSearch"
							/>
							<view class="search-button" @click="handleSearch">
								<image src="/static/icons/icon-send.svg" mode="aspectFit" class="icon-search-btn"></image>
							</view>
						</view>
						</div>
					</view>
				</view>
				<view class="search-tabs">
					<text 
						class="tab-text" 
						:class="{ 'active': activeTab === 'wardrobe' }"
						@click="setActiveTab('wardrobe')"
					>My Wardrobe</text>
					<view class="tab-divider"></view>
					<text 
						class="tab-text" 
						:class="{ 'active': activeTab === 'online' }"
						@click="setActiveTab('online')"
					>Online Search</text>
				</view>
			</view>
		</scroll-view>
		
		<!-- 聊天状态：scroll-view 聊天区域 -->
		<scroll-view 
			v-else
			class="chat-scroll-area" 
			scroll-y 
			:scroll-into-view="scrollTarget"
			:scroll-with-animation="true"
			:enable-back-to-top="true"
		>
			<view class="message-list">
				<view 
					v-for="(msg, index) in chatHistory" 
					:key="index" 
					:id="'msg-' + index"
					class="message-row"
					:class="msg.role"
				>
					<!-- 用户消息 (右侧) -->
					<view v-if="msg.role === 'user'" class="user-bubble">
						<!-- 用户消息图片 -->
						<view v-if="msg.images && msg.images.length > 0" class="user-image-group">
							<image 
								v-for="(img, imgIndex) in msg.images" 
								:key="imgIndex"
								:src="img" 
								mode="aspectFill"
								class="user-msg-img"
								@click="previewImages(msg.images, imgIndex)"
							/>
						</view>
						<text v-if="msg.content" class="message-text">{{ msg.content }}</text>
					</view>
					
					<!-- AI 消息 (左侧)：推荐卡片组件，支持多套推荐与左右滑动 -->
					<view v-else-if="msg.role === 'ai'" class="ai-container ai-fade-in">
						<view class="ai-avatar">
							<image src="/static/icons/icon-robot.svg" mode="aspectFit" class="icon-robot-avatar"></image>
						</view>
						<view class="ai-content">
							<!-- 多套推荐：swiper 左右滑动 -->
							<swiper v-if="getRecommendations(msg).length > 1" class="recommend-swiper" :indicator-dots="true" indicator-active-color="#9D8B70">
								<swiper-item v-for="(rec, ri) in getRecommendations(msg)" :key="ri">
									<RecommendationCard
										:recommendation="rec"
										:show-regenerate="ri === 0"
										@regenerate="handleRegenerate(index)"
										@preview-images="previewImages"
									/>
								</swiper-item>
							</swiper>
							<!-- 单套推荐：直接渲染 -->
							<RecommendationCard
								v-else-if="getRecommendations(msg).length === 1"
								:recommendation="getRecommendations(msg)[0]"
								:show-regenerate="true"
								@regenerate="handleRegenerate(index)"
								@preview-images="previewImages"
							/>
							<!-- 兼容旧格式：无推荐数据时仅显示 content -->
							<view v-else-if="msg.content" class="message-text">{{ msg.content }}</view>
						</view>
					</view>
					
					<!-- 加载指示器：过程感文案轮播 -->
					<view v-if="msg.role === 'loading'" class="ai-container">
						<view class="ai-avatar">
							<image src="/static/icons/icon-robot.svg" mode="aspectFit" class="icon-robot-avatar"></image>
						</view>
						<view class="loading-indicator">
							<text class="loading-step-text">{{ LOADING_STEPS[loadingStep] }}</text>
							<view class="loading-dots">
								<view class="loading-dot"></view>
								<view class="loading-dot"></view>
								<view class="loading-dot"></view>
							</view>
						</view>
					</view>
				</view>
				<view class="spacer" id="bottom-spacer"></view>
			</view>
		</scroll-view>
		
		<!-- 聊天状态：输入框固定在底部，外层 box 铺满右侧、背景与页面一致 -->
		<view v-if="hasSearched" class="input-box-wrapper">
			<view class="input-container fixed-bottom">
				<view class="search-bar">
					<div 
						class="search-bar-drop-zone"
						:class="{ 'drag-over': isDragOverInput }"
						@drop.prevent="handleDropImage"
						@dragover.prevent="handleDragOverInput"
						@dragleave.prevent="handleDragLeaveInput"
						@dragenter.prevent
					>
				<!-- 图片预览区：在输入行上方，仍属于输入框内部 -->
				<view v-if="uploadedImages.length > 0" class="input-thumb-row">
					<scroll-view class="input-thumb-wrap" scroll-x :show-scrollbar="false">
						<view class="input-thumb-list">
							<view v-for="(url, idx) in uploadedImages" :key="idx" class="input-thumb-pill">
								<image :src="url" mode="aspectFill" class="input-thumb-img" @click="previewImageAt(idx)"></image>
								<view class="input-thumb-remove" @click.stop="removeUploadedImageAt(idx)">
									<image src="/static/icons/icon-close.svg" mode="aspectFit" class="icon-close-small"></image>
								</view>
							</view>
						</view>
					</scroll-view>
				</view>
				<!-- 输入行：+ | 文字 | 发送 -->
				<view class="search-input-row">
					<view class="search-icon-left" @click="handleAdd">
						<image src="/static/icons/icon-plus.svg" mode="aspectFit" class="icon-search-btn"></image>
					</view>
					<textarea 
						class="search-input search-textarea"
						v-model="searchQuery"
						placeholder="Ask me anything!"
						placeholder-class="search-placeholder"
						:maxlength="-1"
						:auto-height="true"
						@keydown.enter.exact.prevent="handleSearch"
						@confirm="handleSearch"
					/>
					<view class="search-button" @click="handleSearch">
						<image src="/static/icons/icon-send.svg" mode="aspectFit" class="icon-search-btn"></image>
					</view>
				</view>
					</div>
				</view>
			</view>
			<view class="search-tabs">
				<text 
					class="tab-text" 
					:class="{ 'active': activeTab === 'wardrobe' }"
					@click="setActiveTab('wardrobe')"
				>My Wardrobe</text>
				<view class="tab-divider"></view>
				<text 
					class="tab-text" 
					:class="{ 'active': activeTab === 'online' }"
					@click="setActiveTab('online')"
				>Online Search</text>
			</view>
		</view>
	</view>
</template>

<script setup>
/**
 * 推荐 AI 聊天逻辑：
 * - 初始 / 聊天两种布局切换
 * - 用户消息支持文字 + 图片
 * - 推荐数据 reactive 结构，v-for 渲染，RecommendationCard 独立组件
 * - 支持多会话：由父组件传入 currentConversationId / currentConversation，并 emit create/update
 */
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import RecommendationCard from './RecommendationCard.vue'
import { LOADING_STEPS, getMockAiResponse, MOCK_DELAY_MS, USE_RECOMMENDATION_MOCK, normalizeChatResponse } from './mockData.js'
import { chatRecommendation, getWeatherNow } from '@/api/recommendationApi.js'

const props = defineProps({
	currentConversationId: { type: String, default: null },
	currentConversation: { type: Object, default: null }
})

const emit = defineEmits(['create-conversation', 'update-conversation'])

const activeTab = ref('wardrobe') // 当前标签：wardrobe | online
const searchQuery = ref('')
const hasSearched = ref(false) // 状态管理：是否已搜索

// 天气：由经纬度请求后端获取；加载前显示 —，加载完淡入；半小时内同位置复用
const WEATHER_REUSE_MS = 30 * 60 * 1000
const WEATHER_MIN_LOADING_MS = 300
const weatherCache = { key: '', at: 0, data: null }
const loadingWeather = ref(true)
const weatherTemp = ref('')
const weatherText = ref('')
const weatherWindDesc = ref('')
const weatherTempDisplay = computed(() => (loadingWeather.value ? '—' : (weatherTemp.value || '—')))
const weatherTextDisplay = computed(() => (loadingWeather.value ? '—' : (weatherText.value || '—')))
const weatherWindDisplay = computed(() => (loadingWeather.value ? '—' : (weatherWindDesc.value || '—')))

function applyWeatherData(data) {
  if (data.temp != null && data.temp !== '') weatherTemp.value = String(data.temp)
  if (data.text != null && data.text !== '') weatherText.value = String(data.text)
  if (data.windDesc) weatherWindDesc.value = data.windDesc
}

function setWeatherReady() {
  loadingWeather.value = false
}

const DEFAULT_LAT = 29.87
const DEFAULT_LON = 121.55

async function fetchWeatherForCoords(lat, lon) {
  const key = `${Number(lat).toFixed(3)},${Number(lon).toFixed(3)}`
  const now = Date.now()
  const t0 = Date.now()

  if (weatherCache.key === key && (now - weatherCache.at) < WEATHER_REUSE_MS && weatherCache.data) {
    applyWeatherData(weatherCache.data)
    const dt = Date.now() - t0
    if (dt < WEATHER_MIN_LOADING_MS) {
      await new Promise(r => setTimeout(r, WEATHER_MIN_LOADING_MS - dt))
    }
    setWeatherReady()
    return
  }

  try {
    const data = await getWeatherNow(lat, lon)
    weatherCache.key = key
    weatherCache.at = Date.now()
    weatherCache.data = data
    applyWeatherData(data)
    const dt = Date.now() - t0
    if (dt < WEATHER_MIN_LOADING_MS) {
      await new Promise(r => setTimeout(r, WEATHER_MIN_LOADING_MS - dt))
    }
    setWeatherReady()
  } catch (err) {
    console.warn('[RecommendationAI] 天气请求失败', err?.message || err)
    setWeatherReady()
  }
}

onMounted(() => {
  uni.getLocation({
    type: 'wgs84',
    success: (res) => {
      fetchWeatherForCoords(res.latitude, res.longitude)
    },
    fail: () => {
      fetchWeatherForCoords(DEFAULT_LAT, DEFAULT_LON)
    }
  })
})
const chatHistory = ref([]) // 聊天历史记录
const scrollTarget = ref('') // 用于自动滚动
const justCreatedConversation = ref(false) // 刚建立会话尚未收到 AI 回复，避免被 prop 覆盖
const loadingStep = ref(0) // 加载过程步骤，用于展示「分析中」文案

/** 将 AI 消息转为 recommendation 数组，支持多套推荐与 swiper 滑动 */
const getRecommendations = (msg) => {
	if (msg.recommendations && Array.isArray(msg.recommendations) && msg.recommendations.length > 0) {
		return msg.recommendations
	}
	// 兼容旧格式：content + tags + outfitItems 转为单条 recommendation
	const items = (msg.outfitItems || []).map(it => ({
		type: it.category,
		name: it.name,
		reason: it.desc,
		details: it.details
	}))
	if (msg.list && msg.list.length > 0 && items.length === 0) {
		msg.list.forEach(t => items.push({ type: 'Item', name: t, reason: '' }))
	}
	const tags = msg.tags || []
	const tempTag = tags.find(t => /°C|℃/.test(t))
	const styleTags = tags.filter(t => t !== tempTag)
	const rec = {
		title: styleTags[0] || '',
		temperature: tempTag || '',
		styleTags,
		content: msg.content,
		items,
		whyThisWorks: msg.whyThisWorks || [],
		images: msg.images || []
	}
	// 有 items 或 images 才当推荐卡片；仅 content 时返回 []，由模板以纯文字展示（联调第一阶段）
	return items.length > 0 || (rec.images && rec.images.length > 0) ? [rec] : []
}
const handleRegenerate = (msgIdx) => {
	const msg = chatHistory.value[msgIdx]
	if (msg?.role !== 'ai') return
	chatHistory.value[msgIdx] = { role: 'loading', content: '' }
	loadingStep.value = 0
	const stepInterval = setInterval(() => {
		loadingStep.value = (loadingStep.value + 1) % LOADING_STEPS.length
	}, 500)
	setTimeout(() => {
		clearInterval(stepInterval)
		chatHistory.value[msgIdx] = { ...msg }
		const cid = props.currentConversationId
		if (cid) emit('update-conversation', { id: cid, messages: [...chatHistory.value] })
		scrollToBottom()
	}, 2000)
}

// 依当前会话同步本地状态：新建会话则清空；切换会话则载入该会话消息
watch(
	() => [props.currentConversationId, props.currentConversation],
	([cid, conv]) => {
		if (cid === null || cid === undefined) {
			hasSearched.value = false
			chatHistory.value = []
			justCreatedConversation.value = false
			return
		}
		if (justCreatedConversation.value) return
		if (conv && conv.messages) {
			chatHistory.value = conv.messages.length ? [...conv.messages] : []
			hasSearched.value = chatHistory.value.length > 0
		} else {
			chatHistory.value = []
			hasSearched.value = false
		}
	},
	{ immediate: true }
)

const setActiveTab = (tab) => {
	activeTab.value = tab
}

// 自动滚动到底部
const scrollToBottom = () => {
	nextTick(() => {
		scrollTarget.value = 'bottom-spacer'
		// 延迟确保 DOM 更新完成
		setTimeout(() => {
			scrollTarget.value = ''
		}, 100)
	})
}

const handleSearch = async () => {
	const query = searchQuery.value.trim()
	const hasImages = uploadedImages.value.length > 0
	if (!query && !hasImages) return

	const isNewSession = props.currentConversationId === null || props.currentConversationId === undefined
	const isPendingSession = props.currentConversationId && !props.currentConversation
	const isFirstMessageInConversation = props.currentConversationId && (props.currentConversation?.messages?.length === 0)

	// 1. 切换 UI 状态：搜索框下移，问候语消失
	hasSearched.value = true

	// 2. 添加用户消息（带入文字与已上传图片）
	const imagesToSend = uploadedImages.value.length > 0 ? [...uploadedImages.value] : undefined
	const userMsg = { role: 'user', content: query, images: imagesToSend }
	chatHistory.value.push(userMsg)

	// 首次进入直接输入 或 点击新建会话后首次输入：通知父组件建立会话并加入列表
	if (isNewSession || isPendingSession) {
		const title = (query || '新对话').slice(0, 36)
		const payload = { title, firstMessage: userMsg }
		if (isPendingSession) payload.id = props.currentConversationId
		emit('create-conversation', payload)
		justCreatedConversation.value = true
	}

	// 清空输入框与已上传图片
	searchQuery.value = ''
	uploadedImages.value = []

	// 滚动到底部
	scrollToBottom()

	// 3. 添加加载指示器（过程感文案轮播）
	chatHistory.value.push({ role: 'loading', content: '' })
	loadingStep.value = 0
	scrollToBottom()
	const stepInterval = setInterval(() => {
		loadingStep.value = (loadingStep.value + 1) % LOADING_STEPS.length
	}, 500)

	// 获取 AI 回复：USE_RECOMMENDATION_MOCK 为 true 用 mock，否则请求后端 /api/chat（见 backend/AIwardrobe/README.md）
	const finishLoading = (aiMessage) => {
		clearInterval(stepInterval)
		chatHistory.value = chatHistory.value.filter(msg => msg.role !== 'loading')
		chatHistory.value.push(aiMessage)
		justCreatedConversation.value = false
		const cid = props.currentConversationId
		if (cid) {
			const payload = { id: cid, messages: [...chatHistory.value] }
			if (isFirstMessageInConversation) payload.title = (query || '新对话').slice(0, 36)
			emit('update-conversation', payload)
		}
		scrollToBottom()
	}

	if (USE_RECOMMENDATION_MOCK) {
		setTimeout(() => {
			finishLoading(getMockAiResponse())
		}, MOCK_DELAY_MS)
		return
	}

	// 联调：请求后端，支持第一阶段纯文字 { content } 与第二阶段 { content, recommendations }
	try {
		const res = await chatRecommendation(query)
		finishLoading(normalizeChatResponse(res))
	} catch (err) {
		finishLoading({
			role: 'ai',
			content: '请求失败：' + (err && err.message ? err.message : '网络错误')
		})
		uni.showToast({ title: '推荐请求失败', icon: 'none' })
	}
}

// 本地上传图片（输入框内缩略图，最多 8 张）
const MAX_UPLOAD_IMAGES = 8
const uploadedImages = ref([])
const isDragOverInput = ref(false)

const handleDragOverInput = (e) => {
	e.preventDefault()
	if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy'
	isDragOverInput.value = true
}

const handleDragLeaveInput = () => {
	isDragOverInput.value = false
}

const handleDropImage = (e) => {
	e.preventDefault()
	isDragOverInput.value = false
	// 与 VirtualTryOn 一致：兼容各种 event 结构
	const rawFiles = e.dataTransfer?.files || e.originalEvent?.dataTransfer?.files
	if (!rawFiles || !rawFiles.length) return
	const remain = MAX_UPLOAD_IMAGES - uploadedImages.value.length
	if (remain <= 0) {
		uni.showToast({ title: `最多只能上传 ${MAX_UPLOAD_IMAGES} 张图片`, icon: 'none' })
		return
	}
	const files = Array.from(rawFiles).filter(f => f.type && f.type.startsWith('image/')).slice(0, remain)
	if (files.length === 0) {
		uni.showToast({ title: '请拖入图片文件', icon: 'none' })
		return
	}
	if (typeof URL === 'undefined' || !URL.createObjectURL) return
	const add = files.map(f => URL.createObjectURL(f))
	uploadedImages.value = [...uploadedImages.value, ...add]
}

const handleAdd = () => {
	const remain = MAX_UPLOAD_IMAGES - uploadedImages.value.length
	if (remain <= 0) {
		uni.showToast({
			title: `最多只能上传 ${MAX_UPLOAD_IMAGES} 张图片`,
			icon: 'none',
			duration: 2000
		})
		return
	}
	uni.chooseImage({
		count: remain,
		sizeType: ['original', 'compressed'],
		sourceType: ['album', 'camera'],
		success: (res) => {
			const selectedCount = res.tempFilePaths?.length || 0
			const add = (res.tempFilePaths || []).slice(0, remain)
			uploadedImages.value = [...uploadedImages.value, ...add]
			
			// 如果用户选择的图片数量超过了剩余可上传数量，显示提示
			if (selectedCount > remain) {
				uni.showToast({
					title: `最多只能上传 ${MAX_UPLOAD_IMAGES} 张图片，已自动添加 ${remain} 张`,
					icon: 'none',
					duration: 2500
				})
			}
		},
		fail: (err) => {
			console.error('选择图片失败:', err)
		}
	})
}

const removeUploadedImageAt = (index) => {
	uploadedImages.value = uploadedImages.value.filter((_, i) => i !== index)
}

// 点击缩略图预览完整图片（输入框内）
const previewImageAt = (index) => {
	const urls = uploadedImages.value
	if (!urls || urls.length === 0) return
	uni.previewImage({
		current: urls[index],
		urls
	})
}

// 点击聊天消息中的图片预览大图
const previewImages = (urls, index = 0) => {
	if (!urls || urls.length === 0) return
	uni.previewImage({
		current: urls[index],
		urls
	})
}
</script>

<style scoped>
/* 整体容器 */
.chat-container {
	width: 100%;
	height: 100vh;
	display: flex;
	flex-direction: column;
	position: relative;
	background-color: #FDFBF7;
	overflow: hidden;
}

/* 初始状态：整体滚动区（问候语与输入框同步上移） */
.initial-scroll {
	width: 100%;
	height: 100vh;
}

/* 初始状态内容区：问候语 + 输入框 + 标签 */
.initial-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 40rpx 40rpx 80rpx;
	min-height: 100vh;
	box-sizing: border-box;
}

/* 问候语区块 */
.greeting-wrapper {
	width: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	padding-top: 24vh;
	animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
}

@keyframes fadeInUp {
	from {
		opacity: 0;
		transform: translateY(30rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.robot-hero {
	margin-bottom: 30rpx;
	display: flex;
	justify-content: center;
}

/* 机器人悬浮呼吸动画 */
.robot-hero .icon-robot-hero {
	width: 60px;
	height: 60px;
	display: block;
	/* 4 秒循环，丝滑缓动 */
	animation: float 4s ease-in-out infinite;
}
.icon-robot-avatar {
	width: 26px;
	height: 26px;
	display: block;
}
.icon-search-btn {
	width: 20px;
	height: 20px;
	display: block;
}

@keyframes float {
	0% { transform: translateY(0px); }
	50% { transform: translateY(-6px); } /* 轻轻上浮效果 */
	100% { transform: translateY(0px); }
}

/* 问候语行：挥手 emoji + 文本 */
.greeting-row {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 16rpx;
	margin-bottom: 16rpx;
}

.wave-emoji {
	font-size: 56rpx;
}

.greeting-text {
	font-family: serif;
	font-size: 56rpx;
	font-weight: bold;
	color: #1D1D1F;
}

/* 天气卡片：加载中透明+微位移，数据回来淡入 */
.weather-card {
	opacity: 0;
	transform: translateY(6px);
	transition: opacity 260ms ease, transform 260ms ease;
}
.weather-card.ready {
	opacity: 1;
	transform: translateY(0);
}

/* 天气信息行：温度 | 天气现象 | 风力 | 推荐 */
.weather-row {
	margin-top: 40rpx;
	margin-bottom: 120rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	white-space: nowrap;
}

.weather-info {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: serif; 
	letter-spacing: 0.5px;
}

.weather-divider {
	font-size: 24rpx;
	color: #AAA; 
	margin: 0 15rpx; /* 控制 | 左右的间隔大小 */
	position: relative;
}

/* 加载指示器：过程感文案 + 点点动画 */
.loading-indicator {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	padding: 20rpx 0;
}

.loading-step-text {
	font-size: 28rpx;
	color: #9D8B70;
	font-family: "PingFang SC", -apple-system, sans-serif;
	font-weight: 400;
	letter-spacing: 0.3px;
}

.loading-dots {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.loading-dot {
	width: 12rpx;
	height: 12rpx;
	border-radius: 50%;
	background-color: #9D8B70;
	animation: loading-bounce 1.4s ease-in-out infinite;
}

.loading-dots .loading-dot:nth-child(1) {
	animation-delay: 0s;
}

.loading-dots .loading-dot:nth-child(2) {
	animation-delay: 0.2s;
}

.loading-dots .loading-dot:nth-child(3) {
	animation-delay: 0.4s;
}

@keyframes loading-bounce {
	0%, 80%, 100% {
		transform: scale(0.8);
		opacity: 0.5;
	}
	40% {
		transform: scale(1.2);
		opacity: 1;
	}
}

/* 聊天状态：scroll-view 区域 */
.chat-scroll-area {
	width: 100%;
	height: 100vh;
	flex: 1;
	overflow-y: auto;
}

.message-list {
	width: 100%;
	padding: 40rpx 40rpx 40rpx 40rpx;
	display: flex;
	flex-direction: column;
	min-height: 100%;
	/* 确保消息列表区域文本可被选择 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* 底部占位，为固定输入框 box 留出空间 */
.spacer {
	height: 230rpx;
}

/* 对话气泡 - 左右分栏布局 */
.message-row {
	display: flex;
	width: 100%;
	margin-bottom: 60rpx;
}

/* 用户消息 (右侧) */
.message-row.user {
	justify-content: flex-end;
}

.user-bubble {
	background-color: #F2F2F2;
	padding: 24rpx 40rpx;
	border-radius: 40rpx;
	border-bottom-right-radius: 4rpx; /* 气泡小尾巴效果 */
	max-width: 70%;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	/* 确保用户消息文本可被选择 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* 用户消息中的图片组 */
.user-image-group {
	display: flex;
	gap: 12rpx;
	flex-wrap: wrap;
}

.user-msg-img {
	width: 160rpx;
	height: 160rpx;
	border-radius: 12rpx;
	background: #EEE;
	border: 2rpx solid #E5E5EA;
	object-fit: cover;
}

/* 用户与 AI 消息正文（与图二聊天风格一致：清晰无衬线、统一字号） */
.message-text {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Microsoft YaHei", sans-serif;
	font-weight: 400;
	line-height: 1.6;
	word-wrap: break-word;
	/* 确保文本可被选择和复制 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* AI 消息 (左侧) */
.message-row.ai {
	justify-content: flex-start;
}

.ai-container {
	display: flex;
	gap: 24rpx;
	width: 80%;
	align-items: flex-start;
}

/* AI 结果分模块淡入动画 */
.ai-fade-in {
	animation: aiFadeIn 0.5s ease-out forwards;
}

.ai-fade-block {
	opacity: 0;
	animation: aiBlockFade 0.4s ease-out forwards;
}

.ai-list-item.ai-fade-block {
	opacity: 0;
}

@keyframes aiFadeIn {
	from {
		opacity: 0;
		transform: translateY(8rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

@keyframes aiBlockFade {
	from {
		opacity: 0;
		transform: translateY(6rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.ai-avatar {
	width: 72rpx;
	height: 72rpx;
	background: #EAE5D9;
	border-radius: 50%;
	flex-shrink: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 2rpx solid #1D1D1F;
}

.ai-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	width: 100%;
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* 多套推荐 swiper */
.recommend-swiper {
	width: 100%;
	height: auto;
	min-height: 400rpx;
}

.recommend-swiper swiper-item {
	height: auto;
	padding-bottom: 60rpx;
}

/* AI 列表样式（兼容旧格式，无 RecommendationCard 时） */
.ai-list {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	margin-top: 8rpx;
}

.ai-list-item {
	display: flex;
	align-items: flex-start;
	gap: 12rpx;
}

.list-bullet {
	font-size: 32rpx;
	color: #9D8B70;
	flex-shrink: 0;
	line-height: 1.4;
}

/* AI 推荐列表项（与 message-text 统一，采用图二风格） */
.list-text {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Microsoft YaHei", sans-serif;
	font-weight: 400;
	line-height: 1.6;
	flex: 1;
	/* 确保文本可被选择和复制 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* AI 图片组样式 */
.ai-image-group {
	display: flex;
	gap: 16rpx;
	margin-top: 16rpx;
	flex-wrap: wrap;
}

.rec-img {
	width: 200rpx;
	height: 260rpx;
	border-radius: 12rpx;
	background-color: #EEE;
	border: 2rpx solid #E5E5EA;
	object-fit: cover;
}

/* 输入框外层 box：铺满右侧、背景与页面一致、上方留白 */
.input-box-wrapper {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	width: 100%;
	padding-top: 40rpx;
	padding-bottom: 35rpx;
	background-color: #FDFBF7;
	display: flex;
	flex-direction: column;
	align-items: center;
	z-index: 10;
}

/* 输入框容器 */
.input-container {
	width: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	transition: all 0.6s cubic-bezier(0.25, 1, 0.5, 1);
}

/* 初始状态：在滚动流内，随问候语同步 */
.input-container.input-in-flow {
	flex-shrink: 0;
	margin-top: 80rpx;
}

/* 聊天状态：固定在底部（在 input-box-wrapper 内，无需绝对定位） */
.input-box-wrapper .input-container.fixed-bottom {
	position: relative;
	bottom: auto;
	left: auto;
	transform: none;
}

/* 图片预览区：位于输入行上方，输入框内部 */
.input-thumb-row {
	width: 100%;
	padding: 16rpx 24rpx 12rpx;
	flex-shrink: 0;
}

/* 预览区高度，需与 input-thumb-pill 的 height 一致或略大 */
.input-thumb-wrap {
	width: 100%;
	height: 100rpx;
}

.input-thumb-list {
	display: flex;
	gap: 12rpx;
	height: 100rpx;
	padding: 4rpx 0;
	white-space: nowrap;
}

/* 单张缩略图胶囊（修改 width/height 可调整尺寸，如 80rpx、120rpx） */
.input-thumb-pill {
	position: relative;
	width: 96rpx;
	height: 96rpx;
	border-radius: 16rpx;
	overflow: hidden;
	background: #EEE;
	border: 2rpx solid #E5E5EA;
	flex-shrink: 0;
}

/* 缩略图图片，点击可预览大图 */
.input-thumb-img {
	width: 100%;
	height: 100%;
	display: block;
	object-fit: cover;
	cursor: pointer;
}

/* 缩略图右上角删除按钮 */
.input-thumb-remove {
	position: absolute;
	top: 0;
	right: 0;
	width: 40rpx;
	height: 40rpx;
	border-radius: 0 12rpx 0 8rpx;
	background: rgba(0,0,0,0.5);
	display: flex;
	align-items: center;
	justify-content: center;
}

.icon-close-small {
	width: 22rpx;
	height: 22rpx;
	filter: brightness(0) invert(1);
}

/* 搜索条保持原有长度，不随容器变宽；多行时高度可变 */
.search-bar {
	width: 1400rpx; 
	max-width: 90%; 
	min-height: 100rpx;
	background-color: #FFFFFF;
	border-radius: 50rpx;
	display: flex;
	flex-direction: column;
	align-items: stretch;
	border: 2rpx solid #1D1D1F; 
	box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08); 
	transition: all 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.search-bar-drop-zone {
	display: flex;
	flex-direction: column;
	align-items: stretch;
	min-height: 100%;
	border-radius: inherit;
	transition: background-color 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.search-bar-drop-zone:hover {
	background-color: rgba(0, 0, 0, 0.02);
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.06);
}

.search-bar-drop-zone.drag-over {
	background-color: rgba(157, 139, 112, 0.12);
	box-shadow: inset 0 0 0 3rpx #9D8B70, 0 4rpx 20rpx rgba(157, 139, 112, 0.25);
}

/* 输入行：+ | 文字 | 发送 */
.search-input-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 16rpx 22rpx 16rpx 32rpx;
	flex: 1;
	min-height: 68rpx;
}

.search-bar:focus-within {
	/* 模拟光晕扩散 */
	box-shadow: 0 10rpx 40rpx rgba(0, 0, 0, 0.15);
	border-color: #8C7B60; /* 边框变色为主题色 */
	transform: scale(1.022); /* 轻微放大，产生「提起来」的感觉 */
}

.search-icon-left {
	width: 72rpx;
	height: 72rpx;
	min-height: 72rpx;
	border-radius: 50%;
	background-color: transparent;
	display: flex;
	flex-shrink: 0;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: all 0.2s ease;
	margin-right: 20rpx;
	position: relative;
	left: -10rpx;
	box-sizing: border-box;
	align-self: center;
}

.search-icon-left:hover {
	background-color: #1D1D1F;
}

.search-icon-left:hover .icon-search-btn {
	filter: brightness(0) invert(1);
}

.search-input {
	flex: 1;
	min-width: 120rpx;
	min-height: 72rpx;
	max-height: 400rpx;
	padding: 0;
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Microsoft YaHei", sans-serif;
	font-weight: 400;
	line-height: 72rpx;
	border: none;
	outline: none;
	overflow-y: auto;
	align-self: center;
	box-sizing: border-box;
	vertical-align: middle;
}


.search-placeholder {
	color: #999;
	font-weight: 300;
	font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Microsoft YaHei", sans-serif;
}

.search-button {
	width: 72rpx;
	height: 72rpx;
	min-height: 72rpx;
	margin-left: 20rpx;
	border-radius: 50%;
	background-color: transparent; /* 图片里按钮背景是透明的，边框是外围的 */
	border: 2rpx solid #1D1D1F; /* 按钮圆圈边框，用 rpx 与整体一致 */
	display: flex;
	flex-shrink: 0;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: all 0.2s ease;
	box-sizing: border-box;
	align-self: center;
}

.search-button:hover {
	background-color: #1D1D1F;
}

.search-button:hover .icon-search-btn {
	filter: brightness(0) invert(1);
}

/* 底部标签（初始状态内，位于输入框下方） */
.search-tabs {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 24rpx;
	transition: opacity 0.3s ease;
	flex-shrink: 0;
	margin-top: 25rpx;
}

.tab-text {
	font-size: 26rpx;
	color: #A0A0A0; /* 未选中时灰色 */
	cursor: pointer;
	font-family: "Didot", serif;
	font-weight: 600;
	transition: color 0.2s;
}

.tab-text.active {
	color: #8C7B60; /* 激活时深灰褐色 */
	text-decoration: underline;
	text-decoration-color: #DDD; /* 模拟下划线效果 */
	text-underline-offset: 4px;
}

/* 垂直分割线 */
.tab-divider {
	width: 1px;
	height: 24rpx;
	background-color: #D1D1D1;
}
</style>
