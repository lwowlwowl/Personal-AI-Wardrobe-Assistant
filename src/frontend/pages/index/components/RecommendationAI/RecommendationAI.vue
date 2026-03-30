<!-- Recommendation AI chat: greeting, multiline input, images, user/AI messages -->
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
						<text class="greeting-text">Hi! {{ timeGreeting }}</text>
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
					<InputBar
						v-model="searchQuery"
						:images="uploadedImages"
						:is-drag-over="isDragOverInput"
						@apply-text="onSuggestionApplyText"
						@search="handleSearch"
						@add="handleAdd"
						@drop="handleDropImage"
						@dragover="handleDragOverInput"
						@dragleave="handleDragLeaveInput"
						@preview-thumb="previewImageAt"
						@remove-thumb="removeUploadedImageAt"
					/>
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
							<!-- Plan schedule (multi-day / multi-scene / calendar-style) -->
							<PlanScheduleCard
								v-if="getMessageRenderType(msg) === 'plan'"
								:plan="msg.plan"
								:raw-text="msg.rawText || msg.content || ''"
								:locale="msg.locale || 'en'"
							/>

							<!-- Recommendation: optional text above + cards below, same wrapper -->
							<view
								v-else-if="getMessageRenderType(msg) === 'recommendation'"
								class="mixed-message-wrap"
								:key="msg.rawText || msg.content || `rec-${index}`"
							>
								<ChatMessageBubble
									v-if="msg.content"
									:content="msg.content"
									strip-wardrobe-hash-ids
								/>
								<view class="cards-area">
									<view v-if="getRecommendations(msg).length > 1" class="recommend-list">
										<RecommendationCard
											v-for="(rec, ri) in getRecommendations(msg)"
											:key="ri"
											:recommendation="rec"
											:show-regenerate="shouldShowRegenerateOnRecommendation(msg, ri)"
											:locale="msg.locale || 'en'"
											@regenerate="handleRegenerate(index)"
											@preview-images="previewImages"
											@virtual-try-on="handleRecommendationVirtualTryOn"
											@add-to-calendar="handleAddRecommendationToCalendar"
											@full-outfit-try-on="handleFullOutfitTryOn"
										/>
									</view>
									<RecommendationCard
										v-else-if="getRecommendations(msg).length === 1"
										:recommendation="getRecommendations(msg)[0]"
										:show-regenerate="true"
										:locale="msg.locale || 'en'"
										@regenerate="handleRegenerate(index)"
										@preview-images="previewImages"
										@virtual-try-on="handleRecommendationVirtualTryOn"
										@add-to-calendar="handleAddRecommendationToCalendar"
										@full-outfit-try-on="handleFullOutfitTryOn"
									/>
								</view>
							</view>

							<!-- Plain text / fallback -->
							<ChatMessageBubble
								v-else
								:key="msg.rawText || msg.content || `text-${index}`"
								:content="getDisplayContent(msg)"
							/>
						</view>
					</view>

					<view v-if="msg.role === 'loading'" class="ai-container ai-fade-in">
						<view class="ai-avatar">
							<image src="/static/icons/icon-robot.svg" mode="aspectFit" class="icon-robot-avatar"></image>
						</view>
						<LoadingPanel :ref="setLoadingPanelRef" />
					</view>
				</view>

				<view class="spacer" id="bottom-spacer"></view>
			</view>
		</scroll-view>

		<view v-if="hasSearched" class="input-box-wrapper">
			<view class="input-container fixed-bottom">
				<InputBar
					v-model="searchQuery"
					:images="uploadedImages"
					:is-drag-over="isDragOverInput"
					@apply-text="onSuggestionApplyText"
					@search="handleSearch"
					@add="handleAdd"
					@drop="handleDropImage"
					@dragover="handleDragOverInput"
					@dragleave="handleDragLeaveInput"
					@preview-thumb="previewImageAt"
					@remove-thumb="removeUploadedImageAt"
				/>
			</view>

		</view>
	</view>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import RecommendationCard from './chat-content/RecommendationCard.vue'
