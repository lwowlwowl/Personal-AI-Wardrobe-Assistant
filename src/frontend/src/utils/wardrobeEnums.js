/**
 * 衣橱枚举：API 使用 code（小写+下划线），UI 使用 label。
 * 列表展示用 label，请求/筛选用 value（code）。
 */

// wardrobeEnums.js
// 根据数据库枚举更新分类选项
export const TYPE_OPTIONS = [
  { value: 'top', label: '上衣' },
  { value: 'bottom', label: '下装' },
  { value: 'dress', label: '连衣裙' },
  { value: 'outerwear', label: '外套' },
  { value: 'footwear', label: '鞋履' },
  { value: 'accessory', label: '配饰' },
  { value: 'bag', label: '包包' },
  { value: 'underwear', label: '内衣' },
  { value: 'other', label: '其他' }
]

// 颜色选项
export const COLOR_OPTIONS = [
  { value: 'white', label: '白色' },
  { value: 'black', label: '黑色' },
  { value: 'red', label: '红色' },
  { value: 'blue', label: '蓝色' },
  { value: 'green', label: '绿色' },
  { value: 'yellow', label: '黄色' },
  { value: 'pink', label: '粉色' },
  { value: 'purple', label: '紫色' },
  { value: 'gray', label: '灰色' },
  { value: 'brown', label: '棕色' },
  { value: 'beige', label: '米色' },
  { value: 'navy', label: '藏青色' },
  { value: 'orange', label: '橙色' },
  { value: 'multi', label: '多色' }
]

// 季节选项
export const SEASON_OPTIONS = [
  { value: 'spring', label: '春季' },
  { value: 'summer', label: '夏季' },
  { value: 'autumn', label: '秋季' },
  { value: 'winter', label: '冬季' },
  { value: 'all', label: '四季' }
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
