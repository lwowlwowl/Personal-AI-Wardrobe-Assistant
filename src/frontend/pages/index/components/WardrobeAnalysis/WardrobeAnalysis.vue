<template>
	<view class="page">
		<!-- 展开视图：Activity report / Idle items（页面切换过渡） -->
		<transition name="page" mode="out-in">
			<ActivityReport v-if="expandedView === 'activity-report'" key="activity-report" :trend-value="activityPercentTarget" :is-increase="activityTrend === 'increase'" @back="expandedView = null" />
			<IdleItemsView v-else-if="expandedView === 'idle-items'" key="idle-items" :unworn-count="idleRateTarget" @back="expandedView = null" />
			<view v-else key="bento" class="page-bento-wrap">
		<view v-if="filterOpen" class="filter-backdrop" @click="closeFilter"></view>

		<!-- Bento Grid（渐进加载；有下拉打开时提高层级，避免被背板挡住点击） -->
		<view class="bento-grid bento-grid-entering" :class="{ 'bento-grid-filter-open': filterOpen }" @click="filterOpen && closeFilter()">
			<!-- Activity：increase / decrease 随机展示其一，模板一致仅样式与文案不同 -->
			<view class="card bento-activity">
				<text class="card-label">Wardrobe Activity</text>
				<view class="big-metric">
					<text class="metric-num">{{ activityPercent }}%</text>
					<view class="trend-badge" :class="{ 'trend-badge-decrease': activityTrend === 'decrease' }">
						<text class="metric-arrow" :class="{ 'metric-arrow-decrease': activityTrend === 'decrease' }">{{ activityTrend === 'increase' ? '↗' : '↘' }}</text>
					</view>
				</view>
				<text class="card-sub">{{ activityTrend === 'increase' ? 'Increase compared to last week' : 'Decrease compared to last week' }}</text>
				<text class="card-link" @click="goActivityReport">Activity report →</text>
			</view>

			<!-- Idle Rate -->
			<view class="card bento-idle">
				<text class="card-label">Idle Rate</text>
				<text class="metric-num">{{ idlePercent }}%</text>
				<text class="card-sub">You have {{ idleRateTarget }} unworn items out of 106 total.</text>
				<text class="card-link" @click="goIdleItems">See all idle items →</text>
			</view>

			<!-- Total Items（主卡） -->
			<view class="card card-elevation-main bento-total">
				<view class="card-row">
					<text class="card-label">Total Items</text>
					<view class="filter-trigger" @click.stop="toggleViewBy('total')">
						<text>{{ viewByTotalLabel }}</text>
						<ViewByFilter v-model="viewByTotal" :visible="filterOpen === 'total'" @apply="closeFilter" @reset="closeFilter" />
					</view>
				</view>
				<view class="chart-container">
					<svg viewBox="0 0 300 120" class="line-svg">
						<defs>
							<linearGradient id="greenGradient" x1="0" x2="0" y1="0" y2="1">
								<stop offset="0%" stop-color="#7cb97c" stop-opacity="0.28" />
								<stop offset="40%" stop-color="#7cb97c" stop-opacity="0.18" />
								<stop offset="70%" stop-color="#7cb97c" stop-opacity="0.08" />
								<stop offset="100%" stop-color="#7cb97c" stop-opacity="0" />
							</linearGradient>
						</defs>
						<!-- 3 条水平虚线网格，提升参考感 -->
						<line x1="0" y1="35" x2="300" y2="35" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
						<line x1="0" y1="60" x2="300" y2="60" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
						<line x1="0" y1="85" x2="300" y2="85" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
						<path :d="smoothPathArea" fill="url(#greenGradient)" class="line-area" />
						<path :d="smoothPathStroke" fill="none" stroke="#7cb97c" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="line-stroke" pathLength="1" />
					</svg>
					<view class="chart-labels">
						<text v-for="year in lineYears" :key="year" class="chart-label">{{ year }}</text>
					</view>
				</view>
			</view>

			<!-- Most Worn -->
			<view class="card bento-worn">
				<view class="card-row">
					<text class="card-label">Most Worn Items</text>
					<view class="filter-trigger" @click.stop="toggleViewBy('worn')">
						<text>{{ viewByWornLabel }}</text>
						<ViewByFilter v-model="viewByWorn" :visible="filterOpen === 'worn'" @apply="closeFilter" @reset="closeFilter" />
					</view>
				</view>
				<view class="worn-list">
					<view v-for="item in mostWornWithDot" :key="item.name" class="list-item">
						<view class="dot" :class="{ active: item.dotColor === '#5c6bc0', dark: item.dotColor === '#616161' }" :style="{ background: item.dotColor }"></view>
						<text class="item-title">{{ item.name }}</text>
						<text class="item-wears">{{ item.wears }} wears</text>
					</view>
				</view>
			</view>

			<!-- ⭐ Top Color + Top Style 堆叠 -->
			<view class="bento-stats">
				<view class="mini-card">
					<text class="card-label-small">Top color</text>
					<text class="mini-value">Brown</text>
					<text class="mini-sub">{{ topColorPercent }}%</text>
				</view>
				<view class="mini-card">
					<text class="card-label-small">Top style</text>
					<text class="mini-value">Sporty</text>
					<text class="mini-sub">{{ topStylePercent }}%</text>
				</view>
			</view>

			<!-- Suggested Additions：電商推薦風格 + accordion 展開 -->
			<view class="card bento-suggested">
				<text class="card-label">Suggested Additions</text>
				<view class="suggest-list">
					<view v-for="sug in suggested" :key="sug.name" class="suggest-item" :class="{ 'suggest-item-expanded': expandedSuggestKeys.includes(sug.name) }">
						<view class="suggest-row">
							<image class="suggest-thumb" :src="sug.image" mode="aspectFill" />
							<view class="suggest-content">
								<text class="suggest-title">{{ sug.name }}</text>
								<view class="suggest-tags">
									<text v-for="tag in sug.tags" :key="tag" class="suggest-tag">{{ tag }}</text>
								</view>
							</view>
							<view class="suggest-expand-btn" @click.stop="toggleSuggest(sug.name)">
								<text class="suggest-plus">{{ expandedSuggestKeys.includes(sug.name) ? '−' : '＋' }}</text>
							</view>
						</view>
						<view class="suggest-detail">
							<text class="suggest-text">{{ sug.desc }}</text>
						</view>
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
						<text class="label-text" :class="[seg.labelSize === 'xl' ? 'label-xl' : seg.labelSize === 'lg' ? 'label-lg' : 'label-sm']">{{ seg.label }}</text>
					</view>
				</view>
			</view>
		</view>
			</view>
		</transition>
	</view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ViewByFilter from './ViewByFilter.vue'
