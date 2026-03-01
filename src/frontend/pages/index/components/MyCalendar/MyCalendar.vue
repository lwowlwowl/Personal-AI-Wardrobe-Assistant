<template>
	<view class="calendar-container">
		<view class="calendar-inner">
			<!-- 标题区 -->
			<view class="header">
				<text class="page-title">My Calendar</text>
				<text class="page-sub">— outfit diary —</text>
				<view class="header-divider" />
			</view>

			<!-- 主体：未选中居中 / 已选中左右分栏 -->
			<view class="main-wrapper">
				<!-- 左侧：日历 + This Month -->
				<view class="main-left">
					<view class="side-panel">
						<text class="side-title">This Month</text>
						<view class="stat-item">
							<text class="stat-num">{{ monthStats.daysRecorded }}</text>
							<text class="stat-label">days recorded</text>
						</view>
						<view class="stat-item">
							<text class="stat-num">{{ monthStats.uniqueItems }}</text>
							<text class="stat-label">unique items</text>
						</view>
						<view v-if="currentStreak > 0" class="stat-item streak-item">
							<text class="streak-emoji">🔥</text>
							<text class="stat-num streak-num">{{ currentStreak }}</text>
							<text class="stat-label">day streak</text>
						</view>
					</view>
					<view class="calendar-block">
						<view class="calendar-card">
							<view class="calendar-nav">
								<view class="nav-btn month-switch" @click="prevMonth">
									<text class="nav-arrow">‹</text>
								</view>
								<text class="month-label">{{ monthLabel }}</text>
								<view class="nav-btn month-switch" @click="nextMonth">
									<text class="nav-arrow">›</text>
								</view>
							</view>
							<view class="weekday-row">
								<text v-for="d in weekdays" :key="d" class="weekday-cell">{{ d }}</text>
							</view>
							<view>
								<transition :name="slideDirection === 'left' ? 'month-slide-left' : 'month-slide-right'" mode="out-in">
									<view :key="monthKey" class="calendar-grid">
										<view
											v-for="(cell, idx) in calendarCells"
											:key="cell.dateKey"
											class="day-cell"
											:class="{
												'other-month': !cell.isCurrentMonth,
												'today': cell.isToday,
												'has-items': (outfitsByDate[cell.dateKey]?.length || 0) > 0,
												'selected': selectedDateKey === cell.dateKey
											}"
											:style="{ animationDelay: idx * 20 + 'ms' }"
											@click="selectDay(cell)"
											@mouseenter="hoveredDateKey = (outfitsByDate[cell.dateKey]?.length || 0) > 0 ? cell.dateKey : null"
											@mouseleave="hoveredDateKey = null"
										>
											<view class="day-num-wrap" :class="{ 'today': cell.isToday }">
												<text class="day-num">{{ cell.day }}</text>
											</view>
											<view v-if="outfitsByDate[cell.dateKey]?.length" class="day-status has-outfit">
												<text class="outfit-dot">●</text>
												<text v-if="outfitsByDate[cell.dateKey].length > 1" class="outfit-count">{{ outfitsByDate[cell.dateKey].length }}</text>
											</view>
											<view v-if="selectedDateKey === cell.dateKey" class="selected-bar" />
											<!-- Outfit 预览浮层：hover 时显示 -->
											<transition name="preview-fade">
												<view v-if="hoveredDateKey === cell.dateKey && outfitsByDate[cell.dateKey]?.length" class="outfit-preview">
													<view class="preview-header">
														<text class="preview-date">{{ formatPreviewDate(cell.dateKey) }}</text>
													</view>
													<view class="preview-items">
														<view
															v-for="(item, i) in outfitsByDate[cell.dateKey]"
															:key="item.id + '-' + i"
															class="preview-item"
														>
															<view class="preview-thumb-wrap" :style="{ '--thumb-accent': item.accentColor || '#8d6e63' }">
																<image v-if="item.image" class="preview-thumb" :src="item.image" mode="aspectFill" />
																<view v-else class="preview-thumb placeholder" />
															</view>
															<text class="preview-item-name">{{ item.name }}</text>
														</view>
													</view>
												</view>
											</transition>
										</view>
									</view>
								</transition>
							</view>
						</view>
					</view>
				</view>

				<!-- 右侧：Outfit Panel（仅选中时显示） -->
				<transition name="panel-fade">
					<view v-if="selectedDateKey" class="main-right">
						<view class="outfit-panel">
							<view class="outfit-panel-header">
								<view class="outfit-header-row1">
									<text class="outfit-panel-title">{{ selectedDateLabel }}</text>
								</view>
								<text class="outfit-panel-subtitle">{{ selectedDaySummary }}</text>
								<view v-if="!showAddPanel && (outfitsByDate[selectedDateKey]?.length || 0) > 0" class="add-btn add-btn-primary" @click="openAddPanel">
									<image src="/static/icons/icon-plus.svg" mode="aspectFit" class="add-icon" />
									<text>Add Outfit</text>
								</view>
							</view>
							<!-- 选择衣服模式 / 列表·空状态：用 transition 做淡入淡出 -->
							<transition name="panel-inner-fade" mode="out-in">
								<AddOutfitPanel
									v-if="showAddPanel"
									key="add"
									:token="userToken"
									:initial-selection="existingOutfits"
									@confirm="handleAddOutfitConfirm"
									@cancel="closeAddPanel"
								/>
							<view v-else class="panel-inner">
								<transition name="panel-content-fade" mode="out-in">
									<view v-if="!outfitsByDate[selectedDateKey]?.length" key="empty" class="empty-day">
										<view class="empty-illus">
											<view class="empty-icon-gradient" />
											<image src="/static/icons/icon-wardrobe.svg" mode="aspectFit" class="empty-icon" />
										</view>
										<text class="empty-text">✨ No outfit logged yet</text>
										<text class="empty-hint">Start your style diary today.</text>
										<view class="empty-add-btn" @click="openAddPanel">
											<image src="/static/icons/icon-plus.svg" mode="aspectFit" class="add-icon" />
											<text>Add Outfit</text>
										</view>
									</view>
									<view v-else key="list" class="outfit-list" :class="{ 'is-clearing': isClearing }">
									<view
										v-for="(item, i) in outfitsByDate[selectedDateKey]"
										:key="item.id || i"
										class="outfit-item"
										:class="{ 
											'outfit-item-enter': !isClearing,
											'outfit-item-leave': isClearing
										}"
										:style="{ animationDelay: i * 50 + 'ms' }"
									>
										<view class="outfit-thumb-wrap" :style="{ '--thumb-accent': item.accentColor || '#8d6e63' }">
											<image v-if="item.image" class="outfit-thumb" :src="item.image" mode="aspectFill" />
											<view v-else class="outfit-thumb placeholder" />
										</view>
										<text class="outfit-name">{{ item.name }}</text>
										<view class="remove-btn" @click.stop="removeOutfit(selectedDateKey, i)">
											<image src="/static/icons/icon-trash-red.svg" mode="aspectFit" class="remove-icon" />
										</view>
									</view>
									<view class="outfit-list-footer" :class="{ 'is-clearing': isClearing }">
										<view class="clear-all-btn" @click="clearAllOutfits">
											<text>Clear</text>
										</view>
									</view>
									</view>
								</transition>
							</view>
							</transition>
						</view>
					</view>
				</transition>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import AddOutfitPanel from './AddOutfitPanel.vue'
