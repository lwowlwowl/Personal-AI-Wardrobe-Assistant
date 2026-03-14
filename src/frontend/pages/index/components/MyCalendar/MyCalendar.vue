<template>
	<view
		class="calendar-container"
		@mousemove="onMagneticMouseMove"
		@mouseleave="onMagneticMouseLeave"
	>
		<view class="calendar-inner">
			<text class="bg-watermark">{{ monthLabel.split(' ')[0].toUpperCase() }}</text>

			<view class="scatter-bg-container" :class="{ 'panel-open': selectedDateKey }" aria-hidden="true">
				<view
					v-for="(item, index) in backgroundScatterItems"
					:key="'scatter-' + item.id + '-' + index"
					class="scatter-card"
					:style="item.style"
				>
					<view class="scatter-thumb-wrap">
						<image :src="item.image" mode="aspectFill" class="scatter-img" />
					</view>
				</view>
			</view>

			<view class="wardrobe-decor" aria-hidden="true">
				<view class="tailor-mark top-left"></view>
				<view class="tailor-mark bottom-right"></view>

				<view class="pattern-curve"></view>

				<view class="meta-text left-meta">AI_ANALYSIS: ON // WARDROBE_CAPACITY: 84%</view>
				<view class="meta-text right-meta">
					<text class="care-symbols">⏽ ◿ ⎔</text>
					DRY CLEAN ONLY · HANDLE WITH CARE
				</view>
			</view>
			<!-- 主体：未选中日历时居中；选中时日历后退失焦，右侧面板悬浮于正前方 -->
			<view class="main-wrapper">
				<!-- 左侧：日历 + This Month（选中时 is-shrunk：缩小宽度，为右侧抽屉腾出空间） -->
				<view class="main-left" :class="{ 'is-shrunk': selectedDateKey }">
					<view class="side-panel glass-panel">
						<text class="side-title">This Month</text>
						<view class="stat-bars">
							<view class="stat-bar-wrap">
								<view class="stat-bar-label">
									<text class="stat-num">{{ monthStats.daysRecorded }}</text>
									<text class="stat-label">days recorded</text>
								</view>
								<view class="stat-bar-track">
									<view class="stat-bar-fill" :style="{ width: daysRecordedPercent + '%' }" />
								</view>
							</view>
							<view class="stat-bar-wrap">
								<view class="stat-bar-label">
									<text class="stat-num">{{ monthStats.uniqueItems }}</text>
									<text class="stat-label">unique items</text>
								</view>
								<view class="stat-bar-track">
									<view class="stat-bar-fill stat-bar-fill--secondary" :style="{ width: uniqueItemsPercent + '%' }" />
								</view>
							</view>
							<view v-if="currentStreak > 0" class="stat-bar-wrap streak-bar">
								<view class="stat-bar-label">
									<text class="streak-emoji">🔥</text>
									<text class="stat-num streak-num">{{ currentStreak }}</text>
									<text class="stat-label">day streak</text>
								</view>
								<view class="stat-bar-track">
									<view class="stat-bar-fill stat-bar-fill--streak" :style="{ width: Math.min(currentStreak * 20, 100) + '%' }" />
								</view>
							</view>
						</view>
					</view>
					<view class="calendar-block">
						<view class="calendar-card glass-card">
							<view class="calendar-nav">
								<view
									ref="prevMonthBtnRef"
									class="nav-btn month-switch magnetic-btn"
									:style="magneticStyle(prevMonthOffset)"
									@click="prevMonth"
								>
									<text class="nav-arrow">‹</text>
								</view>
								<text class="month-label">{{ monthLabel }}</text>
								<view
									ref="nextMonthBtnRef"
									class="nav-btn month-switch magnetic-btn"
									:style="magneticStyle(nextMonthOffset)"
									@click="nextMonth"
								>
									<text class="nav-arrow">›</text>
								</view>
							</view>
							<view class="weekday-row">
								<text v-for="d in weekdays" :key="d" class="weekday-cell">{{ d }}</text>
							</view>
							<view
								class="calendar-grid-wrap"
								ref="gridWrapRef"
								:style="gridMouseStyle"
								@mousemove="onGridMouseMove"
								@mouseleave="onGridMouseLeave"
							>
								<view class="day-cell-glow" aria-hidden="true" />
								<transition :name="slideDirection === 'left' ? 'month-slide-left' : 'month-slide-right'" mode="out-in">
									<view :key="monthKey" class="calendar-grid calendar-grid--perspective">
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
											:style="getDayCellStyle(idx)"
											@click="selectDay(cell, $event)"
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

				<!-- FLIP 共享元素：从日格飞向面板标题的浮层 -->
				<view
					v-if="flyVisible"
					class="fly-date-pill"
					:style="flyStyle"
					@transitionend="onFlyTransitionEnd"
				>
					<text class="fly-date-pill-text">{{ flyLabel }}</text>
				</view>
				<!-- 右侧：穿搭面板（选中时 absolute 居中悬浮，景深最前） -->
				<transition name="split-panel-fade">
					<view v-if="selectedDateKey" class="main-right">
						<view class="outfit-panel glass-panel">
							<view class="outfit-panel-header" ref="panelHeaderRef">
								<view class="outfit-header-row1">
									<text class="outfit-panel-title">{{ selectedDateLabel }}</text>
									<view class="close-panel-btn magnetic-btn" @click="closePanel" role="button" aria-label="关闭面板">
										<text class="close-icon">✕</text>
									</view>
								</view>
								<text class="outfit-panel-subtitle">{{ selectedDaySummary }}</text>
								<view
									v-if="!showAddPanel && (outfitsByDate[selectedDateKey]?.length || 0) > 0"
									ref="addBtnPrimaryRef"
									class="add-btn add-btn-primary"
									@click="openAddPanel"
								>
									<image src="/static/icons/icon-plus.svg" mode="aspectFit" class="add-icon" />
									<text>Add Outfit</text>
								</view>
							</view>
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
										<view
											class="empty-illus-wrap"
											ref="emptyIllusRef"
											:style="emptyIllusMouseStyle"
											@mousemove="onEmptyIllusMouseMove"
											@mouseleave="onEmptyIllusMouseLeave"
										>
											<view class="empty-illus-premium">
												<image src="/static/icons/icon-wardrobe.svg" mode="aspectFit" class="empty-illus-icon" />
											</view>
										</view>
										<text class="empty-text">✨ No outfit logged yet</text>
										<text class="empty-hint">Start your style diary today.</text>
										<view
											ref="emptyAddBtnRef"
											class="empty-add-btn"
											@click="openAddPanel"
										>
											<image src="/static/icons/icon-plus.svg" mode="aspectFit" class="add-icon" />
											<text>Add Outfit</text>
										</view>
									</view>
									<view
										v-else
										key="list"
										class="outfit-list"
										ref="outfitListRef"
										:class="{ 'is-clearing': isClearing }"
										:data-scroll="outfitListScroll"
										@scroll="onOutfitListScroll"
									>
									<view
										v-for="(item, i) in outfitsByDate[selectedDateKey]"
										:key="item.id || i"
										class="outfit-item"
										:class="{ 
											'outfit-item-enter': !isClearing,
											'outfit-item-leave': isClearing
										}"
										:style="getOutfitItemStyle(i)"
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
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import AddOutfitPanel from './AddOutfitPanel.vue'
import { getCalendarOutfits, saveCalendarOutfits, API_BASE_URL } from '@/api/calendarApi.js'

