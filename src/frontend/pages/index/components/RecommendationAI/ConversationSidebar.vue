<!-- Recommendation AI 专用：侧栏「新建会话」+「你的对话」列表 + Rename/Delete 弹窗；状态与方法均在此组件内 -->
<template>
	<view class="conversation-side-block">
		<view class="btn-new-session" @click="handleNewSession">
			<text class="btn-new-session-text">New Conversation</text>
		</view>
		<text class="conversation-label">Your conversations</text>
		<view class="conversation-list">
			<view
				v-for="conv in conversations"
				:key="conv.id"
				class="conversation-item"
				:class="{ 'active': currentConversationId === conv.id }"
				@click="handleSwitchConversation(conv.id)"
			>
				<text class="conversation-item-text">{{ conv.title || 'New conversation' }}</text>
				<view class="conversation-item-actions" @click.stop="toggleConvMenu(conv.id)">
					<image src="/static/icons/icon-more.svg" mode="aspectFit" class="icon-more"></image>
				</view>
				<view v-if="openConvMenuId === conv.id" class="conv-menu" @click.stop>
					<view class="conv-menu-item" @click="handleRenameConv(conv.id)">
						<image src="/static/icons/icon-edit.svg" mode="aspectFit" class="conv-menu-icon"></image>
						<text class="conv-menu-text">Rename</text>
					</view>
					<view class="conv-menu-divider"></view>
					<view class="conv-menu-item conv-menu-item-danger" @click="handleDeleteConv(conv.id)">
						<image src="/static/icons/icon-trash-red.svg" mode="aspectFit" class="conv-menu-icon"></image>
						<text class="conv-menu-text">Delete</text>
					</view>
				</view>
			</view>
		</view>
		<RenameModal
			:visible="!!renamingConvId"
			:initial-value="renamingInitialTitle"
			@confirm="confirmRename"
			@cancel="cancelRename"
		/>
		<DeleteModal
			:visible="!!deletingConvId"
			@confirm="confirmDelete"
			@cancel="cancelDelete"
		/>
	</view>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import RenameModal from './RenameModal.vue'
import DeleteModal from './DeleteModal.vue'

// 仅「点击主内容区关闭选单」需由 index 控制；conversationState 由 index 传入以便 collapse 时不丢失
const props = defineProps({
	conversationState: { type: Object, default: () => ({ conversations: [], currentConversationId: null, currentConversation: null }) },
	openMenuConvId: { type: String, default: null }
})

const emit = defineEmits(['update:conversationState', 'update:openMenuConvId'])

const conversations = ref(Array.isArray(props.conversationState?.conversations) ? [...props.conversationState.conversations] : [])
const currentConversationId = ref(props.conversationState?.currentConversationId ?? null)
const openConvMenuId = ref(null)
const renamingConvId = ref(null)
const deletingConvId = ref(null)

const currentConversation = computed(() => {
	if (!currentConversationId.value) return null
	return conversations.value.find(c => c.id === currentConversationId.value) || null
})

const renamingInitialTitle = computed(() => {
	if (!renamingConvId.value) return ''
	const conv = conversations.value.find(c => c.id === renamingConvId.value)
	return (conv?.title || 'New conversation').slice(0, 36)
})

// 同步到 index，供传给 RecommendationAI
function syncState() {
	emit('update:conversationState', {
		conversations: conversations.value,
		currentConversationId: currentConversationId.value,
		currentConversation: currentConversation.value
	})
}

watch([conversations, currentConversationId], syncState, { deep: true })

onMounted(() => {
	const state = props.conversationState
	if (state && Array.isArray(state.conversations) && state.conversations.length > 0) {
		conversations.value = state.conversations
		currentConversationId.value = state.currentConversationId ?? null
	}
	syncState()
})

// 与 index 的 openMenuConvId 双向同步（index 可通过 closeConvMenu 清空）
watch(() => props.openMenuConvId, (v) => { openConvMenuId.value = v ?? null }, { immediate: true })
watch(openConvMenuId, (v) => { emit('update:openMenuConvId', v ?? null) })

const handleNewSession = () => {
	const cur = currentConversation.value
	if (cur && (!cur.messages || cur.messages.length === 0)) return
	currentConversationId.value = 'c' + Date.now()
}

const handleSwitchConversation = (id) => {
	openConvMenuId.value = null
	emit('update:openMenuConvId', null)
	currentConversationId.value = id
}

const toggleConvMenu = (id) => {
	const next = openConvMenuId.value === id ? null : id
	openConvMenuId.value = next
	emit('update:openMenuConvId', next)
}

const handleRenameConv = (id) => {
	openConvMenuId.value = null
	emit('update:openMenuConvId', null)
	renamingConvId.value = id
}

const confirmRename = (newTitle) => {
	if (renamingConvId.value && newTitle && newTitle.trim()) {
		handleUpdateConversation({ id: renamingConvId.value, title: newTitle.trim().slice(0, 36) })
	}
	renamingConvId.value = null
}

