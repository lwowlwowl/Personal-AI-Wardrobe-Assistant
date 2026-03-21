<template>
	<view class="container">
		<!-- 左侧背景区域 -->
		<view class="left-section">
			<image class="background-image" src="/static/wardrobe-bg.png" mode="aspectFill" @error="handleImageError"></image>
			<view class="background-placeholder" v-if="imageError"></view>
			<view class="overlay-mask"></view>
			<view class="quote-overlay">
				<text class="quote-text">Style is a way to say who you are.</text>
				<text class="quote-author">—— Rachel Zoe</text>
			</view>
		</view>
		
		<!-- 右侧表单区域 -->
		<view class="right-section">
			<view class="header user-header">
				<view class="user-chip">
					<view class="user-avatar-circle"></view>
					<text class="user-name-text">teammmm13</text>
				</view>
			</view>
			
			<view class="form-container">
				<view class="welcome-text">
					<text class="welcome-title">Welcome to</text>
					<text class="welcome-subtitle">Personal AI Wardrobe Assistant!</text>
				</view>
				
				<!-- 切换标签 -->
				<view class="tab-wrapper">
				  <view class="tab-container">
					<!-- 新增：滑块背景 -->
					<view class="tab-slider" :class="{ right: activeTab === 'register' }"></view>
			
					<view 
						class="tab" 
						:class="{ active: activeTab === 'login' }" 
						@click="setTab('login')"
					>
						<text class="tab-text" :class="{ 'active-text': activeTab === 'login' }">Login</text>
					</view>
			
					<view 
						class="tab" 
						:class="{ active: activeTab === 'register' }" 
						@click="setTab('register')"
					>
						<text class="tab-text" :class="{ 'active-text': activeTab === 'register' }">Register</text>
					</view>
				  </view>
				</view>

				
				<view class="quote-small">
					<text>Clothes mean nothing until someone lives in them.</text>
				</view>
				
				<!-- 表单：根据 activeTab 切换登录 / 注册 -->
				<view 
					class="form" 
					:class="[
						isEntering ? 'fade-in' : '',
						isSwitching ? 'form-switch' : ''
					]"
				>
					<!-- Login 表单（登录） -->
					<view v-if="activeTab === 'login'">
						<view class="form-item form-item-login-first">
							<text class="label">User name</text>
							<view class="input-wrapper">
								<input 
									class="input" 
									v-model="loginForm.username" 
									placeholder="Username"
									placeholder-class="placeholder"
								/>
							</view>
						</view>
						
						<view class="form-item form-item-login">
							<text class="label">Password</text>
							<view class="input-wrapper password-input-wrapper">
								<input 
									class="input" 
									v-model="loginForm.password" 
									:password="!showPassword"
									placeholder="Password"
									placeholder-class="placeholder"
								/>
								<view class="eye-icon" @click="togglePassword">
									<image class="eye-image" :src="showPassword ? '/static/eye-open.png' : '/static/eye-close.png'" mode="aspectFit"></image>
								</view>
							</view>
						</view>
						
						<view class="form-options">
							<view class="remember-me" @click="toggleRemember">
								<view :class="['checkbox', loginForm.remember ? 'checked' : '']"></view>
								<text class="remember-text">Remember me</text>
							</view>
							<text class="forgot-password" @click="handleForgotPassword">Forgot Password ?</text>
						</view>
						
						<button class="login-btn" @click="handleLogin">Login</button>
					</view>

					<!-- Register 表单（注册） -->
					<view v-else>
						<view class="form-item">
							<text class="label">Email Address</text>
							<view class="input-wrapper">
								<input 
									class="input" 
									v-model="registerForm.email" 
									placeholder="Email address"
									placeholder-class="placeholder"
									type="email"
								/>
							</view>
						</view>
						
						<view class="form-item">
							<text class="label">User name</text>
							<view class="input-wrapper">
								<input 
									class="input" 
									v-model="registerForm.username" 
									placeholder="Username"
									placeholder-class="placeholder"
								/>
							</view>
						</view>
						
						<view class="form-item">
							<text class="label">Password</text>
							<view class="input-wrapper password-input-wrapper">
								<input 
									class="input" 
									v-model="registerForm.password" 
									:password="!showPassword"
									placeholder="Password"
									placeholder-class="placeholder"
									@blur="onPasswordBlur"
								/>
								<view class="eye-icon" @click="togglePassword">
									<image class="eye-image" :src="showPassword ? '/static/eye-open.png' : '/static/eye-close.png'" mode="aspectFit"></image>
								</view>
							</view>
						</view>
						
						<view class="form-item">
							<text class="label">Confirm Password</text>
							<view class="input-wrapper password-input-wrapper" :class="{ 'error': passwordMismatch }">
								<input 
									class="input" 
									:class="{ 'input-error': passwordMismatch }"
									v-model="registerForm.confirmPassword" 
									:password="!showConfirmPassword"
									placeholder="Confirm your Password"
									placeholder-class="placeholder"
									@blur="checkPasswordMatch"
								/>
								<view class="eye-icon" @click="toggleConfirmPassword">
									<image class="eye-image" :src="showConfirmPassword ? '/static/eye-open.png' : '/static/eye-close.png'" mode="aspectFit"></image>
								</view>
							</view>
							<view class="error-message-container">
								<text class="error-message" v-show="passwordMismatch">Passwords do not match, please re-enter</text>
							</view>
						</view>
						
						<button class="login-btn" @click="handleRegister">Register</button>
					</view>
				</view>
				
			</view>
		</view>

		<ForgotPasswordModal :visible="showForgotModal" @close="showForgotModal = false" />
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { loginAuth, registerAuth } from '@/api/userApi.js'
import ForgotPasswordModal from './ForgotPasswordModal.vue'