const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const userToken = ref(uni.getStorageSync('auth_token') || '')
const currentDate = new Date()
const displayYear = ref(currentDate.getFullYear())
const displayMonth = ref(currentDate.getMonth())
const slideDirection = ref('right') // 'left' | 'right' - 用于月份切换动画方向
/** 进入页面时预设不选中，展现完整日历（点选某日后再出现悬浮面板） */
const selectedDateKey = ref(null)
const showAddPanel = ref(false)
const hoveredDateKey = ref(null) // 用于 hover 预览浮层
const isClearing = ref(false) // 用于清除动画状态（清空当天全部时使用）

// 玻璃态 / 动画 / FLIP
const gridMouseX = ref(null)
const gridMouseY = ref(null)
const gridWrapRef = ref(null)
const panelHeaderRef = ref(null)
const outfitListRef = ref(null)
const outfitListScroll = ref(0)
const emptyIllusRef = ref(null)
const emptyIllusMouseX = ref(null) // 百分比 0–100，用于空状态卡片反光
const emptyIllusMouseY = ref(null)
const flyVisible = ref(false)
const flyStyle = ref({})
const flyLabel = ref('')
let flyTransitionEndHandler = null

// 磁吸光标：鼠标靠近按钮 20px 时按钮向鼠标偏移，松开后弹簧回弹
const MAGNETIC_RADIUS = 20
const MAGNETIC_MAX_PULL = 10
const prevMonthBtnRef = ref(null)
const nextMonthBtnRef = ref(null)
const addBtnPrimaryRef = ref(null)
const emptyAddBtnRef = ref(null)
const globalMouseX = ref(null)
const globalMouseY = ref(null)
const prevMonthOffset = ref({ x: 0, y: 0 })
const nextMonthOffset = ref({ x: 0, y: 0 })
const addBtnPrimaryOffset = ref({ x: 0, y: 0 })
const emptyAddBtnOffset = ref({ x: 0, y: 0 })

/** 鼠标在日历网格上的样式（用于光晕追踪） */
const gridMouseStyle = computed(() => {
	if (gridMouseX.value == null || gridMouseY.value == null) return {}
	return {
		'--mouse-x': gridMouseX.value + 'px',
		'--mouse-y': gridMouseY.value + 'px'
	}
})

