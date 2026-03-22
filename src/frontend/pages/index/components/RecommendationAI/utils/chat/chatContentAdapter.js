/**
 * 推荐 AI 聊天内容适配层
 * 目标：
 * 1. 将后端返回统一适配成前端稳定消息结构
 * 2. 把 AI 消息分为 text / recommendation / plan（有推荐内容时统一为 recommendation：上为解读文字，下为推荐卡片）
 * 3. 保留 rawText，方便后续做“查看原始回复”或调试
 *
 * 输出结构：
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

/** 加载过程展示文案（轮播） */
export const LOADING_STEPS = [
	'Curating your exclusive wardrobe…',
	'Analyzing weather & occasion…',
	'Generating your look…'
]

/** 去掉 Markdown 粗体符号，便于正则匹配 */
function stripBold(s) {
	if (typeof s !== 'string') return ''
	return s.replace(/\*\*([^*]+)\*\*/g, '$1').trim()
}

/** -------- plan（多天/计划表）识别与解析 -------- */

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
 * 判定 plan：满足任意两条
 * 1. 出现多个日期/星期 token（>=3）
 * 2. 文本按天拆块（出现 >=2 个 day header）
 * 3. 每天都有完整穿搭项（整体出现 >=5 个分类提示词）
 * 4. 明确计划/周安排语义关键词
 */
function detectPlan(rawText) {
	if (!rawText || typeof rawText !== 'string') return false
	const text = rawText.trim()
	if (text.length < 120) return false

	const cond1 = countMatches(DAY_TOKEN_RE, text) >= 3
	// 容忍行首出现 emoji / markdown 符号（如：**✅ 周一 | ...**）
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

		// 容忍行首出现 emoji / markdown 符号（如：**✅ 周一 | 知性简约风**）
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
			// 若 day header 同行包含其它列内容（markdown table / pipe），把剩余内容也纳入解析
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

/** 从「xxx」或 "xxx" 中提取风格名 */
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
 * 解析单品行：`英文名` (中文|描述) 或 层级 | 单品 | 理由
 * 返回 { type, name, subtitle, reason, details, tags }
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

		// 只删掉中文括号说明（如「（米色针织衫）」），安全保留后面的 (ID: 42)
		// 精确匹配：找到括号内容，但要求里面不能包含 'id'（忽略大小写）
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

/** 从「为什么这样搭」段落提取最多 3 条极简要点 */
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

/** 从全文或块内提取警示句 */
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
 * 类别映射（与衣橱后端固定的 9 类英文 label 对齐）
 * 取值：Top、Bottom、Dress、Outerwear、Footwear、Accessory、Bag、Underwear、Other
 */
const LAYER_MAP = {
	// 中文常见写法
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

	// 英文/旧字段兼容
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
		.replace(/[（(][^）)]*[）)]/g, '') // 去掉（按需）这类括号说明
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

	// 只把行首的「③/3 推荐搭配」视作章节开头；④/⑤ 也必须在新行开头，避免误伤 ID: 42/45 等数字
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

	// 4. 提取为什么这样搭 (④)
	// 【修复点】：加入 4\.?
	const whyMatch = block.match(/(?:④|4\.?)[\s]*\*?\*?\s*(?:为什么这样搭|Why this works|Why it works|Styling rationale)[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=(?:⑤|5\.?|###|$))/i)
	if (whyMatch) whyThisWorks.push(...extractWhyThisWorks(whyMatch[1]))

	const sceneMatch = block.match(/(?:①|1)[\s]*\*?\*?场景理解[^*\n]*\*?\*?[：:]*\s*([^\n]+)/i)
	if (sceneMatch) content = stripBold(sceneMatch[1]).slice(0, 200)

	const tempMatch = block.match(/(-?\d+\s*(?:°C|℃))/i)
	if (tempMatch) temperature = tempMatch[1]

	const cautions = extractCautions(block)

	// 5. 提取可替换方案 (⑤) 及底部的问候语
	// 【修复点】：加入 5\.?
	const altMatch = block.match(/(?:⑤|5\.?)[\s]*\*?\*?\s*(?:可替换方案|Alternatives?|Alternative options?)[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=###|$)/i)
	const alternatives = []
	let footer = ''

	if (altMatch) {
		let rawAltText = altMatch[1].trim()
		const paragraphs = rawAltText.split(/\n\n+/)
		if (paragraphs.length > 1) {
			const lastPara = paragraphs[paragraphs.length - 1].trim()
			// 增加英文问候语匹配词：hope, let me know, feel free 等
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
		// 6. 全局保底：如果 AI 连 ⑤ 都没输出
		// 【修改点】：在 Fallback 匹配中加入英文问候关键词
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

	// 【修复点】：加入 3\.? 兼容 AI 输出的 "3."，并加入 \s* 兼容星号后的空格
	const splitRegex = /(?:\n|^)\s*(?:③|3\.?|###)\s*\*?\*?\s*(?:推荐搭配|Outfit recommendation(?:s)?|Recommended outfit(?:s)?)/i
	const splitIndex = text.search(splitRegex)

	let intro = text
	if (splitIndex !== -1) {
		intro = text.slice(0, splitIndex).trim()
	}

	const introRemoved = splitIndex !== -1 ? text.slice(splitIndex) : text

	// 切割块也加入英文兼容
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

/** 统一默认消息结构，组件可依此判空 */
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
 * 规范化后端 / 历史 / 当前消息
 * 优先级：1) 后端结构优先（有 plan.days / recommendations 即按对应类型渲染）
 *         2) 再按 renderType（后端已修正为结构优先，此处双重保险）
 *         3) 旧数据兼容（从 rawText 解析）  4) 纯文本 fallback
 */

/**
 * 当顶层未带 recommendations（或为空）但 rawText 是完整协议 JSON 时，从 rawText 合并结构。
 * 避免流式/持久化链路只保留 content+renderType 导致界面只剩「AI Analysis」引言、无卡片。
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

	// 1. 结构优先：有 plan.days 即按 plan 渲染（不依赖 renderType，防止后端/历史数据声明错误）
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

	// 2. 结构优先：有 recommendations 即按 recommendation 渲染（不依赖 renderType）
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

	// 3. 无结构内容时，按后端声明的 text 渲染
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

	// 4. 兼容旧数据：必要时才从 rawText 猜
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

	// 5. 最终 fallback
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
