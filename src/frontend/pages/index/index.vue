<template>
	<view class="container" @click="closeMenus">
		<view class="sidebar" :class="{ 'collapsed': isCollapsed }">
			<view class="sidebar-header" @click="toggleSidebar">
				<view class="nav-icon">
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
					v-for="item in sidebarNavItems"
					:key="item.id"
					class="nav-item"
					:class="{ active: activeMenu === item.id }"
					@click="setActiveMenu(item.id)"
				>
					<view class="nav-icon">
						<image
							:src="activeMenu === item.id ? item.iconActive : item.icon"
							mode="aspectFit"
							class="icon-img icon-20"
						></image>
					</view>
					<text class="nav-text" v-show="!isCollapsed">{{ item.label }}</text>
				</view>
			</view>
			
			<!-- Recommendation AI specific: handled by ConversationSidebar component -->
			<template v-if="activeMenu === 'recommendation' && !isCollapsed">
				<view class="divider"></view>
				<ConversationSidebar
					ref="conversationSidebarRef"
					:conversation-state="conversationState"
					:is-logged-in="isLoggedIn"
					@update:conversation-state="onConversationStateUpdate"
					v-model:open-menu-conv-id="openConvMenuId"
				/>
			</template>
			</view>
			
			<view class="divider"></view>
			
			<view class="sidebar-footer">
				<!-- Status card: click to show a top popup, slightly narrower than trigger -->
				<view class="user-status-card">
					<transition name="user-menu-fade">
						<view v-if="showUserMenu" class="user-menu-popup" :class="{ 'user-menu-popup--collapsed': isCollapsed }" @click.stop>
							<template v-if="isLoggedIn">
								<view v-show="!isCollapsed" class="user-menu-header">
									<view class="user-menu-avatar-wrap">
										<image v-if="userProfile?.avatar_url" :src="userAvatarUrl(userProfile.avatar_url)" mode="aspectFill" class="user-menu-avatar-img"></image>
										<image v-else src="/static/icons/icon-user.svg" mode="aspectFit" class="user-menu-avatar-icon"></image>
									</view>
									<text class="user-menu-username">{{ userProfile?.username || displayUserName }}</text>
								</view>
								<view v-if="userProfile?.email && !isCollapsed" class="user-menu-email">{{ userProfile.email }}</view>
								<view v-show="!isCollapsed" class="user-menu-divider"></view>
								<view class="user-menu-item" @click="openSettings">
									<image src="/static/icons/icon-setting.svg" mode="aspectFit" class="user-menu-item-icon"></image>
									<text v-show="!isCollapsed" class="user-menu-item-text">Settings</text>
								</view>
								<view class="user-menu-item" @click="handleLogout">
									<image src="/static/icons/icon-logout.svg" mode="aspectFit" class="user-menu-item-icon"></image>
									<text v-show="!isCollapsed" class="user-menu-item-text">Log out</text>
								</view>
							</template>
							<view v-else class="user-menu-item" @click="handleGoToLogin">
								<image src="/static/icons/icon-logout.svg" mode="aspectFit" class="user-menu-item-icon"></image>
								<text v-show="!isCollapsed" class="user-menu-item-text">Log in</text>
							</view>
						</view>
					</transition>
					<view class="footer-item user-status-trigger" @click.stop="toggleUserMenu">
						<view class="nav-icon footer-avatar-wrap">
							<view v-if="isLoggedIn && userProfile?.avatar_url" class="avatar-circle">
								<image :src="userAvatarUrl(userProfile.avatar_url)" mode="aspectFill" class="avatar-circle-img"></image>
							</view>
							<image v-else src="/static/icons/icon-user.svg" mode="aspectFit" class="icon-img icon-20"></image>
						</view>
						<text class="nav-text" v-show="!isCollapsed">{{ displayUserName }}</text>
					</view>
				</view>
			</view>
		</view>
		
		<view class="main-content" ref="mainContentRef">
			<!-- Switch displayed component by selected menu, with transition -->
			<view class="main-content-inner">
				<transition name="view-fade" mode="out-in">
					<RecommendationAI
						v-if="activeMenu === 'recommendation'"
						key="recommendation"
						:is-logged-in="isLoggedIn"
						:current-conversation-id="conversationState.currentConversationId"
						:current-conversation="conversationState.currentConversation"
						@create-conversation="(e) => conversationSidebarRef?.handleCreateConversation(e)"
						@update-conversation="(e) => conversationSidebarRef?.handleUpdateConversation(e)"
						@switch-to-tryon="handleSwitchToTryon"
						@switch-to-full-outfit-tryon="handleSwitchToFullOutfitTryon"
						@calendar-updated="() => myCalendarRef?.refetch?.()"
					/>
					<VirtualTryOn
					v-else-if="activeMenu === 'tryon'"
					:key="'tryon-' + tryonMountKey"
					:is-logged-in="isLoggedIn"
					:main-content-ref="mainContentRef"
					:initial-clothing-image="initialClothingForTryon || null"
					:initial-person-image="initialPersonImageForTryon || null"
					:initial-outfit-queue="initialOutfitQueueForTryon || []"
				/>
					<WardrobeView
						v-else-if="activeMenu === 'wardrobe'"
						key="wardrobe"
						@switch-to-tryon="handleSwitchToTryon"
					/>
					<MyCalendar ref="myCalendarRef" v-else-if="activeMenu === 'calendar'" key="calendar" />
					<WardrobeAnalysis v-else-if="activeMenu === 'analysis'" key="analysis" :is-logged-in="isLoggedIn" />
				</transition>
			</view>
		</view>

		<SettingsModal
			:visible="showSettingsModal"
			:user-profile="userProfile"
			:display-user-name="displayUserName"
			@close="closeSettingsModal"
			@update:userProfile="onSettingsUpdateUserProfile"
		/>
	</view>
