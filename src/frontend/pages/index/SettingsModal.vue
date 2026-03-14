<template>
	<Transition name="modal">
		<view v-if="visible" class="settings-mask" @click="handleClose">
			<view class="settings-panel" @click.stop>
				<view class="settings-header">
					<text class="settings-title">Account Settings</text>
					<text class="settings-desc">Manage your profile and security</text>
				</view>

				<!-- 个人信息块：头像 + 用户名 -->
				<view class="settings-block settings-block-personal">
					<text class="block-title">Personal information</text>
					<text class="block-desc">Update your avatar and display name</text>

					<view class="avatar-section">
						<view class="avatar-wrap" @click="handleChooseAvatar">
							<image
								v-if="userProfile?.avatar_url"
								:src="userAvatarUrl(userProfile.avatar_url)"
								mode="aspectFill"
								class="avatar-img"
							></image>
							<image v-else src="/static/icons/icon-user.svg" mode="aspectFit" class="avatar-placeholder"></image>
							<view v-if="uploadingAvatar" class="avatar-loading">
								<text class="avatar-loading-text">Uploading…</text>
							</view>
							<view class="avatar-overlay">
								<image src="/static/icons/icon-edit.svg" mode="aspectFit" class="avatar-overlay-icon"></image>
								<text class="avatar-overlay-text">Change</text>
							</view>
						</view>
					</view>

					<view class="username-section">
						<view class="field-stack">
							<text class="field-label">Username</text>
							<text class="field-hint" :class="{ 'field-hint-error': usernameLengthInvalid }">Editable, at least 3 characters</text>
							<input
								id="settings-username"
								v-model="settingsUsername"
								class="field-input"
								type="text"
								placeholder="Enter your username"
								@input="onUsernameInput"
							/>
						</view>
						<view v-if="settingsUsernameError" class="field-error-wrap">
							<text class="field-error">{{ settingsUsernameError }}</text>
						</view>
						<view class="btn-row-right">
							<view
								class="btn-secondary btn-save-username"
								:class="{ 'btn-disabled': !usernameValid, 'btn-active': usernameValid }"
								@click="usernameValid && saveUsername()"
							>
								<text class="btn-text">Save</text>
							</view>
						</view>
					</view>
				</view>

			<!-- 密码修改块 -->
				<view class="settings-block settings-block-password">
					<text class="block-title">Change password</text>
					<text class="block-desc">Enter current password and set a new one. Password should be at least 6 characters long.</text>

					<view class="field-stack">
						<text class="field-label">Current password</text>
						<view class="field-input-wrap password-input-wrapper">
							<input
								v-model="settingsCurrentPassword"
								class="field-input"
								:password="!showCurrentPassword"
								placeholder="Enter your current password"
								@input="onPasswordInput"
							/>
							<view class="eye-icon" @click="toggleShowCurrentPassword">
								<image class="eye-image" :src="showCurrentPassword ? '/static/eye-open.png' : '/static/eye-close.png'" mode="aspectFit"></image>
							</view>
						</view>
					</view>

					<view class="field-stack">
						<text class="field-label">New password</text>
						<view class="field-input-wrap password-input-wrapper">
							<input
								v-model="settingsNewPassword"
								class="field-input"
								:password="!showNewPassword"
								placeholder="Enter your new password"
								@input="onPasswordInput"
							/>
							<view class="eye-icon" @click="toggleShowNewPassword">
								<image class="eye-image" :src="showNewPassword ? '/static/eye-open.png' : '/static/eye-close.png'" mode="aspectFit"></image>
							</view>
						</view>
						<view v-if="settingsNewPassword.length > 0" class="password-strength">
							<view class="strength-bar" :class="[passwordStrengthClass, (passwordStrengthClass === 'strength-medium' || passwordStrengthClass === 'strength-strong') ? 'strength-bar-ok' : '']"></view>
							<text class="strength-text" :class="(passwordStrengthClass === 'strength-medium' || passwordStrengthClass === 'strength-strong') ? 'strength-text-green' : ''">{{ passwordStrengthText }}</text>
						</view>
					</view>

					<view class="field-stack">
						<text class="field-label">Confirm new password</text>
						<view class="field-input-wrap password-input-wrapper">
							<input
								v-model="settingsConfirmPassword"
								class="field-input"
								:password="!showConfirmPassword"
								placeholder="Confirm your new password"
								@input="onPasswordInput"
							/>
							<view class="eye-icon" @click="toggleShowConfirmPassword">
								<image class="eye-image" :src="showConfirmPassword ? '/static/eye-open.png' : '/static/eye-close.png'" mode="aspectFit"></image>
							</view>
						</view>
						<view v-if="confirmMismatch || settingsPasswordError" class="field-error-wrap">
							<text class="field-error">{{ confirmMismatch ? 'Passwords do not match.' : settingsPasswordError }}</text>
						</view>
					</view>

					<view class="btn-row-right">
						<view
							class="btn-primary btn-change-password"
							:class="{ 'btn-disabled': !passwordFormValid, 'btn-active': passwordFormValid }"
							@click="onChangePasswordClick"
						>
							<text class="btn-text">Change password</text>
						</view>
					</view>
				</view>

				<view class="settings-close" @click="handleClose">Close</view>
			</view>
		</view>
	</Transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { uploadUserAvatar, updateUsersMe, changePassword, API_BASE_URL } from '@/api/userApi.js'

