<template>
	<view class="plan-card">
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
				:key="d.key || idx"
				class="day-module"
				:class="{ 'is-expanded': expanded[idx] }"
			>
				<view class="module-header" @click="toggle(idx)">
					<view class="date-box">
						<text class="date-num">{{ formatDayNum(d.dateText) }}</text>
						<view class="date-meta">
							<text class="weekday">{{ d.label }}</text>
							<text class="month">{{ formatMonth(d.dateText) }}</text>
						</view>
					</view>

					<view class="header-content">
						<text class="weather-brief">{{ d.weatherText }}</text>
						<text class="style-keyword" v-if="extractKeyword(d.notes)"># {{ extractKeyword(d.notes) }}</text>
					</view>

					<view class="action-btn">
						<text class="btn-text">{{ expanded[idx] ? 'Close' : 'View Detail' }}</text>
					</view>
				</view>

				<view v-if="expanded[idx]" class="module-body">
					<view class="outfit-grid-v2">
						<view v-for="(it, ii) in d.items" :key="ii" class="closet-item-card">
							<view class="item-images-container">
								<template v-if="it.images && it.images.length > 0">
									<image
										v-for="(img, imgIdx) in it.images"
										:key="imgIdx"
										:src="img"
										mode="aspectFill"
										class="real-item-img"
										@click.stop="previewImages(it.images, imgIdx)"
									/>
								</template>
								<view v-else class="fallback-icon-wrap">
									<text class="type-emoji">{{ mapTypeToEmoji(it.type) }}</text>
								</view>
							</view>
							<view class="item-detail">
								<text class="category-name">{{ mapTypeToEnglish(it.type) }}</text>
								<text class="product-name">{{ cleanName(it.name) }}</text>
							</view>
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

		<view v-else class="fallback-wrap">
			<text class="fallback-text">{{ rawText }}</text>
		</view>
	</view>
</template>

<script setup>
import { computed, reactive } from 'vue'

const props = defineProps({
	plan: { type: Object, default: null },
	rawText: { type: String, default: '' }
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
		Other: 'OTHER'
	}
	return map[type] || 'ITEM'
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
.title-row { display: flex; align-items: baseline; gap: 20rpx; }
.plan-title-zh { font-size: 48rpx; font-weight: 800; color: #1D1D1F; }

.live-indicator {
	display: flex; align-items: center; gap: 8rpx;
	background: #E8F5E9; padding: 4rpx 12rpx; border-radius: 8rpx;
}
.live-indicator text { font-size: 18rpx; color: #4CAF50; font-weight: 700; }
.dot { width: 8rpx; height: 8rpx; background: #4CAF50; border-radius: 50%; }

/* 总体策略 Banner */
.strategy-banner {
	background: #1D1D1F; border-radius: 24rpx; padding: 30rpx; margin-bottom: 40rpx;
}
.banner-label {
	color: #9D8B70; font-size: 18rpx; text-transform: uppercase; 
	letter-spacing: 2rpx; margin-bottom: 12rpx; font-weight: 700;
}
.strategy-text { color: #FFF; font-size: 24rpx; line-height: 1.6; opacity: 0.9; }

/* 模块化日期 */
.day-module {
	background: #FFF; border-radius: 32rpx; margin-bottom: 24rpx;
	border: 1px solid #F1F1F1; overflow: hidden;
}

.module-header {
	padding: 30rpx; display: flex; align-items: center; gap: 30rpx;
}

.date-box {
	display: flex; align-items: center; gap: 16rpx; min-width: 140rpx;
}
.date-num { font-size: 56rpx; font-weight: 800; color: #1D1D1F; }
.date-meta { display: flex; flex-direction: column; }
.weekday { font-size: 22rpx; font-weight: 700; color: #1D1D1F; }
.month { font-size: 18rpx; color: #9D8B70; }

.header-content { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.weather-brief { font-size: 24rpx; color: #48484A; font-weight: 500; }
.style-keyword { font-size: 20rpx; color: #9D8B70; font-weight: 600; }

.action-btn {
	background: #F5F5F7; padding: 12rpx 20rpx; border-radius: 12rpx;
}
.btn-text { font-size: 20rpx; color: #1D1D1F; font-weight: 600; }

/* 单品网格：类似电商清单 */
.module-body { padding: 0 30rpx 30rpx; animation: fadeIn 0.4s ease; }

.outfit-grid-v2 {
	display: grid; grid-template-columns: 1fr 1fr; gap: 20rpx; margin-top: 10rpx;
}

.closet-item-card {
	background: #FAFAFA;
	border-radius: 24rpx;
	padding: 24rpx;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.item-images-container {
	display: flex;
	gap: 16rpx;
	overflow-x: auto;
	padding-bottom: 4rpx;
}

.real-item-img,
.fallback-icon-wrap {
	width: 120rpx;
	height: 120rpx;
	background: #F5F5F7;
	border-radius: 20rpx;
	flex-shrink: 0;
}

.real-item-img {
	border: 1px solid rgba(0, 0, 0, 0.03);
}

.fallback-icon-wrap {
	display: flex;
	align-items: center;
	justify-content: center;
}

.type-emoji { font-size: 50rpx; opacity: 0.8; }

.item-detail {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.category-name {
	font-size: 20rpx;
	color: #9D8B70;
	text-transform: uppercase;
	font-weight: 700;
	letter-spacing: 2rpx;
}

.product-name {
	font-size: 26rpx;
	color: #1D1D1F;
	font-weight: 600;
	line-height: 1.4;
}

/* 造型便签 */
.stylist-note {
	margin-top: 30rpx; background: #FDF7ED; border-radius: 24rpx; padding: 24rpx;
	border-left: 8rpx solid #9D8B70;
}
.note-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12rpx; }
.note-title { font-size: 20rpx; color: #9D8B70; font-weight: 800; text-transform: uppercase; }
.pin-icon { width: 24rpx; height: 24rpx; opacity: 0.3; }
.note-content { font-size: 24rpx; color: #5C5C5C; line-height: 1.6; }

.fallback-wrap { margin-top: 16rpx; }
.fallback-text { font-size: 24rpx; color: #2C2C2E; line-height: 1.6; white-space: pre-wrap; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
