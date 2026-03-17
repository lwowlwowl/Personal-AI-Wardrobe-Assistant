/**
 * 推荐 AI 聊天内容适配层
 * 目标：
 * 1. 将后端返回统一适配成前端稳定消息结构
 * 2. 把 AI 消息分为 text / recommendation / mixed
 * 3. 保留 rawText，方便后续做“查看原始回复”或调试
 *
 * 输出结构：
 * {
 *   role: 'ai',
 *   renderType: 'text' | 'recommendation' | 'mixed' | 'plan',
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

/** 安全文本裁剪 */
function safeTrimText(text, max = 240) {
	if (!text || typeof text !== 'string') return ''
	const t = text.replace(/\n{3,}/g, '\n\n').trim()
	if (t.length <= max) return t
	return t.slice(0, max).trim() + '…'
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
	'plan'
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
		title: '穿搭计划',
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

		const cnInName = /[（(]([^）)]+)[）)]/.exec(name)
		let subtitle
		if (cnInName) {
			subtitle = cnInName[1].trim()
			name = name.replace(/\s*[（(][^）)]+[）)]\s*/, '').trim()
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

/** 从「为什么这样搭」段落提取最多 3 条极简 bullet */
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
 * 类别映射（对齐衣橱后端写死 9 类的 label）
 * Top / Bottom / Dress / Outerwear / Footwear / Accessory / Bag / Underwear / Other
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

	let recMatch = block.match(/(?:③|3)[\s]*\*?\*?推荐搭配[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=(?:④|4)[\s]*\*?\*?|⑤|5[\s]*\*?\*?|###|$)/i)
	if (!recMatch) {
		recMatch = block.match(/\*?\*?推荐搭配[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=为什么这样搭|(?:④|4)[\s]*\*?\*?|⑤|5[\s]*\*?\*?|###|$)/i)
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

	const whyMatch = block.match(/(?:④|4)[\s]*\*?\*?为什么这样搭[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=(?:⑤|5)[\s]*\*?\*?|可替换|###|$)/i)
	if (whyMatch) whyThisWorks.push(...extractWhyThisWorks(whyMatch[1]))

	const sceneMatch = block.match(/(?:①|1)[\s]*\*?\*?场景理解[^*\n]*\*?\*?[：:]*\s*([^\n]+)/i)
	if (sceneMatch) content = stripBold(sceneMatch[1]).slice(0, 200)

	const tempMatch = block.match(/(-?\d+\s*(?:°C|℃))/i)
	if (tempMatch) temperature = tempMatch[1]

	const cautions = extractCautions(block)

	return {
		title: title || '穿搭方案',
		temperature,
		styleTags: title ? [title] : [],
		content: content || undefined,
		items,
		whyThisWorks: whyThisWorks.length ? whyThisWorks : undefined,
		cautions: cautions.length ? cautions : undefined,
		images: []
	}
}

function parseRawContentToRecommendations(rawText) {
	if (!rawText || typeof rawText !== 'string') return { recommendations: [], intro: '' }

	const text = rawText.trim()
	const recommendations = []

	const schemeSplit = text.split(/(?=####\s*方案[一二三四五六七八九十]+|方案[一二三四五六七八九十]\s*\|)/)
	let intro = ''

	for (let i = 0; i < schemeSplit.length; i++) {
		const block = schemeSplit[i].trim()
		if (!block) continue

		if (i === 0 && !/方案[一二三四五六七八九十]/.test(block)) {
			intro = block.slice(0, 500)
			continue
		}

		if (!/方案[一二三四五六七八九十]/.test(block)) continue
		const rec = parseSchemeBlock(block)
		if (rec.items.length > 0 || rec.whyThisWorks?.length || rec.cautions?.length) {
			recommendations.push(rec)
		}
	}

	if (recommendations.length === 0 && (text.includes('推荐搭配') || text.includes('**上衣**') || text.includes('上衣：'))) {
		const single = parseSchemeBlock(text)
		if (single.items.length > 0 || single.whyThisWorks?.length || single.cautions?.length) {
			recommendations.push(single)
		}
	}

	return { recommendations, intro }
}

function detectRenderType({ content = '', recommendations = [] }) {
	if (recommendations.length === 0) return 'text'
	if (content && content.trim()) return 'mixed'
	return 'recommendation'
}

function buildTextMessage(rawText, content) {
	const finalContent = content || rawText || ''
	return {
		role: 'ai',
		renderType: 'text',
		rawText: rawText || finalContent || '',
		content: finalContent || '',
		recommendations: []
	}
}

function buildStructuredMessage(rawText, content, recommendations) {
	return {
		role: 'ai',
		renderType: detectRenderType({ content, recommendations }),
		rawText: rawText || content || '',
		content: content || '',
		recommendations: recommendations || []
	}
}

function buildPlanMessage(rawText, plan) {
	return {
		role: 'ai',
		renderType: 'plan',
		rawText: rawText || '',
		content: plan?.intro || '',
		recommendations: [],
		plan: plan || { days: [] }
	}
}

/**
 * 规范化旧消息 / 历史消息 / 当前返回消息
 */
export function normalizeChatResponse(apiResponse) {
	if (!apiResponse || typeof apiResponse !== 'object') {
		return buildTextMessage('', '')
	}

	const role = apiResponse.role || 'ai'
	const directRenderType = apiResponse.renderType
	const directRecs = Array.isArray(apiResponse.recommendations) ? apiResponse.recommendations : []
	const rawText =
		apiResponse.rawText ||
		apiResponse.raw_text ||
		apiResponse.content ||
		''

	// 已经是新格式
	if (role === 'ai' && directRenderType) {
		if (directRenderType === 'plan') {
			const plan = apiResponse.plan || (rawText ? parsePlanFromRawText(rawText) : null) || { days: [] }
			return {
				role: 'ai',
				renderType: 'plan',
				rawText: rawText || '',
				content: apiResponse.content || plan?.intro || '',
				recommendations: directRecs,
				plan
			}
		}

		// 兼容旧会话：以前 mixed 的 content 可能被截断过；如果有 rawText，就重新提取 intro 作为 content
		if (directRenderType === 'mixed' && rawText && typeof rawText === 'string') {
			const { intro } = parseRawContentToRecommendations(rawText)
			const rebuilt = safeTrimText(intro || '', 800)
			return {
				role: 'ai',
				renderType: directRenderType,
				rawText: rawText || '',
				content: rebuilt || apiResponse.content || '',
				recommendations: directRecs
			}
		}

		return {
			role: 'ai',
			renderType: directRenderType,
			rawText: rawText || '',
			content: apiResponse.content || '',
			recommendations: directRecs
		}
	}

	// plan：优先识别（避免被 recommendation 解析“误吸收”）
	if (rawText && typeof rawText === 'string' && detectPlan(rawText)) {
		const plan = parsePlanFromRawText(rawText)
		if (plan) return buildPlanMessage(rawText, plan)
	}

	// 后端直接给 recommendations
	if (directRecs.length > 0) {
		return buildStructuredMessage(rawText, apiResponse.content || '', directRecs)
	}

	// 旧文本尝试解析
	if (rawText && typeof rawText === 'string') {
		const { recommendations, intro } = parseRawContentToRecommendations(rawText)
		if (recommendations.length > 0) {
			const shortContent = safeTrimText(intro || '', 800)
			return buildStructuredMessage(rawText, shortContent, recommendations)
		}
		return buildTextMessage(rawText, rawText)
	}

	return buildTextMessage('', '')
}
