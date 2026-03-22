<template>
	<Transition name="forgot-modal">
		<view v-if="visible" class="forgot-mask" @click="handleClose">
			<view class="forgot-panel" @click.stop>
				<view class="forgot-header">
					<text class="forgot-title">Reset password</text>
					<text class="forgot-desc">
						Enter the email and username registered on your account, then set a new password (at least 6 characters).
					</text>
				</view>

				<view class="forgot-block">
					<view class="field-stack">
						<text class="field-label">Email</text>
						<input
							v-model="form.email"
							class="field-input"
							type="text"
							placeholder="Enter your email"
							@input="clearSubmitError"
						/>
					</view>

					<view class="field-stack">
						<text class="field-label">Username</text>
						<input
							v-model="form.username"
							class="field-input"
							type="text"
							placeholder="Enter your username"
							@input="clearSubmitError"
						/>
					</view>

					<view class="field-stack">
						<text class="field-label">New password</text>
						<view class="field-input-wrap password-input-wrapper">
							<input
								v-model="form.newPassword"
								class="field-input"
								:password="!showNewPassword"
								placeholder="Enter your new password"
								@input="clearSubmitError"
							/>
							<view class="eye-icon" @click="showNewPassword = !showNewPassword">
								<image
									class="eye-image"
									:src="showNewPassword ? '/static/eye-open.png' : '/static/eye-close.png'"
									mode="aspectFit"
								></image>
							</view>
						</view>
						<view v-if="form.newPassword.length > 0" class="password-strength">
							<view
								class="strength-bar"
								:class="[
									passwordStrengthClass,
									(passwordStrengthClass === 'strength-medium' || passwordStrengthClass === 'strength-strong')
										? 'strength-bar-ok'
										: ''
								]"
							></view>
							<text
								class="strength-text"
								:class="
									passwordStrengthClass === 'strength-medium' || passwordStrengthClass === 'strength-strong'
										? 'strength-text-green'
										: ''
								"
							>
								{{ passwordStrengthText }}
							</text>
						</view>
					</view>

					<view class="field-stack">
						<text class="field-label">Confirm new password</text>
						<view class="field-input-wrap password-input-wrapper">
							<input
								v-model="form.confirmPassword"
								class="field-input"
								:password="!showConfirmPassword"
								placeholder="Confirm your new password"
								@input="clearSubmitError"
							/>
							<view class="eye-icon" @click="showConfirmPassword = !showConfirmPassword">
								<image
									class="eye-image"
									:src="showConfirmPassword ? '/static/eye-open.png' : '/static/eye-close.png'"
									mode="aspectFit"
								></image>
							</view>
						</view>
						<view v-if="confirmMismatch || submitError" class="field-error-wrap">
							<text class="field-error">{{ confirmMismatch ? 'Passwords do not match.' : submitError }}</text>
						</view>
					</view>

					<view class="btn-row-right">
						<view
							class="btn-primary btn-reset-password"
							:class="{ 'btn-disabled': !formValid || submitting, 'btn-active': formValid && !submitting }"
							@click="onSubmit"
						>
							<text class="btn-text">Reset password</text>
						</view>
					</view>
				</view>

				<view class="forgot-close" @click="handleClose">Cancel</view>
			</view>
		</view>
	</Transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { resetPasswordByIdentity } from '@/api/userApi.js'
import { formatApiErrorMessage } from '@/utils/apiErrors.js'

