/** 消息用何种界面渲染：卡片、计划表或纯文字（供模板调用） */

export function getRecommendations(msg) {
	if (Array.isArray(msg?.recommendations) && msg.recommendations.length > 0) {
		return msg.recommendations
	}

	const raw = msg?.rawText
	if (typeof raw === 'string' && raw.trim().startsWith('{')) {
		try {
			const p = JSON.parse(raw.trim())
			if (Array.isArray(p.recommendations) && p.recommendations.length > 0) {
				return p.recommendations
			}
		} catch (_) {}
	}

	const items = (msg?.outfitItems || []).map((it) => ({
		type: it.category,
		name: it.name,
		reason: it.desc,
		details: it.details
	}))

	if (msg?.list && msg.list.length > 0 && items.length === 0) {
		msg.list.forEach((t) => items.push({ type: 'Item', name: t, reason: '' }))
	}

	const tags = msg?.tags || []
	const tempTag = tags.find((t) => /°C|℃/.test(t))
	const styleTags = tags.filter((t) => t !== tempTag)

	const rec = {
		title: styleTags[0] || '',
		temperature: tempTag || '',
		styleTags,
		content: msg?.content || '',
		items,
		whyThisWorks: msg?.whyThisWorks || [],
		images: msg?.images || []
	}

	return items.length > 0 || (rec.images && rec.images.length > 0) ? [rec] : []
}

export function getMessageRenderType(msg) {
	if (msg?.plan && Array.isArray(msg.plan.days) && msg.plan.days.length > 0) return 'plan'

	const recs = getRecommendations(msg)
	if (recs.length > 0) return 'recommendation'

	return 'text'
}

export function getDisplayContent(msg) {
	return msg?.content ?? msg?.rawText ?? ''
}

/** 多条推荐卡片时，「重新生成」按钮只显示在带单品列表的那一张上 */
export function shouldShowRegenerateOnRecommendation(msg, ri) {
	const recs = getRecommendations(msg)
	if (recs.length <= 1) return true
	let lastWithItems = -1
	for (let i = recs.length - 1; i >= 0; i--) {
		if (Array.isArray(recs[i]?.items) && recs[i].items.length > 0) {
			lastWithItems = i
			break
		}
	}
	if (lastWithItems >= 0) return ri === lastWithItems
	return ri === 0
}
