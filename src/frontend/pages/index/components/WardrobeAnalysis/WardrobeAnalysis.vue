<template>
	<view class="page">
		<!-- 光流背景：淡米色 + 藕粉色光斑，高模糊缓慢旋转 -->
		<view class="bg-blob bg-blob-1" aria-hidden="true"></view>
		<view class="bg-blob bg-blob-2" aria-hidden="true"></view>
		<!-- 微纹理噪点图层，消除塑料感 -->
		<view class="grain-overlay" aria-hidden="true"></view>
		<!-- 展开视图：Activity report / Idle items（页面切换过渡） -->
		<transition name="page" mode="out-in">
			<ActivityReport v-if="expandedView === 'activity-report'" key="activity-report" :total-wears="currentWears" :trend-value="activityPercentTarget" :is-increase="activityTrend === 'increase'" :week-data="weeklyActivityData?.week_data" :category-activity="weeklyActivityData?.category_activity" @back="expandedView = null" />
			<IdleItemsView v-else-if="expandedView === 'idle-items'" key="idle-items" :unworn-count="idleCount" @back="expandedView = null" />
			<view v-else key="bento" class="page-bento-wrap">
		<view v-if="filterOpen" class="filter-backdrop" @click="closeFilter"></view>

		<!-- Bento Grid（渐进加载；有下拉打开时提高层级，避免被背板挡住点击） -->
		<view class="bento-grid bento-grid-entering" :class="{ 'bento-grid-filter-open': filterOpen }" @click="filterOpen && closeFilter()">
			<!-- Activity：increase / decrease 随机展示其一，模板一致仅样式与文案不同 -->
			<view class="card bento-activity">
				<text class="card-label">Wardrobe Activity</text>
				<view v-if="loadingActivity" class="loading-state">
					<text class="loading-text">加载中...</text>
				</view>
				<template v-else>
				<view class="big-metric">
					<text class="metric-num">{{ currentWears }}</text>
					<view class="trend-badge" :class="{ 'trend-badge-decrease': activityTrend === 'decrease' }">
						<text class="metric-arrow" :class="{ 'metric-arrow-decrease': activityTrend === 'decrease' }">{{ activityTrend === 'increase' ? '↗' : '↘' }} {{ activityPercent }}%</text>
					</view>
				</view>
				<text class="card-sub">Total wears this week</text>
				</template>
				<text class="card-link" @click="goActivityReport">Activity report →</text>
			</view>

			<!-- Idle Rate -->
			<view class="card bento-idle">
				<text class="card-label">Idle Rate</text>
				<text class="metric-num">{{ idlePercent }}%</text>
				<text class="card-sub">You have {{ idleCount }} unworn items out of {{ totalItemsCount }} total.</text>
				<text class="card-link" @click="goIdleItems">See all idle items →</text>
			</view>

			<!-- Total Items（主卡）：数字美学 + 光流扫光 -->
			<view class="card card-elevation-main bento-total">
				<text class="bg-number" aria-hidden="true">{{ totalItemsCount }}</text>
				<view class="total-content-overlay">
					<view class="card-row">
						<text class="card-label">Total Items</text>
						<view class="filter-trigger" @click.stop="toggleViewBy('total')">
							<text>{{ viewByTotalLabel }}</text>
							<ViewByFilter v-model="viewByTotal" :visible="filterOpen === 'total'" @apply="closeFilter" />
						</view>
					</view>
					<view class="chart-container">
						<view v-if="!isLoggedIn" class="loading-state">
							<text class="loading-text">Please log in first</text>
						</view>
						<view v-else-if="loadingTrend" class="loading-state">
							<text class="loading-text">加载趋势数据...</text>
						</view>
						<template v-else>
							<template v-if="isSinglePointTrend">
								<view class="milestone-state">
									<text class="milestone-num">{{ displaySinglePointValue }}</text>
									<text class="milestone-desc">Items logged. Your wardrobe journey begins.</text>
								</view>
							</template>
							<template v-else>
								<svg viewBox="0 0 300 120" class="line-svg">
									<defs>
										<linearGradient id="greenGradient" x1="0" x2="0" y1="0" y2="1">
											<stop offset="0%" stop-color="#7cb97c" stop-opacity="0.28" />
											<stop offset="40%" stop-color="#7cb97c" stop-opacity="0.18" />
											<stop offset="70%" stop-color="#7cb97c" stop-opacity="0.08" />
											<stop offset="100%" stop-color="#7cb97c" stop-opacity="0" />
										</linearGradient>
										<filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
											<feGaussianBlur stdDeviation="3" result="blur" />
											<feComposite in="SourceGraphic" in2="blur" operator="over" />
										</filter>
									</defs>
									<line x1="0" y1="35" x2="300" y2="35" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
									<line x1="0" y1="60" x2="300" y2="60" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
									<line x1="0" y1="85" x2="300" y2="85" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
									<path :d="smoothPathArea" fill="url(#greenGradient)" class="line-area line-area-breathe" />
									<path
										:d="smoothPathStroke"
										fill="none"
										stroke="#7cb97c"
										stroke-width="3.5"
										stroke-linecap="round"
										stroke-linejoin="round"
										class="line-stroke line-stroke-glow"
										pathLength="1"
										filter="url(#neonGlow)"
									/>
								</svg>
								<view class="chart-labels">
									<text v-for="year in lineYears" :key="year" class="chart-label">{{ year }}</text>
								</view>
								<view class="chart-stats" v-if="totalStats && (totalStats.growth_rate != null || totalStats.projection)">
									<text class="stat-item" v-if="totalStats.growth_rate">增长率: {{ totalStats.growth_rate }}%</text>
									<text class="stat-item" v-if="totalStats.projection">预测{{ totalStats.projection_year }}: {{ totalStats.projection }}</text>
								</view>
							</template>
						</template>
					</view>
				</view>
				<view class="shimmer-sweep" aria-hidden="true"></view>
			</view>

			<!-- Most Worn -->
			<view class="card bento-worn">
				<view class="card-row">
					<text class="card-label">Most Worn Items</text>
					<view class="filter-trigger" @click.stop="toggleViewBy('worn')">
						<text>{{ viewByWornLabel }}</text>
						<ViewByFilter v-model="viewByWorn" :visible="filterOpen === 'worn'" @apply="closeFilter" />
					</view>
				</view>
				<view class="worn-list">
					<view v-if="!isLoggedIn" class="loading-state">
						<text class="loading-text">Please log in first</text>
					</view>
					<view v-else-if="loadingWorn" class="loading-state">
						<text class="loading-text">加载中...</text>
					</view>
					<template v-else>
					<view v-for="item in mostWornWithDot" :key="item.name" class="list-item">
						<view class="dot" :class="{ active: item.dotColor === '#5c6bc0', dark: item.dotColor === '#616161' }" :style="{ background: item.dotColor }"></view>
						<text class="item-title">{{ item.name }}</text>