const props = defineProps({
	visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

const form = ref({
	email: '',
	username: '',
	newPassword: '',
	confirmPassword: ''
})

const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const submitError = ref('')
const submitting = ref(false)

const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const passwordStrengthClass = computed(() => {
	const len = form.value.newPassword.length
	if (len === 0) return ''
	if (len < 6) return 'strength-weak'
	if (len < 10) return 'strength-medium'
	return 'strength-strong'
})

const passwordStrengthText = computed(() => {
	const len = form.value.newPassword.length
	if (len === 0) return ''
	if (len < 6) return 'Too short (min. 6)'
	if (len < 10) return 'OK'
	return 'Strong'
})

const confirmMismatch = computed(() => {
	const a = form.value.newPassword
	const b = form.value.confirmPassword
	return a.length > 0 && b.length > 0 && a !== b
})

const formValid = computed(() => {
	const e = (form.value.email || '').trim()
	const u = (form.value.username || '').trim()
	const p = form.value.newPassword
	const c = form.value.confirmPassword
	return emailRe.test(e) && u.length >= 1 && p.length >= 6 && p === c
})

function resetForm() {
	form.value = { email: '', username: '', newPassword: '', confirmPassword: '' }
	showNewPassword.value = false
	showConfirmPassword.value = false
	submitError.value = ''
}

watch(
	() => props.visible,
	(v) => {
		if (v) resetForm()
	}
)

function handleClose() {
	emit('close')
}

function clearSubmitError() {
	submitError.value = ''
}

async function onSubmit() {
	submitError.value = ''
	const e = (form.value.email || '').trim()
	if (!e) {
		submitError.value = 'Please enter your email.'
		return
	}
	if (!emailRe.test(e)) {
		submitError.value = 'Please enter a valid email address.'
		return
	}
	if (!(form.value.username || '').trim()) {
		submitError.value = 'Please enter your username.'
		return
	}
	if (form.value.newPassword.length < 6) {
		submitError.value = 'New password must be at least 6 characters.'
		return
	}
	if (form.value.newPassword !== form.value.confirmPassword) {
		submitError.value = 'Passwords do not match.'
		return
	}
	if (!formValid.value || submitting.value) return

	submitting.value = true
	uni.showLoading({ title: 'Please wait…', mask: true })
	try {
		const res = await resetPasswordByIdentity({
			email: e,
			username: (form.value.username || '').trim(),
			new_password: form.value.newPassword,
			confirm_password: form.value.confirmPassword
		})
		uni.hideLoading()
		submitting.value = false

		if (res.statusCode === 200 && res.data?.success) {
			handleClose()
			setTimeout(() => {
				uni.showToast({
					title: res.data.message || 'Password has been reset. You can sign in now.',
					icon: 'success',
					duration: 2200
				})
			}, 120)
			return
		}

		const fallback =
			res.statusCode === 400
				? 'Email and username do not match our records.'
				: res.statusCode >= 500
					? 'Server error. Please try again later.'
					: 'Could not reset password. Please try again.'
		submitError.value = formatApiErrorMessage(res.data, fallback)
	} catch {
		uni.hideLoading()
		submitting.value = false
		submitError.value = 'Network error. Please check if the backend is running.'
	}
}
</script>

<style scoped>
.forgot-modal-enter-active,
.forgot-modal-leave-active {
	transition: opacity 0.4s ease;
}
.forgot-modal-enter-active .forgot-panel,
.forgot-modal-leave-active .forgot-panel {
	transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.forgot-modal-enter-from,
.forgot-modal-leave-to {
	opacity: 0;
}
.forgot-modal-enter-from .forgot-panel {
	transform: translateY(40rpx) scale(0.96);
	opacity: 0;
}
.forgot-modal-leave-to .forgot-panel {
	transform: translateY(20rpx) scale(0.98);
	opacity: 0;
}

.forgot-mask {
	position: fixed;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.25);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	z-index: 2000;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 40rpx;
	box-sizing: border-box;
}

.forgot-panel {
	width: 100%;
	max-width: 880rpx;
	background: linear-gradient(135deg, rgba(252, 250, 245, 0.9) 0%, rgba(246, 243, 238, 0.7) 100%);
	backdrop-filter: blur(40px) saturate(120%);
	-webkit-backdrop-filter: blur(40px) saturate(120%);
	border-radius: 28rpx;
	box-shadow:
		inset 0 1px 1px rgba(255, 255, 255, 0.9),
		inset 0 -1px 1px rgba(164, 147, 127, 0.1),
		0 16px 40px -8px rgba(164, 147, 127, 0.2),
		0 32px 80px -16px rgba(164, 147, 127, 0.15);
	border: 1px solid rgba(255, 255, 255, 0.4);
	padding: 48rpx 44rpx 40rpx;
	max-height: 88vh;
	overflow-y: auto;
	font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.forgot-header {
	margin-bottom: 36rpx;
	text-align: center;
}

.forgot-title {
	display: block;
	font-family: 'Didot', 'Bodoni MT', 'Noto Serif', 'Songti SC', serif;
	font-size: 48rpx;
	font-weight: 600;
	color: #3b3833;
	letter-spacing: 0.04em;
	margin-bottom: 12rpx;
}

.forgot-desc {
	display: block;
	font-size: 26rpx;
	color: #8c857b;
	font-weight: 400;
	line-height: 1.45;
	letter-spacing: 0.01em;
}

.forgot-block {
	border-radius: 22rpx;
	padding: 44rpx 40rpx;
	margin-bottom: 8rpx;
	background: rgba(246, 243, 238, 0.6);
	box-shadow: inset 0 2rpx 10rpx rgba(0, 0, 0, 0.01);
}

.field-stack {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	margin-bottom: 24rpx;
}

.field-label {
	font-size: 26rpx;
	font-weight: 500;
	color: #6b655c;
	letter-spacing: 0.01em;
}

.field-input {
	width: 100%;
	height: 84rpx;
	padding: 0 28rpx;
	font-size: 28rpx;
	font-weight: 400;
	color: #3b3833;
	border: 1px solid transparent;
	border-radius: 16rpx;
	box-sizing: border-box;
	background: rgba(164, 147, 127, 0.05);
	box-shadow:
		inset 0 2px 4px rgba(164, 147, 127, 0.1),
		0 1px 0 rgba(255, 255, 255, 0.8);
	transition: all 0.3s cubic-bezier(0.25, 0.8, 0.2, 1);
}

.field-input:focus {
	outline: none;
	background: rgba(255, 255, 255, 0.9);
	box-shadow:
		0 0 0 1px #a4937f,
		0 4px 12px rgba(164, 147, 127, 0.15);
	transform: translateY(-1px);
}

.field-input-wrap {
	position: relative;
	width: 100%;
}

.password-input-wrapper .field-input {
	padding-right: 72rpx;
}

.eye-icon {
	position: absolute;
	right: 28rpx;
	top: 50%;
	transform: translateY(-50%);
	width: 40rpx;
	height: 40rpx;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: opacity 0.2s ease;
}

.eye-icon:hover {
	opacity: 0.7;
}

.eye-image {
	width: 100%;
	height: 100%;
	user-select: none;
}

.field-error-wrap {
	background: rgba(194, 116, 112, 0.08);
	border-radius: 12rpx;
	padding: 12rpx 16rpx;
	margin-top: 8rpx;
	margin-bottom: 4rpx;
}

.field-error {
	display: block;
	font-size: 24rpx;
	font-weight: 500;
	color: #b86561;
}

.password-strength {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-top: 12rpx;
	margin-bottom: 8rpx;
}

.strength-bar {
	height: 8rpx;
	border-radius: 4rpx;
	width: 120rpx;
	transition:
		width 0.25s ease,
		background 0.25s ease;
}

.strength-bar.strength-weak {
	width: 40rpx;
	background: rgba(184, 84, 80, 0.5);
}

.strength-bar.strength-medium {
	width: 80rpx;
	background: rgba(200, 160, 80, 0.6);
}

.strength-bar.strength-strong {
	width: 120rpx;
	background: rgba(100, 160, 120, 0.5);
}

.strength-bar-ok.strength-medium {
	background: rgba(76, 175, 80, 0.6);
}

.strength-bar-ok.strength-strong {
	background: rgba(76, 175, 80, 0.75);
}

.strength-text {
	font-size: 24rpx;
	color: #6b6b6b;
	font-weight: 400;
}

.strength-text-green {
	color: #2e7d32;
}

.btn-row-right {
	display: flex;
	justify-content: flex-end;
	margin-top: 8rpx;
}

.btn-primary {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	padding: 14rpx 28rpx;
	font-size: 24rpx;
	font-weight: 500;
	font-family: inherit;
	border-radius: 18rpx;
	margin-top: 16rpx;
	cursor: pointer;
	border: none;
	transition: all 0.25s cubic-bezier(0.25, 0.8, 0.2, 1);
}

.btn-reset-password.btn-active {
	background: #a4937f;
	color: #fff;
	box-shadow: 0 6rpx 20rpx rgba(164, 147, 127, 0.3);
}

.btn-reset-password.btn-active:hover {
	background: #8f7f6c;
	box-shadow: 0 8rpx 24rpx rgba(164, 147, 127, 0.4);
	transform: translateY(-2rpx);
}

.btn-reset-password.btn-active:active {
	transform: scale(0.96) translateY(0);
	box-shadow: 0 2rpx 12rpx rgba(164, 147, 127, 0.25);
}

.btn-reset-password.btn-disabled {
	background: rgba(210, 200, 185, 0.4) !important;
	color: #c0b7a8 !important;
	cursor: not-allowed;
	box-shadow: none;
	transform: none;
}

.forgot-close {
	text-align: center;
	font-size: 28rpx;
	font-weight: 500;
	color: #8c857b;
	margin-top: 20rpx;
	padding: 24rpx 0;
	cursor: pointer;
	transition:
		color 0.2s ease,
		transform 0.2s cubic-bezier(0.25, 0.8, 0.2, 1);
	letter-spacing: 0.02em;
}

.forgot-close:hover {
	color: #a4937f;
	font-weight: 600;
}

.forgot-close:active {
	transform: scale(0.98);
}
</style>
