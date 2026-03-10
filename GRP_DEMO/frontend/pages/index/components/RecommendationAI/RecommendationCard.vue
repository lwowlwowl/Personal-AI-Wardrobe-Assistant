<!-- 推荐卡片：可复用、支持多套推荐与左右滑动 -->
<template>
	<view class="recommend-card">
		<text v-if="recommendation.content" class="message-text ai-fade-block">{{ recommendation.content }}</text>
		
		<!-- 风格标签：title + styleTags + temperature -->
		<view v-if="displayTags.length > 0" class="tag-row ai-fade-block" style="animation-delay: 0.15s">
			<text v-for="(tag, ti) in displayTags" :key="ti" class="tag" :class="{ 'tag-temp': tag === recommendation.temperature }">{{ tag }}</text>
		</view>
		
		<!-- 穿搭清单：v-for 渲染 -->
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
						<text class="item-desc">{{ item.reason }}</text>
					</view>
					<text v-if="item.details" class="item-expand-icon">{{ expanded[itemIndex] ? '▲' : '▼' }}</text>
				</view>
				<view v-if="item.details && expanded[itemIndex]" class="item-details">
					<text class="item-details-text">{{ item.details }}</text>
				</view>
			</view>
		</view>
		
		<!-- Why this works -->
		<view v-if="recommendation.whyThisWorks && recommendation.whyThisWorks.length > 0" class="why-this-works ai-fade-block" style="animation-delay: 0.5s">
			<text class="why-title">Why this works:</text>
			<view v-for="(line, wi) in recommendation.whyThisWorks" :key="wi" class="why-item">
				<text class="why-bullet">•</text>
				<text class="why-text">{{ line }}</text>
			</view>
		</view>
		
		<!-- 搭配拼图区：grid 三列 -->
		<view v-if="recommendation.images && recommendation.images.length > 0" class="image-row ai-fade-block" style="animation-delay: 0.55s">
			<image 
				v-for="(img, imgIndex) in recommendation.images" 
				:key="imgIndex"
				:src="img" 
				mode="aspectFill"
				class="rec-img-grid"
				@click="$emit('preview-images', recommendation.images, imgIndex)"
			/>
		</view>
		
		<!-- Regenerate Look 按钮 -->
		<view v-if="showRegenerate" class="regenerate-row ai-fade-block" style="animation-delay: 0.6s">
			<view class="btn-regenerate" @click="$emit('regenerate')">
				<text class="btn-regenerate-text">Regenerate Look</text>
			</view>
		</view>
	</view>
</template>

<script setup>
/**
 * 推荐卡片：接收 recommendation 对象，v-for 渲染
 * 结构：{ title, temperature, styleTags, items: [{ type, name, reason, details? }], content, whyThisWorks, images }
 */
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

// 合并 title、styleTags、temperature 用于展示
const displayTags = computed(() => {
	const r = props.recommendation
	const tags = []
	if (r.title) tags.push(r.title)
	if (r.styleTags?.length) tags.push(...r.styleTags)
	if (r.temperature) tags.push(r.temperature)
	return tags
})

const toggleExpand = (itemIndex) => {
	expanded[itemIndex] = !expanded[itemIndex]
}

// 当 recommendation 变化时重置展开状态
watch(() => props.recommendation, () => {
	Object.keys(expanded).forEach(k => delete expanded[k])
}, { deep: true })
</script>

<style scoped>
.recommend-card {
	background: #ffffff;
	border-radius: 40rpx;
	padding: 56rpx;
	box-shadow: 0 16rpx 60rpx rgba(0, 0, 0, 0.05);
	width: 100%;
	box-sizing: border-box;
}

.message-text {
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: "PingFang SC", -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Microsoft YaHei", sans-serif;
	font-weight: 400;
	line-height: 1.6;
	word-wrap: break-word;
	user-select: text;
	-webkit-user-select: text;
}

.ai-fade-block {
	opacity: 0;
	animation: aiBlockFade 0.4s ease-out forwards;
}

@keyframes aiBlockFade {
	from { opacity: 0; transform: translateY(6rpx); }
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

.outfit-list {
	margin-top: 32rpx;
}

.item-block {
	padding: 32rpx 0;
	border-bottom: 1px solid #f1f1f1;
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
}

.item-desc {
	font-size: 26rpx;
	color: #6b6b6b;
	line-height: 1.5;
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
	font-size: 26rpx;
	font-weight: 600;
	color: #1D1D1F;
	display: block;
	margin-bottom: 16rpx;
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