const cancelRename = () => {
	renamingConvId.value = null
}

const handleDeleteConv = (id) => {
	openConvMenuId.value = null
	emit('update:openMenuConvId', null)
	deletingConvId.value = id
}

const cancelDelete = () => {
	deletingConvId.value = null
}

const confirmDelete = () => {
	const id = deletingConvId.value
	if (id) {
		conversations.value = conversations.value.filter(c => c.id !== id)
		if (currentConversationId.value === id) {
			currentConversationId.value = conversations.value[0]?.id ?? null
		}
	}
	deletingConvId.value = null
	syncState()
}

function handleCreateConversation({ id: providedId, title, firstMessage }) {
	const id = providedId || 'c' + Date.now()
	conversations.value.unshift({
		id,
		title: title || 'New conversation',
		messages: firstMessage ? [firstMessage] : []
	})
	currentConversationId.value = id
	syncState()
}

function handleUpdateConversation({ id, messages, title }) {
	const conv = conversations.value.find(c => c.id === id)
	if (conv) {
		if (messages !== undefined) conv.messages = messages
		if (title !== undefined) conv.title = title
	}
	syncState()
}

defineExpose({
	handleCreateConversation,
	handleUpdateConversation
})
</script>

<style scoped>
.conversation-side-block {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	flex: 1;
	min-height: 0;
	overflow: hidden;
}

.btn-new-session {
	flex-shrink: 0;
	width: 100%;
	padding: 20rpx 24rpx;
	border-radius: 50rpx;
	background-color: #9D8B70;
	color: #FFFFFF;
	text-align: center;
	cursor: pointer;
	transition: background-color 0.2s ease;
	box-sizing: border-box;
}

.btn-new-session:hover {
	background-color: #8a7a60;
}

.btn-new-session-text {
	font-size: 28rpx;
	font-weight: 550;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", sans-serif;
}

.conversation-label {
	flex-shrink: 0;
	font-size: 24rpx;
	color: rgba(0, 0, 0, 0.5);
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", sans-serif;
	padding: 0 8rpx;
}

.conversation-list {
	flex: 1;
	min-height: 0;
	overflow-y: auto;
	overflow-x: hidden;
	scrollbar-width: thin;
	scrollbar-color: rgba(157, 139, 112, 0.35) transparent;
}

.conversation-list::-webkit-scrollbar {
	width: 5px;
}
.conversation-list::-webkit-scrollbar-track {
	background: transparent;
}
.conversation-list::-webkit-scrollbar-thumb {
	background: rgba(157, 139, 112, 0.25);
	border-radius: 3px;
}
.conversation-list::-webkit-scrollbar-thumb:hover,
.conversation-list::-webkit-scrollbar-thumb:active {
	background: rgba(157, 139, 112, 0.5);
}

.conversation-item {
	position: relative;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 20rpx 24rpx;
	border-radius: 24rpx;
	cursor: pointer;
	transition: background-color 0.2s ease;
	margin-bottom: 8rpx;
}

.conversation-item:hover {
	background-color: rgba(0, 0, 0, 0.04);
}

.conversation-item:hover .conversation-item-actions {
	opacity: 1;
}

.conversation-item.active {
	background-color: rgba(157, 139, 112, 0.2);
}

.conversation-item-text {
	flex: 1;
	font-size: 26rpx;
	color: #1D1D1F;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", sans-serif;
	font-weight: 400;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	min-width: 0;
}

.conversation-item-actions {
	flex-shrink: 0;
	width: 48rpx;
	height: 48rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	opacity: 0;
	transition: opacity 0.2s ease;
	cursor: pointer;
}

.conversation-item-actions .icon-more {
	width: 24rpx;
	height: 24rpx;
}

.conv-menu {
	position: absolute;
	right: 0;
	top: 100%;
	margin-top: 8rpx;
	background: #fff;
	border-radius: 16rpx;
	box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.12);
	min-width: 160rpx;
	z-index: 100;
	overflow: hidden;
}

.conv-menu-item {
	display: flex;
	align-items: center;
	padding: 24rpx 32rpx;
	cursor: pointer;
	transition: background 0.2s;
}

.conv-menu-icon {
	width: 32rpx;
	height: 32rpx;
	margin-right: 16rpx;
	flex-shrink: 0;
}

.conv-menu-item:hover {
	background: rgba(0, 0, 0, 0.04);
}

.conv-menu-item-danger:hover {
	background: rgba(231, 76, 60, 0.08);
}

.conv-menu-divider {
	height: 1px;
	background: #eee;
}

.conv-menu-text {
	font-size: 26rpx;
	color: #1D1D1F;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", sans-serif;
}

.conv-menu-item-danger .conv-menu-text {
	color: #E74C3C;
}
</style>
