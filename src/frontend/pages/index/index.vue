<template>
	<view class="container">
		<!-- 左侧边栏 -->
		<view class="sidebar">
			<!-- 顶部标题 -->
			<view class="sidebar-header">
				<view class="home-icon">
					<text class="icon-text">🏠</text>
				</view>
				<text class="app-title">Personal AI Wardrobe Assistant</text>
			</view>
			
			<!-- 导航菜单 -->
			<view class="nav-menu">
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'recommendation' }"
					@click="setActiveMenu('recommendation')"
				>
					<view class="nav-icon">
						<text class="icon-text">🤖</text>
					</view>
					<text class="nav-text">Recommendation AI</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'tryon' }"
					@click="setActiveMenu('tryon')"
				>
					<view class="nav-icon">
						<text class="icon-text">📷</text>
					</view>
					<text class="nav-text">Virtual Try-On</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'wardrobe' }"
					@click="setActiveMenu('wardrobe')"
				>
					<view class="nav-icon">
						<text class="icon-text">👕</text>
					</view>
					<text class="nav-text">My Wardrobe</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'analysis' }"
					@click="setActiveMenu('analysis')"
				>
					<view class="nav-icon">
						<text class="icon-text">📊</text>
					</view>
					<text class="nav-text">Wardrobe Analysis</text>
				</view>
			</view>
			
			<!-- 底部菜单 -->
			<view class="sidebar-footer">
				<view class="nav-item" @click="handleGuestUser">
					<view class="nav-icon">
						<text class="icon-text">👤</text>
					</view>
					<text class="nav-text">Guest User</text>
				</view>
				
				<view class="nav-item" @click="handleSetting">
					<view class="nav-icon">
						<text class="icon-text">⚙️</text>
					</view>
					<text class="nav-text">Setting</text>
				</view>
			</view>
		</view>
		
		<!-- 主内容区 -->
		<view class="main-content">
			<!-- 问候语 -->
			<view class="greeting-section">
				<view class="greeting-content">
					<view class="robot-icon">
						<text class="icon-text">🤖</text>
					</view>
					<text class="greeting-text">Hi! Good Afternoon</text>
					<text class="wave-emoji">👋</text>
				</view>
			</view>
			
			<!-- 天气/推荐信息 -->
			<view class="weather-section">
				<text class="weather-text">Today 21°C | Light Breeze | Ideal for a Light Jacket</text>
			</view>
			
			<!-- 搜索栏 -->
			<view class="search-section">
				<view class="search-bar">
					<view class="search-icon-left">
						<text class="icon-text">➕</text>
					</view>
					<input 
						class="search-input" 
						v-model="searchQuery"
						placeholder="Ask me anything!"
						placeholder-class="search-placeholder"
						@focus="handleSearchFocus"
						@blur="handleSearchBlur"
					/>
					<view class="search-button" @click="handleSearch">
						<text class="icon-text">↑</text>
					</view>
				</view>
			</view>
			
			<!-- 搜索标签 -->
			<view class="search-tabs">
				<view 
					class="search-tab" 
					:class="{ 'active': activeTab === 'wardrobe' }"
					@click="setActiveTab('wardrobe')"
				>
					<text class="tab-text">My Wardrobe</text>
				</view>
				<view 
					class="search-tab" 
					:class="{ 'active': activeTab === 'online' }"
					@click="setActiveTab('online')"
				>
					<text class="tab-text">Online Search</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'

const activeMenu = ref('recommendation')
const activeTab = ref('wardrobe')
const searchQuery = ref('')

const setActiveMenu = (menu) => {
	activeMenu.value = menu
	// TODO: 实现菜单切换逻辑
	console.log('切换到菜单:', menu)
}

const setActiveTab = (tab) => {
	activeTab.value = tab
	// TODO: 实现标签切换逻辑
	console.log('切换到标签:', tab)
}

const handleSearchFocus = () => {
	// TODO: 搜索框获得焦点时的逻辑
}

const handleSearchBlur = () => {
	// TODO: 搜索框失去焦点时的逻辑
}

const handleSearch = () => {
	if (!searchQuery.value.trim()) {
		uni.showToast({
			title: '請輸入搜索內容',
			icon: 'none'
		})
		return
	}
	// TODO: 实现搜索逻辑
	console.log('搜索:', searchQuery.value)
}

const handleGuestUser = () => {
	// TODO: 处理访客用户逻辑
	uni.showToast({
		title: '訪客用戶功能開發中',
		icon: 'none'
	})
}

