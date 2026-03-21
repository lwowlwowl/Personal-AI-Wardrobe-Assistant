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
						open: activeFilter === 'category', 
						'has-value': filterCategory.length > 0 
					}"
					@click.stop="toggleFilterDropdown('category')"
				>
					<text>{{ filterCategoryLabel }}</text>
					<image 
						:src="activeFilter === 'category' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" 
						mode="aspectFit" 
						class="icon-arrow"
					></image>
				</view>
				<transition name="filter-panel">
					<view v-if="activeFilter === 'category'" class="dropdown-menu" @click.stop>
						<text class="dropdown-title">Clothing Type</text>
						<view class="option-list">
							<view
								v-for="opt in filterCategoryOptions"
								:key="opt.value"
								class="option-item"
								:class="{ active: selectedCategory.includes(opt.value) }"
								@click.stop="handleOptionClick('category', opt.value)"
							>{{ opt.label }}</view>
						</view>
						<view class="dropdown-actions">
							<view class="reset-btn" @click.stop="resetFilter('category')">
								<text>Reset</text>
							</view>
							<view class="apply-btn" @click.stop="applyFilter('category')">
								<text>Apply</text>
							</view>
						</view>
					</view>
				</transition>
			</view>
			<view class="filter-group">
				<view 
					class="filter-btn" 
					:class="{ 
						open: activeFilter === 'color', 
						'has-value': filterColor.length > 0 
					}"
					@click.stop="toggleFilterDropdown('color')"
				>
					<text>{{ filterColorLabel }}</text>
					<image 
						:src="activeFilter === 'color' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" 
						mode="aspectFit" 
						class="icon-arrow"
					></image>
				</view>
				<transition name="filter-panel">
					<view v-if="activeFilter === 'color'" class="dropdown-menu" @click.stop>
						<text class="dropdown-title">Color</text>
						<view class="option-list">
							<view
								v-for="opt in filterColorOptions"
								:key="opt.value"
								class="option-item"
								:class="{ active: selectedColor.includes(opt.value) }"
								@click.stop="handleOptionClick('color', opt.value)"
							>{{ opt.label }}</view>
						</view>
						<view class="dropdown-actions">
							<view class="reset-btn" @click.stop="resetFilter('color')">
								<text>Reset</text>
							</view>
							<view class="apply-btn" @click.stop="applyFilter('color')">
								<text>Apply</text>
							</view>
						</view>
					</view>
				</transition>
			</view>
			<view class="filter-group">
				<view 
					class="filter-btn" 
					:class="{ 
						open: activeFilter === 'season', 
						'has-value': filterSeason.length > 0 
					}"
					@click.stop="toggleFilterDropdown('season')"
				>
					<text>{{ filterSeasonLabel }}</text>
					<image 
						:src="activeFilter === 'season' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" 
						mode="aspectFit" 
						class="icon-arrow"
					></image>
				</view>
				<transition name="filter-panel">
					<view v-if="activeFilter === 'season'" class="dropdown-menu" @click.stop>
						<text class="dropdown-title">Season</text>
						<view class="option-list">
							<view
								v-for="opt in filterSeasonOptions"
								:key="opt.value"
								class="option-item"
								:class="{ active: selectedSeason.includes(opt.value) }"
								@click.stop="handleOptionClick('season', opt.value)"
							>{{ opt.label }}</view>
						</view>
						<view class="dropdown-actions">
							<view class="reset-btn" @click.stop="resetFilter('season')">
								<text>Reset</text>
							</view>
							<view class="apply-btn" @click.stop="applyFilter('season')">
								<text>Apply</text>
							</view>
						</view>
					</view>
				</transition>
			</view>
		</view>
		<view class="add-inline">
			<view class="add-inline-list">
				<transition name="filter-list-fade" mode="out-in">
					<view v-if="wardrobeLoading" key="loading" class="filter-list-container">
						<view v-for="n in 5" :key="n" class="add-item-card skeleton-card">
							<view class="skeleton-thumb"></view>
							<view class="skeleton-text"></view>
						</view>
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
import { TYPE_OPTIONS, SEASON_OPTIONS } from '@/utils/wardrobeEnums.js'
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
/* 初始必须为 true，防止刚进组件时闪烁空状态 */
const wardrobeLoading = ref(true)

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

			// 与 WardrobeView 保持一致：后端 season 可能是数组 ['autumn','winter']，此处统一转成逗号分隔字符串
			const seasonVal = item.season
			const seasonStr = Array.isArray(seasonVal) ? seasonVal.join(',') : (seasonVal || '')

			return {
				id: item.id,
				name: item.name || 'Unnamed',
				image,
				accentColor: (item.color && /^#?[0-9A-Fa-f]{6}$/i.test(String(item.color).replace(/^#/, ''))) ? (item.color.startsWith('#') ? item.color : '#' + item.color) : '#8d6e63',
				category: item.category || '',
				color: item.color || '',
				season: seasonStr
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

/** Filter 状态 */
// 应用中的筛选条件（与 WardrobeView 的 applied* 含义一致；空数组表示「全部」）
const filterCategory = ref([])
const filterColor = ref([])
const filterSeason = ref([])
const filterSearch = ref('')

// 当前展开的筛选面板名称：'category' | 'color' | 'season' | null
const activeFilter = ref(null)

// 临时选择（下拉展开时编辑的值，点击 Apply 后才同步到已应用条件）
const selectedCategory = ref([])
const selectedColor = ref([])
const selectedSeason = ref([])

// 下拉选项：
// - 类别与季节：直接沿用与「我的衣橱」一致的枚举
// - 颜色：根据实际衣物颜色动态生成，避免出现大量与当前衣橱无关的颜色
const filterCategoryOptions = TYPE_OPTIONS
const filterSeasonOptions = SEASON_OPTIONS
const filterColorOptions = computed(() => {
	const set = new Set()
	for (const item of wardrobeItems.value) {
		const str = item.color || ''
		if (!str) continue
		str
			.split(/[,/]+/)
			.map((s) => s.trim())
			.filter(Boolean)
			.forEach((code) => set.add(code))
	}
	return Array.from(set)
		.sort((a, b) => String(a).localeCompare(String(b)))
		.map((code) => ({ label: code, value: code }))
})

/** 点击下拉按钮：展开或收起对应的筛选面板，并把已应用条件同步到临时选择 */
function toggleFilterDropdown(type) {
	if (activeFilter.value === type) {
		activeFilter.value = null
		return
	}
	activeFilter.value = type
	if (type === 'category') selectedCategory.value = [...filterCategory.value]
	if (type === 'color') selectedColor.value = [...filterColor.value]
	if (type === 'season') selectedSeason.value = [...filterSeason.value]
}

/** 点击选项：只更新临时选择，不立即影响已应用条件 */
function handleOptionClick(type, value) {
	let target
	if (type === 'category') target = selectedCategory
	else if (type === 'color') target = selectedColor
	else target = selectedSeason

	const idx = target.value.indexOf(value)
	if (idx > -1) {
		target.value = target.value.filter((v) => v !== value)
	} else {
		target.value = [...target.value, value]
	}
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
const filterColorLabel = computed(() => {
	const arr = filterColor.value
	if (!arr.length) return 'Color'
	// Color 这里使用实际颜色 code 作为 label（与 WardrobeView 保持一致）
	return arr.length >= 2 ? `Color (${arr.length})` : arr[0]
})
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

// 与 MyWardrobe 的逻辑保持一致：搜索仅做「单词前缀」匹配，而不是任意子串
function nameMatchesSearch(name, searchTerm) {
	const nameWords = (name || '').toLowerCase().split(/\s+/).filter(Boolean)
	const searchWords = searchTerm.trim().toLowerCase().split(/\s+/).filter(Boolean)
	if (searchWords.length === 0) return true
	return searchWords.every((searchWord) =>
		nameWords.some((nameWord) => nameWord.startsWith(searchWord))
	)
}

/** 依 filter 筛选后的衣柜列表（多选：空数组＝不筛选该维度） */
const filteredWardrobeItems = computed(() => {
	const items = wardrobeItems.value
	let list = [...items]

	// type/color/season 可能为多选（逗号或斜线分隔），只要有一个命中即显示
	const parseItemCodes = (str) => (str || '').split(/[,/]+/).map((s) => s.trim()).filter(Boolean)

	const cat = filterCategory.value
	if (cat.length) {
		// Category：下拉使用 code，后端字段多为 label，需将 code 映射回 label 再匹配
		const selectedLabels = cat.map((code) => {
			const opt = TYPE_OPTIONS.find((o) => o.value === code)
			return opt ? opt.label : code
		})
		const set = new Set(selectedLabels.map((l) => l.toLowerCase()))
		list = list.filter((i) => {
			const cats = parseItemCodes(i.category)
			return cats.some((c) => set.has(c.toLowerCase()))
		})
	}

	const col = filterColor.value
	if (col.length) {
		// Color：后端多返回 code，本地直接按 code 匹配
		const set = new Set(col)
		list = list.filter((i) => parseItemCodes(i.color).some((code) => set.has(code)))
	}

	const sea = filterSeason.value
	if (sea.length) {
		// Season：优先按 code 匹配，同时兼容部分数据直接存 label 的情况
		const codeSet = new Set(sea)
		const labelSet = new Set(
			sea
				.map((code) => {
					const opt = SEASON_OPTIONS.find((o) => o.value === code)
					return opt ? String(opt.label).toLowerCase() : String(code).toLowerCase()
				})
		)
		list = list.filter((i) => {
			const seasons = parseItemCodes(i.season)
			return seasons.some((val) => {
				const v = String(val).toLowerCase()
				return codeSet.has(val) || labelSet.has(v)
			})
		})
	}

	if (filterSearch.value.trim()) {
		const q = filterSearch.value.trim()
		list = list.filter((i) => nameMatchesSearch(i.name, q))
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

/** 关闭所有筛选下拉菜单 */
function closeAllFilters() {
	activeFilter.value = null
}

/** Apply：同步临时选择到已应用条件并关闭当前下拉 */
function applyFilter(type) {
	if (type === 'category') filterCategory.value = [...selectedCategory.value]
	else if (type === 'color') filterColor.value = [...selectedColor.value]
	else if (type === 'season') filterSeason.value = [...selectedSeason.value]
	activeFilter.value = null
}

/** Reset：清空指定类型的筛选条件（临时与已应用一并清空），并关闭下拉 */
function resetFilter(type) {
	if (type === 'category') {
		filterCategory.value = []
		selectedCategory.value = []
	} else if (type === 'color') {
		filterColor.value = []
		selectedColor.value = []
	} else if (type === 'season') {
		filterSeason.value = []
		selectedSeason.value = []
	}
	activeFilter.value = null
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
	background: rgba(255, 255, 255, 0.96);
	border-radius: 20rpx;
	padding: 24rpx;
	box-shadow: 0 15rpx 35rpx rgba(0, 0, 0, 0.12);
	z-index: 100;
	width: 320rpx;
	border: 2rpx solid #E8E4DC;
	animation: dropdown-in 0.25s ease;
	backdrop-filter: blur(12px);
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
	justify-content: space-between;
	gap: 20rpx;
	margin-top: 20rpx;
	padding-top: 20rpx;
	border-top: 1rpx solid rgba(0, 0, 0, 0.06);
}

.apply-btn,
.reset-btn {
	flex: 1;
	padding: 16rpx 32rpx;
	font-size: 26rpx;
	border-radius: 12rpx;
	cursor: pointer;
	transition: opacity 0.2s;
	text-align: center;
}

.apply-btn {
	background: #9D8B70;
	color: #FFF;
	font-weight: 600;
}

.reset-btn {
	background: transparent;
	color: #1D1D1F;
}

.filter-panel-enter-active,
.filter-panel-leave-active {
	transition: all 0.22s ease;
}
.filter-panel-enter-from,
.filter-panel-leave-to {
	opacity: 0;
	transform: translateY(-6rpx) scale(0.97);
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

/* =========================================
   高级呼吸骨架屏 (Skeleton Loader)
========================================= */
.skeleton-card {
	pointer-events: none; /* 骨架屏不可点击 */
	background: rgba(255, 255, 255, 0.4);
	border-color: transparent;
}

.skeleton-thumb {
	width: 88rpx;
	height: 88rpx;
	border-radius: 12rpx 16rpx 16rpx 12rpx;
	background: rgba(184, 107, 31, 0.08); /* 使用品牌主题色作为底色 */
	animation: skeleton-pulse 1.5s infinite ease-in-out;
}

.skeleton-text {
	width: 45%;
	height: 28rpx;
	border-radius: 8rpx;
	background: rgba(184, 107, 31, 0.08);
	animation: skeleton-pulse 1.5s infinite ease-in-out;
	animation-delay: 0.2s; /* 文字比图片晚一点呼吸，增加错落感 */
}

@keyframes skeleton-pulse {
	0% { opacity: 0.4; }
	50% { opacity: 1; }
	100% { opacity: 0.4; }
}
</style>
