/**
 * WardrobeAnalysis 模拟数据（API 失败或未登录时使用）
 * 不放在 Vue 内，便于维护与替换为真实 API。
 */

/** 预设展示用常数（Top color/style 等） */
export const DEFAULT_TOP_COLOR_NAME = 'Brown'
export const DEFAULT_TOP_STYLE_NAME = 'Sporty'

/** IdleItemsView 摘要卡「总件数」无数据时的预设显示 */
export const DEFAULT_TOTAL_ITEMS_DISPLAY = 106

/**
 * 获取模拟趋势数据（按 viewBy: 'yearly' | 'monthly' | 'weekly'）
 * @returns {{ labels: string[], values: number[], total_count: number }}
 */
export function getMockTrendData(viewBy) {
	if (viewBy === 'yearly') {
		return {
			labels: ['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023'],
			values: [5, 12, 20, 18, 30, 60, 90, 106],
			total_count: 106
		}
	}
	if (viewBy === 'monthly') {
		const months = []
		const data = []
		const now = new Date()
		for (let i = 11; i >= 0; i--) {
			const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
			months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
			data.push(Math.floor(Math.random() * 20) + 5)
		}
		return {
			labels: months,
			values: data,
			total_count: data[data.length - 1] ?? 0
		}
	}
	// weekly：最近 7 天，X 轴为星期缩写（与 ActivityReport 周视图一致）
	const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
	const days = []
	const data = []
	const now = new Date()
	for (let i = 6; i >= 0; i--) {
		const d = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
		days.push(dayNames[d.getDay()])
		data.push(Math.floor(Math.random() * 5) + 100)
	}
	return {
		labels: days,
		values: data,
		total_count: data[data.length - 1] ?? 0
	}
}

/**
 * 获取模拟「最常穿」清单（按 timeRange: 'yearly' | 'monthly' | 'daily'）
 * @returns {{ name: string, wears: number, color: string }[]}
 */
export function getMockWornData(timeRange) {
	if (timeRange === 'yearly') {
		return [
			{ name: 'White Cotton T-shirt', wears: 35, color: 'white' },
			{ name: 'Classic Denim Jacket', wears: 28, color: 'blue' },
			{ name: 'Black Knit Top', wears: 27, color: 'black' },
			{ name: 'Khaki Chino Pants', wears: 24, color: 'brown' },
			{ name: 'Navy Striped Tee', wears: 22, color: 'navy' }
		]
	}
	if (timeRange === 'monthly') {
		return [
			{ name: 'White Cotton T-shirt', wears: 8, color: 'white' },
			{ name: 'Black Knit Top', wears: 6, color: 'black' },
			{ name: 'Classic Denim Jacket', wears: 5, color: 'blue' },
			{ name: 'Navy Striped Tee', wears: 4, color: 'navy' },
			{ name: 'Khaki Chino Pants', wears: 3, color: 'brown' }
		]
	}
	// daily
	return [
		{ name: 'White Cotton T-shirt', wears: 1, color: 'white' },
		{ name: 'Black Knit Top', wears: 0, color: 'black' },
		{ name: 'Classic Denim Jacket', wears: 0, color: 'blue' },
		{ name: 'Khaki Chino Pants', wears: 0, color: 'brown' },
		{ name: 'Navy Striped Tee', wears: 0, color: 'navy' }
	]
}

/** ActivityReport：每周每日穿搭次数（与下方分类总 wears 一致） */
export const MOCK_WEEK_DATA = [
	{ label: 'Mon', wears: 10 },
	{ label: 'Tue', wears: 16 },
	{ label: 'Wed', wears: 8 },
	{ label: 'Thu', wears: 18 },
	{ label: 'Fri', wears: 12 },
	{ label: 'Sat', wears: 24 },
	{ label: 'Sun', wears: 18 }
]

/** 本周总穿戴次数（主面板 Wardrobe Activity 与展开页 KPI 共用，= MOCK_WEEK_DATA 之和 = MOCK_CATEGORY_ACTIVITY 之和） */
export const MOCK_WEEKLY_TOTAL_WEARS = MOCK_WEEK_DATA.reduce((s, d) => s + d.wears, 0)

/** ActivityReport：按类别活动（与后端 / 衣橱主分类一致，含 Bag、Dress；API 无数据时 fallback） */
export const MOCK_CATEGORY_ACTIVITY = [
	{ name: 'Tops', count: 42, icon: '👕' },
	{ name: 'Bottoms', count: 28, icon: '👖' },
	{ name: 'Outerwear', count: 15, icon: '🧥' },
	{ name: 'Footwear', count: 12, icon: '👟' },
	{ name: 'Accessories', count: 9, icon: '⌚' },
	{ name: 'Bag', count: 0, icon: '👜' },
	{ name: 'Dress', count: 0, icon: '👗' }
]
