<template>
	<view v-if="visible" class="modal-mask" @click="close">
		<view 
			class="modal-wrap" 
			:class="{ 'modal-enter': isEnter, 'modal-leave': isLeave }"
			@click.stop
		>
			<view class="modal-content">
				<view v-if="openField" class="dropdown-backdrop" @click="openField = null"></view>
				<view class="modal-head">
					<view class="close-btn" @click="close">
						<image src="/static/icons/icon-close-red.svg" mode="aspectFit" class="icon-close"></image>
					</view>
				</view>

				<view class="modal-body">
					<view class="image-section">
						<image :src="item.image" mode="aspectFill" class="main-img" />
					</view>
					<view class="info-section">
						<view class="info-row">
							<text class="label">Name:</text>
							<input 
								class="info-input" 
								v-model="editName" 
								placeholder="Item name"
								@blur="emitField('name', editName)"
							/>
						</view>
						<view class="info-row info-row-select">
							<text class="label">Category:</text>
							<view class="select-trigger" @click="openField = openField === 'category' ? null : 'category'">
								<text class="select-value">{{ categoryDisplayText }}</text>
								<image :src="openField === 'category' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="select-arrow"></image>
							</view>
							<view v-if="openField === 'category'" class="select-dropdown">
								<view 
									v-for="opt in categoryOptions" 
									:key="opt.value" 
									class="select-option" 
									:class="{ active: editCategory === opt.value }"
									@click="selectCategory(opt)"
								>{{ opt.label }}</view>
								<view class="select-apply" @click="openField = null">Close</view>
							</view>
						</view>
						<view class="info-row">
							<text class="label">SubCategory:</text>
							<input 
								class="info-input" 
								v-model="editSubcategory" 
								placeholder="e.g. T-shirt, Blouse"
								@blur="emitField('subcategory', editSubcategory)"
							/>
						</view>
						<view class="info-row info-row-readonly">
							<text class="label">Added on:</text>
							<text class="value">{{ item.date || '—' }}</text>
						</view>
						<view class="info-row">
							<text class="label">Color:</text>
							<input
								class="info-input"
								v-model="editColor"
								placeholder="e.g. gray, navy blue"
								@blur="emitField('color', editColor)"
							/>
						</view>
						<view class="info-row info-row-select">
							<text class="label">Season:</text>
							<view class="select-trigger" @click="openField = openField === 'season' ? null : 'season'">
								<text class="select-value">{{ seasonDisplayText }}</text>
								<image :src="openField === 'season' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="select-arrow"></image>
							</view>
							<view v-if="openField === 'season'" class="select-dropdown">
								<view 
									v-for="opt in seasonOptions" 
									:key="opt.value" 
									class="select-option" 
									:class="{ active: editSeasons.includes(opt.value) }"
									@click="toggleOption('season', opt)"
								>{{ opt.label }}</view>
								<view class="select-apply" @click="applyField('season')">Apply</view>
							</view>
						</view>
						<view class="info-row info-row-tags">
							<text class="label">Tags:</text>
							<view class="tags-pills" v-if="tagsList.length">
								<view class="tag-pill" v-for="(tag, i) in tagsList" :key="i">{{ tag }}</view>
							</view>
							<text class="value" v-else>—</text>
						</view>
						<view class="info-row info-row-favourite">
							<text class="label">Favourite:</text>
							<view class="hearts">
								<view 
									v-for="k in 3" 
									:key="k" 
									class="heart-wrap" 
									:class="{ 'heart-pop': heartPopKey === k }"
									@click="setFavourite(k)"
								>
									<image 
										:src="editFavourite >= k ? '/static/icons/icon-heart-filled.svg' : '/static/icons/icon-heart.svg'" 
										mode="aspectFit" 
										class="heart-icon"
									/>
								</view>
							</view>
						</view>
					</view>
				</view>

				<view class="tags-section">
					<text class="tags-title">Similar Tags:</text>
					<view class="similar-items-row">
						<view
							class="similar-item-thumb"
							v-for="similar in similarItems"
							:key="similar.id"
							@click="openSimilarItem(similar)"
						>
							<image :src="similar.image" mode="aspectFill" class="similar-item-img" />
						</view>
						<text class="similar-tags-empty" v-if="!similarItems.length">No other items with similar tags yet.</text>
					</view>
				</view>

				<view class="action-bar">
					<view class="btn try-on-btn" @click="handleTryOn">
						<text>Virtual Try-on</text>
						<image src="/static/icons/icon-tryon.svg" mode="aspectFit" class="icon-camera"></image>
					</view>
					<view class="btn delete-btn" @click="handleDelete">Delete</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { watch, ref, nextTick, computed } from 'vue'
