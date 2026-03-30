/** Recommendation card / bubble display: strip # ids and pad CJK/Latin boundaries (display only). */

const DOUBLE_SPACE = '  '

export function stripWardrobeHashIds(s) {
	if (s == null || typeof s !== 'string') return ''
	return s
		.replace(/\s*[#＃]\s*\d+\b/g, '')
		.replace(/\s{2,}/g, ' ')
		.trim()
}

/**
 * Insert two spaces between Latin words (≥2 letters) and CJK when they touch.
 */
export function padLatinCjkBoundaries(s) {
	if (s == null || typeof s !== 'string') return ''
	let t = s
	t = t.replace(/([\u4e00-\u9fff])([a-zA-Z]{2,})/g, `$1${DOUBLE_SPACE}$2`)
	t = t.replace(/([a-zA-Z]{2,})([\u4e00-\u9fff])/g, `$1${DOUBLE_SPACE}$2`)
	t = t.replace(/ {3,}/g, DOUBLE_SPACE)
	return t
}

/** Display helper: strip # ids, then pad CJK/Latin boundaries. */
export function formatRecommendationDisplay(s) {
	return padLatinCjkBoundaries(stripWardrobeHashIds(s))
}
