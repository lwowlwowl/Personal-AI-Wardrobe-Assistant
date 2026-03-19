<template>
	<view v-if="plan && Array.isArray(plan.days) && plan.days.length > 0" class="plan-card" :key="rawText">
		<view class="plan-header">
			<view class="header-main">
				<text class="plan-title-en">Daily Lookbook</text>
				<view class="title-row">
					<text class="plan-title-zh">{{ planTitle }}</text>
					<view class="live-indicator" v-if="isTodayActive">
						<view class="dot"></view>
						<text>Active Now</text>
					</view>
				</view>
			</view>
		</view>

		<view v-if="planIntro" class="strategy-banner">
			<view class="banner-label">Overall Strategy</view>
			<text class="strategy-text">{{ planIntro }}</text>
		</view>

		<view v-if="days.length" class="day-scroll-container">
			<view
				v-for="(d, idx) in days"
				:key="(d.key || idx) + (rawText || '')"
				class="day-module ai-fade-block"
				:class="{ 'is-expanded': expanded[idx] }"
				:style="{ animationDelay: `${0.15 + idx * 0.1}s` }"
			>
				<view class="module-header" @click="toggle(idx)">
					<view class="date-box" v-if="d.dateText">
						<text class="date-num">{{ formatDayNum(d.dateText) }}</text>
						<view class="date-meta">
							<text class="weekday">{{ d.label }}</text>
							<text class="month">{{ formatMonth(d.dateText) }}</text>
						</view>
					</view>
					<view v-else class="date-box">
						<text class="weekday">{{ d.label || ('Day ' + (idx + 1)) }}</text>
					</view>

					<view class="header-content">
						<text v-if="d.weatherText" class="weather-brief">{{ d.weatherText }}</text>
						<text class="style-keyword" v-if="extractKeyword(d.notes)"># {{ extractKeyword(d.notes) }}</text>
					</view>

					<view class="action-btn">
						<text class="btn-text">{{ expanded[idx] ? 'Close' : 'View Detail' }}</text>
					</view>
				</view>

				<view class="item-list-wrap" :class="{ 'is-open': expanded[idx] }">
					<view class="item-list-inner">
						<view class="plan-item" v-for="(it, i) in (d.items || [])" :key="i">
							<view class="plan-item-img-wrap" v-if="it.images && it.images.length > 0" @click.stop="previewImages(it.images, 0)">
								<image :src="it.images[0]" mode="aspectFill" class="real-item-img" />
							</view>
							<view class="fallback-icon-wrap" v-else>
								<text class="type-emoji">{{ getFallbackEmoji(it.type) }}</text>
							</view>
							<view class="item-detail">
								<view class="item-header-row">
									<text class="category-name">{{ getEnglishCategory(it.type) }}</text>
									<text class="product-name">{{ cleanName(it.name) }}</text>
								</view>
								<text class="item-reason" v-if="it.reason || it.comment">{{ it.reason || it.comment }}</text>
							</view>
						</view>
						<view v-if="d.notes" class="stylist-note">
							<view class="note-top">
								<text class="note-title">Stylist Note</text>
								<image src="/static/icons/icon-pin.svg" class="pin-icon" />
							</view>
							<text class="note-content">{{ cleanNotes(d.notes) }}</text>
						</view>
					</view>
				</view>
			</view>
		</view>

		<view v-else class="fallback-wrap">
			<text class="fallback-text">{{ rawText }}</text>
		</view>
	</view>
	<view v-else class="fallback-wrap">
		<text class="fallback-text">{{ rawText || 'No schedule data.' }}</text>
	</view>
</template>

<script setup>
import { computed, reactive } from 'vue'

const props = defineProps({
	plan: { type: Object, default: null },
	rawText: { type: String, default: '' },
	/** 后端判定语言，用于展示细节（如标题 i18n） */
	locale: { type: String, default: 'en' }
})

