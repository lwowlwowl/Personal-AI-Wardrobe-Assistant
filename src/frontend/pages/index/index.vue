<template>
	<view class="container">
		<view class="sidebar" :class="{ 'collapsed': isCollapsed }">
			<view class="sidebar-header" @click="toggleSidebar">
				<view class="home-icon">
					<image src="/static/icons/icon-home.svg" mode="aspectFit" class="icon-img icon-24"></image>
				</view>
				<view class="app-title-group" v-show="!isCollapsed">
					<text class="app-title">Personal AI</text>
					<text class="app-title">Wardrobe Assistant</text>
				</view>
			</view>
			
			<view class="divider"></view>
			
			<view class="nav-and-conversation">
			<view class="nav-menu">
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'recommendation' }"
					@click="setActiveMenu('recommendation')"
				>
					<view class="nav-icon">
						<image :src="activeMenu === 'recommendation' ? '/static/icons/icon-recommendation-active.svg' : '/static/icons/icon-recommendation.svg'" mode="aspectFit" class="icon-img icon-20"></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Recommendation AI</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'tryon' }"
					@click="setActiveMenu('tryon')"
				>
					<view class="nav-icon">
						<image :src="activeMenu === 'tryon' ? '/static/icons/icon-tryon-active.svg' : '/static/icons/icon-tryon.svg'" mode="aspectFit" class="icon-img icon-20"></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Virtual Try-On</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'wardrobe' }"
					@click="setActiveMenu('wardrobe')"
				>
					<view class="nav-icon">
						<image :src="activeMenu === 'wardrobe' ? '/static/icons/icon-wardrobe-active.svg' : '/static/icons/icon-wardrobe.svg'" mode="aspectFit" class="icon-img icon-20"></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">My Wardrobe</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'calendar' }"
					@click="setActiveMenu('calendar')"
				>
					<view class="nav-icon">
						<image :src="activeMenu === 'calendar' ? '/static/icons/icon-calendar-active.svg' : '/static/icons/icon-calendar.svg'" mode="aspectFit" class="icon-img icon-20"></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">My Calendar</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'analysis' }"
					@click="setActiveMenu('analysis')"
				>
					<view class="nav-icon">
						<image :src="activeMenu === 'analysis' ? '/static/icons/icon-analysis-active.svg' : '/static/icons/icon-analysis.svg'" mode="aspectFit" class="icon-img icon-20"></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Wardrobe Analysis</text>
				</view>
			</view>
			
			<!-- Recommendation AI 专用：由 ConversationSidebar 组件负责 -->
			<template v-if="activeMenu === 'recommendation' && !isCollapsed">
				<view class="divider"></view>
				<ConversationSidebar
					ref="conversationSidebarRef"
					:conversation-state="conversationState"
					@update:conversation-state="onConversationStateUpdate"
					v-model:open-menu-conv-id="openConvMenuId"
				/>
			</template>
			</view>
			
			<view class="divider"></view>
			
			<view class="sidebar-footer">
				<!-- 状态卡片：点击后上方浮出小浮层，浮层宽度略小于触发块 -->
				<view class="user-status-card">
					<transition name="user-menu-fade">
						<view v-if="showUserMenu" class="user-menu-popup" @click.stop>
							<view v-if="isLoggedIn" class="user-menu-item" @click="handleLogout">
								<image src="/static/icons/icon-logout.svg" mode="aspectFit" class="user-menu-item-icon"></image>
								<text class="user-menu-item-text">退出登录</text>
							</view>
							<view v-else class="user-menu-item" @click="handleGoToLogin">
								<image src="/static/icons/icon-logout.svg" mode="aspectFit" class="user-menu-item-icon"></image>
								<text class="user-menu-item-text">前往登录</text>
							</view>
						</view>
					</transition>
					<view class="footer-item user-status-trigger" @click.stop="toggleUserMenu">
						<view class="nav-icon">
							<image src="/static/icons/icon-user.svg" mode="aspectFit" class="icon-img icon-20"></image>
						</view>
						<text class="nav-text" v-show="!isCollapsed">{{ displayUserName }}</text>
					</view>
				</view>
			</view>
		</view>
		
		<view class="main-content" ref="mainContentRef" @click="closeMenus">
			<!-- 根据选中的菜单项切换显示不同的组件，带切换动画 -->
			<view class="main-content-inner">
				<transition name="view-fade" mode="out-in">
					<RecommendationAI
						v-if="activeMenu === 'recommendation'"
						key="recommendation"
						:current-conversation-id="conversationState.currentConversationId"
						:current-conversation="conversationState.currentConversation"
						@create-conversation="(e) => conversationSidebarRef?.handleCreateConversation(e)"
						@update-conversation="(e) => conversationSidebarRef?.handleUpdateConversation(e)"
					/>
					<VirtualTryOn
					v-else-if="activeMenu === 'tryon'"
					:key="'tryon-' + (initialClothingForTryon || '') + '-' + (initialPersonImageForTryon || '')"
					:main-content-ref="mainContentRef"
					:initial-clothing-image="initialClothingForTryon || null"
					:initial-person-image="initialPersonImageForTryon || null"
				/>
					<WardrobeView
						v-else-if="activeMenu === 'wardrobe'"
						key="wardrobe"
						@switch-to-tryon="handleSwitchToTryon"
					/>
					<MyCalendar v-else-if="activeMenu === 'calendar'" key="calendar" />
					<WardrobeAnalysis v-else-if="activeMenu === 'analysis'" key="analysis" />
				</transition>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, nextTick, provide } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { authVerify } from '@/api/wardrobe.js'