const activeTab = ref('login')
const isEntering = ref(false)
const isSwitching = ref(false)
const showForgotModal = ref(false)

// Login 表单数据
const loginForm = ref({
	username: '',
	password: '',
	remember: false
})

// Register 表单数据
const registerForm = ref({
	email: '',
	username: '',
	password: '',
	confirmPassword: ''
})

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const imageError = ref(false)
const passwordMismatch = ref(false)
const isLoading = ref(false)

const handleImageError = () => {
	imageError.value = true
}

const togglePassword = () => {
	showPassword.value = !showPassword.value
}

const toggleConfirmPassword = () => {
	showConfirmPassword.value = !showConfirmPassword.value
}

const toggleRemember = () => {
	loginForm.value.remember = !loginForm.value.remember
}

const goToHomeAfterLogin = () => {
	setTimeout(() => {
		uni.reLaunch({
			url: '/pages/index/index',
			fail: () => {
				uni.navigateTo({ url: '/pages/index/index' })
			}
		})
	}, 1500)
}

// 登录
const handleLogin = async () => {
	if (!loginForm.value.username) {
		uni.showToast({
			title: 'Please enter your username',
			icon: 'none'
		})
		return
	}
	if (!loginForm.value.password) {
		uni.showToast({
			title: 'Please enter your password',
			icon: 'none'
		})
		return
	}

	uni.showLoading({
		title: 'Logging in...',
		mask: true
	})

	try {
		const res = await loginAuth({
			username: loginForm.value.username,
			password: loginForm.value.password,
			remember: loginForm.value.remember
		})
		uni.hideLoading()

		const { statusCode, data } = res

		if (statusCode === 200 && data && data.success === true) {
			uni.showToast({
				title: 'Login successful',
				icon: 'success',
				duration: 1500
			})

			uni.setStorageSync('auth_token', data.access_token)
			uni.setStorageSync('user_info', {
				user_id: data.user_id,
				username: data.username,
				email: data.email
			})

			if (loginForm.value.remember) {
				uni.setStorageSync('remember_me', true)
			}

			goToHomeAfterLogin()
		} else if (statusCode === 200 && data && data.success === false) {
			uni.showToast({
				title: data.message || 'Login failed',
				icon: 'none',
				duration: 3000
			})
		} else if (statusCode === 401) {
			uni.showToast({
				title: (data && (data.detail || data.message)) || 'Incorrect username or password',
				icon: 'none',
				duration: 3000
			})
		} else {
			uni.showToast({
				title: `Server error: ${statusCode}`,
				icon: 'none',
				duration: 3000
			})
		}
	} catch (err) {
		uni.hideLoading()
		uni.showToast({
			title: 'Network error. Please check if backend service is running',
			icon: 'none',
			duration: 3000
		})
	}
}

