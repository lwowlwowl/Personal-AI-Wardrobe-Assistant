<template>
	<scroll-view class="expanded-page" scroll-y>
		<view class="expanded-content">
			<view class="expanded-header">
				<view class="back-btn" @click="emit('back')">
					<text class="back-arrow">←</text>
					<text class="back-text">Back</text>
				</view>
				<text class="expanded-title">Idle Items</text>
			</view>

			<view class="card summary-card">
				<text class="summary-stat">{{ stats.idle_items ?? unwornCount }}</text>
				<text class="summary-desc">unworn items out of {{ stats.total_items || 106 }} total ({{ idleRate }}% idle rate)</text>
			</view>

			<view class="card list-card">
				<text class="card-label">All idle items</text>
				<view class="filter-section">
					<text class="filter-section-label">Time</text>
					<view class="filter-chips">
						<view
							v-for="f in timeFilters"
							:key="'time-' + f.value"
							class="filter-chip"
							:class="{ active: activeTimeFilter === f.value }"
							@click="activeTimeFilter = f.value"
						>
							<text class="filter-chip-text">{{ f.label }}</text>
						</view>
					</view>
				</view>
				<view class="filter-section">
					<text class="filter-section-label">Season</text>
					<view class="filter-chips">
						<view
							v-for="f in seasonFilters"
							:key="'season-' + f.value"
							class="filter-chip"
							:class="{ active: activeSeasonFilter === f.value }"
							@click="activeSeasonFilter = f.value"
						>
							<text class="filter-chip-text">{{ f.label }}</text>
						</view>
					</view>
				</view>
				<view v-if="listReady && filteredItems.length > 0">
				<TransitionGroup name="list" tag="view" class="idle-list" appear>
					<view
						v-for="(item, index) in filteredItems"
						:key="item.name + '-' + item.season + '-' + item.type"
						class="idle-item-card"
						:style="{ '--stagger-delay': index * 100 + 'ms' }"
					>
						<view class="idle-item-thumb" :style="{ background: item.dotColor }">
							<image v-if="item.image" :src="item.image" mode="aspectFill" class="thumb-img" />
						</view>
						<view class="idle-item-content">
							<view class="idle-item-header">
								<view class="idle-status-badge" :class="'status-' + item.status.level">
									<view class="status-dot"></view>
									<text class="status-label">{{ item.status.label }}</text>
								</view>
							</view>
							<text class="idle-name">{{ item.name }}</text>
							<view class="idle-meta-wrap">
								<text class="idle-meta-label">Last worn:</text>
								<text class="idle-meta-value" :class="'meta-' + item.status.level">{{ item.lastWornDisplay }}</text>
							</view>
						</view>
						<view class="idle-item-action" hover-class="idle-item-action-hover" @click="wearToday(item)">
							<text class="action-icon">✦</text>
							<text class="action-text">Try today</text>
						</view>
					</view>
				</TransitionGroup>
				</view>
				<view v-else-if="listReady && filteredItems.length === 0 && (stats.idle_items ?? unwornCount) === 0" class="empty-state">
					<view class="empty-state-illus">🎉</view>
					<text class="empty-state-title">Your wardrobe is well utilized!</text>
					<text class="empty-state-desc">No idle items today.</text>
				</view>
				<view v-else-if="listReady && filteredItems.length === 0 && (stats.idle_items ?? unwornCount) > 0" class="empty-state empty-state-filter">
					<view class="empty-state-illus">🔍</view>
					<text class="empty-state-title">No items match your filters</text>
					<text class="empty-state-desc">Try changing Time or Season to see idle items.</text>
				</view>
				<view v-else class="idle-list idle-list-placeholder" style="min-height: 200rpx"></view>
			</view>
		</view>
	</scroll-view>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { TransitionGroup } from 'vue'
import { COLOR_HEX_BY_CODE } from '@/utils/wardrobeEnums.js'
import { SEASON_OPTIONS } from '@/utils/wardrobeEnums.js'
import { getIdleRate, getIdleItemsDetail, API_BASE_URL } from '@/api/analysisApi.js'

const props = defineProps({
	unwornCount: { type: Number, default: 3 }
})
const emit = defineEmits(['back'])

const loading = ref(true)
const listLoading = ref(false)
const listReady = ref(false)
const stats = ref({
	total_items: 0,
	idle_items: 0,
	idle_rate: 0
})

