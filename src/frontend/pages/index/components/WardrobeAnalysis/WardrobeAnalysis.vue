<template>
	<view
		class="page"
		:class="{ 'page--expanded': !!expandedView }"
	>
		<!-- 主看板（未展开子页）：装饰层仅在 .page 内，避免盖住侧栏 -->
		<template v-if="!expandedView">
			<view class="bg-blob bg-blob-1" aria-hidden="true"></view>
			<view class="bg-blob bg-blob-2" aria-hidden="true"></view>
			<view class="grain-overlay" aria-hidden="true"></view>
		</template>
		<!-- expanded-pages 全屏展开；勿用 transition mode=out-in，否则离场时 .wardrobe-analysis-bento 会从 .page 脱落导致闪屏（须留在 .page-bento-wrap 上） -->
		<transition name="page">
			<ActivityReport v-if="expandedView === 'activity-report'" key="activity-report" :total-wears="currentWears" :trend-value="activityPercentTarget" :is-increase="activityTrend === 'increase'" :week-data="weeklyActivityData?.week_data" :category-activity="weeklyActivityData?.category_activity" @back="expandedView = null" />
			<IdleItemsView v-else-if="expandedView === 'idle-items'" key="idle-items" :unworn-count="idleCount" @back="expandedView = null" />
			<view v-else key="bento" class="page-bento-wrap wardrobe-analysis-bento">
		<view v-if="filterOpen" class="filter-backdrop" @click="closeFilter"></view>

		<!-- .bento-grid：渐进入场；filter 打开时提高 z-index -->
		<view class="bento-grid bento-grid-entering" :class="{ 'bento-grid-filter-open': filterOpen }" @click="filterOpen && closeFilter()">
			<BentoWardrobeActivity
				:loading-activity="loadingActivity"
				:current-wears="currentWears"
				:activity-percent="activityPercent"
				:activity-trend="activityTrend"
				@open-activity-report="goActivityReport"
			/>
			<BentoIdleRate :idle-percent="idlePercent" :idle-count="idleCount" :total-items-count="totalItemsCount" @open-idle-items="goIdleItems" />
			<BentoTotalItems
				:is-logged-in="isLoggedIn"
				:loading-trend="loadingTrend"
				:total-items-count="totalItemsCount"
				:line-years="lineYears"
				:line-data="lineData"
				:total-stats="totalStats"
				v-model:viewByTotal="viewByTotal"
				:filter-open-for-total="filterOpen === 'total'"
				:milestone-replay="milestoneReplayTick"
				@toggle-total-filter="toggleViewBy('total')"
				@apply-filter="closeFilter"
			/>
			<BentoMostWorn
				:is-logged-in="isLoggedIn"
				:loading-worn="loadingWorn"
				v-model:viewByWorn="viewByWorn"
				:filter-open-for-worn="filterOpen === 'worn'"
				:most-worn="mostWorn"
				@toggle-worn-filter="toggleViewBy('worn')"
				@apply-filter="closeFilter"
			/>
			<BentoTopStats
				:top-color-name="topColorName"
				:top-color-percent="topColorPercent"
				:top-style-name="topStyleName"
				:top-style-percent="topStylePercent"
			/>
			<BentoSuggestedAdditions
				:is-logged-in="isLoggedIn"
				:loading-suggested="loadingSuggested"
				:suggested-texts="suggestedTexts"
				@refresh="refreshSuggestedAdditions"
			/>
			<BentoCategoryBreakdown
				:is-logged-in="isLoggedIn"
				:loading-category="loadingCategory"
				:category-data="categoryData"
				@toggle-dimension="toggleCategoryType"
			/>
		</view>
			</view>
		</transition>
	</view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import ActivityReport from './expanded-pages/ActivityReport.vue'
import IdleItemsView from './expanded-pages/IdleItemsView.vue'
import BentoWardrobeActivity from './bento-widgets/WardrobeActivity.vue'
import BentoIdleRate from './bento-widgets/IdleRate.vue'
import BentoTotalItems from './bento-widgets/TotalItems.vue'
import BentoMostWorn from './bento-widgets/MostWorn.vue'
import BentoTopStats from './bento-widgets/TopStats.vue'
import BentoSuggestedAdditions from './bento-widgets/SuggestedAdditions.vue'
import BentoCategoryBreakdown from './bento-widgets/CategoryBreakdown.vue'
/* 副作用 import：保证 bento-widgets/BentoCards.css 打入包（部分目标下 <style src> 不可靠） */
import './bento-widgets/BentoCards.css'
import * as analysisApi from '@/api/analysisApi.js'
const SUGGESTED_CACHE_KEY = 'wardrobe_suggested_additions'

