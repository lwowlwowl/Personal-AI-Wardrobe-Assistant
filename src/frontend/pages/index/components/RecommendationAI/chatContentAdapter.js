/**
 * 推荐 AI 聊天内容适配层
 * 职责：将后端流式返回的长篇 Markdown 解析为结构化 recommendation 数据，供 RecommendationCard 渲染。
 * 与后端约定见：backend/AIwardrobe/README.md
 *
 * - 后端返回 { content: string }（SSE 流式累积），本模块经 normalizeChatResponse 解析为 { role, content?, recommendations }
 * - 单条 recommendation：{ title, temperature, styleTags, content, items, whyThisWorks, cautions, images }
 * - 单品 item：{ type, name, subtitle?, reason?, details?, tags? }
 */

/** 加载过程展示文案（轮播）- 杂志感专业术语 */
export const LOADING_STEPS = [
	'Curating your exclusive wardrobe…',
	'Analyzing weather & occasion…',
	'Generating your look…'
]

// ---------- 智能内容适配：从 LLM 原始 Markdown 解析出方案、单品、不推荐等 ----------

/** 去掉 Markdown 粗体符号，便于正则匹配 */
function stripBold(s) {
	if (typeof s !== 'string') return ''
	return s.replace(/\*\*([^*]+)\*\*/g, '$1').trim()
}