const handleForgotPassword = () => {
	showForgotModal.value = true
}

// 注册相关校验
const validateEmail = (email) => {
	const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
	return re.test(email)
}

const checkPasswordMatch = () => {
	if (registerForm.value.confirmPassword && registerForm.value.password && registerForm.value.password !== registerForm.value.confirmPassword) {
		passwordMismatch.value = true
	} else {
		passwordMismatch.value = false
	}
}

const onPasswordBlur = () => {
	if (registerForm.value.confirmPassword) {
		checkPasswordMatch()
	}
}

// 注册
const handleRegister = async () => {
	if (!registerForm.value.email) {
		uni.showToast({
			title: 'Please enter your email address',
			icon: 'none'
		})
		return
	}
	
	if (!validateEmail(registerForm.value.email)) {
		uni.showToast({
			title: 'Please enter a valid email address',
			icon: 'none'
		})
		return
	}
	
	if (!registerForm.value.username) {
		uni.showToast({
			title: 'Please enter your username',
			icon: 'none'
		})
		return
	}
	
	if (!registerForm.value.password) {
		uni.showToast({
			title: 'Please enter your password',
			icon: 'none'
		})
		return
	}
	
	if (registerForm.value.password.length < 6) {
		uni.showToast({
			title: 'Password must be at least 6 characters',
			icon: 'none'
		})
		return
	}
	
	if (!registerForm.value.confirmPassword) {
		uni.showToast({
			title: 'Please confirm your password',
			icon: 'none'
		})
		return
	}
	
	if (registerForm.value.password !== registerForm.value.confirmPassword) {
		uni.showToast({
			title: 'The two passwords do not match',
			icon: 'none'
		})
		passwordMismatch.value = true
		return
	}
	
	if (isLoading.value) return
	isLoading.value = true
	
	try {
		uni.showLoading({
			title: 'Registering...',
			mask: true
		})

		const res = await registerAuth({
			username: registerForm.value.username,
			email: registerForm.value.email,
			password: registerForm.value.password,
			confirm_password: registerForm.value.confirmPassword
		})

		uni.hideLoading()
		isLoading.value = false

		if (res.statusCode === 200) {
			if (res.data && res.data.success === true) {
				uni.showToast({
					title: 'Registration successful! Please log in',
					icon: 'success',
					duration: 2000
				})
				
				// 注册成功后自动切换到 Login tab，并带上用户名
				loginForm.value.username = registerForm.value.username
				activeTab.value = 'login'
			} else {
				const errorMessage = res.data?.message || 'Registration failed'
				uni.showToast({
					title: errorMessage,
					icon: 'none',
					duration: 3000
				})
			}
		} else if (res.statusCode === 400 || res.statusCode === 409) {
			const errorDetail = res.data?.message || res.data?.detail || ''
			let errorMessage = 'Registration failed'
			
			if (errorDetail.toLowerCase().includes('username')) {
				errorMessage = 'Username is already registered. Please use another one'
			} else if (errorDetail.toLowerCase().includes('email')) {
				errorMessage = 'Email is already registered. Please use another email'
			} else {
				errorMessage = errorDetail || 'Registration failed. Please check your input'
			}
			
			uni.showToast({
				title: errorMessage,
				icon: 'none',
				duration: 3000
			})
		} else if (res.statusCode === 500) {
			const errorDetail = res.data?.message || ''
			let errorMessage = 'Server error. Please try again later'
			
			if (errorDetail.includes('create_user')) {
				errorMessage = 'Server configuration error. Please contact the administrator'
			}
			
			uni.showToast({
				title: errorMessage,
				icon: 'none',
				duration: 3000
			})
		} else {
			const errorDetail = res.data?.message || res.data?.detail || ''
			uni.showToast({
				title: `Registration failed: ${errorDetail || res.statusCode}`,
				icon: 'none',
				duration: 3000
			})
		}
	} catch (error) {
		uni.hideLoading()
		isLoading.value = false

		let errorMessage = 'Registration failed. Please try again later'
		
		if (error.errMsg) {
			if (error.errMsg.includes('timeout')) {
				errorMessage = 'Request timed out. Please check your network connection'
			} else if (error.errMsg.includes('fail')) {
				errorMessage = 'Network request failed. Please check if backend service is running'
			}
		}
		
		uni.showToast({
			title: errorMessage,
			icon: 'none',
			duration: 3000
		})
	}
}

