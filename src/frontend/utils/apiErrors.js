/**
 * Build a single user-visible message from typical FastAPI / app JSON error bodies.
 * Covers: { message }, { detail: string }, Pydantic v2 { detail: [{ msg, loc, ... }] }.
 * @param {unknown} data - Parsed response body (object or occasionally string)
 * @param {string} fallback - Shown when nothing usable is found (must be clear English)
 * @returns {string}
 */
export function formatApiErrorMessage(data, fallback = 'Something went wrong. Please try again.') {
	if (data == null) return fallback
	if (typeof data === 'string') {
		const t = data.trim()
		return t || fallback
	}
	if (typeof data !== 'object') return fallback

	if (typeof data.message === 'string' && data.message.trim()) {
		return data.message.trim()
	}

	const detail = data.detail
	if (typeof detail === 'string' && detail.trim()) {
		return detail.trim()
	}

	if (Array.isArray(detail) && detail.length > 0) {
		const parts = detail
			.map((item) => {
				if (typeof item === 'string') return item.trim()
				if (item && typeof item === 'object' && typeof item.msg === 'string') {
					let msg = item.msg.trim()
					msg = msg.replace(/^Value error,\s*/i, '')
					const loc = Array.isArray(item.loc) ? item.loc.filter((x) => x && x !== 'body') : []
					const field = loc.length ? String(loc[loc.length - 1]) : ''
					if (field && field !== 'body') {
						const label = field === 'username' ? 'Username' : field === 'email' ? 'Email' : field === 'password' ? 'Password' : field
						if (!msg.toLowerCase().startsWith(label.toLowerCase())) {
							return `${label}: ${msg}`
						}
					}
					return msg
				}
				return ''
			})
			.filter(Boolean)
		if (parts.length) return parts.join(' ')
	}

	if (data.success === false && typeof data.message === 'string' && data.message.trim()) {
		return data.message.trim()
	}

	return fallback
}
