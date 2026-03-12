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
				
				<!-- 表单：根據 activeTab 切換登入 / 註冊 -->
				<view class="form" :class="{ 'fade-out': isLeaving, 'fade-in': isEntering }">
					<!-- Login 表单 -->
					<view v-if="activeTab === 'login'">
						<view class="form-item">
							<text class="label">User name</text>
							<view class="input-wrapper">
								<input 
									class="input" 
									v-model="loginForm.username" 
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
									v-model="loginForm.password" 
									:password="!showPassword"
									placeholder="Enter your Password"
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

					<!-- Register 表单 -->
					<view v-else>
						<view class="form-item">
							<text class="label">Email Address</text>
							<view class="input-wrapper">
								<input 
									class="input" 
									v-model="registerForm.email" 
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
									v-model="registerForm.username" 
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
									v-model="registerForm.password" 
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
	</view>
</template>

<script setup>
import { ref, onMounted } from 'vue'   

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

// 登录
const handleLogin = () => {
	if (!loginForm.value.username) {
		uni.showToast({
			title: '請輸入用戶名',
			icon: 'none'
		})
		return
	}
	if (!loginForm.value.password) {
		uni.showToast({
			title: '請輸入密碼',
			icon: 'none'
		})
		return
	}
	
	uni.showLoading({
	        title: '登录中...',
	        mask: true
	    })
		
	uni.request({
	        url: 'http://localhost:8000/api/auth/login',
	        method: 'POST',
	        header: {
	            'Content-Type': 'application/json',
				'Accept': 'application/json'
	        },
	        data: {
	            username: loginForm.value.username,
	            password: loginForm.value.password,
	            remember: loginForm.value.remember
	        },
	        success: (res) => {
	            uni.hideLoading()
	            
	            if (res.statusCode === 200) {
	                if (res.data && res.data.success === true) {
						console.log('登录成功，获取到token')
	                    uni.showToast({
	                        title: '登录成功',
	                        icon: 'success',
	                        duration: 1500
	                    })
	                    
	                    // 存储认证信息
	                    uni.setStorageSync('auth_token', res.data.access_token)
	                    uni.setStorageSync('user_info', {
	                        user_id: res.data.user_id,
	                        username: res.data.username,
	                        email: res.data.email
	                    })
	                    
	                    // 记住我选项
	                    if (loginForm.value.remember) {
	                        uni.setStorageSync('remember_me', true)
	                    }
	                    
	                    // 跳转到主页
	                    setTimeout(() => {
	                                    console.log('准备跳转到首页...')
	                                    
	                                    // 先尝试 reLaunch 重启应用到首页
	                                    uni.reLaunch({
	                                        url: '/pages/index/index',
	                                        success: () => {
	                                            console.log('跳转首页成功')
	                                        },
	                                        fail: (err) => {
	                                            console.error('跳转首页失败:', err)
	                                            
	                                            // 如果 reLaunch 失败，尝试 switchTab
	                                            uni.switchTab({
	                                                url: '/pages/index/index',
	                                                fail: (err2) => {
	                                                    console.error('switchTab 也失败:', err2)
	                                                    // 最后尝试 navigateTo
	                                                    uni.navigateTo({
	                                                        url: '/pages/index/index'
	                                                    })
	                                                }
	                                            })
	                                        }
	                                    })
	                                }, 1500)
	                    
	                } else {
						console.log('登录失败:', res.data.message)
	                    uni.showToast({
	                        title: res.data.message || '登录失败',
	                        icon: 'none',
	                        duration: 3000
	                    })
	                }
	            } else if (res.statusCode === 401) {
	                uni.showToast({
	                    title: res.data.detail || '用户名或密码错误',
	                    icon: 'none',
	                    duration: 3000
	                })
	            } else {
	                uni.showToast({
	                    title: `服务器错误: ${res.statusCode}`,
	                    icon: 'none',
	                    duration: 3000
	                })
	            }
	        },
	        fail: (err) => {
	            uni.hideLoading()
	            console.error('登录请求失败:', err)
	            uni.showToast({
	                title: '网络错误，请检查后端服务是否启动',
	                icon: 'none',
	                duration: 3000
	            })
	        }
	    })
	
}

