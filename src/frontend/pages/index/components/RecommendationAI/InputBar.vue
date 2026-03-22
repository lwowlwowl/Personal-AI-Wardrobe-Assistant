<!--
  推荐 AI 底部/首屏输入栏：主输入、图片，点「+」展开建议菜单。
  【暂停】菜单内「Add photos」已移除：相册/相机入口之后若要恢复，可再接入 emit('add') 或为「+」加长按/第二按钮。
  目前图片仅能通过拖拽到输入栏（H5）等方式加入（见父组件 handleAdd / handleDropImage）。
-->
<template>
	<view class="recommendation-input-bar">
		<transition name="fade">
			<view
				v-if="suggestionsOpen"
				class="suggestions-backdrop"
				@tap="closeSuggestions"
				@click="closeSuggestions"
			/>
		</transition>

		<transition name="slide-up">
			<view
				v-if="suggestionsOpen"
				class="suggestions-panel"
				@tap.stop
			>
				<view class="panel-head">
					<view class="title-wrap">
						<text class="panel-title">✨ SUGGESTIONS</text>
					</view>
					<view class="panel-close" @tap.stop="closeSuggestions" @click.stop.prevent="closeSuggestions">
						<text class="panel-close-x">×</text>
					</view>
				</view>
				<text class="panel-hint">Click a line to fill the box (does not send). Edit to customize.</text>

				<view class="suggestions-list">
					<view
						v-for="(_, idx) in prompts"
						:key="'p-' + idx"
						class="suggestion-row suggestion-row-reveal"
						:class="{ 'is-editing-row': menuEditIndex === idx }"
						:style="{ animationDelay: idx * 55 + 'ms' }"
					>
						<text class="bullet">•</text>
						<view class="row-main" @tap.stop="onPromptLineTap(idx)" @click.stop="onPromptLineTap(idx)">
							<input
								v-if="menuEditIndex === idx"
								class="row-input"
								type="text"
								:value="editBuffer"
								:focus="menuEditIndex === idx"
								:maxlength="-1"
								@input="onEditInput"
								@blur="scheduleBlurFinish(idx)"
								@confirm="onConfirmEdit(idx)"
								@tap.stop
							/>
							<text v-else class="row-text">{{ prompts[idx] }}</text>
						</view>

						<view
							class="edit-btn"
							:class="{ 'is-active': menuEditIndex === idx }"
							@tap.stop="onEditButtonTap(idx)"
							@click.stop.prevent="onEditButtonTap(idx)"
						>
							<text class="edit-btn-label">{{ menuEditIndex === idx ? 'Done' : 'Edit' }}</text>
						</view>
					</view>
				</view>
			</view>
		</transition>

		<view class="search-bar">
			<div
				class="search-bar-drop-zone"
				:class="{ 'drag-over': isDragOver }"
				@drop.prevent="onDrop"
				@dragover.prevent="onDragOver"
				@dragleave.prevent="onDragLeave"
				@dragenter.prevent
			>
				<view v-if="images.length > 0" class="input-thumb-row">
					<scroll-view class="input-thumb-wrap" scroll-x :show-scrollbar="false">
						<view class="input-thumb-list">
							<view v-for="(url, idx) in images" :key="idx" class="input-thumb-pill">
								<image :src="url" mode="aspectFill" class="input-thumb-img" @click="emit('preview-thumb', idx)"></image>
								<view class="input-thumb-remove" @click.stop="emit('remove-thumb', idx)">
									<image src="/static/icons/icon-close.svg" mode="aspectFit" class="icon-close-small"></image>
								</view>
							</view>
						</view>
					</scroll-view>
				</view>

				<view class="search-input-row">
					<view class="search-icon-left" @click.stop="toggleSuggestionsMenu">
						<image src="/static/icons/icon-plus.svg" mode="aspectFit" class="icon-search-btn"></image>
					</view>
					<textarea
						class="search-input search-textarea"
						:value="modelValue"
						placeholder="Ask me anything!"
						placeholder-class="search-placeholder"
						:maxlength="-1"
						:auto-height="true"
						@input="onTextInput"
						@keydown.enter.exact.prevent="emit('search')"
						@confirm="emit('search')"
					/>
					<view class="search-button" @click="emit('search')">
						<image src="/static/icons/icon-send.svg" mode="aspectFit" class="icon-search-btn"></image>
					</view>
				</view>
			</div>
		</view>
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const CUSTOM_AI_PROMPTS_STORAGE_KEY = 'custom_ai_prompts'
const DEFAULT_CUSTOM_AI_PROMPTS = [
	'Build a 3-day spring capsule wardrobe',
	'What should I wear for a rainy commute?',
	'How to style my denim jacket for a date?',
	'Analyze my closet and suggest additions'
]