import { CATEGORY_OPTIONS, SEASON_OPTIONS, TYPE_LABEL_BY_CODE, SEASON_LABEL_BY_CODE, codesToLabels } from '@/utils/wardrobeEnums.js'

const props = defineProps({
	visible: {
		type: Boolean,
		default: false
	},
	item: {
		type: Object,
		default: () => ({})
	},
	/** 全部衣物列表，用于计算同分类的 Similar Tags */
	allClothes: {
		type: Array,
		default: () => []
	}
})

const emit = defineEmits(['update:visible', 'try-on', 'delete', 'update', 'open-item'])

const isEnter = ref(false)
const isLeave = ref(false)

const categoryOptions = CATEGORY_OPTIONS
const seasonOptions = SEASON_OPTIONS

const editName = ref('')
const editCategory = ref('')
const editSubcategory = ref('')
const editColor = ref('')
const editSeasons = ref([])
const editFavourite = ref(0)
const openField = ref(null)

/** 支持后端返回的数组（如 season）或逗号分隔字符串，统一为字符串数组 */
function parseMulti (val) {
	if (val == null) return []
	if (Array.isArray(val)) return val.map((s) => String(s).trim()).filter(Boolean)
	if (typeof val !== 'string') return []
	return val.split(/[,/]+/).map(s => s.trim()).filter(Boolean)
}

const categoryDisplayText = computed(() => editCategory.value ? (TYPE_LABEL_BY_CODE[editCategory.value] || editCategory.value) : '—')
const seasonDisplayText = computed(() => codesToLabels(editSeasons.value, SEASON_LABEL_BY_CODE))

/** 解析单件衣物的 tags 为字符串数组 */
function getTagsFromItem(cloth) {
	const val = cloth?.tags
	if (!val) return []
	if (Array.isArray(val)) {
		return val.map((t) => (typeof t === 'string' ? t : (t?.tag || t))).filter(Boolean)
	}
	if (typeof val === 'string') {
		const s = String(val).trim()
		return s ? s.split(/[,/]+/).map((x) => x.trim()).filter(Boolean) : []
	}
	return []
}

/** 解析 tags 为数组，用于 pill 展示 */
const tagsList = computed(() => getTagsFromItem(props.item))

/** 拥有与当前衣物相似 tags 的其他衣物（同分类且至少有一个共同 tag），按共同 tag 数量排序，取前 N 个 */
const similarItems = computed(() => {
	const cur = props.item
	const curId = cur?.id
	const curCategory = cur?.type || editCategory.value
	const myTags = getTagsFromItem(cur)
	if (!curId || !curCategory || !Array.isArray(props.allClothes) || props.allClothes.length === 0 || !myTags.length) return []
	const sameCategory = props.allClothes.filter((c) => c.id !== curId && (c.type === curCategory || c.category === curCategory))
	const withShared = sameCategory
		.map((c) => {
			const theirTags = getTagsFromItem(c)
			const shared = theirTags.filter((t) => myTags.includes(t.trim()))
			return { item: c, sharedCount: shared.length }
		})
		.filter((x) => x.sharedCount > 0)
		.sort((a, b) => b.sharedCount - a.sharedCount)
	return withShared.map((x) => x.item).slice(0, 8)
})

function openSimilarItem(item) {
	emit('open-item', item)
}

watch(() => props.item, (val) => {
	if (!val) return
	editName.value = val.name || ''
	editCategory.value = val.type || ''
	editSubcategory.value = val.subcategory || ''
	editColor.value = val.color || ''
	editSeasons.value = parseMulti(val.season)
	const f = val.favourite
	editFavourite.value = typeof f === 'number' && f >= 0 && f <= 3 ? f : 0
	openField.value = null
}, { immediate: true, deep: true })

watch(() => props.visible, (v) => {
	if (v) {
		isLeave.value = false
		nextTick(() => {
			isEnter.value = true
			editName.value = props.item?.name || ''
			editCategory.value = props.item?.type || ''
			editSubcategory.value = props.item?.subcategory || ''
			editColor.value = props.item?.color || ''
			editSeasons.value = parseMulti(props.item?.season)
			const f = props.item?.favourite
			editFavourite.value = typeof f === 'number' && f >= 0 && f <= 3 ? f : 0
		})
	} else {
		isEnter.value = false
		isLeave.value = true
		openField.value = null
	}
}, { immediate: true })

function selectCategory(opt) {
	if (!props.item?.id) return
	const value = opt && typeof opt === 'object' && 'value' in opt ? opt.value : opt
	editCategory.value = value
	emit('update', { id: props.item.id, field: 'category', value })
	openField.value = null
}

