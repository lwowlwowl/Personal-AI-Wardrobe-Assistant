/**
 * 衣橱枚举：API 使用 code（小写），UI 使用 label。
 * 主分类（category）与后端写死的 9 个枚举一致；子分类（subcategory）由用户自由输入。
 */

/** 后端写死的主分类（9 个），与 backend models.ClothingCategory 一致 */
export const CATEGORY_OPTIONS = [
	{ label: 'Top', value: 'top' },
	{ label: 'Bottom', value: 'bottom' },
	{ label: 'Dress', value: 'dress' },
	{ label: 'Outerwear', value: 'outerwear' },
	{ label: 'Footwear', value: 'footwear' },
	{ label: 'Accessory', value: 'accessory' },
	{ label: 'Bag', value: 'bag' },
	{ label: 'Underwear', value: 'underwear' },
	{ label: 'Other', value: 'other' },
]

/** @deprecated 请使用 CATEGORY_OPTIONS；保留以兼容旧引用 */
export const TYPE_OPTIONS = CATEGORY_OPTIONS

export const COLOR_OPTIONS = [
	{ label: 'White', value: 'white' },
	{ label: 'Black', value: 'black' },
	{ label: 'Beige', value: 'beige' },
	{ label: 'Brown', value: 'brown' },
	{ label: 'Blue', value: 'blue' },
	{ label: 'Navy', value: 'navy' },
	{ label: 'Olive', value: 'olive' },
	{ label: 'Burnt Orange', value: 'burnt_orange' },
	{ label: 'Black/White', value: 'black_white' },
]

/** 与后端 models.ClothingSeason 一致，含 all_season（四季皆宜） */
export const SEASON_OPTIONS = [
	{ label: 'Spring', value: 'spring' },
	{ label: 'Summer', value: 'summer' },
	{ label: 'Autumn', value: 'autumn' },
	{ label: 'Winter', value: 'winter' },
	{ label: 'All Season', value: 'all_season' },
]

export const DATE_ORDER_OPTIONS = [
	{ label: 'Ascending', value: 'asc' },
	{ label: 'Descending', value: 'desc' },
]

/** category code -> label，用于从接口拿到 category 后显示文案 */
export const TYPE_LABEL_BY_CODE = Object.fromEntries(CATEGORY_OPTIONS.map((o) => [o.value, o.label]))
export const CATEGORY_LABEL_BY_CODE = TYPE_LABEL_BY_CODE
export const COLOR_LABEL_BY_CODE = Object.fromEntries(COLOR_OPTIONS.map((o) => [o.value, o.label]))
export const SEASON_LABEL_BY_CODE = Object.fromEntries(SEASON_OPTIONS.map((o) => [o.value, o.label]))

/** code -> 展示用 hex 色值（与衣服颜色配套，后端联调时由 code 推导，不写死在前端列表里） */
export const COLOR_HEX_BY_CODE = {
	white: '#f5f5f5',
	black: '#616161',
	beige: '#d7bfa2',
	brown: '#c4a77d',
	blue: '#5c6bc0',
	navy: '#2c3e50',
	olive: '#6b7c3c',
	burnt_orange: '#c45c32',
	black_white: '#8a8a8a',
}

/** 将多个 code 转为展示文案（逗号分隔） */
export function codesToLabels(codes, map) {
	if (!Array.isArray(codes) || !codes.length) return '—'
	return codes.map((c) => map[c] || c).join(', ')
}