/** 空状态卡片上的鼠标位置（百分比，用于全息反光） */
const emptyIllusMouseStyle = computed(() => {
	if (emptyIllusMouseX.value == null || emptyIllusMouseY.value == null) {
		return { '--mouse-x': '50%', '--mouse-y': '50%' }
	}
	return {
		'--mouse-x': emptyIllusMouseX.value + '%',
		'--mouse-y': emptyIllusMouseY.value + '%'
	}
})

/** 本月天数（用于进度条分母） */
const daysInCurrentMonth = computed(() => {
	const d = new Date(displayYear.value, displayMonth.value + 1, 0)
	return d.getDate()
})

const daysRecordedPercent = computed(() => {
	const n = monthStats.value.daysRecorded
	const total = daysInCurrentMonth.value || 31
	return Math.min(100, Math.round((n / total) * 100))
})

const uniqueItemsPercent = computed(() => {
	const n = monthStats.value.uniqueItems
	const cap = 50
	return Math.min(100, Math.round((n / cap) * 100))
})

/** 每日穿搭记录：{ "2025-02-09": [{ id, name, image, accentColor? }] }，来自后端 GET /api/calendar/outfits */
const outfitsByDate = ref({})

/** 背景散落卡片 (Moodboard Scatter) - 分区均匀散布：最多 8 张，左 4 右 4，垂直区间错开 */
const backgroundScatterItems = computed(() => {
	const allItems = []
	const seenIds = new Set()

	for (const key in outfitsByDate.value) {
		const outfits = outfitsByDate.value[key]
		if (outfits && outfits.length) {
			for (const item of outfits) {
				if (item.image && !seenIds.has(item.id)) {
					seenIds.add(item.id)
					allItems.push(item)
				}
			}
		}
	}

	const maxCards = 8
	const selectedItems = allItems.sort(() => Math.random() - 0.5).slice(0, maxCards)

	return selectedItems.map((item, index) => {
		const isLeft = index % 2 === 0
		const baseLeft = isLeft ? 2 : 78
		const left = baseLeft + (Math.random() * 8)

		const itemsPerSide = Math.ceil(maxCards / 2)
		const verticalSlot = Math.floor(index / 2)
		const slotHeight = 85 / itemsPerSide
		const top = (verticalSlot * slotHeight) + (Math.random() * (slotHeight * 0.4)) + 2

		const rotation = (Math.random() - 0.5) * 30
		// 缩放范围：0.85 + [0, 0.5) = 0.85 ~ 1.35
		const scale = 0.85 + Math.random() * 0.5
		// 透明度范围：0.6 + [0, 0.35) = 0.6 ~ 0.95
		const opacity = 0.6 + Math.random() * 0.35

		return {
			...item,
			style: {
				left: `${left}%`,
				top: `${top}%`,
				'--r': `${rotation}deg`,
				'--s': scale,
				'--opacity': opacity
			}
		}
	})
})

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

/** 日格入场动画：按行列斜向波浪延迟（Spring） */
function getDayCellStyle(idx) {
	const row = Math.floor(idx / 7)
	const col = idx % 7
	const delay = (row + col) * 28
	return { animationDelay: delay + 'ms' }
}

/** 日历网格鼠标移动：更新 CSS 变量供光晕使用 */
function onGridMouseMove(e) {
	const el = gridWrapRef.value
	if (!el) return
	const rect = el.getBoundingClientRect?.() ?? { left: 0, top: 0 }
	const x = (e.clientX ?? e.touches?.[0]?.clientX ?? 0) - rect.left
	const y = (e.clientY ?? e.touches?.[0]?.clientY ?? 0) - rect.top
	gridMouseX.value = x
	gridMouseY.value = y
}

function onGridMouseLeave() {
	gridMouseX.value = null
	gridMouseY.value = null
}

/** 磁吸：根据按钮 ref 与全局鼠标位置计算偏移 */
function getMagneticOffset(btnRef) {
	const mx = globalMouseX.value
	const my = globalMouseY.value
	if (mx == null || my == null) return { x: 0, y: 0 }
	const el = btnRef?.value?.$el ?? btnRef?.value
	if (!el?.getBoundingClientRect) return { x: 0, y: 0 }
	const rect = el.getBoundingClientRect()
	const cx = rect.left + rect.width / 2
	const cy = rect.top + rect.height / 2
	const dx = mx - cx
	const dy = my - cy
	const distance = Math.sqrt(dx * dx + dy * dy)
	if (distance >= MAGNETIC_RADIUS || distance < 1) return { x: 0, y: 0 }
	const pull = (1 - distance / MAGNETIC_RADIUS) * MAGNETIC_MAX_PULL
	const len = distance
	return {
		x: (dx / len) * pull,
		y: (dy / len) * pull
	}
}