onMounted(() => {
  // 页面加载时添加淡入动画
  isEntering.value = true
  setTimeout(() => {
    isEntering.value = false
  }, 250)
})

const setTab = (tab) => {
  if (tab === activeTab.value) return

  isSwitching.value = true
  activeTab.value = tab

  // 在动画结束后重置 switching 标记，避免持续触发
  setTimeout(() => {
    isSwitching.value = false
  }, 260)
}

</script>



<style scoped>
.container {
	display: flex;
	width: 100vw;
	height: 100vh;
	background-color: #F3EDE3;
}

/* 左侧区域 */
.left-section {
	flex: 1;
	position: relative;
	overflow: hidden;
	margin: 110rpx 40rpx 100rpx 170rpx;
	border-radius: 30rpx;
}

.background-image {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.background-placeholder {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background: linear-gradient(135deg, #9B8B6F 0%, #7A6A4F 100%);
	z-index: 0;
}

.overlay-mask {
	position: absolute;
	inset: 0;
	border-radius: 30rpx;
	background: linear-gradient(
		180deg,
		rgba(0, 0, 0, 0) 10%,
		rgba(0, 0, 0, 0.7) 80%
	);
	z-index: 1;
}

.quote-overlay {
	position: absolute;
	bottom: 80rpx;
	left: 60rpx;
	right: 60rpx;
	z-index: 2;
}

.quote-text {
	display: block;
	font-size: 44rpx;          /* 约 22px */
	font-weight: 500;
	letter-spacing: 0.6rpx;
	color: #FFFFFF;
	line-height: 1.3;
	margin-bottom: 20rpx;
	text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.3);
}

.quote-author {
	display: block;
	font-size: 28rpx;          /* 约 14px */
	color: rgba(255, 255, 255, 0.8);
	text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.3);
}

/* 右侧区域 */
.right-section {
	flex: 1;
	display: flex;
	flex-direction: column;
	justify-content: flex-start;
	padding: 0 80rpx;
	position: relative;
}

.header {
	position: fixed;
	top: 36rpx;
	right: 60rpx;
	z-index: 100;
}

.user-header {
	display: flex;
	align-items: center;
	justify-content: flex-end;
}

.user-chip {
	display: flex;
	align-items: center;
	padding: 8rpx 16rpx;
	border-radius: 999rpx;
	background-color: rgba(248, 250, 252, 0.9);
	box-shadow: 0 6rpx 18rpx rgba(15, 23, 42, 0.08);
}

.user-avatar-circle {
	width: 32rpx;
	height: 32rpx;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #7C6A4E, #A48F6A);
	margin-right: 12rpx;
}

