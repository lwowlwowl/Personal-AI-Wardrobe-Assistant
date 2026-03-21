<template>
	<view class="card bento-idle">
		<text class="card-label">Idle Rate</text>
		<text class="metric-num">{{ idlePercent }}%</text>
		<text class="card-sub">You have {{ idleCount }} unworn items out of {{ totalItemsCount }} total.</text>
		<text class="card-link" @click="$emit('open-idle-items')">See all idle items →</text>
	</view>
</template>

<script setup>
defineProps({
	idlePercent: { type: Number, default: 0 },
	idleCount: { type: Number, default: 0 },
	totalItemsCount: { type: Number, default: 0 }
})
defineEmits(['open-idle-items'])
</script>
