<template>
	<view class="card bento-suggested">
		<view class="card-row suggested-card-row">
			<text class="card-label">Suggested Additions</text>
			<view v-if="isLoggedIn" class="suggested-refresh" :class="{ refreshing: loadingSuggested }" @click="$emit('refresh')">
				<text class="refresh-icon">↻</text>
			</view>
		</view>
		<view class="suggest-list">
			<view v-if="!isLoggedIn" class="loading-state">
				<text class="loading-text">Please log in first</text>
			</view>
			<view v-else-if="loadingSuggested" class="loading-state">
				<text class="loading-text">Generating suggestions...</text>
			</view>
			<view v-else-if="suggestedTexts.length === 0 && wardrobeItemCount < SUGGEST_UNLOCK_COUNT" class="suggest-locked-state bento-empty-slot">
				<view class="ai-core-sleeping" aria-hidden="true">
					<view class="ai-core-glow"></view>
				</view>
				<text class="suggest-locked-title">Stylist is on standby</text>
				<text class="suggest-locked-sub">Add items to initialize your bespoke AI analysis.</text>
				<view v-if="openWardrobeTab" class="bento-add-pill" hover-class="bento-add-pill--pressed" @click="goToWardrobe">
					<text class="bento-add-pill-text">Add items +</text>
				</view>
			</view>
			<view v-else-if="suggestedTexts.length === 0" class="suggest-soft-empty bento-empty-slot">
				<text class="suggest-soft-title">No suggestions yet</text>
				<text class="suggest-soft-sub">Tap refresh — we’ll tailor tips to your closet.</text>
			</view>
			<view
				v-else
				v-for="(sug, index) in suggestedTexts"
				:key="`${index}-${sug}`"
				class="suggest-card-v2"
				:class="{ 'suggest-card-v2-expanded': expandedSuggestIndices.includes(index), 'suggest-card-v2-hover': hoveredSuggestIndex === index }"
				@click="toggleSuggestExpanded(index)"
				@mouseenter="hoveredSuggestIndex = index"
				@mouseleave="hoveredSuggestIndex = null"
			>
				<view class="suggest-side">
					<text class="luxury-index">{{ String(index + 1).padStart(2, '0') }}</text>
					<view class="vertical-line"></view>
				</view>
				<view class="suggest-body">
					<text class="suggest-title">{{ parseSuggestLine(sug).title }}</text>
					<view class="suggest-accordion-grid" :class="{ expanded: expandedSuggestIndices.includes(index) }">
						<view class="suggest-accordion-inner">
							<text v-if="parseSuggestLine(sug).detail" class="suggest-detail">{{ parseSuggestLine(sug).detail }}</text>
							<view class="capability-tags">
								<text v-for="tag in getCapabilityTags(sug)" :key="tag" class="tag">{{ tag }}</text>
							</view>
						</view>
					</view>
				</view>
				<view class="item-ghost-icon" :class="{ visible: hoveredSuggestIndex === index }">✦</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, inject } from 'vue'

const SUGGEST_UNLOCK_COUNT = 5

defineProps({
	isLoggedIn: { type: Boolean, default: false },
	loadingSuggested: { type: Boolean, default: true },
	wardrobeItemCount: { type: Number, default: 0 },
	suggestedTexts: { type: Array, default: () => [] }
})

const openWardrobeTab = inject('openWardrobeTab', null)
function goToWardrobe() {
	if (typeof openWardrobeTab === 'function') openWardrobeTab()
}

defineEmits(['refresh'])

const expandedSuggestIndices = ref([])
const hoveredSuggestIndex = ref(null)

function toggleSuggestExpanded(index) {
	const arr = expandedSuggestIndices.value
	if (arr.includes(index)) {
		expandedSuggestIndices.value = arr.filter((i) => i !== index)
	} else {
		expandedSuggestIndices.value = [...arr, index]
	}
}

function parseSuggestLine(sug) {
	if (!sug || typeof sug !== 'string') return { title: '', detail: '' }
	let sep = '，'
	if (sug.includes(' | ')) sep = ' | '
	else if (sug.includes('｜')) sep = '｜'
	const parts = sug.split(sep)
	const title = parts[0]?.trim() || ''
	const detail = parts.slice(1).join(sep).trim()
	return { title, detail }
}

function getCapabilityTags(sug) {
	if (!sug || typeof sug !== 'string') return ['#Essential']
	const t = sug
	const tags = []
	if (/平衡|balance|搭配|協調|layer|outerwear|imbalance/i.test(t)) tags.push('#Balance')
	if (/百搭|versatility|多樣|多用|flexible|mix-and-match/i.test(t)) tags.push('#Versatility')
	if (/正式|formal|場合|office|semi-formal|commute/i.test(t)) tags.push('#Formal')
	if (/基礎|essential|必備|基本|staple|foundation/i.test(t)) tags.push('#Essential')
	if (/下装|下裝|褲|裙|bottom|jeans|trousers|pants|skirt/i.test(t)) tags.push('#WardrobeBalance')
	if (tags.length === 0) tags.push('#Essential')
	return tags.slice(0, 3)
}
</script>
