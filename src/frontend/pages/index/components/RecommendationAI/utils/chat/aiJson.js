/**
 * If AI message content embeds a full JSON blob (no recommendations/plan at top level yet),
 * expand it to the canonical shape before normalizeChatResponse.
 */
export function expandEmbeddedJsonAiMessage(aiMessage) {
	let toNormalize = aiMessage
	const hasStructure =
		(Array.isArray(aiMessage?.recommendations) && aiMessage.recommendations.length > 0) ||
		(aiMessage?.plan?.days && aiMessage.plan.days.length > 0)
	if (
		!hasStructure &&
		aiMessage?.content &&
		typeof aiMessage.content === 'string' &&
		aiMessage.content.trim().startsWith('{')
	) {
		try {
			const parsed = JSON.parse(aiMessage.content.trim())
			if (parsed && typeof parsed === 'object') {
				toNormalize = {
					role: 'ai',
					rawText: aiMessage.content.trim(),
					content: parsed.content ?? '',
					recommendations: parsed.recommendations ?? [],
					plan: parsed.plan ?? null,
					locale: parsed.locale ?? 'en'
				}
			}
		} catch (_) {}
	}
	return toNormalize
}
