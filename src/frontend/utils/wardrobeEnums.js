/**
 * Wardrobe enums: API uses lowercase codes; UI uses labels.
 * Main categories match the nine fixed backend values; subcategory is free text.
 */

/** Fixed main categories (9), aligned with backend models.ClothingCategory */
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

/** @deprecated Prefer CATEGORY_OPTIONS; kept for legacy imports */
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

/** Matches backend models.ClothingSeason, including all_season */
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

/** category code -> label for displaying API category values */
export const TYPE_LABEL_BY_CODE = Object.fromEntries(CATEGORY_OPTIONS.map((o) => [o.value, o.label]))
export const CATEGORY_LABEL_BY_CODE = TYPE_LABEL_BY_CODE
export const COLOR_LABEL_BY_CODE = Object.fromEntries(COLOR_OPTIONS.map((o) => [o.value, o.label]))
export const SEASON_LABEL_BY_CODE = Object.fromEntries(SEASON_OPTIONS.map((o) => [o.value, o.label]))

/** code -> display hex swatch; UI falls back to gray when unknown */
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
	red: '#c62828',
	light_green: '#81c784',
	green: '#66bb6a',
	orange: '#ff9800',
	gray: '#9e9e9e',
	grey: '#9e9e9e',
	// Common extended colors
	purple: '#7e57c2',
	violet: '#8e24aa',
	pink: '#ec407a',
	yellow: '#fdd835',
	gold: '#ffb300',
	silver: '#9e9e9e',
	mint: '#80cbc4',
	coral: '#ff7043',
	burgundy: '#880e4f',
	khaki: '#c3b091',
	cream: '#fff8e1',
	lavender: '#b39ddb',
	teal: '#00897b',
	maroon: '#ad1457',
}

/** Join multiple codes into display text (comma-separated) */
export function codesToLabels(codes, map) {
	if (!Array.isArray(codes) || !codes.length) return '—'
	return codes.map((c) => map[c] || c).join(', ')
}