<text class="item-wears">{{ item.wears }} wears</text>
				</view>
					</template>
			</view>
		</view>

			<!-- ⭐ Top Color + Top Style 堆叠 -->
			<view class="bento-stats">
				<view class="mini-card">
					<text class="card-label-small">Top color</text>
					<text class="mini-value">{{ topColorName || 'Brown' }}</text>
					<text class="mini-sub">{{ topColorPercent }}%</text>
				</view>
				<view class="mini-card">
					<text class="card-label-small">Top style</text>
					<text class="mini-value">{{ topStyleName || 'Sporty' }}</text>
					<text class="mini-sub">{{ topStylePercent }}%</text>
				</view>
			</view>

			<!-- Suggested Additions：电商推荐风格 + accordion 展开，仅点击刷新时更新 -->
			<view class="card bento-suggested">
				<view class="card-row suggested-card-row">
					<text class="card-label">Suggested Additions</text>
					<view v-if="isLoggedIn" class="suggested-refresh" :class="{ 'refreshing': loadingSuggested }" @click="refreshSuggestedAdditions">
						<text class="refresh-icon">↻</text>
					</view>
				</view>
				<view class="suggest-list">
					<view v-if="!isLoggedIn" class="loading-state">
						<text class="loading-text">Please log in first</text>
					</view>
					<view v-else-if="loadingSuggested" class="loading-state">
						<text class="loading-text">Generating suggestions...</text>
					</view>
					<view v-else-if="suggestedTexts.length === 0" class="suggest-empty">
						<text class="suggest-empty-text">No data</text>
					</view>
					<view
						v-else
						v-for="(sug, index) in suggestedTexts"
						:key="`${index}-${sug}`"
						class="suggest-card-v2"
						:class="{ 'suggest-card-v2-expanded': expandedSuggestIndices.includes(index), 'suggest-card-v2-hover': hoveredSuggestIndex === index }"
						@click="toggleSuggestExpanded(index)"
						@mouseenter="hoveredSuggestIndex = index"
						@mouseleave="hoveredSuggestIndex = null"
					>
						<view class="suggest-side">
							<text class="luxury-index">{{ String(index + 1).padStart(2, '0') }}</text>
							<view class="vertical-line"></view>
						</view>
						<view class="suggest-body">
							<text class="suggest-title">{{ parseSuggestLine(sug).title }}</text>
							<view class="suggest-accordion-grid" :class="{ expanded: expandedSuggestIndices.includes(index) }">
								<view class="suggest-accordion-inner">
									<text v-if="parseSuggestLine(sug).detail" class="suggest-detail">{{ parseSuggestLine(sug).detail }}</text>
									<view class="capability-tags">
										<text v-for="tag in getCapabilityTags(sug)" :key="tag" class="tag">{{ tag }}</text>
									</view>
								</view>
							</view>
						</view>
						<view class="item-ghost-icon" :class="{ visible: hoveredSuggestIndex === index }">✦</view>
					</view>
				</view>
			</view>

			<!-- ⭐ Category Breakdown（主卡） -->
			<view class="card card-elevation-main bento-category">
				<view class="card-row">
					<text class="card-label big-title">Category Breakdown</text>
					<view class="filter-trigger" @click="toggleCategoryType">
						<text>Type</text>
					</view>
				</view>
				<view class="donut-container">
					<svg viewBox="-100 -100 200 200" class="donut-svg" aria-hidden="true" @mouseleave="hoveredSegmentIndex = null">
						<path
							v-for="{ seg, originalIndex } in donutSegmentsForDraw"
							:key="originalIndex"
							:d="seg.path"
							:fill="seg.color"
							stroke="#ffffff"
							stroke-width="3.5"
							stroke-linecap="round"
							:class="['donut-path', { 'donut-path-enter': !donutEntranceDone, 'donut-path-hover': hoveredSegmentIndex === originalIndex }]"
							:style="{ animationDelay: donutEntranceDone ? undefined : originalIndex * 0.08 + 's' }"
							@mouseenter="hoveredSegmentIndex = originalIndex"
							@mouseleave="hoveredSegmentIndex = null"
						/>
						<circle cx="0" cy="0" r="52" fill="#ffffff" pointer-events="none" />
						<!-- 内圈：棕色点状环，圆头端点更柔和 -->
						<circle cx="0" cy="0" r="24" fill="none" stroke="#8d6e63" stroke-width="2" stroke-linecap="round" pathLength="100" stroke-dasharray="4 6" pointer-events="none" />
						<!-- 外圈：浅灰点状环，与内圈风格统一 -->
						<circle cx="0" cy="0" r="42" fill="none" stroke="#E5E0D8" stroke-width="2.5" stroke-linecap="round" pathLength="300" stroke-dasharray="3 9" pointer-events="none" />
					</svg>
					<view class="center-content">
						<view v-if="hoveredSegment" class="center-detail">
							<text class="center-detail-label">{{ hoveredSegment.label }}</text>
							<text class="center-detail-count">{{ hoveredSegment.value }} items</text>
						</view>
						<view v-else class="center-icon">
							<image src="/static/icons/icon-wardrobe.svg" mode="aspectFit" class="center-icon-img" />
						</view>
					</view>
					<view
						v-for="(seg, i) in donutSegments"
						:key="'lbl-' + i"
						:class="['floating-label', { 'floating-label-hover': hoveredSegmentIndex === i }]"
						:style="{ transform: `translate(${seg.labelY}px, ${-seg.labelX}px)`, textAlign: seg.align }"
					>
						<view class="floating-label-inner">
							<text class="label-text" :class="[seg.labelSize === 'xl' ? 'label-xl' : seg.labelSize === 'lg' ? 'label-lg' : 'label-sm']">{{ seg.label }}</text>
						</view>
					</view>
				</view>
			</view>
		</view>
			</view>
		</transition>
	</view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import ViewByFilter from './ViewByFilter.vue'
import ActivityReport from './ActivityReport.vue'
import IdleItemsView from './IdleItemsView.vue'
import { COLOR_HEX_BY_CODE } from '@/utils/wardrobeEnums.js'
import * as analysisApi from '@/api/analysisApi.js'
import {
	getMockTrendData,
	getMockWornData,
	DEFAULT_TOP_COLOR_NAME,
	DEFAULT_TOP_STYLE_NAME,
	MOCK_WEEKLY_TOTAL_WEARS
} from './mockData.js'

const SUGGESTED_CACHE_KEY = 'wardrobe_suggested_additions'

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

const props = defineProps({
	isLoggedIn: { type: Boolean, default: false }
})

/** 点击卡片内链接后展示的展开页 */
const expandedView = ref(null)
const filterOpen = ref(null)
const viewByTotal = ref('weekly')
const viewByWorn = ref('yearly')
const hoveredSegmentIndex = ref(null)
const donutEntranceDone = ref(false)

const activityTrend = ref(Math.random() >= 0.5 ? 'increase' : 'decrease')
const activityPercentTarget = computed(() => {
	if (weeklyActivityData.value != null && weeklyActivityData.value.trend_percent != null) {
		return Math.abs(weeklyActivityData.value.trend_percent)
	}
	return activityTrend.value === 'increase' ? 15 : 8
})

/** 本周活跃度 API 返回（null 表示未拉取或失败，用 mock） */
const weeklyActivityData = ref(null)
/** 本周总穿戴次数（来自 API 或 mock） */
const currentWears = ref(MOCK_WEEKLY_TOTAL_WEARS)
const activityPercent = ref(0)
const idlePercent = ref(0)
const topColorPercent = ref(0)
const topStylePercent = ref(0)
const loadingTrend = ref(true)
const loadingWorn = ref(true)
const loadingSuggested = ref(true)
const loadingActivity = ref(true)

const initialTrend = getMockTrendData('weekly')
const lineYears = ref(initialTrend.labels)
const lineData = ref(initialTrend.values)
const totalItemsCount = ref(initialTrend.total_count)
const totalStats = ref(null)
const idleCount = ref(0)
const topColorName = ref(DEFAULT_TOP_COLOR_NAME)
const topStyleName = ref(DEFAULT_TOP_STYLE_NAME)

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