import { getCalendarOutfits, saveCalendarOutfits, API_BASE_URL } from '@/api/calendarApi.js'

const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const userToken = ref(uni.getStorageSync('auth_token') || '')
const currentDate = new Date()
const displayYear = ref(currentDate.getFullYear())
const displayMonth = ref(currentDate.getMonth())
const slideDirection = ref('right') // 'left' | 'right' - 用于月份切换动画方向
const selectedDateKey = ref(null)
const showAddPanel = ref(false)
const hoveredDateKey = ref(null) // 用于 hover 预览浮层
const isClearing = ref(false) // 用于清除动画状态（清空当天全部时使用）

/** 每日穿搭记录：{ "2025-02-09": [{ id, name, image, accentColor? }] }，来自后端 GET /api/calendar/outfits */
const outfitsByDate = ref({})

/** 将后端返回的单品统一为前端格式（image 为完整 URL） */
function normalizeItem(item) {
	if (!item) return item
	let image = item.image || item.image_url || ''
	if (image && image.startsWith('/') && !image.startsWith('//')) {
		image = `${API_BASE_URL}${image}`
	}
	return {
		id: item.id,
		name: item.name || '未命名',
		image,
		accentColor: item.accentColor || item.accent_color || '#8d6e63'
	}
}

/** 拉取当前显示月份的穿搭记录 */
async function fetchMonthOutfits() {
	const token = userToken.value
	if (!token) {
		outfitsByDate.value = {}
		return
	}
	try {
		const res = await getCalendarOutfits({
			token,
			year: displayYear.value,
			month: displayMonth.value + 1 // API 使用 1–12
		})
		if (res.statusCode === 200 && res.data && res.data.success && res.data.data) {
			const raw = res.data.data.outfits || {}
			const next = {}
			for (const [dateKey, items] of Object.entries(raw)) {
				next[dateKey] = (items || []).map(normalizeItem)
			}
			outfitsByDate.value = next
		} else {
			outfitsByDate.value = {}
		}
	} catch (e) {
		outfitsByDate.value = {}
		uni.showToast({ title: '获取日历记录失败', icon: 'none' })
	}
}

/** 当前选中日期已有的 outfit，用于传递给 AddOutfitPanel */
const existingOutfits = computed(() => {
	if (!selectedDateKey.value) return []
	return outfitsByDate.value[selectedDateKey.value] || []
})

const monthKey = computed(() => `${displayYear.value}-${displayMonth.value}`)

const monthLabel = computed(() => {
	const d = new Date(displayYear.value, displayMonth.value)
	return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

const selectedDateLabel = computed(() => {
	if (!selectedDateKey.value) return ''
	const [y, m, d] = selectedDateKey.value.split('-')
	const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d))
	return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
})

/** 依日期月份推算季节（北半球：3–5 春、6–8 夏、9–11 秋、12–2 冬） */
function getSeasonForDateKey(dateKey) {
	const [, m] = dateKey.split('-')
	const month = parseInt(m, 10)
	if (month >= 3 && month <= 5) return 'Spring'
	if (month >= 6 && month <= 8) return 'Summer'
	if (month >= 9 && month <= 11) return 'Autumn'
	return 'Winter'
}

/** 选中日的摘要：几套穿搭、该日期的季节（依月份，非单品标签） */
const selectedDaySummary = computed(() => {
	const key = selectedDateKey.value
	if (!key) return ''
	const items = outfitsByDate.value[key] || []
	const n = items.length
	if (n === 0) return 'No outfit yet'
	const season = getSeasonForDateKey(key)
	const count = n === 1 ? '1 outfit recorded' : `${n} outfits recorded`
	return `${count}   ·   ${season}`
})

