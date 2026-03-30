import { normalizeChatResponse } from './chatContentAdapter.js'
import { attachWardrobeToAiMessage } from './wardrobeImages.js'

/** Convert one persisted history message into the chat UI shape. */
export function normalizeHistoryMsg(msg, wardrobeList) {
	if (!msg || typeof msg !== 'object') return msg

	if (msg.role === 'ai') {
		let normalized = normalizeChatResponse(msg)
		normalized = attachWardrobeToAiMessage(normalized, wardrobeList)
		return normalized
	}

	if (msg.role === 'user') {
		return {
			role: 'user',
			content: msg.content || '',
			images: Array.isArray(msg.images) ? msg.images : []
		}
	}

	return msg
}
