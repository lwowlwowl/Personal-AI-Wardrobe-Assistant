<template>
	<view v-if="visible" class="modal-mask" @click="close">
		<view 
			class="modal-wrap" 
			:class="{ 'modal-enter': isEnter, 'modal-leave': isLeave }"
			@click.stop
		>
			<view class="modal-content">
				<view class="modal-head">
					<view class="close-btn" @click="close">
						<image src="/static/icons/icon-close-red.svg" mode="aspectFit" class="icon-close"></image>
					</view>
				</view>

				<view class="modal-body">
					<view class="image-section">
						<image :src="item.image" mode="aspectFill" class="main-img" />
					</view>
					<view class="info-section">
						<view class="info-row">
							<text class="label">Name:</text>
							<input 
								class="info-input" 
								v-model="editName" 
								placeholder="Model name"
								@blur="emitField('posture', editName)"
							/>
						</view>
						<view class="info-row info-row-readonly">
							<text class="label">Added on:</text>
							<text class="value">{{ item.date || '—' }}</text>
						</view>
						<view class="info-row info-row-favourite">
							<text class="label">Favourite:</text>
							<view class="hearts">
								<view 
									v-for="k in 3" 
									:key="k" 
									class="heart-wrap" 
									@click="setFavourite(k)"
								>
									<image 
										:src="editFavourite >= k ? '/static/icons/icon-heart-filled.svg' : '/static/icons/icon-heart.svg'" 
										mode="aspectFit" 
										class="heart-icon"
									/>
								</view>
							</view>
						</view>
					</view>
				</view>

				<view class="action-bar">
					<view 
						v-if="item?.id" 
						class="btn default-btn" 
						:class="{ 'is-default': item.id === defaultModelId }"
						@click="item.id !== defaultModelId && handleSetDefault()"
					>
						{{ item.id === defaultModelId ? 'Default' : 'Set default' }}
					</view>
					<view class="btn delete-btn" @click="handleDelete">Delete</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { watch, ref, nextTick } from 'vue'

const props = defineProps({
	visible: {
		type: Boolean,
		default: false
	},
	item: {
		type: Object,
		default: () => ({})
	},
	defaultModelId: {
		type: [Number, String],
		default: null
	}
})

const emit = defineEmits(['update:visible', 'delete', 'update', 'set-default'])

const isEnter = ref(false)
const isLeave = ref(false)
const editName = ref('')
const editFavourite = ref(0)

watch(() => props.item, (val) => {
	if (!val) return
	editName.value = val.posture || val.name || ''
	const f = val.favourite
	editFavourite.value = typeof f === 'number' && f >= 0 && f <= 3 ? f : 0
}, { immediate: true, deep: true })

watch(() => props.visible, (v) => {
	if (v) {
		isLeave.value = false
		nextTick(() => {
			isEnter.value = true
			editName.value = props.item?.posture || props.item?.name || ''
			const f = props.item?.favourite
			editFavourite.value = typeof f === 'number' && f >= 0 && f <= 3 ? f : 0
		})
	} else {
		isEnter.value = false
		isLeave.value = true
	}
}, { immediate: true })

const close = () => {
	isEnter.value = false
	isLeave.value = true
	setTimeout(() => {
		emit('update:visible', false)
		isLeave.value = false
	}, 280)
}

const emitField = (field, value) => {
	if (!props.item?.id) return
	const v = field === 'posture' ? (value || '').trim() : value
	emit('update', { id: props.item.id, field, value: v })
}

const setFavourite = (level) => {
	if (!props.item?.id) return
	const next = editFavourite.value === level ? Math.max(0, level - 1) : level
	editFavourite.value = next
	emit('update', { id: props.item.id, field: 'favourite', value: next })
}

const handleSetDefault = () => {
	if (!props.item?.id || props.item.id === props.defaultModelId) return
	emit('set-default', props.item.id)
}

const handleDelete = () => {
	emit('delete', props.item.id)
	close()
}
</script>

<style scoped>
.modal-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.4);
	backdrop-filter: blur(4px);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 999;
	animation: mask-fade-in 0.28s ease;
}