const days = computed(() => (Array.isArray(props.plan?.days) ? props.plan.days : []))
const planTitle = computed(() => props.plan?.title || '穿搭计划')
const planIntro = computed(() => props.plan?.intro || '')
const expanded = reactive({ 0: true })

const isTodayActive = computed(() => false)

const toggle = (idx) => { expanded[idx] = !expanded[idx] }

// --- 表现形式转换逻辑 ---

const formatDayNum = (t) => {
	const m = t?.match(/\d+\.(\d+)/)
	return m ? m[1] : '•'
}

const formatMonth = (t) => {
	const m = t?.match(/(\d+)\.\d+/)
	return m ? m[1] + '月' : 'March'
}

const extractKeyword = (notes) => {
	const m = notes?.match(/关键词[：:]([^||\n]+)/)
	return m ? m[1].trim().split(' ')[0] : ''
}

const cleanNotes = (notes) => {
	if (!notes) return ''
	return String(notes)
		.replace(/关键词[：:][^||\n]+/g, '')
		.replace(/天气适配点[：:]/g, '')
		.replace(/\*\*/g, '')
		.replace(/^>\s*/gm, '')
		.replace(/✅/g, '')
		.trim()
}

const mapTypeToEnglish = (type) => {
	const map = {
		'上衣': 'TOP',
		'下装': 'BOTTOM',
		'外套': 'OUTERWEAR',
		'鞋履': 'FOOTWEAR',
		'鞋子': 'FOOTWEAR',
		'鞋': 'FOOTWEAR',
		'配饰': 'ACCESSORY',
		'饰品': 'ACCESSORY',
		'包具': 'BAG',
		'包包': 'BAG',
		'包': 'BAG',
		'连衣裙': 'DRESS',
		'裙装': 'DRESS',
		'内衣': 'UNDERWEAR',
		'其他': 'OTHER',
		Top: 'TOP',
		Bottom: 'BOTTOM',
		Dress: 'DRESS',
		Outerwear: 'OUTERWEAR',
		Footwear: 'FOOTWEAR',
		Accessory: 'ACCESSORY',
		Bag: 'BAG',
		Underwear: 'UNDERWEAR',
		Other: 'OTHER',
		// 后端 plan/recommendation 返回的 type 为大写，需直接映射
		TOP: 'TOP',
		BOTTOM: 'BOTTOM',
		DRESS: 'DRESS',
		OUTERWEAR: 'OUTERWEAR',
		FOOTWEAR: 'FOOTWEAR',
		ACCESSORY: 'ACCESSORY',
		BAG: 'BAG',
		UNDERWEAR: 'UNDERWEAR',
		OTHER: 'OTHER'
	}
	const key = typeof type === 'string' ? type.trim() : ''
	return map[key] || map[key.toUpperCase()] || (key ? key.toUpperCase() : 'OTHER')
}

const cleanName = (name) => {
	if (!name) return ''
	return String(name)
		.replace(/[（(][^）)]+[）)]/g, '')
		.replace(/\s*\+\s*/g, ' + ')
		.replace(/\s{2,}/g, ' ')
		.trim()
}

const mapTypeToEmoji = (type) => {
	const t = String(type || '').toLowerCase()
	if (t.includes('top') || type === '上衣') return '👕'
	if (t.includes('bottom') || type === '下装') return '👖'
	if (t.includes('outer') || type === '外套' || t.includes('outerwear')) return '🧥'
	if (t.includes('foot') || type === '鞋履' || type === '鞋子' || type === '鞋') return '👟'
	if (t.includes('bag') || type === '包' || type === '包包' || type === '包具') return '👜'
	if (t.includes('access') || type === '配饰' || type === '饰品') return '🧢'
	if (t.includes('dress') || type === '连衣裙') return '👗'
	if (t.includes('under') || type === '内衣') return '🩲'
	return '✨'
}

const getEnglishCategory = (type) => mapTypeToEnglish(type)
const getFallbackEmoji = (type) => mapTypeToEmoji(type)

const previewImages = (urls, startIndex = 0) => {
	if (!Array.isArray(urls) || urls.length === 0) return
	uni.previewImage({ urls, current: urls[startIndex] || urls[0] })
}
</script>

