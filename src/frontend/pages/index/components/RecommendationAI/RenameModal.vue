<template>
	<view v-if="visible" class="modal-overlay" @click="$emit('cancel')">
		<view class="modal-box rename-modal" @click.stop>
			<text class="modal-title">Rename conversation</text>
			<input 
				class="rename-input" 
				v-model="inputValue" 
				placeholder="Enter a new name"
				:maxlength="36"
				@confirm="onConfirm"
			/>
			<view class="modal-actions">
				<view class="modal-btn modal-btn-cancel" @click="$emit('cancel')">Cancel</view>
				<view class="modal-btn modal-btn-confirm" @click="onConfirm">Save</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
	visible: { type: Boolean, default: false },
	initialValue: { type: String, default: '' }
})

const emit = defineEmits(['confirm', 'cancel'])

const inputValue = ref('')

watch(() => [props.visible, props.initialValue], ([visible, val]) => {
	if (visible) {
		inputValue.value = (val || 'New conversation').slice(0, 36)
	}
}, { immediate: true })

const onConfirm = () => {
	const trimmed = inputValue.value.trim()
	if (trimmed) {
		emit('confirm', trimmed.slice(0, 36))
	}
}
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

.modal-btn-confirm {
	background: #9D8B70;
	color: #fff;
}

.rename-input {
	width: 100%;
	height: 88rpx;
	padding: 0 28rpx;
	border: 2rpx solid #E5E5EA;
	border-radius: 16rpx;
	font-size: 28rpx;
	color: #1D1D1F;
	box-sizing: border-box;
	background: #FAFAFA;
}

.rename-input:focus {
	border-color: #9D8B70;
	background: #fff;
}
</style>
