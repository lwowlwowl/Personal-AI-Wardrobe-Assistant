<template>
	<view class="chat-container">
		<!-- 初始状态：问候语部分（居中布局） -->
		<view class="greeting-wrapper" v-if="!hasSearched">
			<view class="robot-hero">
				<image src="/static/icons/icon-robot.svg" mode="aspectFit" class="icon-robot-hero"></image>
			</view>
			<view class="greeting-row">
				<text class="wave-emoji">👋</text>
				<text class="greeting-text">Hi! Good Afternoon</text>
			</view>
			<view class="weather-row">
				<text class="weather-info">Today 21°C</text>
				<text class="weather-divider">|</text>
				<text class="weather-info">Light Breeze</text>
				<text class="weather-divider">|</text>
				<text class="weather-info">Ideal for a Light Jacket</text>
			</view>
		</view>
		
		<!-- 聊天状态：scroll-view 聊天区域 -->
		<scroll-view 
			v-else
			class="chat-scroll-area" 
			scroll-y 
			:scroll-into-view="scrollTarget"
			:scroll-with-animation="true"
			:enable-back-to-top="true"
		>
			<view class="message-list">
				<view 
					v-for="(msg, index) in chatHistory" 
					:key="index" 
					:id="'msg-' + index"
					class="message-row"
					:class="msg.role"
				>
					<!-- 用户消息 (右侧) -->
					<view v-if="msg.role === 'user'" class="user-bubble">
						<text class="message-text">{{ msg.content }}</text>
					</view>
					
					<!-- AI 消息 (左侧) -->
					<view v-else-if="msg.role === 'ai'" class="ai-container">
						<view class="ai-avatar">
							<image src="/static/icons/icon-robot-avatar.svg" mode="aspectFit" class="icon-robot-avatar"></image>
						</view>
						<view class="ai-content">
							<text class="message-text">{{ msg.content }}</text>
							
							<!-- AI 列表项 -->
							<view v-if="msg.list && msg.list.length > 0" class="ai-list">
								<view v-for="(item, itemIndex) in msg.list" :key="itemIndex" class="ai-list-item">
									<text class="list-bullet">•</text>
									<text class="list-text">{{ item }}</text>
								</view>
							</view>
							
							<!-- AI 图片组 -->
							<view v-if="msg.images && msg.images.length > 0" class="ai-image-group">
								<image 
									v-for="(img, imgIndex) in msg.images" 
									:key="imgIndex"
									:src="img" 
									mode="aspectFill"
									class="rec-img"
								/>
							</view>
						</view>
					</view>
					
					<!-- 加载指示器 -->
					<view v-if="msg.role === 'loading'" class="ai-container">
						<view class="ai-avatar">
							<image src="/static/icons/icon-robot-avatar.svg" mode="aspectFit" class="icon-robot-avatar"></image>
						</view>
						<view class="loading-indicator">
							<view class="loading-dot"></view>
							<view class="loading-dot"></view>
							<view class="loading-dot"></view>
						</view>
					</view>
				</view>
				<view class="spacer" id="bottom-spacer"></view>
			</view>
		</scroll-view>
		
		<!-- 底部标签 - 只在初始状态显示 -->
		<view class="search-tabs" v-if="!hasSearched">
			<text 
				class="tab-text" 
				:class="{ 'active': activeTab === 'wardrobe' }"
				@click="setActiveTab('wardrobe')"
			>My Wardrobe</text>
			
			<view class="tab-divider"></view>
			
			<text 
				class="tab-text" 
				:class="{ 'active': activeTab === 'online' }"
				@click="setActiveTab('online')"
			>Online Search</text>
		</view>
		
		<!-- 搜索栏 - 根据状态调整位置 -->
		<view class="input-container" :class="{ 'fixed-bottom': hasSearched }">
			<view class="search-bar">
				<view class="search-icon-left" @click="handleAdd">
					<image src="/static/icons/icon-plus.svg" mode="aspectFit" class="icon-search-btn"></image>
				</view>
				<input 
					class="search-input" 
					v-model="searchQuery"
					placeholder="Ask me anything!"
					placeholder-class="search-placeholder"
					@keyup.enter="handleSearch"
				/>
				<view class="search-button" @click="handleSearch">
					<image src="/static/icons/icon-send.svg" mode="aspectFit" class="icon-search-btn"></image>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const API_BASE_URL = 'http://localhost:8000'