function onMagneticMouseMove(e) {
	globalMouseX.value = e.clientX ?? e.touches?.[0]?.clientX ?? null
	globalMouseY.value = e.clientY ?? e.touches?.[0]?.clientY ?? null
	prevMonthOffset.value = getMagneticOffset(prevMonthBtnRef)
	nextMonthOffset.value = getMagneticOffset(nextMonthBtnRef)
	addBtnPrimaryOffset.value = getMagneticOffset(addBtnPrimaryRef)
	emptyAddBtnOffset.value = getMagneticOffset(emptyAddBtnRef)
}

function onMagneticMouseLeave() {
	globalMouseX.value = null
	globalMouseY.value = null
	prevMonthOffset.value = { x: 0, y: 0 }
	nextMonthOffset.value = { x: 0, y: 0 }
	addBtnPrimaryOffset.value = { x: 0, y: 0 }
	emptyAddBtnOffset.value = { x: 0, y: 0 }
}

/** 磁吸按钮的 transform 样式（弹簧回弹由 CSS transition 负责） */
function magneticStyle(offset) {
	if (!offset || (offset.x === 0 && offset.y === 0)) return {}
	return { transform: `translate(${offset.x}px, ${offset.y}px)` }
}

/** 空状态卡片：鼠标相对于卡片的百分比，供全息反光使用 */
function onEmptyIllusMouseMove(e) {
	const el = emptyIllusRef.value?.$el ?? emptyIllusRef.value
	if (!el?.getBoundingClientRect) return
	const rect = el.getBoundingClientRect()
	const x = ((e.clientX ?? e.touches?.[0]?.clientX ?? 0) - rect.left) / rect.width * 100
	const y = ((e.clientY ?? e.touches?.[0]?.clientY ?? 0) - rect.top) / rect.height * 100
	emptyIllusMouseX.value = Math.max(0, Math.min(100, x))
	emptyIllusMouseY.value = Math.max(0, Math.min(100, y))
}
function onEmptyIllusMouseLeave() {
	emptyIllusMouseX.value = null
	emptyIllusMouseY.value = null
}

/** 格式化日期为面板标题样式（用于 FLIP 飞入文字） */
function formatDateLabel(dateKey) {
	if (!dateKey) return ''
	const [y, m, d] = dateKey.split('-')
	const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d))
	return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
}

/** 选择日期：FLIP 共享元素飞入 + 若在 Add 模式则退出 */
function selectDay(cell, e) {
	if (showAddPanel.value) {
		showAddPanel.value = false
	}
	const fromRect = e?.currentTarget?.getBoundingClientRect?.() ?? e?.target?.getBoundingClientRect?.() ?? null
	selectedDateKey.value = cell.dateKey
	flyLabel.value = formatDateLabel(cell.dateKey)

	if (fromRect && fromRect.width > 0) {
		flyVisible.value = true
		flyStyle.value = {
			left: fromRect.left + 'px',
			top: fromRect.top + 'px',
			width: fromRect.width + 'px',
			height: fromRect.height + 'px',
			transition: 'none'
		}
		nextTick(() => {
			const header = panelHeaderRef.value
			const el = header?.$el ?? header
			const toRect = el?.getBoundingClientRect?.()
			if (toRect && toRect.width > 0) {
				flyStyle.value = {
					left: toRect.left + 'px',
					top: toRect.top + 'px',
					width: toRect.width + 'px',
					height: toRect.height + 'px',
					transition: '0.52s cubic-bezier(0.34, 1.56, 0.64, 1)'
				}
				flyTransitionEndHandler = () => {
					flyVisible.value = false
					flyTransitionEndHandler = null
				}
			} else {
				flyVisible.value = false
			}
		})
	}
}

function onFlyTransitionEnd() {
	if (flyTransitionEndHandler) flyTransitionEndHandler()
}

function onOutfitListScroll(e) {
	const target = e?.target
	outfitListScroll.value = target ? target.scrollTop : 0
}

/** 右侧列表项：入场延迟 + 滚动视差倾斜（用 --tilt 与入场动画并存） */
function getOutfitItemStyle(i) {
	const scroll = outfitListScroll.value
	const base = 80
	const offset = scroll - i * base
	const tilt = Math.max(-4, Math.min(4, offset * 0.04))
	const delay = i * 50
	return {
		animationDelay: delay + 'ms',
		'--tilt': tilt + 'deg'
	}
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
			// 优先展示后端返回的 detail（例如「穿着日期不能是未来日期」）
			uni.showToast({ title: res.data?.message || res.data?.detail || '保存失败', icon: 'none' })
		}
	} catch (e) {
		uni.showToast({ title: '保存失败', icon: 'none' })
	}
	showAddPanel.value = false
}

/** 打开 Add Outfit 面板 */
function openAddPanel() {
	userToken.value = uni.getStorageSync('auth_token') || userToken.value
	showAddPanel.value = true
}

/** 关闭 Add Outfit 面板 */
function closeAddPanel() {
	showAddPanel.value = false
}

