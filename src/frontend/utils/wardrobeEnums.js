/**
 * 衣橱枚举：API 使用 code（小写+下划线），UI 使用 label。
 * 列表展示用 label，请求/筛选用 value（code）。
 */

export const TYPE_OPTIONS = [
	{ label: 'Blouse', value: 'blouse' },
	{ label: 'T-Shirt', value: 't_shirt' },
	{ label: 'Top', value: 'top' },
	{ label: 'Vest', value: 'vest' },
	{ label: 'Sweater', value: 'sweater' },
	{ label: 'Shirt', value: 'shirt' },
]

export const COLOR_OPTIONS = [
	{ label: 'White', value: 'white' },
	{ label: 'Black', value: 'black' },
	{ label: 'Beige', value: 'beige' },
	{ label: 'Brown', value: 'brown' },
	{ label: 'Navy', value: 'navy' },
	{ label: 'Olive', value: 'olive' },
	{ label: 'Burnt Orange', value: 'burnt_orange' },
	{ label: 'Black/White', value: 'black_white' },
]

export const SEASON_OPTIONS = [
	{ label: 'Spring', value: 'spring' },
	{ label: 'Summer', value: 'summer' },
	{ label: 'Autumn', value: 'autumn' },
	{ label: 'Winter', value: 'winter' },
]

export const DATE_ORDER_OPTIONS = [
	{ label: 'Ascending', value: 'asc' },
	{ label: 'Descending', value: 'desc' },
]

/** code -> label，用于从接口拿到 code 后显示文案 */
export const TYPE_LABEL_BY_CODE = Object.fromEntries(TYPE_OPTIONS.map((o) => [o.value, o.label]))
export const COLOR_LABEL_BY_CODE = Object.fromEntries(COLOR_OPTIONS.map((o) => [o.value, o.label]))
export const SEASON_LABEL_BY_CODE = Object.fromEntries(SEASON_OPTIONS.map((o) => [o.value, o.label]))

/** 将多个 code 转为展示文案（逗号分隔） */
export function codesToLabels(codes, map) {
	if (!Array.isArray(codes) || !codes.length) return '—'
	return codes.map((c) => map[c] || c).join(', ')
}
