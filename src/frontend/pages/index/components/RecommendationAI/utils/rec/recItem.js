/** Image URL for a recommendation item (try-on, etc.). */
export function recTryOnImageUrl(item) {
	if (!item || typeof item !== 'object') return ''
	if (item.image) return String(item.image)
	const arr = item.images
	if (Array.isArray(arr) && arr[0]) return String(arr[0])
	return ''
}

/** Parse wardrobe id from item fields or "(id: 123)" in name. */
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

/** Strip "(id: xxx)" suffix from display name. */
export function stripRecItemNameId(rawName) {
	return String(rawName).replace(/\s*[\(（]\s*id\s*[:：]\s*[A-Za-z0-9_]+\s*[\)）]\s*/gi, '').trim() || 'Item'
}
