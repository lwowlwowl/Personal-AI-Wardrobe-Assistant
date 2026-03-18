<!-- 推荐 AI 聊天组件：初始问候、多行输入、图片上传、用户/AI 消息展示 -->
<template>
	<view class="chat-container">
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
					<view v-if="isLoggedIn" class="weather-card" :class="{ ready: !loadingWeather }">
						<view class="weather-row">
							<text class="weather-info">Today {{ weatherTempDisplay }}{{ loadingWeather ? '' : '°C' }}</text>
							<text class="weather-divider">|</text>
							<text class="weather-info">{{ weatherTextDisplay }}</text>
							<text class="weather-divider">|</text>
							<text class="weather-info">{{ weatherWindDisplay }}</text>
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
					<text class="tab-text" :class="{ active: activeTab === 'wardrobe' }" @click="setActiveTab('wardrobe')">My Wardrobe</text>
					<view class="tab-divider"></view>
					<text class="tab-text" :class="{ active: activeTab === 'online' }" @click="setActiveTab('online')">Online Search</text>
				</view>
			</view>
		</scroll-view>

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
					<view v-if="msg.role === 'user'" class="user-bubble">
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

					<view v-else-if="msg.role === 'ai'" class="ai-container ai-fade-in">
						<view class="ai-avatar">
							<image src="/static/icons/icon-robot.svg" mode="aspectFit" class="icon-robot-avatar"></image>
						</view>

						<view class="ai-content">
							<!-- 计划表（多天/多场景/按日程组织） -->
							<PlanScheduleCard
								v-if="getMessageRenderType(msg) === 'plan'"
								:plan="msg.plan"
								:raw-text="msg.rawText || msg.content || ''"
							/>

							<!-- 推荐型：上文字（可选）+ 下卡片，同一容器内 -->
							<view v-else-if="getMessageRenderType(msg) === 'recommendation'" class="mixed-message-wrap">
								<ChatMessageBubble
									v-if="msg.content"
									:content="msg.content"
								/>
								<view class="cards-area">
									<swiper
										v-if="getRecommendations(msg).length > 1"
										class="recommend-swiper"
										:indicator-dots="true"
										indicator-active-color="#9D8B70"
									>
										<swiper-item v-for="(rec, ri) in getRecommendations(msg)" :key="ri">
											<RecommendationCard
												:recommendation="rec"
												:show-regenerate="ri === 0"
												@regenerate="handleRegenerate(index)"
												@preview-images="previewImages"
											/>
										</swiper-item>
									</swiper>
									<RecommendationCard
										v-else-if="getRecommendations(msg).length === 1"
										:recommendation="getRecommendations(msg)[0]"
										:show-regenerate="true"
										@regenerate="handleRegenerate(index)"
										@preview-images="previewImages"
									/>
								</view>
							</view>

							<!-- 纯文本 / 兜底 -->
							<ChatMessageBubble
								v-else
								:content="getDisplayContent(msg)"
							/>
						</view>
					</view>

					<view v-if="msg.role === 'loading'" class="ai-container ai-fade-in">
						<view class="ai-avatar">
							<image src="/static/icons/icon-robot.svg" mode="aspectFit" class="icon-robot-avatar"></image>
						</view>
						<view class="loading-premium-card">
							<view class="shimmer-layer"></view>
							<view class="loading-content-center">
								<view class="aura-ring"></view>
								<text class="loading-step-text editorial-text">{{ LOADING_STEPS[loadingStep] }}</text>
								<text class="loading-sub-text">Scanning your wardrobe assets...</text>
							</view>
							<view class="loading-progress-wrap">
								<view class="loading-progress-track">
									<view class="loading-progress-fill" :style="{ width: loadingProgress + '%' }"></view>
								</view>
								<text class="loading-progress-label">{{ loadingProgressPercent }}%</text>
							</view>
							<view class="skeleton-lines">
								<view class="skeleton-line short"></view>
								<view class="skeleton-line long"></view>
								<view class="skeleton-line medium"></view>
							</view>
						</view>
					</view>
				</view>

				<view class="spacer" id="bottom-spacer"></view>
			</view>
		</scroll-view>

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
				<text class="tab-text" :class="{ active: activeTab === 'wardrobe' }" @click="setActiveTab('wardrobe')">My Wardrobe</text>
				<view class="tab-divider"></view>
				<text class="tab-text" :class="{ active: activeTab === 'online' }" @click="setActiveTab('online')">Online Search</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import RecommendationCard from './RecommendationCard.vue'
