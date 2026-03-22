<template>
	<view class="recommend-card">
		<view class="card-header">
			<view class="header-left">
				<view class="title-icon">✨</view>
				<text class="title-text">{{ formatRecommendationDisplay(recommendation.title) || 'Outfit Recommendation' }}</text>
			</view>
		</view>

		<view class="outfit-gallery" v-if="recommendation.images && recommendation.images.length > 0">
			<scroll-view scroll-x class="gallery-scroll" :show-scrollbar="false">
				<view class="gallery-inner">
					<view
						v-for="(img, idx) in recommendation.images"
						:key="idx"
						class="gallery-item"
						@click.stop="$emit('preview-images', recommendation.images, idx)"
					>
						<image :src="img" mode="aspectFill" class="gallery-image" />
					</view>
				</view>
			</scroll-view>
		</view>

		<view v-if="recommendation.content" class="message-text rich-text ai-fade-block" v-html="formattedContent"></view>

		<view v-if="recommendation.scenario" class="scenario-line ai-fade-block">{{ formatRecommendationDisplay(recommendation.scenario) }}</view>
		<view v-if="recommendation.strategy" class="strategy-line ai-fade-block">{{ formatRecommendationDisplay(recommendation.strategy) }}</view>

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
				<text class="caution-text">{{ formatRecommendationDisplay(caution) }}</text>
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
					<view class="item-thumb" @click.stop="item.image && $emit('preview-images', [item.image], 0)">
						<image v-if="item.image" :src="item.image" mode="aspectFill" class="thumb-img" />
						<view v-else-if="item.isUploaded" class="thumb-placeholder uploaded-placeholder">
							<text class="icon-emoji">📷</text>
						</view>
						<view v-else class="thumb-placeholder">
							<text class="icon-emoji">👗</text>
						</view>
					</view>

					<view class="item-info-col">
						<view class="item-header">
							<text class="item-category">{{ getEnglishCategory(item.type) }}</text>
							<text class="item-name">{{ cleanName(item.name) }}</text>
						</view>
						<text v-if="item.subtitle" class="item-subtitle">{{ formatRecommendationDisplay(item.subtitle) }}</text>
						<text v-if="item.reason || item.comment" class="item-desc">{{ formatRecommendationDisplay(item.reason || item.comment) }}</text>
						<view v-if="item.tags && item.tags.length" class="item-tags">
							<text v-for="(t, ti) in item.tags" :key="ti" class="item-tag">{{ formatRecommendationDisplay(t) }}</text>
						</view>
					</view>

					<view class="item-tryon-wrap" @click.stop>
						<view
							class="btn-item-tryon"
							:class="{ 'btn-item-tryon--muted': !tryOnImageUrl(item) }"
							@click="onVirtualTryOn(item)"
						>
							<image src="/static/icons/icon-tryon.svg" mode="aspectFit" class="btn-item-tryon-icon" />
							<text class="btn-item-tryon-text">Virtual Try-On</text>
						</view>
					</view>

					<text v-if="item.details" class="item-expand-icon">{{ expanded[itemIndex] ? '▲' : '▼' }}</text>
				</view>

				<view v-if="item.details && expanded[itemIndex]" class="item-details">
					<text class="item-details-text">{{ formatRecommendationDisplay(item.details) }}</text>
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
				<text class="why-text">{{ formatRecommendationDisplay(line) }}</text>
			</view>
		</view>

		<view
			v-if="recommendation.alternatives && recommendation.alternatives.length > 0"
			class="alternatives-section ai-fade-block"
			style="animation-delay: 0.55s"
		>
			<text class="section-title">Alternatives</text>
			<view v-for="(alt, ai) in recommendation.alternatives" :key="ai" class="alt-item">
				<text class="alt-bullet">→</text>
				<text class="alt-text">{{ cleanAltText(alt) }}</text>
			</view>
		</view>

		<view v-if="recommendation.footer" class="card-footer-text ai-fade-block" style="animation-delay: 0.65s">
			<text>{{ formatRecommendationDisplay(recommendation.footer) }}</text>
		</view>

		<view
			v-if="hasOutfitItems || showRegenerate"
			class="card-footer-actions ai-fade-block"
			style="animation-delay: 0.6s"
		>
			<view v-if="hasOutfitItems" class="footer-actions-left">
				<view class="btn-footer-secondary" @click.stop="emit('add-to-calendar', recommendation)">
					<text class="btn-footer-text">Add to Calendar</text>
				</view>
				<view class="btn-footer-secondary" @click.stop="emit('full-outfit-try-on', recommendation)">
					<text class="btn-footer-text">Full Outfit Try-On</text>
				</view>
			</view>
			<view v-if="showRegenerate" class="footer-actions-right">
				<view class="btn-regenerate" @click.stop="emit('regenerate')">
					<text class="btn-regenerate-text">Regenerate Look</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'