function parseStoredPrompts(raw) {
	if (raw == null || raw === '') return null
	try {
		const arr = typeof raw === 'string' ? JSON.parse(raw) : raw
		if (Array.isArray(arr) && arr.length === 4 && arr.every((s) => typeof s === 'string')) {
			return arr
		}
	} catch (_) {}
	return null
}

function loadCustomAiPrompts() {
	const saved = parseStoredPrompts(uni.getStorageSync(CUSTOM_AI_PROMPTS_STORAGE_KEY))
	return saved ? [...saved] : [...DEFAULT_CUSTOM_AI_PROMPTS]
}

function saveCustomAiPrompts(prompts) {
	try {
		uni.setStorageSync(CUSTOM_AI_PROMPTS_STORAGE_KEY, JSON.stringify(prompts))
	} catch (_) {}
}

defineProps({
	modelValue: { type: String, default: '' },
	images: { type: Array, default: () => [] },
	isDragOver: { type: Boolean, default: false }
})

const emit = defineEmits([
	'update:modelValue',
	'apply-text',
	'search',
	/** 预留：相册选图；菜单内入口已暂停，父组件 RecommendationAI 仍监听 */
	'add',
	'drop',
	'dragover',
	'dragleave',
	'preview-thumb',
	'remove-thumb'
])

const prompts = ref([...DEFAULT_CUSTOM_AI_PROMPTS])
const suggestionsOpen = ref(false)
const menuEditIndex = ref(-1)
const editBuffer = ref('')
/** H5：点 Done 会先触发 input blur；延迟执行 blur 保存，让按钮的 click 先取消计时并完成编辑 */
const blurFinishTimer = ref(null)
/** H5 上同一次点击可能先后触发 tap + click，避免连续执行两次把「进入编辑」立刻变成「完成」 */
let editBtnActionLock = false
let promptLineActionLock = false

onMounted(() => {
	prompts.value = loadCustomAiPrompts()
})

function cancelBlurFinish() {
	if (blurFinishTimer.value != null) {
		clearTimeout(blurFinishTimer.value)
		blurFinishTimer.value = null
	}
}

function scheduleBlurFinish(idx) {
	cancelBlurFinish()
	blurFinishTimer.value = setTimeout(() => {
		blurFinishTimer.value = null
		if (menuEditIndex.value === idx) {
			finishEdit(idx)
		}
	}, 200)
}

function closeSuggestions() {
	cancelBlurFinish()
	suggestionsOpen.value = false
	menuEditIndex.value = -1
}

function toggleSuggestionsMenu() {
	suggestionsOpen.value = !suggestionsOpen.value
	if (!suggestionsOpen.value) {
		menuEditIndex.value = -1
	}
}

function onPromptLineTap(idx) {
	if (promptLineActionLock) return
	if (menuEditIndex.value === idx) return
	promptLineActionLock = true
	cancelBlurFinish()
	try {
		const t = (prompts.value[idx] || '').trim()
		if (!t) return
		emit('apply-text', t)
		closeSuggestions()
	} finally {
		queueMicrotask(() => {
			promptLineActionLock = false
		})
	}
}

function startEdit(idx) {
	cancelBlurFinish()
	menuEditIndex.value = idx
	editBuffer.value = prompts.value[idx] || ''
}

function onEditInput(e) {
	editBuffer.value = e?.detail?.value ?? ''
}

function finishEdit(idx) {
	if (menuEditIndex.value !== idx) return
	cancelBlurFinish()
	const newVal = editBuffer.value.trim()
	const next = [...prompts.value]
	if (newVal) {
		next[idx] = newVal
	} else {
		next[idx] = DEFAULT_CUSTOM_AI_PROMPTS[idx]
	}
	prompts.value = next
	saveCustomAiPrompts(next)
	menuEditIndex.value = -1
}

function onConfirmEdit(idx) {
	cancelBlurFinish()
	finishEdit(idx)
}

function onEditButtonTap(idx) {
	if (editBtnActionLock) return
	editBtnActionLock = true
	cancelBlurFinish()
	try {
		if (menuEditIndex.value === idx) {
			finishEdit(idx)
		} else {
			startEdit(idx)
		}
	} finally {
		queueMicrotask(() => {
			editBtnActionLock = false
		})
	}
}

function onTextInput(e) {
	emit('update:modelValue', e?.detail?.value ?? '')
}

function onDrop(e) {
	emit('drop', e)
}

function onDragOver(e) {
	emit('dragover', e)
}

function onDragLeave(e) {
	emit('dragleave', e)
}
</script>

<style scoped>
.fade-enter-active {
	transition: opacity 0.48s cubic-bezier(0.22, 1, 0.36, 1);
}
.fade-leave-active {
	transition: opacity 0.32s cubic-bezier(0.4, 0, 1, 1);
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}