const idleItems = ref([])

function getFullImageUrl(imageUrl) {
	if (!imageUrl) return null
	if (imageUrl.startsWith('http')) return imageUrl
	if (imageUrl.startsWith('/')) return `${API_BASE_URL}${imageUrl}`
	return `${API_BASE_URL}/${imageUrl}`
}

/** Idle status from API item (wear_count, last_worn_date) */
function getIdleStatus(item) {
	if (item.wear_count === 0) return { level: 'never', label: 'Never worn' }
	if (item.last_worn_date) {
		const lastWorn = new Date(item.last_worn_date)
		const now = new Date()
		const monthsDiff = (now.getFullYear() - lastWorn.getFullYear()) * 12 + (now.getMonth() - lastWorn.getMonth())
		if (monthsDiff >= 12) return { level: 'over_year', label: 'Over a year ago' }
	}
	return { level: 'within_year', label: 'Within a year' }
}

function getLastWornDisplay(item, status) {
	if (status.level === 'never') return 'Never'
	if (status.level === 'over_year' && item.last_worn_date) {
		const lastWorn = new Date(item.last_worn_date)
		const now = new Date()
		const monthsDiff = (now.getFullYear() - lastWorn.getFullYear()) * 12 + (now.getMonth() - lastWorn.getMonth())
		return `${monthsDiff} months ago`
	}
	return ''
}

function getSortOrder(lastWorn) {
	if (!lastWorn) return 0
	const months = String(lastWorn).match(/(\d+)\s*month/i)?.[1]
	const weeks = String(lastWorn).match(/(\d+)\s*week/i)?.[1]
	if (months) return parseInt(months) * 4
	if (weeks) return parseInt(weeks)
	return 999
}

async function fetchData() {
	loading.value = true
	try {
		const res = await getIdleRate(30)
		if (res && res.success && res.data) {
			stats.value = res.data
		}
	} catch (e) {
		console.error('獲取閒置率失敗:', e)
	} finally {
		loading.value = false
	}
}

async function fetchIdleItems(page = 1, append = false) {
	listLoading.value = true
	try {
		let timeFilter = activeTimeFilter.value === 'all' ? null : activeTimeFilter.value
		const res = await getIdleItemsDetail({
			page,
			pageSize: pageSize.value,
			timeFilter,
			seasonFilter: activeSeasonFilter.value !== 'all' ? activeSeasonFilter.value : null
		})
		if (res && res.success && res.data) {
			const items = (res.data.items || []).map(item => ({
				...item,
				image: getFullImageUrl(item.image_url),
				dotColor: COLOR_HEX_BY_CODE[item.color] || '#cccccc'
			}))
			if (append) {
				idleItems.value = [...idleItems.value, ...items]
			} else {
				idleItems.value = items
			}
			const pagination = res.data.pagination || {}
			currentPage.value = pagination.page || page
			totalPages.value = pagination.total_pages || 1
			hasMore.value = currentPage.value < totalPages.value
		}
		return res
	} catch (e) {
		console.error('獲取閒置明細失敗:', e)
		throw e
	} finally {
		listLoading.value = false
	}
}

const currentPage = ref(1)
const pageSize = ref(20)
const hasMore = ref(false)
const totalPages = ref(1)

const idleRate = computed(() => {
	if (stats.value.total_items === 0) return 0
	return Math.round((stats.value.idle_items / stats.value.total_items) * 100)
})

const idleItemsWithStatus = computed(() =>
	idleItems.value
		.map((item) => {
			const status = getIdleStatus(item)
			return {
				...item,
				status,
				lastWornDisplay: getLastWornDisplay(item, status),
				sortOrder: getSortOrder(item.last_worn_date)
			}
		})
		.filter((item) => item.status.level !== 'within_year')
)

const timeFilters = [
	{ label: 'All', value: 'all' },
	{ label: 'Never worn', value: 'never' },
	{ label: 'Over a year', value: 'over_year' }
]
const activeTimeFilter = ref('all')
const seasonFilters = [
	{ label: 'All', value: 'all' },
	...SEASON_OPTIONS.map((o) => ({ label: o.label, value: o.value }))
]
const activeSeasonFilter = ref('all')

watch([activeTimeFilter, activeSeasonFilter], () => {
	fetchIdleItems(1, false)
})