import { formatRecommendationDisplay } from '../utils/rec/textDisplay.js'

const props = defineProps({
	recommendation: {
		type: Object,
		required: true,
		default: () => ({})
	},
	showRegenerate: { type: Boolean, default: true },
	/** 后端判定语言，用于展示细节（如标题 i18n） */
	locale: { type: String, default: 'en' }
})

const expanded = reactive({})

const displayTags = computed(() => {
	const r = props.recommendation || {}
	const set = new Set()
	if (r.title) set.add(formatRecommendationDisplay(r.title))
	;(r.styleTags || []).forEach(t => set.add(formatRecommendationDisplay(t)))
	if (r.temperature) set.add(formatRecommendationDisplay(r.temperature))
	return [...set].filter(Boolean)
})

/** 诊断/纯文字卡无 items 时不显示日历与全身试穿，避免误触 */
const hasOutfitItems = computed(() =>
	Array.isArray(props.recommendation?.items) && props.recommendation.items.length > 0
)

const emit = defineEmits(['regenerate', 'preview-images', 'virtual-try-on', 'add-to-calendar', 'full-outfit-try-on'])

const tryOnImageUrl = (item) => {
	if (!item || typeof item !== 'object') return ''
	if (item.image) return String(item.image)
	const arr = item.images
	if (Array.isArray(arr) && arr[0]) return String(arr[0])
	return ''
}

const onVirtualTryOn = (item) => {
	const url = tryOnImageUrl(item)
	if (!url) {
		uni.showToast({ title: 'No image for this item — try-on needs a photo.', icon: 'none' })
		return
	}
	emit('virtual-try-on', { ...item, image: url })
}

const toggleExpand = (itemIndex) => {
	expanded[itemIndex] = !expanded[itemIndex]
}

const cleanName = (name) => {
	if (!name) return ''
	const n = String(name)
		.replace(/[（(][^）)]+[）)]/g, '')
		.replace(/\s*\+\s*/g, ' + ')
		.replace(/\s{2,}/g, ' ')
		.trim()
	return formatRecommendationDisplay(n)
}

const cleanAltText = (s) => {
	if (!s || typeof s !== 'string') return ''
	const n = s
		.replace(/^[-*]\s*/, '')
		.replace(/\s*[\(（]\s*id\s*[:：]\s*\d+\s*[\)）]/gi, '')
		.trim()
	return formatRecommendationDisplay(n)
}

const getEnglishCategory = (type) => {
	const t = String(type || '').toUpperCase()
	if (t.includes('TOP') || t.includes('上衣')) return 'TOP'
	if (t.includes('BOTTOM') || t.includes('下装') || t.includes('裤')) return 'BOTTOM'
	if (t.includes('DRESS') || t.includes('连衣') || t.includes('裙')) return 'DRESS'
	if (t.includes('OUTER') || t.includes('外套') || t.includes('大衣') || t.includes('夹克')) return 'OUTERWEAR'
	if (t.includes('FOOT') || t.includes('SHOE') || t.includes('鞋')) return 'FOOTWEAR'
	if (t.includes('ACCESS') || t.includes('配饰') || t.includes('饰品') || t.includes('帽') || t.includes('防护')) return 'ACCESSORY'
	if (t.includes('BAG') || t.includes('包')) return 'BAG'
	if (t.includes('UNDER') || t.includes('内衣')) return 'UNDERWEAR'
	return 'OTHER'
}

const formattedContent = computed(() => {
	let text = props.recommendation?.content
	if (!text || typeof text !== 'string') return ''

	text = formatRecommendationDisplay(text)
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
	box-shadow: 0 16rpx 60rpx rgba(0, 0, 0, 0.05);
	border: 1px solid rgba(255, 255, 255, 0.9);
	width: 100%;
	box-sizing: border-box;
}

/* --- 画廊样式 --- */
.card-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 16rpx;
}
.header-left {
	display: flex;
	align-items: center;
	gap: 12rpx;
}
.title-icon {
	width: 44rpx;
	height: 44rpx;
	border-radius: 50%;
	background: #F7F4EE;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
}
.title-text {
	font-size: 32rpx;
	font-weight: 700;
	color: #1D1D1F;
	font-family: "Didot", serif;
}

.outfit-gallery {
	margin: 24rpx -32rpx 32rpx;
}
.gallery-scroll {
	width: 100%;
}
.gallery-inner {
	display: flex;
	gap: 20rpx;
	padding: 0 32rpx;
}
.gallery-item {
	width: 150rpx;
	height: 190rpx;
	flex-shrink: 0;
	border-radius: 16rpx;
	overflow: hidden;
	background: #F9F8F6;
	border: 1px solid rgba(0, 0, 0, 0.03);
	box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.02);
}
.gallery-image {
	width: 100%;
	height: 100%;
}