/** 趋势图无数据或 API 失败时的占位（不使用假数据） */
function resetTrendToEmpty() {
	lineYears.value = []
	lineData.value = []
	totalItemsCount.value = 0
	totalStats.value = null
}

function clearMostWorn() {
	mostWorn.value = []
}

function loadSuggestedCacheFromStorage() {
	try {
		const raw = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem(SUGGESTED_CACHE_KEY) : null
		if (!raw) return null
		const arr = JSON.parse(raw)
		return Array.isArray(arr) ? arr : null
	} catch (_) {
		return null
	}
}

function saveSuggestedCacheToStorage(list) {
	try {
		if (typeof sessionStorage !== 'undefined') {
			if (list == null) sessionStorage.removeItem(SUGGESTED_CACHE_KEY)
			else sessionStorage.setItem(SUGGESTED_CACHE_KEY, JSON.stringify(list))
		}
	} catch (_) {}
}

/** Suggested Additions 缓存：内存 + sessionStorage，切页后再回来仍可还原 */
let suggestedAdditionsCache = loadSuggestedCacheFromStorage()

function hydrateSuggestedFromCacheOrFetch() {
	const cached = suggestedAdditionsCache ?? loadSuggestedCacheFromStorage()
	if (cached != null) {
		suggestedAdditionsCache = cached
		suggestedTexts.value = cached
		loadingSuggested.value = false
	} else {
		loadingSuggested.value = true
		fetchSuggestedAdditions()
	}
}

const props = defineProps({
	isLoggedIn: { type: Boolean, default: false }
})

/** 点击卡片内链接后展示的展开页 */
const expandedView = ref(null)
const filterOpen = ref(null)
const viewByTotal = ref('weekly')
const viewByWorn = ref('yearly')
/** 从 expanded-pages 返回时递增，供 TotalItems 单点趋势重播数字动画 */
const milestoneReplayTick = ref(0)

const activityTrend = ref(Math.random() >= 0.5 ? 'increase' : 'decrease')
const activityPercentTarget = computed(() => {
	if (weeklyActivityData.value != null && weeklyActivityData.value.trend_percent != null) {
		return Math.abs(weeklyActivityData.value.trend_percent)
	}
	return activityTrend.value === 'increase' ? 15 : 8
})

/** GET weekly-activity 原始数据；失败或未登录时为 null */
const weeklyActivityData = ref(null)
/** 本周穿戴次数，来自 weekly-activity */
const currentWears = ref(0)
const activityPercent = ref(0)
const idlePercent = ref(0)
const topColorPercent = ref(0)
const topStylePercent = ref(0)
const loadingTrend = ref(true)
const loadingWorn = ref(true)
const loadingSuggested = ref(true)
const loadingActivity = ref(true)

const lineYears = ref([])
const lineData = ref([])
const totalItemsCount = ref(0)
const totalStats = ref(null)
const idleCount = ref(0)
const topColorName = ref('')
const topStyleName = ref('')

const idlePercentTarget = computed(() =>
	totalItemsCount.value ? (idleCount.value / totalItemsCount.value) * 100 : 0
)

function animateCountUp(refVal, targetRef, duration = 800, delay = 0) {
	const startVal = 0
	const getTarget = () => {
		if (typeof targetRef === 'function') return targetRef()
		if (targetRef && targetRef.value !== undefined) return targetRef.value
		return targetRef
	}
	const start = () => {
		const t0 = performance.now()
		function tick(now) {
			const target = getTarget()
			const elapsed = now - t0
			const t = Math.min(elapsed / duration, 1)
			const eased = 1 - Math.pow(1 - t, 3)
			refVal.value = Math.round(startVal + (target - startVal) * eased)
			if (t < 1) requestAnimationFrame(tick)
		}
		requestAnimationFrame(tick)
	}
	if (delay > 0) setTimeout(start, delay)
	else start()
}

const categoryData = ref([])
const loadingCategory = ref(false)

const mostWorn = ref([])
const suggestedTexts = ref([])