import ActivityReport from './ActivityReport.vue'
import IdleItemsView from './IdleItemsView.vue'
import { COLOR_HEX_BY_CODE } from '@/utils/wardrobeEnums.js'

/** 点击卡片内链接后展示的展开页 */
const expandedView = ref(null)

const filterOpen = ref(null)
const viewByTotal = ref('yearly')
const viewByWorn = ref('yearly')
/** 圆环图当前悬停的扇形索引，用于与对应文字标签同步高亮及中心显示详情 */
const hoveredSegmentIndex = ref(null)
/** 入场动画只执行一次，避免 hover 重排时再次播放 */
const donutEntranceDone = ref(false)
/** Suggested Additions 展開的卡片 key（accordion） */
const expandedSuggestKeys = ref([])

/** Wardrobe Activity：每次刷新随机展示 increase 或 decrease，不修改 increase 模板 */
const activityTrend = ref(Math.random() >= 0.5 ? 'increase' : 'decrease')
const activityPercentTarget = computed(() => (activityTrend.value === 'increase' ? 15 : 8))

/** Idle Rate：每次刷新随机展示 3% 或 0%（与 Activity 一致） */
const idleRateTarget = ref(Math.random() >= 0.5 ? 3 : 0)

/** KPI 数字滚动：0.8s 内从 0 滚到目标值，科技感 */
const activityPercent = ref(0)
const idlePercent = ref(0)
const topColorPercent = ref(0)
const topStylePercent = ref(0)
function animateCountUp(refVal, target, duration = 800, delay = 0) {
	const startVal = 0
	const start = () => {
		const t0 = performance.now()
		function tick(now) {
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

onMounted(() => {
	setTimeout(() => { donutEntranceDone.value = true }, 800)
	// 数字滚动：0.8s，与 bento 入场错开一点；Activity 目标值随 increase/decrease 变化
	const countUpDelay = 320
	animateCountUp(activityPercent, activityPercentTarget.value, 800, countUpDelay)
	animateCountUp(idlePercent, idleRateTarget.value, 800, countUpDelay + 60)
	animateCountUp(topColorPercent, 38, 800, countUpDelay + 120)
	animateCountUp(topStylePercent, 45, 800, countUpDelay + 180)
})
const viewByTotalLabel = computed(() => viewByToLabel(viewByTotal.value))
const viewByWornLabel = computed(() => viewByToLabel(viewByWorn.value))
function viewByToLabel(v) {
	return v === 'yearly' ? 'Yearly' : v === 'monthly' ? 'Monthly' : 'Daily'
}

const lineYears = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
const lineData = [5, 12, 20, 18, 30, 60, 90, 106]

const smoothPathStroke = computed(() => getSvgPath(lineData, 300, 120, false))
const smoothPathArea = computed(() => getSvgPath(lineData, 300, 120, true))

function getSvgPath(data, width, height, isArea) {
	const max = Math.max(...data)
	const padding = 10
	const chartH = height - padding * 2
	const stepX = width / (data.length - 1)
	const points = data.map((val, i) => {
		const x = i * stepX
		const y = height - padding - (val / max) * chartH
		return [x, y]
	})
	let d = `M ${points[0][0]},${points[0][1]}`
	// 更圆润的贝塞尔曲线：使用更平滑的控制点
	for (let i = 0; i < points.length - 1; i++) {
		const p0 = points[i]
		const p1 = points[i + 1]
		const midX = (p0[0] + p1[0]) / 2
		// 增加控制点的平滑度，让曲线更圆润
		const cp1x = p0[0] + (midX - p0[0]) * 0.6
		const cp2x = midX + (p1[0] - midX) * 0.4
		d += ` C ${cp1x},${p0[1]} ${cp2x},${p1[1]} ${p1[0]},${p1[1]}`
	}
	if (isArea) {
		d += ` L ${width},${height} L 0,${height} Z`
	}
	return d
}

const categoryData = [
	{ label: 'Top', value: 35, color: '#FCD568' },
	{ label: 'Bottom', value: 25, color: '#68C5FA' },
	{ label: 'Footwear', value: 10, color: '#A694F5' },
	{ label: 'Outerwear', value: 15, color: '#FF69B4' },
	{ label: 'Accessories', value: 15, color: '#E57373' }
]

/**
 * 圆环图（Category Breakdown）每个扇形的路径与标签位置
 * 坐标系：SVG viewBox="-100 -100 200 200"，圆心 (0,0)，单位与 viewBox 一致
 */
const donutSegments = computed(() => {
	let startAngle = 0 // 当前扇形的起始角度（弧度），累加用

	const total = categoryData.reduce((a, b) => a + b.value, 0) // 所有类别数值总和，用于算占比

	// ---------- 圆环几何（扇形本身）----------
	const r1 = 52 // 圆环「内半径」：空心内圈的半径
	const maxValue = Math.max(...categoryData.map((d) => d.value), 1)
	const baseRadius = 76 // 圆环「外半径」基准值
	const radiusRange = 24 // 外半径随数值变化的幅度（数值越大扇形外缘越突出）
	// r2 = 圆环「外半径」：该扇形外弧的半径（可选：item.outerRadius 或按数值计算）

	// ---------- 文字标签半径 ----------
	const defaultLabelGap = 95 // 从「扇形外缘」到「文字锚点」的距离，越大文字越靠外

	return categoryData.map((item) => {
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

/** Most Worn：与 MyWardrobe / 后端一致，使用 color（wardrobeEnums 的 code），色点由 COLOR_HEX_BY_CODE 推导 */
const mostWorn = [
	{ name: 'White Cotton T-shirt', wears: 35, color: 'white' },
	{ name: 'Classic Denim Jacket', wears: 28, color: 'blue' },
	{ name: 'Black Knit Top', wears: 27, color: 'black' },
	{ name: 'Khaki Chino Pants', wears: 24, color: 'brown' },
	{ name: 'Navy Striped Tee', wears: 22, color: 'navy' }
]
const mostWornWithDot = computed(() =>
	mostWorn.map((item) => ({
		...item,
		dotColor: COLOR_HEX_BY_CODE[item.color] || '#cccccc'
	}))
)

const suggested = [
	{ name: 'Cream Knit Sweater', image: '/static/cloth_example.png', tags: ['Warm Layer', 'Minimal'], desc: 'Complements your white cotton tees; provides a clean seasonal outer layer. Pairs with 3 items in your wardrobe. Pairs well with your denim jacket — adds warmth & structure. Pairs well with your denim jacket — adds warmth & structure. ' },
	{ name: 'Dark Denim Overshirt', image: '/static/cloth_example.png', tags: ['Layering', 'Versatile'], desc: 'Pairs well with the classic denim jacket; adds structure and versatility for casual or smart-casual looks.' },
	{ name: 'Khaki Casual Pants', image: '/static/cloth_example.png', tags: ['Neutral', 'Balance'], desc: 'Balances your black knit top and enhances overall color harmony. Works with your existing earth-tone pieces.' }
]

function toggleViewBy(which) {
	filterOpen.value = filterOpen.value === which ? null : which
}
function closeFilter() {
	filterOpen.value = null
}
function toggleCategoryType() {}
function goActivityReport() {
	expandedView.value = 'activity-report'
}
function goIdleItems() {
	expandedView.value = 'idle-items'
}
function toggleSuggest(key) {
	const arr = expandedSuggestKeys.value
	const i = arr.indexOf(key)
	if (i >= 0) {
		expandedSuggestKeys.value = arr.filter((k) => k !== key)
	} else {
		expandedSuggestKeys.value = [...arr, key]
	}
}
</script>

<style scoped>
.page {
	background: #F6F5F1;
	padding: 30rpx;
	position: relative;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	min-height: 100%;
	box-sizing: border-box;
}
.page-bento-wrap {
	display: block;
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

/* 卡片通用样式 + 三档 Elevation（主次层级）
 * - 主卡 .card-elevation-main：Total Items、Category Breakdown，阴影最强
 * - 普通卡 .card：中等阴影
 * - 小卡 .mini-card：无阴影，仅边框
 * 圆角：大卡 20rpx，小卡 16rpx（Apple 感）；背景页 #F6F5F1，卡片 #FFFEFB（纸张感）
 */
/* 普通卡：中等阴影；overflow: visible 避免裁切下拉等浮层 */
.card {
	background: #FFFEFB;
	border-radius: 20rpx;
	padding: 28rpx 32rpx;
	box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05), 0 1rpx 4rpx rgba(0, 0, 0, 0.04);
	display: flex;
	flex-direction: column;
	overflow: visible;
	transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.card:hover {
	transform: translateY(-4rpx);
	box-shadow: 0 12rpx 32rpx rgba(0, 0, 0, 0.08), 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}
/* 主卡（Total Items / Category Breakdown）：更强阴影，视觉重点 */
.card-elevation-main {
	box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.08), 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}
.card-elevation-main:hover {
	box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.1), 0 6rpx 16rpx rgba(0, 0, 0, 0.06);
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
	padding: 6rpx 14rpx;
	border-radius: 50%;
	width: 44rpx;
	height: 44rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 2rpx 8rpx rgba(124, 185, 124, 0.2);
}
.trend-badge-decrease {
	background: rgba(200, 100, 80, 0.18);
	box-shadow: 0 2rpx 8rpx rgba(180, 85, 65, 0.22);
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

.line-svg {
	width: 100%;
	height: 100%;
	min-height: 180rpx;
	display: block;
}

/* 折線進入動畫：畫線效果 stroke-dasharray */
.line-stroke {
	stroke-dasharray: 1;
	stroke-dashoffset: 1;
	animation: drawLine 600ms ease-out forwards;
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

/* 小卡：几乎无阴影，仅边框，弱化层级 */
.mini-card {
	background: #FFFEFB;
	border-radius: 16rpx;
	padding: 18rpx 20rpx;
	box-shadow: none;
	border: 1rpx solid rgba(0, 0, 0, 0.06);
	display: flex;
	flex-direction: column;
	position: relative;
	transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}
.mini-card:hover,
.mini-card:active {
	background: #f5f4f1;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
	transform: translateY(-2rpx);
}

.card-label-small {
	font-size: 24rpx;
	font-weight: 500;
	color: #888;
	display: block;
	letter-spacing: 0.02em;
}

.mini-value {
	font-size: 36rpx;
	font-weight: 800;
	margin-top: 6rpx;
	color: #7a4e18;
	display: block;
	letter-spacing: 0.01em;
}

.mini-sub {
	font-size: 22rpx;
	font-weight: 400;
	color: #999;
	margin-top: 4rpx;
	display: block;
}

/* Suggested Additions - 與其他卡片背景一致 */
.bento-suggested {
	display: flex;
	flex-direction: column;
	padding: 20rpx 24rpx 24rpx;
	background: #FFFEFB;
	border-radius: 20rpx;
	border: 1rpx solid rgba(141, 110, 99, 0.12);
}

.bento-suggested .card-label {
	margin-bottom: 16rpx;
	font-size: 32rpx;
	font-weight: 800;
	color: #1d1d1f;
	letter-spacing: 0.02em;
}

.suggest-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	margin-top: 15rpx;
}

.suggest-item {
	display: flex;
	flex-direction: column;
	overflow: hidden;
	border-radius: 16rpx;
	background: #FFFEFB;
	border: 1rpx solid rgba(141, 110, 99, 0.12);
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
	transition: box-shadow 0.25s ease, transform 0.2s ease;
}
.suggest-item:hover {
	box-shadow: 0 6rpx 20rpx rgba(0, 0, 0, 0.08);
}
.suggest-item:active {
	transform: scale(0.99);
}

.suggest-row {
	display: flex;
	align-items: center;
	gap: 20rpx;
	padding: 16rpx 18rpx;
	min-height: 0;
}

.suggest-thumb {
	width: 88rpx;
	height: 88rpx;
	border-radius: 12rpx;
	flex-shrink: 0;
	background: #f5f2ee;
}

.suggest-content {
	flex: 1;
	min-width: 0;
}

.suggest-title {
	display: block;
	font-size: 28rpx;
	font-weight: 700;
	color: #1d1d1f;
	letter-spacing: 0.02em;
	line-height: 1.35;
	margin-bottom: 8rpx;
}

.suggest-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 8rpx;
}

.suggest-tag {
	font-size: 20rpx;
	padding: 4rpx 12rpx;
	border-radius: 8rpx;
	background: rgba(141, 110, 99, 0.12);
	color: #6d4c41;
	font-weight: 500;
}

.suggest-expand-btn {
	width: 48rpx;
	height: 48rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(184, 107, 31, 0.1);
	flex-shrink: 0;
	transition: background 0.2s ease;
}
.suggest-item:hover .suggest-expand-btn,
.suggest-expand-btn:active {
	background: rgba(184, 107, 31, 0.2);
}

.suggest-plus {
	font-size: 28rpx;
	font-weight: 600;
	color: #8d6e63;
	line-height: 1;
}

/* Accordion：height transition */
.suggest-detail {
	max-height: 0;
	overflow: hidden;
	transition: max-height 0.35s ease-out;
}
.suggest-item-expanded .suggest-detail {
	max-height: 200rpx;
}

.suggest-text {
	display: block;
	font-size: 24rpx;
	font-weight: 400;
	color: #666;
	line-height: 1.5;
	padding: 0 18rpx 18rpx 18rpx;
	margin-top: -8rpx;
	padding-left: 126rpx;
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

.donut-path {
	transform-origin: 50% 50%;
	transition: opacity 0.25s ease, transform 0.25s ease;
	cursor: pointer;
}
.donut-path.donut-path-enter {
	animation: donut-segment-enter 0.5s ease-out backwards;
}
.donut-path:hover,
.donut-path.donut-path-hover {
	opacity: 0.9;
	transform: scale(1.02);
}
@keyframes donut-segment-enter {
	from {
		opacity: 0;
		transform: scale(0.4);
	}
	to {
		opacity: 1;
		transform: scale(1);
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
	transition: transform 0.2s ease;
}
.floating-label.floating-label-hover .label-text {
	color: #5d4037;
	transform: scale(1.08);
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
.bento-total    { grid-column: 3 / 5; grid-row: 1 / 3; }

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