/** 从「xxx」或 "xxx" 中提取风格名 */
function extractTitleFromHeader(line) {
	const quoted = /[「\"]([^」\"]+)[」\"]/.exec(line)
	if (quoted) return quoted[1].trim()
	const pipeParts = line.split(/\|/).map(p => p.trim())
	for (const p of pipeParts) {
		if (p && !/^方案[一二三四五六七八九十]+$/.test(p) && !/^推荐指数|★+$/.test(p))
			return p.replace(/^[「\"](.+)[」\"]$/, '$1').trim()
	}
	return ''
}

/**
 * 解析单品行：`英文名` (中文|描述) 或 层级 | 单品 | 理由
 * 返回 { type, name, subtitle, reason, details, tags }
 */
function parseItemLine(line) {
	const trimmed = stripBold(line)
	// 反引号英文 + 括号中文|描述
	const backtick = /`([^`]+)`\s*[（(]([^）)]+)[）)]/.exec(trimmed)
	if (backtick) {
		const en = backtick[1].trim()
		const cnBlock = backtick[2]
		const pipe = cnBlock.indexOf('|')
		const subtitle = pipe >= 0 ? cnBlock.slice(0, pipe).trim() : cnBlock.trim()
		const desc = pipe >= 0 ? cnBlock.slice(pipe + 1).trim() : ''
		// 从描述或副标题中抽标签：逗号/顿号分隔的短词
		const tagCandidates = (subtitle + ' ' + desc).split(/[,，、|]/).map(s => s.trim()).filter(s => s.length >= 2 && s.length <= 8)
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
	// 表格行：层级 | 单品 | 理由
	const tableMatch = /^([^|]+)\|([^|]+)\|?(.*)$/.exec(trimmed)
	if (tableMatch) {
		const type = tableMatch[1].trim().replace(/^\*\*|\*\*$/g, '')
		let name = tableMatch[2].trim().replace(/^\*\*|\*\*$/g, '')
		const reason = tableMatch[3].trim().replace(/^\*\*|\*\*$/g, '') || undefined
		// 若 name 中含 (中文)，拆成 name + subtitle
		const cnInName = /[（(]([^）)]+)[）)]/.exec(name)
		let subtitle
		if (cnInName) {
			subtitle = cnInName[1].trim()
			name = name.replace(/\s*[（(][^）)]+[）)]\s*/, '').trim()
		}
		return { type: type || 'Item', name: name || '—', subtitle, reason, details: undefined, tags: undefined }
	}
	// **层级**：单品描述 或 层级：单品描述
	const colonMatch = /^(?:\*\*)?([^：:]+)(?:\*\*)?[：:]\s*(.+)$/.exec(trimmed)
	if (colonMatch) {
		const type = stripBold(colonMatch[1])
		const rest = colonMatch[2].trim()
		// 可能含 `英文` (中文)
		const inner = /`([^`]+)`\s*[（(]([^）)]+)[）)]/.exec(rest)
		if (inner) {
			const en = inner[1].trim()
			const cn = inner[2].trim()
			const pipe = cn.indexOf('|')
			const subtitle = pipe >= 0 ? cn.slice(0, pipe).trim() : cn
			const details = pipe >= 0 ? cn.slice(pipe + 1).trim() : undefined
			return { type, name: en, subtitle, reason: undefined, details, tags: undefined }
		}
		return { type, name: rest.slice(0, 80), subtitle: undefined, reason: undefined, details: undefined, tags: undefined }
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
		// 去掉 "**温度适配**：" 这类小标题，只保留后半句
		const afterColon = t.replace(/^[^*]*\*\*[^*]*\*\*[：:]\s*/, '').trim()
		const one = afterColon || t
		if (one.length > 4 && one.length < 120) bullets.push(one)
		if (bullets.length >= 3) break
	}
	// 若没有列表，尝试按句号/分号拆成短句
	if (bullets.length === 0) {
		const sentences = block.split(/[。；;]/).map(s => stripBold(s).trim()).filter(s => s.length > 6 && s.length < 100)
		return sentences.slice(0, 3)
	}
	return bullets
}

/** 从全文或块内提取警示句（强烈不推荐、▲、❌、! **请务必**） */
function extractCautions(text) {
	const list = []
	// ! **请务必携带**、**强烈不推荐**、▲、❌ 开头的句子
	const patterns = [
		/!?\s*\*\*([^*]+)\*\*[：:]?\s*([^\n]+)/g,
		/▲\s*([^\n]+)/g,
		/❌\s*([^\n]+)/g,
		/\*\*强烈不推荐\*\*[^\n]*/g,
		/\*\*请务必[^*]*\*\*[^\n]*/g
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

/** 层级中英文映射 */
const LAYER_MAP = {
	上衣: 'Top', 外套: 'Outerwear', 中层: 'Mid Layer', 下装: 'Bottom', 鞋履: 'Shoes', 配饰: 'Accessories',
	'Top': 'Top', 'Outerwear': 'Outerwear', 'Bottom': 'Bottom', 'Shoes': 'Shoes', 'Accessories': 'Accessories'
}

function mapType(type) {
	return LAYER_MAP[type] || type || 'Item'
}

/**
 * 将单个「方案X」块解析为 recommendation 对象
 */
function parseSchemeBlock(block) {
	const title = extractTitleFromHeader(block)
	const items = []
	const whyThisWorks = []
	let content = ''
	let temperature = ''

	// 推荐搭配：③ **推荐搭配** 或 **推荐搭配(基于...)** 后的表格/列表
	let recMatch = block.match(/(?:③|3)[\s]*\*?\*?推荐搭配[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=(?:④|4)[\s]*\*?\*?|⑤|5[\s]*\*?\*?|###|$)/i)
	if (!recMatch) recMatch = block.match(/\*?\*?推荐搭配[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=为什么这样搭|(?:④|4)[\s]*\*?\*?|⑤|5[\s]*\*?\*?|###|$)/i)
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

	// 为什么这样搭：④ **为什么这样搭**
	const whyMatch = block.match(/(?:④|4)[\s]*\*?\*?为什么这样搭[^*\n]*\*?\*?[：:]*\s*([\s\S]*?)(?=(?:⑤|5)[\s]*\*?\*?|可替换|###|$)/i)
	if (whyMatch) whyThisWorks.push(...extractWhyThisWorks(whyMatch[1]))

	// 场景理解 / 穿搭核心思路 可作为 content 摘要（取第一段）
	const sceneMatch = block.match(/(?:①|1)[\s]*\*?\*?场景理解[^*\n]*\*?\*?[：:]*\s*([^\n]+)/i)
	if (sceneMatch) content = stripBold(sceneMatch[1]).slice(0, 200)

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

/**
 * 从原始长文本中拆出多个「方案」并解析为 recommendations 数组
 */
function parseRawContentToRecommendations(rawText) {
	if (!rawText || typeof rawText !== 'string') return []
	const text = rawText.trim()
	const recommendations = []

	// 按 #### 方案一 / 方案二 / 方案三 拆分（兼容无 #### 的「方案一 |」）
	const schemeSplit = text.split(/(?=####\s*方案[一二三四五六七八九十]+|方案[一二三]\s*\|)/)
	let intro = ''
	for (let i = 0; i < schemeSplit.length; i++) {
		const block = schemeSplit[i].trim()
		if (!block) continue
		// 第一个块若不含「方案X」，视为引言
		if (i === 0 && !/方案[一二三四五六七八九十]/.test(block)) {
			intro = block.slice(0, 400)
			continue
		}
		if (!/方案[一二三四五六七八九十]/.test(block)) continue
		const rec = parseSchemeBlock(block)
		if (rec.items.length > 0 || rec.whyThisWorks?.length || rec.title) recommendations.push(rec)
	}

	// 若没有拆出任何方案，尝试按 ### 标题拆（如「明日早课专属穿搭方案」下直接跟列表）
	if (recommendations.length === 0 && (text.includes('推荐搭配') || text.includes('**上衣**'))) {
		const single = parseSchemeBlock(text)
		if (single.items.length > 0 || single.whyThisWorks?.length) recommendations.push(single)
	}

	return { recommendations, intro }
}

/**
 * 将后端流式返回的数据规范为聊天消息结构，供 push 到 chatHistory
 * 若仅有 content（长 Markdown），则经智能解析得到 recommendations + 简短 content
 * @param {{ content?: string, recommendations?: Array }} apiResponse - 后端返回（如 SSE 累积的 { content }）
 * @returns {{ role: 'ai', content?: string, recommendations?: Array }}
 */
export function normalizeChatResponse(apiResponse) {
	if (!apiResponse || typeof apiResponse !== 'object') {
		return { role: 'ai', content: '' }
	}
	const hasRecs = Array.isArray(apiResponse.recommendations) && apiResponse.recommendations.length > 0
	if (hasRecs) {
		return {
			role: 'ai',
			...(apiResponse.content != null && { content: apiResponse.content }),
			recommendations: apiResponse.recommendations
		}
	}
	// 仅有 content：解析长 Markdown 为结构化 recommendations
	const raw = apiResponse.content
	if (raw && typeof raw === 'string' && raw.length > 100) {
		const { recommendations, intro } = parseRawContentToRecommendations(raw)
		if (recommendations.length > 0) {
			// 引言截断为简短摘要（可选展示在首张卡片上方）
			const shortContent = intro.replace(/\n+/g, ' ').slice(0, 280).trim()
			return {
				role: 'ai',
				...(shortContent && { content: shortContent }),
				recommendations
			}
		}
	}
	// 解析失败或内容过短：退回纯 content 展示
	return {
		role: 'ai',
		...(apiResponse.content != null && { content: apiResponse.content || '' })
	}
}