/* --- 正文与标签 --- */
.message-text {
	font-size: 30rpx;
	color: #2C2C2E;
	font-family: "PingFang SC", -apple-system, sans-serif;
	font-weight: 400;
	line-height: 1.7;
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
	margin-top: 32rpx;
}

.tag {
	display: inline-block;
	background: #F7F4EE;
	padding: 12rpx 28rpx;
	border-radius: 40rpx;
	font-size: 24rpx;
	color: #6B6B6B;
	font-weight: 500;
	font-family: "PingFang SC", sans-serif;
}

.tag-temp {
	background: #F0F4F6;
	color: #5A8B99;
}

.scenario-line,
.strategy-line {
	font-size: 28rpx;
	color: #6B6B6B;
	line-height: 1.25;
	margin-top: 16rpx;
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
	background: rgba(200, 60, 50, 0.05);
	border: 1px solid rgba(200, 60, 50, 0.15);
	border-radius: 20rpx;
	padding: 20rpx 24rpx;
}

.caution-icon {
	flex-shrink: 0;
	width: 36rpx;
	height: 36rpx;
	line-height: 36rpx;
	text-align: center;
	background: rgba(200, 60, 50, 0.15);
	color: #C83C32;
	font-size: 24rpx;
	font-weight: 700;
	border-radius: 50%;
}

.caution-text {
	font-size: 28rpx;
	color: #8B2E26;
	line-height: 1.5;
	flex: 1;
}

/* --- 列表单品带微缩图的布局 (本次优化的核心区域) --- */
.outfit-list {
	margin-top: 40rpx;
	border-top: 1px solid rgba(0, 0, 0, 0.04);
}

.item-block {
	padding: 32rpx 0;
	border-bottom: 1px solid rgba(0, 0, 0, 0.04);
	transition: background 0.3s ease;
}

.item-block-expandable {
	cursor: pointer;
}

.item-block:last-child {
	border-bottom: none;
}

.item-block-main {
	display: flex;
	align-items: flex-start;
	gap: 24rpx;
}

.item-thumb {
	width: 100rpx;
	height: 100rpx;
	flex-shrink: 0;
	border-radius: 16rpx;
	overflow: hidden;
	background: #F9F8F6;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 1px solid rgba(0, 0, 0, 0.05);
}
.thumb-img {
	width: 100%;
	height: 100%;
}
.thumb-placeholder {
	font-size: 40rpx;
	color: #BBAF9E;
}
.uploaded-placeholder {
	background: #EAE6DF;
}

.item-info-col {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	justify-content: center;
	min-height: 100rpx;
}
.item-header {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 16rpx;
}

.item-category {
	font-size: 24rpx;
	font-weight: 700;
	color: #9D8B70;
	text-transform: uppercase;
	letter-spacing: 0.1em;
	flex-shrink: 0;
	font-family: "Didot", serif;
	display: flex;
	align-items: center;
}

.item-category::after {
	content: '';
	display: inline-block;
	width: 2rpx;
	height: 22rpx;
	background-color: rgba(157, 139, 112, 0.4);
	margin-left: 18rpx;
}

.item-name {
	font-size: 28rpx;
	font-weight: 500;
	color: #1D1D1F;
	font-family: "Didot", serif;
	letter-spacing: 0.02em;
	flex: 1;
}

.item-subtitle {
	font-size: 24rpx;
	color: #888;
	line-height: 1.5;
	margin-top: 4rpx;
}

.item-desc {
	font-size: 27rpx;
	color: #888;
	line-height: 1.5;
}

.item-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 10rpx;
	margin-top: 8rpx;
}

.item-tag {
	font-size: 22rpx;
	color: #9D8B70;
	background: rgba(157, 139, 112, 0.08);
	padding: 4rpx 16rpx;
	border-radius: 20rpx;
}

.item-tryon-wrap {
	flex-shrink: 0;
	align-self: flex-start;
	margin-top: 4rpx;
}

.btn-item-tryon {
	display: flex;
	align-items: center;
	gap: 8rpx;
	padding: 12rpx 20rpx;
	border-radius: 999rpx;
	background: #F0E6D8;
	border: 1rpx solid rgba(157, 139, 112, 0.25);
	transition: opacity 0.18s ease, transform 0.18s ease;
	/* H5：<text> 默认可选字，光标会变成直线 I；按钮应为手形且不可选字 */
	cursor: pointer;
	user-select: none;
	-webkit-user-select: none;
}

.btn-item-tryon:active {
	opacity: 0.88;
	transform: scale(0.97);
}

.btn-item-tryon--muted {
	opacity: 0.45;
}

.btn-item-tryon-icon {
	width: 28rpx;
	height: 28rpx;
	flex-shrink: 0;
}

