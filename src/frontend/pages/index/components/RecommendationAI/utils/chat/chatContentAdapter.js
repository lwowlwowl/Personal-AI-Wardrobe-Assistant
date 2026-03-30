/**
 * Recommendation AI chat content adapter.
 * Goals:
 * 1. Normalize backend payloads into a stable frontend message shape.
 * 2. Classify AI messages as text / recommendation / plan (when there is outfit content,
 *    use recommendation: analysis text above, cards below).
 * 3. Keep rawText for "view raw reply" or debugging.
 *
 * Output shape:
 * {
 *   role: 'ai',
 *   renderType: 'text' | 'recommendation' | 'plan',
 *   rawText: string,
 *   content: string,
 *   recommendations: [],
 *   plan?: {
 *     title?: string,
 *     intro?: string,
 *     days: Array<{
 *       key: string,
 *       label: string,
 *       dateText?: string,
 *       weatherText?: string,
 *       items: Array<{ type: string, name: string }>,
 *       notes?: string
 *     }>
 *   }
 * }
 */

/** Loading-step copy (rotating). */
export const LOADING_STEPS = [
	'Curating your exclusive wardrobe…',
	'Analyzing weather & occasion…',
	'Generating your look…'
]

/** Strip Markdown bold markers for easier regex matching. */
function stripBold(s) {
	if (typeof s !== 'string') return ''
	return s.replace(/\*\*([^*]+)\*\*/g, '$1').trim()
}

/** -------- Plan (multi-day / schedule) detection & parsing -------- */

const PLAN_KEYWORDS = [
	'下周',
	'一周',
	'周计划',
	'周安排',
	'每日搭配',
	'出行安排',
	'行程',
	'计划',
	'5套不重样',
	'5 套不重样',
	'outfit schedule',
	'schedule',
	'plan',
	'week',
	'daily'
]

const DAY_TOKEN_RE = /(?:周[一二三四五六日天]|星期[一二三四五六日天]|礼拜[一二三四五六日天]|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon\.?|Tue\.?|Wed\.?|Thu\.?|Fri\.?|Sat\.?|Sun\.?|Day\s*\d+|\d{1,2}[./-]\d{1,2})/gi

const PLAN_CATEGORY_HINTS = [
	'上衣', '下装', '外套', '鞋', '鞋履', '配饰', '包', '内衣', '其他',
	'Top', 'Bottom', 'Dress', 'Outerwear', 'Footwear', 'Accessory', 'Bag', 'Underwear', 'Other'
]

function countMatches(re, text) {
	if (!text) return 0
	const m = text.match(re)
	return m ? m.length : 0
}

function hasAnyKeyword(text, keywords) {
	const t = (text || '').toLowerCase()
	return keywords.some(k => t.includes(String(k).toLowerCase()))
}

/**
 * Detect plan: any two of the following conditions true.
 * 1. Multiple date/weekday tokens (>=3).
 * 2. Text splits into day blocks (>=2 day headers).
 * 3. Enough category hints across categories (>=5).
 * 4. Explicit schedule/week-plan keywords.
 */
function detectPlan(rawText) {
	if (!rawText || typeof rawText !== 'string') return false
	const text = rawText.trim()
	if (text.length < 120) return false

	const cond1 = countMatches(DAY_TOKEN_RE, text) >= 3
	// Allow leading emoji / markdown markers (e.g. **✅ Monday | ...**).
	const dayHeaderCount = countMatches(/^[^a-zA-Z0-9\u4e00-\u9fa5]*(?:\s*\|?\s*)?(周[一二三四五六日天]|星期[一二三四五六日天]|礼拜[一二三四五六日天]|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Day\s*\d+|\d{1,2}[./-]\d{1,2})/gmi, text)
	const cond2 = dayHeaderCount >= 2

	let catHits = 0
	for (const h of PLAN_CATEGORY_HINTS) {
		if (text.includes(h)) catHits++
	}
	const cond3 = catHits >= 5
	const cond4 = hasAnyKeyword(text, PLAN_KEYWORDS)

	const score = [cond1, cond2, cond3, cond4].filter(Boolean).length
	return score >= 2
}

