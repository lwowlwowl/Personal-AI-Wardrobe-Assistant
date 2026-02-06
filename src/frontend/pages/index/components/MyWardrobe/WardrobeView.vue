<template>
	<scroll-view class="wardrobe-container" scroll-y :show-scrollbar="false">
		<view class="wardrobe-inner">
			<!-- Header: 標題可選，設計圖上有的寫 Wardrobe Management -->
			<view class="header">
				<view class="toggle-switch">
					<view 
						class="switch-item" 
						:class="{ active: viewMode === 'Model' }" 
						@click="viewMode = 'Model'"
					>Model</view>
					<view 
						class="switch-item" 
						:class="{ active: viewMode === 'Cloth' }" 
						@click="viewMode = 'Cloth'"
					>Cloth</view>
				</view>
				<view class="search-bar">
					<image src="/static/icons/icon-search.svg" mode="aspectFit" class="icon-search"></image>
					<input 
						v-if="viewMode === 'Cloth'"
						class="search-input" 
						type="text" 
						placeholder="Search by keywords..." 
						placeholder-class="search-placeholder"
						v-model="searchQuery"
					/>
					<input 
						v-else
						class="search-input" 
						type="text" 
						placeholder="Search by posture..." 
						placeholder-class="search-placeholder"
						v-model="modelSearchQuery"
					/>
				</view>
			</view>

			<!-- Filter Section -->
			<view class="filter-section">
				<view class="filter-header">
					<text class="section-title">Filter</text>
					<view class="filter-buttons">
						<view class="filter-group">
							<view 
								class="filter-btn" 
								:class="{ open: activeFilter === 'favourite', 'has-value': appliedFavouriteLevels.length > 0 }"
								@click="toggleFilter('favourite')"
							>
								<text>Favourite</text>
								<image 
									:src="activeFilter === 'favourite' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" 
									mode="aspectFit" 
									class="icon-arrow"
								></image>
							</view>
							<view v-if="activeFilter === 'favourite'" class="dropdown-menu">
								<text class="dropdown-title">Favourite</text>
								<view class="option-list favourite-levels">
									<view 
										v-for="n in 4" 
										:key="n" 
										class="option-item option-hearts" 
										:class="{ active: selectedFavouriteLevels.includes(n - 1) }"
										@click="toggleFavouriteLevel(n - 1)"
									>
										<text class="hearts-label">{{ n - 1 }} {{ n - 1 === 1 ? 'heart' : 'hearts' }}</text>
										<view class="hearts-inline">
											<image 
												v-for="k in 3" 
												:key="k" 
												:src="k <= n - 1 ? '/static/icons/icon-heart-filled.svg' : '/static/icons/icon-heart.svg'" 
												mode="aspectFit" 
												class="heart-small"
											/>
										</view>
									</view>
								</view>
								<view class="dropdown-actions">
									<view class="apply-btn" @click="applyFavourite">Apply</view>
									<view class="reset-btn" @click="resetFavourite">Reset</view>
								</view>
							</view>
						</view>
						<view class="filter-group">
							<view 
								class="filter-btn" 
								:class="{ open: activeFilter === 'date', 'has-value': appliedDate != null }"
								@click="toggleFilter('date')"
							>
								<text>Date</text>
								<image :src="activeFilter === 'date' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="icon-arrow"></image>
							</view>
							<view v-if="activeFilter === 'date'" class="dropdown-menu">
								<text class="dropdown-title">Sort by Date</text>
								<radio-group @change="onDateChange">
									<label class="radio-item">
										<radio value="asc" :checked="dateSortOrder === 'asc'" color="#5a9a2e" /> Ascending
									</label>
									<label class="radio-item">
										<radio value="desc" :checked="dateSortOrder === 'desc'" color="#5a9a2e" /> Descending
									</label>
								</radio-group>
								<view class="dropdown-actions">
									<view class="apply-btn" @click="applyDate">Apply</view>
									<view class="reset-btn" @click="resetDate">Reset</view>
								</view>
							</view>
						</view>
						<view v-if="viewMode === 'Cloth'" class="filter-group">
							<view 
								class="filter-btn" 
								:class="{ open: activeFilter === 'type', 'has-value': appliedTypes.length > 0 }"
								@click="toggleFilter('type')"
							>
								<text>Clothing type</text>
								<image :src="activeFilter === 'type' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="icon-arrow"></image>
							</view>
							<view v-if="activeFilter === 'type'" class="dropdown-menu">
								<text class="dropdown-title">Clothing Type</text>
								<view class="option-list">
									<view 
										v-for="opt in typeOptions" 
										:key="opt.value" 
										class="option-item" 
										:class="{ active: selectedTypes.includes(opt.value) }"
										@click="toggleType(opt.value)"
									>{{ opt.label }}</view>
								</view>
								<view class="dropdown-actions">
									<view class="apply-btn" @click="applyType">Apply</view>
									<view class="reset-btn" @click="resetType">Reset</view>
								</view>
							</view>
						</view>
						<view v-if="viewMode === 'Cloth'" class="filter-group">
							<view 
								class="filter-btn" 
								:class="{ open: activeFilter === 'color', 'has-value': appliedColors.length > 0 }"
								@click="toggleFilter('color')"
							>
								<text>Color</text>
								<image :src="activeFilter === 'color' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="icon-arrow"></image>
							</view>
							<view v-if="activeFilter === 'color'" class="dropdown-menu">
								<text class="dropdown-title">Color</text>
								<view class="option-list">
									<view 
										v-for="opt in colorOptions" 
										:key="opt.value" 
										class="option-item" 
										:class="{ active: selectedColors.includes(opt.value) }"
										@click="toggleColor(opt.value)"
									>{{ opt.label }}</view>
								</view>
								<view class="dropdown-actions">
									<view class="apply-btn" @click="applyColor">Apply</view>
									<view class="reset-btn" @click="resetColor">Reset</view>
								</view>
							</view>
						</view>
						<view v-if="viewMode === 'Cloth'" class="filter-group">
							<view 
								class="filter-btn" 
								:class="{ open: activeFilter === 'season', 'has-value': appliedSeasons.length > 0 }"
								@click="toggleFilter('season')"
							>
								<text>Season</text>
								<image :src="activeFilter === 'season' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="icon-arrow"></image>
							</view>
							<view v-if="activeFilter === 'season'" class="dropdown-menu">
								<text class="dropdown-title">Season</text>
								<view class="option-list">
									<view 
										v-for="opt in seasonOptions" 
										:key="opt.value" 
										class="option-item" 
										:class="{ active: selectedSeasons.includes(opt.value) }"
										@click="toggleSeason(opt.value)"
									>{{ opt.label }}</view>
								</view>
								<view class="dropdown-actions">
									<view class="apply-btn" @click="applySeason">Apply</view>
									<view class="reset-btn" @click="resetSeason">Reset</view>
								</view>
							</view>
						</view>
					</view>
				</view>
				<view class="upload-widget" @click="handleUpload">
					<div
						class="upload-dashed"
						:class="{ dragging: uploadDragging }"
						@drop.prevent.stop="handleUploadDrop"
						@dragover.prevent.stop="handleUploadDragOver"
						@dragleave.prevent.stop="handleUploadDragLeave"
						@dragenter.prevent.stop
					>
						<image src="/static/icons/icon-image-upload.svg" mode="aspectFit" class="icon-upload"></image>
						<text class="upload-text"><text class="blue">Click to upload</text> or drag and drop</text>
						<text class="upload-hint">JPG, JPEG, PNG less than 1MB</text>
					</div>
				</view>
			</view>

			<view class="divider"></view>

			<transition name="view-switch" mode="out-in">
				<view :key="viewMode" class="view-switch-inner">
					<!-- Cloth Grid -->
					<template v-if="viewMode === 'Cloth'">
						<transition name="page-fade" mode="out-in">
							<view class="clothes-grid" :key="currentPage">
								<view 
									v-for="(item, index) in paginatedList" 
									:key="item.id" 
									class="cloth-card"
									@click="openDetail(item)"
								>
									<view class="img-wrapper">
										<image :src="item.image" mode="aspectFill" class="cloth-img" />
									</view>
								</view>
							</view>
						</transition>
						<view class="pagination" v-if="totalPages > 1">
							<view 
								class="page-btn prev" 
								:class="{ disabled: currentPage <= 1 }"
								@click="currentPage > 1 && (currentPage = currentPage - 1)"
							>Prev</view>
							<view class="pagination-dots">
								<view 
									v-for="i in totalPages" 
									:key="i" 
									class="dot" 
									:class="{ active: currentPage === i }"
									@click="currentPage = i"
								></view>
							</view>
							<view 
								class="page-btn next" 
								:class="{ disabled: currentPage >= totalPages }"
								@click="currentPage < totalPages && (currentPage = currentPage + 1)"
							>Next</view>
						</view>
					</template>

					<!-- Model Grid -->
					<template v-else>
						<transition name="page-fade" mode="out-in">
							<view class="clothes-grid model-grid" :key="modelCurrentPage">
								<view 
									v-for="(item, index) in modelPaginatedList" 
									:key="item.id" 
									class="model-card"
									:class="{ 'is-default': item.id === defaultModelId }"
									@click="openModelDetail(item)"
								>
									<view class="model-img-wrap">
										<image :src="item.image" mode="aspectFill" class="model-img" />
										<view v-if="item.id === defaultModelId" class="model-default-badge">Default</view>
									</view>
								</view>
							</view>
						</transition>
						<view class="pagination" v-if="modelTotalPages > 1">
							<view 
								class="page-btn prev" 
								:class="{ disabled: modelCurrentPage <= 1 }"
								@click="modelPrevPage"
							>Prev</view>
							<view class="pagination-dots">
								<view 
									v-for="i in modelTotalPages" 
									:key="i" 
									class="dot" 
									:class="{ active: modelCurrentPage === i }"
									@click="modelCurrentPage = i"
								></view>
							</view>
							<view 
								class="page-btn next" 
								:class="{ disabled: modelCurrentPage >= modelTotalPages }"
								@click="modelNextPage"
							>Next</view>
						</view>
					</template>
				</view>
			</transition>
		</view>

		<DetailModal
			v-model:visible="showModal"
			:item="selectedItem"
			@try-on="handleVirtualTryOn"
			@delete="handleDeleteItem"
			@update="handleItemUpdate"
		/>
		<ModelDetailModal
			v-model:visible="showModelModal"
			:item="selectedModel"
			:default-model-id="defaultModelId"
			@delete="handleModelDelete"
			@update="handleModelUpdate"
			@set-default="handleSetDefaultModel"
		/>
	</scroll-view>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import DetailModal from './DetailModal.vue'