import ChatMessageBubble from './chat-content/ChatMessageBubble.vue'
import PlanScheduleCard from './chat-content/PlanScheduleCard.vue'
import { normalizeChatResponse } from './utils/chat/chatContentAdapter.js'
import { todayKey } from './utils/common/dates.js'
import { recTryOnImageUrl, recClothingId, stripRecItemNameId } from './utils/rec/recItem.js'
import { expandEmbeddedJsonAiMessage } from './utils/chat/aiJson.js'
import { attachWardrobeToAiMessage } from './utils/chat/wardrobeImages.js'
import {
	getRecommendations,
	getMessageRenderType,
	getDisplayContent,
	shouldShowRegenerateOnRecommendation
} from './utils/chat/msgRender.js'
import { normalizeHistoryMsg } from './utils/chat/historyMsg.js'
import { regenerateSuffix } from './utils/common/regenerate.js'
import LoadingPanel from './chat-content/LoadingPanel.vue'
import InputBar from './InputBar.vue'
import { chatRecommendation, getWeatherNow, getAuthToken } from '@/api/recommendationApi.js'
import { getClothingList, getPrimaryModelPhoto } from '@/api/wardrobe.js'
import { resolveWardrobeImageUrl, isPlaceholderWardrobeUrl } from '@/api/wardrobeMedia.js'
import { getCalendarOutfits, saveCalendarOutfits } from '@/api/calendarApi.js'
import { getOutfitTryOnSortIndex, buildOutfitTryOnStepLabel } from './utils/rec/outfitOrder.js'

const timeGreeting = computed(() => {
	const h = new Date().getHours()
	if (h >= 5 && h < 12) return 'Good Morning'
	if (h >= 12 && h < 17) return 'Good Afternoon'
	if (h >= 17 && h < 22) return 'Good Evening'
	return 'Good Night'
})

const props = defineProps({
	isLoggedIn: { type: Boolean, default: false },
	// Parent may pass numeric id; accept string or number to avoid prop warnings
	currentConversationId: { type: [String, Number], default: null },
	currentConversation: { type: Object, default: null }
})

const emit = defineEmits(['create-conversation', 'update-conversation', 'switch-to-tryon', 'switch-to-full-outfit-tryon', 'calendar-updated'])

const handleRecommendationVirtualTryOn = async (item) => {
	if (!item?.image) {
		uni.showToast({ title: 'No image for this item — try-on needs a photo.', icon: 'none' })
		return
	}
	const defaultPersonImage = await fetchPrimaryModelImageUrl()
	emit('switch-to-tryon', item, defaultPersonImage)
}

const handleFullOutfitTryOn = async (recommendation) => {
	if (!props.isLoggedIn) {
		uni.showToast({ title: 'Please log in first', icon: 'none' })
		return
	}
	const items = recommendation?.items
	if (!Array.isArray(items) || items.length === 0) {
		uni.showToast({ title: 'No items in this look', icon: 'none' })
		return
	}
	const decorated = items
		.map((it, idx) => ({ it, idx, url: recTryOnImageUrl(it) }))
		.filter((x) => x.url)
	if (decorated.length === 0) {
		uni.showToast({ title: 'No images in this look', icon: 'none' })
		return
	}
	decorated.sort((a, b) => {
		const d = getOutfitTryOnSortIndex(a.it.type) - getOutfitTryOnSortIndex(b.it.type)
		if (d !== 0) return d
		return a.idx - b.idx
	})
	const outfitQueue = decorated.map((x) => ({
		image: x.url,
		label: buildOutfitTryOnStepLabel(x.it)
	}))
	const personImage = await fetchPrimaryModelImageUrl()
	emit('switch-to-full-outfit-tryon', { personImage, outfitQueue })
}

