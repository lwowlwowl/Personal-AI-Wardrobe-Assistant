<template>
	<view class="card card-elevation-main bento-total" :class="{ 'bento-total--empty': isTotalTrendEmpty }">
		<image v-if="isTotalTrendEmpty" class="total-empty-watermark" src="/static/icons/icon-wardrobe.svg" mode="aspectFit" aria-hidden="true" />
		<text class="bg-number" aria-hidden="true">{{ bgNumberDisplay }}</text>
		<view class="total-content-overlay">
			<view class="card-row">
				<text class="card-label">Total Items</text>
				<view class="filter-trigger" @click.stop="$emit('toggle-total-filter')">
					<text>{{ viewByTotalLabel }}</text>
					<ViewByFilter :model-value="viewByTotal" :visible="filterOpenForTotal" @update:model-value="$emit('update:viewByTotal', $event)" @apply="$emit('apply-filter')" />
				</view>
			</view>
			<view class="chart-container">
				<view v-if="!isLoggedIn" class="loading-state">
					<text class="loading-text">Please log in first</text>
				</view>
				<view v-else-if="loadingTrend" class="loading-state loading-state--breathe">
					<text class="loading-text">Loading trend data...</text>
				</view>
				<view v-else-if="isTotalTrendEmpty" class="total-trend-empty bento-empty-slot">
					<text class="total-trend-empty-dash">—</text>
					<text class="total-trend-empty-title">Ready to organize your style?</text>
					<text class="total-trend-empty-sub">Add pieces to see growth over time.</text>
					<view v-if="openWardrobeTab" class="bento-add-pill" hover-class="bento-add-pill--pressed" @click="goToWardrobe">
						<text class="bento-add-pill-text">Add items +</text>
					</view>
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
							<text class="stat-item" v-if="totalStats.growth_rate">Growth rate: {{ totalStats.growth_rate }}%</text>
							<text class="stat-item" v-if="totalStats.projection">Forecast {{ totalStats.projection_year }}: {{ totalStats.projection }}</text>
						</view>
					</template>
				</template>
			</view>
		</view>
		<view class="shimmer-sweep" aria-hidden="true"></view>
	</view>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import ViewByFilter from '../ViewByFilter.vue'

const openWardrobeTab = inject('openWardrobeTab', null)
function goToWardrobe() {
	if (typeof openWardrobeTab === 'function') openWardrobeTab()
}

const props = defineProps({
	isLoggedIn: { type: Boolean, default: false },
	loadingTrend: { type: Boolean, default: true },
	totalItemsCount: { type: Number, default: 0 },
	lineYears: { type: Array, default: () => [] },
	lineData: { type: Array, default: () => [] },
	totalStats: { type: Object, default: null },
	viewByTotal: { type: String, default: 'weekly' },
	filterOpenForTotal: { type: Boolean, default: false },
	/** Parent increments when closing expanded sub-page to replay single-point count-up */
	milestoneReplay: { type: Number, default: 0 }
})

defineEmits(['update:viewByTotal', 'toggle-total-filter', 'apply-filter'])

function viewByToLabel(v) {
	return v === 'yearly' ? 'Yearly' : v === 'monthly' ? 'Monthly' : 'Weekly'
}
const viewByTotalLabel = computed(() => viewByToLabel(props.viewByTotal))

function getSvgPath(data, width, height, isArea) {
	if (!data || !Array.isArray(data)) return ''
	const validData = data.filter((val) => val !== null && val !== undefined && !isNaN(val) && isFinite(val))
	const padding = 10
	const chartH = height - padding * 2
	if (validData.length === 0) {
		const y = height - padding
		if (isArea) return ''
		return `M 0,${y} L ${width},${y}`
	}
	if (validData.length === 1) return ''
	const max = Math.max(...validData, 1)
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
		d += ` L ${width},${height} L 0,${height} Z`
	}
	return d
}

const validTrendData = computed(() => {
	const data = props.lineData
	if (!data || !Array.isArray(data)) return []
	return data.filter((v) => v !== null && v !== undefined && !isNaN(v) && isFinite(v))
})

/** Empty wardrobe: no trend points and total is 0 — show guided empty state */
const isTotalTrendEmpty = computed(
	() =>
		props.isLoggedIn &&
		!props.loadingTrend &&
		(props.totalItemsCount || 0) === 0 &&
		validTrendData.value.length === 0
)

const bgNumberDisplay = computed(() => (isTotalTrendEmpty.value ? '—' : String(props.totalItemsCount ?? 0)))

const isSinglePointTrend = computed(() => validTrendData.value.length === 1)
const singlePointValue = computed(() =>
	validTrendData.value.length === 1 ? validTrendData.value[0] : 0
)

const displaySinglePointValue = ref(0)

const smoothPathStroke = computed(() => getSvgPath(props.lineData, 300, 120, false))
const smoothPathArea = computed(() => getSvgPath(props.lineData, 300, 120, true))

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

function runSinglePointCountUp(delay = 0) {
	if (validTrendData.value.length !== 1) return
	displaySinglePointValue.value = 0
	requestAnimationFrame(() => {
		animateCountUp(displaySinglePointValue, () => singlePointValue.value ?? 0, 800, delay)
	})
}

watch(singlePointValue, (newVal, oldVal) => {
	if (isSinglePointTrend.value && newVal !== oldVal) runSinglePointCountUp()
})

watch(
	() => props.milestoneReplay,
	(_n, oldN) => {
		if (oldN === undefined) return
		runSinglePointCountUp(320)
	}
)
</script>
