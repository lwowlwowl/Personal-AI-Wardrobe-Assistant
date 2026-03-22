<template>
	<view class="chat-bubble ai-fade-block">
		<view class="message-text rich-text" v-html="formattedContent"></view>
	</view>
</template>

<script setup>
import { computed } from 'vue'
import { formatRecommendationDisplay } from '../utils/rec/textDisplay.js'

const props = defineProps({
	content: { type: String, default: '' },
	/** 与推荐卡片一致：去 # 编号 + 中英边界加两格 */
	stripWardrobeHashIds: { type: Boolean, default: false }
})

const normalizedText = computed(() => {
	if (!props.content || typeof props.content !== 'string') return ''
	let t = props.content
		.replace(/\r\n/g, '\n')
		.replace(/\n{3,}/g, '\n\n')
		.trim()
	if (props.stripWardrobeHashIds) {
		t = formatRecommendationDisplay(t)
	}
	return t
})

function escapeHtml(text) {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
}

function enrichInline(text) {
	return text
		.replace(/\*\*([^*]+)\*\*/g, '<span class="highlight-text">$1</span>')
		.replace(/`([^`]+)`/g, '<span class="inline-code">$1</span>')
}

function renderParagraph(paragraph) {
	const t = paragraph.trim()
	if (!t) return ''

	const lines = t.split('\n').map(line => line.trim()).filter(Boolean)

	const allBullets = lines.length > 1 && lines.every(line => /^[-*•]\s+/.test(line))
	if (allBullets) {
		const items = lines
			.map(line => line.replace(/^[-*•]\s+/, ''))
			.map(line => `<view class="list-bullet"><span class="bullet-dot">•</span><span>${enrichInline(line)}</span></view>`)
			.join('')
		return `<div class="paragraph-group bullet-group">${items}</div>`
	}

	const questionLike = /[？?]$/.test(t) || /^你是否|^你愿意|^要不要|^可以先/i.test(t)
	if (questionLike) {
		return `<div class="paragraph-group question-block">${enrichInline(t)}</div>`
	}

	const hintLike = /^(例如|比如|你可以|我可以|建议|温馨提示|提示|注意)/.test(t)
	if (hintLike) {
		return `<div class="paragraph-group hint-block">${enrichInline(t)}</div>`
	}

	return `<div class="paragraph-group">${enrichInline(t).replace(/\n/g, '<br>')}</div>`
}

const formattedContent = computed(() => {
	const text = normalizedText.value
	if (!text) return ''

	const safe = escapeHtml(text)
	const paragraphs = safe.split(/\n{2,}/).filter(Boolean)
	return paragraphs.map(renderParagraph).join('')
})
</script>

<style scoped>
.chat-bubble {
	position: relative;
	background: #FFFFFF;
	border-radius: 16rpx 30rpx 30rpx 30rpx;
	padding: 30rpx 34rpx;
	box-shadow: 0 8rpx 28rpx rgba(0, 0, 0, 0.04);
	width: 100%;
	max-width: 100%;
	border: 1px solid rgba(0, 0, 0, 0.04);
	box-sizing: border-box;
}

.message-text {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Microsoft YaHei", sans-serif;
	font-weight: 400;
	line-height: 1.72;
	letter-spacing: 0.02em;
	word-break: break-word;
	user-select: text;
	-webkit-user-select: text;
}

.rich-text {
	font-size: 30rpx;
	color: #2C2C2E;
	line-height: 1.72;
}

:deep(.paragraph-group) {
	margin-bottom: 18rpx;
}

:deep(.paragraph-group:last-child) {
	margin-bottom: 0;
}

:deep(.question-block) {
	background: transparent;
	border: none;
	border-radius: 0;
	padding: 4rpx 0 4rpx 24rpx;
	border-left: 6rpx solid rgba(157, 139, 112, 0.4);
	color: #1D1D1F;
	font-weight: 500;
	margin-top: 16rpx;
}

:deep(.hint-block) {
	background: transparent;
	border: none;
	border-radius: 0;
	padding: 4rpx 0 4rpx 24rpx;
	border-left: 6rpx solid rgba(52, 199, 89, 0.4);
	margin-top: 16rpx;
}

:deep(.bullet-group) {
	padding-left: 4rpx;
}

:deep(.list-bullet) {
	display: flex;
	align-items: flex-start;
	margin-top: 10rpx;
	margin-bottom: 10rpx;
}

:deep(.bullet-dot) {
	color: #9D8B70;
	margin-right: 14rpx;
	font-size: 30rpx;
	line-height: 1.5;
	flex-shrink: 0;
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

:deep(.inline-code) {
	display: inline-block;
	padding: 2rpx 10rpx;
	border-radius: 10rpx;
	background: rgba(0, 0, 0, 0.05);
	font-size: 0.92em;
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