.user-name-text {
	font-size: 24rpx;
	color: #555;
	font-weight: 500;
}

.form-container {
	display: flex;
	flex-direction: column;
	width: 100%;
	padding-top: 160rpx;  /* 整体往上提 */
	animation: loginCardFadeIn 0.6s ease;
}

.welcome-text {
	text-align: center;
	margin-bottom: 30rpx;
	height: 220rpx;       /* 标题区略收窄，视觉更上移 */
	display: flex;
	flex-direction: column;
	justify-content: center;
}

.welcome-title {
	display: block;
	font-size: 48rpx;
	color: #666;
	margin-bottom: 10rpx;
	font-family: 'Georgia', 'Times New Roman', serif;
	font-style: italic;
	letter-spacing: 1rpx;
}

.welcome-subtitle {
	display: block;
	font-size: 60rpx;
	font-weight: 700;
	color: #333;
	font-family: 'Georgia', 'Times New Roman', serif;
	letter-spacing: 2rpx;
}

/* 切换标签 */
.tab-wrapper {
	background-color: #EEE8DE;   /* 外层柔和底色 */
	padding: 4rpx;
	border-radius: 28rpx;
	margin: 0 auto 40rpx auto;
	display: block;
	width: 70%;
	height: 96rpx;
	box-sizing: border-box;
}

.tab-container {
  display: flex;
  gap: 0;
  margin-bottom: 0;
  justify-content: center;
  position: relative;

  height: 100%;
  overflow: hidden;
  border-radius: 24rpx;
  padding: 0;
  background-color: transparent;
}


.tab {
  flex: 1;
  height: 88rpx;              /* 96rpx(tab-wrapper) - padding上下 */
  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: 24rpx;
  background-color: transparent;
  cursor: pointer;
  transition: color 0.3s;
  position: relative;
  z-index: 1;
  padding: 0;                 /* 去掉原来的 20rpx 60rpx */
}

.tab-slider {
  position: absolute;
  left: 0;
  top: 0;
  width: 50%;
  height: 100%;
  border-radius: 24rpx;
  background-color: #9E8B6D;
  z-index: 0;

  transform: translateX(0);
  transition: transform 240ms ease;
}

.tab-slider.right {
  transform: translateX(100%);
}


.tab.active {
	z-index: 2;
}

.tab:hover .tab-text {
	transform: translateY(-2rpx);
}

.tab-text {
	font-size: 28rpx;
	color: #7C6A4E;
	transition: all 0.3s;
}

.active-text {
	color: #FFFFFF;
	font-weight: 700;
}