.btn-item-tryon-text {
	font-size: 22rpx;
	font-weight: 600;
	color: #5a4b35;
	white-space: nowrap;
	user-select: none;
	-webkit-user-select: none;
}

.item-expand-icon {
	font-size: 20rpx;
	color: #D1C8B8;
	flex-shrink: 0;
	margin-top: 10rpx;
}

.item-details {
	margin-top: 24rpx;
	padding-top: 24rpx;
	border-top: 1px dashed rgba(0,0,0,0.08);
}

.item-details-text {
	font-size: 26rpx;
	color: #6B6B6B;
	line-height: 1.6;
}

/* --- 下方分析区块（Why this works / Alternatives 标题与正文字号、字体在此改）--- */
.why-this-works {
	margin-top: 40rpx;
	padding: 32rpx 0 16rpx;
	border-top: 1px solid rgba(0,0,0,0.04);
}

.why-title {
	font-size: 30rpx;
	font-weight: 800;
	color: #1D1D1F;
	display: block;
	margin-bottom: 24rpx;
	font-family: "Didot", serif;
	letter-spacing: 0.03em;
}

.why-item {
	display: flex;
	gap: 16rpx;
	margin-bottom: 16rpx;
}

.why-bullet {
	font-size: 24rpx;
	color: #9D8B70;
	flex-shrink: 0;
	line-height: 1.6;
}

.why-text {
	font-size: 26rpx;
	font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
	font-weight: 600;
	color: #4A4A4A;
	line-height: 1.6;
}

.alternatives-section {
	margin-top: 40rpx;
	padding: 32rpx 36rpx;
	background: linear-gradient(180deg, rgba(157, 139, 112, 0.06) 0%, rgba(157, 139, 112, 0.02) 100%);
	border-radius: 24rpx;
	border: 1px solid rgba(157, 139, 112, 0.1);
}

.section-title {
	font-size: 30rpx;
	font-weight: 800;
	color: #1D1D1F;
	display: block;
	margin-bottom: 24rpx;
	font-family: "Didot", serif;
	letter-spacing: 0.03em;
}

.alt-item {
	display: flex;
	gap: 16rpx;
	margin-bottom: 16rpx;
}

.alt-item:last-child {
	margin-bottom: 0;
}

.alt-bullet {
	color: #9D8B70;
	font-weight: 400;
	font-family: "Didot", serif;
}

.alt-text {
	font-size: 24rpx;
	font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
	font-weight: 600;
	color: #4A4A4A;
	line-height: 2;
}

.card-footer-text {
	margin-top: 48rpx;
	padding-top: 32rpx;
	border-top: 1px solid rgba(0,0,0,0.04);
	font-size: 26rpx;
	color: #888;
	font-style: italic;
	line-height: 1.6;
	text-align: center;
	font-family: serif;
}

/* --- Footer actions: Add to Calendar | Full Outfit Try-On | Regenerate --- */
.card-footer-actions {
	margin-top: 48rpx;
	display: flex;
	flex-direction: row;
	align-items: center;
	justify-content: space-between;
	flex-wrap: wrap;
	gap: 20rpx;
}

.footer-actions-left {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 16rpx;
	flex: 1;
	min-width: 0;
}

.footer-actions-right {
	flex-shrink: 0;
	margin-left: auto;
}

.btn-footer-secondary {
	padding: 20rpx 32rpx;
	background: #FAF8F4;
	border: 1px solid rgba(157, 139, 112, 0.4);
	border-radius: 50rpx;
	text-align: center;
	cursor: pointer;
	transition: opacity 0.2s ease, transform 0.2s ease;
	box-shadow: 0 4rpx 12rpx rgba(157, 139, 112, 0.06);
	user-select: none;
	-webkit-user-select: none;
}

.btn-footer-secondary:active {
	opacity: 0.88;
	transform: scale(0.98);
}

.btn-footer-text {
	font-size: 24rpx;
	color: #5a4b35;
	font-weight: 600;
	letter-spacing: 0.02em;
}

.btn-regenerate {
	padding: 24rpx 48rpx;
	background: #FFFFFF;
	border: 1px solid #9D8B70;
	border-radius: 50rpx;
	text-align: center;
	cursor: pointer;
	transition: all 0.3s ease;
	box-shadow: 0 4rpx 12rpx rgba(157, 139, 112, 0.1);
}

.btn-regenerate:hover {
	background: #FDFBF7;
	transform: translateY(-2rpx);
	box-shadow: 0 8rpx 20rpx rgba(157, 139, 112, 0.15);
}

.btn-regenerate:active {
	transform: translateY(0);
}

.btn-regenerate-text {
	font-size: 26rpx;
	color: #9D8B70;
	font-weight: 600;
	letter-spacing: 0.04em;
}
</style>
