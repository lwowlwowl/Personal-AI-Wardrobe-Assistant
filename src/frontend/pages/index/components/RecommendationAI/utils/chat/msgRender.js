/** How to render a message in the UI: cards, plan, or plain text (for templates). */

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

/** When multiple recommendation cards exist, show Regenerate only on the card that has item rows. */
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