@keyframes mask-fade-in {
	from { opacity: 0; }
	to { opacity: 1; }
}

.modal-wrap {
	width: 92%;
	max-width: 820px;
	max-height: 92vh;
	display: flex;
	justify-content: center;
	align-items: center;
	transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1),
	            opacity 0.28s ease;
}

.modal-wrap.modal-enter {
	animation: modal-zoom-in 0.32s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.modal-wrap.modal-leave {
	animation: modal-zoom-out 0.24s ease forwards;
}

@keyframes modal-zoom-in {
	from {
		opacity: 0;
		transform: scale(0.92) translateY(20rpx);
	}
	to {
		opacity: 1;
		transform: scale(1) translateY(0);
	}
}

@keyframes modal-zoom-out {
	from {
		opacity: 1;
		transform: scale(1) translateY(0);
	}
	to {
		opacity: 0;
		transform: scale(0.95) translateY(16rpx);
	}
}

.modal-content {
	width: 100%;
	max-height: 92vh;
	overflow-y: auto;
	background-color: #FDFBF7;
	border-radius: 24rpx;
	padding: 48rpx 48rpx 5rpx 48rpx;
	position: relative;
	box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.12);
	border: 2rpx solid rgba(0, 0, 0, 0.08);
}

.modal-head {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 88rpx;
	display: flex;
	justify-content: flex-end;
	align-items: center;
	padding: 0 24rpx;
	z-index: 6;
}

.close-btn {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
}

.icon-close {
	width: 44rpx;
	height: 44rpx;
}

.modal-body {
	display: flex;
	margin-top: 24rpx;
	gap: 40rpx;
}

.image-section {
	flex: 1;
	min-width: 0;
	width: 0;
	aspect-ratio: 4 / 5;
	border-radius: 16rpx;
	overflow: hidden;
	background: #F5F0E6;
}

.image-section .main-img {
	width: 100%;
	height: 100%;
	display: block;
	object-fit: cover;
}

.info-section {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	justify-content: center;
	font-family: "Bodoni MT", "Noto Serif", "Songti SC", serif;
}

.info-row {
	display: flex;
	align-items: center;
	margin-bottom: 22rpx;
	font-size: 32rpx;
	color: #1D1D1F;
	line-height: 1.45;
}

.info-row .label {
	font-weight: 600;
	margin-right: 12rpx;
	flex-shrink: 0;
}

.info-row .value {
	font-weight: 400;
}

.info-input {
	flex: 1;
	min-width: 0;
	font-size: 32rpx;
	color: #1D1D1F;
	font-weight: 400;
	font-family: "Bodoni MT", "Noto Serif", "Songti SC", serif;
	background: transparent;
	border: none;
	border-bottom: 1rpx solid transparent;
	border-radius: 0;
	padding: 4rpx 0;
	outline: none;
	transition: border-color 0.2s;
}

.info-input:focus {
	border-bottom-color: rgba(29, 29, 31, 0.25);
}

.info-input::placeholder {
	color: #AAA;
}

.info-row-favourite {
	align-items: center;
}

.hearts {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.heart-wrap {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 8rpx;
	cursor: pointer;
	transition: transform 0.2s, opacity 0.2s;
}

.heart-wrap:active {
	transform: scale(0.92);
	opacity: 0.85;
}

.heart-icon {
	width: 40rpx;
	height: 40rpx;
}

.action-bar {
	display: flex;
	border-top: 2rpx solid rgba(0, 0, 0, 0.12);
	margin-top: 52rpx;
	padding-top: 0;
	gap: 0;
}

.action-bar .btn {
	flex: 1;
	text-align: center;
	padding: 28rpx 0;
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 30rpx;
	font-weight: 600;
	cursor: pointer;
	transition: background 0.2s ease;
	border-right: 2rpx solid rgba(0, 0, 0, 0.12);
}

.action-bar .btn:last-child {
	border-right: none;
}

.action-bar .btn:active {
	opacity: 0.85;
}

.default-btn {
	color: #9D8B70;
}

.default-btn.is-default {
	color: #999;
	cursor: default;
}

.delete-btn {
	color: #1D1D1F;
}
</style>
