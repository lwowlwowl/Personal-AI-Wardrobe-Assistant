<template>
	<view v-if="visible" class="settings-mask high-contrast" @click="handleClose">
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
					</view>
				</view>

				<view class="username-section">
					<view class="field-row">
						<view class="field-label-wrap">
							<view class="field-label-row">
								<text class="field-label">Username</text>
								<image src="/static/icons/icon-edit.svg" mode="aspectFit" class="field-edit-icon"></image>
							</view>
							<text class="field-hint">Editable, at least 3 characters</text>
						</view>
						<view class="field-input-wrap">
							<input
								id="settings-username"
								v-model="settingsUsername"
								class="field-input"
								type="text"
								placeholder="Enter your username"
								@input="onUsernameInput"
							/>
						</view>
					</view>
					<text v-if="settingsUsernameError" class="field-error">{{ settingsUsernameError }}</text>
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

				<view class="field-row field-row-spaced">
					<view class="field-label-wrap">
						<text class="field-label">Current password</text>
					</view>
					<view class="field-input-wrap">
						<input
							v-model="settingsCurrentPassword"
							class="field-input"
							type="password"
							placeholder="Enter your current password"
							@input="onPasswordInput"
						/>
					</view>
				</view>

				<view class="field-row field-row-spaced">
					<view class="field-label-wrap">
						<text class="field-label">New password</text>
						<text class="field-hint field-hint-inline">At least 6 characters</text>
					</view>
					<view class="field-input-wrap">
						<input
							v-model="settingsNewPassword"
							class="field-input"
							type="password"
							placeholder="Enter your new password"
							@input="onPasswordInput"
						/>
					</view>
				</view>
				<text v-if="settingsNewPassword.length > 0 && settingsNewPassword.length < 6" class="field-error field-error-inline">Password should be at least 6 characters long.</text>
				<view v-if="settingsNewPassword.length > 0" class="password-strength">
					<view class="strength-bar" :class="passwordStrengthClass"></view>
					<text class="strength-text">{{ passwordStrengthText }}</text>
				</view>

				<view class="field-row field-row-spaced">
					<view class="field-label-wrap">
						<text class="field-label">Confirm new password</text>
					</view>
					<view class="field-input-wrap">
						<input
							v-model="settingsConfirmPassword"
							class="field-input"
							type="password"
							placeholder="Confirm your new password"
							@input="onPasswordInput"
						/>
					</view>
				</view>
				<text v-if="confirmMismatch" class="field-error">Passwords do not match</text>
				<text v-if="settingsPasswordError" class="field-error">{{ settingsPasswordError }}</text>

				<view class="btn-row-right">
					<view
						class="btn-primary btn-change-password"
						:class="{ 'btn-disabled': !passwordFormValid, 'btn-active': passwordFormValid }"
						@click="passwordFormValid && savePassword()"
					>
						<text class="btn-text">Change password</text>
					</view>
				</view>
			</view>

			<view class="settings-close" @click="handleClose">Close</view>
		</view>
	</view>
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

