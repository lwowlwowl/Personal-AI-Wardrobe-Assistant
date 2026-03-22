/**
 * 虚拟试衣串联时的层次顺序（由内到外）。
 * 数值越小越先应用；与推荐卡片里的类别语义一致。
 */
export function getOutfitTryOnSortIndex(type) {
	const t = String(type || '').toUpperCase()
	const raw = String(type || '')
	const has = (s) => raw.includes(s) || t.includes(s)

	if (t.includes('UNDER') || has('\u5185\u8863')) return 1
	if (t.includes('TOP') || has('\u4e0a\u8863')) return 10
	if (t.includes('DRESS') || has('\u8fde\u8863') || has('\u88d9')) return 20
	if (t.includes('BOTTOM') || has('\u4e0b\u88c5') || has('\u88e4')) return 30
	if (t.includes('OUTER') || has('\u5916\u5957') || has('\u5927\u8863') || has('\u5939\u514b')) return 40
	if (t.includes('FOOT') || t.includes('SHOE') || has('\u978b')) return 50
	if (t.includes('ACCESS') || has('\u914d\u9970') || has('\u9970\u54c1') || has('\u5e3d') || has('\u9632\u62a4')) return 60
	if (t.includes('BAG') || has('\u5305')) return 70
	return 80
}

/** 英文类别标签，供界面展示（与推荐卡片组件的类别一致） */
export function getOutfitCategoryLabel(type) {
	const t = String(type || '').toUpperCase()
	const raw = String(type || '')
	const has = (s) => raw.includes(s) || t.includes(s)

	if (t.includes('UNDER') || has('\u5185\u8863')) return 'UNDERWEAR'
	if (t.includes('TOP') || has('\u4e0a\u8863')) return 'TOP'
	if (t.includes('DRESS') || has('\u8fde\u8863') || has('\u88d9')) return 'DRESS'
	if (t.includes('BOTTOM') || has('\u4e0b\u88c5') || has('\u88e4')) return 'BOTTOM'
	if (t.includes('OUTER') || has('\u5916\u5957') || has('\u5927\u8863') || has('\u5939\u514b')) return 'OUTERWEAR'
	if (t.includes('FOOT') || t.includes('SHOE') || has('\u978b')) return 'FOOTWEAR'
	if (t.includes('ACCESS') || has('\u914d\u9970') || has('\u9970\u54c1') || has('\u5e3d') || has('\u9632\u62a4')) return 'ACCESSORY'
	if (t.includes('BAG') || has('\u5305')) return 'BAG'
	return 'OTHER'
}

/** 试衣队列里单行展示文案 */
export function buildOutfitTryOnStepLabel(item) {
	const cat = getOutfitCategoryLabel(item?.type)
	let name = String(item?.name || 'Item')
		.replace(/\s*[\(（]\s*id\s*[:：]\s*[A-Za-z0-9_]+\s*[\)）]\s*/gi, '')
		.replace(/[（(][^）)]+[）)]/g, '')
		.replace(/\s{2,}/g, ' ')
		.trim() || 'Item'
	if (name.length > 48) name = `${name.slice(0, 46)}…`
	return `${cat} · ${name}`
}