function toggleViewBy(which) {
	filterOpen.value = filterOpen.value === which ? null : which
}
function closeFilter() {
	filterOpen.value = null
}
/** CategoryBreakdown 维度切换占位，尚未接 API */
function toggleCategoryType() {}
function goActivityReport() {
	expandedView.value = 'activity-report'
}
function goIdleItems() {
	expandedView.value = 'idle-items'
}

async function fetchSuggestedAdditions() {
	loadingSuggested.value = true
	try {
		if (!analysisApi.isLoggedIn()) {
			suggestedTexts.value = []
			return
		}
		const response = await analysisApi.getSuggestedAdditions(3)
		const items = response?.data?.items
		if (response && response.success && Array.isArray(items) && items.length > 0) {
			const list = items.slice(0, 3)
			suggestedTexts.value = list
			suggestedAdditionsCache = list
			saveSuggestedCacheToStorage(list)
		} else {
			suggestedTexts.value = []
			suggestedAdditionsCache = []
			saveSuggestedCacheToStorage([])
		}
	} catch (e) {
		suggestedTexts.value = []
	} finally {
		loadingSuggested.value = false
	}
}

/** 仅在用户点击刷新时调用，用于更新 Suggested Additions（每次点击都发请求，不因 loading 中而跳过） */
function refreshSuggestedAdditions() {
	if (!props.isLoggedIn) return
	fetchSuggestedAdditions()
}

async function fetchTrendData() {
	loadingTrend.value = true
	try {
		const response = await analysisApi.getTrend(viewByTotal.value)
		if (response && response.success && response.data) {
			const data = response.data
			if (data.labels && data.labels.length > 0 && data.values && data.values.length > 0) {
				lineYears.value = data.labels
				lineData.value = data.values
				totalItemsCount.value = data.total_count
				totalStats.value = data.statistics
			} else {
				resetTrendToEmpty()
			}
		} else {
			resetTrendToEmpty()
		}
	} catch (e) {
		resetTrendToEmpty()
	} finally {
		loadingTrend.value = false
	}
}

async function fetchWeeklyActivity() {
	loadingActivity.value = true
	try {
		const response = await analysisApi.getWeeklyActivity()
		if (response && response.success && response.data) {
			const d = response.data
			weeklyActivityData.value = d
			currentWears.value = d.total_wears_this_week ?? 0
			activityTrend.value = (d.trend_percent ?? 0) >= 0 ? 'increase' : 'decrease'
			animateCountUp(activityPercent, () => Math.abs(d.trend_percent ?? 0), 600)
		} else {
			weeklyActivityData.value = null
			if (analysisApi.isLoggedIn()) {
				console.warn('[Wardrobe Activity] Invalid API response; ensure GET /api/analysis/weekly-activity returns success and data. response:', response)
				currentWears.value = 0
			}
		}
	} catch (e) {
		weeklyActivityData.value = null
		if (analysisApi.isLoggedIn()) {
			console.error('[Wardrobe Activity] request failed:', e)
			currentWears.value = 0
		}
	} finally {
		loadingActivity.value = false
	}
}

async function fetchSummaryData() {
	try {
		const response = await analysisApi.getSummary()
		if (response && response.data && response.data.total_items != null) {
			totalItemsCount.value = response.data.total_items
		}
	} catch (e) {}
}

async function fetchCategoryDistribution() {
	if (!analysisApi.isLoggedIn()) {
		categoryData.value = []
		return
	}
	loadingCategory.value = true
	try {
		const response = await analysisApi.getCategoryDistribution()
		if (response && response.success && Array.isArray(response.data)) {
			categoryData.value = response.data.filter((d) => d && (Number(d.value) || 0) > 0)
		} else {
			categoryData.value = []
		}
	} catch (e) {
		categoryData.value = []
	} finally {
		loadingCategory.value = false
	}
}

async function fetchIdleRate() {
	try {
		const response = await analysisApi.getIdleRate(30)
		if (response && response.success && response.data) {
			const data = response.data
			totalItemsCount.value = data.total_items
			idleCount.value = data.idle_items
			animateCountUp(idlePercent, data.idle_rate, 800)
		} else {
			animateCountUp(idlePercent, totalItemsCount.value ? (idleCount.value / totalItemsCount.value * 100) : 0, 800)
		}
	} catch (e) {
		animateCountUp(idlePercent, totalItemsCount.value ? (idleCount.value / totalItemsCount.value * 100) : 0, 800)
	}
}