/** 
 * 计算连续记录天数（day streak）
 * 
 * 逻辑说明：
 * 
 * 【当前月份的逻辑】
 * - 如果今天有记录：从今天开始往前倒推，计算连续有记录的天数
 * - 如果今天没记录：不显示 streak（返回 0），因为今天还没记，streak 已经断了
 *   这样设计的好处：只有今天有记录时才显示 streak，更符合"习惯打卡"的实时性
 * 
 * 【过去月份的逻辑】
 * - 从该月最后一天往前倒推，找到最后一个有记录的天作为起点
 * - 如果该月完全没有记录，返回 0
 * - 从找到的最后一个有记录的天开始，继续往前倒推，计算连续有记录的天数
 *   这样可以看到用户在该月结束时的连续记录情况
 * 
 * 【未来月份的逻辑】
 * - 返回 0（未来还没有记录）
 */
function calculateStreak() {
	const today = new Date()
	const todayYear = today.getFullYear()
	const todayMonth = today.getMonth()
	
	const viewYear = displayYear.value
	const viewMonth = displayMonth.value
	
	let startDate = new Date()
	
	// 根据查看的月份决定起始日期
	if (viewYear === todayYear && viewMonth === todayMonth) {
		// 【当前月份】只有今天有记录时才显示 streak
		const todayKey = toDateKey(todayYear, todayMonth, today.getDate())
		const todayHasRecord = outfitsByDate.value[todayKey]?.length > 0
		if (!todayHasRecord) {
			// 今天没记录，不显示 streak
			return 0
		}
		// 今天有记录，从今天开始往前倒推
	} else if (viewYear < todayYear || (viewYear === todayYear && viewMonth < todayMonth)) {
		// 【过去月份】从该月最后一天往前倒推，找到最后一个有记录的天作为起点
		const lastDay = new Date(viewYear, viewMonth + 1, 0) // 该月最后一天
		const firstDay = new Date(viewYear, viewMonth, 1) // 该月第一天
		
		// 从最后一天往前找，找到最后一个有记录的天
		let foundStart = false
		let checkDate = new Date(lastDay)
		
		while (checkDate >= firstDay) {
			const key = toDateKey(checkDate.getFullYear(), checkDate.getMonth(), checkDate.getDate())
			if (outfitsByDate.value[key]?.length > 0) {
				startDate = new Date(checkDate)
				foundStart = true
				break
			}
			checkDate.setDate(checkDate.getDate() - 1)
		}
		
		// 如果该月完全没有记录，streak 为 0
		if (!foundStart) {
			return 0
		}
	} else {
		// 【未来月份】streak 为 0
		return 0
	}
	
	// 从起始日期往前倒推，计算连续有记录的天数（仅限当前查看月份内，跨月不连续）
	const viewMonth0 = viewMonth
	let streak = 0
	let checkDate = new Date(startDate)
	while (true) {
		const y = checkDate.getFullYear()
		const m = checkDate.getMonth()
		if (y !== viewYear || m !== viewMonth0) break // 仅限当月
		const key = toDateKey(y, m, checkDate.getDate())
		if (outfitsByDate.value[key]?.length > 0) {
			streak++
			checkDate.setDate(checkDate.getDate() - 1)
		} else {
			break
		}
	}
	return streak
}

const currentStreak = computed(() => calculateStreak())

/** 本月穿搭统计（与 MY_CALENDAR.md 口径一致：uniqueItems 按 item.id 去重） */
const monthStats = computed(() => {
	const year = displayYear.value
	const month = displayMonth.value
	const prefix = `${year}-${String(month + 1).padStart(2, '0')}-`
	let daysRecorded = 0
	const uniqueIds = new Set()
	for (const [key, items] of Object.entries(outfitsByDate.value)) {
		if (key.startsWith(prefix) && items?.length) {
			daysRecorded++
			for (const item of items) {
				if (item.id != null) uniqueIds.add(item.id)
			}
		}
	}
	return { daysRecorded, uniqueItems: uniqueIds.size }
})

/** 将年月日转换为日期键字符串（格式：YYYY-MM-DD） */
function toDateKey(y, m, d) {
	const pad = (n) => String(n).padStart(2, '0')
	return `${y}-${pad(m + 1)}-${pad(d)}`
}

/** 生成日历单元格数组（包含当前月、上月末尾、下月开头的日期，共42个单元格） */
const calendarCells = computed(() => {
	const year = displayYear.value
	const month = displayMonth.value
	const first = new Date(year, month, 1)
	const last = new Date(year, month + 1, 0)
	const firstDay = first.getDay()
	const daysInMonth = last.getDate()

	const today = new Date()
	const todayKey = toDateKey(today.getFullYear(), today.getMonth(), today.getDate())

	const cells = []
	const prevMonth = month === 0 ? 11 : month - 1
	const prevYear = month === 0 ? year - 1 : year
	const prevLast = new Date(prevYear, prevMonth + 1, 0)
	const prevDays = prevLast.getDate()

	for (let i = 0; i < firstDay; i++) {
		const d = prevDays - firstDay + i + 1
		cells.push({
			day: d,
			dateKey: toDateKey(prevYear, prevMonth, d),
			isCurrentMonth: false,
			isToday: false
		})
	}

	for (let d = 1; d <= daysInMonth; d++) {
		const key = toDateKey(year, month, d)
		cells.push({
			day: d,
			dateKey: key,
			isCurrentMonth: true,
			isToday: key === todayKey
		})
	}

	const remaining = 42 - cells.length
	const nextMonth = month === 11 ? 0 : month + 1
	const nextYear = month === 11 ? year + 1 : year
	for (let d = 1; d <= remaining; d++) {
		cells.push({
			day: d,
			dateKey: toDateKey(nextYear, nextMonth, d),
			isCurrentMonth: false,
			isToday: false
		})
	}

	return cells
})

