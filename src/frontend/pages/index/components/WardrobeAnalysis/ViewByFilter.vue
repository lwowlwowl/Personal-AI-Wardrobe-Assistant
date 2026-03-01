<template>
	<view class="filter-popover" :class="{ visible: visible }" @click.stop>
		<view class="popover-content">
			<text class="popover-title">View by</text>

			<view class="options-list">
				<view
					v-for="opt in options"
					:key="opt.value"
					class="option-item"
					@click="selectOption(opt.value)"
				>
					<view class="checkbox-custom" :class="{ checked: modelValue === opt.value }">
						<text v-if="modelValue === opt.value" class="check-icon">✓</text>
					</view>
					<text class="option-text">{{ opt.label }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
const props = defineProps({
	modelValue: { type: String, default: 'yearly' },
	visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'apply'])

const options = [
	{ label: 'Yearly', value: 'yearly' },
	{ label: 'Monthly', value: 'monthly' },
	{ label: 'Daily', value: 'daily' }
]

const selectOption = (val) => {
	emit('update:modelValue', val)
	emit('apply')
}
</script>

<style scoped>
/* smooth popover：淡入 + 輕微上移 + 輕微縮放，easing 讓出現不硬切 */
.filter-popover {
	position: absolute;
	top: 100%;
	right: 0;
	left: auto;
	margin-top: 16rpx;
	z-index: 9999;
	opacity: 0;
	pointer-events: none;
	transform: translateY(-12rpx) scale(0.98);
	transform-origin: top right;
	transition: opacity 0.28s cubic-bezier(0.22, 1, 0.36, 1),
		transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.filter-popover.visible {
	opacity: 1;
	pointer-events: auto;
	transform: translateY(0) scale(1);
}

.popover-content {
	background: #fff;
	padding: 24rpx;
	border-radius: 20rpx;
	box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.12);
	min-width: 260rpx;
	max-width: 90vw;
	border: 2rpx solid #E8E4DC;
	text-align: left;
	box-sizing: border-box;
}

.popover-title {
	font-size: 24rpx;
	color: #9e9e9e;
	margin-bottom: 16rpx;
	display: block;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.options-list {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.option-item {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	gap: 14rpx;
	padding: 16rpx 0;
	border-radius: 12rpx;
	transition: background 0.2s ease, transform 0.15s ease;
	cursor: pointer;
}
.option-item:active {
	background: rgba(0, 0, 0, 0.04);
	transform: scale(0.98);
}

.checkbox-custom {
	width: 28rpx;
	height: 28rpx;
	border-radius: 6rpx;
	border: 2rpx solid #E8E4DC;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.2s ease;
	flex-shrink: 0;
	background-color: #fff;
}

.checkbox-custom.checked {
	background-color: #5a9a2e;
	border-color: #5a9a2e;
}

.check-icon {
	color: #fff;
	font-size: 16rpx;
	font-weight: 700;
	line-height: 1;
}

.option-text {
	font-size: 26rpx;
	color: #3d3d3d;
	white-space: nowrap;
}
</style>