import ModelDetailModal from './ModelDetailModal.vue'
import { TYPE_OPTIONS, COLOR_OPTIONS, SEASON_OPTIONS } from '@/utils/wardrobeEnums.js'

const emit = defineEmits(['switch-to-tryon'])

const viewMode = ref('Cloth')
const searchQuery = ref('')
const modelSearchQuery = ref('')
const activeFilter = ref(null)
const showModal = ref(false)
const selectedItem = ref({})
const showModelModal = ref(false)
const selectedModel = ref({})
const currentPage = ref(1)

// Favourite: filter by heart count 0-3 (multi-select)
const selectedFavouriteLevels = ref([])
const appliedFavouriteLevels = ref([])

// Date：升序/降序
const dateSortOrder = ref('desc')
const appliedDate = ref(null)

// Clothing type（多选，存 code）
const typeOptions = TYPE_OPTIONS
const selectedTypes = ref([])
const appliedTypes = ref([])

// Color（多选，存 code）
const colorOptions = COLOR_OPTIONS
const selectedColors = ref([])
const appliedColors = ref([])

// Season（多选，存 code）
const seasonOptions = SEASON_OPTIONS
const selectedSeasons = ref([])
const appliedSeasons = ref([])

// Mock 資料（type/color/season 使用 API code，與 MY_WARDROBE.md 附錄一致）
const clothes = ref([
	{ id: 1, name: 'Basic White Tee', type: 't_shirt', date: '2024-01-10', color: 'white', season: 'summer', favourite: 0, image: 'https://placehold.co/400x500/f5f0e6/8c7b60?text=White+Tee' },
	{ id: 2, name: 'Pumpkin Puff Sleeve Top', type: 'blouse', date: '2024-11-18', color: 'burnt_orange', season: 'summer', favourite: 1, image: 'https://placehold.co/400x500/e8a857/5c4a32?text=Pumpkin+Top' },
	{ id: 3, name: 'Black Camisole', type: 'top', date: '2024-02-15', color: 'black', season: 'summer', favourite: 2, image: 'https://placehold.co/400x500/2c2c2c/fff?text=Black+Camisole' },
	{ id: 4, name: 'Striped Long Sleeve', type: 'top', date: '2023-12-05', color: 'black_white', season: 'autumn', favourite: 1, image: 'https://placehold.co/400x500/f5f0e6/2c2c2c?text=Striped' },
	{ id: 5, name: 'Brown Tank', type: 'vest', date: '2023-08-20', color: 'brown', season: 'summer', favourite: 0, image: 'https://placehold.co/400x500/8b6914/f5f0e6?text=Brown+Tank' },
	{ id: 6, name: 'Navy V-Neck', type: 'sweater', date: '2024-01-05', color: 'navy', season: 'winter', favourite: 3, image: 'https://placehold.co/400x500/1e3a5f/f5f0e6?text=Navy+V-Neck' },
	{ id: 7, name: 'Beige Button Up', type: 'shirt', date: '2024-03-01', color: 'beige', season: 'spring', favourite: 1, image: 'https://placehold.co/400x500/d4b896/5c4a32?text=Beige+Shirt' },
	{ id: 8, name: 'Olive Wrap Top', type: 'blouse', date: '2023-10-12', color: 'olive', season: 'autumn', favourite: 0, image: 'https://placehold.co/400x500/6b7c3c/f5f0e6?text=Olive+Wrap' },
	{ id: 9, name: 'Example Cloth', type: 'blouse', date: '2024-12-01', color: 'white', season: 'spring', favourite: 0, image: '/static/cloth_example.png' },
])

