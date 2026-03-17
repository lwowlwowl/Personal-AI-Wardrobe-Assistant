<template>
	<view class="recommend-card">
		<view v-if="recommendation.content" class="message-text rich-text ai-fade-block" v-html="formattedContent"></view>

		<view v-if="displayTags.length > 0" class="tag-row ai-fade-block" style="animation-delay: 0.15s">
			<text
				v-for="(tag, ti) in displayTags"
				:key="ti"
				class="tag"
				:class="{ 'tag-temp': tag === recommendation.temperature }"
			>
				{{ tag }}
			</text>
		</view>

		<view
			v-if="recommendation.cautions && recommendation.cautions.length > 0"
			class="cautions-wrap ai-fade-block"
			style="animation-delay: 0.18s"
		>
			<view v-for="(caution, ci) in recommendation.cautions" :key="ci" class="caution-chip">
				<text class="caution-icon">!</text>
				<text class="caution-text">{{ caution }}</text>
			</view>
		</view>

		<view v-if="recommendation.items && recommendation.items.length > 0" class="outfit-list">
			<view
				v-for="(item, itemIndex) in recommendation.items"
				:key="itemIndex"
				class="item-block ai-fade-block"
				:class="{ 'item-block-expandable': item.details }"
				:style="{ animationDelay: (0.2 + itemIndex * 0.08) + 's' }"
				@click="item.details && toggleExpand(itemIndex)"
			>
				<view class="item-block-main">
					<text class="item-category">{{ item.type }}</text>
					<view class="item-info">
						<text class="item-name">{{ item.name }}</text>
						<text v-if="item.subtitle" class="item-subtitle">{{ item.subtitle }}</text>
						<text v-if="item.reason" class="item-desc">{{ item.reason }}</text>
						<view v-if="item.tags && item.tags.length" class="item-tags">
							<text v-for="(t, ti) in item.tags" :key="ti" class="item-tag">{{ t }}</text>
						</view>
					</view>
					<text v-if="item.details" class="item-expand-icon">{{ expanded[itemIndex] ? '▲' : '▼' }}</text>
				</view>

				<view v-if="item.details && expanded[itemIndex]" class="item-details">
					<text class="item-details-text">{{ item.details }}</text>
				</view>
			</view>
		</view>

		<view
			v-if="recommendation.whyThisWorks && recommendation.whyThisWorks.length > 0"
			class="why-this-works ai-fade-block"
			style="animation-delay: 0.5s"
		>
			<text class="why-title">Why this works</text>
			<view v-for="(line, wi) in recommendation.whyThisWorks" :key="wi" class="why-item">
				<text class="why-bullet">•</text>
				<text class="why-text">{{ line }}</text>
			</view>
		</view>

		<view
			v-if="recommendation.images && recommendation.images.length > 0"
			class="image-row ai-fade-block"
			style="animation-delay: 0.55s"
		>
			<image
				v-for="(img, imgIndex) in recommendation.images"
				:key="imgIndex"
				:src="img"
				mode="aspectFill"
				class="rec-img-grid"
				@click="$emit('preview-images', recommendation.images, imgIndex)"
			/>
		</view>

		<view v-if="showRegenerate" class="regenerate-row ai-fade-block" style="animation-delay: 0.6s">
			<view class="btn-regenerate" @click="$emit('regenerate')">
				<text class="btn-regenerate-text">Regenerate Look</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'

const props = defineProps({
	recommendation: {
		type: Object,
		required: true,
		default: () => ({})
	},
	showRegenerate: { type: Boolean, default: true }
})

defineEmits(['regenerate', 'preview-images'])

const expanded = reactive({})

const displayTags = computed(() => {
	const r = props.recommendation || {}
	const set = new Set()
	if (r.title) set.add(r.title)
	;(r.styleTags || []).forEach(t => set.add(t))
	if (r.temperature) set.add(r.temperature)
	return [...set]
})

const toggleExpand = (itemIndex) => {
	expanded[itemIndex] = !expanded[itemIndex]
}

const formattedContent = computed(() => {
	let text = props.recommendation?.content
	if (!text || typeof text !== 'string') return ''

	text = text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')

	text = text.replace(/\*\*([^*]+)\*\*/g, '<span class="highlight-text">$1</span>')
	text = text.replace(/^[-*]\s+(.+)$/gm, '<p class="list-bullet"><span class="bullet-dot">•</span>$1</p>')
	text = text.replace(/\n\n/g, '<div class="paragraph-spacer"></div>')
	text = text.replace(/\n/g, '<br>')

	return text
})

watch(
	() => props.recommendation,
	() => {
		Object.keys(expanded).forEach(k => delete expanded[k])
	},
	{ deep: true }
)
</script>