const filteredItems = computed(() => {
	let list = [...idleItemsWithStatus.value]
	if (activeTimeFilter.value === 'never') {
		list = list.filter((item) => item.status.level === 'never')
	} else if (activeTimeFilter.value === 'over_year') {
		list = list.filter((item) => item.status.level === 'over_year')
	}
	if (activeSeasonFilter.value !== 'all') {
		list = list.filter((item) => item.season === activeSeasonFilter.value)
	}
	list = list.sort((a, b) => b.sortOrder - a.sortOrder)
	return list
})

function wearToday(item) {
	uni.showToast({ title: `Marked "${item.name}" as worn today`, icon: 'none' })
}

onMounted(async () => {
	await nextTick()
	listReady.value = true
	await fetchData()
	await fetchIdleItems(1, false)
})
</script>

<style scoped>
.expanded-page {
	background: #F6F5F1;
	height: 100vh;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	box-sizing: border-box;
}
.expanded-content {
	padding: 24rpx 30rpx 40rpx;
}

.expanded-header {
	display: flex;
	align-items: center;
	gap: 20rpx;
	margin-bottom: 28rpx;
}

.back-btn {
	display: inline-flex;
	align-items: center;
	gap: 6rpx;
	padding: 10rpx 16rpx;
	border-radius: 14rpx;
	background: rgba(0, 0, 0, 0.04);
	transition: background 0.2s ease, transform 0.15s ease;
}
.back-btn:active { transform: scale(0.98); }