async function handleAddRecommendationToCalendar(recommendation) {
	const token = getAuthToken()
	if (!props.isLoggedIn || !token) {
		uni.showToast({ title: 'Please log in first', icon: 'none' })
		return
	}
	const recItems = recommendation?.items
	if (!Array.isArray(recItems) || recItems.length === 0) {
		uni.showToast({ title: 'No items in this look', icon: 'none' })
		return
	}
	await fetchMyWardrobe()

	const newById = new Map()
	for (const item of recItems) {
		const cid = recClothingId(item)
		if (cid == null || newById.has(cid)) continue
		const cloth = myWardrobeList.value.find(c => Number(c?.id) === cid)
		const rawName = cloth?.name || item.name || 'Item'
		const name = stripRecItemNameId(rawName)
		let image = cloth?.image || item.image || ''
		if (image) image = resolveWardrobeImageUrl(image)
		newById.set(cid, {
			id: cid,
			name,
			image,
			accentColor: '#8d6e63'
		})
	}
	if (newById.size === 0) {
		uni.showToast({ title: 'No wardrobe-linked items in this recommendation', icon: 'none' })
		return
	}

	const today = new Date()
	const dateKey = todayKey()
	const year = today.getFullYear()
	const month = today.getMonth() + 1

	try {
		const res = await getCalendarOutfits({ token, year, month })
		const merged = new Map()
		if (res.statusCode === 200 && res.data?.success && res.data.data?.outfits) {
			const existing = res.data.data.outfits[dateKey] || []
			for (const e of existing) {
				if (e.id == null) continue
				const id = Number(e.id)
				if (!Number.isFinite(id)) continue
				let img = e.image || ''
				if (img) img = resolveWardrobeImageUrl(img)
				merged.set(id, {
					id,
					name: e.name || '',
					image: img,
					accentColor: e.accentColor || '#8d6e63'
				})
			}
		}
		for (const [id, entry] of newById) {
			merged.set(id, entry)
		}
		const payload = [...merged.values()]
		const saveRes = await saveCalendarOutfits({ token, date: dateKey, items: payload })
		if (saveRes.statusCode === 200 && saveRes.data?.success) {
			uni.showToast({ title: 'Added to today on calendar', icon: 'success' })
			emit('calendar-updated')
		} else {
			const msg = saveRes.data?.detail || saveRes.data?.message || 'Could not save calendar'
			uni.showToast({ title: typeof msg === 'string' ? msg : 'Could not save calendar', icon: 'none' })
		}
	} catch (e) {
		uni.showToast({ title: 'Could not save calendar', icon: 'none' })
	}
}

const searchQuery = ref('')
const hasSearched = ref(false)

/** Only writes suggestion into main input; does not call handleSearch or change hasSearched */
const onSuggestionApplyText = (text) => {
	searchQuery.value = text
}

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
		console.warn('[RecommendationAI] Weather request failed', err?.message || err)
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
const loadingPanelRef = ref(null)

function setLoadingPanelRef(el) {
	loadingPanelRef.value = el
}

// --- Map AI item id -> wardrobe image (match by clothingId only) ---
const myWardrobeList = ref([])

function buildImageUrl(imageUrl) {
	if (imageUrl == null || imageUrl === '') return ''
	return resolveWardrobeImageUrl(imageUrl)
}

async function fetchPrimaryModelImageUrl() {
	const token = getAuthToken()
	if (!token) return null
	try {
		const res = await getPrimaryModelPhoto(token)
		if (res?.statusCode !== 200 || !res.data?.success || !res.data?.data) return null
		const photo = res.data.data
		const raw = photo.image_url || photo.imageUrl || ''
		const url = buildImageUrl(raw)
		if (!raw || !url || isPlaceholderWardrobeUrl(url)) return null
		return url
	} catch {
		return null
	}
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
			// Backend caps page_size at 100 (else 422)
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
		console.warn('[RecommendationAI] Failed to load wardrobe data', err?.message || err)
	}
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
				? conv.messages.map((m) => normalizeHistoryMsg(m, myWardrobeList.value))
				: []
			hasSearched.value = chatHistory.value.length > 0
		} else {
			chatHistory.value = []
			hasSearched.value = false
		}
	},
	{ immediate: true }
)

