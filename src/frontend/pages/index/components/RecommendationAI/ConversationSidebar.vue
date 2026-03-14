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
				:class="{ 'active': currentConversationId === conv.id, 'has-menu-open': openConvMenuId === conv.id }"
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
import { listConversations, createConversation, updateConversation, deleteConversation } from '@/api/recommendationApi.js'

// 仅「点击主内容区关闭选单」需由 index 控制；conversationState 由 index 传入以便 collapse 时不丢失
const props = defineProps({
	conversationState: { type: Object, default: () => ({ conversations: [], currentConversationId: null, currentConversation: null }) },
	openMenuConvId: { type: String, default: null },
	isLoggedIn: { type: Boolean, default: false }
})

const emit = defineEmits(['update:conversationState', 'update:openMenuConvId'])

const conversations = ref(Array.isArray(props.conversationState?.conversations) ? [...props.conversationState.conversations] : [])
const currentConversationId = ref(props.conversationState?.currentConversationId ?? null)
const openConvMenuId = ref(null)
const renamingConvId = ref(null)
const deletingConvId = ref(null)
const loadingConversations = ref(false)

// 是否为后端返回的 id（数字或数字字符串）
function isServerId(id) {
	if (id == null) return false
	if (typeof id === 'number') return true
	return typeof id === 'string' && /^\d+$/.test(id)
}

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

// 登入后从后端拉取对话列表
async function loadConversationsFromServer() {
	if (!props.isLoggedIn) return
	loadingConversations.value = true
	try {
		const { data } = await listConversations()
		conversations.value = (data || []).map(c => ({
			id: c.id,
			title: c.title || 'New conversation',
			messages: Array.isArray(c.messages) ? c.messages : []
		}))
		// 登入后拉取列表时不自动进入任一会话，保持主页面（问候语 + 输入框）；若当前选中的对话已不在列表中则清空选中
		const stillExists = conversations.value.some(c => c.id === currentConversationId.value)
		if (!stillExists) {
			currentConversationId.value = null
		}
	} catch (e) {
		console.warn('[ConversationSidebar] 拉取对话列表失败', e?.message || e)
	} finally {
		loadingConversations.value = false
		syncState()
	}
}

watch([conversations, currentConversationId], syncState, { deep: true })

watch(() => props.isLoggedIn, (loggedIn) => {
	if (loggedIn) loadConversationsFromServer()
	else {
		conversations.value = []
		currentConversationId.value = null
		syncState()
	}
}, { immediate: false })

onMounted(() => {
	if (props.isLoggedIn) {
		loadConversationsFromServer()
	} else {
		const state = props.conversationState
		if (state && Array.isArray(state.conversations) && state.conversations.length > 0) {
			conversations.value = state.conversations
			currentConversationId.value = state.currentConversationId ?? null
		}
		syncState()
	}
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

const confirmDelete = async () => {
	const id = deletingConvId.value
	deletingConvId.value = null
	if (!id) return
	if (props.isLoggedIn && isServerId(id)) {
		try {
			await deleteConversation(id)
		} catch (e) {
			console.warn('[ConversationSidebar] 删除对话失败', e?.message || e)
		}
	}
	conversations.value = conversations.value.filter(c => c.id !== id)
	if (currentConversationId.value === id) {
		currentConversationId.value = conversations.value[0]?.id ?? null
	}
	syncState()
}

async function handleCreateConversation({ id: providedId, title, firstMessage }) {
	const clientId = providedId || 'c' + Date.now()
	const messages = firstMessage ? [firstMessage] : []
	conversations.value.unshift({
		id: clientId,
		title: title || 'New conversation',
		messages
	})
	currentConversationId.value = clientId
	syncState()

	if (props.isLoggedIn) {
		try {
			const serverConv = await createConversation({ title: title || 'New conversation', messages })
			const idx = conversations.value.findIndex(c => c.id === clientId)
			if (idx !== -1) {
				conversations.value[idx] = {
					id: serverConv.id,
					title: serverConv.title || 'New conversation',
					messages: Array.isArray(serverConv.messages) ? serverConv.messages : messages
				}
				if (currentConversationId.value === clientId) {
					currentConversationId.value = serverConv.id
				}
			}
			syncState()
		} catch (e) {
			console.warn('[ConversationSidebar] 创建对话同步失败', e?.message || e)
		}
	}
}

function handleUpdateConversation({ id, messages, title }) {
	const conv = conversations.value.find(c => c.id === id)
	if (conv) {
		if (messages !== undefined) conv.messages = messages
		if (title !== undefined) conv.title = title
	}
	syncState()

	if (props.isLoggedIn && isServerId(id)) {
		const payload = {}
		if (messages !== undefined) payload.messages = messages
		if (title !== undefined) payload.title = title
		if (Object.keys(payload).length === 0) return
		updateConversation(id, payload).catch(e => {
			console.warn('[ConversationSidebar] 更新对话同步失败', e?.message || e)
		})
	}
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
	transition: all 0.2s ease;
	margin-bottom: 8rpx;
}

.conversation-item:hover {
	background-color: #EEE8DE;
	transform: translateX(2px);
}

.conversation-item:hover .conversation-item-actions {
	opacity: 1;
}

.conversation-item.active {
	background-color: rgba(157, 139, 112, 0.2);
}

/* 展开菜单的项置于最前，避免下方项盖住菜单导致无法点击 Rename/Delete */
.conversation-item.has-menu-open {
	z-index: 200;
	position: relative;
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
	z-index: 300;
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