function normalizeDayLabel(token) {
	if (!token) return ''
	const t = token.trim()
	const map = {
		Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday',
		'Mon.': 'Monday', 'Tue.': 'Tuesday', 'Wed.': 'Wednesday', 'Thu.': 'Thursday', 'Fri.': 'Friday', 'Sat.': 'Saturday', 'Sun.': 'Sunday'
	}
	if (map[t]) return map[t]
	return t
}

function parsePlanDays(rawText) {
	const text = (rawText || '').replace(/\r\n/g, '\n')
	const lines = text.split('\n')
	const days = []
	let current = null

	function pushCurrent() {
		if (!current) return
		const block = current.rawLines.join('\n')
		const items = []

		const kvLines = block.split('\n').map(l => l.trim()).filter(Boolean)
		for (const l of kvLines) {
			const m = /^(上衣|下装|外套|鞋履|鞋子|鞋|配饰|饰品|包包|包|内衣|其他|Top|Bottom|Dress|Outerwear|Footwear|Accessory|Bag|Underwear|Other)\s*[：:]\s*(.+)$/.exec(stripBold(l))
			if (m) {
				items.push({ type: mapType(m[1]), name: stripBold(m[2]).slice(0, 200) })
			}
		}

		if (items.length === 0) {
			for (const l of kvLines) {
				if (!l.includes('|')) continue
				if (/^\|?\s*[-:]+\s*\|/.test(l)) continue
				const parts = l.split('|').map(s => stripBold(s).trim()).filter(Boolean)
				if (parts.length >= 2) {
					const t = parts[0]
					const name = parts[1]
					if (t && name) {
						const mapped = mapType(t)
						if (mapped && mapped !== 'Other') {
							items.push({ type: mapped, name: name.slice(0, 200) })
						}
					}
				}
			}
		}

		const notes = kvLines
			.filter(l => !/^(上衣|下装|外套|鞋履|鞋子|鞋|配饰|饰品|包包|包|内衣|其他|Top|Bottom|Dress|Outerwear|Footwear|Accessory|Bag|Underwear|Other)\s*[：:]/.test(stripBold(l)))
			.join('\n')
			.slice(0, 1600)

		days.push({
			key: current.key,
			label: current.label,
			dateText: current.dateText || undefined,
			weatherText: current.weatherText || undefined,
			items,
			notes: notes || undefined
		})
		current = null
	}

	for (const line of lines) {
		const raw = line
		const trimmed = raw.trim()
		if (!trimmed) continue

		// Allow leading emoji / markdown markers on the day header line.
		const headerMatch = /^[^a-zA-Z0-9\u4e00-\u9fa5]*(?:\|?\s*)?(周[一二三四五六日天]|星期[一二三四五六日天]|礼拜[一二三四五六日天]|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Mon\.?|Tue\.?|Wed\.?|Thu\.?|Fri\.?|Sat\.?|Sun\.?|Day\s*\d+|\d{1,2}[./-]\d{1,2})(?:\s*[\(|（]([^)\n）]+)[\)|）])?/.exec(trimmed)
		if (headerMatch) {
			pushCurrent()
			const label = normalizeDayLabel(headerMatch[1])
			const meta = headerMatch[2] ? stripBold(headerMatch[2]).trim() : ''
			current = {
				key: `${label}-${days.length}`,
				label,
				dateText: meta && /(\d{1,2}[./-]\d{1,2})/.test(meta) ? meta : undefined,
				weatherText: meta && /(℃|°C|降水|湿度|风|晴|雨|雪)/.test(meta) ? meta : undefined,
				rawLines: []
			}
			// If the day header row has extra pipe columns, include the rest for parsing.
			const rest = trimmed.slice(headerMatch[0].length).trim().replace(/^\|+/, '').trim()
			if (rest) current.rawLines.push(rest)
			continue
		}

		if (!current) continue
		current.rawLines.push(raw)
	}
	pushCurrent()

	return days
}

