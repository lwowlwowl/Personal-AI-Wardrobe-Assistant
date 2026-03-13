<template>
	<view v-if="visible" class="modal-overlay modal-overlay-enter" @click="handleOverlayClick">
		<view class="modal-box modal-box-enter" @click.stop>
			<view class="modal-header">
				<view class="modal-header-inner">
					<text class="modal-title">Upload Model Photo</text>
					<text class="close-btn" @click="close">×</text>
				</view>
				<view class="modal-title-divider"></view>
			</view>

			<view class="modal-content" @click.stop @touchstart.stop>
				<view class="form-group">
					<text class="form-label">Model photo name</text>
					<input
						type="text"
						class="form-input"
						v-model="photoName"
						placeholder="Enter model photo name"
						:adjust-position="true"
					/>
				</view>

				<view class="form-group form-group-optional">
					<text class="form-label">Description (optional)</text>
					<textarea
						class="form-textarea"
						v-model="description"
						:placeholder="descriptionPlaceholder"
						maxlength="200"
						:adjust-position="true"
					/>
				</view>

				<view class="form-group switch-group">
					<view class="switch-row">
						<text class="switch-label">Set as default model</text>
						<switch
							class="model-switch"
							:checked="isPrimary"
							@change="onSwitchChange"
							color="#8c7355"
						/>
					</view>
					<text class="form-hint">This model will be used for virtual try-on by default</text>
				</view>
			</view>

			<view class="modal-actions">
				<view class="btn-cancel" @click="close">Cancel</view>
				<view class="btn-confirm" @click="submit">Upload Photo</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
	visible: {
		type: Boolean,
		default: false
	}
})

const emit = defineEmits(['update:visible', 'confirm'])

const photoName = ref('')
const description = ref('')
const isPrimary = ref(false)

const descriptionPlaceholder = 'Describe this model photo...\ne.g. standing pose, front view'

watch(() => props.visible, (v) => {
	if (v) {
		photoName.value = ''
		description.value = ''
		isPrimary.value = false
	}
})

function handleOverlayClick() {
	emit('update:visible', false)
}

function close() {
	emit('update:visible', false)
}

function onSwitchChange(e) {
	isPrimary.value = e.detail.value
}

function submit() {
	const name = (photoName.value || '').trim()
	if (!name) {
		uni.showToast({ title: 'Please enter model photo name', icon: 'none' })
		return
	}
	emit('confirm', {
		photo_name: name,
		description: (description.value || '').trim(),
		is_primary: isPrimary.value
	})
	emit('update:visible', false)
}
</script>

<style scoped>
@keyframes overlayFadeIn {
	from { opacity: 0; }
	to { opacity: 1; }
}

@keyframes modalEnter {
	from {
		opacity: 0;
		transform: translateY(-30px);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 9999;
}

.modal-overlay-enter {
	animation: overlayFadeIn 0.25s ease-out;
}

.modal-box {
	position: relative;
	z-index: 10001;
	width: 90%;
	max-width: 480px;
	background: #fff;
	border-radius: 18px;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
	overflow: hidden;
	display: flex;
	flex-direction: column;
	box-shadow:
		0 10px 30px rgba(0, 0, 0, 0.12),
		0 4px 12px rgba(0, 0, 0, 0.07);
}

.modal-box-enter {
	animation: modalEnter 0.3s ease-out;
}

.modal-header {
	padding: 28px 28px 0;
	font-weight: bold;
	margin-bottom: 10px;
}

.modal-header-inner {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.modal-title {
	font-size: 18px;
	font-weight: 700;
	color: #1d1d1f;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.close-btn {
	font-size: 28px;
	color: #999;
	cursor: pointer;
	line-height: 1;
	padding: 0 4px;
}

.modal-title-divider {
	height: 1px;
	background: #e8e4dc;
	margin-top: 16px;
}

.modal-content {
	padding: 20px;
	flex: 1;
	background-color: #f8f8f8;
	margin: 0 20px;
	border-radius: 12px;
}

.form-group {
	margin-bottom: 20px;
}

.form-group:last-child {
	margin-bottom: 0;
}

.form-label {
	display: block;
	font-size: 14px;
	font-weight: 500;
	color: #4f4f4f;
	margin-bottom: 8px;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.form-input {
	width: 100%;
	box-sizing: border-box;
	background-color: #f7f7f7;
	border-radius: 10px;
	border: 1px solid #e1e1e1;
	padding: 12px 16px;
	min-height: 44px;
	font-size: 14px;
	color: #1d1d1f;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
	transition: all 0.3s ease;
	position: relative;
	z-index: 2;
	-webkit-user-select: text !important;
	user-select: text !important;
	cursor: text;
}

.form-input:focus {
	background-color: #ffffff;
	border: 1px solid #b89c7a;
	box-shadow: 0 0 10px rgba(184, 156, 122, 0.15);
	outline: none;
}

.form-input::placeholder,
.form-input::-webkit-input-placeholder {
	font-weight: 20;
	color: #999;
}

.form-textarea {
	width: 100%;
	box-sizing: border-box;
	background-color: #f7f7f7;
	border-radius: 10px;
	border: 1px solid #e1e1e1;
	padding: 12px 16px;
	min-height: 90px;
	resize: none;
	font-size: 14px;
	color: #1d1d1f;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
	transition: all 0.3s ease;
	position: relative;
	z-index: 2;
	-webkit-user-select: text !important;
	user-select: text !important;
	cursor: text;
}

.form-textarea:focus {
	background-color: #ffffff;
	border: 1px solid #b89c7a;
	box-shadow: 0 0 10px rgba(184, 156, 122, 0.15);
	outline: none;
}

.form-textarea::placeholder,
.form-textarea::-webkit-input-placeholder {
	font-weight: 400;
	color: #999;
}

.switch-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
}

.switch-label {
	font-size: 14px;
	color: #1d1d1f;
	font-weight: 500;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.model-switch {
	transform: scale(0.9);
	transition: transform 0.2s ease;
}

.form-hint {
	display: block;
	font-size: 13px;
	font-weight: 400;
	color: #6c6c6c;
	margin-top: 8px;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.modal-actions {
	padding: 28px;
	border-top: 1px solid #e8e4dc;
	display: flex;
	gap: 12px;
}

.btn-cancel,
.btn-confirm {
	flex: 1;
	padding: 14px 28px;
	text-align: center;
	border-radius: 10px;
	font-size: 14px;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.3s ease;
	border: none;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
}

.btn-cancel {
	background: #f1efeb;
	color: #666;
}

.btn-cancel:hover {
	background: #e8e4dc;
}

.btn-cancel:active {
	opacity: 0.9;
}

.btn-confirm {
	background-color: #8c7355;
	color: #fff;
}

.btn-confirm:hover {
	background-color: #9b8162;
	cursor: pointer;
}

.btn-confirm:active {
	background-color: #7a6349;
	opacity: 0.95;
}
</style>
