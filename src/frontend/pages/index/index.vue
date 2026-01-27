<template>
	<view class="container">
		<view class="sidebar" :class="{ 'collapsed': isCollapsed }">
			<view class="sidebar-header" @click="toggleSidebar">
				<view class="home-icon">
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#1D1D1F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
						<polyline points="9 22 9 12 15 12 15 22"></polyline>
					</svg>
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
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" :stroke="activeMenu === 'recommendation' ? '#FFF' : '#1D1D1F'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<rect x="3" y="11" width="18" height="10" rx="2"></rect>
							<circle cx="12" cy="5" r="2"></circle>
							<path d="M12 7v4"></path>
							<line x1="8" y1="16" x2="8" y2="16"></line>
							<line x1="16" y1="16" x2="16" y2="16"></line>
						</svg>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Recommendation AI</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'tryon' }"
					@click="setActiveMenu('tryon')"
				>
					<view class="nav-icon">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" :stroke="activeMenu === 'tryon' ? '#FFF' : '#1D1D1F'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
							<circle cx="12" cy="13" r="4"></circle>
						</svg>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Virtual Try-On</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'wardrobe' }"
					@click="setActiveMenu('wardrobe')"
				>
					<view class="nav-icon">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" :stroke="activeMenu === 'wardrobe' ? '#FFF' : '#1D1D1F'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M20.38 3.46L16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"></path>
						</svg>
					</view>
					<text class="nav-text" v-show="!isCollapsed">My Wardrobe</text>
				</view>
				
				<view 
					class="nav-item" 
					:class="{ 'active': activeMenu === 'analysis' }"
					@click="setActiveMenu('analysis')"
				>
					<view class="nav-icon">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" :stroke="activeMenu === 'analysis' ? '#FFF' : '#1D1D1F'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<line x1="18" y1="20" x2="18" y2="10"></line>
							<line x1="12" y1="20" x2="12" y2="4"></line>
							<line x1="6" y1="20" x2="6" y2="14"></line>
						</svg>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Wardrobe Analysis</text>
				</view>
			</view>
			
			<view class="divider"></view>
			
			<view class="sidebar-footer">
				<view class="nav-item footer-item" @click="handleGuestUser">
					<view class="nav-icon">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1D1D1F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
							<circle cx="12" cy="7" r="4"></circle>
						</svg>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Guest User</text>
				</view>
				
				<view class="nav-item footer-item" @click="handleSetting">
					<view class="nav-icon">
						<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1D1D1F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
							<circle cx="12" cy="12" r="3"></circle>
							<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
						</svg>
					</view>
					<text class="nav-text" v-show="!isCollapsed">Setting</text>
				</view>
			</view>
		</view>
		
		<view class="main-content" ref="mainContentRef">
			<!-- 根据选中的菜单项切换显示不同的组件 -->
			<RecommendationAI v-if="activeMenu === 'recommendation'" />
			<VirtualTryOn v-if="activeMenu === 'tryon'" :main-content-ref="mainContentRef" />
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import RecommendationAI from './components/RecommendationAI.vue'
import VirtualTryOn from './components/VirtualTryOn.vue'

const activeMenu = ref('recommendation')
const isCollapsed = ref(false)
const mainContentRef = ref(null)

const setActiveMenu = (menu) => {
	activeMenu.value = menu
}

const toggleSidebar = () => {
	isCollapsed.value = !isCollapsed.value
}

const handleGuestUser = () => {}
const handleSetting = () => {}
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
	align-items: flex-start; /* 改为顶部对齐，允许内容超出 */
	justify-content: center; /* 水平居中 */
	position: relative;
	transition: margin-left 0.3s ease;
	overflow-y: hidden; /* 默认不允许滚动，由子组件控制 */
	height: 100vh; /* 设置固定高度 */
}

</style>