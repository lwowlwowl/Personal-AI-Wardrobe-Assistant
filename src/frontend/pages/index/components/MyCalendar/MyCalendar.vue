<template>
	<view
		class="calendar-container"
		@mousemove="onMagneticMouseMove"
		@mouseleave="onMagneticMouseLeave"
	>
		<view class="calendar-inner">
			<text class="bg-watermark">{{ monthLabel.split(' ')[0].toUpperCase() }}</text>

			<view class="scatter-bg-container" :class="{ 'panel-open': selectedDateKey }" aria-hidden="true">
				<transition-group name="scatter-polaroid" tag="view" class="scatter-transition-group">
				<view
					v-for="(item, index) in backgroundScatterItems"
						:key="'scatter-' + monthKey + '-' + (item.id != null ? item.id : 'i' + index)"
					class="scatter-card"
					:style="item.style"
				>
					<view class="scatter-thumb-wrap">
						<image :src="item.image" mode="aspectFill" class="scatter-img" />
					</view>
				</view>
				</transition-group>
			</view>

			<view class="wardrobe-decor" aria-hidden="true">
				<view class="tailor-mark top-left"></view>
				<view class="tailor-mark bottom-right"></view>

				<view class="pattern-curve"></view>

			</view>
			<!-- Main: centered when no day selected; when selected, calendar shrinks back and right panel floats in front -->
			<view class="main-wrapper">
				<!-- Left: calendar + This Month (is-shrunk when selected: narrower to make room for the drawer) -->
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
											<!-- Outfit preview overlay: shown on hover -->
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

				<!-- FLIP shared element: flies from day cell to panel header -->
				<view
					v-if="flyVisible"
					class="fly-date-pill"
					:style="flyStyle"
					@transitionend="onFlyTransitionEnd"
				>
					<text class="fly-date-pill-text">{{ flyLabel }}</text>
				</view>
				<!-- Right: outfit panel (absolute centered when selected, top stacking) -->
				<transition name="split-panel-fade">
					<view v-if="selectedDateKey" class="main-right">
						<view class="outfit-panel glass-panel">
							<view class="outfit-panel-header" ref="panelHeaderRef">
								<view class="outfit-header-row1">
									<text class="outfit-panel-title">{{ selectedDateLabel }}</text>
									<view class="close-panel-btn magnetic-btn" @click="closePanel" role="button" aria-label="Close panel">
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
import { formatApiErrorMessage } from '@/utils/apiErrors.js'

/** Build date key string YYYY-MM-DD from year, month, day */
function toDateKey(y, m, d) {
	const pad = (n) => String(n).padStart(2, '0')
	return `${y}-${pad(m + 1)}-${pad(d)}`
}

/** Normalize backend item to frontend shape (image as absolute URL) */
function normalizeItem(item) {
	if (!item) return item
	let image = item.image || item.image_url || ''
	if (image && image.startsWith('/') && !image.startsWith('//')) {
		image = `${API_BASE_URL}${image}`
	}
	return {
		id: item.id,
		name: item.name || 'Unnamed',
		image,
		accentColor: item.accentColor || item.accent_color || '#8d6e63'
	}
}

/** Season from month (Northern hemisphere: Mar–May spring, Jun–Aug summer, Sep–Nov autumn, Dec–Feb winter) */
function getSeasonForDateKey(dateKey) {
	const [, m] = dateKey.split('-')
	const month = parseInt(m, 10)
	if (month >= 3 && month <= 5) return 'Spring'
	if (month >= 6 && month <= 8) return 'Summer'
	if (month >= 9 && month <= 11) return 'Autumn'
	return 'Winter'
}

/**
 * Day streak: consecutive days with at least one outfit in the viewed month.
 * outfitsByDate: plain object { "YYYY-MM-DD": items[] }
 */
function calculateStreakFromMap(outfitsByDate, viewYear, viewMonth) {
	const today = new Date()
	const todayYear = today.getFullYear()
	const todayMonth = today.getMonth()

	let startDate = new Date()

	if (viewYear === todayYear && viewMonth === todayMonth) {
		const todayKey = toDateKey(todayYear, todayMonth, today.getDate())
		const todayHasRecord = outfitsByDate[todayKey]?.length > 0
		if (!todayHasRecord) {
			return 0
		}
	} else if (viewYear < todayYear || (viewYear === todayYear && viewMonth < todayMonth)) {
		const lastDay = new Date(viewYear, viewMonth + 1, 0)
		const firstDay = new Date(viewYear, viewMonth, 1)

		let foundStart = false
		let checkDate = new Date(lastDay)

		while (checkDate >= firstDay) {
			const key = toDateKey(checkDate.getFullYear(), checkDate.getMonth(), checkDate.getDate())
			if (outfitsByDate[key]?.length > 0) {
				startDate = new Date(checkDate)
				foundStart = true
				break
			}
			checkDate.setDate(checkDate.getDate() - 1)
		}

		if (!foundStart) {
			return 0
		}
	} else {
		return 0
	}

	const viewMonth0 = viewMonth
	let streak = 0
	let checkDate = new Date(startDate)
	while (true) {
		const y = checkDate.getFullYear()
		const m = checkDate.getMonth()
		if (y !== viewYear || m !== viewMonth0) break
		const key = toDateKey(y, m, checkDate.getDate())
		if (outfitsByDate[key]?.length > 0) {
			streak++
			checkDate.setDate(checkDate.getDate() - 1)
		} else {
			break
		}
	}
	return streak
}

