<template>
	<scroll-view class="expanded-page" scroll-y>
		<view class="expanded-content">
			<view class="expanded-header">
				<view class="back-btn" @click="emit('back')">
					<text class="back-arrow">←</text>
					<text class="back-text">Back</text>
				</view>
				<text class="expanded-title">Activity Report</text>
			</view>

			<view class="card card-main report-card section section-1">
			<text class="card-label">Weekly Trend</text>
			<view class="kpi-row">
				<text class="trend-icon" :class="isIncrease ? 'trend-up' : 'trend-down'">{{ isIncrease ? '↑' : '↓' }}</text>
				<text class="kpi-value">{{ displayedTrendValue }}%</text>
				<text class="kpi-vs">vs last week</text>
			</view>
			<text class="kpi-message">{{ isIncrease ? 'You changed outfits more often this week ✨' : 'Your wardrobe picks are more intentional this week 💫' }}</text>
			<view class="week-chart-desc">Outfit changes per day</view>
			<view class="week-chart-area">
				<view class="chart-grid" aria-hidden="true">
					<view class="grid-line" v-for="g in 3" :key="g" :style="{ bottom: (g * 25) + '%' }"></view>
					<view class="avg-line" :style="{ bottom: avgLinePercent + '%' }"></view>
				</view>
				<view class="week-bars">
					<view
						v-for="(day, i) in weekDataWithHeight"
						:key="i"
						class="week-bar-wrap"
						@mouseenter="hoveredBarIndex = i"
						@mouseleave="hoveredBarIndex = null"
					>
						<view class="week-bar-tooltip" v-show="hoveredBarIndex === i">
							<text class="week-bar-tooltip-text">{{ day.wears }} wears</text>
						</view>
						<view class="week-bar-track">
							<view class="week-bar" :style="{ height: day.heightPercent + '%', animationDelay: i * 60 + 'ms' }" :class="{ hover: hoveredBarIndex === i }"></view>
						</view>
						<text class="week-label">{{ day.label }}</text>
					</view>
				</view>
				<text class="most-active-day">Most active day: {{ mostActiveDay }}</text>
			</view>
		</view>

		<view class="card card-secondary report-card section section-2">
			<text class="card-label">Activity by category</text>
			<view class="category-rows">
				<view v-for="(row, rowIdx) in categoryActivityWithPercent" :key="row.name" class="category-row" hover-class="category-row-hover">
					<view class="category-row-main">
						<text class="category-icon">{{ row.icon }}</text>
						<view class="category-info">
							<text class="category-name">{{ row.name }}</text>
							<view class="category-progress-track">
								<view class="category-progress-fill" :style="{ width: progressAnimated ? row.percent + '%' : '0%', transitionDelay: rowIdx * 80 + 'ms' }"></view>
							</view>
						</view>
					</view>
					<text class="category-count">{{ row.count }} wears</text>
				</view>
			</view>
		</view>
		</view>
	</scroll-view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
	trendValue: { type: Number, default: 8 },
	isIncrease: { type: Boolean, default: false }
})

const emit = defineEmits(['back'])

/** 下方 Activity by category 总 wears，与柱状图一周总 wears 保持一致；带图标与占比 */
const categoryActivity = [
	{ name: 'Tops', count: 42, icon: '👕' },
	{ name: 'Bottoms', count: 28, icon: '👖' },
	{ name: 'Outerwear', count: 15, icon: '🧥' },
	{ name: 'Footwear', count: 12, icon: '👟' },
	{ name: 'Accessories', count: 9, icon: '⌚' }
]
const totalWears = categoryActivity.reduce((sum, c) => sum + c.count, 0)
const categoryActivityWithPercent = computed(() =>
	categoryActivity.map((c) => ({ ...c, percent: totalWears ? (c.count / totalWears) * 100 : 0 }))
)

