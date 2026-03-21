<template>
	<view class="card bento-activity">
		<text class="card-label">Wardrobe Activity</text>
		<view v-if="loadingActivity" class="loading-state">
			<text class="loading-text">Loading...</text>
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
		<text class="card-link" @click="$emit('open-activity-report')">Activity report →</text>
	</view>
</template>

<script setup>
defineProps({
	loadingActivity: { type: Boolean, default: true },
	currentWears: { type: Number, default: 0 },
	activityPercent: { type: Number, default: 0 },
	activityTrend: { type: String, default: 'increase' }
})
defineEmits(['open-activity-report'])
</script>
