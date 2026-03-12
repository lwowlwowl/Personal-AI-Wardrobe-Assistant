/**
 * 推荐 AI 的 Mock 数据与常量
 * 与后端 AIwardrobe 联调约定见：backend/AIwardrobe/README.md
 *
 * API 约定（真实接口为 POST /api/ai/chat/stream，SSE 流式）：
 * - Mock 与 normalizeChatResponse 兼容：{ content?: string, recommendations?: Array }
 * 单条 recommendation：{ title, temperature, styleTags, content, items, whyThisWorks, images }
 */

/** 是否使用 Mock（true=本地 mock，false=请求后端 /api/ai/chat/stream） */
export const USE_RECOMMENDATION_MOCK = false

/** 加载过程展示文案（轮播） */
export const LOADING_STEPS = [
	'Analyzing weather…',
	'Matching wardrobe…',
	'Generating recommendations…'
]

/** 单条推荐卡片数据结构（与 RecommendationCard.vue 的 props 一致） */
const MOCK_RECOMMENDATION = {
	title: 'Campus Casual',
	temperature: '18-22°C',
	styleTags: ['Light Layering', 'Casual'],
	content: '🌤 Tomorrow looks perfect for light layering.\n\nWe styled a campus-ready outfit that keeps you warm in the morning and breathable at noon.',
	items: [
		{ type: 'Top', name: 'Thin Knit Sweater', reason: 'Warm & breathable', details: '建议选择羊绒或美利奴羊毛混纺，透气且保暖。色彩与下装形成层次对比。' },
		{ type: 'Bottom', name: 'Straight Jeans', reason: 'Versatile fit', details: '直筒版型平衡上身宽松感，深色系与米色针织形成经典搭配。' },
		{ type: 'Outerwear', name: 'Softshell Jacket', reason: 'Morning warmth, noon off', details: '轻薄防风，叠穿不臃肿。建议选择与针织同色系。' },
		{ type: 'Shoes', name: 'White Sneakers', reason: 'Clean & fresh look', details: '白色鞋款打破深色主导，呼应针织的清爽感，比例更协调。' },
		{ type: 'Accessories', name: 'Light Scarf', reason: 'Wind-break accent', details: '浅色围巾与上衣同色系，避免视觉割裂。' }
	],
	whyThisWorks: [
		'Soft knit keeps warmth without bulk',
		'Straight jeans balance proportions',
		'White sneakers brighten the look'
	],
	images: [
		'https://images.unsplash.com/photo-1434389677669-e08b4cac3105?q=80&w=400',
		'https://images.unsplash.com/photo-1542272454315-4c01d7abdf4a?q=80&w=400',
		'https://images.unsplash.com/photo-1549298916-b41d501d3772?q=80&w=400'
	]
}

/**
 * 返回与 API 一致的 AI 消息结构（当前为 mock，联调时改为调用接口后组装成此结构）
 * @returns {{ role: 'ai', recommendations: Array }} 可直接 push 到 chatHistory 的消息对象
 */
export function getMockAiResponse() {
	return {
		role: 'ai',
		recommendations: [{ ...MOCK_RECOMMENDATION }]
	}
}

/**
 * 模拟请求延迟（ms），仅 USE_RECOMMENDATION_MOCK 为 true 时使用
 */
export const MOCK_DELAY_MS = 2500

/**
 * 将后端 /api/chat 返回的数据规范为聊天消息结构，供 push 到 chatHistory
 * @param {{ content?: string, recommendations?: Array }} apiResponse - 后端返回的 body
 * @returns {{ role: 'ai', content?: string, recommendations?: Array }}
 */
export function normalizeChatResponse(apiResponse) {
	if (!apiResponse || typeof apiResponse !== 'object') {
		return { role: 'ai', content: '' }
	}
	const hasRecs = Array.isArray(apiResponse.recommendations) && apiResponse.recommendations.length > 0
	return {
		role: 'ai',
		...(apiResponse.content != null && { content: apiResponse.content }),
		...(hasRecs && { recommendations: apiResponse.recommendations })
	}
}