const scrollToBottom = () => {
	nextTick(() => {
		scrollTarget.value = 'bottom-spacer'
		setTimeout(() => {
			scrollTarget.value = ''
		}, 100)
	})
}

/** After Regenerate in long chats, height jumps can mis-scroll; anchor to this message-row to keep focus */
const scrollToMessageIndex = (idx) => {
	if (idx == null || idx < 0) return
	nextTick(() => {
		scrollTarget.value = 'msg-' + idx
		setTimeout(() => {
			scrollTarget.value = ''
		}, 150)
	})
}

/**
 * After stream: wait for loading animation, parse JSON, normalize, replace loading row (shared by handleSearch / regenerate).
 * @param {{ scrollAfter?: boolean, anchorMsgIdx?: number, replaceAtIndex?: number }} [options] — pass replaceAtIndex to avoid replacing the wrong loading row when several exist
 */
async function replaceLoadingWithAiMessage(aiMessage, options = {}) {
	const { scrollAfter = true, anchorMsgIdx, replaceAtIndex } = options
	const panel = loadingPanelRef.value
	if (panel && typeof panel.complete === 'function') {
		await panel.complete()
	} else {
		await new Promise((r) => setTimeout(r, 300))
	}

	const toNormalize = expandEmbeddedJsonAiMessage(aiMessage)
	let normalized = normalizeChatResponse(toNormalize)
	normalized = attachWardrobeToAiMessage(normalized, myWardrobeList.value)

	let loadingIdx = -1
	if (replaceAtIndex != null && chatHistory.value[replaceAtIndex]?.role === 'loading') {
		loadingIdx = replaceAtIndex
	} else {
		for (let i = chatHistory.value.length - 1; i >= 0; i--) {
			if (chatHistory.value[i].role === 'loading') {
				loadingIdx = i
				break
			}
		}
	}
	if (loadingIdx !== -1) {
		chatHistory.value.splice(loadingIdx, 1, normalized)
	} else {
		chatHistory.value.push(normalized)
	}
	if (scrollAfter) {
		scrollToBottom()
	} else if (anchorMsgIdx != null) {
		scrollToMessageIndex(anchorMsgIdx)
	}
}