const activeTab = ref('wardrobe')
const searchQuery = ref('')
const hasSearched = ref(false) // 状态管理：是否已搜索
const chatHistory = ref([]) // 聊天历史记录
const scrollTarget = ref('') // 用于自动滚动

const setActiveTab = (tab) => {
	activeTab.value = tab
}

// 自动滚动到底部
const scrollToBottom = () => {
	nextTick(() => {
		scrollTarget.value = 'bottom-spacer'
		// 延迟一下确保 DOM 更新完成
		setTimeout(() => {
			scrollTarget.value = ''
		}, 100)
	})
}

const streamChat = async ({ query, history, onDelta, onError }) => {
	const response = await fetch(`${API_BASE_URL}/api/ai/chat/stream`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ query, history })
	})

	if (!response.ok || !response.body) {
		throw new Error(`请求失败: ${response.status}`)
	}

	const reader = response.body.getReader()
	const decoder = new TextDecoder('utf-8')
	let buffer = ''
	let finished = false

	while (!finished) {
		const { value, done } = await reader.read()
		if (done) break

		buffer += decoder.decode(value, { stream: true })
		let sepIndex = buffer.indexOf('\n\n')

		while (sepIndex !== -1) {
			const rawEvent = buffer.slice(0, sepIndex).trim()
			buffer = buffer.slice(sepIndex + 2)

			if (rawEvent.startsWith('data:')) {
				const dataLine = rawEvent
					.split('\n')
					.find(line => line.startsWith('data:'))
				if (dataLine) {
					const dataText = dataLine.replace(/^data:\s*/, '')
					const payload = JSON.parse(dataText)

					if (payload.type === 'delta' && payload.content) {
						onDelta(payload.content)
					} else if (payload.type === 'error') {
						onError(payload.message || '流式响应异常')
						finished = true
						break
					} else if (payload.type === 'done') {
						finished = true
						break
					}
				}
			}

			sepIndex = buffer.indexOf('\n\n')
		}
	}
}

const handleSearch = async () => {
	const query = searchQuery.value.trim()
	if (!query) return

	// 1. 切换 UI 状态：搜索框下移，问候语消失
	hasSearched.value = true
	
	// 2. 添加用户消息
	chatHistory.value.push({ role: 'user', content: query })
	
	// 清空输入框
	searchQuery.value = ''
	
	// 滚动到底部
	scrollToBottom()
	
	// 3. 添加加载指示器
	chatHistory.value.push({ role: 'loading', content: '' })
	scrollToBottom()

	// 4. 创建空白 AI 消息并接收流式内容
	chatHistory.value = chatHistory.value.filter(msg => msg.role !== 'loading')
	chatHistory.value.push({ role: 'ai', content: '', list: [], images: [] })
	const aiIndex = chatHistory.value.length - 1

	try {
		const history = chatHistory.value
			.filter(msg => msg.role === 'user' || msg.role === 'ai')
			.slice(0, -1) // 去掉当前空白 ai 占位
			.slice(-10)   // 仅保留最近 10 条上下文
			.map(msg => ({ role: msg.role, content: msg.content }))

		await streamChat({
			query,
			history,
			onDelta: (deltaText) => {
				chatHistory.value[aiIndex].content += deltaText
				scrollToBottom()
			},
			onError: (message) => {
				chatHistory.value[aiIndex].content = message || '模型服务异常，请稍后再试'
				scrollToBottom()
			}
		})

		if (!chatHistory.value[aiIndex].content) {
			chatHistory.value[aiIndex].content = '未获取到模型回复，请稍后再试'
			scrollToBottom()
		}
	} catch (err) {
		chatHistory.value[aiIndex].content = '请求失败，请检查后端服务和模型配置'
		scrollToBottom()
	}
}

const handleAdd = () => {
	console.log('Add clicked')
}
</script>

<style scoped>
/* 整体容器 */
.chat-container {
	width: 100%;
	height: 100vh;
	display: flex;
	flex-direction: column;
	position: relative;
	background-color: #FDFBF7;
	overflow: hidden;
}

/* 初始状态：问候语部分（居中布局） */
.greeting-wrapper {
	width: 100%;
	height: 100vh;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	text-align: center;
	padding: 40rpx;
	position: absolute;
	top: 0;
	left: 0;
	z-index: 1; /* 确保在搜索栏下方，但内容可见 */
	animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
}