<style scoped>
.recommend-card {
	--card-bg: rgba(255, 255, 255, 0.85);
	background: var(--card-bg);
	backdrop-filter: blur(20px);
	-webkit-backdrop-filter: blur(20px);
	border-radius: 40rpx;
	padding: 56rpx;
	box-shadow: 0 16rpx 60rpx rgba(0, 0, 0, 0.06);
	border: 1px solid rgba(255, 255, 255, 0.9);
	width: 100%;
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
	animation: aiBlockFade 0.4s ease-out forwards;
}

@keyframes aiBlockFade {
	from { opacity: 0; transform: translateY(10rpx); }
	to { opacity: 1; transform: translateY(0); }
}

.tag-row {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-top: 24rpx;
}

.tag {
	display: inline-block;
	background: #f3f2ee;
	padding: 12rpx 24rpx;
	border-radius: 40rpx;
	font-size: 24rpx;
	color: #6b6b6b;
	font-family: "PingFang SC", -apple-system, sans-serif;
}

.tag-temp {
	background: #e8f4f8;
	color: #4a90a4;
}

.cautions-wrap {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	margin-top: 24rpx;
}

.caution-chip {
	display: flex;
	align-items: flex-start;
	gap: 12rpx;
	background: rgba(200, 60, 50, 0.08);
	border: 1px solid rgba(200, 60, 50, 0.25);
	border-radius: 20rpx;
	padding: 20rpx 24rpx;
}

.caution-icon {
	flex-shrink: 0;
	width: 36rpx;
	height: 36rpx;
	line-height: 36rpx;
	text-align: center;
	background: rgba(200, 60, 50, 0.2);
	color: #c83c32;
	font-size: 24rpx;
	font-weight: 700;
	border-radius: 50%;
}

.caution-text {
	font-size: 26rpx;
	color: #8b2e26;
	line-height: 1.5;
	flex: 1;
}

.outfit-list {
	margin-top: 32rpx;
}

.item-block {
	padding: 32rpx 0;
	border-bottom: 1px solid rgba(0, 0, 0, 0.06);
	transition: background 0.2s;
}

.item-block-expandable {
	cursor: pointer;
}

.item-block:last-child {
	border-bottom: none;
}

.item-block-main {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	gap: 24rpx;
}

.item-category {
	font-size: 26rpx;
	font-weight: 600;
	color: #9D8B70;
	flex-shrink: 0;
	width: 140rpx;
	font-family: "Didot", "Times New Roman", serif;
	letter-spacing: 0.04em;
}

.item-info {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.item-name {
	font-size: 30rpx;
	font-weight: 500;
	color: #1D1D1F;
	font-family: "Didot", "Times New Roman", serif;
	letter-spacing: 0.02em;
}

.item-subtitle {
	font-size: 26rpx;
	color: #5c5c5c;
	line-height: 1.5;
}

.item-desc {
	font-size: 26rpx;
	color: #6b6b6b;
	line-height: 1.5;
}

.item-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 10rpx;
	margin-top: 6rpx;
}

.item-tag {
	font-size: 22rpx;
	color: #9D8B70;
	background: rgba(157, 139, 112, 0.1);
	padding: 6rpx 16rpx;
	border-radius: 20rpx;
}

.item-expand-icon {
	font-size: 24rpx;
	color: #9D8B70;
	flex-shrink: 0;
}

.item-details {
	margin-top: 20rpx;
	padding-top: 20rpx;
	border-top: 1px dashed #eee;
}

.item-details-text {
	font-size: 26rpx;
	color: #6b6b6b;
	line-height: 1.6;
}

.why-this-works {
	margin-top: 32rpx;
	padding-top: 24rpx;
	border-top: 1px solid #f1f1f1;
}

.why-title {
	font-size: 28rpx;
	font-weight: 600;
	color: #1D1D1F;
	display: block;
	margin-bottom: 16rpx;
	font-family: "Didot", "Times New Roman", serif;
	letter-spacing: 0.03em;
}

.why-item {
	display: flex;
	gap: 12rpx;
	margin-bottom: 8rpx;
}

.why-bullet {
	font-size: 24rpx;
	color: #9D8B70;
	flex-shrink: 0;
}

.why-text {
	font-size: 26rpx;
	color: #6b6b6b;
	line-height: 1.5;
}

.image-row {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 24rpx;
	margin-top: 32rpx;
}

.rec-img-grid {
	width: 100%;
	aspect-ratio: 1;
	border-radius: 16rpx;
	background: #EEE;
	object-fit: cover;
}

.regenerate-row {
	margin-top: 40rpx;
}

.btn-regenerate {
	padding: 24rpx 48rpx;
	border: 2rpx solid #9D8B70;
	border-radius: 50rpx;
	text-align: center;
	cursor: pointer;
	transition: all 0.2s;
}

.btn-regenerate:hover {
	background: rgba(157, 139, 112, 0.08);
}

.btn-regenerate-text {
	font-size: 28rpx;
	color: #9D8B70;
	font-weight: 500;
}
</style>