/** 每日穿搭次数：一周总和 = totalWears（与下方分类总 wears 一致），hover 显示具体 wear 数 */
const weekData = [
	{ label: 'Mon', wears: 10 },
	{ label: 'Tue', wears: 16 },
	{ label: 'Wed', wears: 8 },
	{ label: 'Thu', wears: 18 },
	{ label: 'Fri', wears: 12 },
	{ label: 'Sat', wears: 24 },
	{ label: 'Sun', wears: 18 }
]
const maxWears = Math.max(...weekData.map((d) => d.wears), 1)
const avgWears = weekData.reduce((s, d) => s + d.wears, 0) / weekData.length
const avgLinePercent = (avgWears / maxWears) * 100
const mostActiveDay = computed(() => {
	const best = weekData.reduce((a, b) => (a.wears >= b.wears ? a : b))
	return best.label
})
const weekDataWithHeight = computed(() =>
	weekData.map((d) => ({
		...d,
		heightPercent: (d.wears / maxWears) * 100
	}))
)
const hoveredBarIndex = ref(null)
const progressAnimated = ref(false)
const displayedTrendValue = ref(0)
function animateCountUp() {
	const target = props.trendValue
	const duration = 800
	const start = performance.now()
	function tick(now) {
		const elapsed = now - start
		const t = Math.min(elapsed / duration, 1)
		const eased = 1 - Math.pow(1 - t, 3)
		displayedTrendValue.value = Math.round(0 + (target - 0) * eased)
		if (t < 1) requestAnimationFrame(tick)
	}
	requestAnimationFrame(tick)
}
onMounted(() => {
	requestAnimationFrame(() => {
		animateCountUp()
		setTimeout(() => {
			progressAnimated.value = true
		}, 400)
	})
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
	border-radius: 20rpx;
	box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.05), 0 0 0 1rpx rgba(168, 212, 168, 0.06);
	margin-bottom: 24rpx;
	opacity: 0;
	transform: translateY(24rpx);
	animation: sectionFadeUp 0.4s ease forwards;
}
.section-1 { animation-delay: 0ms; }
.section-2 { animation-delay: 120ms; }
@keyframes sectionFadeUp {
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
.card-main {
	padding: 40rpx 36rpx;
}
.card-secondary {
	padding: 24rpx 28rpx;
}

.card-label {
	font-size: 30rpx;
	font-weight: 700;
	color: #1d1d1f;
	margin-bottom: 16rpx;
	display: block;
}
.card-main .card-label {
	font-size: 36rpx;
	font-weight: 700;
	margin-bottom: 20rpx;
}
.card-secondary .card-label {
	font-size: 26rpx;
	margin-bottom: 16rpx;
	font-weight: 600;
}
.kpi-row {
	display: flex;
	align-items: baseline;
	gap: 8rpx;
	margin-bottom: 12rpx;
}
.trend-icon {
	font-size: 36rpx;
	font-weight: 700;
	line-height: 1;
}
.trend-up {
	color: #34c759;
}
.trend-down {
	color: #e55c3c;
}
.kpi-value {
	font-size: 96rpx;
	font-weight: 800;
	color: #1d1d1f;
	line-height: 1.1;
	font-variant-numeric: tabular-nums;
	letter-spacing: -0.02em;
}
.kpi-vs {
	font-size: 26rpx;
	color: #888;
	font-weight: 500;
}
.kpi-message {
	font-size: 28rpx;
	color: #1d1d1f;
	line-height: 1.3;
	margin-bottom: 20rpx;
	display: block;
}

.week-chart-desc {
	font-size: 26rpx;
	color: #888;
	margin-bottom: 16rpx;
}
.week-chart-area {
	position: relative;
}
.chart-grid {
	position: absolute;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	pointer-events: none;
	z-index: 0;
}
.grid-line {
	position: absolute;
	left: 0;
	right: 0;
	height: 0;
	border-top: 1rpx dashed rgba(0, 0, 0, 0.06);
}
.avg-line {
	position: absolute;
	left: 0;
	right: 0;
	height: 0;
	border-top: 2rpx dashed rgba(124, 184, 124, 0.5);
}
.week-bars {
	position: relative;
	z-index: 1;
	display: flex;
	align-items: flex-end;
	justify-content: space-between;
	gap: 14rpx;
	height: 460rpx;
	padding-top: 8rpx;
}
.week-bar-wrap {
	flex: 1;
	max-width: 60rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 12rpx;
	position: relative;
	cursor: pointer;
}
.week-bar-tooltip {
	position: absolute;
	bottom: calc(50%);
	left: 50%;
	transform: translateX(-50%);
	background: #1d1d1f;
	color: #fff;
	padding: 0rpx 16rpx;
	border-radius: 10rpx;
	white-space: nowrap;
	z-index: 10;
	pointer-events: none;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.2);
}
.week-bar-tooltip-text {
	font-size: 22rpx;
	font-weight: 600;
	white-space: nowrap;
	display: inline-block;
}
.week-bar-track {
	width: 100%;
	height: 400rpx;
	display: flex;
	align-items: flex-end;
	justify-content: center;
	transform-origin: bottom;
}
.week-bar {
	width: 100%;
	min-height: 20rpx;
	max-height: 100%;
	background: linear-gradient(180deg, rgba(124, 184, 124, 0.95) 0%, rgba(168, 212, 168, 0.7) 40%, rgba(168, 212, 168, 0.35) 100%);
	border-radius: 24rpx 24rpx 12rpx 12rpx;
	transform-origin: bottom;
	animation: bar-grow 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
	transition: transform 0.2s ease, filter 0.2s ease;
}
@keyframes bar-grow {
	from { transform: scaleY(0); }
	to { transform: scaleY(1); }
}
.week-bar.hover {
	transform: scaleY(1.05);
	filter: brightness(1.08);
}
.week-label {
	font-size: 22rpx;
	color: #666;
	font-weight: 600;
}
.most-active-day {
	display: block;
	font-size: 26rpx;
	color: #888;
	margin-top: 20rpx;
	font-weight: 600;
}

.category-rows {
	display: flex;
	flex-direction: column;
	gap: 4rpx;
}
.category-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 14rpx 16rpx;
	border-radius: 12rpx;
	gap: 16rpx;
	transition: background 0.2s ease;
}
.category-row:hover,
.category-row-hover {
	background: rgba(0, 0, 0, 0.03);
}
.category-row:hover .category-progress-fill,
.category-row-hover .category-progress-fill {
	background: linear-gradient(90deg, #7cb87c 0%, #5a9e5a 100%);
}
.category-row-main {
	display: flex;
	align-items: center;
	gap: 14rpx;
	flex: 1;
	min-width: 0;
}
.category-icon {
	font-size: 36rpx;
	line-height: 1;
	flex-shrink: 0;
}
.category-info {
	flex: 1;
	min-width: 0;
}
.category-name {
	font-size: 26rpx;
	font-weight: 600;
	color: #1d1d1f;
	display: block;
	margin-bottom: 10rpx;
}
.category-progress-track {
	height: 20rpx;
	background: rgba(0, 0, 0, 0.06);
	border-radius: 999rpx;
	overflow: hidden;
}
.category-progress-fill {
	height: 100%;
	background: linear-gradient(90deg, #A8D4A8 0%, #7cb87c 100%);
	border-radius: 999rpx;
	transition: width 600ms cubic-bezier(0.25, 0.1, 0.25, 1);
}
.category-count {
	font-size: 24rpx;
	color: #888;
	font-weight: 600;
	flex-shrink: 0;
}
</style>
