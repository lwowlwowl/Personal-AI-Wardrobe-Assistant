<template>
	<view class="bento-stats">
		<view class="mini-card">
			<text class="card-label-small">Top color</text>
			<text class="mini-value">{{ topColorName || '—' }}</text>
			<text class="mini-sub">{{ topColorPercent }}%</text>
		</view>
		<view class="mini-card">
			<text class="card-label-small">Top style</text>
			<text class="mini-value">{{ topStyleName || '—' }}</text>
			<text class="mini-sub">{{ topStylePercent }}%</text>
		</view>
	</view>
</template>

<script setup>
defineProps({
	topColorName: { type: String, default: '' },
	topColorPercent: { type: Number, default: 0 },
	topStyleName: { type: String, default: '' },
	topStylePercent: { type: Number, default: 0 }
})
</script>