const handleRegenerate = async (msgIdx) => {
	if (!props.isLoggedIn) {
		uni.showToast({ title: 'Please log in first', icon: 'none' })
		return
	}
	const prevAi = chatHistory.value[msgIdx]
	if (prevAi?.role !== 'ai') return

	let userIdx = msgIdx - 1
	while (userIdx >= 0 && chatHistory.value[userIdx].role !== 'user') {
		userIdx -= 1
	}
	if (userIdx < 0) {
		uni.showToast({ title: 'Cannot find the question for this reply', icon: 'none' })
		return
	}

	const userMsg = chatHistory.value[userIdx]
	const locale = prevAi?.locale
	const isZh = locale === 'zh' || locale === 'zh-CN' || locale === 'zh_CN'
	const userText = (userMsg.content || '').trim()
	const regHint = regenerateSuffix(isZh)

	let query = userText
	if (!query) {
		query = (isZh ? '请继续根据对话上下文回答。' : 'Please continue based on the conversation context.') + regHint
	} else {
		query = query + regHint
	}

	chatHistory.value[msgIdx] = { role: 'loading', content: '' }
	scrollToMessageIndex(msgIdx)

	const history = chatHistory.value
		.slice(0, userIdx)
		.filter(m => m.role === 'user' || m.role === 'ai')
		.map(m => ({
			role: m.role,
			content: (m.rawText || m.content || '').trim()
		}))
		.filter(m => m.content)

	// Send previous assistant full text so the model has context; prevAi is still the pre-replace object
	const prevBody = (prevAi.rawText || prevAi.content || '').trim()
	if (prevBody) {
		const cap = 20000
		history.push({
			role: 'ai',
			content: prevBody.length > cap ? prevBody.slice(0, cap) + '\n…(truncated)' : prevBody
		})
	}

	const finishRegenerate = async (aiMessage) => {
		await replaceLoadingWithAiMessage(aiMessage, {
			scrollAfter: false,
			anchorMsgIdx: msgIdx,
			replaceAtIndex: msgIdx
		})
		justCreatedConversation.value = false
		const cid = props.currentConversationId
		if (cid) {
			emit('update-conversation', { id: cid, messages: [...chatHistory.value] })
		}
	}

	try {
		const res = await chatRecommendation(query, history)
		await finishRegenerate(res)
	} catch (err) {
		const reason = (err && err.message) || 'Network or server error.'
		await finishRegenerate({
			role: 'ai',
			content: 'Request failed: ' + reason
		})
		uni.showToast({
			title: reason.length > 120 ? reason.slice(0, 117) + '…' : reason,
			icon: 'none',
			duration: 4000
		})
	}
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
		const title = (query || 'New chat').slice(0, 36)
		const payload = { title, firstMessage: userMsg }
		if (isPendingSession) payload.id = props.currentConversationId
		emit('create-conversation', payload)
		justCreatedConversation.value = true
	}

	searchQuery.value = ''
	uploadedImages.value = []
	scrollToBottom()

	chatHistory.value.push({ role: 'loading', content: '' })
	const loadingRowIndex = chatHistory.value.length - 1
	scrollToBottom()

	// After API: replace placeholder with final structured message (replace, not append)
	const finishLoading = async (aiMessage) => {
		await replaceLoadingWithAiMessage(aiMessage, { replaceAtIndex: loadingRowIndex })

		justCreatedConversation.value = false

		const cid = props.currentConversationId
		if (cid) {
			const payload = { id: cid, messages: [...chatHistory.value] }
			if (isFirstMessageInConversation) payload.title = (query || 'New chat').slice(0, 36)
			emit('update-conversation', payload)
		}
		scrollToBottom()
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
		await finishLoading(res)
	} catch (err) {
		const reason = (err && err.message) || 'Network or server error.'
		await finishLoading({
			role: 'ai',
			content: 'Request failed: ' + reason
		})
		uni.showToast({
			title: reason.length > 120 ? reason.slice(0, 117) + '…' : reason,
			icon: 'none',
			duration: 4000
		})
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
		uni.showToast({ title: `You can upload at most ${MAX_UPLOAD_IMAGES} images`, icon: 'none' })
		return
	}

	const files = Array.from(rawFiles)
		.filter(f => f.type && f.type.startsWith('image/'))
		.slice(0, remain)

	if (files.length === 0) {
		uni.showToast({ title: 'Please drop image files', icon: 'none' })
		return
	}

	if (typeof URL === 'undefined' || !URL.createObjectURL) return
	const add = files.map(f => URL.createObjectURL(f))
	uploadedImages.value = [...uploadedImages.value, ...add]
}

/** Album/camera: InputBar does not emit('add') yet (Add photos menu removed); handlers kept for later. H5: drag images onto input. */
const handleAdd = () => {
	const remain = MAX_UPLOAD_IMAGES - uploadedImages.value.length
	if (remain <= 0) {
		uni.showToast({
			title: `You can upload at most ${MAX_UPLOAD_IMAGES} images`,
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
					title: `You can upload at most ${MAX_UPLOAD_IMAGES} images; added ${remain}`,
					icon: 'none',
					duration: 2500
				})
			}
		},
		fail: (err) => {
			console.error('[RecommendationAI] chooseImage failed:', err)
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
/* Root chat container */
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

/* 1. Top bubble: backstage analysis / strategy tone */
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
	content: 'AI Analysis & Strategy';
	display: flex;
	align-items: center;
	font-size: 22rpx;
	color: #9D8B70;
	font-weight: 900;
	text-transform: uppercase;
	letter-spacing: 0.06em;
	margin-bottom: 16rpx;
	font-family: "Didot", serif;
	opacity: 0.8;
}