const props = defineProps({
	visible: { type: Boolean, default: false },
	userProfile: { type: Object, default: () => null },
	displayUserName: { type: String, default: '' }
})

const emit = defineEmits(['close', 'update:userProfile'])

const settingsUsername = ref('')
const settingsUsernameError = ref('')
const settingsCurrentPassword = ref('')
const settingsNewPassword = ref('')
const settingsConfirmPassword = ref('')
const settingsPasswordError = ref('')
const uploadingAvatar = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

function userAvatarUrl(url) {
	if (!url) return ''
	return url.startsWith('http') ? url : `${API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
}

// 用户名实时校验：至少 3 字符
const usernameValid = computed(() => {
	const name = (settingsUsername.value || '').trim()
	return name.length >= 3
})

const usernameLengthInvalid = computed(() => {
	const name = (settingsUsername.value || '').trim()
	return name.length > 0 && name.length < 3
})

function onUsernameInput() {
	const name = (settingsUsername.value || '').trim()
	if (name.length >= 3) settingsUsernameError.value = ''
}

// 密码强度（简单：仅按长度）
const passwordStrengthClass = computed(() => {
	const len = settingsNewPassword.value.length
	if (len === 0) return ''
	if (len < 6) return 'strength-weak'
	if (len < 10) return 'strength-medium'
	return 'strength-strong'
})

const passwordStrengthText = computed(() => {
	const len = settingsNewPassword.value.length
	if (len === 0) return ''
	if (len < 6) return 'Too short (min. 6)'
	if (len < 10) return 'OK'
	return 'Strong'
})

const confirmMismatch = computed(() => {
	const newPwd = settingsNewPassword.value
	const confirm = settingsConfirmPassword.value
	return newPwd.length > 0 && confirm.length > 0 && newPwd !== confirm
})

// 密码表单可提交：当前密码非空、新密码≥6、确认一致
const passwordFormValid = computed(() => {
	const current = settingsCurrentPassword.value
	const newPwd = settingsNewPassword.value
	const confirm = settingsConfirmPassword.value
	return current.length > 0 && newPwd.length >= 6 && newPwd === confirm
})

function toggleShowCurrentPassword() { showCurrentPassword.value = !showCurrentPassword.value }
function toggleShowNewPassword() { showNewPassword.value = !showNewPassword.value }
function toggleShowConfirmPassword() { showConfirmPassword.value = !showConfirmPassword.value }

watch(() => [props.visible, props.userProfile?.username, props.displayUserName], () => {
	if (props.visible) {
		settingsUsername.value = props.userProfile?.username || props.displayUserName || ''
		settingsUsernameError.value = ''
		settingsCurrentPassword.value = ''
		settingsNewPassword.value = ''
		settingsConfirmPassword.value = ''
		settingsPasswordError.value = ''
		showCurrentPassword.value = false
		showNewPassword.value = false
		showConfirmPassword.value = false
	}
}, { immediate: true })

function handleClose() {
	emit('close')
}

async function saveUsername() {
	if (!usernameValid.value) return
	const name = (settingsUsername.value || '').trim()
	settingsUsernameError.value = ''
	const token = uni.getStorageSync('auth_token')
	if (!token) return
	try {
		const res = await updateUsersMe(token, { username: name })
		if (res.statusCode === 200 && res.data) {
			emit('update:userProfile', { username: res.data.username || name })
			emit('close')
			setTimeout(() => { uni.showToast({ title: 'Saved!', icon: 'success' }) }, 100)
		} else {
			const d = res.data?.detail
			settingsUsernameError.value = Array.isArray(d) ? (d[0] || 'Save failed') : (d || 'Save failed')
		}
	} catch {
		settingsUsernameError.value = 'Network error'
	}
}

/** 根据后端返回的 detail 和 statusCode 给出具体原因，方便用户知道是「当前密码错误」还是其他 */
function passwordFailureMessage(detail, statusCode) {
	const msg = Array.isArray(detail) ? (detail[0] || '') : (detail || '')
	const s = (msg || '').toString()
	if (/当前密码|密码错误|incorrect|wrong|修改失败/i.test(s)) return 'Current password is incorrect.'
	if (statusCode === 400) return 'Current password is incorrect.'
	return s || 'Failed to change password.'
}

/** 点击「Change password」时：先在校验处统一把错误显示在 Confirm 下方，再在通过时发请求 */
function onChangePasswordClick() {
	settingsPasswordError.value = ''
	const current = settingsCurrentPassword.value
	const newPwd = settingsNewPassword.value
	const confirm = settingsConfirmPassword.value
	if (!current.length) {
		settingsPasswordError.value = 'Please enter your current password.'
		return
	}
	if (newPwd.length < 6) {
		settingsPasswordError.value = 'New password must be at least 6 characters.'
		return
	}
	if (newPwd !== confirm) {
		settingsPasswordError.value = 'Passwords do not match.'
		return
	}
	if (current === newPwd) {
		settingsPasswordError.value = 'New password cannot be the same as current password.'
		return
	}
	savePassword()
}

async function savePassword() {
	const current = settingsCurrentPassword.value
	const newPwd = settingsNewPassword.value
	settingsPasswordError.value = ''
	const token = uni.getStorageSync('auth_token')
	if (!token) return
	try {
		const res = await changePassword(token, current, newPwd)
		if (res.statusCode === 200) {
			settingsCurrentPassword.value = ''
			settingsNewPassword.value = ''
			settingsConfirmPassword.value = ''
			emit('close')
			setTimeout(() => { uni.showToast({ title: 'Changed!', icon: 'success' }) }, 100)
		} else {
			const d = res.data?.detail ?? res.data
			settingsPasswordError.value = passwordFailureMessage(d, res.statusCode)
		}
	} catch {
		settingsPasswordError.value = 'Network error'
	}
}

function onPasswordInput() {
	settingsPasswordError.value = ''
}

function handleChooseAvatar() {
	if (uploadingAvatar.value) return
	uni.chooseImage({
		count: 1,
		sizeType: ['compressed'],
		sourceType: ['album', 'camera'],
		success: async (res) => {
			const filePath = res.tempFilePaths[0]
			const token = uni.getStorageSync('auth_token')
			if (!token) return
			uploadingAvatar.value = true
			try {
				const upRes = await uploadUserAvatar({ token, filePath })
				if (upRes.statusCode === 200 && upRes.data?.avatar_url) {
					emit('update:userProfile', { avatar_url: upRes.data.avatar_url })
				}
			} finally {
				uploadingAvatar.value = false
			}
		}
	})
}
</script>

<style scoped>
/* ========== 入场/离场动效 ========== */
.modal-enter-active,
.modal-leave-active {
	transition: opacity 0.4s ease;
}
.modal-enter-active .settings-panel,
.modal-leave-active .settings-panel {
	transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-enter-from,
.modal-leave-to {
	opacity: 0;
}
.modal-enter-from .settings-panel {
	transform: translateY(40rpx) scale(0.96);
	opacity: 0;
}
.modal-leave-to .settings-panel {
	transform: translateY(20rpx) scale(0.98);
	opacity: 0;
}

/* ========== 毛玻璃遮罩 ========== */
.settings-mask {
	position: fixed;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.25);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	z-index: 1000;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 40rpx;
	box-sizing: border-box;
}

/* ========== 弹窗本体：高阶玻璃拟态 (VisionOS 级光影) ========== */
.settings-panel {
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
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.settings-header {
	margin-bottom: 40rpx;
	text-align: center;
	position: relative;
}

.settings-title {
	display: block;
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 48rpx;
	font-weight: 600;
	color: #3B3833;
	letter-spacing: 0.04em;
	margin-bottom: 12rpx;
}

.settings-desc {
	display: block;
	font-size: 26rpx;
	color: #8C857B;
	font-weight: 400;
	letter-spacing: 0.01em;
}

/* 分块卡片：极致留白，加大内边距约 20% */
.settings-block {
	border-radius: 22rpx;
	padding: 44rpx 40rpx;
	margin-bottom: 28rpx;
	border: none;
}

.settings-block-personal {
	background: rgba(255, 255, 255, 0.7);
	box-shadow: 0 4rpx 20rpx rgba(130, 120, 105, 0.04);
}

.settings-block-password {
	margin-bottom: 24rpx;
	background: rgba(246, 243, 238, 0.6);
	box-shadow: inset 0 2rpx 10rpx rgba(0, 0, 0, 0.01);
}

.block-title {
	display: block;
	font-size: 30rpx;
	font-weight: 600;
	color: #3B3833;
	margin-bottom: 8rpx;
	letter-spacing: 0.02em;
}

.block-desc {
	display: block;
	font-size: 24rpx;
	color: #8C857B;
	margin-bottom: 28rpx;
	line-height: 1.45;
	font-weight: 400;
}

/* 头像区域：破局 - 悬浮溢出 + 多层光环徽章感 */
.avatar-section {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-top: -24rpx;
	margin-bottom: 28rpx;
}

.avatar-wrap {
	position: relative;
	width: 188rpx;
	height: 188rpx;
	border-radius: 50%;
	overflow: hidden;
	background: rgba(0, 0, 0, 0.06);
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	box-shadow:
		0 0 0 2rpx rgba(255, 255, 255, 0.9),
		0 0 0 6rpx rgba(164, 147, 127, 0.12),
		0 0 0 10rpx rgba(255, 255, 255, 0.5),
		0 12rpx 40rpx rgba(164, 147, 127, 0.15),
		0 24rpx 48rpx -8rpx rgba(164, 147, 127, 0.1);
	border: none;
	margin-bottom: 20rpx;
	transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.2, 1), box-shadow 0.3s ease;
}

.avatar-wrap:hover {
	transform: scale(1.03);
	box-shadow:
		0 0 0 2rpx rgba(255, 255, 255, 0.95),
		0 0 0 6rpx rgba(164, 147, 127, 0.18),
		0 0 0 10rpx rgba(255, 255, 255, 0.6),
		0 16rpx 48rpx rgba(164, 147, 127, 0.2),
		0 32rpx 64rpx -8rpx rgba(164, 147, 127, 0.12);
}

.avatar-wrap:active {
	transform: scale(0.98);
}

.avatar-overlay {
	position: absolute;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.45);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 8rpx;
	opacity: 0;
	transition: opacity 0.25s ease;
}

.avatar-wrap:hover .avatar-overlay {
	opacity: 1;
}

.avatar-overlay-icon {
	width: 36rpx;
	height: 36rpx;
	filter: brightness(0) invert(1);
}

.avatar-overlay-text {
	color: #fff;
	font-size: 22rpx;
	font-weight: 500;
	letter-spacing: 0.02em;
}

.avatar-img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.avatar-placeholder {
	width: 80rpx;
	height: 80rpx;
	opacity: 0.6;
}

.avatar-loading {
	position: absolute;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 2;
}

.avatar-loading-text {
	color: #fff;
	font-size: 24rpx;
}

/* 次要按钮（Save）：与暖色背景融为一体 */
.btn-secondary {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 10rpx;
	padding: 12rpx 24rpx;
	font-size: 24rpx;
	font-family: inherit;
	font-weight: 500;
	background: rgba(164, 147, 127, 0.08);
	color: #7A6F62;
	border: 1px solid rgba(164, 147, 127, 0.15);
	border-radius: 18rpx;
	cursor: pointer;
	transition: all 0.25s cubic-bezier(0.25, 0.8, 0.2, 1);
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.btn-secondary:hover {
	background: #472904;
	color: #fff;
	box-shadow: 0 4rpx 12rpx rgba(110, 95, 80, 0.35);
}

.btn-secondary:active {
	transform: scale(0.96);
}

.btn-row-right {
	display: flex;
	justify-content: flex-end;
	margin-top: 20rpx;
}

.settings-block-password .btn-row-right {
	margin-top: 24rpx;
}

/* 上下结构：Label 在上，Input 占满宽度 */
.field-stack {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	margin-bottom: 24rpx;
}

.username-section .field-stack {
	margin-bottom: 16rpx;
}

.field-label {
	font-size: 26rpx;
	font-weight: 500;
	color: #6B655C;
	letter-spacing: 0.01em;
}

.field-hint {
	display: block;
	font-size: 24rpx;
	color: #A39B90;
	margin-top: 2rpx;
	font-weight: 400;
}

.field-hint-error {
	color: #B86561;
}

/* 输入框：雕刻感 (Recessed) - 嵌入材质内部的凹陷感 */
.field-input {
	width: 100%;
	height: 84rpx;
	padding: 0 28rpx;
	font-size: 28rpx;
	font-weight: 400;
	color: #3B3833;
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
		0 0 0 1px #A4937F,
		0 4px 12px rgba(164, 147, 127, 0.15);
	transform: translateY(-1px);
}

.password-input-wrapper {
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

/* 报错：柔和浅红背景 + 淡红文字 */
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
	color: #B86561;
}

/* 密码强度 */
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
	transition: width 0.25s ease, background 0.25s ease;
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
	color: #6B6B6B;
	font-weight: 400;
}

.strength-text-green {
	color: #2E7D32;
}

.btn-save-username.btn-disabled {
	opacity: 0.5;
	cursor: not-allowed;
	background: rgba(0, 0, 0, 0.04) !important;
}

.btn-save-username.btn-active {
	background: #8F7F6C;
	color: #fff;
	border-color: rgba(143, 127, 108, 0.6);
	box-shadow: 0 4rpx 12rpx rgba(110, 95, 80, 0.2);
}

.btn-save-username.btn-active:hover {
	background: #7A6B5A;
	color: #fff;
	box-shadow: 0 6rpx 16rpx rgba(110, 95, 80, 0.35);
}

/* 主要按钮：提取主页选中菜单的灰棕/摩卡色 */
.btn-primary {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	padding: 14rpx 28rpx;
	font-size: 24rpx;
	font-weight: 500;
	font-family: inherit;
	border-radius: 18rpx;
	margin-top: 24rpx;
	cursor: pointer;
	border: none;
	transition: all 0.25s cubic-bezier(0.25, 0.8, 0.2, 1);
}

.btn-change-password.btn-active {
	background: #A4937F;
	color: #fff;
	box-shadow: 0 6rpx 20rpx rgba(164, 147, 127, 0.3);
}

.btn-change-password.btn-active:hover {
	background: #8F7F6C;
	box-shadow: 0 8rpx 24rpx rgba(164, 147, 127, 0.4);
	transform: translateY(-2rpx);
}

.btn-change-password.btn-active:active {
	transform: scale(0.96) translateY(0);
	box-shadow: 0 2rpx 12rpx rgba(164, 147, 127, 0.25);
}

.btn-change-password.btn-disabled {
	background: rgba(210, 200, 185, 0.4) !important;
	color: #C0B7A8 !important;
	cursor: not-allowed;
	box-shadow: none;
	transform: none;
}

/* Close 按钮 */
.settings-close {
	text-align: center;
	font-size: 28rpx;
	font-weight: 500;
	color: #8C857B;
	margin-top: 24rpx;
	padding: 24rpx 0;
	cursor: pointer;
	transition: color 0.2s ease, transform 0.2s cubic-bezier(0.25, 0.8, 0.2, 1);
	letter-spacing: 0.02em;
}

.settings-close:hover {
	color: #A4937F;
	font-weight: 600;
}

.settings-close:active {
	transform: scale(0.98);
}
</style>