.slide-up-enter-active {
	transition:
		opacity 0.5s cubic-bezier(0.22, 1, 0.36, 1),
		transform 0.55s cubic-bezier(0.34, 1.25, 0.64, 1),
		filter 0.45s ease-out;
}
.slide-up-leave-active {
	transition:
		opacity 0.28s cubic-bezier(0.4, 0, 1, 1),
		transform 0.3s cubic-bezier(0.4, 0, 1, 1),
		filter 0.25s ease-in;
}
.slide-up-enter-from,
.slide-up-leave-to {
	opacity: 0;
	transform: translateY(32rpx) scale(0.94);
	filter: blur(6px);
}
.slide-up-enter-to,
.slide-up-leave-from {
	filter: blur(0);
}

.recommendation-input-bar {
	width: 1400rpx;
	max-width: 90%;
	margin-left: auto;
	margin-right: auto;
	align-self: center;
	position: relative;
	z-index: 20;
	display: flex;
	flex-direction: column;
	align-items: stretch;
	box-sizing: border-box;
	pointer-events: auto;
}

.suggestions-backdrop {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 18;
	background: rgba(38, 35, 32, 0.14);
	backdrop-filter: blur(5px) saturate(1.05);
	-webkit-backdrop-filter: blur(5px) saturate(1.05);
}

.suggestions-panel {
	position: absolute;
	left: 0;
	right: 0;
	bottom: 100%;
	margin-bottom: 28rpx;
	z-index: 22;
	padding: 36rpx 40rpx 28rpx;
	background: linear-gradient(
		165deg,
		rgba(255, 255, 255, 0.99) 0%,
		rgba(252, 250, 247, 0.97) 45%,
		rgba(248, 245, 240, 0.96) 100%
	);
	backdrop-filter: blur(24px) saturate(1.08);
	-webkit-backdrop-filter: blur(24px) saturate(1.08);
	border-radius: 36rpx;
	border: 1px solid rgba(255, 255, 255, 0.88);
	box-shadow:
		0 28rpx 80rpx rgba(45, 40, 35, 0.1),
		0 10rpx 32rpx rgba(157, 139, 112, 0.08),
		inset 0 1rpx 0 rgba(255, 255, 255, 0.95);
	box-sizing: border-box;
}

.panel-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 8rpx;
}

.title-wrap {
	display: flex;
	align-items: center;
	gap: 8rpx;
}

.panel-title {
	font-size: 24rpx;
	font-family: 'Didot', 'Times New Roman', serif;
	font-weight: 700;
	color: #9d8b70;
	letter-spacing: 0.1em;
}

.panel-close {
	width: 56rpx;
	height: 56rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.04);
	transition: transform 0.28s cubic-bezier(0.34, 1.2, 0.64, 1), background 0.25s ease;
	cursor: pointer;
}
.panel-close:active {
	transform: scale(0.92);
}
.panel-close:hover {
	background: rgba(0, 0, 0, 0.09);
	transform: scale(1.05);
}

.panel-close-x {
	font-size: 36rpx;
	line-height: 1;
	color: #6c6c70;
	font-weight: 300;
}

.panel-hint {
	display: block;
	font-size: 24rpx;
	color: #a0a0a5;
	line-height: 1.45;
	margin-bottom: 24rpx;
}

.suggestions-list {
	display: flex;
	flex-direction: column;
}