/** Total Items 仅一个数据点（yearly 单点）时，从 0 上涨到该数字的动画，与其他 KPI 一致 */
function runSinglePointCountUp(delay = 0) {
	if (validTrendData.value.length !== 1) return
	displaySinglePointValue.value = 0
	requestAnimationFrame(() => {
		animateCountUp(displaySinglePointValue, () => singlePointValue.value ?? 0, 800, delay)
	})
}

const viewByTotalLabel = computed(() => viewByToLabel(viewByTotal.value))
const viewByWornLabel = computed(() => viewByToLabel(viewByWorn.value))
function viewByToLabel(v) {
	return v === 'yearly' ? 'Yearly' : v === 'monthly' ? 'Monthly' : 'Weekly'
}

const smoothPathStroke = computed(() => getSvgPath(lineData.value, 300, 120, false))
const smoothPathArea = computed(() => getSvgPath(lineData.value, 300, 120, true))

/** 趋势图有效数据（过滤 null/NaN），用于单点判断与里程碑数值 */
const validTrendData = computed(() => {
	const data = lineData.value
	if (!data || !Array.isArray(data)) return []
	return data.filter(v => v !== null && v !== undefined && !isNaN(v) && isFinite(v))
})

/** 仅 1 个数据点时为 true，此时展示里程碑排版而非折线图 */
const isSinglePointTrend = computed(() => validTrendData.value.length === 1)

/** 仅 1 个数据点时展示的数值（里程碑大数字）；用于动画的显示值，进入/回到页面时从 0 涨到目标 */
const displaySinglePointValue = ref(0)

/** 仅 1 个数据点时展示的数值（里程碑大数字）— 目标值，供动画与 fallback 使用 */
const singlePointValue = computed(() =>
	validTrendData.value.length === 1 ? validTrendData.value[0] : 0
)

function getSvgPath(data, width, height, isArea) {
	if (!data || !Array.isArray(data)) return ''
	const validData = data.filter(val => val !== null && val !== undefined && !isNaN(val) && isFinite(val))

	const padding = 10
	const chartH = height - padding * 2

	// 🛡️ 没数据时：只画一条贴底的占位线，不画绿色的面积
	if (validData.length === 0) {
		const y = height - padding
		if (isArea) return ''
		return `M 0,${y} L ${width},${y}`
	}

	// 🛡️ 只有 1 个数据点：不画 path，由 template 展示里程碑排版
	if (validData.length === 1) return ''

	const max = Math.max(...validData, 1)
	// 2 个及以上数据点：贝塞尔曲线 + 面积
	const stepX = width / (validData.length - 1)
	const points = validData.map((val, i) => {
		const x = i * stepX
		const y = height - padding - (val / max) * chartH
		return [x, y]
	})

	let d = `M ${points[0][0]},${points[0][1]}`
	for (let i = 0; i < points.length - 1; i++) {
		const p0 = points[i]
		const p1 = points[i + 1]
		const midX = (p0[0] + p1[0]) / 2
		const cp1x = p0[0] + (midX - p0[0]) * 0.6
		const cp2x = midX + (p1[0] - midX) * 0.4
		d += ` C ${cp1x},${p0[1]} ${cp2x},${p1[1]} ${p1[0]},${p1[1]}`
	}

	if (isArea) {
		// 正常情况的填充闭合
		d += ` L ${width},${height} L 0,${height} Z`
	}

	return d
}

const categoryData = ref([
	{ label: 'Top', value: 35, color: '#FCD568' },
	{ label: 'Bottom', value: 25, color: '#68C5FA' },
	{ label: 'Footwear', value: 10, color: '#A694F5' },
	{ label: 'Outerwear', value: 15, color: '#FF69B4' },
	{ label: 'Accessories', value: 15, color: '#E57373' }
])

/**
 * 圆环图（Category Breakdown）每个扇形的路径与标签位置
 * 坐标系：SVG viewBox="-100 -100 200 200"，圆心 (0,0)，单位与 viewBox 一致
 */
const donutSegments = computed(() => {
	let startAngle = 0
	const total = categoryData.value.reduce((a, b) => a + b.value, 0)

	// ---------- 圆环几何（扇形本身）----------
	const r1 = 52 // 圆环「内半径」：空心内圈的半径
	const maxValue = Math.max(...categoryData.value.map((d) => d.value), 1)
	const baseRadius = 76 // 圆环「外半径」基准值
	const radiusRange = 24 // 外半径随数值变化的幅度（数值越大扇形外缘越突出）
	// r2 = 圆环「外半径」：该扇形外弧的半径（可选：item.outerRadius 或按数值计算）

	// ---------- 文字标签半径 ----------
	const defaultLabelGap = 110 // 从「扇形外缘」到「文字锚点」的距离，越大文字越靠外（略外推避免遮挡）

	return categoryData.value.map((item) => {
		const r2 = item.outerRadius ?? (baseRadius + (item.value / maxValue) * radiusRange)

		// 扇形角度与弧线端点（弧度）
		const sliceAngle = (item.value / total) * 2 * Math.PI // 该扇形占的弧度
		const endAngle = startAngle + sliceAngle // 扇形结束角度

		// 扇形四顶点（外弧两点 + 内弧两点），用于绘制 SVG path
		const x1 = Math.cos(startAngle) * r2
		const y1 = Math.sin(startAngle) * r2
		const x2 = Math.cos(endAngle) * r2
		const y2 = Math.sin(endAngle) * r2
		const x3 = Math.cos(endAngle) * r1
		const y3 = Math.sin(endAngle) * r1
		const x4 = Math.cos(startAngle) * r1
		const y4 = Math.sin(startAngle) * r1

		const largeArc = sliceAngle > Math.PI ? 1 : 0 // 大弧/小弧标志
		const path = `M ${x4} ${y4} L ${x1} ${y1} A ${r2} ${r2} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${r1} ${r1} 0 ${largeArc} 0 ${x4} ${y4} Z`

		// ---------- 文字标签位置（浮在圆环外）----------
		const midAngle = startAngle + sliceAngle / 2 // 扇形中线角度
		const angleOffsetRad = ((item.labelAngleOffset ?? 0) * Math.PI) / 180 // 可选：每项 labelAngleOffset 度数微调
		const labelAngle = midAngle + angleOffsetRad // 标签所在角度
		const labelR = r2 + defaultLabelGap + (item.labelRadiusOffset ?? 0) // 标签锚点的半径（越大越靠外）
		const labelX = Math.cos(labelAngle) * labelR // 标签 X（用于 floating-label 的 transform）
		const labelY = Math.sin(labelAngle) * labelR // 标签 Y（用于 floating-label 的 transform）

		// 标签对齐：右半圆左对齐、左半圆右对齐，让文字朝外
		const align = Math.cos(labelAngle) > 0 ? 'left' : 'right'
		// 标签字号：可选 item.labelSize，否则按 value 分 xl / lg / sm
		const labelSize = item.labelSize ?? (item.value >= 30 ? 'xl' : item.value >= 20 ? 'lg' : 'sm')

		startAngle = endAngle
		return { ...item, path, labelX, labelY, align, labelSize }
	})
})

