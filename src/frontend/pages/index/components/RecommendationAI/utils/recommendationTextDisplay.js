/** 推荐卡片 / 气泡：去掉 #编号、中英混排加空格，仅影响展示 */

const DOUBLE_SPACE = '  '

export function stripWardrobeHashIds(s) {
	if (s == null || typeof s !== 'string') return ''
	return s
		.replace(/\s*[#＃]\s*\d+\b/g, '')
		.replace(/\s{2,}/g, ' ')
		.trim()
}

/**
 * 英文服饰词（≥2 个拉丁字母）与汉字紧贴时，边界处插入两个空格，避免「与puffer构」挤在一起
 */
export function padLatinCjkBoundaries(s) {
	if (s == null || typeof s !== 'string') return ''
	let t = s
	t = t.replace(/([\u4e00-\u9fff])([a-zA-Z]{2,})/g, `$1${DOUBLE_SPACE}$2`)
	t = t.replace(/([a-zA-Z]{2,})([\u4e00-\u9fff])/g, `$1${DOUBLE_SPACE}$2`)
	t = t.replace(/ {3,}/g, DOUBLE_SPACE)
	return t
}

/** 展示用：先去 # 编号，再中英边界加两格 */
export function formatRecommendationDisplay(s) {
	return padLatinCjkBoundaries(stripWardrobeHashIds(s))
}