const close = () => {
	isEnter.value = false
	isLeave.value = true
	setTimeout(() => {
		emit('update:visible', false)
		isLeave.value = false
	}, 280)
}

const emitField = (field, value) => {
	if (!props.item?.id) return
	const v = field === 'name' || field === 'subcategory' || field === 'color'
		? (value || '').trim()
		: value
	emit('update', { id: props.item.id, field, value: v })
}

const toggleOption = (field, opt) => {
	const code = opt && typeof opt === 'object' && 'value' in opt ? opt.value : opt
	const arr = editSeasons.value
	const i = arr.indexOf(code)
	if (i >= 0) arr.splice(i, 1)
	else arr.push(code)
}

const applyField = (field) => {
	if (!props.item?.id) return
	if (field !== 'season') return
	const value = editSeasons.value.join(',')
	emit('update', { id: props.item.id, field, value })
	openField.value = null
}

const heartPopKey = ref(null)
const setFavourite = (level) => {
	if (!props.item?.id) return
	heartPopKey.value = level
	setTimeout(() => { heartPopKey.value = null }, 400)
	const next = editFavourite.value === level ? Math.max(0, level - 1) : level
	editFavourite.value = next
	emit('update', { id: props.item.id, field: 'favourite', value: next })
}

const handleTryOn = () => {
	emit('try-on', props.item)
}

const handleDelete = () => {
  emit('delete', props.item.id)
}
</script>

<style scoped>
.modal-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.4);
	backdrop-filter: blur(4px);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 999;
	animation: mask-fade-in 0.28s ease;
}

@keyframes mask-fade-in {
	from { opacity: 0; }
	to { opacity: 1; }
}

.modal-wrap {
	width: 92%;
	max-width: 820px;
	max-height: 92vh;
	display: flex;
	justify-content: center;
	align-items: center;
	transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1),
	            opacity 0.28s ease;
}

.modal-wrap.modal-enter {
	animation: modal-zoom-in 0.32s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.modal-wrap.modal-leave {
	animation: modal-zoom-out 0.24s ease forwards;
}

@keyframes modal-zoom-in {
	from {
		opacity: 0;
		transform: scale(0.95);
	}
	to {
		opacity: 1;
		transform: scale(1);
	}
}

@keyframes modal-zoom-out {
	from {
		opacity: 1;
		transform: scale(1);
	}
	to {
		opacity: 0;
		transform: scale(0.95);
	}
}

.modal-content {
	width: 100%;
	max-height: 92vh;
	overflow-y: auto;
	background-color: #FDFBF7;
	border-radius: 24rpx;
	padding: 48rpx 48rpx 5rpx 48rpx;
	position: relative;
	box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.12);
	border: 2rpx solid rgba(0, 0, 0, 0.08);
}

.dropdown-backdrop {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 5;
	cursor: default;
}

.modal-head {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 88rpx;
	display: flex;
	justify-content: flex-end;
	align-items: center;
	padding: 0 24rpx;
	z-index: 6;
}

.close-btn {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	border-radius: 50%;
	transition: background 0.2s ease;
}
.close-btn:hover {
	background: #f3f1ec;
}

.icon-close {
	width: 44rpx;
	height: 44rpx;
}

.modal-body {
	display: flex;
	margin-top: 24rpx;
	gap: 40rpx;
}

.image-section {
	flex: 1;
	min-width: 0;
	width: 0;
	aspect-ratio: 4 / 5;
	border-radius: 16rpx;
	overflow: hidden;
	background: #F5F0E6;
}

.image-section .main-img {
	width: 100%;
	height: 100%;
	display: block;
	object-fit: cover;
}

.info-section {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	justify-content: center;
	font-family: "Bodoni MT", "Noto Serif", "Songti SC", serif;
}

.info-row {
	display: flex;
	align-items: center;
	margin-bottom: 22rpx;
	font-size: 32rpx;
	color: #1D1D1F;
	line-height: 1.45;
}

.info-row .label {
	font-weight: 600;
	margin-right: 12rpx;
	flex-shrink: 0;
}

.info-row .value {
	font-weight: 400;
}

.info-row-tags {
	align-items: flex-start;
}
.info-row-tags .label {
	margin-top: 2rpx;
}
.tags-pills {
	display: flex;
	flex-wrap: wrap;
	gap: 8rpx;
}
.tag-pill {
	background: #F3F1EC;
	border-radius: 999rpx;
	padding: 8rpx 20rpx;
	font-size: 24rpx;
	color: #3A3631;
	font-weight: 500;
}