function userAvatarUrl(url) {
	if (!url) return ''
	return url.startsWith('http') ? url : `${API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
}

// 用户名实时校验：至少 3 字符
const usernameValid = computed(() => {
	const name = (settingsUsername.value || '').trim()
	return name.length >= 3
})

function onUsernameInput() {
	const name = (settingsUsername.value || '').trim()
	if (name.length > 0 && name.length < 3) {
		settingsUsernameError.value = 'At least 3 characters'
	} else {
		settingsUsernameError.value = ''
	}
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

watch(() => [props.visible, props.userProfile?.username, props.displayUserName], () => {
	if (props.visible) {
		settingsUsername.value = props.userProfile?.username || props.displayUserName || ''
		settingsUsernameError.value = ''
		settingsCurrentPassword.value = ''
		settingsNewPassword.value = ''
		settingsConfirmPassword.value = ''
		settingsPasswordError.value = ''
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
			uni.showToast({ title: 'Saved', icon: 'success' })
		} else {
			const d = res.data?.detail
			settingsUsernameError.value = Array.isArray(d) ? (d[0] || 'Save failed') : (d || 'Save failed')
		}
	} catch {
		settingsUsernameError.value = 'Network error'
	}
}

async function savePassword() {
	if (!passwordFormValid.value) return
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
			uni.showToast({ title: 'Password updated', icon: 'success' })
		} else {
			const d = res.data?.detail
			settingsPasswordError.value = Array.isArray(d) ? (d[0] || 'Failed') : (d || 'Failed')
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
.settings-mask {
	position: fixed;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.45);
	z-index: 1000;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 40rpx;
	box-sizing: border-box;
}

.settings-mask.high-contrast {
	background: rgba(0, 0, 0, 0.6);
}

.settings-mask.high-contrast .settings-panel {
	background: #FFFEF9;
	border: 2rpx solid #2C2C2C;
	box-shadow: 0 24rpx 64rpx rgba(0, 0, 0, 0.25);
}

.settings-mask.high-contrast .settings-title,
.settings-mask.high-contrast .block-title,
.settings-mask.high-contrast .field-label { color: #1A1A1A; }
.settings-mask.high-contrast .settings-desc,
.settings-mask.high-contrast .block-desc,
.settings-mask.high-contrast .field-hint { color: #444; }
.settings-mask.high-contrast .field-input { border-width: 2rpx; border-color: #333; background: #fff; }

.settings-panel {
	width: 100%;
	max-width: 880rpx;
	background: linear-gradient(165deg, #FDFBF7 0%, #F7F3EC 50%, #F0EAE0 100%);
	border-radius: 28rpx;
	box-shadow: 0 24rpx 64rpx rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.04);
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
	font-size: 44rpx;
	font-weight: 600;
	color: #1D1D1F;
	letter-spacing: 0.02em;
	margin-bottom: 12rpx;
}

.settings-desc {
	display: block;
	font-size: 26rpx;
	color: #6B6B6B;
	font-weight: 400;
	letter-spacing: 0.01em;
}

/* 分块卡片 */
.settings-block {
	border-radius: 22rpx;
	box-shadow: 0 6rpx 24rpx rgba(0, 0, 0, 0.08), 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
	padding: 36rpx 32rpx;
	margin-bottom: 28rpx;
}

.settings-block-personal {
	background: #fff;
	border: 1rpx solid rgba(0, 0, 0, 0.06);
}

.settings-block-password {
	margin-bottom: 24rpx;
	background: #F8F6F2;
	border: 1rpx solid rgba(0, 0, 0, 0.08);
	box-shadow: 0 6rpx 24rpx rgba(0, 0, 0, 0.06), inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
}

.block-title {
	display: block;
	font-size: 30rpx;
	font-weight: 600;
	color: #1D1D1F;
	margin-bottom: 8rpx;
	letter-spacing: 0.02em;
}

.block-desc {
	display: block;
	font-size: 24rpx;
	color: #6B6B6B;
	margin-bottom: 28rpx;
	line-height: 1.45;
	font-weight: 400;
}

/* 头像区域 */
.avatar-section {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 28rpx;
}

.avatar-wrap {
	position: relative;
	width: 160rpx;
	height: 160rpx;
	border-radius: 50%;
	overflow: hidden;
	background: #F1ECE4;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.12);
	border: 4rpx solid rgba(255, 255, 255, 0.9);
	margin-bottom: 20rpx;
	transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.avatar-wrap:hover {
	transform: scale(1.02);
	box-shadow: 0 10rpx 28rpx rgba(0, 0, 0, 0.14);
}

.avatar-wrap:active {
	transform: scale(0.98);
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
}

.avatar-loading-text {
	color: #fff;
	font-size: 24rpx;
}

/* 次要按钮（Save）：浅色背景 + 圆角 + 边框 */
.btn-secondary {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: 10rpx;
	padding: 12rpx 24rpx;
	font-size: 24rpx;
	font-family: inherit;
	font-weight: 600;
	background: #E8E2D8;
	border: 2rpx solid rgba(139, 115, 85, 0.25);
	border-radius: 18rpx;
	cursor: pointer;
	transition: background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease, border-color 0.2s ease;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.06);
}

.btn-secondary:hover {
	background: #DDD6CA;
	border-color: rgba(139, 115, 85, 0.35);
	box-shadow: 0 6rpx 16rpx rgba(0, 0, 0, 0.08);
}

.btn-secondary:active {
	transform: scale(0.97);
	background: #D2CABE;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

/* 按钮右对齐 */
.btn-row-right {
	display: flex;
	justify-content: flex-end;
	margin-top: 20rpx;
}

.settings-block-password .btn-row-right {
	margin-top: 24rpx;
}

/* 左标签 + 右输入 横向行 */
.field-row {
	display: flex;
	align-items: center;
	gap: 28rpx;
	margin-bottom: 24rpx;
}

.field-row-spaced {
	margin-bottom: 32rpx;
	min-height: 88rpx;
	align-items: center;
}

.field-label-wrap {
	min-width: 200rpx;
	flex-shrink: 0;
}

.field-input-wrap {
	flex: 1;
	min-width: 0;
}

/* 用户名区域 */
.username-section {
	margin-top: 8rpx;
}

.field-label-row {
	display: flex;
	align-items: center;
	gap: 10rpx;
	margin-bottom: 6rpx;
}

.field-label {
	font-size: 28rpx;
	font-weight: 600;
	color: #333;
	letter-spacing: 0.01em;
}

.field-edit-icon {
	width: 28rpx;
	height: 28rpx;
	opacity: 0.6;
}

.field-hint {
	display: block;
	font-size: 24rpx;
	color: #8A8A8A;
	margin-top: 4rpx;
	font-weight: 400;
}

.field-hint-inline {
	margin-top: 6rpx;
}

.field-input {
	width: 100%;
	height: 84rpx;
	padding: 0 28rpx;
	font-size: 28rpx;
	font-weight: 400;
	color: #1D1D1F;
	border: 2rpx solid rgba(0, 0, 0, 0.1);
	border-radius: 18rpx;
	box-sizing: border-box;
	background: #FAFAFA;
	box-shadow: inset 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
	transition: border-color 0.22s ease, box-shadow 0.22s ease, background 0.2s ease;
}

.field-input:focus {
	outline: none;
	border-color: #9D8B70;
	background: #fff;
	box-shadow: inset 0 2rpx 8rpx rgba(0, 0, 0, 0.04), 0 0 0 4rpx rgba(157, 139, 112, 0.22);
}

.field-error {
	display: block;
	font-size: 24rpx;
	font-weight: 500;
	color: #C24A4A;
	margin-bottom: 12rpx;
	margin-left: 228rpx;
}

.field-error-inline {
	margin-left: 228rpx;
	margin-bottom: 12rpx;
}

/* 密码强度 */
.password-strength {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-bottom: 20rpx;
	margin-left: 228rpx;
}

.strength-bar {
	height: 8rpx;
	border-radius: 4rpx;
	width: 120rpx;
	transition: width 0.25s ease, background 0.25s ease;
}

.strength-bar.strength-weak {
	width: 40rpx;
	background: #E57373;
}

.strength-bar.strength-medium {
	width: 80rpx;
	background: #FFB74D;
}

.strength-bar.strength-strong {
	width: 120rpx;
	background: #81C784;
}

.strength-text {
	font-size: 24rpx;
	color: #6B6B6B;
	font-weight: 400;
}

.btn-save-username.btn-disabled {
	opacity: 0.6;
	cursor: not-allowed;
	background: #E5E0D8 !important;
	border-color: rgba(0,0,0,0.08) !important;
}

.btn-save-username.btn-active:hover {
	background: #DDD6CA !important;
}

/* 主要按钮（Change password）：深色 + 悬浮/按下动效 */
.btn-primary {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	padding: 14rpx 28rpx;
	font-size: 24rpx;
	font-weight: 600;
	font-family: inherit;
	border-radius: 18rpx;
	margin-top: 24rpx;
	cursor: pointer;
	border: 2rpx solid transparent;
	transition: transform 0.15s ease, box-shadow 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.btn-change-password.btn-active {
	background: linear-gradient(180deg, #A89078 0%, #8B7355 100%);
	color: #fff;
	box-shadow: 0 8rpx 24rpx rgba(139, 115, 85, 0.38);
}

.btn-change-password.btn-active:hover {
	background: linear-gradient(180deg, #9A826A 0%, #7D6848 100%);
	box-shadow: 0 10rpx 28rpx rgba(139, 115, 85, 0.45);
	transform: translateY(-2rpx);
}

.btn-change-password.btn-active:active {
	transform: scale(0.98) translateY(0);
	box-shadow: 0 4rpx 16rpx rgba(139, 115, 85, 0.35);
}

.btn-change-password.btn-disabled {
	background: #E0DCD6 !important;
	color: #9A9A9A !important;
	cursor: not-allowed;
	box-shadow: none;
	transform: none;
}

/* Close */
.settings-close {
	text-align: center;
	font-size: 30rpx;
	font-weight: 600;
	color: #8B7355;
	margin-top: 24rpx;
	padding: 24rpx 0;
	cursor: pointer;
	transition: color 0.2s ease, transform 0.15s ease;
	letter-spacing: 0.02em;
}

.settings-close:hover {
	color: #6B5A45;
}

.settings-close:active {
	transform: scale(0.98);
}
</style>