// Model mock data (posture for search, date, favourite 0-3)
const models = ref([
	{ id: 101, posture: 'Arms crossed', date: '2024-10-01', favourite: 0, image: 'https://placehold.co/400x500/e8e4dc/8c7b60?text=Model+1' },
	{ id: 102, posture: 'Hands in pockets', date: '2024-09-15', favourite: 0, image: 'https://placehold.co/400x500/d4d0c8/5c4a32?text=Model+2' },
	{ id: 103, posture: 'Example model', date: '2024-12-01', favourite: 0, image: '/static/model_example.png' },
])
// Only one default model; always shown as first block (model_example 為預設)
const defaultModelId = ref(103)

const displayList = computed(() => {
	let list = [...clothes.value]
	if (searchQuery.value.trim()) {
		const q = searchQuery.value.trim().toLowerCase()
		list = list.filter(
			(c) =>
				(c.name || '').toLowerCase().includes(q) ||
				(c.type || '').toLowerCase().includes(q) ||
				(c.color || '').toLowerCase().includes(q)
		)
	}
	const dateOrder = appliedDate.value
	if (dateOrder === 'asc' || dateOrder === 'desc') {
		list = [...list].sort((a, b) => dateOrder === 'asc' ? (a.date || '').localeCompare(b.date || '') : (b.date || '').localeCompare(a.date || ''))
	}
	if (appliedFavouriteLevels.value.length > 0) {
		const levels = appliedFavouriteLevels.value
		list = list.filter((c) => levels.includes(Number(c.favourite) || 0))
	}
	// type/color/season 可能为多选（逗号分隔），筛选时只要有一个 code 命中即显示
	const parseItemCodes = (str) => (str || '').split(/[,/]+/).map((s) => s.trim()).filter(Boolean)
	if (appliedTypes.value.length > 0) {
		const types = appliedTypes.value
		list = list.filter((c) => parseItemCodes(c.type).some((code) => types.includes(code)))
	}
	if (appliedColors.value.length > 0) {
		const colors = appliedColors.value
		list = list.filter((c) => parseItemCodes(c.color).some((code) => colors.includes(code)))
	}
	if (appliedSeasons.value.length > 0) {
		const seasons = appliedSeasons.value
		list = list.filter((c) => parseItemCodes(c.season).some((code) => seasons.includes(code)))
	}
	return list
})