.quote-small {
	text-align: center;
	margin-bottom: 50rpx;
	height: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.quote-small text {
	font-size: 24rpx;
	color: #666;
}

/* 表单 */
.form {
	margin-top: 40rpx;
	display: flex;
	flex-direction: column;
	transition: all 0.25s ease;
}

.form.fade-in {
	animation: fadeInUp 0.25s ease;
}

@keyframes fadeInUp {
	from {
		opacity: 0;
		transform: translateY(16rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

/* Tab 切换时的内容滑动动画 */
.form-switch {
	animation: formSlideDown 0.26s ease-out;
}

@keyframes formSlideDown {
	from {
		opacity: 0;
		transform: translateY(10rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

/* 整体表单淡入动画，提升产品感 */
@keyframes loginCardFadeIn {
	from {
		opacity: 0;
		transform: translateY(10rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.form-item {
	margin: 0 auto 55rpx auto;   /* Register 等通用栏位：间距较小 */
	width: 80%;
	position: relative;  /* 让错误提示可以绝对定位而不影响布局 */
}

/* Login 表单：首个栏位与栏位之间间距更大 */
.form-item-login-first {
	margin-top: 80rpx;
	margin-bottom: 100rpx;
}

.form-item-login {
	margin-bottom: 70rpx;
}

.label {
	display: block;
	font-size: 30rpx;
	font-weight: bold;
	color: #333;
	margin-bottom: 30rpx;
}

.input-wrapper {
	position: relative;
	transition: transform 0.2s ease;
}

.input {
	width: 100%;
	height: 104rpx;                 /* 约 52px */
	background-color: #F5F5F5;
	border-radius: 28rpx;           /* 约 14px */
	padding: 0 36rpx;               /* 约 18px */
	font-size: 28rpx;
	border: none;
	transition: all 0.2s ease;
	box-shadow: none;
}

.input:hover {
	background-color: #ECECEC;
	box-shadow: 0 0 0 4rpx rgba(0, 0, 0, 0.03);  /* ≈ 2px */
}

.input:focus {
	background-color: #FFFFFF;
	outline: none;
	box-shadow: 0 0 0 6rpx rgba(158, 139, 109, 0.18); /* 3px 等效阴影，略更明显 */
}

.input:focus::placeholder {
	transform: translateX(4rpx);
}

.placeholder {
	color: #CCCCCC;
	transition: transform 0.2s ease;
}

.error-message-container {
	position: absolute;
	left: 0;
	top: 100%;          /* 固定在输入框下方，但不占据文档流高度 */
}

.error-message {
	display: block;
	color: #E74C3C;      /* 红色文字 */
	font-size: 24rpx;
	margin-left: 40rpx;
}

.password-input-wrapper {
	position: relative;
}

.eye-icon {
	position: absolute;
	right: 40rpx;
	top: 50%;
	transform: translateY(-50%);
	width: 40rpx;
	height: 40rpx;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
}

.eye-icon:hover {
	opacity: 0.7;
}

.eye-image {
	width: 100%;
	height: 100%;
	user-select: none;
}

.form-options {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin: 0 auto 50rpx auto;
	width: 80%;
}

.remember-me {
	display: flex;
	align-items: center;
	cursor: pointer;
}

.checkbox {
	width: 36rpx;
	height: 36rpx;
	border: 2rpx solid #999;
	border-radius: 8rpx;
	margin-right: 15rpx;
	transition: all 0.3s;
}

.checkbox.checked {
	background-color: #9B8B6F;
	border-color: #9B8B6F;
	position: relative;
}

.checkbox.checked::after {
	content: '✓';
	position: absolute;
	color: #FFFFFF;
	font-size: 24rpx;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
}

.remember-text {
	font-size: 26rpx;
	color: #666;
}

.forgot-password {
	font-size: 26rpx;
	color: #666;
	cursor: pointer;
}

.login-btn {
	width: 40%;
	max-width: 360rpx;
	height: 104rpx;                /* 约 52px */
	background-color: #9E8B6D;
	color: #FFFFFF;
	border-radius: 28rpx;          /* 约 14px */
	font-size: 32rpx;
	font-weight: 600;
	border: none;
	margin-top: 100rpx;
	cursor: pointer;
	letter-spacing: 0.4rpx;
	box-shadow: 0 12rpx 28rpx rgba(158, 139, 109, 0.25);
	transition: all 0.2s;
	display: flex;
	align-items: center;           /* 垂直居中文字 */
	justify-content: center;       /* 水平居中 */
}

.login-btn:hover {
	transform: translateY(-2rpx);
	box-shadow: 0 20rpx 40rpx rgba(158, 139, 109, 0.30);
}

.login-btn:active {
	transform: translateY(0);
}

.login-btn::after {
	border: none;
}

/* 响应式降级：窄屏隐藏左侧大图，表单居中（Web + 小程序更友好） */
@media (max-width: 900px) {
	.container {
		height: auto;
		min-height: 100vh;
	}
	.left-section {
		display: none;
	}
	.right-section {
		padding: 0 40rpx;
	}
	.header {
		right: 40rpx;
	}
	.tab-wrapper {
		width: 90%;
	}
	.form-item {
		width: 100%;
	}
	.form-options {
		width: 100%;
	}
}
</style>
