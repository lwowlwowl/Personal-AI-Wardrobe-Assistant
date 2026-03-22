/**
 * 用本地衣橱列表给 AI 消息里的单品挂上真实图片（会修改 msg 内的对象）。
 * @param msg AI 消息
 * @param wardrobeList 本地衣橱列表（项含 id、image 等）
 */
export function attachWardrobeToAiMessage(msg, wardrobeList) {
	if (!msg || msg.role !== 'ai') return msg
	if (!Array.isArray(wardrobeList) || wardrobeList.length === 0) return msg

	const processItems = (items) => {
		if (!Array.isArray(items)) return
		for (const item of items) {
			let id = item?.clothingId
			if ((id == null || id === '') && typeof item?.name === 'string') {
				const m = item.name.match(/[\(（]\s*id\s*[:：]\s*(\d+)\s*[\)）]/i)
				if (m) id = Number(m[1])
			}

			if (
				item?.name &&
				typeof item.name === 'string' &&
				(item.name.includes('上传') ||
					item.name.toLowerCase().includes('uploaded') ||
					((id == null || id === '') && /id\s*[:：]\s*(None|null|uploaded)/i.test(item.name)))
			) {
				item.isUploaded = true
			}

			if (typeof item?.name === 'string') {
				item.name = item.name.replace(/\s*[\(（]\s*id\s*[:：]\s*[A-Za-z0-9_]+\s*[\)）]\s*/gi, '').trim()
			}

			if (id == null || id === '') continue
			const needle = Number(id)
			if (!Number.isFinite(needle)) continue
			item.clothingId = needle
			const cloth = wardrobeList.find((c) => Number(c?.id) === needle)
			if (cloth?.image) {
				item.image = cloth.image
				item.images = [cloth.image]
			}
		}
	}

	if (msg.renderType === 'plan' && Array.isArray(msg?.plan?.days)) {
		for (const day of msg.plan.days) {
			processItems(day?.items)
		}
	}

	if (Array.isArray(msg?.recommendations)) {
		for (const rec of msg.recommendations) {
			processItems(rec?.items)
			const itemImages = (rec?.items || []).map((i) => i.image).filter(Boolean)
			if (itemImages.length > 0) {
				const existing = Array.isArray(rec.images) ? rec.images : []
				rec.images = [...new Set([...existing, ...itemImages])]
			}
		}
	}

	return msg
}