/** 切换到上一个月，设置滑动方向为 left（用于动画） */
function prevMonth() {
	slideDirection.value = 'left'
	if (displayMonth.value === 0) {
		displayMonth.value = 11
		displayYear.value--
	} else {
		displayMonth.value--
	}
}

/** 切换到下一个月，设置滑动方向为 right（用于动画） */
function nextMonth() {
	slideDirection.value = 'right'
	if (displayMonth.value === 11) {
		displayMonth.value = 0
		displayYear.value++
	} else {
		displayMonth.value++
	}
}

onMounted(() => fetchMonthOutfits())
watch([displayYear, displayMonth], () => fetchMonthOutfits())

/** 选择日期：如果当前处于 Add Outfit 模式，则退出该模式 */
function selectDay(cell) {
	// 如果切换日期时处于编辑状态，退出编辑状态
	if (showAddPanel.value) {
		showAddPanel.value = false
	}
	selectedDateKey.value = cell.dateKey
}

/** 格式化预览浮层显示的日期 */
function formatPreviewDate(dateKey) {
	const [y, m, d] = dateKey.split('-')
	const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d))
	return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

/** 确认添加 Outfit：调用 POST 全量覆盖，成功后更新本地状态 */
async function handleAddOutfitConfirm(selectedItems) {
	if (!selectedDateKey.value) return
	const token = userToken.value
	if (!token) {
		uni.showToast({ title: '请先登录', icon: 'none' })
		return
	}
	const key = selectedDateKey.value
	const payload = selectedItems.map((i) => ({
		id: i.id,
		name: i.name,
		image: i.image,
		accentColor: i.accentColor
	}))
	try {
		const res = await saveCalendarOutfits({ token, date: key, items: payload })
		if (res.statusCode === 200 && res.data && res.data.success && res.data.data) {
			const data = res.data.data
			const items = (data.items || []).map(normalizeItem)
			if (items.length === 0) {
				const rest = { ...outfitsByDate.value }
				delete rest[key]
				outfitsByDate.value = rest
			} else {
				outfitsByDate.value = { ...outfitsByDate.value, [key]: items }
			}
		} else {
			uni.showToast({ title: res.data?.message || '保存失败', icon: 'none' })
		}
	} catch (e) {
		uni.showToast({ title: '保存失败', icon: 'none' })
	}
	showAddPanel.value = false
}

/** 打开 Add Outfit 面板：同步最新 token，便于子组件拉取衣橱列表 */
function openAddPanel() {
	userToken.value = uni.getStorageSync('auth_token') || userToken.value
	showAddPanel.value = true
}

/** 关闭 Add Outfit 面板 */
function closeAddPanel() {
	showAddPanel.value = false
}

/** 删除指定日期的指定索引的 outfit：本地立即更新，再调用 POST 全量覆盖（保持体感顺滑、无闪回） */
async function removeOutfit(dateKey, index) {
	if (!outfitsByDate.value[dateKey]) return
	const token = userToken.value
	if (!token) {
		uni.showToast({ title: '请先登录', icon: 'none' })
		return
	}

	// 先乐观更新本地状态（用户立即看到结果）
	const current = outfitsByDate.value[dateKey] || []
	const arr = current.filter((_, i) => i !== index)
	if (arr.length === 0) {
		const next = { ...outfitsByDate.value }
		delete next[dateKey]
		outfitsByDate.value = next
	} else {
		outfitsByDate.value = { ...outfitsByDate.value, [dateKey]: arr }
	}

	const payload = arr.map((i) => ({ id: i.id, name: i.name, image: i.image, accentColor: i.accentColor }))
	try {
		const res = await saveCalendarOutfits({ token, date: dateKey, items: payload })
		if (!(res.statusCode === 200 && res.data && res.data.success)) {
			uni.showToast({ title: res.data?.message || '删除失败', icon: 'none' })
		}
	} catch (e) {
		uni.showToast({ title: '删除失败', icon: 'none' })
	}
}

/** 清除选中日期的所有 outfits：动画后调用 POST items:[] */
function clearAllOutfits() {
	if (!selectedDateKey.value) return
	const items = outfitsByDate.value[selectedDateKey.value] || []
	if (items.length === 0) return
	const token = userToken.value
	if (!token) {
		uni.showToast({ title: '请先登录', icon: 'none' })
		return
	}

	isClearing.value = true
	const itemCount = items.length
	const itemFadeDuration = 300
	const staggerDelay = 50
	const totalItemAnimation = itemFadeDuration + (itemCount - 1) * staggerDelay

	setTimeout(async () => {
		try {
			const res = await saveCalendarOutfits({
				token,
				date: selectedDateKey.value,
				items: []
			})
			if (res.statusCode === 200 && res.data && res.data.success) {
				const next = { ...outfitsByDate.value }
				delete next[selectedDateKey.value]
				outfitsByDate.value = next
			} else {
				uni.showToast({ title: res.data?.message || '清除失败', icon: 'none' })
			}
		} catch (e) {
			uni.showToast({ title: '清除失败', icon: 'none' })
		}
		setTimeout(() => { isClearing.value = false }, 100)
	}, totalItemAnimation)
}
</script>