function parsePlanFromRawText(rawText) {
	const text = (rawText || '').trim()
	const days = parsePlanDays(text)
	if (!days.length) return null

	const firstIdx = text.search(/^[^a-zA-Z0-9\u4e00-\u9fa5]*(?:\s*\|?\s*)?(周[一二三四五六日天]|星期[一二三四五六日天]|礼拜[一二三四五六日天]|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Day\s*\d+|\d{1,2}[./-]\d{1,2})/m)
	const intro = firstIdx > 0 ? text.slice(0, firstIdx).trim().slice(0, 800) : ''

	return {
		title: 'Outfit plan',
		intro: intro || undefined,
		days
	}
}

/** Extract style title from 「xxx」 or quoted "xxx". */
function extractTitleFromHeader(line) {
	const quoted = /[「\"]([^」\"]+)[」\"]/.exec(line)
	if (quoted) return quoted[1].trim()
	const pipeParts = line.split(/\|/).map(p => p.trim())
	for (const p of pipeParts) {
		if (p && !/^方案[一二三四五六七八九十]+$/.test(p) && !/^推荐指数|★+$/.test(p)) {
			return p.replace(/^[「\"](.+)[」\"]$/, '$1').trim()
		}
	}
	return ''
}

/**
 * Parse one item line: `English` (CJK|desc) or Layer | item | reason.
 * Returns { type, name, subtitle, reason, details, tags }.
 */
function parseItemLine(line) {
	const trimmed = stripBold(line).replace(/^[-*]\s*/, '').trim()

	const backtick = /`([^`]+)`\s*[（(]([^）)]+)[）)]/.exec(trimmed)
	if (backtick) {
		const en = backtick[1].trim()
		const cnBlock = backtick[2]
		const pipe = cnBlock.indexOf('|')
		const subtitle = pipe >= 0 ? cnBlock.slice(0, pipe).trim() : cnBlock.trim()
		const desc = pipe >= 0 ? cnBlock.slice(pipe + 1).trim() : ''
		const tagCandidates = (subtitle + ' ' + desc)
			.split(/[,，、|]/)
			.map(s => s.trim())
			.filter(s => s.length >= 2 && s.length <= 8)
		const tags = [...new Set(tagCandidates)].slice(0, 5)

		return {
			type: 'Item',
			name: en,
			subtitle: subtitle || undefined,
			reason: desc ? desc.slice(0, 60) : undefined,
			details: desc || undefined,
			tags: tags.length ? tags : undefined
		}
	}

	const tableMatch = /^([^|]+)\|([^|]+)\|?(.*)$/.exec(trimmed)
	if (tableMatch) {
		const type = tableMatch[1].trim().replace(/^\*\*|\*\*$/g, '')
		let name = tableMatch[2].trim().replace(/^\*\*|\*\*$/g, '')
		const reason = tableMatch[3].trim().replace(/^\*\*|\*\*$/g, '') || undefined

		// Remove CJK parenthetical notes only (e.g. (beige knit top)); keep (ID: 42)
		// Match only when the parenthetical does not contain 'id' (case-insensitive).
		const cnInName = /[（(](?!\s*id\s*[:：])([^）)]+)[）)]/i.exec(name)
		let subtitle
		if (cnInName) {
			subtitle = cnInName[1].trim()
			name = name.replace(cnInName[0], '').trim()
		}

		return {
			type: type || 'Item',
			name: name || '—',
			subtitle,
			reason,
			details: undefined,
			tags: undefined
		}
	}

	const colonMatch = /^(?:\*\*)?([^：:]+)(?:\*\*)?[：:]\s*(.+)$/.exec(trimmed)
	if (colonMatch) {
		const type = stripBold(colonMatch[1])
		const rest = colonMatch[2].trim()
		const inner = /`([^`]+)`\s*[（(]([^）)]+)[）)]/.exec(rest)

		if (inner) {
			const en = inner[1].trim()
			const cn = inner[2].trim()
			const pipe = cn.indexOf('|')
			const subtitle = pipe >= 0 ? cn.slice(0, pipe).trim() : cn
			const details = pipe >= 0 ? cn.slice(pipe + 1).trim() : undefined
			return { type, name: en, subtitle, reason: undefined, details, tags: undefined }
		}

		return {
			type,
			name: rest.slice(0, 80),
			subtitle: undefined,
			reason: undefined,
			details: undefined,
			tags: undefined
		}
	}

	return null
}

/** Extract up to 3 bullet points from the "why this works" style section. */
function extractWhyThisWorks(block) {
	const bullets = []
	const lines = block.split(/\n/)

	for (const line of lines) {
		const t = stripBold(line).trim()
		if (!t || /^[-*]\s*$/.test(t)) continue
		const afterColon = t.replace(/^[^*]*\*\*[^*]*\*\*[：:]\s*/, '').trim()
		const one = afterColon || t
		if (one.length > 4 && one.length < 120) bullets.push(one)
		if (bullets.length >= 3) break
	}

	if (bullets.length === 0) {
		const sentences = block
			.split(/[。；;]/)
			.map(s => stripBold(s).trim())
			.filter(s => s.length > 6 && s.length < 100)
		return sentences.slice(0, 3)
	}

	return bullets
}

/** Extract caution lines from the full text or a block. */
function extractCautions(text) {
	const list = []
	const patterns = [
		/!\s*\*\*([^*]+)\*\*[：:]?\s*([^\n]+)/g,
		/▲\s*([^\n]+)/g,
		/❌\s*([^\n]+)/g,
		/\*\*强烈不推荐\*\*[^\n]*/g,
		/\*\*不推荐\*\*[^\n]*/g,
		/\*\*请务必[^*]*\*\*[^\n]*/g,
		/(?:注意|避免)[：:]\s*([^\n]+)/g
	]

	const seen = new Set()
	for (const re of patterns) {
		let m
		const copy = new RegExp(re.source, re.flags)
		while ((m = copy.exec(text)) !== null) {
			const raw = m[0].trim()
			const cleaned = stripBold(raw).replace(/^[!▲❌\s]+/, '').trim()
			if (cleaned.length > 4 && cleaned.length < 200 && !seen.has(cleaned)) {
				seen.add(cleaned)
				list.push(cleaned)
			}
		}
	}
	return list
}

/**
 * Category mapping (aligned with backend wardrobe 9 English labels).
 * Values: Top, Bottom, Dress, Outerwear, Footwear, Accessory, Bag, Underwear, Other.
 */
const LAYER_MAP = {
	// Common Chinese labels
	上衣: 'Top',
	下装: 'Bottom',
	连衣裙: 'Dress',
	裙装: 'Dress',
	外套: 'Outerwear',
	中层: 'Outerwear',
	鞋履: 'Footwear',
	鞋子: 'Footwear',
	鞋: 'Footwear',
	配饰: 'Accessory',
	饰品: 'Accessory',
	包: 'Bag',
	包包: 'Bag',
	内衣: 'Underwear',
	其他: 'Other',
	其它: 'Other',

	// English / legacy aliases
	Top: 'Top',
	Bottom: 'Bottom',
	Dress: 'Dress',
	Outerwear: 'Outerwear',
	Mid: 'Outerwear',
	'Mid Layer': 'Outerwear',
	Shoes: 'Footwear',
	Footwear: 'Footwear',
	Accessories: 'Accessory',
	Accessory: 'Accessory',
	Bag: 'Bag',
	Underwear: 'Underwear',
	Other: 'Other'
}

function normalizeTypeKey(type) {
	if (!type || typeof type !== 'string') return ''
	return type
		.replace(/[（(][^）)]*[）)]/g, '') // strip optional parenthetical notes
		.replace(/\s+/g, ' ')
		.trim()
}