const PAGE_SIZE = 8

const totalPages = computed(() => {
	const total = displayList.value.length
	return Math.max(1, Math.ceil(total / PAGE_SIZE))
})

const paginatedList = computed(() => {
	const list = displayList.value
	const start = (currentPage.value - 1) * PAGE_SIZE
	return list.slice(start, start + PAGE_SIZE)
})

// Model list: default model always first, then rest (filtered/sorted)
const modelDisplayList = computed(() => {
	const defaultId = defaultModelId.value
	const defaultModel = defaultId ? models.value.find((m) => m.id === defaultId) : null
	let rest = defaultId ? models.value.filter((m) => m.id !== defaultId) : [...models.value]
	const q = modelSearchQuery.value.trim().toLowerCase()
	if (q) rest = rest.filter((m) => (m.posture || '').toLowerCase().includes(q))
	if (appliedFavouriteLevels.value.length > 0) {
		const levels = appliedFavouriteLevels.value
		rest = rest.filter((m) => levels.includes(Number(m.favourite) || 0))
	}
	const dateOrder = appliedDate.value
	if (dateOrder === 'asc' || dateOrder === 'desc') {
		rest = [...rest].sort((a, b) => dateOrder === 'asc' ? (a.date || '').localeCompare(b.date || '') : (b.date || '').localeCompare(a.date || ''))
	}
	return defaultModel ? [defaultModel, ...rest] : rest
})