.info-input {
	flex: 1;
	min-width: 0;
	font-size: 32rpx;
	color: #1D1D1F;
	font-weight: 400;
	font-family: "Bodoni MT", "Noto Serif", "Songti SC", serif;
	background: transparent;
	border: none;
	border-bottom: 1rpx solid transparent;
	border-radius: 0;
	padding: 4rpx 0;
	outline: none;
	transition: border-color 0.2s;
}

.info-input:focus {
	border-bottom-color: rgba(29, 29, 31, 0.25);
}

.info-input::placeholder {
	color: #AAA;
}

.info-row-select {
	position: relative;
	align-items: flex-start;
}

.info-row-favourite {
	align-items: center;
}

.hearts {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

@keyframes heart-pop {
	0% { transform: scale(1); }
	50% { transform: scale(1.25); }
	100% { transform: scale(1); }
}

.heart-wrap {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 8rpx;
	cursor: pointer;
	transition: transform 0.2s, opacity 0.2s;
}
.heart-wrap.heart-pop {
	animation: heart-pop 0.4s ease;
}

.heart-wrap:active {
	opacity: 0.85;
}

.heart-icon {
	width: 40rpx;
	height: 40rpx;
}

.select-trigger {
	display: flex;
	align-items: flex-start;
	gap: 8rpx;
	min-height: 44rpx;
	padding: 6rpx 12rpx;
	margin: -6rpx -12rpx;
	border-radius: 12rpx;
	cursor: pointer;
	transition: background 0.2s;
	flex: 1;
	min-width: 0;
}

.select-trigger:active {
	background: rgba(0, 0, 0, 0.05);
}

.select-value {
	flex: 1;
	min-width: 0;
	font-weight: 400;
	color: #1D1D1F;
	white-space: normal;
	word-break: break-word;
	line-height: 1.45;
}

.select-arrow {
	width: 24rpx;
	height: 24rpx;
	flex-shrink: 0;
	opacity: 0.6;
}

.select-dropdown {
	position: absolute;
	left: 0;
	right: 0;
	top: 100%;
	margin-top: 8rpx;
	background: #FFF;
	border-radius: 16rpx;
	padding: 16rpx;
	box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
	border: 2rpx solid #E8E4DC;
	z-index: 10;
	max-height: 440rpx;
	overflow-y: auto;
}

.select-option {
	padding: 16rpx 20rpx;
	font-size: 28rpx;
	color: #1D1D1F;
	border-radius: 12rpx;
	margin-bottom: 4rpx;
	transition: background 0.2s;
	cursor: pointer;
}

.select-option:last-of-type {
	margin-bottom: 0;
}

.select-option.active {
	background: #FFF9F1;
	font-weight: 600;
}

.select-apply {
	margin-top: 16rpx;
	padding: 16rpx;
	text-align: center;
	font-weight: 600;
	font-size: 28rpx;
	color: #9D8B70;
	background: #F5F0E6;
	border-radius: 12rpx;
	cursor: pointer;
	transition: opacity 0.2s;
}

.select-apply:active {
	opacity: 0.85;
}

.tags-section {
	margin-top: 32rpx;
}

.tags-title {
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 26rpx;
	color: #1D1D1F;
	margin-bottom: 16rpx;
	display: block;
}

.similar-items-row {
	display: flex;
	gap: 16rpx;
	flex-wrap: wrap;
	align-items: center;
}

.similar-item-thumb {
	width: 96rpx;
	height: 96rpx;
	border-radius: 12rpx;
	overflow: hidden;
	background: #E8E4DC;
	flex-shrink: 0;
	cursor: pointer;
	transition: transform 0.2s, box-shadow 0.2s;
}

.similar-item-thumb:active {
	transform: scale(0.96);
}

.similar-item-img {
	width: 100%;
	height: 100%;
}

.similar-tags-empty {
	color: #999;
	font-size: 24rpx;
	line-height: 1.4;
}

.action-bar {
	display: flex;
	border-top: 2rpx solid rgba(0, 0, 0, 0.12);
	margin-top: 52rpx;
	padding-top: 0;
}

.action-bar .btn {
	flex: 1;
	text-align: center;
	padding: 28rpx 0;
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 30rpx;
	cursor: pointer;
	transition: background 0.2s ease;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
}

.action-bar .btn:active {
	opacity: 0.85;
}

.try-on-btn {
	border-right: 2rpx solid rgba(0, 0, 0, 0.12);
	font-weight: 600;
	color: #1D1D1F;
}

.icon-camera {
	width: 36rpx;
	height: 36rpx;
}

.delete-btn {
	color: #1D1D1F;
	font-weight: 600;
}
</style>