const handleSetting = () => {
	// TODO: 处理设置逻辑
	uni.showToast({
		title: '設置功能開發中',
		icon: 'none'
	})
}
</script>

<style scoped>
.container {
	display: flex;
	width: 100vw;
	height: 100vh;
	background-color: #F3EDE3;
}

/* 左侧边栏 */
.sidebar {
	width: 23.61%;
	background-color: #F8EDDD;
	display: flex;
	flex-direction: column;
	padding: 40rpx 30rpx;
	box-shadow: 2rpx 0 8rpx rgba(0, 0, 0, 0.04);
}

.sidebar-header {
	display: flex;
	align-items: center;
	margin-bottom: 60rpx;
	padding-bottom: 30rpx;
	border-bottom: 1rpx solid rgba(0, 0, 0, 0.08);
}

.home-icon {
	width: 40rpx;
	height: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 15rpx;
}

.app-title {
	font-size: 24rpx;
	font-weight: 600;
	color: #333;
	line-height: 1.4;
	flex: 1;
}

.nav-menu {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.nav-item {
	display: flex;
	align-items: center;
	padding: 20rpx 16rpx;
	border-radius: 16rpx;
	cursor: pointer;
	transition: all 0.2s ease;
	margin-bottom: 4rpx;
}

.nav-item:active {
	opacity: 0.7;
}

.nav-item.active {
	background-color: rgba(168, 155, 132, 0.15);
}

.nav-item.active .nav-icon {
	background-color: #A89B84;
}

.nav-item.active .icon-text {
	color: #FFFFFF;
}

.nav-item.active .nav-text {
	color: #A89B84;
	font-weight: 600;
}

.nav-icon {
	width: 44rpx;
	height: 44rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 12rpx;
	background-color: transparent;
	margin-right: 16rpx;
	transition: all 0.2s ease;
}

.icon-text {
	font-size: 32rpx;
	color: #666;
	transition: all 0.2s ease;
}

.nav-text {
	font-size: 26rpx;
	color: #333;
	transition: all 0.2s ease;
}

.sidebar-footer {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	padding-top: 30rpx;
	border-top: 1rpx solid rgba(0, 0, 0, 0.08);
}

/* 主内容区 */
.main-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	padding: 60rpx 80rpx;
	overflow-y: auto;
}

.greeting-section {
	margin-bottom: 30rpx;
}

.greeting-content {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 16rpx;
}

.robot-icon {
	width: 60rpx;
	height: 60rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #FFFFFF;
	border-radius: 16rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.06);
}

.greeting-text {
	font-size: 48rpx;
	font-weight: 600;
	color: #333;
}

.wave-emoji {
	font-size: 48rpx;
}

.weather-section {
	text-align: center;
	margin-bottom: 50rpx;
}

.weather-text {
	font-size: 28rpx;
	color: #666;
	line-height: 1.5;
}

.search-section {
	margin-bottom: 30rpx;
}

.search-bar {
	display: flex;
	align-items: center;
	background-color: #FFFFFF;
	border-radius: 50rpx;
	padding: 0 20rpx;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
	border: 2rpx solid rgba(168, 155, 132, 0.2);
	transition: all 0.2s ease;
}

.search-bar:focus-within {
	border-color: #A89B84;
	box-shadow: 0 6rpx 20rpx rgba(168, 155, 132, 0.15);
}

.search-icon-left {
	width: 44rpx;
	height: 44rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 16rpx;
}

.search-input {
	flex: 1;
	height: 88rpx;
	font-size: 28rpx;
	color: #333;
	padding: 0 10rpx;
}

.search-placeholder {
	color: #999;
}

.search-button {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #A89B84;
	border-radius: 50%;
	cursor: pointer;
	transition: all 0.2s ease;
	margin-left: 10rpx;
}

.search-button:active {
	opacity: 0.8;
	transform: scale(0.95);
}

.search-button .icon-text {
	color: #FFFFFF;
	font-size: 32rpx;
	font-weight: 600;
}

.search-tabs {
	display: flex;
	justify-content: center;
	gap: 30rpx;
}

.search-tab {
	padding: 12rpx 30rpx;
	cursor: pointer;
	transition: all 0.2s ease;
}

.search-tab.active .tab-text {
	color: #A89B84;
	font-weight: 600;
}

.tab-text {
	font-size: 26rpx;
	color: #666;
	transition: all 0.2s ease;
}

.search-tab:active {
	opacity: 0.7;
}
</style>