const modelCurrentPage = ref(1)
const modelTotalPages = computed(() => {
	const total = modelDisplayList.value.length
	return Math.max(1, Math.ceil(total / PAGE_SIZE))
})
const modelPaginatedList = computed(() => {
	const list = modelDisplayList.value
	const start = (modelCurrentPage.value - 1) * PAGE_SIZE
	return list.slice(start, start + PAGE_SIZE)
})

watch(modelTotalPages, (val) => {
	if (modelCurrentPage.value > val) modelCurrentPage.value = val
}, { immediate: true })

function modelPrevPage() {
	if (modelCurrentPage.value > 1) modelCurrentPage.value -= 1
}
function modelNextPage() {
	if (modelCurrentPage.value < modelTotalPages.value) modelCurrentPage.value += 1
}

watch(totalPages, (val) => {
	if (currentPage.value > val) {
		currentPage.value = val
	}
}, { immediate: true })

watch(viewMode, () => {
	activeFilter.value = null
})

const toggleFilter = (name) => {
	if (activeFilter.value === name) {
		activeFilter.value = null
		return
	}
	activeFilter.value = name
	if (name === 'favourite') selectedFavouriteLevels.value = [...appliedFavouriteLevels.value]
	if (name === 'date') dateSortOrder.value = appliedDate.value ?? 'desc'
	if (name === 'type') selectedTypes.value = [...appliedTypes.value]
	if (name === 'color') selectedColors.value = [...appliedColors.value]
	if (name === 'season') selectedSeasons.value = [...appliedSeasons.value]
}

const toggleFavouriteLevel = (level) => {
	const arr = selectedFavouriteLevels.value
	const i = arr.indexOf(level)
	if (i >= 0) arr.splice(i, 1)
	else arr.push(level)
	arr.sort((a, b) => a - b)
}

const onDateChange = (e) => {
	const v = e.detail?.value
	if (v === 'asc' || v === 'desc') dateSortOrder.value = v
}

const applyFavourite = () => {
	appliedFavouriteLevels.value = [...selectedFavouriteLevels.value]
	activeFilter.value = null
}

const resetFavourite = () => {
	appliedFavouriteLevels.value = []
	selectedFavouriteLevels.value = []
	activeFilter.value = null
}

const applyDate = () => {
	appliedDate.value = dateSortOrder.value
	activeFilter.value = null
}

const resetDate = () => {
	appliedDate.value = null
	dateSortOrder.value = 'desc'
	activeFilter.value = null
}

const toggleType = (opt) => {
	const i = selectedTypes.value.indexOf(opt)
	if (i >= 0) selectedTypes.value = selectedTypes.value.filter((_, idx) => idx !== i)
	else selectedTypes.value = [...selectedTypes.value, opt]
}

const applyType = () => {
	appliedTypes.value = [...selectedTypes.value]
	activeFilter.value = null
}

const resetType = () => {
	appliedTypes.value = []
	selectedTypes.value = []
	activeFilter.value = null
}

const toggleColor = (opt) => {
	const i = selectedColors.value.indexOf(opt)
	if (i >= 0) selectedColors.value = selectedColors.value.filter((_, idx) => idx !== i)
	else selectedColors.value = [...selectedColors.value, opt]
}

const applyColor = () => {
	appliedColors.value = [...selectedColors.value]
	activeFilter.value = null
}

const resetColor = () => {
	appliedColors.value = []
	selectedColors.value = []
	activeFilter.value = null
}

const toggleSeason = (opt) => {
	const i = selectedSeasons.value.indexOf(opt)
	if (i >= 0) selectedSeasons.value = selectedSeasons.value.filter((_, idx) => idx !== i)
	else selectedSeasons.value = [...selectedSeasons.value, opt]
}

const applySeason = () => {
	appliedSeasons.value = [...selectedSeasons.value]
	activeFilter.value = null
}

const resetSeason = () => {
	appliedSeasons.value = []
	selectedSeasons.value = []
	activeFilter.value = null
}

const openDetail = (item) => {
	selectedItem.value = { ...item }
	showModal.value = true
}