function normalizeTopPercent(raw) {
	if (raw == null || raw === '') return 0
	const n = Number(raw)
	if (Number.isNaN(n) || !Number.isFinite(n)) return 0
	return Math.max(0, Math.min(100, Math.round(n)))
}

async function fetchTopColor() {
	try {
		const response = await analysisApi.getTopColor()
		if (response && response.success && response.data?.top_color) {
			const tc = response.data.top_color
			topColorName.value = tc.color_name || '—'
			animateCountUp(topColorPercent, normalizeTopPercent(tc.percentage), 800)
			return
		}
	} catch (e) {
		if (analysisApi.isLoggedIn()) console.error('[WardrobeAnalysis] top-color:', e)
	}
	topColorName.value = 'No data'
	animateCountUp(topColorPercent, 0, 800)
}

async function fetchTopStyle() {
	try {
		const response = await analysisApi.getTopStyle()
		if (response && response.success && response.data?.top_style) {
			const ts = response.data.top_style
			topStyleName.value = ts.style_name || '—'
			animateCountUp(topStylePercent, normalizeTopPercent(ts.percentage), 800)
			return
		}
	} catch (e) {
		if (analysisApi.isLoggedIn()) console.error('[WardrobeAnalysis] top-style:', e)
	}
	topStyleName.value = 'No data'
	animateCountUp(topStylePercent, 0, 800)
}

async function fetchMostWornItems() {
	loadingWorn.value = true
	try {
		if (analysisApi.isLoggedIn()) {
			const response = await analysisApi.getMostWorn(viewByWorn.value, 5)
			if (response && response.success && response.data && response.data.items) {
				mostWorn.value = response.data.items.map(item => ({
					name: item.name,
					wears: parseInt(item.wears) || 0,
					color: item.color || 'gray'
				}))
			} else {
				clearMostWorn()
			}
		} else {
			clearMostWorn()
		}
	} catch (e) {
		clearMostWorn()
	} finally {
		loadingWorn.value = false
	}
}

watch(viewByTotal, () => {
	if (props.isLoggedIn) fetchTrendData()
})
watch(viewByWorn, () => {
	if (props.isLoggedIn) fetchMostWornItems()
})
watch(expandedView, (cur, prev) => {
	if (prev != null && cur === null) milestoneReplayTick.value++
})
watch(() => props.isLoggedIn, (loggedIn) => {
	if (loggedIn) {
		loadingTrend.value = true
		loadingWorn.value = true
		fetchTrendData()
		fetchSummaryData()
		fetchWeeklyActivity()
		fetchMostWornItems()
		fetchCategoryDistribution()
		fetchIdleRate()
		fetchTopColor()
		fetchTopStyle()
		hydrateSuggestedFromCacheOrFetch()
	} else {
		weeklyActivityData.value = null
		currentWears.value = 0
		loadingActivity.value = false
		loadingSuggested.value = false
		suggestedTexts.value = []
		suggestedAdditionsCache = null
		saveSuggestedCacheToStorage(null)
		categoryData.value = []
		loadingCategory.value = false
	}
})

onMounted(() => {
	const countUpDelay = 320
	animateCountUp(activityPercent, activityPercentTarget, 800, countUpDelay)
	animateCountUp(idlePercent, () => idlePercentTarget.value, 800, countUpDelay + 60)
	if (!props.isLoggedIn) {
		loadingTrend.value = false
		loadingWorn.value = false
		loadingSuggested.value = false
		loadingActivity.value = false
		return
	}
	hydrateSuggestedFromCacheOrFetch()
	Promise.all([
		fetchTrendData(),
		fetchSummaryData(),
		fetchWeeklyActivity(),
		fetchMostWornItems(),
		fetchCategoryDistribution(),
		fetchIdleRate(),
		fetchTopColor(),
		fetchTopStyle()
	]).then(() => {
		animateCountUp(activityPercent, activityPercentTarget, 400)
		animateCountUp(idlePercent, () => idlePercentTarget.value, 400)
	}).catch(() => {})
})
</script>