/** 关闭悬浮面板，让日历重新聚焦 */
function closePanel() {
	selectedDateKey.value = null
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
			uni.showToast({ title: res.data?.message || res.data?.detail || '删除失败', icon: 'none' })
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
				uni.showToast({ title: res.data?.message || res.data?.detail || '清除失败', icon: 'none' })
			}
		} catch (e) {
			uni.showToast({ title: '清除失败', icon: 'none' })
		}
		setTimeout(() => { isClearing.value = false }, 100)
	}, totalItemAnimation)
}
</script>

<style scoped>
/* =========================================
   1. 赋予背景「布料纹理」(Fabric Weave Texture)
========================================= */
.calendar-container {
	width: 100%;
	height: 100vh;
	overflow: hidden;
	background-color: #FDFBF7;
	/* 极细的网格线，模拟高级亚麻或纯棉布料的经纬线 */
	background-image:
		linear-gradient(rgba(141, 110, 99, 0.02) 1px, transparent 1px),
		linear-gradient(90deg, rgba(141, 110, 99, 0.02) 1px, transparent 1px);
	background-size: 8rpx 8rpx;
	position: relative;
	z-index: 0;
}

/* =========================================
   2. AI 衣橱主题装饰层 (Thematic Decor)
========================================= */
.wardrobe-decor {
	position: absolute;
	inset: 0;
	pointer-events: none;
	z-index: 0;
	overflow: hidden;
}

/* 裁缝打版十字定位标 (Tailor Crosshairs) */
.tailor-mark {
	position: absolute;
	width: 40rpx;
	height: 40rpx;
}
.tailor-mark::before,
.tailor-mark::after {
	content: '';
	position: absolute;
	background: rgba(184, 107, 31, 0.2);
}
.tailor-mark::before {
	top: 0;
	bottom: 0;
	left: 50%;
	width: 2rpx;
	transform: translateX(-50%);
}
.tailor-mark::after {
	left: 0;
	right: 0;
	top: 50%;
	height: 2rpx;
	transform: translateY(-50%);
}
.tailor-mark.top-left {
	top: 8%;
	left: 6%;
}
.tailor-mark.bottom-right {
	bottom: 8%;
	right: 6%;
}

/* 服装制版弧形虚线 (Pattern Drafting Curve) */
.pattern-curve {
	position: absolute;
	top: -10%;
	left: -5%;
	width: 45vw;
	height: 80vh;
	border: 2rpx dashed rgba(184, 107, 31, 0.08);
	border-radius: 50%;
	transform: rotate(15deg);
}

/* 边缘排版：AI 数据与洗标 (Vertical Editorial Text) */
.meta-text {
	position: absolute;
	font-family: "Courier New", Courier, monospace;
	font-size: 20rpx;
	color: rgba(141, 110, 99, 0.25);
	letter-spacing: 0.15em;
	writing-mode: vertical-rl;
	transform: rotate(180deg);
}

.left-meta {
	bottom: 8%;
	left: 3%;
}

.right-meta {
	top: 8%;
	right: 3%;
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.care-symbols {
	font-family: sans-serif;
	font-size: 28rpx;
	letter-spacing: 0.3em;
	transform: rotate(90deg);
	margin-bottom: 24rpx;
}

/* =========================================
   背景情绪板散落卡片 (Moodboard Scatter) - 高级静态版
========================================= */
.scatter-bg-container {
	position: absolute;
	inset: 0;
	z-index: 0;
	pointer-events: none;
	overflow: hidden;
}

/* 拍立得相纸质感：使用 CSS 变量便于面板打开时统一缩小与降透明 */
.scatter-card {
	position: absolute;
	width: 240rpx;
	height: 280rpx;
	padding: 16rpx 16rpx 56rpx 16rpx;
	background: #ffffff;
	border-radius: 4rpx;
	box-shadow:
		0 30rpx 60rpx rgba(141, 110, 99, 0.12),
		0 4rpx 16rpx rgba(0, 0, 0, 0.06),
		inset 0 0 0 1rpx rgba(0, 0, 0, 0.03);
	filter: contrast(0.95) sepia(10%);
	transform: rotate(var(--r)) scale(var(--s));
	opacity: var(--opacity);
	transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.5s ease;
	will-change: transform;
}

/* 右侧面板打开时：背景卡片等比例缩小且透明度降低，不抢主内容 */
.scatter-bg-container.panel-open .scatter-card {
	transform: rotate(var(--r)) scale(calc(var(--s) * 0.75));
	opacity: calc(var(--opacity) * 0.55);
}

/* 纸胶带 (Masking Tape) 手工质感 */
.scatter-card::before {
	content: '';
	position: absolute;
	top: -12rpx;
	left: 50%;
	width: 80rpx;
	height: 24rpx;
	transform: translateX(-50%) rotate(-2deg);
	background: rgba(230, 225, 215, 0.85);
	box-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.05);
	border-left: 2rpx dashed rgba(255, 255, 255, 0.4);
	border-right: 2rpx dashed rgba(255, 255, 255, 0.4);
	backdrop-filter: blur(2px);
	z-index: 10;
}