const openModelDetail = (item) => {
	selectedModel.value = { ...item }
	showModelModal.value = true
}

const handleModelDelete = (id) => {
	models.value = models.value.filter((m) => m.id !== id)
	if (defaultModelId.value === id) defaultModelId.value = null
}

const handleSetDefaultModel = (id) => {
	defaultModelId.value = id
}

const handleModelUpdate = ({ id, field, value }) => {
	const idx = models.value.findIndex((m) => m.id === id)
	if (idx < 0) return
	models.value[idx] = { ...models.value[idx], [field]: value }
	selectedModel.value = { ...models.value[idx] }
}

const handleVirtualTryOn = (item) => {
	showModal.value = false
	const defaultModel = defaultModelId.value ? models.value.find((m) => m.id === defaultModelId.value) : null
	const defaultModelImage = defaultModel?.image ?? null
	emit('switch-to-tryon', item, defaultModelImage)
}

const handleDeleteItem = (id) => {
	clothes.value = clothes.value.filter((c) => c.id !== id)
}

const handleItemUpdate = ({ id, field, value }) => {
	const idx = clothes.value.findIndex((c) => c.id === id)
	if (idx < 0) return
	clothes.value[idx] = { ...clothes.value[idx], [field]: value }
	selectedItem.value = { ...clothes.value[idx] }
}

const uploadDragging = ref(false)

const handleUploadDragOver = (event) => {
	uploadDragging.value = true
	if (event?.dataTransfer) event.dataTransfer.dropEffect = 'copy'
}

const handleUploadDragLeave = () => {
	uploadDragging.value = false
}

const handleUploadDrop = (event) => {
	uploadDragging.value = false
	if (event && event.preventDefault) event.preventDefault()
	if (event && event.stopPropagation) event.stopPropagation()
	const dataTransfer = event?.dataTransfer || event?.originalEvent?.dataTransfer
	const files = dataTransfer?.files
	if (!files || files.length === 0) return
	const file = files[0]
	if (!file.type || !file.type.startsWith('image/')) {
		uni.showToast({ title: 'Please drop an image file', icon: 'none' })
		return
	}
	const url = URL.createObjectURL(file)
	const newItem = viewMode.value === 'Model'
		? {
			id: Date.now(),
			posture: 'New Model',
			date: new Date().toISOString().slice(0, 10),
			favourite: 0,
			image: url,
		}
		: {
			id: Date.now(),
			name: 'New Item',
			type: 'blouse',
			date: new Date().toISOString().slice(0, 10),
			color: '',
			season: '',
			favourite: 0,
			image: url,
		}
	if (viewMode.value === 'Model') {
		models.value = [newItem, ...models.value]
	} else {
		clothes.value = [newItem, ...clothes.value]
	}
}

const handleUpload = () => {
	uni.chooseImage({
		count: 1,
		sizeType: ['compressed'],
		sourceType: ['album', 'camera'],
		success: (res) => {
			const tempFilePath = res.tempFilePaths[0]
			if (viewMode.value === 'Model') {
				models.value.unshift({
					id: Date.now(),
					posture: 'New Model',
					date: new Date().toISOString().slice(0, 10),
					favourite: 0,
					image: tempFilePath,
				})
			} else {
				clothes.value.unshift({
					id: Date.now(),
					name: 'New Item',
					type: 'blouse',
					date: new Date().toISOString().slice(0, 10),
					color: '',
					season: '',
					favourite: 0,
					image: tempFilePath,
				})
			}
		},
	})
}
</script>

<style scoped>
.wardrobe-container {
	width: 100%;
	height: 100%;
	min-height: 100%;
	background-color: #FDFBF7;
	box-sizing: border-box;
}

.wardrobe-inner {
	width: 100%;
	min-height: 100%;
	padding: 60rpx 80rpx 80rpx;
	box-sizing: border-box;
}

.header {
	display: flex;
	align-items: center;
	gap: 32rpx;
	margin-bottom: 48rpx;
}

.toggle-switch {
	background-color: #F5F0E6;
	border-radius: 44rpx;
	padding: 10rpx;
	display: flex;
	border: 2rpx solid rgba(29, 29, 31, 0.2);
	box-shadow: inset 0 1rpx 2rpx rgba(0, 0, 0, 0.04);
}

.switch-item {
	min-width: 120rpx;
	padding: 18rpx 40rpx;
	border-radius: 36rpx;
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 28rpx;
	font-weight: 600;
	color: #1D1D1F;
	transition: background 0.25s ease, color 0.25s ease, box-shadow 0.25s ease;
	cursor: pointer;
	text-align: center;
}