/** Month stats (uniqueItems deduped by item.id) */
function computeMonthStats(outfitsByDate, year, month) {
	const prefix = `${year}-${String(month + 1).padStart(2, '0')}-`
	let daysRecorded = 0
	const uniqueIds = new Set()
	for (const [key, items] of Object.entries(outfitsByDate)) {
		if (key.startsWith(prefix) && items?.length) {
			daysRecorded++
			for (const item of items) {
				if (item.id != null) uniqueIds.add(item.id)
			}
		}
	}
	return { daysRecorded, uniqueItems: uniqueIds.size }
}

/** Build 42 calendar cells: current month plus leading/trailing padding */
function buildCalendarCells(year, month) {
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
}

/** Format date for panel title (FLIP fly-in label) */
function formatDateLabel(dateKey) {
	if (!dateKey) return ''
	const [y, m, d] = dateKey.split('-')
	const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d))
	return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
}

/** Format date shown in hover preview */
function formatPreviewDate(dateKey) {
	const [y, m, d] = dateKey.split('-')
	const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d))
	return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

const userToken = ref(uni.getStorageSync('auth_token') || '')
const currentDate = new Date()
const displayYear = ref(currentDate.getFullYear())
const displayMonth = ref(currentDate.getMonth())
const slideDirection = ref('right') // 'left' | 'right' — month switch animation direction
/** No selection on load so full calendar shows first; floating panel after picking a day */
const selectedDateKey = ref(null)
const showAddPanel = ref(false)
const hoveredDateKey = ref(null) // hover preview overlay
const isClearing = ref(false) // clearing animation when removing all outfits for a day

// Glass / animation / FLIP
const gridMouseX = ref(null)
const gridMouseY = ref(null)
const gridWrapRef = ref(null)
const panelHeaderRef = ref(null)
const outfitListRef = ref(null)
const outfitListScroll = ref(0)
const emptyIllusRef = ref(null)
const emptyIllusMouseX = ref(null) // 0–100% for empty-state card sheen
const emptyIllusMouseY = ref(null)
const flyVisible = ref(false)
const flyStyle = ref({})
const flyLabel = ref('')
let flyTransitionEndHandler = null

// Magnetic cursor: within 20px of a button, pull toward pointer; spring back on leave
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

/** Calendar grid style for glow tracking (CSS vars) */
const gridMouseStyle = computed(() => {
	if (gridMouseX.value == null || gridMouseY.value == null) return {}
	return {
		'--mouse-x': gridMouseX.value + 'px',
		'--mouse-y': gridMouseY.value + 'px'
	}
})

/** Mouse position on empty-state card (percent) for holographic sheen */
const emptyIllusMouseStyle = computed(() => {
	if (emptyIllusMouseX.value == null || emptyIllusMouseY.value == null) {
		return { '--mouse-x': '50%', '--mouse-y': '50%' }
	}
	return {
		'--mouse-x': emptyIllusMouseX.value + '%',
		'--mouse-y': emptyIllusMouseY.value + '%'
	}
})

/** Days in current month (progress bar denominator) */
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

/** Outfits by date from GET /api/calendar/outfits: { "2025-02-09": [{ id, name, image, accentColor? }] } */
const outfitsByDate = ref({})

/** Background scatter cards (moodboard): up to 8, split left/right, staggered vertically */
const backgroundScatterItems = computed(() => {
	// Tied to viewed month so month change retriggers transition-group (data may lag until fetch completes)
	displayYear.value
	displayMonth.value

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
		// Scale: 0.85 + [0, 0.5) → ~0.85–1.35
		const scale = 0.85 + Math.random() * 0.5
		// Opacity: 0.6 + [0, 0.35) → ~0.6–0.95
		const opacity = 0.6 + Math.random() * 0.35

		return {
			...item,
			style: {
				left: `${left}%`,
				top: `${top}%`,
				'--r': `${rotation}deg`,
				'--s': scale,
				'--opacity': opacity,
				'--scatter-enter-delay': `${index * 55}ms`,
				'--scatter-leave-delay': `${(maxCards - 1 - index) * 40}ms`
			}
		}
	})
})

