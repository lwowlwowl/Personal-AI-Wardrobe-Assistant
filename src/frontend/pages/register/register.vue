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
			<view class="header">
				<text class="team-name">teammmm13</text>
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
				
				    <view class="tab" :class="{ active: activeTab === 'login' }" @click="setTab('login')">
				      <text class="tab-text" :class="{ 'active-text': activeTab === 'login' }">Login</text>
				    </view>
				
				    <view class="tab" :class="{ active: activeTab === 'register' }" @click="setTab('register')">
				      <text class="tab-text" :class="{ 'active-text': activeTab === 'register' }">Register</text>
				    </view>
				  </view>
				</view>
				
				<view class="quote-small">
					<text>Clothes mean nothing until someone lives in them.</text>
				</view>
				
				<!-- 表单 -->
				<view class="form" :class="{ 'fade-out': isLeaving, 'fade-in': isEntering }">
					<view class="form-item">
						<text class="label">Email Address</text>
						<view class="input-wrapper">
							<input 
								class="input" 
								v-model="formData.email" 
								placeholder="Enter your Email Address"
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
								v-model="formData.username" 
								placeholder="Enter your User name"
								placeholder-class="placeholder"
							/>
						</view>
					</view>
					
					<view class="form-item">
						<text class="label">Password</text>
						<view class="input-wrapper password-input-wrapper">
							<input 
								class="input" 
								v-model="formData.password" 
								:password="!showPassword"
								placeholder="Enter your Password"
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
								v-model="formData.confirmPassword" 
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
							<text class="error-message" v-show="passwordMismatch">密碼不一致，請重新輸入</text>
						</view>
					</view>
					
					<button class="register-btn" @click="handleRegister">Register</button>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'

const formData = ref({
	email: '',
	username: '',
	password: '',
	confirmPassword: ''
})

const showPassword = ref(false)
const showConfirmPassword = ref(false)
const imageError = ref(false)
const passwordMismatch = ref(false)

const handleImageError = () => {
	imageError.value = true
}

const togglePassword = () => {
	showPassword.value = !showPassword.value
}

const toggleConfirmPassword = () => {
	showConfirmPassword.value = !showConfirmPassword.value
}

const checkPasswordMatch = () => {
	if (formData.value.confirmPassword && formData.value.password && formData.value.password !== formData.value.confirmPassword) {
		passwordMismatch.value = true
	} else {
		passwordMismatch.value = false
	}
}

const onPasswordBlur = () => {
	// 当密码输入框失去焦点时，如果确认密码已有值，则检测是否一致
	if (formData.value.confirmPassword) {
		checkPasswordMatch()
	}
}

const validateEmail = (email) => {
	const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
	return re.test(email)
}

const handleRegister = () => {
	if (!formData.value.email) {
		uni.showToast({
			title: '請輸入郵箱地址',
			icon: 'none'
		})
		return
	}
	
	if (!validateEmail(formData.value.email)) {
		uni.showToast({
			title: '請輸入有效的郵箱地址',
			icon: 'none'
		})
		return
	}
	
	if (!formData.value.username) {
		uni.showToast({
			title: '請輸入用戶名',
			icon: 'none'
		})
		return
	}
	
	if (!formData.value.password) {
		uni.showToast({
			title: '請輸入密碼',
			icon: 'none'
		})
		return
	}
	
	if (formData.value.password.length < 6) {
		uni.showToast({
			title: '密碼長度至少6位',
			icon: 'none'
		})
		return
	}
	
	if (!formData.value.confirmPassword) {
		uni.showToast({
			title: '請確認密碼',
			icon: 'none'
		})
		return
	}
	
	if (formData.value.password !== formData.value.confirmPassword) {
		uni.showToast({
			title: '兩次輸入的密碼不一致',
			icon: 'none'
		})
		passwordMismatch.value = true
		return
	}
	
	// TODO: 實現註冊邏輯
	console.log('註冊', formData.value)
	uni.showToast({
		title: '註冊成功',
		icon: 'success',
		duration: 2000
	})
	
	// 註冊成功後跳轉到登錄頁
	setTimeout(() => {
		uni.redirectTo({
			url: '/pages/login/login'
		})
	}, 2000)
}

const activeTab = ref('register')
const isLeaving = ref(false)
const isEntering = ref(false)

onMounted(() => {
  // 页面加载时添加淡入动画
  isEntering.value = true
  setTimeout(() => {
    isEntering.value = false
  }, 250)
})