.scatter-thumb-wrap {
	width: 100%;
	height: 100%;
	overflow: hidden;
	background: #f5f2ee;
	box-shadow: inset 0 4rpx 10rpx rgba(0, 0, 0, 0.04);
}

.scatter-img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	display: block;
}

.calendar-inner {
	padding: 80rpx 24rpx 48rpx; /* 顶部留白，避免两侧组件贴顶 */
	width: 100%;
	max-width: 100%;
	height: 100%;
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	position: relative;
}

/* =========================================
   巨型环境水印 (解决背景空旷感)
========================================= */
.bg-watermark {
	position: absolute;
	top: 45%;
	left: 50%;
	transform: translate(-50%, -50%);
	font-size: 32vw;
	font-family: "Didot", "Bodoni MT", "Times New Roman", serif;
	font-weight: 700;
	color: rgba(184, 107, 31, 0.03);
	white-space: nowrap;
	pointer-events: none;
	z-index: 0;
	user-select: none;
	letter-spacing: -0.04em;
}

/* =========================================
   1. 容器：移除 gap 和 :has，改用 margin 物理占位
========================================= */
.main-wrapper {
	width: 100%;
	max-width: 2400rpx;
	margin: 0 auto;
	display: flex;
	justify-content: center;
	align-items: center;
	flex: 1;
	min-height: 0;
	position: relative;
	/* 删除了原本的 gap: 0 和 transition: gap */
}

/* =========================================
   2. 左侧日历：让出更多空间
========================================= */
.main-left {
	flex: 0 1 1400rpx;
	width: 100%;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 28rpx;
	/* 该贝塞尔曲线与右边面板保持绝对同步 */
	transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
	will-change: flex-basis, max-width;
}

.main-left.is-shrunk {
	/* 从原来的 1080rpx 改小，给中间留出更多呼吸空间 */
	flex: 0 1 960rpx;
}

/* =========================================
   3. 右侧面板：释放玻璃的完整形态 (移除裁剪)
========================================= */
.main-right {
	position: relative;
	width: 880rpx;
	max-width: 880rpx;
	margin-left: 200rpx;
	height: calc(100vh - 260rpx);
	display: flex;
	flex-direction: column;
	/* 删除 overflow: hidden，让玻璃边框与阴影在滑动全程保持完整，不被切断 */
}

.outfit-panel.glass-panel {
	/* 内部面板强制固定宽度，不受外层 shrink 影响 */
	width: 880rpx;
	flex-shrink: 0;
	height: 100%;
	max-height: 100%;
	/* 下方材质由「重塑高级玻璃材质」区块统一覆盖 */
}

/* =========================================
   4. 右侧抽屉滑入/滑出动画：解耦透明度与空间位移
========================================= */
.split-panel-fade-enter-active,
.split-panel-fade-leave-active {
	/* 透明度用较短的 0.35s ease-out，在位移结束前就已 100% 清晰，消除顿挫感 */
	transition:
		opacity 0.35s ease-out,
		transform 0.6s cubic-bezier(0.16, 1, 0.3, 1),
		max-width 0.6s cubic-bezier(0.16, 1, 0.3, 1),
		margin-left 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}
.split-panel-fade-enter-from,
.split-panel-fade-leave-to {
	opacity: 0;
	transform: translateX(60rpx);
	max-width: 0;
	margin-left: 0;
}
.split-panel-fade-enter-to,
.split-panel-fade-leave-from {
	opacity: 1;
	transform: translateX(0);
	max-width: 880rpx;
	margin-left: 200rpx;
}

/* =========================================
   重塑高级玻璃材质 (Apple-style Glassmorphism)
========================================= */
.glass-panel,
.glass-card {
	/* 底色改为高纯净度透白，与背景 FDFBF7 产生明显对比 */
	background: rgba(255, 255, 255, 0.65);
	backdrop-filter: blur(30px) saturate(120%);
	-webkit-backdrop-filter: blur(30px) saturate(120%);

	/* 顶部与左侧反光白边，模拟玻璃被光照的厚度 */
	border-top: 2rpx solid rgba(255, 255, 255, 1);
	border-left: 2rpx solid rgba(255, 255, 255, 0.8);
	border-right: 1rpx solid rgba(255, 255, 255, 0.4);
	border-bottom: 1rpx solid rgba(255, 255, 255, 0.2);

	box-shadow:
		inset 0 2rpx 0 rgba(255, 255, 255, 0.6), /* 顶部内侧高光 */
		0 12rpx 40rpx rgba(141, 110, 99, 0.06),
		0 4rpx 12rpx rgba(0, 0, 0, 0.03);
}

