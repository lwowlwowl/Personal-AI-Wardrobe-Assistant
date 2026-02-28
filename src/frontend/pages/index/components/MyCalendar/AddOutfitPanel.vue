<template>
	<view class="panel-inner" @click="closeAllFilters">
		<input
			v-model="filterSearch"
			class="filter-search filter-search-top"
			placeholder="Search..."
			placeholder-class="filter-search-placeholder"
			@click.stop
		/>
		<view class="filter-bar" @click.stop>
			<view class="filter-group">
				<view 
					class="filter-btn" 
					:class="{ 
						open: filterCategoryOpen, 
						'has-value': filterCategory.length > 0 
					}"
					@click="openFilter('category')"
				>
					<text>{{ filterCategoryLabel }}</text>
					<image 
						:src="filterCategoryOpen ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" 
						mode="aspectFit" 
						class="icon-arrow"
					></image>
				</view>
				<transition name="dropdown-fade">
					<view v-if="filterCategoryOpen" class="dropdown-menu" @click.stop>
						<text class="dropdown-title">Clothing Type</text>
						<view class="option-list">
							<view
								v-for="opt in filterCategoryOptions"
								:key="opt.value"
								class="option-item"
								:class="{ active: isFilterSelected('category', opt) }"
								@click.stop="toggleFilter('category', opt)"
							>{{ opt.label }}</view>
						</view>
						<view class="dropdown-actions">
							<view class="reset-btn" @click.stop="resetFilter('category')">
								<text>Reset</text>
							</view>
						</view>
					</view>
				</transition>
			</view>
			<view class="filter-group">
				<view 
					class="filter-btn" 
					:class="{ 
						open: filterColorOpen, 
						'has-value': filterColor.length > 0 
					}"
					@click="openFilter('color')"
				>
					<text>{{ filterColorLabel }}</text>
					<image 
						:src="filterColorOpen ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" 
						mode="aspectFit" 
						class="icon-arrow"
					></image>
				</view>
				<transition name="dropdown-fade">
					<view v-if="filterColorOpen" class="dropdown-menu" @click.stop>
						<text class="dropdown-title">Color</text>
						<view class="option-list">
							<view
								v-for="opt in filterColorOptions"
								:key="opt.value"
								class="option-item"
								:class="{ active: isFilterSelected('color', opt) }"
								@click.stop="toggleFilter('color', opt)"
							>{{ opt.label }}</view>
						</view>
						<view class="dropdown-actions">
							<view class="reset-btn" @click.stop="resetFilter('color')">
								<text>Reset</text>
							</view>
						</view>
					</view>
				</transition>
			</view>
			<view class="filter-group">
				<view 
					class="filter-btn" 
					:class="{ 
						open: filterSeasonOpen, 
						'has-value': filterSeason.length > 0 
					}"
					@click="openFilter('season')"
				>
					<text>{{ filterSeasonLabel }}</text>
					<image 
						:src="filterSeasonOpen ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" 
						mode="aspectFit" 
						class="icon-arrow"
					></image>
				</view>
				<transition name="dropdown-fade">
					<view v-if="filterSeasonOpen" class="dropdown-menu" @click.stop>
						<text class="dropdown-title">Season</text>
						<view class="option-list">
							<view
								v-for="opt in filterSeasonOptions"
								:key="opt.value"
								class="option-item"
								:class="{ active: isFilterSelected('season', opt) }"
								@click.stop="toggleFilter('season', opt)"
							>{{ opt.label }}</view>
						</view>
						<view class="dropdown-actions">
							<view class="reset-btn" @click.stop="resetFilter('season')">
								<text>Reset</text>
							</view>
						</view>
					</view>
				</transition>
			</view>
		</view>
		<view class="add-inline">
			<view class="add-inline-list">
				<transition name="filter-list-fade" mode="out-in">
					<view v-if="wardrobeLoading" key="loading" class="add-empty">
						<text class="add-empty-text">加载衣橱中…</text>
					</view>
					<view v-else-if="filteredWardrobeItems.length > 0" key="filter-list" class="filter-list-container">
						<view
							v-for="(item, index) in filteredWardrobeItems"
							:key="item.id"
							class="add-item-card filter-item-enter"
							:class="{ 'add-item-selected': isPending(item) }"
							:style="{ animationDelay: index * 30 + 'ms' }"
							@click="togglePending(item)"
						>
							<view class="add-item-thumb-wrap" :style="{ '--thumb-accent': item.accentColor || '#8d6e63' }">
								<image v-if="item.image" class="add-item-thumb" :src="item.image" mode="aspectFill" />
								<view v-else class="add-item-thumb placeholder" />
							</view>
							<text class="add-item-name">{{ item.name }}</text>
							<view v-if="isPending(item)" class="add-item-check">
								<image src="/static/icons/icon-check.svg" mode="aspectFit" class="check-icon" />
							</view>
						</view>
					</view>
					<view v-else key="filter-empty" class="add-empty">
						<view class="add-empty-illus">
							<view class="add-empty-icon-gradient" />
							<image src="/static/icons/icon-wardrobe.svg" mode="aspectFit" class="add-empty-icon" />
						</view>
						<text class="add-empty-text">✨ No matching items found</text>
						<text class="add-empty-hint">Try adjusting your filters or add more clothes to your wardrobe.</text>
					</view>
				</transition>
			</view>
			<view class="add-panel-footer">
				<text class="footer-count">{{ pendingSelection.length }} item{{ pendingSelection.length !== 1 ? 's' : '' }} selected</text>
				<view class="footer-confirm-btn" @click="handleConfirm">
					<text>{{ pendingSelection.length ? 'Update' : 'Back' }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { TYPE_OPTIONS, COLOR_OPTIONS, SEASON_OPTIONS } from '@/utils/wardrobeEnums.js'
import { getClothingList, API_BASE_URL } from '@/api/wardrobe.js'

const props = defineProps({
	token: {
		type: String,
		default: ''
	},
	initialSelection: {
		type: Array,
		default: () => []
	}
})

const emit = defineEmits(['confirm', 'cancel'])

/** 待加入的单品（多选后确认） */
const pendingSelection = ref([...props.initialSelection])

// 监听 initialSelection 的变化，当父组件切换日期时更新 pendingSelection
watch(() => props.initialSelection, (newVal) => {
	pendingSelection.value = [...newVal]
}, { deep: true })

/** 衣柜项目：来自 GET /api/clothing，字段映射 image_url -> image，color 可作 accentColor */
const wardrobeItems = ref([])
const wardrobeLoading = ref(false)

async function loadWardrobe() {
	// 优先用父组件传入的 token，否则从本地存储读取（与「我的衣柜」同源）
	const token = props.token || uni.getStorageSync('auth_token') || ''
	if (!token) {
		wardrobeItems.value = []
		wardrobeLoading.value = false
		return
	}
	wardrobeLoading.value = true
	try {
		const res = await getClothingList({
			token,
			page: 1,
			page_size: 100,
			order_by: 'created_at',
			order_desc: true
		})
		if (res.statusCode !== 200) {
			wardrobeItems.value = []
			return
		}
		// 兼容：res.data 可能为已解析对象或 JSON 字符串；后端格式为 { success, data: { items, pagination } }
		let body = res.data
		if (typeof body === 'string') {
			try {
				body = JSON.parse(body)
			} catch (_) {
				wardrobeItems.value = []
				return
			}
		}
		const rawItems = (body && body.data && body.data.items) || (body && body.items) || []
		if (!Array.isArray(rawItems)) {
			wardrobeItems.value = []
			return
		}
		const items = rawItems.map((item) => {
			let image = item.image_url || item.image || ''
			if (image && image.startsWith('/') && !image.startsWith('//')) {
				image = `${API_BASE_URL}${image}`
			}
			return {
				id: item.id,
				name: item.name || '未命名',
				image,
				accentColor: (item.color && /^#?[0-9A-Fa-f]{6}$/i.test(String(item.color).replace(/^#/, ''))) ? (item.color.startsWith('#') ? item.color : '#' + item.color) : '#8d6e63',
				category: item.category || '',
				color: item.color || '',
				season: item.season || ''
			}
		})
		wardrobeItems.value = items
	} catch (e) {
		wardrobeItems.value = []
		console.warn('[AddOutfitPanel] loadWardrobe failed', e)
	} finally {
		wardrobeLoading.value = false
	}
}

onMounted(() => loadWardrobe())
watch(() => props.token, () => loadWardrobe())

/** Filter 状态：多选数组，空数组表示「全部」 */
const filterCategory = ref([])
const filterColor = ref([])
const filterSeason = ref([])
const filterSearch = ref('')
const filterCategoryOpen = ref(false)
const filterColorOpen = ref(false)
const filterSeasonOpen = ref(false)

const filterCategoryOptions = TYPE_OPTIONS
const filterColorOptions = COLOR_OPTIONS
const filterSeasonOptions = SEASON_OPTIONS

/** 切换筛选选项（多选）：如果已选中则取消，未选中则添加 */
function toggleFilter(type, opt) {
	// opt 是 { label, value } 对象，使用 value (code) 进行存储和匹配
	const optValue = typeof opt === 'string' ? opt : opt.value
	if (type === 'category') {
		const arr = filterCategory.value
		const i = arr.indexOf(optValue)
		if (i === -1) filterCategory.value = [...arr, optValue]
		else filterCategory.value = arr.filter((_, j) => j !== i)
	} else if (type === 'color') {
		const arr = filterColor.value
		const i = arr.indexOf(optValue)
		if (i === -1) filterColor.value = [...arr, optValue]
		else filterColor.value = arr.filter((_, j) => j !== i)
	} else if (type === 'season') {
		const arr = filterSeason.value
		const i = arr.indexOf(optValue)
		if (i === -1) filterSeason.value = [...arr, optValue]
		else filterSeason.value = arr.filter((_, j) => j !== i)
	}
}

/** 检查筛选选项是否已选中 */
function isFilterSelected(type, opt) {
	// opt 是 { label, value } 对象，使用 value (code) 进行匹配
	const optValue = typeof opt === 'string' ? opt : opt.value
	if (type === 'category') return filterCategory.value.includes(optValue)
	if (type === 'color') return filterColor.value.includes(optValue)
	if (type === 'season') return filterSeason.value.includes(optValue)
	return false
}

/** 筛选按钮显示的标签：未选中时显示默认文本，选中1项显示该项标签，选中多项显示数量 */
const filterCategoryLabel = computed(() => {
	const arr = filterCategory.value
	if (!arr.length) return 'Clothing type'
	// 将 code 转换为 label
	const labels = arr.map(code => {
		const opt = TYPE_OPTIONS.find(o => o.value === code)
		return opt ? opt.label : code
	})
	return arr.length >= 2 ? `Clothing type (${arr.length})` : labels[0]
})
/** 筛选按钮显示的标签：未选中时显示默认文本，选中1项显示该项标签，选中多项显示数量 */
const filterColorLabel = computed(() => {
	const arr = filterColor.value
	if (!arr.length) return 'Color'
	// 将 code 转换为 label
	const labels = arr.map(code => {
		const opt = COLOR_OPTIONS.find(o => o.value === code)
		return opt ? opt.label : code
	})
	return arr.length >= 2 ? `Color (${arr.length})` : labels[0]
})
/** 筛选按钮显示的标签：未选中时显示默认文本，选中1项显示该项标签，选中多项显示数量 */
const filterSeasonLabel = computed(() => {
	const arr = filterSeason.value
	if (!arr.length) return 'Season'
	// 将 code 转换为 label
	const labels = arr.map(code => {
		const opt = SEASON_OPTIONS.find(o => o.value === code)
		return opt ? opt.label : code
	})
	return arr.length >= 2 ? `Season (${arr.length})` : labels[0]
})

/** 依 filter 筛选后的衣柜列表（多选：空数组＝不筛选该维度） */
const filteredWardrobeItems = computed(() => {
	const items = wardrobeItems.value
	let list = [...items]
	const cat = filterCategory.value
	if (cat.length) {
		// 将选中的 code 转换为对应的 label，然后与 wardrobeItems 中的 category 匹配
		const selectedLabels = cat.map(code => {
			const opt = TYPE_OPTIONS.find(o => o.value === code)
			return opt ? opt.label : code
		})
		const set = new Set(selectedLabels.map(l => l.toLowerCase()))
		list = list.filter((i) => {
			const itemCategory = (i.category || '').toLowerCase()
			return set.has(itemCategory)
		})
	}
	const col = filterColor.value
	if (col.length) {
		// 将选中的 code 转换为对应的 label，然后与 wardrobeItems 中的 color 匹配
		const selectedLabels = col.map(code => {
			const opt = COLOR_OPTIONS.find(o => o.value === code)
			return opt ? opt.label : code
		})
		const set = new Set(selectedLabels.map(l => l.toLowerCase()))
		list = list.filter((i) => {
			const itemColor = (i.color || '').toLowerCase()
			return set.has(itemColor)
		})
	}
	const sea = filterSeason.value
	if (sea.length) {
		// 将选中的 code 转换为对应的 label，然后与 wardrobeItems 中的 season 匹配
		const selectedLabels = sea.map(code => {
			const opt = SEASON_OPTIONS.find(o => o.value === code)
			return opt ? opt.label : code
		})
		const set = new Set(selectedLabels.map(l => l.toLowerCase()))
		list = list.filter((i) => {
			const itemSeason = (i.season || '').toLowerCase()
			return set.has(itemSeason)
		})
	}
	if (filterSearch.value.trim()) {
		const q = filterSearch.value.trim().toLowerCase()
		list = list.filter((i) => (i.name || '').toLowerCase().includes(q))
	}
	return list
})

/** 检查单品是否已在待选列表中 */
function isPending(item) {
	return pendingSelection.value.some((p) => p.id === item.id)
}

/** 切换单品的选中状态：如果已选中则移除，未选中则添加 */
function togglePending(item) {
	const idx = pendingSelection.value.findIndex((p) => p.id === item.id)
	if (idx >= 0) {
		pendingSelection.value = pendingSelection.value.filter((_, i) => i !== idx)
	} else {
		pendingSelection.value = [...pendingSelection.value, { ...item }]
	}
}

/** 确认选择：如果有选中项则发送 confirm 事件，否则发送 cancel 事件 */
function handleConfirm() {
	if (pendingSelection.value.length > 0) {
		emit('confirm', [...pendingSelection.value])
	} else {
		emit('cancel')
	}
}

/** 打开指定的筛选下拉菜单（如果已打开则关闭，实现切换效果） */
function openFilter(type) {
	const open = type === 'category' ? filterCategoryOpen.value : type === 'color' ? filterColorOpen.value : filterSeasonOpen.value
	filterCategoryOpen.value = false
	filterColorOpen.value = false
	filterSeasonOpen.value = false
	if (!open) {
		if (type === 'category') filterCategoryOpen.value = true
		else if (type === 'color') filterColorOpen.value = true
		else if (type === 'season') filterSeasonOpen.value = true
	}
}

/** 关闭所有筛选下拉菜单 */
function closeAllFilters() {
	filterCategoryOpen.value = false
	filterColorOpen.value = false
	filterSeasonOpen.value = false
}

/** 重置指定类型的筛选条件（清空选中项） */
function resetFilter(type) {
	if (type === 'category') {
		filterCategory.value = []
	} else if (type === 'color') {
		filterColor.value = []
	} else if (type === 'season') {
		filterSeason.value = []
	}
	// 重置后关闭 dropdown
	closeAllFilters()
}
</script>

<style scoped>
.panel-inner {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
}

/* Filter Bar */
.filter-bar {
	display: flex;
	flex-wrap: wrap;
	gap: 20rpx;
	margin-bottom: 24rpx;
}

.filter-group {
	position: relative;
}

.filter-btn {
	background: #FFF;
	border: 2rpx solid #8E8070;
	border-radius: 16rpx;
	padding: 12rpx 24rpx;
	font-weight: 600;
	color: #1D1D1F;
	display: inline-flex;
	align-items: center;
	gap: 10rpx;
	box-shadow: 2rpx 2rpx 0 rgba(142, 128, 112, 0.2);
	transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, transform 0.2s;
	cursor: pointer;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
	font-size: 24rpx;
}

.filter-btn:active {
	transform: translateY(2rpx);
	box-shadow: none;
}

.filter-btn.open,
.filter-btn.has-value {
	background-color: #FFF9F1;
	border-color: #9D8B70;
	box-shadow: 2rpx 2rpx 0 rgba(157, 139, 112, 0.3);
}

.icon-arrow {
	width: 24rpx;
	height: 24rpx;
}

.filter-search {
	padding: 18rpx 24rpx;
	border-radius: 12rpx;
	background: rgba(0, 0, 0, 0.04);
	font-size: 28rpx;
	color: #1d1d1f;
	min-height: 64rpx;
	box-sizing: border-box;
}
.filter-search-top {
	width: 100%;
	margin-bottom: 16rpx;
}
.filter-search-placeholder {
	color: #999;
}

.dropdown-menu {
	position: absolute;
	top: 100%;
	left: 0;
	margin-top: 16rpx;
	background: #FFF;
	border-radius: 20rpx;
	padding: 24rpx;
	box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.12);
	z-index: 100;
	width: 320rpx;
	border: 2rpx solid #E8E4DC;
	animation: dropdown-in 0.25s ease;
}

@keyframes dropdown-in {
	from {
		opacity: 0;
		transform: translateY(-8rpx) scale(0.95);
	}
	to {
		opacity: 1;
		transform: translateY(0) scale(1);
	}
}

.dropdown-title {
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 32rpx;
	font-weight: 600;
	color: #1D1D1F;
	margin-bottom: 16rpx;
	display: block;
}

.option-list {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.option-item {
	padding: 16rpx 20rpx;
	font-size: 26rpx;
	color: #1D1D1F;
	border-radius: 12rpx;
	cursor: pointer;
	transition: background 0.2s;
}

.option-item:hover,
.option-item.active {
	background-color: #FFF9F1;
}

.option-item.active {
	font-weight: 600;
}

.dropdown-actions {
	display: flex;
	justify-content: center;
	margin-top: 20rpx;
	padding-top: 20rpx;
	border-top: 1rpx solid rgba(0, 0, 0, 0.06);
}

.reset-btn {
	padding: 14rpx 28rpx;
	font-size: 26rpx;
	border-radius: 12rpx;
	cursor: pointer;
	transition: opacity 0.2s, background 0.2s;
	background: transparent;
	color: #1D1D1F;
	font-weight: 500;
}

.reset-btn:hover {
	background: rgba(0, 0, 0, 0.04);
}

.reset-btn:active {
	opacity: 0.7;
}

.dropdown-fade-enter-active,
.dropdown-fade-leave-active {
	transition: opacity 0.25s ease, transform 0.25s ease;
}

.dropdown-fade-enter-from {
	opacity: 0;
	transform: translateY(-8rpx) scale(0.95);
}

.dropdown-fade-leave-to {
	opacity: 0;
	transform: translateY(-8rpx) scale(0.95);
}

/* 右侧面板内「选择衣服」：容器与可滚动列表（替代原底部弹窗） */
.add-inline {
	display: flex;
	flex-direction: column;
	flex: 1;
	min-height: 0;
}
.add-inline-list {
	flex: 1;
	min-height: 0;
	overflow-y: auto;
	padding: 12rpx 6rpx 24rpx 0;
}

.filter-list-container {
	display: flex;
	flex-direction: column;
}

/* 单品卡片：精品化，hover 浮起，选中勾选 */
.add-item-card {
	display: flex;
	align-items: center;
	gap: 24rpx;
	padding: 24rpx 28rpx;
	border-radius: 28rpx;
	background: rgba(255, 255, 255, 0.9);
	border: 1rpx solid rgba(0, 0, 0, 0.04);
	margin-bottom: 16rpx;
	transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
	cursor: pointer;
}
.add-item-card:hover {
	background: rgba(184, 107, 31, 0.06);
	transform: translateY(-2rpx);
	box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.06);
}
.add-item-card:active {
	transform: translateY(0);
}
.add-item-card.add-item-selected {
	background: rgba(184, 107, 31, 0.1);
	border-color: rgba(184, 107, 31, 0.25);
	box-shadow: 0 4rpx 16rpx rgba(184, 107, 31, 0.12);
}

.add-item-thumb-wrap {
	position: relative;
	flex-shrink: 0;
	border-radius: 16rpx;
	overflow: hidden;
	box-shadow: inset 6rpx 0 0 0 var(--thumb-accent, #8d6e63);
}

.add-item-thumb {
	width: 88rpx;
	height: 88rpx;
	border-radius: 12rpx 16rpx 16rpx 12rpx;
	background: #f5f2ee;
	display: block;
}
.add-item-thumb.placeholder {
	background: #e8e4df;
}

.add-item-name {
	flex: 1;
	font-size: 28rpx;
	font-weight: 500;
	color: #1d1d1f;
	letter-spacing: 0.01em;
}

.add-item-check {
	width: 48rpx;
	height: 48rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 50%;
	background: #8d6e63;
	color: #fff;
}
.check-icon {
	width: 28rpx;
	height: 28rpx;
}

/* 底部确认区 */
.add-panel-footer {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 20rpx 36rpx;
	padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
	background: #fff;
	border-top: 1rpx solid rgba(0, 0, 0, 0.06);
	min-height: 80rpx;
}

.footer-count {
	font-size: 28rpx;
	font-weight: 600;
	color: #8d6e63;
}

.footer-confirm-btn {
	padding: 20rpx 40rpx;
	border-radius: 24rpx;
	background: #8d6e63;
	color: #fff;
	font-size: 28rpx;
	font-weight: 600;
	transition: background 0.2s ease, transform 0.2s ease;
	cursor: pointer;
}
.footer-confirm-btn:hover {
	background: #7a5e52;
}
.footer-confirm-btn:active {
	transform: scale(0.97);
}

/* Filter 列表切换动画 */
.filter-list-fade-enter-active,
.filter-list-fade-leave-active {
	transition: opacity 0.3s cubic-bezier(0.22, 1, 0.36, 1), transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.filter-list-fade-enter-from {
	opacity: 0;
	transform: translateY(20rpx);
}

.filter-list-fade-leave-to {
	opacity: 0;
	transform: translateY(-20rpx);
}

.filter-list-fade-enter-to,
.filter-list-fade-leave-from {
	opacity: 1;
	transform: translateY(0);
}

/* Filter 列表项进入动画（stagger） */
.filter-item-enter {
	opacity: 0;
	transform: translateY(16rpx) scale(0.96);
	animation: filter-item-enter 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

@keyframes filter-item-enter {
	to {
		opacity: 1;
		transform: translateY(0) scale(1);
	}
}

/* 空状态 */
.add-empty {
	padding: 80rpx 40rpx;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	min-height: 400rpx;
}

.add-empty-illus {
	width: 140rpx;
	height: 140rpx;
	margin: 0 auto 32rpx;
	border-radius: 50%;
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
	overflow: hidden;
}

.add-empty-icon-gradient {
	position: absolute;
	inset: 0;
	background: linear-gradient(135deg, rgba(184, 107, 31, 0.12) 0%, rgba(184, 107, 31, 0.06) 100%);
	border-radius: 50%;
}

.add-empty-icon {
	width: 72rpx;
	height: 72rpx;
	position: relative;
	z-index: 1;
	opacity: 0.6;
}

.add-empty-text {
	display: block;
	font-size: 32rpx;
	color: #4a4a4a;
	font-weight: 600;
	letter-spacing: -0.02em;
	margin-bottom: 12rpx;
}

.add-empty-hint {
	display: block;
	font-size: 26rpx;
	color: #888;
	line-height: 1.6;
	max-width: 480rpx;
	letter-spacing: 0.01em;
}
</style>