/** 用于绘制：hover 的扇形移到最后绘制，避免被两侧挡住 */
const donutSegmentsForDraw = computed(() => {
	const list = donutSegments.value.map((seg, originalIndex) => ({ seg, originalIndex }))
	const hovered = hoveredSegmentIndex.value
	if (hovered == null) return list
	const [item] = list.splice(hovered, 1)
	list.push(item)
	return list
})

/** 悬停的扇形，用于中心显示详情 */
const hoveredSegment = computed(() => {
	const i = hoveredSegmentIndex.value
	if (i == null) return null
	return donutSegments.value[i] ?? null
})

const mostWorn = ref([
	{ name: 'White Cotton T-shirt', wears: 35, color: 'white' },
	{ name: 'Classic Denim Jacket', wears: 28, color: 'blue' },
	{ name: 'Black Knit Top', wears: 27, color: 'black' },
	{ name: 'Khaki Chino Pants', wears: 24, color: 'brown' },
	{ name: 'Navy Striped Tee', wears: 22, color: 'navy' }
])
/** 从「red, light green, white, orange」这类多色字符串中取第一个颜色 code，用于小圆点 */
function firstColorCode(colorStr) {
	if (!colorStr || typeof colorStr !== 'string') return 'gray'
	const first = colorStr.split(',')[0].trim()
	if (!first) return 'gray'
	return first.replace(/\s+/g, '_').toLowerCase()
}

const mostWornWithDot = computed(() =>
	mostWorn.value.map((item) => {
		const code = firstColorCode(item.color)
		return {
			...item,
			dotColor: COLOR_HEX_BY_CODE[code] || '#9e9e9e'
		}
	})
)

const suggestedTexts = ref([])
/** 手风琴：当前展开的建议项索引（null 表示全收拢） */
/** 已展开的建议项索引集合，允许多条同时展开 */
const expandedSuggestIndices = ref([])
function toggleSuggestExpanded(index) {
	const arr = expandedSuggestIndices.value
	if (arr.includes(index)) {
		expandedSuggestIndices.value = arr.filter((i) => i !== index)
	} else {
		expandedSuggestIndices.value = [...arr, index]
	}
}
/** 悬停的建议项，用于幽灵图标显现 */
const hoveredSuggestIndex = ref(null)

/** 解析单条建议：首句为标题，其余为详情 */
function parseSuggestLine(sug) {
	if (!sug || typeof sug !== 'string') return { title: '', detail: '' }
	const parts = sug.split('，')
	const title = parts[0]?.trim() || ''
	const detail = parts.slice(1).join('，').trim()
	return { title, detail }
}

/** 从文案中推断能力标签（平衡/百搭/正式等） */
function getCapabilityTags(sug) {
	if (!sug || typeof sug !== 'string') return ['#Essential']
	const t = sug
	const tags = []
	if (/平衡|balance|搭配|協調/i.test(t)) tags.push('#Balance')
	if (/百搭|versatility|多樣|多用/i.test(t)) tags.push('#Versatility')
	if (/正式|formal|場合|office/i.test(t)) tags.push('#Formal')
	if (/基礎|essential|必備|基本/i.test(t)) tags.push('#Essential')
	if (/下装|下裝|褲|裙|bottom/i.test(t)) tags.push('#WardrobeBalance')
	if (tags.length === 0) tags.push('#Essential')
	return tags.slice(0, 3)
}

function toggleViewBy(which) {
	filterOpen.value = filterOpen.value === which ? null : which
}
function closeFilter() {
	filterOpen.value = null
}
/** 预留：Category 维度切换（如 Type/Season），目前仅作为按钮占位 */
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

function setMockTrendData() {
	const mock = getMockTrendData(viewByTotal.value)
	lineYears.value = mock.labels
	lineData.value = mock.values
	totalItemsCount.value = mock.total_count
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
				setMockTrendData()
			}
		} else {
			setMockTrendData()
		}
	} catch (e) {
		setMockTrendData()
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
				console.warn('[Wardrobe Activity] API 未返回有效数据，请确认后端 /api/analysis/weekly-activity 已启动且返回 success+data。response:', response)
				currentWears.value = 0
			}
		}
	} catch (e) {
		weeklyActivityData.value = null
		if (analysisApi.isLoggedIn()) {
			console.error('[Wardrobe Activity] 请求失败:', e)
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
	try {
		const response = await analysisApi.getCategoryDistribution()
		if (response && response.success && response.data) {
			categoryData.value = response.data
		}
	} catch (e) {}
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

async function fetchTopColor() {
	try {
		const response = await analysisApi.getTopColor()
		if (response && response.success && response.data) {
			const data = response.data
			topColorName.value = data.top_color.color_name
			animateCountUp(topColorPercent, data.top_color.percentage, 800)
		}
	} catch (e) {}
}

async function fetchTopStyle() {
	try {
		const response = await analysisApi.getTopStyle()
		if (response && response.success && response.data) {
			const data = response.data
			topStyleName.value = data.top_style.style_name
			animateCountUp(topStylePercent, data.top_style.percentage, 800)
		}
	} catch (e) {}
}

function setMockWornData(timeRange) {
	mostWorn.value = getMockWornData(timeRange)
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
				setMockWornData(viewByWorn.value)
			}
		} else {
			setMockWornData(viewByWorn.value)
		}
	} catch (e) {
		setMockWornData(viewByWorn.value)
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
	if (prev != null && cur === null) runSinglePointCountUp(320)
})
/** 监听单点目标值：资料到位后自动触发滚动动画，避免登入/切筛选/慢 API 时中间数字卡在 0 */
watch(singlePointValue, (newVal, oldVal) => {
	if (isSinglePointTrend.value && newVal !== oldVal) runSinglePointCountUp()
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
		// Suggested Additions：先从 sessionStorage 还原（切页后模块可能重载），有缓存则不请求
		const cached = suggestedAdditionsCache ?? loadSuggestedCacheFromStorage()
		if (cached != null) {
			suggestedAdditionsCache = cached
			suggestedTexts.value = cached
			loadingSuggested.value = false
		} else {
			loadingSuggested.value = true
			fetchSuggestedAdditions()
		}
	} else {
		weeklyActivityData.value = null
		currentWears.value = MOCK_WEEKLY_TOTAL_WEARS
		loadingActivity.value = false
		loadingSuggested.value = false
		suggestedTexts.value = []
		suggestedAdditionsCache = null
		saveSuggestedCacheToStorage(null)
	}
})