import ChatMessageBubble from './ChatMessageBubble.vue'
import PlanScheduleCard from './PlanScheduleCard.vue'
import { LOADING_STEPS, normalizeChatResponse } from './chatContentAdapter.js'
import { chatRecommendation, getWeatherNow } from '@/api/recommendationApi.js'
import { getClothingList, API_BASE_URL } from '@/api/wardrobe.js'

const props = defineProps({
	isLoggedIn: { type: Boolean, default: false },
	// 父组件目前会传数字 ID，这里放宽为字符串或数字，避免类型告警
	currentConversationId: { type: [String, Number], default: null },
	currentConversation: { type: Object, default: null }
})

const emit = defineEmits(['create-conversation', 'update-conversation'])

const activeTab = ref('wardrobe')
const searchQuery = ref('')
const hasSearched = ref(false)

const WEATHER_MIN_LOADING_MS = 300
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
	const t0 = Date.now()
	try {
		const data = await getWeatherNow(lat, lon)
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

function tryFetchWeather() {
	if (!props.isLoggedIn) {
		setWeatherReady()
		return
	}
	loadingWeather.value = true
	uni.getLocation({
		type: 'wgs84',
		success: (res) => {
			fetchWeatherForCoords(res.latitude, res.longitude)
		},
		fail: () => {
			fetchWeatherForCoords(DEFAULT_LAT, DEFAULT_LON)
		}
	})
}

onMounted(() => {
	tryFetchWeather()
	fetchMyWardrobe()
})

watch(() => props.isLoggedIn, (loggedIn) => {
	if (loggedIn) {
		tryFetchWeather()
		fetchMyWardrobe()
	}
})

const chatHistory = ref([])
const scrollTarget = ref('')
const justCreatedConversation = ref(false)
const loadingStep = ref(0)
const loadingProgress = ref(0)
const loadingProgressPercent = computed(() => Math.floor(loadingProgress.value))
let progressTimer = null

// --- AI 單品 ID -> 衣櫥真實圖片 對應（僅依靠 clothingId 精準匹配）---
const myWardrobeList = ref([])

function getAuthToken() {
	// 與 MyWardrobe/WardrobeView.vue 對齊
	return uni.getStorageSync('auth_token') || ''
}

function buildImageUrl(imageUrl) {
	if (!imageUrl) return ''
	if (imageUrl.startsWith('http')) return imageUrl
	if (imageUrl.startsWith('/')) return `${API_BASE_URL}${imageUrl}`
	return `${API_BASE_URL}/${imageUrl}`
}

async function fetchMyWardrobe() {
	if (!props.isLoggedIn) {
		myWardrobeList.value = []
		return
	}
	const token = getAuthToken()
	if (!token) return
	try {
		const res = await getClothingList({
			token,
			page: 1,
			// 后端限制 page_size <= 100（否则 422）
			page_size: 100,
			order_by: 'created_at',
			order_desc: true
		})
		if (res?.statusCode === 200 && res?.data?.success) {
			const items = res.data?.data?.items || []
			myWardrobeList.value = items.map(it => ({
				id: (it.id != null && it.id !== '' ? Number(it.id) : null),
				name: it.name || '',
				category: it.category || '',
				subcategory: it.subcategory || '',
				color: it.color || '',
				tags: Array.isArray(it.tags) ? it.tags : [],
				description: it.description || '',
				image_url: it.image_url || '',
				image: buildImageUrl(it.image_url || '')
			}))
		}
	} catch (err) {
		console.warn('[RecommendationAI] 拉取衣櫥資料失敗', err?.message || err)
	}
}

function attachImagesToAiMessage(msg) {
	if (!msg || msg.role !== 'ai') return msg
	if (!Array.isArray(myWardrobeList.value) || myWardrobeList.value.length === 0) return msg

	const processItems = (items) => {
		if (!Array.isArray(items)) return
		for (const item of items) {
			// 保底：若後端未解析 clothingId，但 name 仍帶 (ID: 123)，前端只做 ID 抽取（不做名稱模糊匹配）
			let id = item?.clothingId
			if ((id == null || id === '') && typeof item?.name === 'string') {
				const m = item.name.match(/[\(（]\s*id\s*[:：]\s*(\d+)\s*[\)）]/i)
				if (m) id = Number(m[1])
			}

			// 标记“用户上传图片”等特殊项（无 ID 且名称中含 uploaded/上传/None）
			if (
				item?.name &&
				(typeof item.name === 'string') &&
				(
					item.name.includes('上传') ||
					item.name.toLowerCase().includes('uploaded') ||
					((id == null || id === '') && /id\s*[:：]\s*(None|null|uploaded)/i.test(item.name))
				)
			) {
				item.isUploaded = true
			}

			// 清理展示名称中的 (ID: xxx)
			if (typeof item?.name === 'string') {
				item.name = item.name.replace(/\s*[\(（]\s*id\s*[:：]\s*[A-Za-z0-9_]+\s*[\)）]\s*/gi, '').trim()
			}

			if (id == null || id === '') continue
			const needle = Number(id)
			if (!Number.isFinite(needle)) continue
			const cloth = myWardrobeList.value.find(c => Number(c?.id) === needle)
			if (!cloth || !cloth.image) continue

			// 精準 ID 命中：直接覆寫圖片字段
			item.image = cloth.image
			item.images = [cloth.image]
		}
	}

	// plan：day.items[*].images
	if (msg.renderType === 'plan' && Array.isArray(msg?.plan?.days)) {
		for (const day of msg.plan.days) {
			processItems(day?.items)
		}
	}

	// recommendation：recommendations[*].items[*].images（兼容後端/前端解析結構）
	if (Array.isArray(msg?.recommendations)) {
		for (const rec of msg.recommendations) {
			processItems(rec?.items)

			// 将本推荐方案内所有单品图片汇总到 rec.images，供画廊显示
			const itemImages = (rec?.items || []).map(i => i.image).filter(Boolean)
			if (itemImages.length > 0) {
				const existing = Array.isArray(rec.images) ? rec.images : []
				const merged = [...new Set([...existing, ...itemImages])]
				rec.images = merged
			}
		}
	}

	return msg
}

function normalizeHistoryMessage(msg) {
	if (!msg || typeof msg !== 'object') return msg

	if (msg.role === 'ai') {
		let normalized = normalizeChatResponse(msg)
		// 关键：历史消息也需要附加图片
		normalized = attachImagesToAiMessage(normalized)
		return normalized
	}

	if (msg.role === 'user') {
		return {
			role: 'user',
			content: msg.content || '',
			images: Array.isArray(msg.images) ? msg.images : []
		}
	}

	return msg
}

const getRecommendations = (msg) => {
	if (Array.isArray(msg?.recommendations) && msg.recommendations.length > 0) {
		return msg.recommendations
	}

	const items = (msg?.outfitItems || []).map(it => ({
		type: it.category,
		name: it.name,
		reason: it.desc,
		details: it.details
	}))

	if (msg?.list && msg.list.length > 0 && items.length === 0) {
		msg.list.forEach(t => items.push({ type: 'Item', name: t, reason: '' }))
	}

	const tags = msg?.tags || []
	const tempTag = tags.find(t => /°C|℃/.test(t))
	const styleTags = tags.filter(t => t !== tempTag)

	const rec = {
		title: styleTags[0] || '',
		temperature: tempTag || '',
		styleTags,
		content: msg?.content || '',
		items,
		whyThisWorks: msg?.whyThisWorks || [],
		images: msg?.images || []
	}

	return items.length > 0 || (rec.images && rec.images.length > 0) ? [rec] : []
}

const getMessageRenderType = (msg) => {
	if (msg?.renderType) return msg.renderType

	if (msg?.plan && Array.isArray(msg.plan.days) && msg.plan.days.length > 0) return 'plan'

	const recs = getRecommendations(msg)
	if (recs.length > 0) return 'recommendation'
	return 'text'
}

const getDisplayContent = (msg) => {
	return msg?.rawText || msg?.content || ''
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
			chatHistory.value = conv.messages.length
				? conv.messages.map(normalizeHistoryMessage)
				: []
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

const scrollToBottom = () => {
	nextTick(() => {
		scrollTarget.value = 'bottom-spacer'
		setTimeout(() => {
			scrollTarget.value = ''
		}, 100)
	})
}

const handleSearch = async () => {
	if (!props.isLoggedIn) {
		uni.showToast({ title: 'Please log in first', icon: 'none' })
		return
	}

	const query = searchQuery.value.trim()
	const hasImages = uploadedImages.value.length > 0
	if (!query && !hasImages) return

	const isNewSession = props.currentConversationId === null || props.currentConversationId === undefined
	const isPendingSession = props.currentConversationId && !props.currentConversation
	const isFirstMessageInConversation = props.currentConversationId && (props.currentConversation?.messages?.length === 0)

	hasSearched.value = true

	const imagesToSend = uploadedImages.value.length > 0 ? [...uploadedImages.value] : undefined
	const userMsg = { role: 'user', content: query, images: imagesToSend }
	chatHistory.value.push(userMsg)

	if (isNewSession || isPendingSession) {
		const title = (query || '新对话').slice(0, 36)
		const payload = { title, firstMessage: userMsg }
		if (isPendingSession) payload.id = props.currentConversationId
		emit('create-conversation', payload)
		justCreatedConversation.value = true
	}

	searchQuery.value = ''
	uploadedImages.value = []
	scrollToBottom()

	chatHistory.value.push({ role: 'loading', content: '' })
	loadingStep.value = 0
	loadingProgress.value = 0
	scrollToBottom()

	const stepInterval = setInterval(() => {
		loadingStep.value = (loadingStep.value + 1) % LOADING_STEPS.length
	}, 800)

	const progressStartAt = Date.now()
	progressTimer = setInterval(() => {
		const elapsed = Date.now() - progressStartAt

		// 分段“假进度”节奏：前期快、中期卡一会、后期慢慢逼近 95
		let cap = 95
		let factor = 0.08
		let stallChance = 0

		if (elapsed < 650) {
			// 0-0.65s：先“起步犹豫”一小下（更像真实）
			cap = 22
			factor = 0.16
			stallChance = 0.25
		} else if (elapsed < 1400) {
			// 0.65-1.4s：快速拉升到 ~60
			cap = 60
			factor = 0.26
			stallChance = 0.08
		} else if (elapsed < 2400) {
			// 1.4-2.4s：早期再轻微卡一下（停在 60-68）
			cap = 68
			factor = 0.06
			stallChance = 0.18
		} else if (elapsed < 5200) {
			// 1.2-5.2s：中段放缓，停留在 75-88 区间更久
			cap = 88
			factor = 0.035
			stallChance = 0.12
		} else {
			// 5.2s+：最后非常缓慢逼近 95
			cap = 95
			factor = 0.018
			stallChance = 0.06
		}

		const remaining = cap - loadingProgress.value
		if (remaining > 0.2) {
			// 让进度“非匀速”：用轻微波动 + 偶发停顿制造真实感（且保持单调递增）
			if (stallChance > 0 && Math.random() < stallChance) return
			const wobble = 0.75 + 0.25 * Math.sin(elapsed / 230)
			loadingProgress.value += remaining * factor * wobble
			if (loadingProgress.value > cap) loadingProgress.value = cap
		}
	}, 150)

	const finishLoading = (aiMessage) => {
		clearInterval(stepInterval)
		clearInterval(progressTimer)
		progressTimer = null
		loadingProgress.value = 100

		setTimeout(() => {
			let normalized = normalizeChatResponse(aiMessage)
			normalized = attachImagesToAiMessage(normalized)

			// 用 AI 消息替换 loading 消息，避免“先删再加”导致视觉断层
			const loadingIdx = chatHistory.value.findIndex(msg => msg.role === 'loading')
			if (loadingIdx !== -1) {
				chatHistory.value.splice(loadingIdx, 1, normalized)
			} else {
				chatHistory.value.push(normalized)
			}

			justCreatedConversation.value = false

			const cid = props.currentConversationId
			if (cid) {
				const payload = { id: cid, messages: [...chatHistory.value] }
				if (isFirstMessageInConversation) payload.title = (query || '新对话').slice(0, 36)
				emit('update-conversation', payload)
			}
			scrollToBottom()
		}, 300)
	}

	const history = chatHistory.value
		.slice(0, -2)
		.filter(m => m.role === 'user' || m.role === 'ai')
		.map(m => ({
			role: m.role,
			content: (m.rawText || m.content || '').trim()
		}))
		.filter(m => m.content)

	try {
		const res = await chatRecommendation(query, history)
		finishLoading(res)
	} catch (err) {
		finishLoading({
			role: 'ai',
			content: '请求失败：' + (err && err.message ? err.message : '网络错误')
		})
		uni.showToast({ title: '推荐请求失败', icon: 'none' })
	}
}

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
	const rawFiles = e.dataTransfer?.files || e.originalEvent?.dataTransfer?.files
	if (!rawFiles || !rawFiles.length) return

	const remain = MAX_UPLOAD_IMAGES - uploadedImages.value.length
	if (remain <= 0) {
		uni.showToast({ title: `最多只能上传 ${MAX_UPLOAD_IMAGES} 张图片`, icon: 'none' })
		return
	}

	const files = Array.from(rawFiles)
		.filter(f => f.type && f.type.startsWith('image/'))
		.slice(0, remain)

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

const previewImageAt = (index) => {
	const urls = uploadedImages.value
	if (!urls || urls.length === 0) return
	uni.previewImage({
		current: urls[index],
		urls
	})
}

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
.chat-container::before {
	content: '';
	position: absolute;
	inset: 0;
	pointer-events: none;
	background: 
		radial-gradient(ellipse 80% 50% at 20% 20%, rgba(240, 235, 225, 0.6), transparent),
		radial-gradient(ellipse 60% 40% at 80% 80%, rgba(230, 220, 210, 0.4), transparent),
		radial-gradient(ellipse 50% 60% at 60% 30%, rgba(250, 245, 238, 0.5), transparent);
	animation: meshFloat 18s ease-in-out infinite;
}
@keyframes meshFloat {
	0%, 100% { opacity: 1; transform: scale(1) translate(0, 0); }
	33% { opacity: 0.95; transform: scale(1.02) translate(2%, 1%); }
	66% { opacity: 1; transform: scale(0.98) translate(-1%, 2%); }
}

.mixed-message-wrap {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	width: 100%;
}

/* 1. 将上方的文字气泡改造成“后台思考/分析记录” */
.mixed-message-wrap :deep(.chat-bubble) {
	background: transparent !important;
	box-shadow: none !important;
	border: none !important;
	padding: 12rpx 20rpx 12rpx 32rpx;
	border-left: 6rpx solid rgba(157, 139, 112, 0.3) !important;
	border-radius: 0 !important;
	margin: 0 0 16rpx 12rpx;
}

.mixed-message-wrap :deep(.chat-bubble)::before {
	content: '💭 AI Analysis & Strategy';
	display: flex;
	align-items: center;
	font-size: 22rpx;
	color: #9D8B70;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.06em;
	margin-bottom: 16rpx;
	font-family: "Didot", serif;
	opacity: 0.8;
}

/* 2. 弱化思考文字的字号和颜色，拉开与正式卡片的层级差距 */
.mixed-message-wrap :deep(.chat-bubble .message-text),
.mixed-message-wrap :deep(.chat-bubble .rich-text) {
	font-size: 26rpx !important;
	color: #8E8E93 !important;
	line-height: 1.6 !important;
}

.mixed-message-wrap :deep(.chat-bubble .highlight-text) {
	background: none !important;
	color: #6C6C70 !important;
	font-weight: 600 !important;
	padding: 0 !important;
}

/* 3. 确保推荐卡片（正式结果）恢复完整的圆角和阴影 */
.mixed-message-wrap :deep(.recommend-card) {
	border-radius: 40rpx !important;
	border-top: 1px solid rgba(255, 255, 255, 0.9) !important;
	box-shadow: 0 16rpx 60rpx rgba(0, 0, 0, 0.05) !important;
}

.cards-area {
	width: 100%;
}

.ai-content {
	width: 100%;
	max-width: calc(100% - 70rpx);
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.recommend-swiper {
	width: 100%;
	min-height: 720rpx;
}

/* 初始状态：整体滚动区（问候语与输入框同步上移） */
.initial-scroll {
	width: 100%;
	height: 100vh;
	position: relative;
	z-index: 1;
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

/* 高级毛玻璃 Loading 卡片 */
.loading-premium-card {
	position: relative;
	width: 100%;
	min-height: 400rpx;
	background: rgba(255, 255, 255, 0.4);
	backdrop-filter: blur(20px);
	-webkit-backdrop-filter: blur(20px);
	border-radius: 40rpx;
	border: 1px solid rgba(255, 255, 255, 0.8);
	overflow: hidden;
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	box-shadow: 0 16rpx 60rpx rgba(0, 0, 0, 0.03);
}

/* 核心：极其细腻的斜向流光扫过卡片 */
.shimmer-layer {
	position: absolute;
	inset: 0;
	background: linear-gradient(
		120deg,
		rgba(255, 255, 255, 0) 0%,
		rgba(255, 255, 255, 0.8) 50%,
		rgba(255, 255, 255, 0) 100%
	);
	background-size: 200% 100%;
	animation: premiumShimmer 2.5s infinite linear;
	z-index: 1;
}

@keyframes premiumShimmer {
	0% { background-position: -200% 0; }
	100% { background-position: 200% 0; }
}

/* 内部文字布局 */
.loading-content-center {
	position: relative;
	z-index: 2;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 16rpx;
}

/* 光晕环：柔和呼吸光圈 */
.aura-ring {
	width: 80rpx;
	height: 80rpx;
	border-radius: 50%;
	background: radial-gradient(circle, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.3) 50%, transparent 70%);
	animation: auraPulse 2.5s ease-in-out infinite;
}

@keyframes auraPulse {
	0%, 100% { transform: scale(1); opacity: 0.6; }
	50% { transform: scale(1.15); opacity: 1; }
}

/* 衬线体排版，增加呼吸感 */
.editorial-text {
	font-family: "Didot", "Times New Roman", "PingFang SC", serif;
	font-size: 36rpx;
	color: #1D1D1F;
	letter-spacing: 0.05em;
	animation: textBreath 3s ease-in-out infinite;
}

.loading-step-text {
	font-size: 28rpx;
	color: #9D8B70;
	font-family: "Didot", "Times New Roman", "PingFang SC", serif;
	font-weight: 400;
	letter-spacing: 0.04em;
}

.loading-sub-text {
	font-size: 24rpx;
	color: #9D8B70;
	letter-spacing: 0.1em;
	text-transform: uppercase;
	opacity: 0.7;
}

@keyframes textBreath {
	0%, 100% { transform: scale(1); opacity: 0.8; letter-spacing: 0.05em; }
	50% { transform: scale(1.02); opacity: 1; letter-spacing: 0.08em; }
}

/* 底部骨架屏：增加真实感 */
.skeleton-lines {
	position: absolute;
	bottom: 60rpx;
	left: 60rpx;
	right: 60rpx;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	opacity: 0.3;
	z-index: 2;
}

.skeleton-line {
	height: 12rpx;
	background: #EAE5D9;
	border-radius: 10rpx;
}

.skeleton-line.short { width: 30%; }
.skeleton-line.long { width: 80%; }
.skeleton-line.medium { width: 60%; }

/* 实时进度条：渐进式阻尼 + 能量光效 */
.loading-progress-wrap {
	position: relative;
	z-index: 2;
	width: 100%;
	padding: 0 60rpx;
	box-sizing: border-box;
	display: flex;
	align-items: center;
	gap: 24rpx;
	margin-top: 32rpx;
}
.loading-progress-track {
	flex: 1;
	height: 6rpx;
	background: rgba(157, 139, 112, 0.15);
	border-radius: 6rpx;
	overflow: hidden;
	position: relative;
}
.loading-progress-fill {
	height: 100%;
	background: linear-gradient(90deg, #9D8B70 0%, #C4B59D 50%, #9D8B70 100%);
	background-size: 200% 100%;
	border-radius: 6rpx;
	transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	animation: gradientFlow 2s linear infinite;
	position: relative;
}
.loading-progress-fill::after {
	content: '';
	position: absolute;
	right: 0;
	top: -2rpx;
	bottom: -2rpx;
	width: 20rpx;
	background: #FFF;
	box-shadow: 0 0 10rpx 4rpx rgba(255, 255, 255, 0.8);
	border-radius: 50%;
	filter: blur(2px);
}
@keyframes gradientFlow {
	0% { background-position: 100% 0; }
	100% { background-position: -100% 0; }
}
.loading-progress-label {
	font-size: 20rpx;
	color: #9D8B70;
	font-variant-numeric: tabular-nums;
	min-width: 56rpx;
	text-align: right;
	font-weight: 500;
}

/* 聊天状态：scroll-view 区域 */
.chat-scroll-area {
	position: relative;
	z-index: 1;
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