const goToLogin = () => {
  uni.navigateTo({
    url: '/pages/login/login',
    complete() {
      // ✅ 关键：跳走后立刻把 register 页的状态还原
      // 因为 navigateTo 不会销毁 register 页，回来的时候会保留 old state
      activeTab.value = 'register'
      isLeaving.value = false
    }
  })
}

const setTab = async (tab) => {
  if (tab === activeTab.value) return

  // 点 register：直接切回
  if (tab === 'register') {
    activeTab.value = 'register'
    return
  }

  // 点 login：先让滑块动画到左边，同时表单淡出
  activeTab.value = 'login'
  isLeaving.value = true
  await nextTick()

  // 等动画完成再跳转
  setTimeout(() => {
    goToLogin()
  }, 260) // 跟你的 transition 240ms 接近即可
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
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background-color: rgba(155, 139, 111, 0.5);
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
	font-size: 60rpx;
	font-weight: 600;
	color: #FFFFFF;
	line-height: 1.3;
	margin-bottom: 20rpx;
	text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.3);
}

.quote-author {
	display: block;
	font-size: 38rpx;
	color: #FFFFFF;
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
	top: 40rpx;
	right: 80rpx;
	text-align: right;
	z-index: 100;
}

.team-name {
	font-size: 28rpx;
	color: #333;
	font-weight: 500;
}

.form-container {
	display: flex;
	flex-direction: column;
	width: 100%;
	padding-top: 200rpx;
}

.welcome-text {
	text-align: center;
	margin-bottom: 40rpx;
	height: 260rpx;
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
	background-color: #F8EDDD;
	border-radius: 50rpx;
	padding: 8rpx;
	margin: 0 auto 40rpx auto;
	display: block;
	width: 60%;
	height: 98rpx;
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
  border-radius: 50rpx;
}


.tab {
  flex: 1;
  height: 82rpx;              /* 98rpx(tab-wrapper) - 16rpx(padding上下) */
  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: 40rpx;
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
  border-radius: 40rpx;
  background-color: #9B8B6F;
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

.tab-text {
	font-size: 28rpx;
	color: #9E896A;
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
	margin-top: 35rpx;
	display: flex;
	flex-direction: column;
	transition: all 0.25s ease;
}

.form.fade-in {
	animation: fadeInUp 0.25s ease;
}

.form.fade-out {
	opacity: 0;
	transform: translateY(-12rpx);
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

.form-item {
	margin: 0 auto 40rpx auto;
	width: 80%;
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
	transition: box-shadow 0.2s ease, transform 0.2s ease;
}

.input-wrapper:focus-within {
	box-shadow: 0 12rpx 40rpx rgba(155, 139, 111, 0.15);
	transform: translateY(-11rpx);
}

.input {
	width: 100%;
	height: 90rpx;
	background-color: #FFFFFF;
	border-radius: 45rpx;
	padding: 0 40rpx;
	font-size: 28rpx;
	border: 2rpx solid transparent;
	transition: all 0.2s ease;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.input:focus {
	border-color: #7A6A4F;
	outline: none;
}

.input-error {
	border-color: #E74C3C !important;
	box-shadow: 0 2rpx 8rpx rgba(231, 76, 60, 0.2) !important;
}

.input-wrapper.error .input {
	border-color: #E74C3C;
	box-shadow: 0 2rpx 8rpx rgba(231, 76, 60, 0.2);
}

.error-message-container {
	min-height: 50rpx;
	margin-top: 15rpx;
}

.error-message {
	display: block;
	color: #E74C3C;
	font-size: 24rpx;
	margin-left: 40rpx;
	animation: shake 0.3s ease;
}

@keyframes shake {
	0%, 100% { transform: translateX(0); }
	25% { transform: translateX(-8rpx); }
	75% { transform: translateX(8rpx); }
}

.input:focus::placeholder {
	transform: translateX(4rpx);
}

.placeholder {
	color: #CCCCCC;
	transition: transform 0.2s ease;
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

.eye-image {
	width: 100%;
	height: 100%;
	user-select: none;
}

.register-btn {
	width: 20%;
	height: 86rpx;
	background-color: #9B8B6F;
	color: #FFFFFF;
	border-radius: 45rpx;
	font-size: 32rpx;
	font-weight: 500;
	border: none;
	margin-top: 40rpx;
	cursor: pointer;
	transition: all 0.3s;
}

.register-btn:hover {
	background-color: #8A7A5F;
}

.register-btn:active {
	transform: scale(0.95);
}

.register-btn::after {
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
}
</style>