function mapType(type) {
	const key = normalizeTypeKey(type)
	return LAYER_MAP[key] || LAYER_MAP[type] || key || type || 'Other'
}

function parseSchemeBlock(block) {
	const title = extractTitleFromHeader(block)
	const items = []
	const whyThisWorks = []
	let content = ''
	let temperature = ''

	// Only treat section starts at line start with ③/3 "outfit recommendation"; ④/⑤ must start on new lines to avoid IDs like 42/45.
	let recMatch = block.match(/(?:^|\n)\s*(?:③|3\.?|###)[\s]*\*?\*?\s*(?:推荐搭配|Outfit recommendation(?:s)?|Recommended outfit(?:s)?)[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=(?:^|\n)\s*(?:④|4\.?)[\s]*\*?\*?|(?:^|\n)\s*(?:⑤|5\.?)[\s]*\*?\*?|###|$)/i)
	if (!recMatch) {
		recMatch = block.match(/\*?\*?\s*(?:推荐搭配|Outfit recommendation(?:s)?|Recommended outfit(?:s)?)[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=(?:为什么这样搭|Why this works|Why it works|Styling rationale)|(?:^|\n)\s*(?:④|4\.?)[\s]*\*?\*?|(?:^|\n)\s*(?:⑤|5\.?)[\s]*\*?\*?|###|$)/i)
	}
	if (recMatch) {
		const tableBlock = recMatch[1]
		const lines = tableBlock.split(/\n/).map(s => s.trim()).filter(Boolean)
		for (const line of lines) {
			if (/^[-|]\s*$/.test(line) || /^层级|层級/.test(line)) continue
			const item = parseItemLine(line)
			if (item) {
				item.type = mapType(item.type)
				items.push(item)
			}
		}
	}

	// 4. Extract "why this works" (④)
	// Note: allow optional 4\.?
	const whyMatch = block.match(/(?:④|4\.?)[\s]*\*?\*?\s*(?:为什么这样搭|Why this works|Why it works|Styling rationale)[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=(?:⑤|5\.?|###|$))/i)
	if (whyMatch) whyThisWorks.push(...extractWhyThisWorks(whyMatch[1]))

	const sceneMatch = block.match(/(?:①|1)[\s]*\*?\*?场景理解[^*\n]*\*?\*?[：:]*\s*([^\n]+)/i)
	if (sceneMatch) content = stripBold(sceneMatch[1]).slice(0, 200)

	const tempMatch = block.match(/(-?\d+\s*(?:°C|℃))/i)
	if (tempMatch) temperature = tempMatch[1]

	const cautions = extractCautions(block)

	// 5. Extract alternatives (⑤) and footer greeting
	// Note: allow optional 5\.?
	const altMatch = block.match(/(?:⑤|5\.?)[\s]*\*?\*?\s*(?:可替换方案|Alternatives?|Alternative options?)[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=###|$)/i)
	const alternatives = []
	let footer = ''

	if (altMatch) {
		let rawAltText = altMatch[1].trim()
		const paragraphs = rawAltText.split(/\n\n+/)
		if (paragraphs.length > 1) {
			const lastPara = paragraphs[paragraphs.length - 1].trim()
			// Also match English closings: hope, let me know, feel free, etc.
			if (!lastPara.includes('：') && !lastPara.includes(':') || /祝|需要我|期待|随时|hope|let me know|feel free|would you/i.test(lastPara)) {
				footer = lastPara.replace(/^[-*•→]\s*/, '').trim()
				paragraphs.pop()
			}
		}
		const remainingText = paragraphs.join('\n\n')
		const lines = remainingText.split('\n').map(s => s.trim()).filter(s => s && s.length > 2)
		alternatives.push(...lines)
	}

	if (!footer) {
		// 6. Fallback: if ⑤ was omitted entirely
		// Include English greeting keywords in fallback match
		const fallbackMatch = block.match(/(?:\n\s*|^)(需要我|祝你们?|期待|随时告诉|有什么问题|Let me know|Feel free|Would you|Hope)[\s\S]*$/i)
		if (fallbackMatch) footer = fallbackMatch[0].replace(/^[-*•→]\s*/, '').trim()
	}

	return {
		title: title || 'Recommended look',
		temperature,
		styleTags: title ? [title] : [],
		content: content || undefined,
		items,
		whyThisWorks: whyThisWorks.length ? whyThisWorks : undefined,
		cautions: cautions.length ? cautions : undefined,
		alternatives: alternatives.length ? alternatives : undefined,
		footer: footer || undefined,
		images: []
	}
}

function parseRawContentToRecommendations(rawText) {
	if (!rawText || typeof rawText !== 'string') return { recommendations: [], intro: '' }

	const text = rawText.trim()
	const recommendations = []

	// Allow 3\.? for AI output like "3." and optional spaces after asterisks.
	const splitRegex = /(?:\n|^)\s*(?:③|3\.?|###)\s*\*?\*?\s*(?:推荐搭配|Outfit recommendation(?:s)?|Recommended outfit(?:s)?)/i
	const splitIndex = text.search(splitRegex)

	let intro = text
	if (splitIndex !== -1) {
		intro = text.slice(0, splitIndex).trim()
	}

	const introRemoved = splitIndex !== -1 ? text.slice(splitIndex) : text

	// Split blocks with English-compatible headings too.
	const schemeBlocks = introRemoved.split(/(?=(?:③|3\.?|###)\s*\*?\*?\s*(?:推荐搭配|Outfit recommendation(?:s)?|Recommended outfit(?:s)?))/i)

	for (const blk of schemeBlocks) {
		const block = blk.trim()
		if (!block) continue
		const rec = parseSchemeBlock(block)
		if (rec.items.length > 0 || rec.whyThisWorks?.length || rec.cautions?.length) {
			recommendations.push(rec)
		}
	}

	if (recommendations.length === 0 && (text.includes('推荐搭配') || /Outfit recommendation/i.test(text) || text.includes('**上衣**') || text.includes('上衣：'))) {
		const single = parseSchemeBlock(text)
		if (single.items.length > 0 || single.whyThisWorks?.length || single.cautions?.length) {
			recommendations.push(single)
		}
	}

	return { recommendations, intro }
}

function buildTextMessage(rawText, content) {
	const finalContent = content || rawText || ''
	return {
		...createBaseMessage(),
		rawText: rawText || finalContent || '',
		content: finalContent || '',
		recommendations: [],
		plan: null
	}
}

/** Default empty message shape; components can use empty checks. */
function createBaseMessage() {
	return {
		role: 'ai',
		renderType: 'text',
		rawText: '',
		content: '',
		recommendations: [],
		plan: null,
		locale: 'en'
	}
}

/**
 * Normalize backend / history / current messages.
 * Priority: 1) structured fields when present (plan.days / recommendations)
 *           2) renderType (belt-and-suspenders when backend is aligned)
 *           3) legacy parse from rawText  4) plain text fallback
 */

/**
 * When top-level recommendations are missing but rawText is full protocol JSON,
 * merge structure from rawText. Prevents stream/persist paths that only keep
 * content+renderType from showing intro text without cards.
 */
function mergeStructuredFieldsFromRawText(apiResponse) {
	if (!apiResponse || typeof apiResponse !== 'object') return apiResponse
	const raw = String(apiResponse.rawText || apiResponse.raw_text || '').trim()
	if (!raw.startsWith('{')) return apiResponse
	let p
	try {
		p = JSON.parse(raw)
	} catch (_) {
		return apiResponse
	}
	if (!p || typeof p !== 'object') return apiResponse

	const hasRecs = Array.isArray(apiResponse.recommendations) && apiResponse.recommendations.length > 0
	const parsedRecs = Array.isArray(p.recommendations) && p.recommendations.length > 0
	const noPlan =
		!apiResponse.plan || !Array.isArray(apiResponse.plan?.days) || apiResponse.plan.days.length === 0
	const parsedPlan = p.plan && Array.isArray(p.plan.days) && p.plan.days.length > 0

	if (!hasRecs && parsedRecs) {
		const next = { ...apiResponse, recommendations: p.recommendations }
		if ((apiResponse.content == null || apiResponse.content === '') && p.content) next.content = p.content
		if (!apiResponse.locale && p.locale) next.locale = p.locale
		if (noPlan && parsedPlan) next.plan = p.plan
		return next
	}
	if (noPlan && parsedPlan) {
		const next = { ...apiResponse, plan: p.plan }
		if ((apiResponse.content == null || apiResponse.content === '') && p.content) next.content = p.content
		if (!apiResponse.locale && p.locale) next.locale = p.locale
		return next
	}
	return apiResponse
}

export function normalizeChatResponse(apiResponse) {
	if (!apiResponse || typeof apiResponse !== 'object') {
		return buildTextMessage('', '')
	}

	const merged = mergeStructuredFieldsFromRawText(apiResponse)

	const role = merged.role || 'ai'
	const rawText =
		merged.rawText ||
		merged.raw_text ||
		merged.content ||
		''
	const locale = merged.locale || 'en'
	const renderType = merged.renderType || ''

	// 1. Structure wins: if plan.days exists, render plan (ignore wrong renderType).
	if (
		role === 'ai' &&
		merged.plan &&
		Array.isArray(merged.plan.days) &&
		merged.plan.days.length > 0
	) {
		return {
			...createBaseMessage(),
			role: 'ai',
			renderType: 'plan',
			rawText,
			content: merged.content || merged.plan.intro || '',
			recommendations: [],
			plan: merged.plan,
			locale
		}
	}

	// 2. Structure wins: if recommendations exist, render recommendation (ignore wrong renderType).
	if (
		role === 'ai' &&
		Array.isArray(merged.recommendations) &&
		merged.recommendations.length > 0
	) {
		return {
			...createBaseMessage(),
			role: 'ai',
			renderType: 'recommendation',
			rawText,
			content: merged.content || '',
			recommendations: merged.recommendations,
			plan: null,
			locale
		}
	}

	// 3. No structured payload: honor backend-declared text render.
	if (role === 'ai' && renderType === 'text') {
		return {
			...createBaseMessage(),
			role: 'ai',
			renderType: 'text',
			rawText,
			content: merged.content || rawText || '',
			recommendations: [],
			plan: null,
			locale
		}
	}

	// 4. Legacy: parse from rawText only when needed.
	if (role === 'ai' && rawText && typeof rawText === 'string') {
		if (detectPlan(rawText)) {
			const plan = parsePlanFromRawText(rawText)
			if (plan?.days?.length) {
				return {
					...createBaseMessage(),
					role: 'ai',
					renderType: 'plan',
					rawText,
					content: merged.content || plan.intro || '',
					recommendations: [],
					plan,
					locale
				}
			}
		}

		const { recommendations, intro } = parseRawContentToRecommendations(rawText)
		if (recommendations.length > 0) {
			return {
				...createBaseMessage(),
				role: 'ai',
				renderType: 'recommendation',
				rawText,
				content: merged.content || intro || '',
				recommendations,
				plan: null,
				locale
			}
		}
	}

	// 5. Final fallback
	return {
		...createBaseMessage(),
		role: 'ai',
		renderType: 'text',
		rawText,
		content: merged.content || rawText || '',
		recommendations: [],
		plan: null,
		locale
	}
}