import RecommendationAI from './components/RecommendationAI/RecommendationAI.vue'
import ConversationSidebar from './components/RecommendationAI/ConversationSidebar.vue'
import VirtualTryOn from './components/VirtualTryOn.vue'
import WardrobeView from './components/MyWardrobe/WardrobeView.vue'
import MyCalendar from './components/MyCalendar/MyCalendar.vue'
import WardrobeAnalysis from './components/WardrobeAnalysis/WardrobeAnalysis.vue'

const activeMenu = ref('recommendation')
const isCollapsed = ref(false)
const mainContentRef = ref(null)
const conversationSidebarRef = ref(null)
const initialClothingForTryon = ref(null)
const initialPersonImageForTryon = ref(null)

// 由 ConversationSidebar 同步过来，仅用于传给 RecommendationAI
const conversationState = ref({
	conversations: [],
	currentConversationId: null,
	currentConversation: null
})

// 侧边栏显示的用户名：登录后显示用户名，否则显示 Guest User
const displayUserName = ref('Guest User')
const isLoggedIn = ref(false)

// 供子组件（如 WardrobeView）在 checkAuthStatus 后同步登入状态
const updateAuthState = (loggedIn, username) => {
	isLoggedIn.value = !!loggedIn
	displayUserName.value = loggedIn && username ? username : 'Guest User'
}

const refreshDisplayUserName = async () => {
	const token = uni.getStorageSync('auth_token')
	if (!token) {
		displayUserName.value = 'Guest User'
		isLoggedIn.value = false
		return
	}
	try {
		const res = await authVerify(token)
		if (res.statusCode === 200 && res.data?.valid) {
			const username = res.data?.username || uni.getStorageSync('user_info')?.username
			displayUserName.value = username || 'Guest User'
			isLoggedIn.value = true
		} else {
			uni.removeStorageSync('auth_token')
			uni.removeStorageSync('user_info')
			displayUserName.value = 'Guest User'
			isLoggedIn.value = false
		}
	} catch {
		// 网络错误等保持当前显示，不强制清除
		displayUserName.value = uni.getStorageSync('user_info')?.username || 'Guest User'
		isLoggedIn.value = !!(token && uni.getStorageSync('user_info'))
	}
}
;(async () => { await refreshDisplayUserName() })()
onShow(() => {
	refreshDisplayUserName()
})

provide('updateAuthState', updateAuthState)

const openConvMenuId = ref(null)
const showUserMenu = ref(false)
const closeMenus = () => {
	openConvMenuId.value = null
	showUserMenu.value = false
}
const toggleUserMenu = () => {
	showUserMenu.value = !showUserMenu.value
}
const handleLogout = () => {
	uni.removeStorageSync('auth_token')
	uni.removeStorageSync('user_info')
	displayUserName.value = 'Guest User'
	isLoggedIn.value = false
	showUserMenu.value = false
	uni.reLaunch({
		url: '/pages/login/login'
	})
}

const handleGoToLogin = () => {
	showUserMenu.value = false
	uni.navigateTo({
		url: '/pages/login/login'
	})
}
const onConversationStateUpdate = (v) => {
	if (v && Array.isArray(v.conversations)) conversationState.value = v
}

