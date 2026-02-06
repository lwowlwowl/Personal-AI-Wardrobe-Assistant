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
					:class="{ 'active': activeMenu === 'analysis' }"
					@click="setActiveMenu('analysis')"
				>
					<view class="nav-icon">
						<image :src="activeMenu === 'analysis' ? '/static/icons/icon-analysis-active.svg' : '/static/icons/icon-analysis.svg'" mode="aspectFit" class="icon-img icon-20"></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Wardrobe Analysis</text>
				</view>
			</view>
			
			<view class="divider"></view>
			
			<view class="sidebar-footer">
				<view class="nav-item footer-item" @click="handleGuestUser">
					<view class="nav-icon">
						<image src="/static/icons/icon-user.svg" mode="aspectFit" class="icon-img icon-20"></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Guest User</text>
				</view>
				
				<view class="nav-item footer-item" @click="handleSetting">
					<view class="nav-icon">
						<image src="/static/icons/icon-setting.svg" mode="aspectFit" class="icon-img icon-20"></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Setting</text>
				</view>
			</view>
		</view>
		
		<view class="main-content" ref="mainContentRef">
			<!-- 根据选中的菜单项切换显示不同的组件，带切换动画 -->
			<view class="main-content-inner">
				<transition name="view-fade" mode="out-in">
					<RecommendationAI v-if="activeMenu === 'recommendation'" key="recommendation" />
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
					<view v-else-if="activeMenu === 'analysis'" key="analysis" class="view-placeholder">Wardrobe Analysis (Coming soon)</view>
				</transition>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import RecommendationAI from './components/RecommendationAI.vue'
import VirtualTryOn from './components/VirtualTryOn.vue'
import WardrobeView from './components/MyWardrobe/WardrobeView.vue'

const activeMenu = ref('recommendation')
const isCollapsed = ref(false)
const mainContentRef = ref(null)
const initialClothingForTryon = ref(null)
const initialPersonImageForTryon = ref(null)

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

// 後端聯調保留：訪客/設置的 Toast 提示
const handleGuestUser = () => {
	uni.showToast({
		title: '訪客用戶功能開發中',
		icon: 'none'
	})
}

const handleSetting = () => {
	uni.showToast({
		title: '設置功能開發中',
		icon: 'none'
	})
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

.nav-menu {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

/* 导航项 */
.nav-item {
	display: flex;
	align-items: center;
	padding: 24rpx 24rpx;
	border-radius: 50rpx; /* 完整的胶囊圆角 */
	cursor: pointer;
	transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
	justify-content: flex-start;
	/* 固定高度，防止激活状态改变布局 */
	min-height: 72rpx;
	height: 72rpx;
	box-sizing: border-box;
}

/* 折叠时导航项居中 */
.sidebar.collapsed .nav-item {
	justify-content: center;
	padding: 24rpx 0;
}

.nav-item:hover {
	background-color: rgba(0,0,0,0.03);
}

/* 激活状态：深褐色背景，白色文字 */
.nav-item.active {
	background-color: #9D8B70; 
	box-shadow: 0 4rpx 12rpx rgba(157, 139, 112, 0.3);
	/* 确保激活状态不改变高度和布局 */
	min-height: 72rpx;
	height: 72rpx;
}

.nav-item.active .nav-text {
	color: #FFFFFF;
	font-weight: 500;
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
	/* 英文用系统无衬线体更易读，或者也用 Didot 保持一致，这里推荐无衬线体搭配 */
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
	font-weight: 550;
	color: #48484a; /* 稍微柔和一点的黑 */
	letter-spacing: 0.3px;
	white-space: nowrap;
	opacity: 1;
	transition: opacity 0.3s ease, width 0.3s ease;
	overflow: hidden;
	white-space: nowrap;
}

.sidebar-footer {
	margin-top: auto;
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

.footer-item {
	padding-left: 0; /* 底部菜单靠左对齐，不需要胶囊背景 */
}

.sidebar.collapsed .footer-item {
	justify-content: center;
}

.footer-item:hover {
	background-color: transparent;
	opacity: 0.7;
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

.view-placeholder {
	width: 100%;
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 36rpx;
	color: #9D8B70;
}

</style>