/** Fetch outfits for the displayed month */
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
			month: displayMonth.value + 1 // API expects 1–12
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
		uni.showToast({
			title: e?.message || 'Could not load calendar. Check your connection and try again.',
			icon: 'none',
			duration: 3500
		})
	}
}

/** Existing outfits for selected day (passed to AddOutfitPanel) */
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

/** Selected day summary: outfit count and season from month (not item tags) */
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

const currentStreak = computed(() =>
	calculateStreakFromMap(outfitsByDate.value, displayYear.value, displayMonth.value)
)

/** Month stats (same rules as my_calendar_api.md: uniqueItems by item.id) */
const monthStats = computed(() =>
	computeMonthStats(outfitsByDate.value, displayYear.value, displayMonth.value)
)

const calendarCells = computed(() => buildCalendarCells(displayYear.value, displayMonth.value))

/** Previous month; slide direction left for animation */
function prevMonth() {
	slideDirection.value = 'left'
	if (displayMonth.value === 0) {
		displayMonth.value = 11
		displayYear.value--
	} else {
		displayMonth.value--
	}
}

/** Next month; slide direction right for animation */
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

defineExpose({ refetch: fetchMonthOutfits })

/** Day cell enter: diagonal wave delay by row+col (spring feel) */
function getDayCellStyle(idx) {
	const row = Math.floor(idx / 7)
	const col = idx % 7
	const delay = (row + col) * 28
	return { animationDelay: delay + 'ms' }
}

/** Calendar grid mousemove: update CSS vars for glow */
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

/** Magnetic pull: offset from button ref and global mouse */
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

/** Magnetic button transform (spring return via CSS transition) */
function magneticStyle(offset) {
	if (!offset || (offset.x === 0 && offset.y === 0)) return {}
	return { transform: `translate(${offset.x}px, ${offset.y}px)` }
}

/** Empty-state card: mouse position % on card for sheen */
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

/** Select day: FLIP shared element + exit Add mode if open */
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

/** Right list item: enter delay + scroll parallax tilt (--tilt with enter animation) */
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

/** Confirm add outfit: POST full replace, then update local state */
async function handleAddOutfitConfirm(selectedItems) {
	if (!selectedDateKey.value) return
	const token = userToken.value
	if (!token) {
		uni.showToast({ title: 'Please sign in first.', icon: 'none' })
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
			closePanel()
		} else {
			uni.showToast({
				title: formatApiErrorMessage(res.data, 'Could not save outfit. Please try again.'),
				icon: 'none',
				duration: 4000
			})
			showAddPanel.value = false
		}
	} catch (e) {
		uni.showToast({
			title: e?.message || 'Could not save outfit. Check your network and try again.',
			icon: 'none',
			duration: 3500
		})
		showAddPanel.value = false
	}
}

/** Open Add Outfit panel */
function openAddPanel() {
	userToken.value = uni.getStorageSync('auth_token') || userToken.value
	showAddPanel.value = true
}

/** Close Add Outfit panel */
function closeAddPanel() {
	showAddPanel.value = false
}

/** Close floating panel; calendar regains focus */
function closePanel() {
	selectedDateKey.value = null
	showAddPanel.value = false
}

/** Remove outfit at index for date: optimistic local update then POST full replace */
async function removeOutfit(dateKey, index) {
	if (!outfitsByDate.value[dateKey]) return
	const token = userToken.value
	if (!token) {
		uni.showToast({ title: 'Please sign in first.', icon: 'none' })
		return
	}

	// Optimistic local update first
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
			uni.showToast({
				title: formatApiErrorMessage(res.data, 'Could not update outfits. Please try again.'),
				icon: 'none',
				duration: 4000
			})
		}
	} catch (e) {
		uni.showToast({
			title: e?.message || 'Could not update outfits. Check your network and try again.',
			icon: 'none',
			duration: 3500
		})
	}
}

/** Clear all outfits for selected day: after animation, POST items:[] */
function clearAllOutfits() {
	if (!selectedDateKey.value) return
	const items = outfitsByDate.value[selectedDateKey.value] || []
	if (items.length === 0) return
	const token = userToken.value
	if (!token) {
		uni.showToast({ title: 'Please sign in first.', icon: 'none' })
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
				uni.showToast({
					title: formatApiErrorMessage(res.data, 'Could not clear outfits. Please try again.'),
					icon: 'none',
					duration: 4000
				})
			}
		} catch (e) {
			uni.showToast({
				title: e?.message || 'Could not clear outfits. Check your network and try again.',
				icon: 'none',
				duration: 3500
			})
		}
		setTimeout(() => { isClearing.value = false }, 100)
	}, totalItemAnimation)
}
</script>

<style scoped lang="scss">
@use './MyCalendar.scss' as *;
</style>