/* 右侧抽屉面板层级最高，材质更不透明且厚重 */
.outfit-panel.glass-panel {
	background: rgba(255, 255, 255, 0.85);
	backdrop-filter: blur(40px);
	-webkit-backdrop-filter: blur(40px);

	box-shadow:
		inset 0 2rpx 0 rgba(255, 255, 255, 0.8),
		0 40rpx 100rpx rgba(141, 110, 99, 0.12),
		0 10rpx 30rpx rgba(0, 0, 0, 0.04);
}

@supports not (backdrop-filter: blur(1px)) {
	.glass-panel,
	.glass-card {
		background: rgba(255, 255, 255, 0.95);
	}
	.outfit-panel.glass-panel {
		background: #FFFFFF;
	}
}

.side-panel {
	width: 100%;
	padding: 28rpx 32rpx;
	border-radius: 24rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.side-title {
	display: block;
	font-size: 22rpx;
	font-weight: 600;
	color: #aaa;
	text-transform: uppercase;
	letter-spacing: 0.1em;
	margin-bottom: 20rpx;
}

/* 流体进度条：非对称视觉 */
.stat-bars {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}
.stat-bar-wrap {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}
.stat-bar-label {
	display: flex;
	align-items: baseline;
	gap: 8rpx;
}
.stat-bar-track {
	height: 20rpx;
	min-height: 8px;
	border-radius: 999rpx;
	background: rgba(0, 0, 0, 0.08);
	overflow: hidden;
}
.stat-bar-fill {
	height: 100%;
	min-width: 4px;
	border-radius: 999rpx;
	background: linear-gradient(90deg, rgba(184, 107, 31, 0.7) 0%, rgba(141, 110, 99, 0.6) 100%);
	transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.stat-bar-fill--secondary {
	background: linear-gradient(90deg, rgba(100, 80, 70, 0.55) 0%, rgba(120, 95, 85, 0.5) 100%);
}
.stat-bar-fill--streak {
	background: linear-gradient(90deg, rgba(200, 120, 60, 0.75) 0%, rgba(184, 107, 31, 0.65) 100%);
}
.streak-bar .stat-bar-label {
	gap: 6rpx;
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

.calendar-card {
	width: 100%;
	padding: 28rpx 24rpx 32rpx;
	border-radius: 24rpx;
}

/* 日历网格容器：鼠标光晕追踪 */
.calendar-grid-wrap {
	position: relative;
}
.day-cell-glow {
	position: absolute;
	inset: 0;
	pointer-events: none;
	border-radius: 12rpx;
	background: radial-gradient(
		circle 120rpx at var(--mouse-x, -999px) var(--mouse-y, -999px),
		rgba(255, 255, 255, 0.25) 0%,
		rgba(255, 255, 255, 0.08) 40%,
		transparent 70%
	);
	opacity: 0.9;
	transition: opacity 0.2s ease;
	z-index: 0;
}
.calendar-grid-wrap:not(:hover) .day-cell-glow {
	opacity: 0;
}
.calendar-grid--perspective {
	perspective: 1200px;
	transform-style: preserve-3d;
}

/* 右侧 Outfit Panel：玻璃拟态 */
.outfit-panel {
	height: calc(100vh - 260rpx);
	max-height: calc(100vh - 360rpx);
	min-height: 0;
	display: flex;
	flex-direction: column;
	padding: 40rpx 44rpx 52rpx;
	border-radius: 28rpx;
	box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06), 0 2rpx 16rpx rgba(0, 0, 0, 0.03);
}

/* FLIP 共享元素：飞入的日期胶囊 */
.fly-date-pill {
	position: fixed;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0 24rpx;
	border-radius: 16rpx;
	background: rgba(184, 107, 31, 0.2);
	border: 2rpx solid rgba(184, 107, 31, 0.35);
	box-shadow: 0 8rpx 24rpx rgba(184, 107, 31, 0.2);
	z-index: 9999;
	pointer-events: none;
	box-sizing: border-box;
}
.fly-date-pill-text {
	font-size: 32rpx;
	font-weight: 700;
	color: #1d1d1f;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 100%;
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
.close-panel-btn {
	width: 64rpx;
	height: 64rpx;
	border-radius: 50%;
	background: rgba(0, 0, 0, 0.04);
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	transition: all 0.2s ease;
}
.close-panel-btn:hover {
	background: rgba(0, 0, 0, 0.08);
	transform: rotate(90deg);
}
.close-panel-btn:active {
	transform: scale(0.9) rotate(90deg);
}
.close-icon {
	font-size: 32rpx;
	color: #666;
	line-height: 1;
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
.add-btn-primary:active {
	transform: translateY(2rpx);
	box-shadow: inset 0 4rpx 12rpx rgba(0, 0, 0, 0.15);
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
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
	transition: background 0.25s cubic-bezier(0.22, 1, 0.36, 1), transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease;
	cursor: pointer;
}
.nav-btn.magnetic-btn {
	transition: background 0.25s cubic-bezier(0.22, 1, 0.36, 1), transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease;
}
.add-btn.magnetic-btn,
.empty-add-btn.magnetic-btn {
	transition: background 0.2s ease, transform 0.45s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease;
}
.month-switch:hover {
	background: rgba(0, 0, 0, 0.08);
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.06);
}
.month-switch:active {
	transform: scale(0.92) translateY(2rpx);
	background: rgba(0, 0, 0, 0.1);
	box-shadow: inset 0 4rpx 12rpx rgba(0, 0, 0, 0.12);
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
	position: relative;
	z-index: 1;
}

/* 日格：Stagger + Spring 入场（斜向波浪）+ 光随指动 */
.day-cell {
	aspect-ratio: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	border-radius: 12rpx;
	background: transparent;
	border: 1rpx solid transparent;
	transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
	position: relative;
	opacity: 0;
	transform: translateZ(-100px) rotateX(20deg);
	animation: sophisticated-entry 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
@keyframes sophisticated-entry {
	to {
		opacity: 1;
		transform: translateZ(0) rotateX(0);
	}
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
/* 非当月日期：数字用浅灰色，当月日期保持黑色 */
.day-cell.other-month .day-num {
	color: #999;
}
.day-cell.other-month {
	opacity: 0.85;
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
	color: #1d1d1f; /* 当月日期：黑色 */
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
	transform: scale(0.97) translateY(2rpx);
	box-shadow: inset 0 4rpx 12rpx rgba(0, 0, 0, 0.12);
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

/* 空状态：鼠标追踪容器，传递 --mouse-x / --mouse-y 给下方卡片 */
.empty-illus-wrap {
	width: 160rpx;
	height: 160rpx;
	margin: 0 auto 36rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: default;
}

/* Apple 级拟真光影：全息金属/绸缎反光卡片 + 原有衣橱图标 */
.empty-illus-premium {
	position: relative;
	width: 160rpx;
	height: 160rpx;
	border-radius: 40rpx;
	background: linear-gradient(135deg, #f5f2ee 0%, #e8e4df 100%);
	box-shadow:
		inset 2rpx 2rpx 4rpx rgba(255, 255, 255, 0.8),
		inset -2rpx -2rpx 8rpx rgba(0, 0, 0, 0.05),
		0 16rpx 32rpx rgba(141, 110, 99, 0.1);
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
}
.empty-illus-icon {
	width: 72rpx;
	height: 72rpx;
	opacity: 0.7;
	position: relative;
	z-index: 1;
	pointer-events: none;
}

/* 跟随鼠标的光泽反射（丝绸/拉丝金属高光） */
.empty-illus-premium::after {
	content: '';
	position: absolute;
	inset: -50%;
	background: radial-gradient(
		circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
		rgba(255, 255, 255, 0.9) 0%,
		rgba(255, 255, 255, 0) 60%
	);
	mix-blend-mode: overlay;
	pointer-events: none;
	transition: opacity 0.3s ease;
}
.empty-illus-wrap:hover .empty-illus-premium::after {
	opacity: 1;
}
.empty-illus-wrap:not(:hover) .empty-illus-premium::after {
	opacity: 0;
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
	transition: background 0.2s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease;
	cursor: pointer;
}
.empty-add-btn:hover {
	background: rgba(184, 107, 31, 0.28);
}
.empty-add-btn:active {
	background: rgba(184, 107, 31, 0.35);
	transform: scale(0.97) translateY(2rpx);
	box-shadow: inset 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
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
	perspective: 800px;
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
	transition: background 0.2s ease, transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease;
	cursor: pointer;
}
.clear-all-btn:hover {
	background: rgba(184, 107, 31, 0.15);
	border-color: rgba(184, 107, 31, 0.3);
}
.clear-all-btn:active {
	background: rgba(184, 107, 31, 0.2);
	transform: scale(0.98) translateY(2rpx);
	box-shadow: inset 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

/* 日记卡片：滚动视差倾斜 + hover 浮起 */
.outfit-item {
	display: flex;
	align-items: center;
	gap: 20rpx;
	padding: 24rpx 28rpx;
	border-radius: 24rpx;
	background: rgba(255, 255, 255, 0.7);
	backdrop-filter: blur(8px);
	border: 1rpx solid rgba(255, 255, 255, 0.5);
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.03);
	transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
	transform-origin: center center;
	transform: perspective(800px) rotateX(var(--tilt, 0deg));
}
.outfit-item:hover {
	box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.08), 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
	cursor: pointer;
}
/* 瀑布流入场 + 视差倾斜（--tilt 由 JS 更新） */
.outfit-item-enter {
	opacity: 0;
	transform: perspective(800px) translateY(24rpx) rotateX(var(--tilt, 0deg));
	animation: outfit-item-enter 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}
@keyframes outfit-item-enter {
	to {
		opacity: 1;
		transform: perspective(800px) translateY(0) rotateX(var(--tilt, 0deg));
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
		margin-left: 0;
	}
	.calendar-block {
		max-width: 100%;
	}
}
</style>