<style scoped>
.calendar-container {
	width: 100%;
	height: 100vh;      /* 锁定一屏 */
	overflow: hidden;   /* 不让整页滚 */
	background: #FDFBF7;
}

/* 整页外边距：上 左右 下，调整页面内容与边缘的距离 */
.calendar-inner {
	padding: 80rpx 24rpx 48rpx;
	width: 100%;
	max-width: 100%;
	height: 100%;
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
}

/* 标题区：Aesop 风格 - 奢侈留白、大标题、淡副标 */
.header {
	margin-bottom: 60rpx;
	text-align: center;
}

.page-title {
	display: block;
	font-size: 72rpx;
	font-weight: 600;
	font-family: "Didot", "Bodoni MT", "Noto Serif", serif;
	color: #1d1d1f;
	letter-spacing: -0.04em;
	line-height: 1.1;
}

.page-sub {
	display: block;
	font-size: 24rpx;
	font-weight: 400;
	color: #c0c0c0;
	margin-top: 12rpx;
	letter-spacing: 0.2em;
}

.header-divider {
	height: 1rpx;
	background: linear-gradient(90deg, transparent, rgba(0,0,0,0.06) 20%, rgba(0,0,0,0.06) 80%, transparent);
	margin-top: 48rpx;
}

/* ========== 左侧日历与右侧面板：大小 / 比例 / 位置 控制说明 ==========
 * 调整下面 .main-wrapper / .main-left / .main-right 中的数值即可生效。
 * 未选中日期时只显示左侧日历；选中后右侧面板出现在日历右侧，布局不跳变。
 */

/* 主内容区域（版心）：控制整体宽度与左右栏间距、对齐 */
.main-wrapper {
	width: 100%;
	max-width: 2700rpx;   /* 整体最大宽度，大屏不会无限变宽，可改为 1200rpx / 1600rpx */
	margin: 0 auto;       /* 水平居中 */
	display: flex;
	flex-direction: row;
	gap: 275rpx;          /* 左侧日历与右侧面板之间的间距，可改为 32rpx / 48rpx 等 */
	align-items: stretch; /* 左右两栏等高 */
	flex: 1;
	min-height: 0;
}

/* 左侧日历：控制宽度与在左栏内的位置 */
.main-left {
	flex: 0 0 1080rpx;    /* 基准宽度，建议与 min/max 协调，如 760rpx / 800rpx */
	min-width: 720rpx;   /* 最小宽度，小屏时不会被压得太窄 */
	max-width: 2060rpx;   /* 最大宽度，避免日历在大屏时过宽 */
	display: flex;
	margin-left: 130rpx;
	flex-direction: column;
	align-items: center;   /* 左栏内内容水平居中，改为 flex-start 靠左、flex-end 靠右 */
	justify-content: flex-start; /* 左栏内内容垂直靠上，改为 center 居中、flex-end 靠下 */
	gap: 28rpx;          /* 左栏内部（This Month 与日历之间）的间距 */
}

/* 右侧面板：控制宽度与占比，选中日期时显示 */
.main-right {
	flex: 1 1 auto;     /* 占满剩余空间；若想固定宽度可改为 flex: 0 0 600rpx */
	min-width: 520rpx;  /* 最小宽度，防止被压得太窄 */
	max-width: 1080rpx;  /* 最大宽度，与左侧日历宽度协调 */
	display: flex;
	flex-direction: column;
	min-height: 0;
	animation: panel-fade-in 0.28s ease;
}

@keyframes panel-fade-in {
	from {
		opacity: 0;
	}
	to {
		opacity: 1;
	}
}

.side-panel {
	width: 100%;
	display: flex;
	flex-direction: row;
	flex-wrap: wrap;
	align-items: baseline;
	gap: 24rpx;
	padding: 28rpx 32rpx;
	border-radius: 24rpx;
	background: rgba(255, 255, 255, 0.6);
	border: 1rpx solid rgba(0, 0, 0, 0.04);
}

/* 顶部统计条：背景信息，更轻 - 字体更小、灰度更淡 */
.side-title {
	font-size: 22rpx;
	font-weight: 600;
	color: #aaa;
	text-transform: uppercase;
	letter-spacing: 0.1em;
}

.stat-item {
	display: flex;
	align-items: baseline;
	gap: 8rpx;
	margin-bottom: 0;
}
.stat-num {
	font-size: 36rpx;
	font-weight: 600;
	color: #888;
	line-height: 1.2;
}
.stat-label {
	font-size: 20rpx;
	color: #bbb;
	margin-top: 0;
}
.streak-item {
	gap: 6rpx;
}
.streak-emoji {
	font-size: 28rpx;
	line-height: 1;
}
.streak-num {
	color: #C8A27A;
}

.calendar-block {
	width: 100%;
	max-width: 100%;
	flex: 1;
}

/* 日历 Card：主角，更聚焦 - 加强阴影让它更「浮」 */
.calendar-card {
	width: 100%;
	padding: 28rpx 24rpx 32rpx;
	background: #fff;
	border-radius: 24rpx;
	border: 1rpx solid rgba(0, 0, 0, 0.06);
	box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.08), 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