/* 2. Softer analysis text vs main cards */
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

/* 3. Full radius + shadow on recommendation cards */
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

.recommend-list {
	width: 100%;
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

/* Initial: full-height scroll (greeting + input move together) */
.initial-scroll {
	width: 100%;
	height: 100vh;
	position: relative;
	z-index: 1;
}

/* Initial content: greeting + input + chips */
.initial-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 40rpx 40rpx 80rpx;
	min-height: 100vh;
	box-sizing: border-box;
}

/* Greeting block */
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

/* Robot icon float / breathe */
.robot-hero .icon-robot-hero {
	width: 60px;
	height: 60px;
	display: block;
	/* 4s loop, smooth easing */
	animation: float 4s ease-in-out infinite;
}
.icon-robot-avatar {
	width: 26px;
	height: 26px;
	display: block;
}

@keyframes float {
	0% { transform: translateY(0px); }
	50% { transform: translateY(-6px); } /* subtle lift */
	100% { transform: translateY(0px); }
}

/* Greeting row: wave emoji + text */
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

/* Weather card: faint + offset while loading; fade in when ready */
.weather-card {
	opacity: 0;
	transform: translateY(6px);
	transition: opacity 260ms ease, transform 260ms ease;
}
.weather-card.ready {
	opacity: 1;
	transform: translateY(0);
}

/* Weather row: temp | condition | wind */
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
	margin: 0 15rpx; /* spacing around | dividers */
	position: relative;
}

/* Chat mode: scroll-view */
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
	padding: 40rpx 40rpx 320rpx 40rpx;
	display: flex;
	flex-direction: column;
	min-height: 100%;
	/* Allow text selection in message list */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* Bottom spacer for fixed input bar */
.spacer {
	height: 320rpx;
}

/* Message rows: left (AI) / right (user) */
.message-row {
	display: flex;
	width: 100%;
	margin-bottom: 60rpx;
}

/* User message (right) */
.message-row.user {
	justify-content: flex-end;
}

.user-bubble {
	background-color: #F2F2F2;
	padding: 24rpx 40rpx;
	border-radius: 40rpx;
	border-bottom-right-radius: 4rpx; /* tail notch */
	max-width: 70%;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	/* User bubble text selectable */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* User message images */
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

/* Message body: clean sans, unified size */
.message-text {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Microsoft YaHei", sans-serif;
	font-weight: 400;
	line-height: 1.6;
	word-wrap: break-word;
	/* Selectable / copyable */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* AI message (left) */
.message-row.ai {
	justify-content: flex-start;
}

.ai-container {
	display: flex;
	gap: 24rpx;
	width: 80%;
	align-items: flex-start;
}

/* AI block fade-in */
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

/* Multi-rec swiper */
.recommend-swiper {
	width: 100%;
	height: auto;
	min-height: 400rpx;
}

.recommend-swiper swiper-item {
	height: auto;
	padding-bottom: 60rpx;
}

/* Input shell: full width, page bg, top padding */
.input-box-wrapper {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	width: 100%;
	padding-top: 50rpx;
	padding-bottom: 56rpx;
	background: linear-gradient(180deg, rgba(253, 251, 247, 0) 0%, rgba(253, 251, 247, 0.82) 34%, rgba(253, 251, 247, 1) 100%);
	display: flex;
	flex-direction: column;
	align-items: center;
	z-index: 10;
	pointer-events: none;
}

/* Input container */
.input-container {
	width: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	transition: all 0.6s cubic-bezier(0.25, 1, 0.5, 1);
	pointer-events: none;
}

/* Initial: in scroll flow with greeting */
.input-container.input-in-flow {
	flex-shrink: 0;
	margin-top: 80rpx;
	pointer-events: auto;
}

/* Chat: bottom area inside input-box-wrapper (no absolute on inner) */
.input-box-wrapper .input-container.fixed-bottom {
	position: relative;
	bottom: auto;
	left: auto;
	transform: none;
}

</style>
