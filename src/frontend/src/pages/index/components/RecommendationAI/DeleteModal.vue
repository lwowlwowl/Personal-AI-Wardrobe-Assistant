<template>
	<view v-if="visible" class="modal-overlay" @click="$emit('cancel')">
		<view class="modal-box delete-modal" @click.stop>
			<text class="modal-title">Delete conversation</text>
			<text class="delete-modal-desc">Are you sure you want to delete this conversation?</text>
			<view class="modal-actions">
				<view class="modal-btn modal-btn-cancel" @click="$emit('cancel')">Cancel</view>
				<view class="modal-btn modal-btn-danger" @click="$emit('confirm')">Delete</view>
			</view>
		</view>
	</view>
</template>

<script setup>
defineProps({
	visible: { type: Boolean, default: false }
})

defineEmits(['confirm', 'cancel'])
</script>

<style scoped>
.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.45);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
}

.modal-box {
	background: #fff;
	border-radius: 24rpx;
	padding: 48rpx 40rpx;
	width: 560rpx;
	max-width: 90vw;
	box-shadow: 0 24rpx 80rpx rgba(0, 0, 0, 0.18);
}

.modal-title {
	font-size: 42rpx;
	font-weight: 600;
	font-family: 'Times New Roman', Times, serif;
	color: #1D1D1F;
	display: block;
	margin-bottom: 28rpx;
	letter-spacing: -0.02em;
}

.delete-modal-desc {
	display: block;
	font-size: 28rpx;
	font-family: 'Times New Roman', Times, serif;
	color: #6B6B6B;
	line-height: 1.5;
}

.modal-actions {
	display: flex;
	justify-content: center;
	gap: 20rpx;
	margin-top: 36rpx;
}

.modal-btn {
	padding: 20rpx 36rpx;
	border-radius: 16rpx;
	font-size: 30rpx;
	font-weight: 500;
	cursor: pointer;
	transition: background 0.2s, color 0.2s;
}

.modal-btn:active {
	opacity: 0.9;
}

/* 取消：灰色文字按钮，非实心块 */
.modal-btn-cancel {
	background: transparent;
	color: #6B6B6B;
}

.modal-btn-cancel:hover {
	background: rgba(0, 0, 0, 0.06);
}

/* 删除：深色危险红，hover 加深，无渐变 */
.modal-btn-danger {
	background: #D92D20;
	color: #fff;
}

.modal-btn-danger:hover {
	background: #B3261E;
}
</style>