/* 右侧 Outfit Panel：用 height + max-height 限制高度（不用 flex:1 避免被父级拉满导致改数值无效）
 * 调长度：只改这一处的 260rpx。数值越小面板越高（如 220rpx），数值越大面板越矮（如 300rpx）
 */
/* 右侧 Outfit Panel：辅助，更柔和 - 更轻、更像「抽屉」 */
.outfit-panel {
	height: calc(100vh - 260rpx);
	max-height: calc(100vh - 360rpx);
	min-height: 0;
	display: flex;
	flex-direction: column;
	padding: 40rpx 44rpx 52rpx;
	background: rgba(255, 255, 255, 0.95);
	border-radius: 28rpx;
	border: 1rpx solid rgba(0, 0, 0, 0.04);
	box-shadow: 0 2rpx 16rpx rgba(0, 0, 0, 0.03), 0 1rpx 4rpx rgba(0, 0, 0, 0.02);
}

.outfit-panel-header {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	margin-bottom: 24rpx;
}

.outfit-header-row1 {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.outfit-panel-title {
	font-size: 38rpx;
	font-weight: 700;
	color: #1d1d1f;
	letter-spacing: -0.02em;
}

.outfit-panel-subtitle {
	font-size: 26rpx;
	font-weight: 500;
	color: #666;
}

.add-btn-primary {
	padding: 18rpx 28rpx;
	font-size: 28rpx;
	font-weight: 700;
	background: rgba(184, 107, 31, 0.2);
	border: 2rpx solid rgba(184, 107, 31, 0.4);
	border-radius: 16rpx;
	align-self: flex-start;
	margin-top: 4rpx;
}
.add-btn-primary:hover {
	background: rgba(184, 107, 31, 0.28);
	border-color: rgba(184, 107, 31, 0.5);
}
.add-btn-primary .add-icon {
	width: 36rpx;
	height: 36rpx;
}

/* Add 模式 / 列表·空状态 切换：淡入淡出 */
.panel-inner {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
}
.panel-inner-fade-enter-active,
.panel-inner-fade-leave-active {
	transition: opacity 0.25s ease;
}
.panel-inner-fade-enter-from,
.panel-inner-fade-leave-to {
	opacity: 0;
}
.panel-inner-fade-enter-to,
.panel-inner-fade-leave-from {
	opacity: 1;
}

.panel-content-fade-enter-active,
.panel-content-fade-leave-active {
	transition: opacity 0.3s cubic-bezier(0.22, 1, 0.36, 1), transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.panel-content-fade-enter-from {
	opacity: 0;
	transform: translateY(16rpx);
}
.panel-content-fade-leave-to {
	opacity: 0;
	transform: translateY(-16rpx);
}
.panel-content-fade-enter-to,
.panel-content-fade-leave-from {
	opacity: 1;
	transform: translateY(0);
}


.calendar-nav {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 48rpx;
	margin-bottom: 36rpx;
}

.nav-btn {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.04);
	transition: background 0.25s cubic-bezier(0.22, 1, 0.36, 1), transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
	cursor: pointer;
}
.month-switch:hover {
	background: rgba(0, 0, 0, 0.08);
}
.month-switch:active {
	transform: scale(0.88);
	background: rgba(0, 0, 0, 0.1);
}

.nav-arrow {
	font-size: 36rpx;
	font-weight: 600;
	color: #1d1d1f;
	line-height: 1;
}

.month-label {
	font-size: 40rpx;
	font-weight: 700;
	color: #1d1d1f;
	min-width: 280rpx;
	text-align: center;
}

.weekday-row {
	display: grid;
	grid-template-columns: repeat(7, 1fr);
	gap: 6rpx;
	margin-bottom: 12rpx;
	padding: 0 4rpx;
}

.weekday-cell {
	font-size: 24rpx;
	font-weight: 700;
	color: #555;
	text-align: center;
	letter-spacing: 0.02em;
}

/* 月份切换：淡入 + 位移，轻柔过渡 */
/* 月份切换：slide-left / slide-right + fade，慢柔丝滑 */
.month-slide-left-enter-active,
.month-slide-left-leave-active,
.month-slide-right-enter-active,
.month-slide-right-leave-active {
	transition: opacity 0.4s cubic-bezier(0.22, 1, 0.36, 1), transform 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
/* 向左切换（prevMonth）：新内容（更早的月份）从左边滑入，旧内容向右滑出 */
.month-slide-left-enter-from {
	opacity: 0;
	transform: translateX(-40rpx);
}
.month-slide-left-leave-to {
	opacity: 0;
	transform: translateX(40rpx);
}
/* 向右切换（nextMonth）：新内容（更晚的月份）从右边滑入，旧内容向左滑出 */
.month-slide-right-enter-from {
	opacity: 0;
	transform: translateX(40rpx);
}
.month-slide-right-leave-to {
	opacity: 0;
	transform: translateX(-40rpx);
}
.month-slide-left-enter-to,
.month-slide-left-leave-from,
.month-slide-right-enter-to,
.month-slide-right-leave-from {
	opacity: 1;
	transform: translateX(0);
}

.calendar-grid {
	display: grid;
	grid-template-columns: repeat(7, 1fr);
	gap: 6rpx;
}

/* 日历格子：纸张感，预设无边框，hover 才浮现 */
.day-cell {
	aspect-ratio: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	border-radius: 12rpx;
	background: transparent;
	border: 1rpx solid transparent;
	transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
	position: relative;
}
.day-cell:hover {
	border-color: rgba(0, 0, 0, 0.08);
	background: rgba(255, 255, 255, 0.4);
	transform: scale(1.03);
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
	cursor: pointer;
}
.day-cell:active {
	transform: scale(0.97);
}
.day-cell.other-month {
	opacity: 0.35;
}
.day-cell.today {
	background: rgba(255, 242, 217, 0.55);
}
.day-cell.today:hover {
	border-color: rgba(184, 107, 31, 0.25);
}
.day-cell.has-items {
	background: rgba(184, 107, 31, 0.04);
}
.day-cell.has-items:hover {
	border-color: rgba(184, 107, 31, 0.15);
}
.day-cell.selected {
	background: rgba(184, 107, 31, 0.14);
	border: 4rpx solid #C8A27A;
	box-shadow: 0 6rpx 20rpx rgba(184, 107, 31, 0.25);
	transform: scale(1.05);
	z-index: 1;
}
.day-cell.selected:hover {
	background: rgba(184, 107, 31, 0.2);
	border-color: #C8A27A;
	transform: scale(1.05);
	box-shadow: 0 8rpx 24rpx rgba(184, 107, 31, 0.3);
}

.selected-bar {
	position: absolute;
	bottom: 8rpx;
	left: 50%;
	transform: translateX(-50%);
	width: 28rpx;
	height: 6rpx;
	border-radius: 3rpx;
	background: #8d6e63;
}
.day-num-wrap {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	padding: 0;
}
.day-num-wrap.today {
	padding: 4rpx 12rpx;
	border-radius: 16rpx;
	background: #8d6e63;
}
.day-num {
	font-size: 32rpx;
	font-weight: 600;
	color: #1d1d1f;
}
.day-num-wrap.today .day-num {
	color: #fff;
}

/* Outfit 预览浮层：hover 时显示 */
.outfit-preview {
	position: absolute;
	bottom: calc(100% + 12rpx);
	left: 50%;
	transform: translateX(-50%);
	width: 280rpx;
	background: #fff;
	border-radius: 20rpx;
	box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.15), 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
	border: 1rpx solid rgba(0, 0, 0, 0.06);
	z-index: 100;
	padding: 20rpx;
	pointer-events: none;
}
.outfit-preview::after {
	content: '';
	position: absolute;
	bottom: -8rpx;
	left: 50%;
	transform: translateX(-50%);
	width: 0;
	height: 0;
	border-left: 8rpx solid transparent;
	border-right: 8rpx solid transparent;
	border-top: 8rpx solid #fff;
}
.preview-header {
	margin-bottom: 12rpx;
	padding-bottom: 12rpx;
	border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
}
.preview-date {
	font-size: 24rpx;
	font-weight: 600;
	color: #333;
}
.preview-items {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
}
.preview-item {
	display: flex;
	align-items: center;
	gap: 12rpx;
}
.preview-thumb-wrap {
	width: 56rpx;
	height: 56rpx;
	border-radius: 12rpx;
	overflow: hidden;
	flex-shrink: 0;
	box-shadow: inset 4rpx 0 0 0 var(--thumb-accent, #8d6e63);
}
.preview-thumb {
	width: 100%;
	height: 100%;
	border-radius: 8rpx 12rpx 12rpx 8rpx;
	background: #f5f2ee;
	display: block;
}
.preview-thumb.placeholder {
	background: #e8e4df;
}
.preview-item-name {
	font-size: 24rpx;
	font-weight: 400;
	color: #666;
	flex: 1;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.preview-fade-enter-active,
.preview-fade-leave-active {
	transition: opacity 0.2s cubic-bezier(0.22, 1, 0.36, 1), transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}
.preview-fade-enter-from {
	opacity: 0;
	transform: translateX(-50%) translateY(8rpx);
}
.preview-fade-leave-to {
	opacity: 0;
	transform: translateX(-50%) translateY(8rpx);
}
.preview-fade-enter-to,
.preview-fade-leave-from {
	opacity: 1;
	transform: translateX(-50%) translateY(0);
}

/* 日历格子状态：有记录 ● / 多套 ●2 */
.day-status {
	margin-top: 6rpx;
}

.has-outfit {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 4rpx;
}

.outfit-dot {
	font-size: 16rpx;
	color: #8d6e63;
	line-height: 1;
}

.outfit-count {
	font-size: 18rpx;
	font-weight: 700;
	color: #8d6e63;
}

/* 右侧面板出现/消失：仅淡入淡出，不位移，避免切换日期时面板跳到右边 */
.panel-fade-enter-active,
.panel-fade-leave-active {
	transition: opacity 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}
.panel-fade-enter-from,
.panel-fade-leave-to {
	opacity: 0;
}
.panel-fade-enter-to,
.panel-fade-leave-from {
	opacity: 1;
}

.add-btn {
	display: flex;
	align-items: center;
	gap: 8rpx;
	padding: 12rpx 20rpx;
	border-radius: 12rpx;
	background: rgba(184, 107, 31, 0.12);
	color: #7a4e18;
	font-size: 26rpx;
	font-weight: 600;
	transition: background 0.2s ease, transform 0.2s ease;
	cursor: pointer;
}
.add-btn:hover {
	background: rgba(184, 107, 31, 0.2);
}
.add-btn:active {
	background: rgba(184, 107, 31, 0.25);
	transform: scale(0.97);
}

.add-icon {
	width: 32rpx;
	height: 32rpx;
}

.empty-day {
	text-align: center;
	padding: 56rpx 40rpx 64rpx;
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}

.empty-illus {
	width: 160rpx;
	height: 160rpx;
	margin: 0 auto 36rpx;
	border-radius: 50%;
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
	overflow: hidden;
}

.empty-icon-gradient {
	position: absolute;
	inset: 0;
	background: linear-gradient(135deg, rgba(184, 107, 31, 0.18) 0%, rgba(141, 110, 99, 0.08) 50%, rgba(184, 107, 31, 0.12) 100%);
}

.empty-icon {
	width: 72rpx;
	height: 72rpx;
	opacity: 0.65;
	position: relative;
	z-index: 1;
}

.empty-text {
	display: block;
	font-size: 34rpx;
	color: #4a4a4a;
	font-weight: 600;
	letter-spacing: -0.02em;
}
.empty-hint {
	display: block;
	font-size: 28rpx;
	color: #888;
	margin-top: 12rpx;
	letter-spacing: 0.01em;
}

.empty-add-btn {
	display: inline-flex;
	align-items: center;
	gap: 10rpx;
	margin-top: 32rpx;
	padding: 20rpx 36rpx;
	border-radius: 16rpx;
	background: rgba(184, 107, 31, 0.2);
	border: 2rpx solid rgba(184, 107, 31, 0.35);
	color: #7a4e18;
	font-size: 28rpx;
	font-weight: 700;
	transition: background 0.2s ease, transform 0.2s ease;
	cursor: pointer;
}
.empty-add-btn:hover {
	background: rgba(184, 107, 31, 0.28);
}
.empty-add-btn:active {
	background: rgba(184, 107, 31, 0.35);
	transform: scale(0.97);
}
.empty-add-btn .add-icon {
	width: 36rpx;
	height: 36rpx;
}

.outfit-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	flex: 1;
	min-height: 0;
	overflow-y: auto;
	padding-right: 8rpx;
}
.outfit-list-footer {
	margin-top: auto;
	padding-top: 24rpx;
	border-top: 1rpx solid rgba(0, 0, 0, 0.06);
}
.clear-all-btn {
	width: 100%;
	padding: 18rpx 28rpx;
	border-radius: 16rpx;
	background: rgba(184, 107, 31, 0.1);
	border: 1rpx solid rgba(184, 107, 31, 0.2);
	color: #8d6e63;
	font-size: 28rpx;
	font-weight: 600;
	text-align: center;
	transition: background 0.2s ease, transform 0.2s ease;
	cursor: pointer;
}
.clear-all-btn:hover {
	background: rgba(184, 107, 31, 0.15);
	border-color: rgba(184, 107, 31, 0.3);
}
.clear-all-btn:active {
	background: rgba(184, 107, 31, 0.2);
	transform: scale(0.98);
}

/* 日记卡片风格：无分割线，用留白分隔，hover 时浮起 */
.outfit-item {
	display: flex;
	align-items: center;
	gap: 20rpx;
	padding: 24rpx 28rpx;
	border-radius: 24rpx;
	background: #fff;
	border: none;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.03);
	transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.3s ease;
}
.outfit-item:hover {
	transform: translateY(-4rpx);
	box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.08), 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
	cursor: pointer;
}
/* 瀑布流入场：依次从下往上浮起 + 淡入 */
.outfit-item-enter {
	opacity: 0;
	transform: translateY(24rpx);
	animation: outfit-item-enter 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
@keyframes outfit-item-enter {
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.outfit-item-leave {
	animation: outfit-item-leave 0.3s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
@keyframes outfit-item-leave {
	from {
		opacity: 1;
		transform: translateY(0) scale(1);
	}
	to {
		opacity: 0;
		transform: translateY(-24rpx) scale(0.95);
	}
}

.outfit-list.is-clearing {
	pointer-events: none;
}

.outfit-list-footer.is-clearing {
	opacity: 0;
	transition: opacity 0.2s ease;
}

.outfit-thumb-wrap {
	position: relative;
	flex-shrink: 0;
	border-radius: 20rpx;
	overflow: hidden;
	box-shadow: inset 6rpx 0 0 0 var(--thumb-accent, #8d6e63);
}

.outfit-thumb {
	width: 100rpx;
	height: 100rpx;
	border-radius: 14rpx 20rpx 20rpx 14rpx;
	background: #f5f2ee;
	display: block;
}
.outfit-thumb.placeholder {
	background: #e8e4df;
}

.outfit-name {
	flex: 1;
	font-size: 28rpx;
	font-weight: 500;
	color: #333;
	letter-spacing: 0.01em;
	line-height: 1.4;
}

.remove-btn {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 50%;
	opacity: 0.85;
	transition: opacity 0.2s ease, background 0.2s ease;
	flex-shrink: 0;
}
.remove-btn:hover {
	opacity: 1;
	background: rgba(0, 0, 0, 0.06);
}
.remove-btn:active {
	opacity: 1;
	background: rgba(0, 0, 0, 0.1);
}
.remove-icon {
	width: 28rpx;
	height: 28rpx;
}


/* 响应式：Mobile 上下结构 */
@media (max-width: 768px) {
	.main-wrapper {
		flex-direction: column;
		align-items: stretch;
	}
	.main-left {
		flex: none;
		max-width: 100%;
		min-width: 0;
	}
	.main-right {
		flex: none;
		min-width: 0;
		max-width: 100%;
	}
	.calendar-block {
		max-width: 100%;
	}
}
</style>