const setActiveMenu = (menu) => {
	activeMenu.value = menu
	if (menu !== 'tryon') {
		initialClothingForTryon.value = null
		initialPersonImageForTryon.value = null
	}
}

const toggleSidebar = () => {
	isCollapsed.value = !isCollapsed.value
}

const handleSwitchToTryon = (item, defaultModelImage) => {
	initialClothingForTryon.value = item?.image ?? null
	initialPersonImageForTryon.value = defaultModelImage ?? null
	nextTick(() => {
		activeMenu.value = 'tryon'
	})
}
</script>

<style scoped>
/* 定义衬线字体栈，模拟设计图的优雅感 */
.container {
	display: flex;
	width: 100vw;
	height: 100vh;
	/* 主体背景色 - 极淡的米白色 */
	background-color: #FDFBF7; 
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	color: #1D1D1F;
	font-weight: bold;
}

/* 左侧边栏 */
.sidebar {
	width: 260rpx; /* 调整宽度比例 */
	min-width: 250px; /* 桌面端最小宽度 */
	/* 侧边栏背景色 - 稍深一点的米色 */
	background-color: #F5F0E6; 
	display: flex;
	flex-direction: column;
	padding: 60rpx 40rpx 20rpx 40rpx;
	border-right: 1px solid rgba(0,0,0,0.05);
	transition: width 0.3s ease, min-width 0.3s ease, padding 0.3s ease;
	overflow: hidden;
}

/* 折叠状态 */
.sidebar.collapsed {
	width: 100rpx;
	min-width: 80px;
	padding: 60rpx 20rpx 20rpx 20rpx;
}

.sidebar-header {
	display: flex;
	align-items: center; /* 垂直居中对齐 */
	height: 88rpx;
	margin-bottom: 20rpx;
	gap: 24rpx; /* Home icon 和文本之间的距离 */
	cursor: pointer;
	justify-content: center; /* 折叠时居中 */
	transition: justify-content 0.3s ease;
	white-space: nowrap;
}

.sidebar.collapsed .sidebar-header {
	justify-content: center;
	gap: 0;
}

.app-title-group {
	display: flex;
	flex-direction: column;
}

.app-title {
	font-size: 40rpx; /* 字体加大 */
	font-weight: 500;
	color: #1D1D1F;
	line-height: 1.2;
	/* 继承 container 的 Didot 字体，或者显式指定 */
	font-family: "Didot", "Bodoni MT", "Songti SC", serif;
	letter-spacing: -0.5px; /* 紧凑一点更优雅 */

	/* 强制文字即使空间不够也不换行 */
    white-space: nowrap; 
    /* 防止文字溢出导致布局错乱 */
	overflow: hidden;
    text-overflow: ellipsis;
}

.divider {
	width: 100%;
	height: 1px;
	background-color: rgba(0, 0, 0, 0.1);
	margin: 30rpx 0;
	transition: width 0.3s ease, margin 0.3s ease;
}