<style scoped>
.page {
	background: linear-gradient(165deg, #f2efe8 0%, #f5f0eb 40%, #f0ebe6 100%);
	padding: 30rpx;
	position: relative;
	overflow: hidden;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	min-height: 100%;
	box-sizing: border-box;
}

/* 展开页自带背景；此处若保留 padding 会与 scroll 区形成色差条 */
.page--expanded {
	padding: 0;
	min-height: 100%;
	height: 100%;
}

/* 光流背景：两枚高模糊光斑缓慢旋转，营造流动丝绸感 */
.bg-blob {
	position: absolute;
	width: 120%;
	height: 120%;
	left: 50%;
	top: 50%;
	transform: translate(-50%, -50%);
	border-radius: 50%;
	pointer-events: none;
	filter: blur(80px);
	opacity: 0.85;
}
.bg-blob-1 {
	background: radial-gradient(circle at 30% 40%, rgba(248, 242, 232, 0.95) 0%, rgba(242, 232, 218, 0.5) 40%, transparent 65%);
	animation: blob-rotate 28s linear infinite;
}
.bg-blob-2 {
	background: radial-gradient(circle at 70% 60%, rgba(232, 218, 212, 0.7) 0%, rgba(228, 208, 200, 0.4) 45%, transparent 70%);
	animation: blob-rotate 32s linear infinite reverse;
}
@keyframes blob-rotate {
	from { transform: translate(-50%, -50%) rotate(0deg); }
	to { transform: translate(-50%, -50%) rotate(360deg); }
}

/* 微纹理噪点图层：极低透明度，纸张/哑光质感 */
.grain-overlay {
	position: absolute;
	inset: 0;
	pointer-events: none;
	z-index: 1;
	opacity: 0.035;
	background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
	background-repeat: repeat;
}

.page-bento-wrap {
	display: block;
	position: relative;
	z-index: 2;
}

.filter-backdrop {
	position: absolute;
	inset: 0;
	z-index: 15;
	background: transparent;
}
.filter-backdrop:active { opacity: 0; }

/* Bento Grid Layout
 * 
 * 网格系统说明：
 * - 4列布局：grid-template-columns: 1.3fr 1.3fr 1.35fr 1.35fr
 *   前两列等宽(1.3fr)，后两列稍宽(1.35fr)，总共4列
 * - 4行布局：grid-template-rows: 0.65fr 0.65fr 0.45fr 1.35fr
 *   行高按比例分配
 * - 卡片间距：gap: 24rpx
 * 
 */
.bento-grid {
	display: grid;
	gap: 24rpx;
	grid-template-columns: 1.3fr 1.3fr 1.35fr 1.35fr;
	grid-template-rows: 0.65fr 0.65fr 0.45fr 1.35fr;
	overflow: visible;
	position: relative;
}
.bento-grid-filter-open {
	z-index: 20;
}

/* 渐进加载：每块卡片依次出现，Keynote 节奏 */
.bento-grid-entering > * {
	opacity: 0;
	animation: bento-item-enter 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.bento-grid-entering > *:nth-child(1) { animation-delay: 0s; }
.bento-grid-entering > *:nth-child(2) { animation-delay: 0.07s; }
.bento-grid-entering > *:nth-child(3) { animation-delay: 0.14s; }
.bento-grid-entering > *:nth-child(4) { animation-delay: 0.21s; }
.bento-grid-entering > *:nth-child(5) { animation-delay: 0.28s; }
.bento-grid-entering > *:nth-child(6) { animation-delay: 0.35s; }
.bento-grid-entering > *:nth-child(7) { animation-delay: 0.42s; }
@keyframes bento-item-enter {
	from {
		opacity: 0;
		transform: translateY(16rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

</style>

<style>
/* 主看板 ↔ expanded-pages（ActivityReport / IdleItemsView）：淡入 + 轻微纵向位移（仅 transition 根节点，侧栏不受影响） */
.page-enter-active {
	transition:
		opacity 0.44s cubic-bezier(0.22, 1, 0.36, 1),
		transform 0.44s cubic-bezier(0.22, 1, 0.36, 1);
}
.page-leave-active {
	transition:
		opacity 0.34s cubic-bezier(0.4, 0, 0.2, 1),
		transform 0.34s cubic-bezier(0.4, 0, 0.2, 1);
}
.page-enter-from {
	opacity: 0;
	transform: translateY(22px);
}
.page-leave-to {
	opacity: 0;
	transform: translateY(-14px);
}
</style>
