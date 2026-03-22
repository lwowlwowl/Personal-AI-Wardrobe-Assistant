/** 推荐卡片里单品的图 URL（试衣等） */
export function recTryOnImageUrl(item) {
	if (!item || typeof item !== 'object') return ''
	if (item.image) return String(item.image)
	const arr = item.images
	if (Array.isArray(arr) && arr[0]) return String(arr[0])
	return ''
}

/** 从单品对象或 name 里的 (id: 123) 解析衣橱 id */
export function recClothingId(item) {
	let id = item?.clothingId ?? item?.clothing_id
	if ((id == null || id === '') && typeof item?.name === 'string') {
		const m = item.name.match(/[\(（]\s*id\s*[:：]\s*(\d+)\s*[\)）]/i)
		if (m) id = Number(m[1])
	}
	if (id == null || id === '') return null
	const n = Number(id)
	return Number.isFinite(n) ? n : null
}

/** 去掉展示名里的 (id: xxx) 后缀 */
export function stripRecItemNameId(rawName) {
	return String(rawName).replace(/\s*[\(（]\s*id\s*[:：]\s*[A-Za-z0-9_]+\s*[\)）]\s*/gi, '').trim() || 'Item'
}