.switch-item.active {
	background-color: #9D8B70;
	color: #FFF;
	box-shadow: 0 4rpx 12rpx rgba(157, 139, 112, 0.35);
}

.search-bar {
	flex: 1;
	border: 2rpx solid #1D1D1F;
	border-radius: 50rpx;
	padding: 20rpx 28rpx;
	display: flex;
	align-items: center;
	background: #FFF;
	gap: 16rpx;
}

.icon-search {
	width: 36rpx;
	height: 36rpx;
	flex-shrink: 0;
}

.search-input {
	flex: 1;
	font-size: 30rpx;
	color: #1D1D1F;
	font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
}

.search-placeholder {
	color: #999;
	font-weight: 300;
	font-family: serif;
}

.filter-section {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	gap: 32rpx;
	flex-wrap: wrap;
}

.filter-header {
	flex: 1;
	min-width: 0;
}

.section-title {
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 48rpx;
	font-weight: 600;
	color: #1D1D1F;
	margin-bottom: 24rpx;
	display: block;
}

.filter-buttons {
	display: flex;
	flex-wrap: wrap;
	gap: 20rpx;
}

.filter-group {
	position: relative;
}

.filter-btn {
	background: #FFF;
	border: 2rpx solid #8E8070;
	border-radius: 16rpx;
	padding: 16rpx 28rpx;
	font-weight: 600;
	color: #1D1D1F;
	display: inline-flex;
	align-items: center;
	gap: 10rpx;
	box-shadow: 2rpx 2rpx 0 rgba(142, 128, 112, 0.2);
	transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, transform 0.2s;
	cursor: pointer;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
	font-size: 26rpx;
}

.filter-btn:active {
	transform: translateY(2rpx);
	box-shadow: none;
}

.filter-btn.open,
.filter-btn.has-value {
	background-color: #FFF9F1;
	border-color: #9D8B70;
	box-shadow: 2rpx 2rpx 0 rgba(157, 139, 112, 0.3);
}

.icon-arrow {
	width: 24rpx;
	height: 24rpx;
}

.dropdown-menu {
	position: absolute;
	top: 100%;
	left: 0;
	margin-top: 16rpx;
	background: #FFF;
	border-radius: 20rpx;
	padding: 24rpx;
	box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.12);
	z-index: 100;
	width: 320rpx;
	border: 2rpx solid #E8E4DC;
	animation: dropdown-in 0.25s ease;
}