const handleForgotPassword = () => {
	uni.showToast({
		title: '忘記密碼功能開發中',
		icon: 'none'
	})
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

// 註冊
const handleRegister = async () => {
	if (!registerForm.value.email) {
		uni.showToast({
			title: '請輸入郵箱地址',
			icon: 'none'
		})
		return
	}
	
	if (!validateEmail(registerForm.value.email)) {
		uni.showToast({
			title: '請輸入有效的郵箱地址',
			icon: 'none'
		})
		return
	}
	
	if (!registerForm.value.username) {
		uni.showToast({
			title: '請輸入用戶名',
			icon: 'none'
		})
		return
	}
	
	if (!registerForm.value.password) {
		uni.showToast({
			title: '請輸入密碼',
			icon: 'none'
		})
		return
	}
	
	if (registerForm.value.password.length < 6) {
		uni.showToast({
			title: '密碼長度至少6位',
			icon: 'none'
		})
		return
	}
	
	if (!registerForm.value.confirmPassword) {
		uni.showToast({
			title: '請確認密碼',
			icon: 'none'
		})
		return
	}
	
	if (registerForm.value.password !== registerForm.value.confirmPassword) {
		uni.showToast({
			title: '兩次輸入的密碼不一致',
			icon: 'none'
		})
		passwordMismatch.value = true
		return
	}
	
	if (isLoading.value) return
	isLoading.value = true
	
	try {
		uni.showLoading({
			title: '註冊中...',
			mask: true
		})
		
		console.log('發送註冊請求:', {
			username: registerForm.value.username,
			email: registerForm.value.email,
			password: registerForm.value.password,
			confirm_password: registerForm.value.confirmPassword
		})
		
		const res = await uni.request({
			url: 'http://localhost:8000/api/auth/register',
			method: 'POST',
			header: {
				'Content-Type': 'application/json'
			},
			data: {
				username: registerForm.value.username,
				email: registerForm.value.email,
				password: registerForm.value.password,
				confirm_password: registerForm.value.confirmPassword
			},
			timeout: 10000
		})
		
		console.log('註冊API完整響應:', res)
		console.log('響應狀態碼:', res.statusCode)
		console.log('響應數據:', res.data)
		
		uni.hideLoading()
		isLoading.value = false
		
		if (res.statusCode === 200) {
			if (res.data && res.data.success === true) {
				uni.showToast({
					title: '註冊成功！請登入',
					icon: 'success',
					duration: 2000
				})
				
				// 註冊成功後自動切換到 Login tab，並帶上用戶名
				loginForm.value.username = registerForm.value.username
				activeTab.value = 'login'
			} else {
				const errorMessage = res.data?.message || '註冊失敗'
				uni.showToast({
					title: errorMessage,
					icon: 'none',
					duration: 3000
				})
			}
		} else if (res.statusCode === 400 || res.statusCode === 409) {
			const errorDetail = res.data?.message || res.data?.detail || ''
			let errorMessage = '註冊失敗'
			
			if (errorDetail.includes('用户名') || errorDetail.includes('username')) {
				errorMessage = '用戶名已被註冊，請換一個用戶名'
			} else if (errorDetail.includes('邮箱') || errorDetail.includes('email')) {
				errorMessage = '郵箱已被註冊，請使用其他郵箱'
			} else {
				errorMessage = errorDetail || '註冊失敗，請檢查輸入信息'
			}
			
			uni.showToast({
				title: errorMessage,
				icon: 'none',
				duration: 3000
			})
		} else if (res.statusCode === 500) {
			const errorDetail = res.data?.message || ''
			let errorMessage = '服務器錯誤，請稍後重試'
			
			if (errorDetail.includes('create_user')) {
				errorMessage = '服務器配置錯誤，請聯繫管理員'
			}
			
			uni.showToast({
				title: errorMessage,
				icon: 'none',
				duration: 3000
			})
		} else {
			const errorDetail = res.data?.message || res.data?.detail || ''
			uni.showToast({
				title: `註冊失敗: ${errorDetail || res.statusCode}`,
				icon: 'none',
				duration: 3000
			})
		}
	} catch (error) {
		uni.hideLoading()
		isLoading.value = false
		
		console.error('註冊請求異常:', error)
		
		let errorMessage = '註冊失敗，請稍後重試'
		
		if (error.errMsg) {
			if (error.errMsg.includes('timeout')) {
				errorMessage = '請求超時，請檢查網絡連接'
			} else if (error.errMsg.includes('fail')) {
				errorMessage = '網絡請求失敗，請檢查後端服務是否啟動'
			}
		}
		
		uni.showToast({
			title: errorMessage,
			icon: 'none',
			duration: 3000
		})
	}
}

const activeTab = ref('login')
const isLeaving = ref(false)
const isEntering = ref(false)

onMounted(() => {
  // 页面加载时添加淡入动画
  isEntering.value = true
  setTimeout(() => {
    isEntering.value = false
  }, 250)
})

const setTab = (tab) => {
  if (tab === activeTab.value) return
  activeTab.value = tab
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
	margin-top: 60rpx;
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
	margin: 0 auto 60rpx auto;
	width: 80%;
	position: relative;  /* 让错误提示可以绝对定位而不影响布局 */
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
	width: 20%;
	height: 85rpx;
	background-color: #9B8B6F;
	color: #FFFFFF;
	border-radius: 45rpx;
	font-size: 32rpx;
	font-weight: 500;
	border: none;
	margin-top: 80rpx;   /* 压缩按钮与上方表单的距离 */
	cursor: pointer;
	transition: all 0.3s;
}

.login-btn:hover {
	background-color: #8A7A5F;
}

.login-btn:active {
	transform: scale(0.95);
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
