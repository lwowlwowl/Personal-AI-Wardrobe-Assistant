<!-- 纯聊天气泡：情感安抚、日常闲聊等无穿搭方案的大段文本，收缩宽度 + 富文本 -->
<template>
	<view class="chat-bubble ai-fade-block">
		<view class="message-text rich-text" v-html="formattedContent"></view>
	</view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
	content: { type: String, default: '' }
})

// 简易 Markdown -> HTML（加粗、列表、换行），用于富文本展示
const formattedContent = computed(() => {
	let text = props.content
	if (!text || typeof text !== 'string') return ''
	text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
	text = text.replace(/\*\*([^*]+)\*\*/g, '<span class="highlight-text">$1</span>')
	text = text.replace(/^[-*]\s+(.+)$/gm, '<p class="list-bullet"><span class="bullet-dot">•</span>$1</p>')
	text = text.replace(/\n\n/g, '<div class="paragraph-spacer"></div>')
	text = text.replace(/\n/g, '<br>')
	return text
})
</script>

<style scoped>
.chat-bubble {
	position: relative;
	background: #FFFFFF;
	border-radius: 12rpx 32rpx 32rpx 32rpx;
	padding: 32rpx 40rpx;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.03);
	max-width: 90%;
	border: 1px solid rgba(0, 0, 0, 0.03);
	box-sizing: border-box;
}

.message-text {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Microsoft YaHei", sans-serif;
	font-weight: 400;
	line-height: 1.65;
	letter-spacing: 0.02em;
	word-wrap: break-word;
	user-select: text;
	-webkit-user-select: text;
}

.rich-text {
	font-size: 30rpx;
	color: #2C2C2E;
	line-height: 1.7;
}
.chat-bubble .rich-text::first-line {
	letter-spacing: 0.06em;
}

:deep(.highlight-text) {
	font-weight: 600;
	color: #1D1D1F;
	background: linear-gradient(120deg, rgba(157, 139, 112, 0.2) 0%, rgba(157, 139, 112, 0) 100%);
	background-repeat: no-repeat;
	background-size: 100% 40%;
	background-position: 0 88%;
	padding: 0 4rpx;
}
:deep(.list-bullet) {
	display: flex;
	margin-top: 12rpx;
	margin-bottom: 12rpx;
	padding-left: 12rpx;
}
:deep(.bullet-dot) {
	color: #9D8B70;
	margin-right: 16rpx;
	font-size: 32rpx;
	line-height: 1.5;
}
:deep(.paragraph-spacer) {
	height: 24rpx;
}

.ai-fade-block {
	opacity: 0;
	animation: chatBubbleFade 0.4s ease-out forwards;
}
@keyframes chatBubbleFade {
	from { opacity: 0; transform: translateY(10rpx); }
	to { opacity: 1; transform: translateY(0); }
}
</style>