@keyframes dropdown-in {
	from {
		opacity: 0;
		transform: translateY(-12rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.dropdown-title {
	font-size: 24rpx;
	color: #999;
	margin-bottom: 16rpx;
	display: block;
}

.radio-item {
	display: flex;
	align-items: center;
	margin-bottom: 16rpx;
	font-size: 26rpx;
	color: #1D1D1F;
	cursor: pointer;
}

.radio-item radio {
	margin-right: 12rpx;
}

.option-list {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	max-height: 320rpx;
	overflow-y: auto;
	margin-bottom: 8rpx;
}

.option-item {
	padding: 16rpx 20rpx;
	font-size: 26rpx;
	color: #1D1D1F;
	border-radius: 12rpx;
	cursor: pointer;
	transition: background 0.2s;
}

.option-item:hover,
.option-item.active {
	background-color: #FFF9F1;
}

.option-item.active {
	font-weight: 600;
}

.option-list.favourite-levels .option-item.option-hearts {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16rpx;
}

.option-hearts .hearts-label {
	flex-shrink: 0;
}

.option-hearts .hearts-inline {
	display: flex;
	align-items: center;
	gap: 6rpx;
}

.option-hearts .heart-small {
	width: 28rpx;
	height: 28rpx;
}

.dropdown-actions {
	display: flex;
	justify-content: space-between;
	margin-top: 24rpx;
	gap: 20rpx;
}

.apply-btn,
.reset-btn {
	padding: 16rpx 32rpx;
	font-size: 26rpx;
	border-radius: 12rpx;
	cursor: pointer;
	transition: opacity 0.2s;
}

.apply-btn {
	background: #9D8B70;
	color: #FFF;
	font-weight: 600;
}

.reset-btn {
	background: transparent;
	color: #1D1D1F;
}

.upload-widget {
	width: 520rpx;
	flex-shrink: 0;
	min-width: 320rpx;
}

.upload-dashed {
	border: 4rpx dashed #D1D1D1;
	border-radius: 24rpx;
	padding: 40rpx;
	background: #FFF;
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	cursor: pointer;
	transition: background 0.25s, border-color 0.25s;
}

.upload-dashed:active {
	background: #FDFBF7;
	border-color: #9D8B70;
}

.upload-dashed.dragging {
	border-color: #007AFF;
	background-color: #F0F8FF;
}

.icon-upload {
	width: 80rpx;
	height: 80rpx;
	margin-bottom: 16rpx;
}

.upload-text {
	font-size: 26rpx;
	color: #1D1D1F;
	margin-bottom: 8rpx;
	white-space: nowrap;
}

.upload-text .blue {
	color: #007AFF;
	font-weight: 600;
}

.upload-hint {
	font-size: 22rpx;
	color: #999;
}

.divider {
	height: 2rpx;
	background: #E8E4DC;
	margin: 40rpx 0;
}

.clothes-grid {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 36rpx;
}

.cloth-card {
	background: transparent;
	cursor: pointer;
	transition: transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.cloth-card:active {
	transform: scale(0.98);
}

.img-wrapper {
	width: 100%;
	aspect-ratio: 4 / 5;
	background: #F5F0E6;
	border-radius: 16rpx;
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
}

.cloth-img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.model-card {
	background: transparent;
	cursor: pointer;
	transition: transform 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
}

.model-card:active {
	transform: scale(0.98);
}

.model-img-wrap {
	position: relative;
	width: 100%;
	aspect-ratio: 4 / 5;
	background: #F5F0E6;
	border-radius: 16rpx;
	overflow: hidden;
}

.model-img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.model-card.is-default .model-img-wrap {
	border: 3rpx solid #9D8B70;
	box-shadow: 0 4rpx 16rpx rgba(157, 139, 112, 0.25);
}

.model-default-badge {
	position: absolute;
	top: 12rpx;
	left: 12rpx;
	padding: 6rpx 14rpx;
	font-size: 22rpx;
	font-weight: 600;
	color: #FFF;
	background: #9D8B70;
	border-radius: 8rpx;
	letter-spacing: 0.5rpx;
}

.view-switch-inner {
	width: 100%;
}

.view-switch-enter-active,
.view-switch-leave-active {
	transition: opacity 0.28s ease, transform 0.28s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.view-switch-leave-to {
	opacity: 0;
	transform: translateX(-16rpx);
}
.view-switch-enter-from {
	opacity: 0;
	transform: translateX(16rpx);
}
.view-switch-enter-to,
.view-switch-leave-from {
	opacity: 1;
	transform: translateX(0);
}

.page-fade-enter-active,
.page-fade-leave-active {
	transition: opacity 0.35s ease, transform 0.35s cubic-bezier(0.25, 0.1, 0.25, 1);
}
.page-fade-leave-to {
	opacity: 0;
	transform: translateX(-24rpx);
}
.page-fade-enter-from {
	opacity: 0;
	transform: translateX(24rpx);
}
.page-fade-enter-to,
.page-fade-leave-from {
	opacity: 1;
	transform: translateX(0);
}

.pagination {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 32rpx;
	margin-top: 56rpx;
}

.page-btn {
	padding: 16rpx 28rpx;
	font-size: 28rpx;
	color: #1D1D1F;
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-weight: 600;
	background: #F5F0E6;
	border: 2rpx solid #9D8B70;
	border-radius: 12rpx;
	cursor: pointer;
	transition: background 0.25s ease, color 0.25s ease, opacity 0.25s ease, transform 0.2s ease;
}
.page-btn:not(.disabled):active {
	opacity: 0.92;
	transform: scale(0.97);
}

.page-btn:active {
	opacity: 0.9;
}

.page-btn.disabled {
	color: #AAA;
	border-color: #D1D1D1;
	background: #F5F5F5;
	cursor: not-allowed;
	opacity: 0.7;
}

.pagination-dots {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 20rpx;
}

.dot {
	width: 16rpx;
	height: 16rpx;
	border-radius: 50%;
	border: 2rpx solid #1D1D1F;
	background: transparent;
	cursor: pointer;
	transition: background 0.2s;
}

.dot.active {
	background: #1D1D1F;
}

@media (max-width: 900px) {
	.clothes-grid {
		grid-template-columns: repeat(2, 1fr);
	}
	.filter-section {
		flex-direction: column;
	}
	.upload-widget {
		width: 100%;
	}
}
</style>