onMounted(() => {
	// 等所有扇形入场动画结束后再移除 donut-path-enter（最末段 delay 约 0.56s + 动画 0.8s ≈ 1.4s）
	setTimeout(() => { donutEntranceDone.value = true }, 1600)
	const countUpDelay = 320
	animateCountUp(activityPercent, activityPercentTarget, 800, countUpDelay)
	animateCountUp(idlePercent, () => idlePercentTarget.value, 800, countUpDelay + 60)
	animateCountUp(topColorPercent, 38, 800, countUpDelay + 120)
	animateCountUp(topStylePercent, 45, 800, countUpDelay + 180)
	if (!props.isLoggedIn) {
		loadingTrend.value = false
		loadingWorn.value = false
		loadingSuggested.value = false
		loadingActivity.value = false
		return
	}
	// Suggested Additions：先从 sessionStorage 还原（切页后可能重载），有缓存则不请求
	const cached = suggestedAdditionsCache ?? loadSuggestedCacheFromStorage()
	if (cached != null) {
		suggestedAdditionsCache = cached
		suggestedTexts.value = cached
		loadingSuggested.value = false
	} else {
		loadingSuggested.value = true
		fetchSuggestedAdditions()
	}
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
		// 单点里程碑动画改由 watch(singlePointValue) 在资料到位时触发，此处不再重复调用
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
	position: fixed;
	inset: 0;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
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
	position: fixed;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
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
 * 如何调整卡片位置和大小：
 * 1. 调整列跨度：grid-column: 1 (占1列) 或 grid-column: 1 / 3 (占2列) 或 grid-column: 3 / 5 (占2列)
 * 2. 调整行跨度：grid-row: 1 (占1行) 或 grid-row: 2 / 4 (占2行)
 * 3. 调整列宽比例：修改 grid-template-columns，例如改为 1fr 1fr 2fr 2fr 会让右侧更宽
 * 4. 调整卡片间距：修改 gap 值
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

/* 卡片通用样式：玻璃拟态 + 弥散阴影（::after 有色模糊层），无 box-shadow
 * - 主卡 .card-elevation-main：弥散层更明显
 * - 普通卡 .card：中等弥散
 * - 小卡 .mini-card：弱弥散 + 边框
 */
/* 普通卡：玻璃拟态 + 弥散阴影；overflow: visible 避免裁切下拉等浮层 */
.card {
	position: relative;
	background: rgba(255, 254, 251, 0.88);
	backdrop-filter: blur(20rpx);
	-webkit-backdrop-filter: blur(20rpx);
	border-radius: 20rpx;
	padding: 28rpx 32rpx;
	display: flex;
	flex-direction: column;
	overflow: visible;
	border: 1rpx solid rgba(255, 255, 255, 0.6);
}
.card::after {
	content: '';
	position: absolute;
	z-index: -1;
	left: 8rpx;
	top: 8rpx;
	right: -4rpx;
	bottom: -4rpx;
	border-radius: 22rpx;
	background: linear-gradient(145deg, rgba(168, 212, 168, 0.14) 0%, rgba(200, 188, 180, 0.08) 50%, rgba(180, 200, 200, 0.06) 100%);
	filter: blur(24rpx);
	opacity: 0.95;
}
/* 主卡：弥散层略大、略浓 */
.card-elevation-main::after {
	left: 12rpx;
	top: 12rpx;
	right: -6rpx;
	bottom: -6rpx;
	border-radius: 24rpx;
	background: linear-gradient(150deg, rgba(168, 212, 168, 0.18) 0%, rgba(210, 195, 185, 0.1) 45%, rgba(190, 205, 200, 0.08) 100%);
	filter: blur(32rpx);
}

.card-label {
	font-size: 30rpx;
	font-family: "Semi Bold";
	font-weight: 700;
	color: #1d1d1f;
	margin-bottom: 12rpx;
}

.big-title {
	font-size: 40rpx;
	font-weight: 900;
}

.card-sub {
	margin-top: 10rpx;
	font-size: 28rpx;
	color: #777;
	line-height: 1.45;
}

.card-link {
	margin-top: 16rpx;
	display: inline-block;
	font-size: 22rpx;
	color: #9c6b2f;
	font-weight: 600;
	transition: opacity 0.15s ease, transform 0.15s ease;
}
.card-link:active {
	opacity: 0.75;
	transform: scale(0.98);
}

/* 顶栏两卡：链接吸底 */
.bento-activity,
.bento-idle {
	display: flex;
	flex-direction: column;
}
.bento-activity .card-link,
.bento-idle .card-link {
	margin-top: auto;
	padding-top: 20rpx;
	border-top: 1rpx solid rgba(0, 0, 0, 0.04);
}

/* Metric */
.metric-num {
	font-size: 86.4rpx;
	font-weight: 700;
	font-family: "Medium";
	color: #1d1d1f;
	line-height: 1;
	margin-right: 12rpx;
}

.big-metric {
	display: flex;
	align-items: center;
	gap: 10rpx;
	margin-top: 8rpx;
	margin-bottom: 8rpx;
}

.trend-badge {
	background: rgba(124, 185, 124, 0.15);
	padding: 6rpx 16rpx;
	width: auto;
	border-radius: 999rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}
.trend-badge-decrease {
	background: rgba(200, 100, 80, 0.18);
}

.metric-arrow {
	color: #5a9d5a;
	font-size: 28rpx;
	font-weight: bold;
	line-height: 1;
}
.metric-arrow-decrease {
	color: #b85541;
}

/* Dropdown Row */
.card-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16rpx;
}

.filter-trigger {
	display: inline-flex;
	align-items: center;
	gap: 4rpx;
	font-size: 24rpx;
	color: #6b6b6b;
	padding: 8rpx 14rpx;
	border-radius: 16rpx;
	background: #f5f5f3;
	border: 1rpx solid rgba(0, 0, 0, 0.06);
	position: relative;
	transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}
.filter-trigger:active {
	background: #ebebe8;
	border-color: rgba(0, 0, 0, 0.08);
	transform: scale(0.98);
}
.arrow-down {
	font-size: 20rpx;
	color: #8e8e8e;
	opacity: 0.9;
}

/* Chart Container */
.chart-container {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
	padding-top: 28rpx;
}
.loading-state {
	display: flex;
	justify-content: center;
	align-items: center;
	min-height: 180rpx;
}
.loading-text {
	color: #999;
	font-size: 28rpx;
}
.chart-stats {
	margin-top: 20rpx;
	display: flex;
	flex-wrap: wrap;
	gap: 20rpx;
	font-size: 24rpx;
	color: #666;
}
.stat-item {
	background: #f5f5f3;
	padding: 6rpx 16rpx;
	border-radius: 20rpx;
}

.line-svg {
	width: 100%;
	height: 100%;
	min-height: 180rpx;
	display: block;
}

/* 曲线下绿色填充：呼吸感（用 CSS 动画，兼容性更好） */
.line-area-breathe {
	animation: line-area-breathe 4s ease-in-out infinite;
}
@keyframes line-area-breathe {
	0%, 100% { opacity: 0.55; }
	50% { opacity: 1; }
}

/* 折线：发光 + 进入动画 */
.line-stroke {
	stroke-dasharray: 1;
	stroke-dashoffset: 1;
	animation: drawLine 600ms ease-out forwards;
}
.line-stroke-glow {
	filter: url(#neonGlow);
}
@keyframes drawLine {
	to {
		stroke-dashoffset: 0;
	}
}

.chart-labels {
	display: flex;
	justify-content: space-between;
	font-size: 20rpx;
	color: #b0b0b0;
	margin-top: 12rpx;
	font-weight: 400;
}

.chart-label {
	font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}

/* 单年数据：里程碑排版 (Editorial Empty State) */
.milestone-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	min-height: 200rpx;
	padding: 32rpx 24rpx;
}
.milestone-num {
	font-size: 120rpx;
	font-weight: 200;
	line-height: 1.1;
	color: #1d1d1f;
	font-family: Georgia, 'Times New Roman', serif;
	letter-spacing: -0.04em;
}
.milestone-desc {
	margin-top: 16rpx;
	font-size: 26rpx;
	font-weight: 400;
	color: #8e8e93;
	letter-spacing: 0.02em;
	text-align: center;
	max-width: 420rpx;
}

/* Most Worn Items - 优化排版 */
.bento-worn {
	display: flex;
	flex-direction: column;
}

.bento-worn .card-row {
	margin-bottom: 20rpx;
}

.worn-list {
	display: flex;
	flex-direction: column;
	gap: 28rpx;
	margin-top: 12rpx;
	flex: 1;
}

.list-item {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-bottom: 15rpx;
	min-height: 44rpx;
}
.item-wears {
	font-size: 26rpx;
	font-weight: 600;
	color: #666;
	letter-spacing: 0.02em;
	flex-shrink: 0;
	width: 140rpx;
	text-align: right;
}

.dot {
	width: 30rpx;
	height: 30rpx;
	border-radius: 50%;
	flex-shrink: 0;
	margin-top: 2rpx;
	border: 2.5rpx solid rgba(255, 255, 255, 0.95);
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15), inset 0 1rpx 3rpx rgba(255, 255, 255, 0.6);
}