@keyframes suggestionRowReveal {
	from {
		opacity: 0;
		transform: translateY(16rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.suggestion-row-reveal {
	animation: suggestionRowReveal 0.52s cubic-bezier(0.22, 1, 0.36, 1) backwards;
}

.suggestion-row {
	display: flex;
	align-items: center;
	gap: 16rpx;
	padding: 22rpx 14rpx;
	margin: 0 -12rpx;
	border-bottom: 1px solid rgba(0, 0, 0, 0.045);
	border-radius: 18rpx;
	transition:
		background 0.32s cubic-bezier(0.22, 1, 0.36, 1),
		box-shadow 0.32s ease,
		transform 0.28s ease;
}

.suggestion-row:last-of-type {
	border-bottom: none;
}

.suggestion-row:hover:not(.is-editing-row) {
	background-color: rgba(157, 139, 112, 0.05);
	border-bottom-color: transparent;
}

.suggestion-row.is-editing-row {
	background: rgba(157, 139, 112, 0.07);
	box-shadow: inset 0 0 0 1rpx rgba(157, 139, 112, 0.14);
}

.bullet {
	flex-shrink: 0;
	font-size: 32rpx;
	color: #9d8b70;
	line-height: 1;
	opacity: 0.7;
}

.row-main {
	flex: 1;
	min-width: 0;
	display: flex;
	align-items: center;
	min-height: 60rpx;
}

.row-text {
	font-size: 28rpx;
	color: #2c2c2e;
	line-height: 1.5;
	font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
	font-weight: 500;
	word-break: break-word;
}

.row-input {
	width: 100%;
	font-size: 28rpx;
	color: #1d1d1f;
	font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
	font-weight: 500;
	line-height: 1.5;
	padding: 12rpx 20rpx;
	min-height: 68rpx;
	background: #ffffff;
	border-radius: 14rpx;
	border: 1px solid rgba(157, 139, 112, 0.4);
	box-shadow: 0 2rpx 8rpx rgba(157, 139, 112, 0.06), inset 0 0 0 4rpx rgba(157, 139, 112, 0.1);
	box-sizing: border-box;
	transition: all 0.25s ease;
}

.row-input:focus {
	border-color: #9d8b70;
	box-shadow: 0 4rpx 12rpx rgba(157, 139, 112, 0.15), inset 0 0 0 2rpx #9d8b70;
	outline: none;
}

/* Edit / Done：轻描边胶囊，Done 仅略加深边框与底色，避免大块实心渐变 */
.edit-btn {
	flex-shrink: 0;
	min-width: 108rpx;
	padding: 12rpx 28rpx;
	border-radius: 999rpx;
	box-sizing: border-box;
	text-align: center;
	cursor: pointer;
	background: transparent;
	border: 1px solid rgba(157, 139, 112, 0.35);
	transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.edit-btn:active {
	transform: scale(0.98);
}

.edit-btn:hover {
	background: rgba(157, 139, 112, 0.08);
}

.edit-btn-label {
	font-size: 24rpx;
	color: #7a6b55;
	font-weight: 600;
	font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
	transition: color 0.2s ease;
}

.edit-btn.is-active {
	background: #9d8b70;
	border-color: #85735e;
}

.edit-btn.is-active:hover {
	background: #8c7b60;
	border-color: #6e6254;
}

.edit-btn.is-active .edit-btn-label {
	color: #ffffff;
}

.icon-search-btn {
	width: 20px;
	height: 20px;
	display: block;
}

.input-thumb-row {
	width: 100%;
	padding: 16rpx 24rpx 12rpx;
	flex-shrink: 0;
}

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

.input-thumb-pill {
	position: relative;
	width: 96rpx;
	height: 96rpx;
	border-radius: 16rpx;
	overflow: hidden;
	background: #eee;
	border: 2rpx solid #e5e5ea;
	flex-shrink: 0;
}

.input-thumb-img {
	width: 100%;
	height: 100%;
	display: block;
	object-fit: cover;
	cursor: pointer;
}

.input-thumb-remove {
	position: absolute;
	top: 0;
	right: 0;
	width: 40rpx;
	height: 40rpx;
	border-radius: 0 12rpx 0 8rpx;
	background: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
}

.icon-close-small {
	width: 22rpx;
	height: 22rpx;
	filter: brightness(0) invert(1);
}

.search-bar {
	pointer-events: auto;
	width: 100%;
	max-width: 100%;
	min-height: 100rpx;
	background: rgba(255, 255, 255, 0.66);
	backdrop-filter: blur(24px);
	-webkit-backdrop-filter: blur(24px);
	border-radius: 50rpx;
	display: flex;
	flex-direction: column;
	align-items: stretch;
	border: 1px solid rgba(255, 255, 255, 0.88);
	box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.06), 0 4rpx 12rpx rgba(0, 0, 0, 0.02);
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
	box-shadow: inset 0 0 0 3rpx #9d8b70, 0 4rpx 20rpx rgba(157, 139, 112, 0.25);
}

.search-input-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 16rpx 22rpx 16rpx 32rpx;
	flex: 1;
	min-height: 68rpx;
}

.search-bar:focus-within {
	box-shadow: 0 10rpx 40rpx rgba(0, 0, 0, 0.15);
	border-color: #8c7b60;
	transform: scale(1.022);
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
	background-color: #1d1d1f;
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
	color: #1d1d1f;
	font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
	font-weight: 400;
	line-height: 72rpx;
	border: none;
	outline: none;
	overflow-y: auto;
	align-self: center;
	box-sizing: border-box;
	vertical-align: middle;
	transition: height 0.2s ease;
}

.search-placeholder {
	color: #999;
	font-weight: 300;
	font-family: 'PingFang SC', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
}

.search-button {
	width: 72rpx;
	height: 72rpx;
	min-height: 72rpx;
	margin-left: 20rpx;
	border-radius: 50%;
	background-color: transparent;
	border: 2rpx solid #1d1d1f;
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
	background-color: #1d1d1f;
}

.search-button:hover .icon-search-btn {
	filter: brightness(0) invert(1);
}
</style>