@keyframes fadeInUp {
	from {
		opacity: 0;
		transform: translateY(30rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.robot-hero {
	margin-bottom: 30rpx;
	display: flex;
	justify-content: center;
}

/* 机器人悬浮呼吸动画 */
.robot-hero .icon-robot-hero {
	width: 60px;
	height: 60px;
	display: block;
	/* 4秒循环，丝滑缓动 */
	animation: float 4s ease-in-out infinite;
}
.icon-robot-avatar {
	width: 32px;
	height: 32px;
	display: block;
}
.icon-search-btn {
	width: 20px;
	height: 20px;
	display: block;
}

@keyframes float {
	0% { transform: translateY(0px); }
	50% { transform: translateY(-6px); } /* 轻轻上浮 */
	100% { transform: translateY(0px); }
}

.greeting-row {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 16rpx;
	margin-bottom: 16rpx;
}

.wave-emoji {
	font-size: 56rpx;
}

.greeting-text {
	font-family: serif;
	font-size: 56rpx;
	font-weight: bold;
	color: #1D1D1F;
}

.weather-row {
	margin-top: 40rpx;
	margin-bottom: 200rpx; /* 增加底部间距，确保与搜索栏有足够空间 */
	display: flex;
	align-items: center;
	justify-content: center;
	white-space: nowrap; /* 核心：强制一行 */
}

.weather-info {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: serif; 
	letter-spacing: 0.5px;
}

.weather-divider {
	font-size: 24rpx;
	color: #AAA; 
	margin: 0 15rpx; /* 核心：这里控制 | 左右的间隔大小 */
	position: relative;
}

/* 加载指示器 */
.loading-indicator {
	display: flex;
	align-items: center;
	gap: 16rpx;
	padding: 20rpx 0;
}

.loading-dot {
	width: 12rpx;
	height: 12rpx;
	border-radius: 50%;
	background-color: #9D8B70;
	animation: loading-bounce 1.4s ease-in-out infinite;
}

.loading-dot:nth-child(1) {
	animation-delay: 0s;
}

.loading-dot:nth-child(2) {
	animation-delay: 0.2s;
}

.loading-dot:nth-child(3) {
	animation-delay: 0.4s;
}

@keyframes loading-bounce {
	0%, 80%, 100% {
		transform: scale(0.8);
		opacity: 0.5;
	}
	40% {
		transform: scale(1.2);
		opacity: 1;
	}
}

/* 聊天状态：scroll-view 区域 */
.chat-scroll-area {
	width: 100%;
	height: 100vh;
	flex: 1;
	overflow-y: auto;
}

.message-list {
	width: 100%;
	padding: 40rpx;
	display: flex;
	flex-direction: column;
	min-height: 100%;
	/* 确保消息列表区域文本可被选择 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

.spacer {
	height: 200rpx; /* 为底部输入框留出空间 */
}

/* 对话气泡 - 左右分栏布局 */
.message-row {
	display: flex;
	width: 100%;
	margin-bottom: 60rpx;
}

/* 用户消息 (右侧) */
.message-row.user {
	justify-content: flex-end;
}

.user-bubble {
	background-color: #F2F2F2;
	padding: 24rpx 40rpx;
	border-radius: 40rpx;
	border-bottom-right-radius: 4rpx; /* 小尾巴效果 */
	max-width: 70%;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
	/* 确保用户消息文本可被选择 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

.message-text {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
	line-height: 1.6;
	word-wrap: break-word;
	/* 确保文本可被选择和复制 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* AI 消息 (左侧) */
.message-row.ai {
	justify-content: flex-start;
}

.ai-container {
	display: flex;
	gap: 24rpx;
	max-width: 85%;
	align-items: flex-start;
}

.ai-avatar {
	width: 60rpx;
	height: 60rpx;
	background: #EAE5D9;
	border-radius: 50%;
	flex-shrink: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 2rpx solid #1D1D1F;
}

.ai-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	/* 确保整个 AI 内容区域文本可被选择 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* AI 列表样式 */
.ai-list {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	margin-top: 8rpx;
}

.ai-list-item {
	display: flex;
	align-items: flex-start;
	gap: 12rpx;
}

.list-bullet {
	font-size: 32rpx;
	color: #9D8B70;
	flex-shrink: 0;
	line-height: 1.4;
}

.list-text {
	font-size: 28rpx;
	color: #1D1D1F;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
	line-height: 1.6;
	flex: 1;
	/* 确保文本可被选择和复制 */
	user-select: text;
	-webkit-user-select: text;
	-moz-user-select: text;
	-ms-user-select: text;
}

/* AI 图片组样式 */
.ai-image-group {
	display: flex;
	gap: 16rpx;
	margin-top: 16rpx;
	flex-wrap: wrap;
}

.rec-img {
	width: 200rpx;
	height: 260rpx;
	border-radius: 12rpx;
	background-color: #EEE;
	border: 2rpx solid #E5E5EA;
	object-fit: cover;
}

/* 搜索栏 - 核心动画：从居中到底部 */
.input-container {
	width: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	
	position: absolute;
	top: 60%; /* 稍微下移，给天气信息留出更多空间 */
	left: 50%;
	transform: translate(-50%, -50%); /* 居中 */
	
	/* 关键：添加 0.6s 的平滑过渡 */
	transition: all 0.6s cubic-bezier(0.25, 1, 0.5, 1);
	z-index: 10; /* 降低 z-index，避免遮挡天气信息 */
}

/* 激活状态：固定在底部 */
.input-container.fixed-bottom {
	top: unset;      /* 取消 top 定位 */
	bottom: 40rpx;   /* 距离底部 40rpx */
	transform: translate(-50%, 0); /* 保持水平居中，取消垂直偏移 */
}

/* 搜索条保持原有长度，不随容器变宽 */
.search-bar {
	width: 1400rpx; 
	max-width: 90%; 
	height: 100rpx;
	justify-content: space-between;
	background-color: #FFFFFF;
	border-radius: 50rpx;
	display: flex;
	align-items: center;
	padding: 0 16rpx 0 32rpx;
	border: 2rpx solid #1D1D1F; 
	box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08); 
	transition: all 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.search-bar:focus-within {
	/* 模拟光晕扩散 */
	box-shadow: 0 10rpx 40rpx rgba(0, 0, 0, 0.15);
	border-color: #8C7B60; /* 边框变色为主题色 */
	transform: scale(1.022); /* 极其轻微的放大，产生"提起来"的感觉 */
}

.search-icon-left {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	background-color: transparent;
	display: flex;
	flex-shrink: 0;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: all 0.2s ease;
	margin-right: 20rpx;
	position: relative;
	left: -10rpx;
}

.search-icon-left:hover {
	background-color: #1D1D1F;
}

.search-icon-left:hover .icon-search-btn {
	opacity: 0.85;
}

.search-input {
	flex: 1;
	height: 100%;
	padding: 0;
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: SF Pro Display;
	line-height: 100rpx;
	border: none;
	outline: none;
}

.search-placeholder {
	color: #999;
	font-weight: 300;
	font-family: serif; 
}

.search-button {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	background-color: transparent; /* 图片里按钮背景是透明的，边框是外围的 */
	border: 1px solid #1D1D1F; /* 按钮自带圆圈边框 */
	display: flex;
	flex-shrink: 0;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: all 0.2s ease;
}

.search-button:hover {
	background-color: #1D1D1F;
}
/* hover 时箭头变白 */
.search-button:hover .icon-search-btn {
	opacity: 0.85;
}

/* 底部标签 - 使用分割线设计 */
.search-tabs {
	position: absolute;
	bottom: 620rpx; /* 调整底部位置，减小与搜索框的间隔 */
	left: 50%;
	transform: translateX(-50%);
	z-index: 10;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 24rpx;
	transition: opacity 0.3s ease;
}

.tab-text {
	font-size: 26rpx;
	color: #A0A0A0; /* 未选中灰色 */
	cursor: pointer;
	font-family: "Didot", serif;
	font-weight: 600;
	transition: color 0.2s;
}

.tab-text.active {
	color: #8C7B60; /* 激活时是深灰褐色 (Wardrobe) */
	text-decoration: underline;
	text-decoration-color: #DDD; /* 模拟图片的下划线效果 */
	text-underline-offset: 4px;
}

/* 垂直分割线 */
.tab-divider {
	width: 1px;
	height: 24rpx;
	background-color: #D1D1D1;
}
</style>