.dot.active {
	background: #4a7bd0;
}

.dot.dark {
	background: #444;
}

.item-title {
	flex: 1;
	min-width: 0;
	font-size: 28rpx;
	font-weight: 600;
	font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	color: #1d1d1f;
	line-height: 1.4;
	letter-spacing: -0.01em;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.bento-worn .card-link {
	margin-top: auto;
	padding-top: 24rpx;
	border-top: 1rpx solid rgba(0, 0, 0, 0.05);
}

.bold {
	color: #9c6b2f;
	font-weight: 600;
}

/* ⭐ Mini stacked stats - Top Color/Style 堆叠卡片容器
 * 
 * 调整堆叠卡片的方法：
 * 1. 调整两个小卡片之间的间距：修改 gap（当前 20rpx）
 *    - 更紧凑：gap: 16rpx;
 *    - 更宽松：gap: 24rpx;
 * 
 * 2. 调整堆叠方向：改为横向堆叠
 *    - flex-direction: row; (横向)
 *    - 当前：flex-direction: column; (纵向)
 * 
 * 3. 调整整体高度：添加 min-height
 *    - min-height: 200rpx;
 */
.bento-stats {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

/* 小卡：玻璃拟态 + 光影逻辑 hover，与全局风格一致 */
.mini-card {
	position: relative;
	background: rgba(255, 255, 255, 0.65);
	backdrop-filter: blur(20rpx);
	-webkit-backdrop-filter: blur(20rpx);
	border-radius: 20rpx;
	padding: 24rpx;
	border: 1rpx solid rgba(255, 255, 255, 0.4);
	display: flex;
	flex-direction: column;
	transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
}
.mini-card::after {
	content: '';
	position: absolute;
	z-index: -1;
	left: 4rpx;
	top: 4rpx;
	right: -2rpx;
	bottom: -2rpx;
	border-radius: 22rpx;
	background: linear-gradient(145deg, rgba(168, 212, 168, 0.08) 0%, rgba(200, 188, 180, 0.05) 100%);
	filter: blur(16rpx);
	opacity: 0.9;
	transition: filter 0.5s cubic-bezier(0.23, 1, 0.32, 1), background 0.5s ease, opacity 0.5s ease;
}
.mini-card:hover {
	background: rgba(255, 254, 251, 0.92);
	border-color: rgba(141, 110, 99, 0.25);
	transform: translateY(-6rpx) translateZ(10px);
	box-shadow: 0 10rpx 30rpx rgba(141, 110, 99, 0.05);
}
.mini-card:hover::after {
	filter: blur(24rpx);
	background: linear-gradient(145deg, rgba(168, 212, 168, 0.12) 0%, rgba(200, 188, 180, 0.1) 100%);
	opacity: 1;
}

.card-label-small {
	font-size: 24rpx;
	font-weight: 500;
	color: #888;
	display: block;
	letter-spacing: 0.02em;
	transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.mini-value {
	font-size: 36rpx;
	font-weight: 800;
	margin-top: 6rpx;
	color: #7a4e18;
	display: block;
	letter-spacing: 0.01em;
	transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), color 0.4s ease;
}
.mini-card:hover .mini-value {
	transform: translateY(-2rpx);
	color: #5d4037;
}

.mini-sub {
	font-size: 22rpx;
	font-weight: 400;
	color: #999;
	margin-top: 4rpx;
	display: block;
}

/* Suggested Additions - 玻璃拟态 + 弥散阴影 */
.bento-suggested {
	position: relative;
	display: flex;
	flex-direction: column;
	padding: 20rpx 24rpx 24rpx;
	background: rgba(255, 254, 251, 0.88);
	backdrop-filter: blur(20rpx);
	-webkit-backdrop-filter: blur(20rpx);
	border-radius: 20rpx;
	border: 1rpx solid rgba(141, 110, 99, 0.12);
}
.bento-suggested::after {
	content: '';
	position: absolute;
	z-index: -1;
	left: 8rpx;
	top: 8rpx;
	right: -4rpx;
	bottom: -4rpx;
	border-radius: 22rpx;
	background: linear-gradient(145deg, rgba(141, 110, 99, 0.08) 0%, rgba(200, 188, 180, 0.06) 100%);
	filter: blur(24rpx);
	opacity: 0.9;
}

.suggested-card-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 4rpx;
}

.bento-suggested .card-label {
	margin-bottom: 0;
	font-size: 32rpx;
	font-weight: 800;
	color: #1d1d1f;
	letter-spacing: 0.02em;
}

.suggested-refresh {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 56rpx;
	height: 56rpx;
	border-radius: 50%;
	background: rgba(141, 110, 99, 0.08);
	touch-action: manipulation;
}
.suggested-refresh:active {
	background: rgba(141, 110, 99, 0.16);
}
.suggested-refresh.refreshing .refresh-icon {
	animation: suggest-refresh-spin 0.8s linear infinite;
}

.refresh-icon {
	font-size: 36rpx;
	font-weight: 600;
	color: #8b7a6b;
	line-height: 1;
}

@keyframes suggest-refresh-spin {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}

.suggest-list {
	display: flex;
	flex-direction: column;
	gap: 0;
	margin-top: 26rpx;
	perspective: 1200rpx;
}

/* 互动式购物卡片 v2：杂志化手风琴 + 幽灵图标 + 3D 倾斜 + 极光扫光 */
.suggest-card-v2 {
	position: relative;
	padding: 30rpx 0;
	padding-right: 56rpx;
	border-bottom: 1rpx solid rgba(0, 0, 0, 0.04);
	display: flex;
	align-items: flex-start;
	gap: 36rpx;
	transform-style: preserve-3d;
	transition: background 0.6s cubic-bezier(0.16, 1, 0.3, 1),
		padding-left 0.6s cubic-bezier(0.16, 1, 0.3, 1),
		transform 0.6s cubic-bezier(0.16, 1, 0.3, 1),
		box-shadow 0.6s cubic-bezier(0.16, 1, 0.3, 1);
	cursor: pointer;
	overflow: visible;
}
/* 左侧极光扫光：悬停时像扫描仪亮起 */
.suggest-card-v2::before {
	content: '';
	position: absolute;
	left: 0;
	top: 0;
	width: 4rpx;
	height: 100%;
	background: #8b7a6b;
	transform: scaleY(0);
	transform-origin: center top;
	transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
	box-shadow: 0 0 15rpx #8b7a6b;
	pointer-events: none;
	z-index: 0;
}
.suggest-card-v2:first-child {
	padding-top: 20rpx;
}
.suggest-card-v2:last-child {
	border-bottom: none;
}
.suggest-card-v2:hover,
.suggest-card-v2.suggest-card-v2-hover {
	background: rgba(141, 110, 99, 0.04);
	padding-left: 20rpx;
	transform: translateX(12rpx) translateY(-2rpx) rotateX(2deg) rotateY(-2deg);
	box-shadow: -10rpx 0 30rpx rgba(141, 110, 99, 0.08);
}
.suggest-card-v2:hover::before,
.suggest-card-v2.suggest-card-v2-hover::before {
	transform: scaleY(1);
}
.suggest-card-v2-expanded {
	background: rgba(141, 110, 99, 0.03);
}

.suggest-side {
	flex-shrink: 0;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 12rpx;
	margin-left: 20rpx;
}
.luxury-index {
	font-family: "Didot", "Playfair Display", Georgia, serif;
	font-style: italic;
	font-size: 36rpx;
	color: #8b7a6b;
	opacity: 0.6;
	line-height: 1;
}
.vertical-line {
	width: 1rpx;
	flex: 1;
	min-height: 24rpx;
	background: linear-gradient(to bottom, rgba(139, 122, 107, 0.25), transparent);
	border-radius: 1rpx;
}

.suggest-body {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}
.suggest-title {
	display: block;
	font-size: 30rpx;
	font-weight: 700;
	color: #2c2c2c;
	margin-bottom: 4rpx;
	line-height: 1.35;
}
.suggest-accordion-grid {
	display: grid;
	grid-template-rows: 0fr;
	transition: grid-template-rows 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.suggest-accordion-grid.expanded {
	grid-template-rows: 1fr;
}
.suggest-accordion-inner {
	overflow: hidden;
	min-height: 0;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}
.suggest-detail {
	font-size: 26rpx;
	color: #888;
	line-height: 1.6;
	display: block;
}
.capability-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
}
.suggest-card-v2 .tag {
	font-size: 18rpx;
	color: #8b7a6b;
	padding: 4rpx 12rpx;
	background: rgba(141, 110, 99, 0.06);
	border-radius: 4rpx;
	text-transform: uppercase;
	letter-spacing: 1rpx;
}

.item-ghost-icon {
	position: absolute;
	right: 48rpx;
	top: 50%;
	transform: translateY(-50%);
	font-size: 40rpx;
	color: rgba(212, 175, 55, 0.35);
	opacity: 0.4;
	transition: opacity 0.3s ease, transform 0.3s ease, color 0.3s ease;
}
.item-ghost-icon.visible {
	opacity: 1;
	color: #c9a227;
	transform: translateY(-50%) translateX(-6rpx);
}

.suggest-empty {
	padding: 12rpx 4rpx 6rpx;
}

.suggest-empty-text {
	font-size: 25rpx;
	color: #8b7a6b;
}

/* Donut */
.donut-container {
	flex: 1;
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 40rpx 20rpx;
	min-height: 320rpx;
}

.donut-svg {
	width: 100%;
	height: 100%;
	max-height: 800rpx;
	overflow: visible;
	transform: rotate(-90deg);
}

/* 1. 初始状态：完全平面 */
.donut-path {
	transform-origin: 50% 50%;
	transition: opacity 0.4s cubic-bezier(0.17, 0.67, 0.83, 0.67),
		transform 0.4s cubic-bezier(0.17, 0.67, 0.83, 0.67),
		filter 0.4s cubic-bezier(0.17, 0.67, 0.83, 0.67);
	cursor: pointer;
	transform: translateZ(0);
	filter: drop-shadow(0 0 0 rgba(0, 0, 0, 0));
}
.donut-path.donut-path-enter {
	animation: donut-segment-enter 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) backwards;
}
/* 容器 hover 时，所有扇形先变暗 */
.donut-svg:hover .donut-path {
	opacity: 0.6;
	filter: drop-shadow(0 0 0 rgba(0, 0, 0, 0)) grayscale(0.2);
}
/* 2. 当前 hover 的扇形：保持明亮并长出厚度（多层 drop-shadow 模拟侧边） */
.donut-svg .donut-path:hover,
.donut-svg .donut-path.donut-path-hover {
	opacity: 1;
	transform: translateY(-10rpx) translateZ(20rpx);
	filter: grayscale(0)
		drop-shadow(0 2rpx 0 rgba(0, 0, 0, 0.1))
		drop-shadow(0 4rpx 0 rgba(0, 0, 0, 0.1))
		drop-shadow(0 6rpx 0 rgba(0, 0, 0, 0.1))
		drop-shadow(0 8rpx 0 rgba(0, 0, 0, 0.15))
		drop-shadow(0 20rpx 30rpx rgba(0, 0, 0, 0.1));
}
/* 统一上升入场：自下而上 + 淡入，每个扇形仅 delay 递增 */
@keyframes donut-segment-enter {
	from {
		opacity: 0;
		transform: translateY(24px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.center-content {
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	pointer-events: none;
	width: 140rpx;
	height: 140rpx;
	border-radius: 50%;
	background: #fff;
	box-shadow: 0 6rpx 20rpx rgba(0, 0, 0, 0.06);
	display: flex;
	align-items: center;
	justify-content: center;
}

.center-icon {
	display: flex;
	align-items: center;
	justify-content: center;
}

.center-icon-img {
	width: 64rpx;
	height: 64rpx;
	opacity: 0.8;
}

.center-detail {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 0 16rpx;
}

.center-detail-label {
	font-size: 28rpx;
	font-weight: 700;
	color: #1d1d1f;
	text-align: center;
	letter-spacing: 0.02em;
}

.center-detail-count {
	font-size: 16rpx;
	font-weight: 500;
	color: #666;
	margin-top: 6rpx;
	text-align: center;
}

.floating-label {
	position: absolute;
	top: 50%;
	left: 50%;
	pointer-events: none;
	width: 120rpx;
	margin-left: -60rpx;
	margin-top: -10rpx;
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 10;
}
.floating-label-inner {
	transition: transform 0.4s cubic-bezier(0.17, 0.67, 0.83, 0.67);
	display: flex;
	justify-content: center;
	align-items: center;
}
.floating-label.floating-label-hover .floating-label-inner {
	transform: scale(1.1) translateY(-16rpx);
}
.floating-label.floating-label-hover .label-text {
	color: #5d4037;
}

.label-text {
	font-weight: 700;
	color: #8d6e63;
	font-family: "Didot", "Bodoni MT", serif;
	line-height: 1.2;
	transition: color 0.2s ease, transform 0.2s ease;
}

.label-xl { font-size: 72rpx; }
.label-lg { font-size: 54rpx; }
.label-sm { font-size: 32rpx; }

/* ⭐ Grid Placement - 卡片位置和大小配置
 * 
 * 每个卡片的布局调整说明：
 * 
 * 1. Wardrobe Activity (左上角)
 *    - 位置：第1列，第1行
 *    - 大小：1列 x 1行
 *    - 调整：如需更宽，改为 grid-column: 1 / 3
 * 
 * 2. Idle Rate (中上)
 *    - 位置：第2列，第1行
 *    - 大小：1列 x 1行
 *    - 调整：如需更宽，改为 grid-column: 2 / 4
 * 
 * 3. Total Items (右上，横跨2列2行)
 *    - 位置：第3-4列，第1-2行
 *    - 大小：2列 x 2行
 *    - 调整：如需更窄，改为 grid-column: 3; 如需跨3列，改为 grid-column: 2 / 5
 * 
 * 4. Most Worn Items (左中，跨2行)
 *    - 位置：第1列，第2-3行
 *    - 大小：1列 x 2行
 *    - 调整：如需跨3行，改为 grid-row: 2 / 5
 * 
 * 5. Top Color/Style (中中，两个堆叠的小卡片)
 *    - 位置：第2列，第2行
 *    - 大小：1列 x 1行（内部包含两个 mini-card）
 *    - 调整：如需更宽，改为 grid-column: 2 / 4
 * 
 * 6. Suggested Additions (左下，横跨2列)
 *    - 位置：第1-2列，第4行
 *    - 大小：2列 x 1行
 *    - 调整：如需更窄，改为 grid-column: 1; 如需跨3列，改为 grid-column: 1 / 4
 * 
 * 7. Category Breakdown (右侧大卡片，跨2列2行)
 *    - 位置：第3-4列，第3-4行
 *    - 大小：2列 x 2行
 *    - 调整：如需更小，改为 grid-row: 3 / 4; 如需更宽，改为 grid-column: 2 / 5
 * 
 * 调整示例：
 * - 让 Activity 和 Idle 各占2列：grid-column: 1 / 3 和 grid-column: 3 / 5
 * - 让 Total Items 占满整行：grid-column: 1 / 5
 * - 让 Category 占满右侧整列：grid-column: 3 / 5; grid-row: 1 / 4
 */
.bento-activity { grid-column: 1; grid-row: 1; }
.bento-idle     { grid-column: 2; grid-row: 1; }
.bento-total {
	grid-column: 3 / 5;
	grid-row: 1 / 3;
	overflow: hidden;
}

/* Total Items 數字美學：右下角背景數字 + 掃光 */
.bento-total .bg-number {
	position: absolute;
	right: -20rpx;
	bottom: -40rpx;
	font-size: 200rpx;
	font-weight: 900;
	color: #000;
	opacity: 0.05;
	font-style: italic;
	line-height: 1;
	pointer-events: none;
	user-select: none;
}
.bento-total .total-content-overlay {
	position: relative;
	z-index: 1;
	display: flex;
	flex-direction: column;
	flex: 1;
	min-height: 0;
}
.bento-total .shimmer-sweep {
	position: absolute;
	top: 0;
	left: -100%;
	width: 50%;
	height: 100%;
	background: linear-gradient(
		to right,
		transparent,
		rgba(255, 255, 255, 0.5),
		transparent
	);
	transform: skewX(-25deg);
	animation: shimmer-sweep 6s ease-in-out infinite;
	pointer-events: none;
	z-index: 2;
}
@keyframes shimmer-sweep {
	0% { left: -100%; }
	30% { left: 150%; }
	100% { left: 150%; }
}

.bento-worn     { grid-column: 1; grid-row: 2 / 4; }
.bento-stats    { grid-column: 2; grid-row: 2; }

.bento-suggested{ grid-column: 1 / 3; grid-row: 4; }

.bento-category { grid-column: 3 / 5; grid-row: 3 / 5; }


@media (max-width: 1024px) {
	.page { padding: 24rpx; }
	.bento-grid {
		grid-template-columns: 1fr 1fr;
		grid-template-rows: auto auto auto auto auto auto;
	}
	.bento-activity { grid-column: 1; grid-row: 1; }
	.bento-idle { grid-column: 2; grid-row: 1; }
	.bento-total { grid-column: 1 / -1; grid-row: 2; }
	.bento-category { grid-column: 1 / -1; grid-row: 3; min-height: 480rpx; }
	.bento-worn { grid-column: 1; grid-row: 4; }
	.bento-stats { grid-column: 2; grid-row: 4; }
	.bento-suggested { grid-column: 1 / -1; grid-row: 5; }
}

@media (max-width: 600px) {
	.page { padding: 20rpx; }
	.bento-grid {
		grid-template-columns: 1fr;
		gap: 20rpx;
	}
	.bento-activity { grid-column: 1; grid-row: 1; }
	.bento-idle { grid-column: 1; grid-row: 2; }
	.bento-total { grid-column: 1; grid-row: 3; }
	.bento-category { grid-column: 1; grid-row: 4; min-height: 420rpx; }
	.bento-worn { grid-column: 1; grid-row: 5; }
	.bento-stats { grid-column: 1; grid-row: 6; }
	.bento-suggested { grid-column: 1; grid-row: 7; }
}

/* ============================================
 * 布局调整快速参考指南
 * ============================================
 * 
 * 【调整卡片在网格中的位置和大小】
 * 
 * 1. 修改网格列数/行数：
 *    - 改为3列：grid-template-columns: 1fr 1fr 1fr;
 *    - 改为5列：grid-template-columns: 1fr 1fr 1fr 1fr 1fr;
 *    - 改为4行：grid-template-rows: auto auto auto auto;
 * 
 * 2. 调整卡片占用的列数：
 *    - 占1列：grid-column: 1; 或 grid-column: 2;
 *    - 占2列：grid-column: 1 / 3; 或 grid-column: 3 / 5;
 *    - 占3列：grid-column: 1 / 4;
 *    - 占满整行：grid-column: 1 / -1;
 * 
 * 3. 调整卡片占用的行数：
 *    - 占1行：grid-row: 1; 或 grid-row: 2;
 *    - 占2行：grid-row: 2 / 4;
 *    - 占3行：grid-row: 1 / 4;
 * 
 * 【调整卡片内部元素】
 * 
 * 1. 调整卡片内边距：
 *    - 在 .card 中修改 padding: 28rpx;
 *    - 或针对特定卡片：.bento-activity { padding: 32rpx; }
 * 
 * 2. 调整数字大小：
 *    - 在 .metric-num 中修改 font-size: 64rpx;
 *    - 或针对特定卡片：.bento-idle .metric-num { font-size: 72rpx; }
 * 
 * 3. 调整文字大小：
 *    - 标题：.card-label { font-size: 26rpx; }
 *    - 副标题：.card-sub { font-size: 22rpx; }
 *    - 链接：.card-link { font-size: 22rpx; }
 * 
 * 4. 调整元素间距：
 *    - 列表项间距：.worn-list { gap: 28rpx; }
 *    - 建议项间距：.suggest-list { gap: 16rpx; }
 *    - 堆叠卡片间距：.bento-stats { gap: 20rpx; }
 * 
 * 【调整特定卡片示例】
 * 
 * 示例1：让 Activity 卡片更宽（占2列）
 *   .bento-activity { grid-column: 1 / 3; }
 * 
 * 示例2：让 Category 卡片更高（占3行）
 *   .bento-category { grid-row: 1 / 4; }
 * 
 * 示例3：让 Total Items 占满整行
 *   .bento-total { grid-column: 1 / -1; }
 * 
 * 示例4：调整 Activity 卡片内边距
 *   .bento-activity { padding: 32rpx; }
 * 
 * 示例5：调整 Idle Rate 数字大小
 *   .bento-idle .metric-num { font-size: 72rpx; }
 * 
 * 示例6：调整圆环图大小
 *   .donut-container { min-height: 500rpx; }
 *   .donut-svg { max-height: 600rpx; }
 */
</style>

<style>
/* 页面切换过渡：展开视图（Idle Items 等）进入/退出 */
.page-enter-active,
.page-leave-active {
	transition: opacity 220ms ease, transform 220ms ease;
}
.page-enter-from,
.page-leave-to {
	opacity: 0;
	transform: translateY(10px);
}
</style>
