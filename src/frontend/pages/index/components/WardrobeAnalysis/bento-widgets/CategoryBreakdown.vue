<template>
	<view class="card card-elevation-main bento-category">
		<view class="card-row">
			<text class="card-label big-title">Category Breakdown</text>
			<view class="filter-trigger" @click="$emit('toggle-dimension')">
				<text>Type</text>
			</view>
		</view>
		<view v-if="!isLoggedIn" class="loading-state donut-empty-state">
			<text class="loading-text">Please log in first</text>
		</view>
		<view v-else-if="loadingCategory" class="loading-state donut-empty-state">
			<text class="loading-text">Loading...</text>
		</view>
		<view v-else-if="!hasCategoryDonutData" class="loading-state donut-empty-state">
			<text class="loading-text">No category data yet</text>
		</view>
		<view v-else class="donut-container">
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
				<circle cx="0" cy="0" r="24" fill="none" stroke="#8d6e63" stroke-width="2" stroke-linecap="round" pathLength="100" stroke-dasharray="4 6" pointer-events="none" />
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
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const props = defineProps({
	isLoggedIn: { type: Boolean, default: false },
	loadingCategory: { type: Boolean, default: false },
	categoryData: { type: Array, default: () => [] }
})

defineEmits(['toggle-dimension'])

const hoveredSegmentIndex = ref(null)
const donutEntranceDone = ref(false)

const categoryChartTotal = computed(() =>
	props.categoryData.reduce((sum, d) => sum + (Number(d.value) || 0), 0)
)
const hasCategoryDonutData = computed(
	() => props.categoryData.length > 0 && categoryChartTotal.value > 0
)

const donutSegments = computed(() => {
	let startAngle = 0
	const total = categoryChartTotal.value
	const list = props.categoryData
	if (total <= 0 || !list.length) return []

	const r1 = 52
	const maxValue = Math.max(...list.map((d) => d.value), 1)
	const baseRadius = 76
	const radiusRange = 24
	const defaultLabelGap = 110

	return list.map((item) => {
		const r2 = item.outerRadius ?? (baseRadius + (item.value / maxValue) * radiusRange)
		const sliceAngle = (item.value / total) * 2 * Math.PI
		const endAngle = startAngle + sliceAngle
		const x1 = Math.cos(startAngle) * r2
		const y1 = Math.sin(startAngle) * r2
		const x2 = Math.cos(endAngle) * r2
		const y2 = Math.sin(endAngle) * r2
		const x3 = Math.cos(endAngle) * r1
		const y3 = Math.sin(endAngle) * r1
		const x4 = Math.cos(startAngle) * r1
		const y4 = Math.sin(startAngle) * r1
		const largeArc = sliceAngle > Math.PI ? 1 : 0
		const path = `M ${x4} ${y4} L ${x1} ${y1} A ${r2} ${r2} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${r1} ${r1} 0 ${largeArc} 0 ${x4} ${y4} Z`
		const midAngle = startAngle + sliceAngle / 2
		const angleOffsetRad = ((item.labelAngleOffset ?? 0) * Math.PI) / 180
		const labelAngle = midAngle + angleOffsetRad
		const labelR = r2 + defaultLabelGap + (item.labelRadiusOffset ?? 0)
		const labelX = Math.cos(labelAngle) * labelR
		const labelY = Math.sin(labelAngle) * labelR
		const align = Math.cos(labelAngle) > 0 ? 'left' : 'right'
		const labelSize = item.labelSize ?? (item.value >= 30 ? 'xl' : item.value >= 20 ? 'lg' : 'sm')
		startAngle = endAngle
		return { ...item, path, labelX, labelY, align, labelSize }
	})
})

const donutSegmentsForDraw = computed(() => {
	const list = donutSegments.value.map((seg, originalIndex) => ({ seg, originalIndex }))
	const hovered = hoveredSegmentIndex.value
	if (hovered == null) return list
	const [item] = list.splice(hovered, 1)
	list.push(item)
	return list
})

const hoveredSegment = computed(() => {
	const i = hoveredSegmentIndex.value
	if (i == null) return null
	return donutSegments.value[i] ?? null
})

watch(
	() => props.loadingCategory,
	(loading) => {
		if (!loading) hoveredSegmentIndex.value = null
	}
)

onMounted(() => {
	setTimeout(() => {
		donutEntranceDone.value = true
	}, 1600)
})
</script>
