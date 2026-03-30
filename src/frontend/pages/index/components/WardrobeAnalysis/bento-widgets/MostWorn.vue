<template>
	<view class="card bento-worn">
		<view class="card-row">
			<text class="card-label">Most Worn Items</text>
			<view class="filter-trigger" @click.stop="$emit('toggle-worn-filter')">
				<text>{{ viewByWornLabel }}</text>
				<ViewByFilter
					:model-value="viewByWorn"
					:visible="filterOpenForWorn"
					@update:model-value="$emit('update:viewByWorn', $event)"
					@apply="$emit('apply-filter')"
				/>
			</view>
		</view>
		<view class="worn-list">
			<view v-if="!isLoggedIn" class="loading-state">
				<text class="loading-text">Please log in first</text>
			</view>
			<view v-else-if="loadingWorn" class="loading-state">
				<text class="loading-text">Loading...</text>
			</view>
			<template v-else>
				<view v-if="mostWornWithDot.length === 0" class="worn-empty-state bento-empty-slot loading-state--breathe">
					<view class="worn-skeleton-list">
						<view v-for="n in 3" :key="n" class="worn-skeleton-row">
							<view class="worn-skel-dot"></view>
							<view class="worn-skel-bar"></view>
							<view class="worn-skel-meta"></view>
						</view>
					</view>
					<text class="worn-empty-title">Your favorites will appear here.</text>
					<text class="worn-empty-hint">Record your OOTD to see your most-loved items.</text>
					<view v-if="openWardrobeTab" class="worn-empty-cta" @click="goToWardrobe">
						<text class="worn-empty-cta-text">Add to wardrobe →</text>
					</view>
				</view>
				<!-- :key=viewByWorn remounts block; row stagger via nth-child (no transition-group — uni-app perf) -->
				<view v-else class="worn-list-items worn-list-items--animate" :key="viewByWorn">
					<view v-for="item in mostWornWithDot" :key="`${item.name}-${item.wears}`" class="list-item">
						<view class="dot" :class="{ active: item.dotColor === '#5c6bc0', dark: item.dotColor === '#616161' }" :style="{ background: item.dotColor }"></view>
						<text class="item-title">{{ item.name }}</text>
						<text class="item-wears">{{ item.wears }} wears</text>
					</view>
				</view>
			</template>
		</view>
	</view>
</template>

<script setup>
import { computed, inject } from 'vue'

const openWardrobeTab = inject('openWardrobeTab', null)
function goToWardrobe() {
	if (typeof openWardrobeTab === 'function') openWardrobeTab()
}
import ViewByFilter from '../ViewByFilter.vue'
import { COLOR_HEX_BY_CODE } from '@/utils/wardrobeEnums.js'

const props = defineProps({
	isLoggedIn: { type: Boolean, default: false },
	loadingWorn: { type: Boolean, default: true },
	viewByWorn: { type: String, default: 'yearly' },
	filterOpenForWorn: { type: Boolean, default: false },
	mostWorn: { type: Array, default: () => [] }
})

defineEmits(['update:viewByWorn', 'toggle-worn-filter', 'apply-filter'])

function viewByToLabel(v) {
	return v === 'yearly' ? 'Yearly' : v === 'monthly' ? 'Monthly' : 'Weekly'
}
const viewByWornLabel = computed(() => viewByToLabel(props.viewByWorn))

function firstColorCode(colorStr) {
	if (!colorStr || typeof colorStr !== 'string') return 'gray'
	const first = colorStr.split(',')[0].trim()
	if (!first) return 'gray'
	return first.replace(/\s+/g, '_').toLowerCase()
}

const mostWornWithDot = computed(() =>
	props.mostWorn.map((item) => {
		const code = firstColorCode(item.color)
		return {
			...item,
			dotColor: COLOR_HEX_BY_CODE[code] || '#9e9e9e'
		}
	})
)
</script>

<style scoped>
.worn-list-items {
	display: flex;
	flex-direction: column;
	gap: 28rpx;
	width: 100%;
	box-sizing: border-box;
	overflow: hidden;
}

/* Staggered enter: diagonal slide + slight scale + soft overshoot (avoid blur on text) */
.worn-list-items--animate .list-item {
	opacity: 0;
	animation: worn-item-reveal 0.58s cubic-bezier(0.16, 1, 0.32, 1) forwards;
}

.worn-list-items--animate .list-item:nth-child(1) {
	animation-delay: 0.03s;
}
.worn-list-items--animate .list-item:nth-child(2) {
	animation-delay: 0.1s;
}
.worn-list-items--animate .list-item:nth-child(3) {
	animation-delay: 0.17s;
}
.worn-list-items--animate .list-item:nth-child(4) {
	animation-delay: 0.24s;
}
.worn-list-items--animate .list-item:nth-child(5) {
	animation-delay: 0.31s;
}
.worn-list-items--animate .list-item:nth-child(6) {
	animation-delay: 0.38s;
}
.worn-list-items--animate .list-item:nth-child(7) {
	animation-delay: 0.45s;
}
.worn-list-items--animate .list-item:nth-child(8) {
	animation-delay: 0.52s;
}

@keyframes worn-item-reveal {
	0% {
		opacity: 0;
		transform: translate3d(-22rpx, 24rpx, 0) scale(0.92);
	}
	68% {
		opacity: 1;
		transform: translate3d(4rpx, -5rpx, 0) scale(1.025);
	}
	100% {
		opacity: 1;
		transform: translate3d(0, 0, 0) scale(1);
	}
}
</style>