<style scoped>
.plan-card {
	background: #FDFBF7; /* 极简暖白，像纸张一样 */
	border-radius: 40rpx;
	padding: 40rpx;
	box-shadow: 0 20rpx 60rpx rgba(0,0,0,0.05);
}

/* 头部设计 */
.plan-header { margin-bottom: 40rpx; }
.plan-title-en {
	font-size: 20rpx;
	text-transform: uppercase;
	letter-spacing: 8rpx;
	color: #C4B59D;
	margin-bottom: 8rpx;
}
.title-row {
	display: flex;
	align-items: center;
	gap: 20rpx;
	margin-top: 8rpx;
}
.plan-title-zh { font-size: 48rpx; font-weight: 800; color: #1D1D1F; }

.live-indicator {
	display: flex;
	align-items: center;
	gap: 10rpx;
	background: rgba(52, 199, 89, 0.1);
	padding: 6rpx 16rpx;
	border-radius: 20rpx;
	font-size: 22rpx;
	color: #248A3D;
	font-weight: 600;
	letter-spacing: 0.02em;
}
.live-indicator .dot {
	width: 12rpx;
	height: 12rpx;
	background: #34C759;
	border-radius: 50%;
	animation: pulse-green 2s infinite cubic-bezier(0.4, 0, 0.2, 1);
}
@keyframes pulse-green {
	0% { box-shadow: 0 0 0 0 rgba(52, 199, 89, 0.4); }
	70% { box-shadow: 0 0 0 8rpx rgba(52, 199, 89, 0); }
	100% { box-shadow: 0 0 0 0 rgba(52, 199, 89, 0); }
}

/* 总体策略 Banner（深色块标题「OVERALL STRATEGY」与正文：字号、字体在此调整） */
.strategy-banner {
	background: #1D1D1F; border-radius: 24rpx; padding: 32rpx; margin-bottom: 40rpx;
	font-family: "Didot", serif;
}
.banner-label {
	color: #9D8B70; font-size: 28rpx; text-transform: uppercase;
	letter-spacing: 2rpx; margin-bottom: 14rpx; font-weight: 700;
}
.strategy-text { color: #FFF; font-size: 28rpx; line-height: 1.65; opacity: 0.95; }

/* 每天的卡片模块 */
.day-module {
	display: flex;
	flex-direction: column;
	background: #FFFFFF;
	border: 1px solid rgba(0, 0, 0, 0.04);
	border-radius: 32rpx;
	margin-bottom: 24rpx;
	padding: 24rpx 32rpx;
	transition: all 0.3s ease;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.02);
}
.day-module.is-expanded {
	background: #FCFBFA;
	border-color: rgba(157, 139, 112, 0.15);
	box-shadow: 0 8rpx 32rpx rgba(157, 139, 112, 0.06);
	padding-bottom: 32rpx;
}
/* 未展开时：卡片有最小高度，头部占满可用高度，日期/天气/按钮在竖直方向居中 */
.day-module:not(.is-expanded) {
	min-height: 168rpx; /* 24+120+24，保证有空间给 header 填满并居中 */
}
.day-module:not(.is-expanded) .module-header {
	flex: 1;
	min-height: 0;
}
.day-module:not(.is-expanded) .item-list-wrap {
	flex: 0 0 0;
	min-height: 0;
}

.module-header {
	padding: 0;
	display: flex;
	align-items: center;
	gap: 30rpx; /* 日期与天气、天气与按钮的间距，可改此值 */
}

.date-box {
	display: flex;
	align-items: center;
	gap: 16rpx;
	width: 250rpx; /* 日期+月份列宽，避免「明天(周四)」等换行过碎，可在此调整 */
	min-width: 220rpx;
}
.date-num {
	font-size: 56rpx;
	font-family: "Didot", serif;
	color: #1D1D1F;
	font-weight: bold;
	line-height: 1;
}
.date-meta {
	display: flex;
	flex-direction: column;
}
.weekday {
	font-size: 30rpx;
	color: #1D1D1F;
	font-weight: 600;
	text-transform: uppercase;
	letter-spacing: 0.05em;
}
.month {
	font-size: 26rpx;
	color: #888;
}

.header-content { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.weather-brief { font-size: 28rpx; color: #48484A; font-weight: 500; }
.style-keyword { font-size: 20rpx; color: #9D8B70; font-weight: 600; }

.action-btn {
	background: #F5F5F7; padding: 14rpx 24rpx; border-radius: 12rpx;
}
.btn-text { font-size: 28rpx; color: #1D1D1F; font-weight: 600; }

/* 丝滑的网格高度展开动画 */
.item-list-wrap {
	display: grid;
	grid-template-rows: 0fr;
	transition: grid-template-rows 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
	opacity: 0;
	min-height: 0; /* 未展开时不占高，便于 header 占满并居中 */
}
.item-list-wrap.is-open {
	grid-template-rows: 1fr;
	opacity: 1;
}
.item-list-inner {
	overflow: hidden;
	display: flex;
	flex-direction: column;
	gap: 24rpx;
	padding-top: 24rpx;
}

.plan-item {
	background: #FFFFFF;
	border-radius: 24rpx;
	padding: 20rpx;
	display: flex;
	align-items: center;
	gap: 24rpx;
	border: 1px solid rgba(0, 0, 0, 0.03);
}

.item-header-row {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	margin-bottom: 6rpx;
}

.category-name {
	font-size: 22rpx;
	font-weight: 700;
	color: #9D8B70;
	text-transform: uppercase;
	letter-spacing: 0.1em;
	font-family: "Didot", serif;
	display: flex;
	align-items: center;
}
.category-name::after {
	content: '';
	display: inline-block;
	width: 2rpx;
	height: 20rpx;
	background-color: rgba(157, 139, 112, 0.3);
	margin-left: 16rpx;
	margin-right: 16rpx;
}

.product-name {
	font-size: 28rpx;
	color: #1D1D1F;
	font-family: "Didot", serif;
	font-weight: 500;
	flex: 1;
}

.item-detail {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
	flex: 1;
	min-width: 0;
}

.item-reason {
	font-size: 24rpx;
	color: #6B6B6B;
	line-height: 1.5;
	margin-top: 8rpx;
}

.plan-item-img-wrap {
	width: 100rpx;
	height: 100rpx;
	flex-shrink: 0;
	border-radius: 16rpx;
	overflow: hidden;
}
.real-item-img {
	width: 100%;
	height: 100%;
	border-radius: 16rpx;
}
.fallback-icon-wrap {
	width: 100rpx;
	height: 100rpx;
	background: #F5F5F7;
	border-radius: 16rpx;
	flex-shrink: 0;
	display: flex;
	align-items: center;
	justify-content: center;
}
.type-emoji { font-size: 50rpx; opacity: 0.8; }

/* 造型便签（「Stylist Note」标题与正文：字号、字体在此调整） */
.stylist-note {
	margin-top: 0; background: #FDF7ED; border-radius: 24rpx; padding: 24rpx;
	border-left: 8rpx solid #9D8B70;
	font-family: "Didot", serif;
}
.note-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.note-title { font-size: 26rpx; color: #9D8B70; font-weight: 800; text-transform: uppercase; }
.pin-icon { width: 24rpx; height: 24rpx; opacity: 0.3; }
.note-content { font-size: 24rpx; color: #5C5C5C; line-height: 1.6; }

.fallback-wrap { margin-top: 16rpx; }
.fallback-text { font-size: 24rpx; color: #2C2C2E; line-height: 1.6; white-space: pre-wrap; }

/* --- 入场动画（每日模块依次向上浮现）--- */
.ai-fade-block {
	opacity: 0;
	animation: aiBlockFade 0.5s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
}

@keyframes aiBlockFade {
	from {
		opacity: 0;
		transform: translateY(20rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}
</style>