.back-arrow { font-size: 28rpx; color: #1d1d1f; font-weight: 600; }
.back-text { font-size: 26rpx; color: #1d1d1f; font-weight: 600; }

.expanded-title {
	font-size: 36rpx;
	font-weight: 800;
	color: #1d1d1f;
	letter-spacing: 0.02em;
}

.card {
	background: #FFFEFB;
	border-radius: 32rpx;
	padding: 28rpx 32rpx;
	box-shadow: 0 6rpx 24rpx rgba(0, 0, 0, 0.06), 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
	margin-bottom: 24rpx;
	transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.summary-card {
	text-align: center;
	padding: 32rpx;
}
.summary-stat {
	font-size: 64rpx;
	font-weight: 800;
	color: #1d1d1f;
	display: block;
	line-height: 1.2;
}
.summary-desc {
	font-size: 26rpx;
	color: #777;
	margin-top: 10rpx;
	display: block;
}

.card-label {
	font-size: 30rpx;
	font-weight: 700;
	color: #1d1d1f;
	margin-bottom: 20rpx;
	display: block;
}

.filter-section {
	margin-bottom: 20rpx;
}
.filter-section:last-of-type {
	margin-bottom: 24rpx;
	padding-bottom: 20rpx;
	border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
}
.filter-section-label {
	font-size: 24rpx;
	color: #888;
	font-weight: 600;
	display: block;
	margin-bottom: 12rpx;
}
.filter-chips {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
}
.filter-chip {
	padding: 5rpx 20rpx;
	border-radius: 24rpx;
	background: rgba(0, 0, 0, 0.04);
	border: 1rpx solid transparent;
	transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
	cursor: pointer;
}
.filter-chip:active { transform: scale(0.98); }
.filter-chip.active {
	background: rgba(184, 107, 31, 0.15);
	border-color: rgba(184, 107, 31, 0.3);
}
.filter-chip-text {
	font-size: 26rpx;
	font-weight: 600;
	color: #1d1d1f;
}
.filter-chip.active .filter-chip-text {
	color: #7a4e18;
}

.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 60rpx 40rpx;
	text-align: center;
}
.empty-state-illus {
	font-size: 80rpx;
	line-height: 1;
	margin-bottom: 24rpx;
	width: 120rpx;
	height: 120rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: linear-gradient(135deg, rgba(184, 107, 31, 0.08) 0%, rgba(184, 107, 31, 0.04) 100%);
	border-radius: 50%;
}
.empty-state-title {
	font-size: 32rpx;
	font-weight: 700;
	color: #1d1d1f;
	line-height: 1.4;
	margin-bottom: 12rpx;
}
.empty-state-desc {
	font-size: 26rpx;
	color: #777;
	line-height: 1.5;
}

.idle-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	position: relative;
}
.idle-item-card {
	display: flex;
	align-items: center;
	gap: 20rpx;
	padding: 24rpx;
	background: #FFFEFB;
	border-radius: 24rpx;
	border: 1rpx solid rgba(0, 0, 0, 0.06);
	box-shadow: 0 6rpx 20rpx rgba(0, 0, 0, 0.06), 0 2rpx 6rpx rgba(0, 0, 0, 0.03);
	transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}
.idle-item-card:hover {
	background: #FFFEFB;
	transform: translateY(-6rpx);
	box-shadow: 0 12rpx 36rpx rgba(0, 0, 0, 0.08), 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.idle-item-thumb {
	width: 120rpx;
	height: 120rpx;
	border-radius: 12rpx;
	flex-shrink: 0;
	background: #f0f0f0;
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
}
.thumb-img {
	width: 100%;
	height: 100%;
}

.idle-item-content {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}
.idle-item-header {
	margin-bottom: 4rpx;
}
.idle-status-badge {
	display: inline-flex;
	align-items: center;
	gap: 8rpx;
	padding: 6rpx 12rpx;
	border-radius: 14rpx;
	font-size: 22rpx;
	font-weight: 500;
}
.status-dot {
	width: 8rpx;
	height: 8rpx;
	border-radius: 50%;
}
.status-never .status-dot {
	background: rgba(180, 120, 120, 0.8);
}
.status-over_year .status-dot {
	background: rgba(140, 120, 160, 0.8);
}
.status-label { font-size: 22rpx; }
.status-never {
	background: rgba(220, 180, 180, 0.2);
	color: #a06767;
}
.status-over_year {
	background: rgba(200, 180, 220, 0.2);
	color: #7a6a8a;
}

.idle-name {
	font-size: 28rpx;
	font-weight: 700;
	color: #1d1d1f;
	line-height: 1.3;
	margin-bottom: 4rpx;
}
.idle-meta-wrap {
	display: flex;
	align-items: baseline;
	gap: 8rpx;
	margin-top: 6rpx;
}
.idle-meta-label {
	font-size: 24rpx;
	color: #888;
	font-weight: 500;
}
.idle-meta-value {
	font-size: 26rpx;
	font-weight: 700;
	padding: 4rpx 10rpx;
	border-radius: 8rpx;
}
.meta-never {
	color: #a06767;
	background: rgba(220, 180, 180, 0.15);
}
.meta-over_year {
	color: #7a6a8a;
	background: rgba(200, 180, 220, 0.15);
}

.idle-item-action {
	display: inline-flex;
	align-items: center;
	gap: 8rpx;
	padding: 10rpx 16rpx;
	background: transparent;
	border: 1rpx solid rgba(184, 107, 31, 0.2);
	border-radius: 16rpx;
	flex-shrink: 0;
	transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}
.idle-item-action:hover,
.idle-item-action-hover {
	background: #8a6b3a;
	border-color: #8a6b3a;
}
.idle-item-action:hover .action-icon,
.idle-item-action:hover .action-text,
.idle-item-action-hover .action-icon,
.idle-item-action-hover .action-text {
	color: #fff;
	opacity: 1;
}
.idle-item-action:active {
	background: rgba(184, 107, 31, 0.06);
	border-color: rgba(184, 107, 31, 0.3);
	transform: scale(0.98);
}
.idle-item-action:active:hover,
.idle-item-action-hover:active {
	background: #7a5e32;
	border-color: #7a5e32;
}
.action-icon {
	font-size: 20rpx;
	color: #9a7b4a;
	opacity: 0.85;
	transition: color 0.2s ease, opacity 0.2s ease;
}
.action-text {
	font-size: 24rpx;
	font-weight: 500;
	color: #8a6b3a;
	white-space: nowrap;
	transition: color 0.2s ease, opacity 0.2s ease;
}

/* TransitionGroup: stagger enter + smooth rearrange (use :deep for scoped) */
:deep(.list-enter-active),
:deep(.list-appear-active),
:deep(.list-leave-active) {
	transition: opacity 400ms ease, transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
:deep(.list-enter-active),
:deep(.list-appear-active) {
	transition-delay: var(--stagger-delay);
}
:deep(.list-enter-from),
:deep(.list-appear-from),
:deep(.list-leave-to) {
	opacity: 0;
	transform: translateY(12rpx);
}
:deep(.list-move) {
	transition: transform 400ms ease;
}
:deep(.list-leave-active) {
	position: absolute;
	width: calc(100% - 0rpx);
}
</style>