</template>

<script setup>
import { ref, nextTick, provide, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { authVerify, getUsersMe, API_BASE_URL } from '@/api/userApi.js'
import RecommendationAI from './components/RecommendationAI/RecommendationAI.vue'
import ConversationSidebar from './components/RecommendationAI/sidebar/ConversationSidebar.vue'
import VirtualTryOn from './components/VirtualTryOn.vue'
import WardrobeView from './components/MyWardrobe/WardrobeView.vue'
import MyCalendar from './components/MyCalendar/MyCalendar.vue'
import WardrobeAnalysis from './components/WardrobeAnalysis/WardrobeAnalysis.vue'
import SettingsModal from './SettingsModal.vue'

const sidebarNavItems = [
	{ id: 'recommendation', label: 'Recommendation AI', icon: '/static/icons/icon-recommendation.svg', iconActive: '/static/icons/icon-recommendation-active.svg' },
	{ id: 'tryon', label: 'Virtual Try-On', icon: '/static/icons/icon-tryon.svg', iconActive: '/static/icons/icon-tryon-active.svg' },
	{ id: 'wardrobe', label: 'My Wardrobe', icon: '/static/icons/icon-wardrobe.svg', iconActive: '/static/icons/icon-wardrobe-active.svg' },
	{ id: 'calendar', label: 'My Calendar', icon: '/static/icons/icon-calendar.svg', iconActive: '/static/icons/icon-calendar-active.svg' },
	{ id: 'analysis', label: 'Wardrobe Analysis', icon: '/static/icons/icon-analysis.svg', iconActive: '/static/icons/icon-analysis-active.svg' }
]

const activeMenu = ref('recommendation')
const isCollapsed = ref(false)
const mainContentRef = ref(null)
const conversationSidebarRef = ref(null)
const initialClothingForTryon = ref(null)
const initialPersonImageForTryon = ref(null)
/** Full outfit try-on: chain each garment; each result becomes the next "person" image */
const initialOutfitQueueForTryon = ref(null)
const tryonMountKey = ref(0)

// Synced from ConversationSidebar, only passed to RecommendationAI
const conversationState = ref({
	conversations: [],
	currentConversationId: null,
	currentConversation: null
})

// Username shown in sidebar: username when logged in, otherwise Guest User
const displayUserName = ref('Guest User')
const isLoggedIn = ref(false)
// Current user profile (fetched by getUsersMe after login, includes avatar and email)
const userProfile = ref(null)

// Used by child components (e.g. WardrobeView) to sync auth state after checkAuthStatus
const updateAuthState = (loggedIn, username) => {
	isLoggedIn.value = !!loggedIn
	displayUserName.value = loggedIn && username ? username : 'Guest User'
}

const refreshDisplayUserName = async () => {
	const token = uni.getStorageSync('auth_token')
	if (!token) {
		displayUserName.value = 'Guest User'
		isLoggedIn.value = false
		userProfile.value = null
		return
	}
	try {
		const res = await authVerify(token)
		if (res.statusCode === 200 && res.data?.valid) {
			const username = res.data?.username || uni.getStorageSync('user_info')?.username
			displayUserName.value = username || 'Guest User'
			isLoggedIn.value = true
			// Fetch full user profile (avatar, email)
			try {
				const meRes = await getUsersMe(token)
				if (meRes.statusCode === 200 && meRes.data) {
					userProfile.value = {
						username: meRes.data.username ?? username,
						email: meRes.data.email ?? '',
						avatar_url: meRes.data.avatar_url ?? null
					}
				} else {
					userProfile.value = { username: displayUserName.value, email: '', avatar_url: null }
				}
			} catch {
				userProfile.value = { username: displayUserName.value, email: '', avatar_url: null }
			}
		} else {
			uni.removeStorageSync('auth_token')
			uni.removeStorageSync('user_info')
			displayUserName.value = 'Guest User'
			isLoggedIn.value = false
			userProfile.value = null
		}
	} catch {
		// Keep current display on network errors; do not force-clear
		displayUserName.value = uni.getStorageSync('user_info')?.username || 'Guest User'
		isLoggedIn.value = !!(token && uni.getStorageSync('user_info'))
		if (!isLoggedIn.value) userProfile.value = null
	}
}

const userAvatarUrl = (url) => {
	if (!url) return ''
	return url.startsWith('http') ? url : `${API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
}

const showSettingsModal = ref(false)

function openSettings() {
	showUserMenu.value = false
	showSettingsModal.value = true
}

function closeSettingsModal() {
	showSettingsModal.value = false
}

function onSettingsUpdateUserProfile(payload) {
	if (payload.username != null) {
		displayUserName.value = payload.username
		if (userProfile.value) userProfile.value.username = payload.username
		uni.setStorageSync('user_info', { ...uni.getStorageSync('user_info'), username: payload.username })
	}
	if (payload.avatar_url != null && userProfile.value) {
		userProfile.value.avatar_url = payload.avatar_url
	}
}

onMounted(() => {
	refreshDisplayUserName()
})
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

const myCalendarRef = ref(null)
const setActiveMenu = (menu) => {
	activeMenu.value = menu
	if (menu !== 'tryon') {
		initialClothingForTryon.value = null
		initialPersonImageForTryon.value = null
		initialOutfitQueueForTryon.value = null
	}
	if (menu === 'calendar') {
		nextTick(() => {
			myCalendarRef.value?.refetch?.()
		})
	}
}

provide('openWardrobeTab', () => {
	setActiveMenu('wardrobe')
})

const toggleSidebar = () => {
	isCollapsed.value = !isCollapsed.value
}

const handleSwitchToTryon = (item, defaultModelImage) => {
	initialOutfitQueueForTryon.value = null
	initialClothingForTryon.value = item?.image ?? null
	initialPersonImageForTryon.value = defaultModelImage ?? null
	tryonMountKey.value += 1
	nextTick(() => {
		activeMenu.value = 'tryon'
	})
}

const normalizeOutfitQueuePayload = (payload) => {
	const q = payload?.outfitQueue
	if (Array.isArray(q) && q.length > 0) {
		return q
			.map((e, i) => {
				if (typeof e === 'string') return { image: e, label: `Garment ${i + 1}` }
				const image = e?.image || e?.url || ''
				const label = String(e?.label || '').trim() || `Step ${i + 1}`
				return image ? { image, label } : null
			})
			.filter(Boolean)
	}
	const urls = Array.isArray(payload?.clothingUrls) ? payload.clothingUrls.filter(Boolean) : []
	if (urls.length === 0) return null
	return urls.map((url, i) => ({ image: url, label: `Garment ${i + 1}` }))
}

const handleSwitchToFullOutfitTryon = (payload) => {
	const normalized = normalizeOutfitQueuePayload(payload)
	initialClothingForTryon.value = null
	initialPersonImageForTryon.value = payload?.personImage ?? null
	initialOutfitQueueForTryon.value = normalized && normalized.length > 0 ? normalized : null
	tryonMountKey.value += 1
	nextTick(() => {
		activeMenu.value = 'tryon'
	})
}
</script>

<style scoped>
/* Define a serif font stack to mimic the design's elegance */
.container {
	display: flex;
	width: 100vw;
	height: 100vh;
	/* Main background color - very light off-white */
	background-color: #FDFBF7; 
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	color: #1D1D1F;
	font-weight: bold;
}

/* Left sidebar */
.sidebar {
	width: 260rpx; /* Adjusted width ratio */
	min-width: 250px; /* Desktop minimum width */
	/* Sidebar background - slightly deeper beige */
	background-color: #F5F0E6; 
	display: flex;
	flex-direction: column;
	padding: 60rpx 40rpx 20rpx 40rpx;
	border-right: 1px solid rgba(0,0,0,0.05);
	transition: width 0.3s ease, min-width 0.3s ease, padding 0.3s ease;
	overflow: hidden;
}

/* Collapsed state */
.sidebar.collapsed {
	width: 100rpx;
	min-width: 80px;
	padding: 60rpx 20rpx 20rpx 20rpx;
}

.sidebar-header {
	display: flex;
	align-items: center; /* Vertically center aligned */
	height: 88rpx;
	margin-bottom: 20rpx;
	gap: 24rpx; /* Gap between home icon and text */
	cursor: pointer;
	justify-content: center; /* Center when collapsed */
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
	font-size: 40rpx; /* Larger font size */
	font-weight: 500;
	color: #1D1D1F;
	line-height: 1.2;
	/* Inherit Didot from container, or specify explicitly */
	font-family: "Didot", "Bodoni MT", "Songti SC", serif;
	letter-spacing: -0.5px; /* Slightly tighter for elegance */

	/* Force no line wrap even when space is tight */
    white-space: nowrap; 
    /* Prevent overflow from breaking layout */
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

/* Navigation item */
.nav-item {
	position: relative;
	display: flex;
	align-items: center;
	padding: 10px 14px;
	border-radius: 10px;
	cursor: pointer;
	/* Only background-color; avoid animating box-shadow/filter (heavy repaint, sidebar text looks soft) */
	transition: background-color 0.16s ease;
	justify-content: flex-start;
	/* Fixed height to prevent layout shift on active state */
	min-height: 72rpx;
	height: 72rpx;
	box-sizing: border-box;
}

/* Center nav items when collapsed */
.sidebar.collapsed .nav-item {
	justify-content: center;
	padding: 10px 0;
}

.nav-item:hover {
	background-color: #F1ECE4;
}

/* Active state: soft light background + dark text */
.nav-item.active {
	background-color: #9D8B70;
	box-shadow: 0 6px 16px rgba(157, 139, 112, 0.35);
	/* Ensure active state does not change height/layout */
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
	margin-right: 20rpx; /* Gap between nav icon and text */
	transition: margin-right 0.3s ease;
	/* Fixed icon container size to avoid active-state shifts */
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
/* Bottom-left avatar: change circle size only via .avatar-circle width/height */
.footer-avatar-wrap {
	width: 80rpx;
	height: 80rpx;
}
.avatar-circle {
	width: 80rpx;
	height: 80rpx;
	border-radius: 50%;
	overflow: hidden;
	flex-shrink: 0;
}
.avatar-circle-img {
	width: 100%;
	height: 100%;
	object-fit: cover;
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
	transition: color 0.16s ease, opacity 0.3s ease, width 0.3s ease;
	overflow: hidden;
}

/* Bottom user row container: stick to bottom via margin-top:auto; adjust spacing here or in .footer-item */
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

/* Status card container (relative positioning for popup alignment) */
.user-status-card {
	position: relative;
	width: 100%;
}

/* Trigger block: borderless by default, border on hover only; keep sidebar-matching background */
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

/* Popup show/hide animation: opacity + translateY, 120ms ease-out, no scale/bounce */
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

/* Top popup: same width as trigger (no side inset), black text */
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
/* In collapsed mode, popup shows icons only with enough width to avoid crowding */
.user-menu-popup--collapsed {
	min-width: 125rpx;
	left: 50%;
	transform: translateX(-50%);
}
.user-menu-popup--collapsed .user-menu-item {
	justify-content: center;
}
.user-menu-header {
	display: flex;
	align-items: center;
	gap: 20rpx;
	padding: 24rpx 28rpx 16rpx;
}
.user-menu-avatar-wrap {
	position: relative;
	width: 96rpx;
	height: 96rpx;
	border-radius: 50%;
	overflow: hidden;
	flex-shrink: 0;
	background: #F1ECE4;
	display: flex;
	align-items: center;
	justify-content: center;
}
.user-menu-avatar-img {
	width: 100%;
	height: 100%;
}
.user-menu-avatar-icon {
	width: 52rpx;
	height: 52rpx;
	opacity: 0.7;
}
.user-menu-username {
	font-size: 38rpx;
	font-weight: 700;
	color: #1D1D1F;
	letter-spacing: 0.02em;
	flex: 1;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.user-menu-email {
	padding: 0 28rpx 16rpx;
	font-size: 24rpx;
	color: #666;
	font-weight: normal;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.user-menu-divider {
	height: 1px;
	background: rgba(0, 0, 0, 0.08);
	margin: 0 16rpx;
}
.user-menu-item {
	display: flex;
	align-items: center;
	justify-content: flex-start;
	gap: 14rpx;
	padding: 20rpx 32rpx;
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

/* Main content area */
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
	min-height: 0;
	position: relative;
	/* Fill main-content height so nested % heights match (avoid top gap / wrong 100vh band) */
	align-self: stretch;
	flex: 1;
}

/* View switching: opacity only to avoid heavy transform compositing and blurry text */
.view-fade-enter-active,
.view-fade-leave-active {
	transition: opacity 0.2s ease;
}
.view-fade-enter-from,
.view-fade-leave-to {
	opacity: 0;
}
.view-fade-enter-to,
.view-fade-leave-from {
	opacity: 1;
}
</style>