.nav-and-conversation {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.nav-menu {
	flex-shrink: 0;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

/* 导航项 */
.nav-item {
	position: relative;
	display: flex;
	align-items: center;
	padding: 10px 14px;
	border-radius: 10px;
	cursor: pointer;
	transition: all 0.18s ease;
	justify-content: flex-start;
	/* 固定高度，防止激活状态改变布局 */
	min-height: 72rpx;
	height: 72rpx;
	box-sizing: border-box;
}

/* 折叠时导航项居中 */
.sidebar.collapsed .nav-item {
	justify-content: center;
	padding: 10px 0;
}

.nav-item:hover {
	background-color: #F1ECE4;
}

/* 激活状态：柔和浅背景 + 深文字 */
.nav-item.active {
	background-color: #9D8B70;
	box-shadow: 0 6px 16px rgba(157, 139, 112, 0.35);
	/* 确保激活状态不改变高度和布局 */
	min-height: 72rpx;
	height: 72rpx;
}

.nav-item.active:hover {
	background-color: #9D8B70;
}

.nav-item.active .nav-text {
	color: #FFFFFF;
	font-weight: 600;
}

.nav-item.active .icon-img {
	filter: brightness(0) invert(1);
}

.nav-icon {
	width: 40rpx;
	height: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 20rpx; /* 导航图标和文字之间的距离 */
	transition: margin-right 0.3s ease;
	/* 固定图标容器尺寸，防止激活状态改变 */
	flex-shrink: 0;
}

.icon-img {
	display: block;
}
.icon-img.icon-24 {
	width: 24px;
	height: 24px;
}
.icon-img.icon-20 {
	width: 20px;
	height: 20px;
}

.sidebar.collapsed .nav-icon {
	margin-right: 0;
}

.nav-text {
	font-size: 28rpx;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
	font-weight: 550;
	color: #48484a;
	letter-spacing: 0.3px;
	white-space: nowrap;
	opacity: 1;
	transition: opacity 0.3s ease, width 0.3s ease;
	overflow: hidden;
}

/* 底部用户行容器：margin-top: auto 贴底；上下间距在此或 .footer-item 调整 */
.sidebar-footer {
	position: relative;
	flex-shrink: 0;
	margin-top: auto;
	padding-top: 5rpx;
	padding-bottom: 13rpx;
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

/* 状态卡片容器（相对定位，供浮层对齐） */
.user-status-card {
	position: relative;
	width: 100%;
}

/* 触发块：平时无框，hover 时才显示框，背景与侧栏一致不改变 */
.footer-item.user-status-trigger {
	display: flex;
	align-items: center;
	padding: 20rpx 24rpx;
	min-height: 72rpx;
	box-sizing: border-box;
	cursor: pointer;
	transition: border-color 0.2s, box-shadow 0.2s;
	border-radius: 16rpx;
	border: 1px solid transparent;
	background: transparent;
	box-shadow: none;
}
.footer-item.user-status-trigger:hover {
	border-color: rgba(0, 0, 0, 0.1);
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}
.footer-item.user-status-trigger:active {
	border-color: rgba(0, 0, 0, 0.12);
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.08);
}

.sidebar.collapsed .footer-item.user-status-trigger {
	justify-content: center;
	padding: 24rpx 0;
}

/* 浮层出现/消失动效：opacity + translateY，120ms ease-out，无 scale/弹性 */
.user-menu-fade-enter-active,
.user-menu-fade-leave-active {
	transition: opacity 120ms ease-out, transform 120ms ease-out;
}
.user-menu-fade-enter-from,
.user-menu-fade-leave-to {
	opacity: 0;
	transform: translateY(6px);
}
.user-menu-fade-enter-to,
.user-menu-fade-leave-from {
	opacity: 1;
	transform: translateY(0);
}

/* 上方浮层：宽度与触发块一致（左右不缩进），字体黑色 */
.user-menu-popup {
	position: absolute;
	left: 0;
	right: 0;
	bottom: 100%;
	margin-bottom: 10rpx;
	background: #fff;
	border-radius: 14rpx;
	border: 1px solid rgba(0, 0, 0, 0.08);
	box-shadow: 0 8rpx 28rpx rgba(0, 0, 0, 0.12);
	overflow: hidden;
	z-index: 100;
}
.user-menu-item {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	gap: 12rpx;
	padding: 20rpx 28rpx;
	font-size: 26rpx;
	font-weight: 500;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
	cursor: pointer;
	transition: background-color 0.2s;
}
.user-menu-item-icon {
	width: 32rpx;
	height: 32rpx;
	flex-shrink: 0;
}
.user-menu-item-text {
	color: #1D1D1F;
}
.user-menu-item:hover {
	background-color: rgba(0, 0, 0, 0.05);
}
.user-menu-item:active {
	background-color: rgba(0, 0, 0, 0.08);
}

/* 主内容区 */
.main-content {
	flex: 1;
	display: flex;
	align-items: flex-start;
	justify-content: center;
	position: relative;
	transition: margin-left 0.3s ease;
	overflow: hidden;
	height: 100vh;
}

.main-content-inner {
	width: 100%;
	height: 100%;
	position: relative;
}

/* 视图切换动画 */
.view-fade-enter-active,
.view-fade-leave-active {
	transition: opacity 0.28s ease, transform 0.28s ease;
}
.view-fade-enter-from {
	opacity: 0;
	transform: translateX(12rpx);
}
.view-fade-leave-to {
	opacity: 0;
	transform: translateX(-12rpx);
}
.view-fade-enter-to,
.view-fade-leave-from {
	opacity: 1;
	transform: translateX(0);
}

</style>
