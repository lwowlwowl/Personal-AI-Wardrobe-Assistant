<template>
	<view class="wardrobe-root">
	<scroll-view class="wardrobe-container" scroll-y :show-scrollbar="false">
		<view class="wardrobe-inner">
			<!-- 添加上传状态提示 -->
			<view v-if="uploadLoading" class="upload-loading">
				<text>Uploading & tagging...</text>
				<view class="loading-spinner"></view>
			</view>
			
			<view v-if="uploadError" class="upload-error">
				<text>{{ uploadError }}</text>
				<text class="close-error" @click="uploadError = ''">×</text>
			</view>
			<!-- Control panel: primary controls (row 1) + filters (row 2) + upload card spanning two rows -->
			<view class="control-panel">
				<!-- Row 1: toggle + search -->
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
							:key="'cloth-search-' + clearKey"
							class="search-input" 
							type="text" 
							placeholder="Search your wardrobe..." 
							placeholder-class="search-placeholder"
							v-model="searchQuery"
						/>
						<input 
							v-else
							:key="'model-search-' + clearKey"
							class="search-input" 
							type="text" 
							placeholder="Search model gallery..." 
							placeholder-class="search-placeholder"
							v-model="modelSearchQuery"
						/>
					</view>
				</view>

				<!-- Row 2: Filter label + chips -->
				<view class="filter-header">
					<text class="section-title">Filter</text>
					<view class="filter-buttons">
						<view class="filter-group">
							<view  
								class="filter-btn filter-chip"
								:class="{ open: activeFilter === 'favourite', 'has-value': appliedFavouriteLevels.length > 0 }"
								@click="toggleFilter('favourite')"
							>
								<text>{{ favouriteLabel }}</text>
								<image 
									:src="activeFilter === 'favourite' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" 
									mode="aspectFit" 
									class="icon-arrow"
								></image>
							</view>
							<transition name="filter-panel">
								<view v-if="activeFilter === 'favourite'" class="filter-floating-panel">
									<text class="panel-title">Favourite</text>
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
								<view class="panel-actions">
									<view class="apply-btn" @click="applyFavourite">Apply</view>
									<view class="reset-btn" @click="resetFavourite">Reset</view>
								</view>
								</view>
							</transition>
						</view>
						<view class="filter-group">
							<view 
								class="filter-btn filter-chip" 
								:class="{ open: activeFilter === 'date', 'has-value': appliedDate != null }"
								@click="toggleFilter('date')"
							>
								<text>Date</text>
								<image :src="activeFilter === 'date' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="icon-arrow"></image>
							</view>
							<transition name="filter-panel">
								<view v-if="activeFilter === 'date'" class="filter-floating-panel">
									<text class="panel-title">Sort by Date</text>
								<radio-group @change="onDateChange">
									<label class="radio-item">
										<radio value="asc" :checked="dateSortOrder === 'asc'" color="#5a9a2e" /> Ascending
									</label>
									<label class="radio-item">
										<radio value="desc" :checked="dateSortOrder === 'desc'" color="#5a9a2e" /> Descending
									</label>
								</radio-group>
								<view class="panel-actions">
									<view class="apply-btn" @click="applyDate">Apply</view>
									<view class="reset-btn" @click="resetDate">Reset</view>
								</view>
								</view>
							</transition>
						</view>
						<view v-if="viewMode === 'Cloth'" class="filter-group">
							<view 
								class="filter-btn filter-chip" 
								:class="{ open: activeFilter === 'type', 'has-value': appliedTypes.length > 0 }"
								@click="toggleFilter('type')"
							>
								<text>{{ typeLabel }}</text>
								<image :src="activeFilter === 'type' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="icon-arrow"></image>
							</view>
							<transition name="filter-panel">
								<view v-if="activeFilter === 'type'" class="filter-floating-panel">
									<text class="panel-title">Clothing Type</text>
								<view class="option-list">
									<view 
										v-for="opt in typeOptions" 
										:key="opt.value" 
										class="option-item" 
										:class="{ active: selectedTypes.includes(opt.value) }"
										@click="toggleType(opt.value)"
									>{{ opt.label }}</view>
								</view>
								<view class="panel-actions">
									<view class="apply-btn" @click="applyType">Apply</view>
									<view class="reset-btn" @click="resetType">Reset</view>
								</view>
								</view>
							</transition>
						</view>
						<view v-if="viewMode === 'Cloth'" class="filter-group">
							<view 
								class="filter-btn filter-chip" 
								:class="{ open: activeFilter === 'color', 'has-value': appliedColors.length > 0 }"
								@click="toggleFilter('color')"
							>
								<text>{{ colorLabel }}</text>
								<image :src="activeFilter === 'color' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="icon-arrow"></image>
							</view>
							<transition name="filter-panel">
								<view v-if="activeFilter === 'color'" class="filter-floating-panel">
									<text class="panel-title">Color</text>
								<view class="option-list">
									<view 
										v-for="opt in colorOptions" 
										:key="opt.value" 
										class="option-item" 
										:class="{ active: selectedColors.includes(opt.value) }"
										@click="toggleColor(opt.value)"
									>{{ opt.label }}</view>
								</view>
								<view class="panel-actions">
									<view class="apply-btn" @click="applyColor">Apply</view>
									<view class="reset-btn" @click="resetColor">Reset</view>
								</view>
								</view>
							</transition>
						</view>
						<view v-if="viewMode === 'Cloth'" class="filter-group">
							<view 
								class="filter-btn filter-chip" 
								:class="{ open: activeFilter === 'season', 'has-value': appliedSeasons.length > 0 }"
								@click="toggleFilter('season')"
							>
								<text>{{ seasonLabel }}</text>
								<image :src="activeFilter === 'season' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="icon-arrow"></image>
							</view>
							<transition name="filter-panel">
								<view v-if="activeFilter === 'season'" class="filter-floating-panel">
									<text class="panel-title">Season</text>
								<view class="option-list">
									<view 
										v-for="opt in seasonOptions" 
										:key="opt.value" 
										class="option-item" 
										:class="{ active: selectedSeasons.includes(opt.value) }"
										@click="toggleSeason(opt.value)"
									>{{ opt.label }}</view>
								</view>
								<view class="panel-actions">
									<view class="apply-btn" @click="applySeason">Apply</view>
									<view class="reset-btn" @click="resetSeason">Reset</view>
								</view>
								</view>
							</transition>
						</view>
					</view>
				</view>

				<!-- Upload card: spans both rows, aligned to the right -->
				<view class="upload-widget" @click="viewMode === 'Cloth' ? testSimpleUpload() : openModelUpload()">
					<div
						class="upload-hero-card"
						:class="{ dragging: uploadDragging }"
						@drop.prevent.stop="handleUploadDrop"
						@dragover.prevent.stop="handleUploadDragOver"
						@dragleave.prevent.stop="handleUploadDragLeave"
						@dragenter.prevent.stop
					>
						<view class="upload-hero-inner">
							<image src="/static/icons/icon-image-upload.svg" mode="aspectFit" class="icon-upload"></image>
							<text class="upload-title">Add item</text>
							<text class="upload-subtitle">Drop photo here</text>
							<text class="upload-hint">Auto-tagging enabled</text>
							<text class="upload-meta">Color · Category · Season</text>
						</view>
					</div>
				</view>
			</view>
			<view class="divider"></view>

			<transition name="view-switch" mode="out-in">
				<view :key="viewMode" class="view-switch-inner">
					<!-- Cloth Grid -->
					<template v-if="viewMode === 'Cloth'">
						<view v-if="isInitialLoadingCloth" class="clothes-grid">
							<view v-for="n in 8" :key="'cloth-skel-' + n" class="cloth-card">
								<view class="img-wrapper is-loading"></view>
								<view class="card-caption">
									<view class="skeleton-text"></view>
								</view>
							</view>
						</view>
						<view v-else-if="clothes.length === 0" class="empty-state-wrap">
							<view class="empty-state-panel">
								<view class="empty-state-bg-pattern" aria-hidden="true">👗 🧥 👕 👖</view>
								<view class="empty-state-illustration">
									<view class="empty-state-icon-texture" aria-hidden="true">👕 👗 👖</view>
									<image src="/static/icons/icon-wardrobe.svg" mode="aspectFit" class="empty-state-icon" />
								</view>
								<text class="empty-state-headline">Your wardrobe is waiting</text>
								<text class="empty-state-subtitle">Add your first clothing item to begin your styling journey.</text>
								<view class="empty-state-cta" @click="testSimpleUpload">Upload first item</view>
							</view>
						</view>
						<transition v-else name="state-fade" mode="out-in">
							<view v-if="displayList.length === 0" key="noresults" class="no-results-wrap">
								<view class="no-results-content">
									<view class="no-results-visual">
										<text class="no-results-mark">✨</text>
									</view>
									<text class="no-results-title">Hmm, not in this collection.</text>
									<text class="no-results-desc">Let's step back and see what else we have.</text>
									<view class="no-results-action" @click="clearAllFilters">
										<text class="action-text">Show all my items</text>
										<view class="action-underline"></view>
									</view>
								</view>
							</view>
							<view v-else key="datalist" class="list-container">
								<transition name="page-fade" mode="out-in">
									<view class="clothes-grid" :key="`grid-${currentPage}-${displayList.length}`">
										<view 
											v-for="(item, index) in paginatedList" 
											:key="item.id" 
											class="cloth-card stagger-enter"
											:style="{ 'animation-delay': `${index * 0.05}s` }"
											@click="openDetail(item)"
										>
									<view class="img-wrapper" :class="{ 'is-loaded': item.imageLoaded }">
										<!-- 方式1: 使用原生image -->
										  <image 
										    :src="item.image" 
										    mode="aspectFill" 
										    class="cloth-img"
										    @load="handleImageLoad($event, item)"
										    @error="handleImageError($event, item)"
										  />
										  
										  <!-- 方式2: 使用web-view作为备选 -->
										  <view v-if="item.imageError" class="image-fallback">
										    <text class="fallback-text">{{ item.name }}</text>
										  </view>

										  <!-- 卡片 Hover 快捷操作浮层 -->
										  <view class="card-overlay">
											  <view class="card-overlay-top">
												  <text class="card-tag">Cloth</text>
											  </view>
											  <view class="card-overlay-bottom">
												  <view class="quick-actions">
													  <view class="quick-btn primary" @click.stop="quickTryOn(item)">
														  <text>Virtual Try-On</text>
													  </view>
													  <view class="quick-btn danger" @click.stop="quickDelete(item)">
														  <text>Delete</text>
													  </view>
												  </view>
											  </view>
										  </view>
									</view>
									<!-- 底部名称：在非 hover 状态也给一点信息感 -->
									<view class="card-caption">
										<text class="card-caption-name" :title="item.name">
											{{ item.name || 'Unnamed item' }}
										</text>
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
							</view>
						</transition>
					</template>

					<!-- Model Grid -->
					<template v-else>
						<transition name="state-fade" mode="out-in">
							<view v-if="isInitialLoadingModel" key="loading-model" class="clothes-grid model-grid">
								<view v-for="n in 8" :key="'model-skel-' + n" class="model-card">
									<view class="model-img-wrap is-loading"></view>
									<view class="card-caption">
										<view class="skeleton-text"></view>
									</view>
								</view>
							</view>

							<view v-else-if="models.length === 0" key="empty-model" class="empty-state-wrap">
								<view class="empty-state-panel">
									<view class="empty-state-bg-pattern" aria-hidden="true">📷 ✨ 📸 🖼️</view>
									<view class="empty-state-illustration">
										<view class="empty-state-icon-texture" aria-hidden="true">📷 🖼️</view>
										<image src="/static/icons/icon-image-upload.svg" mode="aspectFit" class="empty-state-icon" style="filter: grayscale(100%) opacity(0.8);" />
									</view>
									<text class="empty-state-headline">No models yet</text>
									<text class="empty-state-subtitle">Upload your first model photo to begin your styling journey.</text>
									<view class="empty-state-cta" @click="openModelUpload">Add model photo</view>
								</view>
							</view>

							<view v-else-if="modelDisplayList.length === 0" key="noresults-model" class="no-results-wrap">
								<view class="no-results-content">
									<view class="no-results-visual">
										<text class="no-results-mark">✨</text>
									</view>
									<text class="no-results-title">Whoops, no match.</text>
									<text class="no-results-desc">I couldn't find any model photos matching that name. Let's go back to the full gallery.</text>
									<view class="no-results-action" @click="clearAllFilters">
										<text class="action-text">Show all models</text>
										<view class="action-underline"></view>
									</view>
								</view>
							</view>

							<view v-else key="datalist-model" class="list-container">
								<transition name="page-fade" mode="out-in">
									<view class="clothes-grid model-grid" :key="`grid-model-${modelCurrentPage}-${modelDisplayList.length}`">
										<view 
											v-for="(item, index) in modelPaginatedList" 
											:key="item.id" 
											class="model-card stagger-enter"
											:class="{ 'is-default': item.id === defaultModelId }"
											:style="{ 'animation-delay': `${index * 0.05}s` }"
											@click="openModelDetail(item)"
										>
											<view class="model-img-wrap">
												<image :src="item.image" mode="aspectFill" class="model-img" />
												<view v-if="item.id === defaultModelId" class="model-default-badge">Default</view>
												<view class="card-overlay">
													<view class="card-overlay-top">
														<text class="card-tag">Model</text>
													</view>
													<view class="card-overlay-bottom">
														<view class="quick-actions">
															<view class="quick-btn primary" @click.stop="handleSetDefaultModel(item.id)">
																<text>{{ item.id === defaultModelId ? 'Default' : 'Set default' }}</text>
															</view>
															<view class="quick-btn danger" @click.stop="handleModelDelete(item.id)">
																<text>Delete</text>
															</view>
														</view>
													</view>
												</view>
											</view>
											<view class="card-caption">
												<text class="card-caption-name" :title="item.photo_name || item.posture">
													{{ item.photo_name || item.posture || 'Unnamed' }}
												</text>
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
							</view>
						</transition>
					</template>
				</view>
			</transition>
		</view>
	</scroll-view>

		<ModelUploadModal
			:visible="showModelUploadModal"
			@update:visible="showModelUploadModal = $event"
			@confirm="handleModelUploadConfirm"
		/>
		<ClothUploadModal
			:visible="showCategoryModal"
			:item-id="createdItemIdForEdit"
			:initial-form-data="uploadFormData"
			:type-options="typeOptions"
			:season-options="seasonOptions"
			@update:visible="onClothUploadVisibleChange"
			@confirm="handleClothUploadConfirm"
		/>
		<ClothDetailModal
			v-model:visible="showModal"
			:item="selectedItem"
			:all-clothes="clothes"
			@try-on="handleVirtualTryOn"
			@delete="handleDeleteItem"
			@update="handleItemUpdate"
			@open-item="handleOpenSimilarItem"
		/>
		<ModelDetailModal
			v-model:visible="showModelModal"
			:item="selectedModel"
			:default-model-id="defaultModelId"
			@delete="handleModelDelete"
			@update="handleModelUpdate"
			@set-default="handleSetDefaultModel"
		/>
		<DeleteConfirmModal
			:visible="showDeleteModal"
			:title="deleteModalTitle"
			:content="deleteModalContent"
			@confirm="doDeleteConfirm"
			@cancel="handleDeleteCancel"
		/>
	</view>
</template>

<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import ClothDetailModal from './cloth-modal/ClothDetailModal.vue'
import ModelDetailModal from './model-modal/ModelDetailModal.vue'
import ModelUploadModal from './model-modal/ModelUploadModal.vue'
import ClothUploadModal from './cloth-modal/ClothUploadModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { TYPE_OPTIONS, SEASON_OPTIONS } from '@/utils/wardrobeEnums.js'
import { authVerify } from '@/api/userApi.js'
import {
  getClothingList,
  uploadClothing,
  deleteClothing,
  updateClothing,
  getModelPhotos,
  uploadModelPhoto,
  deleteModelPhoto,
  setModelPhotoPrimary,
  updateModelPhoto,
  resolveWardrobeImageUrl,
  applyClothingImageUrlFixes,
  isClothingDeleteNotFoundResponse
} from '@/api/wardrobe.js'

const emit = defineEmits(['switch-to-tryon'])

// 注入父组件提供的 auth 状态同步函数，用于同步侧边栏显示
const updateAuthState = inject('updateAuthState', null)

// ============ 用户认证状态 ============
// 从本地存储获取token和用户信息
const userToken = ref(uni.getStorageSync('auth_token') || '')
const userInfo = ref(uni.getStorageSync('user_info') || null)
const isLoggedIn = ref(!!userToken.value)
const isCheckingAuth = ref(false) // 用于token验证
// 首次加载状态：数据回来前显示骨架屏，避免闪现空状态
const isInitialLoadingCloth = ref(true)
const isInitialLoadingModel = ref(true)

// ============ 上传相关状态 ============
const uploadLoading = ref(false)
const uploadError = ref('')
const showCategoryModal = ref(false)
/** 上传并打标成功后要编辑的衣物 id，确认时走 update 而非再次上传 */
const createdItemIdForEdit = ref(null)

function createEmptyClothingUploadForm() {
  return {
    name: '',
    category: '', // 后端 9 个主分类之一
    subcategory: '', // 用户可自由输入的子分类
    color: '',
    season: '',
    brand: '',
    tags: '',
    description: '',
    price: '',
    purchase_date: ''
  }
}

const uploadFormData = ref(createEmptyClothingUploadForm())

/** Successful upload+tagging: fill form and open category modal */
function openClothTaggingModalFromUploadData(data) {
  const al = data.auto_label
  const raw =
    al && typeof al === 'object' && al._raw && typeof al._raw === 'object'
      ? al._raw
      : al || {}
  const tagsFromApi = data.tags
  const tagsStr =
    Array.isArray(tagsFromApi) && tagsFromApi.length
      ? tagsFromApi.map(String).filter(Boolean).join(', ')
      : [raw.subcategory, raw.style, raw.occasion, raw.pattern].filter(Boolean).map(String).join(', ')
  uploadFormData.value = {
    name: data.name || raw.subcategory || raw.category || 'Unnamed',
    category: raw.category || data.category || '',
    subcategory: raw.subcategory || '',
    color: typeof raw.color === 'string' ? raw.color : (raw.color || ''),
    season: Array.isArray(raw.season) ? (raw.season[0] || '') : (raw.season || ''),
    brand: raw.brand || '',
    tags: tagsStr,
    description: raw.description || '',
    price: uploadFormData.value.price || '',
    purchase_date: uploadFormData.value.purchase_date || ''
  }
  createdItemIdForEdit.value = data.id
  showCategoryModal.value = true
}

// ============ 认证相关方法 ============

/**
 * 检查认证状态
 */
async function checkAuthStatus() {
  if (!userToken.value) {
    isLoggedIn.value = false
    isInitialLoadingCloth.value = false
    isInitialLoadingModel.value = false
    updateAuthState?.(false)
    return false
  }

  isCheckingAuth.value = true
  
  try {
    const response = await authVerify(userToken.value)

    if (response.statusCode === 200 && response.data.valid) {
      // token有效
      isLoggedIn.value = true
      userInfo.value = {
        id: response.data.user_id,
        username: response.data.username,
        email: response.data.email
      }
      uni.setStorageSync('user_info', userInfo.value)
      updateAuthState?.(true, userInfo.value.username)
      return true
    } else {
      // token无效，清除本地存储
      clearAuthData()
      updateAuthState?.(false)
      return false
    }
  } catch (error) {
    console.error('authVerify failed:', error)
    // 网络错误时保持现有状态，但标记为检查中
    return false
  } finally {
    isCheckingAuth.value = false
  }
}

/**
 * 清除认证数据
 */
function clearAuthData() {
  uni.removeStorageSync('auth_token')
  uni.removeStorageSync('user_info')
  userToken.value = ''
  userInfo.value = null
  isLoggedIn.value = false
  isInitialLoadingCloth.value = false
  isInitialLoadingModel.value = false
  updateAuthState?.(false)
}

const MAX_LOCAL_IMAGE_BYTES = 10 * 1024 * 1024

/** Album/camera: require login + max file size; returns temp path or null (toast already shown). */
async function pickLocalImageUnderMaxSize() {
  if (!isLoggedIn.value) {
    uni.showToast({ title: 'Please log in first', icon: 'none' })
    return null
  }
  try {
    const chooseResult = await uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera']
    })
    if (!chooseResult.tempFilePaths || chooseResult.tempFilePaths.length === 0) {
      uni.showToast({ title: 'No image selected', icon: 'none' })
      return null
    }
    const tempFilePath = chooseResult.tempFilePaths[0]
    const fileInfo = await uni.getFileInfo({ filePath: tempFilePath })
    if (fileInfo.size > MAX_LOCAL_IMAGE_BYTES) {
      uni.showToast({ title: 'File size must be under 10MB', icon: 'none' })
      return null
    }
    return tempFilePath
  } catch (error) {
    console.error('pickLocalImageUnderMaxSize:', error)
    uni.showToast({ title: 'Failed to select image', icon: 'none' })
    return null
  }
}

const testSimpleUpload = async () => {
  console.log('clothing upload start...')
  const tempFilePath = await pickLocalImageUnderMaxSize()
  if (!tempFilePath) return

  console.log('logged in, token:', userToken.value.substring(0, 20) + '...')
  console.log('temp file path:', tempFilePath)

  uploadLoading.value = true
  createdItemIdForEdit.value = null
  uni.showLoading({ title: 'Uploading & tagging...', mask: true })
  try {
    const result = await uploadClothing({
      token: userToken.value,
      filePath: tempFilePath,
      formData: createEmptyClothingUploadForm()
    })
    if (result.statusCode !== 200 || !result.data?.success) {
      throw new Error(result.data?.message || result.data?.detail || 'Upload failed')
    }
    const data = result.data?.data || result.data
    openClothTaggingModalFromUploadData(data)
  } catch (err) {
    const msg = err.message || err.errMsg || 'Upload failed'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    uploadLoading.value = false
    uni.hideLoading()
  }
}

function onClothUploadVisibleChange(v) {
  showCategoryModal.value = v
  if (!v) closeCategoryModal()
}

async function handleClothUploadConfirm({ itemId, payload }) {
  try {
    uni.showLoading({ title: 'Saving...', mask: true })
    const result = await updateClothing(userToken.value, itemId, payload)
    uni.hideLoading()
    if (result.statusCode === 200 && result.data?.success !== false) {
      uni.showToast({ title: 'Saved', icon: 'success' })
      createdItemIdForEdit.value = null
      loadClothingData({ showSkeleton: false })
    } else {
      uni.showToast({ title: result.data?.message || 'Save failed', icon: 'none' })
    }
  } catch (err) {
    uni.hideLoading()
    uni.showToast({ title: err.message || err.errMsg || 'Network error', icon: 'none' })
  }
}

// 重置上传表单
const resetUploadForm = () => {
  uploadFormData.value = createEmptyClothingUploadForm()
}

// 关闭模态框
const closeCategoryModal = () => {
  showCategoryModal.value = false
  createdItemIdForEdit.value = null
  resetUploadForm()
}


// 加载衣物数据的方法
// showSkeleton: 是否显示骨架屏（初次进入为 true，上传/删除后刷新为 false）
const loadClothingData = async (options = {}) => {
  const { showSkeleton = true } = options
  try {
    if (!isLoggedIn.value) {
      isInitialLoadingCloth.value = false
      return
    }
    if (showSkeleton) isInitialLoadingCloth.value = true
    console.log('=== loadClothingData (with image URL fix) ===')
    
    const response = await getClothingList({
      token: userToken.value,
      page: 1,
      page_size: 100,
      order_by: 'created_at',
      order_desc: true
    })
    
    if (response.statusCode === 200 && response.data.success) {
      const items = response.data.data.items || []
      console.log(`Fetched ${items.length} clothing items`)
      
      // 第一步：构建初始数据
      const initialItems = items.map(item => {
        const imageUrl = resolveWardrobeImageUrl(item.image_url)
        
        // 后端 season 为数组 ["autumn","winter"]，前端筛选/详情用逗号分隔字符串，此处统一成字符串
        const seasonVal = item.season
        const seasonStr = Array.isArray(seasonVal) ? seasonVal.join(',') : (seasonVal || '')

        const tagsArr = (item.tags || []).map((t) => (typeof t === 'string' ? t : (t?.tag || t))).filter(Boolean)
        return {
          id: item.id,
          name: item.name || 'Unnamed item',
          type: item.category || '',
          subcategory: item.subcategory || '',
          date: item.created_at ? item.created_at.slice(0, 10) : item.date || '',
          color: item.color || '',
          season: seasonStr,
          tags: tagsArr,
          favourite: (() => {
            const v = item.is_favorite
            if (typeof v === 'number') return Math.min(3, Math.max(0, v))
            if (v === true) return 1
            return 0
          })(),
          image: imageUrl,
          _rawImageUrl: item.image_url,
          _source: 'api',
          _needsFix: item.image_url && item.image_url.startsWith('/') // 标记需要修复
        }
      })
      
      // 第二步：应用修复（如果需要）
      clothes.value = await applyClothingImageUrlFixes(initialItems)
      
      console.log(`Done: ${clothes.value.length} items in wardrobe`)
    }
    
  } catch (error) {
    console.error('loadClothingData failed:', error)
  } finally {
    isInitialLoadingCloth.value = false
  }
}

const handleDeleteItem = (id) => {
  deletePayload.value = { type: 'cloth', id }
  showDeleteModal.value = true
}

const doDeleteClothing = async (id) => {
  try {
    console.log('=== delete clothing ===', id)
    uni.showLoading({ title: 'Deleting...', mask: true })
    const response = await deleteClothing(userToken.value, id)
    uni.hideLoading()
    const notFound = isClothingDeleteNotFoundResponse(response, null)
    if (response.statusCode === 200 && response.data && response.data.success) {
      clothes.value = clothes.value.filter((c) => c.id !== id)
      uni.showToast({ title: 'Deleted', icon: 'success', duration: 2000 })
      if (selectedItem.value && selectedItem.value.id === id) {
        showModal.value = false
        selectedItem.value = {}
      }
      if (paginatedList.value.some(item => item.id === id)) {
        await loadClothingData({ showSkeleton: false })
      }
    } else if (notFound) {
      clothes.value = clothes.value.filter((c) => c.id !== id)
      if (selectedItem.value && selectedItem.value.id === id) {
        showModal.value = false
        selectedItem.value = {}
      }
      uni.showToast({ title: 'Removed from list', icon: 'none', duration: 2000 })
    } else {
      uni.showToast({
        title: response.data?.message || response.data?.detail || 'Delete failed',
        icon: 'none',
        duration: 3000
      })
    }
  } catch (error) {
    uni.hideLoading()
    console.error('delete clothing failed:', error)
    const isNotFound = isClothingDeleteNotFoundResponse(null, error)
    if (isNotFound) {
      clothes.value = clothes.value.filter((c) => c.id !== id)
      if (selectedItem.value && selectedItem.value.id === id) {
        showModal.value = false
        selectedItem.value = {}
      }
      uni.showToast({ title: 'Removed from list', icon: 'none', duration: 2000 })
    } else {
      uni.showToast({ title: 'Delete failed: network error', icon: 'none', duration: 3000 })
    }
  }
}

function doDeleteConfirm() {
  const { type, id } = deletePayload.value
  showDeleteModal.value = false
  deletePayload.value = { type: null, id: null }
  if (type === 'cloth' && id != null) doDeleteClothing(id)
  else if (type === 'model' && id != null) doDeleteModel(id)
}

function handleDeleteCancel() {
  showDeleteModal.value = false
  deletePayload.value = { type: null, id: null }
}

// ============ 模特照片相关状态 ============
const showModelUploadModal = ref(false)
const selectedModelImageFile = ref(null)

// 从后端加载的模特照片数据
const models = ref([])
const defaultModelId = ref(null)

// 当前选中的模特照片（用于编辑）
const selectedModel = ref({})
const showModelModal = ref(false)

// ============ 模特照片相关方法 ============

/**
 * 加载模特照片数据
 * showSkeleton: 是否显示骨架屏（初次/切换 Tab 为 true，上传/删除后刷新为 false）
 */
const loadModelPhotos = async (options = {}) => {
  const { showSkeleton = true } = options
  try {
    if (!isLoggedIn.value) {
      isInitialLoadingModel.value = false
      return
    }
    if (showSkeleton) isInitialLoadingModel.value = true
    console.log('=== loadModelPhotos ===')
    
    const response = await getModelPhotos({
      token: userToken.value,
      page: modelCurrentPage.value,
      page_size: PAGE_SIZE,
      order_by: 'created_at',
      order_desc: true,
      is_active: true
    })
    
    if (response.statusCode === 200 && response.data.success) {
      const photos = response.data.data.photos || []
      console.log(`Fetched ${photos.length} model photos`)
      
      // 转换数据格式
      models.value = photos.map(photo => {
        const imageUrl = resolveWardrobeImageUrl(photo.image_url)
        
        return {
          id: photo.id,
          posture: photo.photo_name, // 使用photo_name作为posture显示
          date: photo.created_at ? photo.created_at.slice(0, 10) : '',
          favourite: 0, // 模特照片没有收藏功能
          image: imageUrl,
          photo_name: photo.photo_name,
          description: photo.description,
          is_primary: photo.is_primary,
          is_active: photo.is_active,
          _rawImageUrl: photo.image_url,
          _source: 'api'
        }
      })
      
      // 仅当有明确设为「主要」的模特时设置 defaultModelId，否则不指定默认（避免新上传未勾选默认却被当成默认）
      const primaryModel = models.value.find(model => model.is_primary)
      defaultModelId.value = primaryModel ? primaryModel.id : null
      
      console.log(`Model photos loaded: ${models.value.length}, defaultId: ${defaultModelId.value}`)
      
    } else {
      console.error('loadModelPhotos failed:', response.data?.message)
    }
    
  } catch (error) {
    console.error('loadModelPhotos error:', error)
  } finally {
    isInitialLoadingModel.value = false
  }
}

/**
 * 打开模特照片上传模态框
 */
const openModelUpload = async () => {
  console.log('model photo upload start...')
  const tempFilePath = await pickLocalImageUnderMaxSize()
  if (!tempFilePath) return
  console.log('temp file path:', tempFilePath)
  selectedModelImageFile.value = tempFilePath
  showModelUploadModal.value = true
}

/**
 * 模特上传弹窗确认：执行上传
 */
const handleModelUploadConfirm = async (formData) => {
  if (!selectedModelImageFile.value) {
    uni.showToast({ title: 'No image selected', icon: 'none' })
    return
  }
  try {
    uni.showLoading({ title: 'Uploading...', mask: true })
    await performModelUpload(selectedModelImageFile.value, formData)
    uni.showToast({ title: 'Model photo uploaded', icon: 'success' })
    closeModelUploadModal()
    loadModelPhotos({ showSkeleton: false })
  } catch (error) {
    console.error('uploadModelPhoto failed:', error)
    uni.showToast({ title: 'Upload failed', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

/**
 * 执行模特照片上传
 */
const performModelUpload = async (filePath, formData) => {
  const result = await uploadModelPhoto({
    token: userToken.value,
    filePath,
    formData: {
      photo_name: formData.photo_name ?? '',
      description: formData.description ?? '',
      is_primary: formData.is_primary === true
    }
  })
  if (result.statusCode !== 200 || !result.data?.success) {
    throw new Error(result.data?.message || 'Upload failed')
  }
  return result
}

const closeModelUploadModal = () => {
  showModelUploadModal.value = false
  selectedModelImageFile.value = null
}

/**
 * 删除模特照片：仅打开自定义确认弹窗
 */
const handleModelDelete = (id) => {
  deletePayload.value = { type: 'model', id }
  showDeleteModal.value = true
}

const doDeleteModel = async (id) => {
  try {
    console.log('=== delete model photo ===', id)
    uni.showLoading({ title: 'Deleting...', mask: true })
    const response = await deleteModelPhoto(userToken.value, id, false)
    uni.hideLoading()
    if (response.statusCode === 200 && response.data.success) {
      const modelIndex = models.value.findIndex((m) => m.id === id)
      if (modelIndex !== -1) models.value[modelIndex].is_active = false
      uni.showToast({ title: 'Deleted', icon: 'success', duration: 2000 })
      if (selectedModel.value && selectedModel.value.id === id) {
        showModelModal.value = false
        selectedModel.value = {}
      }
      loadModelPhotos({ showSkeleton: false })
    } else {
      uni.showToast({
        title: response.data?.message || 'Delete failed',
        icon: 'none',
        duration: 3000
      })
    }
  } catch (error) {
    uni.hideLoading()
    console.error('delete model photo failed:', error)
    uni.showToast({ title: 'Delete failed: network error', icon: 'none', duration: 3000 })
  }
}

/**
 * 设置默认模特照片
 */
const handleSetDefaultModel = async (id) => {
  try {
    console.log('set default model photo:', id)
    
    // 显示加载提示
    uni.showLoading({
      title: 'Setting...',
      mask: true
    })
    
    const response = await setModelPhotoPrimary(userToken.value, id)
    
    uni.hideLoading()
    
    if (response.statusCode === 200 && response.data.success) {
      // 更新默认模特ID
      defaultModelId.value = id
      
      // 更新所有模特照片的is_primary状态
      models.value.forEach(model => {
        model.is_primary = (model.id === id)
      })
      
      uni.showToast({
        title: 'Set as default model photo',
        icon: 'success',
        duration: 2000
      })
      
    } else {
      const errorMsg = response.data?.message || 'Set failed'
      uni.showToast({
        title: errorMsg,
        icon: 'none',
        duration: 3000
      })
    }
    
  } catch (error) {
    uni.hideLoading()
    console.error('setModelPhotoPrimary failed:', error)
    uni.showToast({
      title: 'Set failed: network error',
      icon: 'none',
      duration: 3000
    })
  }
}

/**
 * 更新模特照片信息
 */
const handleModelUpdate = async ({ id, field, value }) => {
  try {
    console.log('update model photo:', { id, field, value })
    
    // 如果是is_primary字段，使用专门的API
    if (field === 'is_primary' && value === true) {
      await handleSetDefaultModel(id)
      return
    }
    
    // 显示加载提示
    uni.showLoading({
      title: 'Updating...',
      mask: true
    })
    
    // 构建更新数据
    const updateData = { [field]: value }
    
    const response = await updateModelPhoto(userToken.value, id, updateData)
    
    uni.hideLoading()
    
    if (response.statusCode === 200 && response.data.success) {
      // 更新前端数据
      const modelIndex = models.value.findIndex((m) => m.id === id)
      if (modelIndex !== -1) {
        models.value[modelIndex][field] = value
        selectedModel.value = { ...models.value[modelIndex] }
      }
      
      uni.showToast({
        title: 'Updated',
        icon: 'success',
        duration: 2000
      })
      
    } else {
      const errorMsg = response.data?.message || 'Update failed'
      uni.showToast({
        title: errorMsg,
        icon: 'none',
        duration: 3000
      })
    }
    
  } catch (error) {
    uni.hideLoading()
    console.error('updateModelPhoto failed:', error)
    uni.showToast({
      title: 'Update failed: network error',
      icon: 'none',
      duration: 3000
    })
  }
}

/**
 * 打开模特照片详情
 */
const openModelDetail = (item) => {
  selectedModel.value = { ...item }
  showModelModal.value = true
}

// ============ 页面加载时初始化 ============
onMounted(async () => {
  await checkAuthStatus()
  if (isLoggedIn.value) {
    await loadClothingData()
    await loadModelPhotos()
  } else {
    isInitialLoadingCloth.value = false
    isInitialLoadingModel.value = false
  }
})





const viewMode = ref('Cloth')
const searchQuery = ref('')
const modelSearchQuery = ref('')
const activeFilter = ref(null)
const showModal = ref(false)
const selectedItem = ref({})
const showDeleteModal = ref(false)
const deletePayload = ref({ type: null, id: null })
const deleteModalTitle = computed(() =>
	deletePayload.value.type === 'model' ? 'Delete model photo' : 'Delete item'
)
const deleteModalContent = computed(() =>
	deletePayload.value.type === 'model'
		? 'Are you sure you want to delete this model photo?\nThis action cannot be undone.'
		: 'Are you sure you want to delete this clothing item?\nThis action cannot be undone.'
)
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

// Color（多选，存 code）；选项由当前衣物列表的颜色动态推导
const selectedColors = ref([])
const appliedColors = ref([])

// Season（多选，存 code）
const seasonOptions = SEASON_OPTIONS
const selectedSeasons = ref([])
const appliedSeasons = ref([])
const seasonLabel = computed(() => {
	const count = appliedSeasons.value.length
	return count > 0 ? `Season (${count})` : 'Season'
})

// 多选筛选项的按钮文案：有选中时显示数量
const favouriteLabel = computed(() => {
	const count = appliedFavouriteLevels.value.length
	return count > 0 ? `Favourite (${count})` : 'Favourite'
})
const typeLabel = computed(() => {
	const count = appliedTypes.value.length
	return count > 0 ? `Clothing type (${count})` : 'Clothing type'
})
const colorLabel = computed(() => {
	const count = appliedColors.value.length
	return count > 0 ? `Color (${count})` : 'Color'
})

// 衣物列表：初始为空，登录后由 loadClothingData 从接口拉取
const clothes = ref([])

// 颜色筛选选项：根据当前衣物列表的颜色动态推导（去重 + 排序）
const colorOptions = computed(() => {
	const set = new Set()
	for (const c of clothes.value) {
		const str = (c.color || '')
		if (!str) continue
		str.split(/[,/]+/).map((s) => s.trim()).filter(Boolean).forEach((code) => set.add(code))
	}
	return Array.from(set).sort((a, b) => String(a).localeCompare(String(b))).map((code) => ({
		label: code,
		value: code
	}))
})


// 搜索：仅匹配名称，允许前缀匹配，不允许任意子串（swea/swe ✅ sweater，we ❌ sweater）
const nameMatchesSearch = (name, searchTerm) => {
	const nameWords = (name || '').toLowerCase().split(/\s+/).filter(Boolean)
	const searchWords = searchTerm.trim().toLowerCase().split(/\s+/).filter(Boolean)
	if (searchWords.length === 0) return true
	return searchWords.every((searchWord) =>
		nameWords.some((nameWord) => nameWord.startsWith(searchWord))
	)
}

const displayList = computed(() => {
	let list = [...clothes.value]
	if (searchQuery.value.trim()) {
		const q = searchQuery.value.trim()
		list = list.filter((c) => nameMatchesSearch(c.name, q))
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
  // 首先按主要照片排序
  const sortedModels = [...models.value]
    .filter(model => model.is_active !== false) // 排除已删除的
    .sort((a, b) => {
      // 主要照片排第一
      if (a.is_primary && !b.is_primary) return -1
      if (!a.is_primary && b.is_primary) return 1
      // 然后按创建时间降序
      return (b.date || '').localeCompare(a.date || '')
    })
  
  // 应用搜索过滤：仅匹配名称（photo_name），且搜索词须为完整单词
  const q = modelSearchQuery.value.trim()
  if (q) {
    return sortedModels.filter((m) => nameMatchesSearch(m.photo_name, q))
  }
  
  return sortedModels
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

watch(viewMode, (newMode) => {
	activeFilter.value = null
	if (newMode === 'Model' && isLoggedIn.value) loadModelPhotos()
	else if (newMode === 'Cloth' && isLoggedIn.value) loadClothingData()
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

/** 强制搜索框重挂载用（uni-app 下程序清空后 input 可能不更新） */
const clearKey = ref(0)

/** 一键清除所有筛选条件（含搜索框），用于「无搜索结果」时一键还原 */
const clearAllFilters = () => {
	activeFilter.value = null
	appliedFavouriteLevels.value = []
	selectedFavouriteLevels.value = []
	appliedDate.value = null
	dateSortOrder.value = 'desc'
	appliedTypes.value = []
	selectedTypes.value = []
	appliedColors.value = []
	selectedColors.value = []
	appliedSeasons.value = []
	selectedSeasons.value = []
	searchQuery.value = ''
	modelSearchQuery.value = ''
	currentPage.value = 1
	modelCurrentPage.value = 1
	clearKey.value++
}

const openDetail = (item) => {
	selectedItem.value = { ...item }
	showModal.value = true
}

/** 在详情弹窗内点击「相似标签」小图：切换到该衣物的详情（同一弹窗） */
const handleOpenSimilarItem = (item) => {
	if (!item?.id) return
	const fromList = clothes.value.find((c) => c.id === item.id)
	selectedItem.value = fromList ? { ...fromList } : { ...item }
	showModal.value = true
}

// 图片加载成功时清除错误标记并标记为已加载（用于 skeleton 过渡）
const handleImageLoad = (_event, item) => {
	if (!item?.id) return
	const idx = clothes.value.findIndex((c) => c.id === item.id)
	if (idx >= 0) {
		clothes.value[idx] = {
			...clothes.value[idx],
			imageError: false,
			imageLoaded: true
		}
	}
}

// 图片加载失败时标记错误并结束 skeleton
const handleImageError = (_event, item) => {
	if (!item?.id) return
	const idx = clothes.value.findIndex((c) => c.id === item.id)
	if (idx >= 0) {
		clothes.value[idx] = {
			...clothes.value[idx],
			imageError: true,
			imageLoaded: true
		}
	}
}

const handleVirtualTryOn = (item) => {
	showModal.value = false
	const defaultModel = defaultModelId.value ? models.value.find((m) => m.id === defaultModelId.value) : null
	const defaultModelImage = defaultModel?.image ?? null
	emit('switch-to-tryon', item, defaultModelImage)
}

// 卡片上的快捷操作：直接进入虚拟试穿
const quickTryOn = (item) => {
	if (!item) return
	handleVirtualTryOn(item)
}

// 卡片上的快捷操作：直接删除衣物
const quickDelete = (item) => {
	if (!item?.id) return
	handleDeleteItem(item.id)
}

// 衣物编辑：同步到后端并更新本地
const handleItemUpdate = async ({ id, field, value }) => {
	const idx = clothes.value.findIndex((c) => c.id === id)
	if (idx < 0) return
	const prev = { ...clothes.value[idx] }
	// 本地字段：category 对应列表的 type（筛选用），subcategory 对应 subcategory
	const localField = field === 'category' ? 'type' : field
	clothes.value[idx] = { ...prev, [localField]: value }
	selectedItem.value = { ...clothes.value[idx] }
	// 后端字段：category / subcategory 直传，favourite -> is_favorite（0-3 整数），season 需为 JSON 数组字符串
	const backendField = field === 'favourite' ? 'is_favorite' : field
	let backendValue = field === 'favourite' ? Math.min(3, Math.max(0, Number(value) || 0)) : value
	if (field === 'season') {
		const arr = (typeof value === 'string' ? value.split(',') : Array.isArray(value) ? value : []).map((s) => String(s).trim()).filter(Boolean)
		backendValue = JSON.stringify(arr)
	}
	try {
		const res = await updateClothing(userToken.value, id, { [backendField]: backendValue })
		if (res.statusCode !== 200 || !res.data?.success) {
			clothes.value[idx] = prev
			selectedItem.value = { ...prev }
			uni.showToast({ title: res.data?.message || 'Update failed', icon: 'none' })
		}
	} catch (err) {
		clothes.value[idx] = prev
		selectedItem.value = { ...prev }
		uni.showToast({ title: 'Network error, not synced', icon: 'none' })
	}
}

const uploadDragging = ref(false)

const handleUploadDragOver = (event) => {
	uploadDragging.value = true
	if (event?.dataTransfer) event.dataTransfer.dropEffect = 'copy'
}

const handleUploadDragLeave = () => {
	uploadDragging.value = false
}

const handleUploadDrop = async (event) => {
	uploadDragging.value = false
	if (event && event.preventDefault) event.preventDefault()
	if (event && event.stopPropagation) event.stopPropagation()
	const dataTransfer = event?.dataTransfer || event?.originalEvent?.dataTransfer
	const files = dataTransfer?.files
	if (!files || files.length === 0) return
	const file = files[0]
	if (!file.type || !file.type.startsWith('image/')) {
		uni.showToast({ title: 'Drop an image file', icon: 'none' })
		return
	}
	// 仅 Cloth 模式支持拖拽上传；且必须走后端打标，绝不往列表里塞假数据
	if (viewMode.value !== 'Cloth') {
		uni.showToast({ title: 'Switch to Cloth mode to drag & drop', icon: 'none' })
		return
	}
	if (!isLoggedIn.value) {
		uni.showToast({ title: 'Please log in first', icon: 'none' })
		return
	}
	if (file.size > 10 * 1024 * 1024) {
		uni.showToast({ title: 'File size must be under 10MB', icon: 'none' })
		return
	}
	uploadLoading.value = true
	createdItemIdForEdit.value = null
	uni.showLoading({ title: 'Uploading & tagging...', mask: true })
	let blobUrl = null
	try {
		let result = null
		try {
			result = await uploadClothing({
				token: userToken.value,
				file,
				formData: createEmptyClothingUploadForm()
			})
		} catch (e1) {
			// 若 fetch 失败（如 CORS），尝试用 blob URL 走 uni.uploadFile
			blobUrl = URL.createObjectURL(file)
			result = await uploadClothing({
				token: userToken.value,
				filePath: blobUrl,
				formData: createEmptyClothingUploadForm()
			})
		}
		if (!result || result.statusCode !== 200 || !result.data?.success) {
			throw new Error(result?.data?.message || result?.data?.detail || 'Upload failed')
		}
		const data = result.data?.data || result.data
		openClothTaggingModalFromUploadData(data)
	} catch (err) {
		const msg = err?.message || err?.errMsg || 'Upload failed'
		uni.showToast({ title: msg, icon: 'none' })
	} finally {
		if (blobUrl) URL.revokeObjectURL(blobUrl)
		uploadLoading.value = false
		uni.hideLoading()
	}
}

</script>

<style scoped>
.wardrobe-root {
	width: 100%;
	height: 100%;
	position: relative;
}

.wardrobe-container {
	width: 100%;
	height: 100%;
	min-height: 100%;
	background: radial-gradient(circle at 10% 10%, #F9F8F6, #F1EEE8);
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
	border-radius: 999rpx;
	padding: 18rpx 26rpx;
	display: flex;
	align-items: center;
	background: #ffffff;
	border: 2rpx solid #E6E2DC;
	gap: 16rpx;
	box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
	transition: all 0.25s ease;
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

.search-bar:focus-within {
	border-color: #8C7355;
	box-shadow: 0 0 0 4rpx rgba(140, 115, 85, 0.15);
}

.search-placeholder {
	color: #999;
	font-weight: 300;
	font-family: serif;
}

/* Two-row control panel: row 1 = primary controls, row 2 = filters; upload spans both rows */
.control-panel {
	display: grid;
	grid-template-columns: auto 1fr auto;
	grid-template-rows: auto auto;
	column-gap: 32rpx;
	row-gap: 24rpx;
	padding: 32rpx 32rpx 28rpx;
	margin-bottom: 32rpx;
	border-radius: 24rpx;
	background: rgba(255, 255, 255, 0.65);
	border: 2rpx solid rgba(0, 0, 0, 0.05);
	box-shadow:
		0 10px 30px rgba(0, 0, 0, 0.05),
		inset 0 1px 0 rgba(255, 255, 255, 0.6);
	backdrop-filter: blur(12px);
	-webkit-backdrop-filter: blur(12px);
	position: sticky;
	top: 24rpx;
	z-index: 20;
}

.control-panel .header {
	grid-column: 1 / span 2;
	grid-row: 1;
}

.filter-header {
	grid-column: 1 / span 2;
	grid-row: 2;
	min-width: 0;
	display: flex;
	align-items: center;
	gap: 18rpx;
}

.section-title {
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 48rpx;
	font-weight: 600;
	color: #1D1D1F;
	display: inline-flex;
	align-items: center;
	margin: 0rpx 20rpx;
	margin-right: 24rpx;
}

.section-title-icon {
	font-size: 34rpx;
	margin-right: 10rpx;
	font-weight: 500;
	color: #7B766F;
	letter-spacing: 0.04em;
}

.filter-buttons {
	display: flex;
	flex-wrap: nowrap;
	gap: 16rpx;
	padding-bottom: 4rpx;
	flex: 1;
	min-width: 0;
	overflow: visible;
}

.filter-group {
	position: relative;
}

.filter-btn {
	background: #F5F3F0;
	border-radius: 20rpx;
	padding: 14rpx 26rpx;
	font-weight: 600;
	color: #1D1D1F;
	display: inline-flex;
	align-items: center;
	gap: 10rpx;
	border: 2rpx solid #E8E4DC;
	box-shadow: none;
	transition: all 0.2s ease;
	cursor: pointer;
	font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
	font-size: 26rpx;
}

.filter-chip:hover {
	transform: translateY(-1rpx);
	background: #F8F5F1;
	box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}

.filter-chip:active {
	transform: scale(0.98);
}

.filter-chip.open,
.filter-chip.has-value {
	background: #8C7355;
	color: #FFFFFF;
	border-color: #8C7355;
	box-shadow: 0 10rpx 26rpx rgba(129, 112, 88, 0.45);
}

.filter-chip.open text,
.filter-chip.has-value text {
	color: #FFFFFF;
}

.icon-arrow {
	width: 24rpx;
	height: 24rpx;
}

/* Filter panel: overlay under chips (does not stretch control panel height) */
.filter-floating-panel {
	position: absolute;
	top: calc(100% + 12rpx);
	left: 0;
	background: rgba(255, 255, 255, 0.92);
	border-radius: 20rpx;
	padding: 24rpx 26rpx;
	border: 2rpx solid #E8E4DC;
	box-shadow:
		0 20px 40px rgba(0, 0, 0, 0.08),
		0 4px 10px rgba(0, 0, 0, 0.05);
	z-index: 2000;
	width: 320rpx;
	transform-origin: top left;
	backdrop-filter: blur(14rpx);
	-webkit-backdrop-filter: blur(14rpx);
}

.filter-panel-enter-active,
.filter-panel-leave-active {
	transition: all 0.22s ease;
}

.filter-panel-enter-from,
.filter-panel-leave-to {
	opacity: 0;
	transform: translateY(-6rpx) scale(0.97);
}

.filter-panel-enter-to,
.filter-panel-leave-from {
	opacity: 1;
	transform: translateY(0) scale(1);
}

.panel-title {
	display: block;
	font-size: 22rpx;
	font-weight: 600;
	color: #8a8376;
	letter-spacing: 0.5rpx;
	text-transform: uppercase;
	margin-bottom: 18rpx;
	padding-bottom: 12rpx;
	border-bottom: 1rpx solid #F0EBE3;
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

.filter-floating-panel .option-list {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
	max-height: 320rpx;
	overflow-y: auto;
	margin-bottom: 4rpx;
	scrollbar-width: none; /* Firefox: hide scrollbar thumb */
}

.filter-floating-panel .option-list::-webkit-scrollbar {
	width: 0;
	height: 0;
	display: none; /* Chrome / Edge / Safari: hide scrollbar thumb */
}

.filter-floating-panel .option-item {
	padding: 18rpx 22rpx;
	font-size: 26rpx;
	color: #1D1D1F;
	border-radius: 14rpx;
	cursor: pointer;
	transition: all 0.15s ease;
}

.option-item:hover,
.option-item.active {
	background-color: #F5F3F0;
	transform: translateX(3rpx);
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

.panel-actions {
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
	grid-column: 3;
	grid-row: 1 / span 2;
	align-self: stretch;
	width: 360rpx;
	min-width: 320rpx;
}

/* fashion dropzone */
.upload-hero-card {
	position: relative;
	height: 100%;
	border-radius: 24rpx;
	padding: 6rpx;
	border: 2rpx dashed #D9D3CA;
	background: rgba(255, 255, 255, 0.6);
	cursor: pointer;
	box-shadow: none;
	transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.upload-hero-card:hover {
	border-color: #8C7355;
	background: rgba(140, 115, 85, 0.05);
	transform: scale(1.02);
}

.upload-hero-card:active {
	transform: scale(0.99);
}

.upload-hero-card.dragging {
	border-color: #8C7355;
	background: rgba(140, 115, 85, 0.08);
	box-shadow: 0 10px 40px rgba(140, 115, 85, 0.15);
}

.upload-hero-inner {
	position: relative;
	border-radius: 18rpx;
	padding: 40rpx 36rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	/* 内层柔和实边 */
	border: 2rpx solid rgba(191, 169, 140, 0.22);
	/* 极淡径向渐变 + 线性渐变 */
	background: radial-gradient(circle at 50% 0%, rgba(191, 169, 140, 0.1), transparent 55%),
		linear-gradient(180deg, #FAF7F2, #F4EFE8);
	transition: background 0.2s ease, border-color 0.2s ease;
}

.upload-hero-card.dragging .upload-hero-inner {
	background: radial-gradient(circle at 50% 0%, rgba(191, 169, 140, 0.14), transparent 55%),
		linear-gradient(180deg, #F4EFE8, #EDE6DC);
}

.icon-upload {
	width: 100rpx;
	height: 100rpx;
	margin-bottom: 20rpx;
	transition: transform 0.2s ease;
}

.upload-hero-card:hover .icon-upload {
	transform: translateY(-4rpx);
}

.upload-title {
	font-size: 32rpx;
	color: #1D1D1F;
	font-weight: 600;
	margin-bottom: 8rpx;
	letter-spacing: 0.3rpx;
}

.upload-subtitle {
	font-size: 26rpx;
	color: #5f5a52;
	margin-bottom: 6rpx;
}

.upload-hint {
	font-size: 22rpx;
	color: #8a8376;
	margin-bottom: 4rpx;
}

.upload-meta {
	font-size: 20rpx;
	color: #a39e94;
	letter-spacing: 0.5rpx;
}

.divider {
	height: 1rpx;
	margin: 24rpx 0 32rpx;
	background: linear-gradient(90deg, transparent, #E8E4DC, transparent);
	border-bottom: 1rpx solid #E8E4DC;
}

.clothes-grid {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 36rpx;
}

.cloth-card {
	background: transparent;
	cursor: pointer;
	perspective: 1200px;
	transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.28s ease, opacity 0.28s ease;
}

.img-wrapper {
	position: relative;
	width: 100%;
	aspect-ratio: 4 / 5;
	transform-style: preserve-3d;
	/* studio 展示：电商拍摄感 */
	background: radial-gradient(circle at 50% 40%, #ffffff, #F3F1EC);
	box-shadow:
		inset 0 1rpx 0 rgba(255, 255, 255, 0.7),
		0 6rpx 16rpx rgba(0, 0, 0, 0.04);
	border-radius: 16rpx;
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.28s ease;
}

.img-wrapper:hover {
	transform: translateY(-4rpx) rotateY(4deg);
	box-shadow:
		inset 0 1rpx 0 rgba(255, 255, 255, 0.8),
		0 30px 60px rgba(0, 0, 0, 0.15);
}

.cloth-img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	transition: transform 0.3s ease;
}

.img-wrapper:hover .cloth-img {
	transform: scale(1.03);
}

/* skeleton shimmer for image container before load */
.img-wrapper::before {
	content: "";
	position: absolute;
	inset: 0;
	background: linear-gradient(120deg, #f5f1e6 0%, #f9f5ec 20%, #f5f1e6 40%, #f5f1e6 100%);
	background-size: 200% 100%;
	animation: cloth-skeleton-shimmer 1.6s ease-in-out infinite;
}

.img-wrapper.is-loaded::before {
	animation: none;
	opacity: 0;
	transition: opacity 0.3s ease-out;
}

@keyframes cloth-skeleton-shimmer {
	0% {
		background-position: 200% 0;
	}
	100% {
		background-position: -200% 0;
	}
}

/* 首次加载骨架屏：统一占位色 + 呼吸动画 */
.is-loading {
	background: #F5F0E6 !important;
	box-shadow: none !important;
}
.is-loading::before {
	content: "";
	position: absolute;
	inset: 0;
	background: linear-gradient(120deg, transparent 0%, rgba(255, 255, 255, 0.4) 20%, transparent 40%);
	background-size: 200% 100%;
	animation: cloth-skeleton-shimmer 1.5s infinite linear;
}
.skeleton-text {
	height: 28rpx;
	width: 60%;
	background: #E8E4DC;
	border-radius: 6rpx;
	margin-top: 12rpx;
	margin-left: 4rpx;
	position: relative;
	overflow: hidden;
}
.skeleton-text::before {
	content: "";
	position: absolute;
	inset: 0;
	background: linear-gradient(120deg, transparent 0%, rgba(255, 255, 255, 0.5) 20%, transparent 40%);
	background-size: 200% 100%;
	animation: cloth-skeleton-shimmer 1.5s infinite linear;
}

/* 卡片 Hover 浮层：快捷操作 + 名称 */
.card-overlay {
	position: absolute;
	inset: 0;
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	padding: 20rpx 22rpx;
	background: linear-gradient(to bottom, rgba(0, 0, 0, 0.1), rgba(0, 0, 0, 0.45));
	opacity: 0;
	pointer-events: none;
	transition: opacity 0.22s ease;
}

.img-wrapper:hover .card-overlay {
	opacity: 1;
	pointer-events: auto;
}

.card-overlay-top {
	display: flex;
	justify-content: flex-start;
}

.card-tag {
	padding: 6rpx 16rpx;
	border-radius: 999rpx;
	background: rgba(253, 251, 247, 0.85);
	font-size: 22rpx;
	color: #7A6A55;
}

.card-overlay-bottom {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
}

.card-name {
	font-size: 28rpx;
	color: #FFF;
	font-weight: 600;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.quick-actions {
	display: flex;
	justify-content: flex-end;
	gap: 12rpx;
}

.quick-btn {
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	font-size: 22rpx;
	font-weight: 500;
	background: rgba(253, 251, 247, 0.9);
	color: #3c3c3e;
	transition: background 0.18s ease, transform 0.18s ease, opacity 0.18s ease;
}

.quick-btn.primary {
	background: #F0E6D8;
	color: #5a4b35;
}

.quick-btn.danger {
	background: #C62828;
	color: #FFF;
	border: 1rpx solid rgba(255, 255, 255, 0.3);
}

.quick-btn:active {
	opacity: 0.85;
	transform: scale(0.97);
}

/* 卡片底部标题：在非 hover 状态也提供轻量信息 */
.card-caption {
	margin-top: 10rpx;
	padding: 0 4rpx;
	transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
}

.card-caption-name {
	display: block;
	font-size: 32rpx;
	color: #5b5b5f;
	font-weight: 500;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.model-card {
	background: transparent;
	cursor: pointer;
	perspective: 1200px;
	transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.28s ease, opacity 0.28s ease;
}

.model-card:active {
	transform: scale(0.98);
}

.model-img-wrap {
	position: relative;
	width: 100%;
	aspect-ratio: 4 / 5;
	transform-style: preserve-3d;
	background: radial-gradient(circle at 50% 40%, #ffffff, #F3F1EC);
	box-shadow:
		inset 0 1rpx 0 rgba(255, 255, 255, 0.7),
		0 6rpx 16rpx rgba(0, 0, 0, 0.04);
	border-radius: 16rpx;
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.28s ease;
}

.model-img-wrap:hover {
	transform: translateY(-4rpx) rotateY(4deg);
	box-shadow:
		inset 0 1rpx 0 rgba(255, 255, 255, 0.8),
		0 30px 60px rgba(0, 0, 0, 0.15);
}

.model-img-wrap:hover .model-img {
	transform: scale(1.03);
}

.model-img-wrap:hover .card-overlay {
	opacity: 1;
	pointer-events: auto;
}

.model-img {
	width: 100%;
	height: 100%;
	object-fit: cover;
	transition: transform 0.3s ease;
}

.model-card.is-default .model-img-wrap {
	border: 3rpx solid #9D8B70;
	box-shadow: 0 4rpx 16rpx rgba(157, 139, 112, 0.25);
}

.model-card.is-default .model-img-wrap:hover {
	box-shadow:
		inset 0 1rpx 0 rgba(255, 255, 255, 0.8),
		0 30px 60px rgba(0, 0, 0, 0.15),
		0 0 0 3rpx #9D8B70;
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

@keyframes empty-float {
	0%, 100% { transform: translateY(0); }
	50% { transform: translateY(-6px); }
}

.empty-state-wrap {
	position: relative;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	min-height: 420rpx;
	padding: 64rpx 48rpx;
	text-align: center;
	overflow: hidden;
}

/* 空状态轻背景容器：磨砂面板 */
.empty-state-panel {
	position: relative;
	width: 100%;
	max-width: 1200rpx;
	background: rgba(255, 255, 255, 0.6);
	backdrop-filter: blur(8px);
	-webkit-backdrop-filter: blur(8px);
	border-radius: 24rpx;
	padding: 96rpx 160rpx;
	box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	overflow: hidden;
}

.empty-state-bg-pattern {
	position: absolute;
	inset: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 120rpx;
	letter-spacing: 0.4em;
	opacity: 0.03;
	pointer-events: none;
	user-select: none;
}

.empty-state-illustration {
	position: relative;
	margin-bottom: 32rpx;
	animation: empty-float 4s ease-in-out infinite;
}

/* icon 后方淡淡服装纹理 */
.empty-state-icon-texture {
	position: absolute;
	left: 50%;
	top: 50%;
	transform: translate(-50%, -50%);
	font-size: 100rpx;
	letter-spacing: 0.3em;
	opacity: 0.05;
	pointer-events: none;
	white-space: nowrap;
}

.empty-state-icon {
	position: relative;
	width: 160rpx;
	height: 160rpx;
	opacity: 0.9;
}

.empty-state-headline {
	font-family: "Playfair Display", "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 56rpx;
	font-weight: 600;
	color: #3A3631;
	margin-bottom: 20rpx;
	line-height: 1.3;
}

.empty-state-subtitle {
	font-family: Georgia, 'Times New Roman', Times, serif;
	font-size: 27rpx;
	color: #8A847C;
	margin-bottom: 48rpx;
	line-height: 1.5;
	max-width: 1600rpx;
}

.empty-state-cta {
	padding: 24rpx 56rpx;
	border-radius: 999rpx;
	background: #8C7355;
	color: #FFF;
	font-size: 30rpx;
	font-weight: 600;
	font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
	cursor: pointer;
	transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.empty-state-cta:hover {
	transform: translateY(-2rpx);
	box-shadow: 0 6rpx 20rpx rgba(140, 115, 85, 0.35);
}
.empty-state-cta:active {
	transform: translateY(0);
}

/* --- 搜索/筛选无结果的高级感样式 --- */
.no-results-wrap {
	display: flex;
	justify-content: center;
	align-items: center;
	min-height: 50vh;
	width: 100%;
}
.no-results-content {
	display: flex;
	flex-direction: column;
	align-items: center;
	text-align: center;
	max-width: 600rpx;
	animation: fade-in-up 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
@keyframes fade-in-up {
	from { opacity: 0; transform: translateY(20rpx); }
	to { opacity: 1; transform: translateY(0); }
}
.no-results-visual {
	position: relative;
	margin-bottom: 32rpx;
	display: flex;
	justify-content: center;
	align-items: center;
	width: 120rpx;
	height: 120rpx;
	border-radius: 50%;
	background: linear-gradient(135deg, #FDFBF7, #F3F1EC);
	box-shadow:
		inset 0 4rpx 10rpx rgba(255, 255, 255, 0.8),
		0 10rpx 30rpx rgba(140, 115, 85, 0.08);
}
.no-results-mark {
	font-size: 56rpx;
	color: #9D8B70;
	transform: rotate(-45deg);
	opacity: 0.8;
}
.no-results-title {
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 48rpx;
	font-weight: 600;
	color: #1D1D1F;
	margin-bottom: 16rpx;
	letter-spacing: 0.02em;
}
.no-results-desc {
	font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
	font-size: 28rpx;
	line-height: 1.6;
	color: #8A847C;
	margin-bottom: 48rpx;
}
.no-results-action {
	position: relative;
	cursor: pointer;
	padding: 8rpx 0;
	display: inline-flex;
	flex-direction: column;
	align-items: center;
}
.no-results-action .action-text {
	font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
	font-size: 28rpx;
	font-weight: 600;
	color: #8C7355;
	letter-spacing: 0.02em;
	transition: color 0.3s ease;
}
.no-results-action:hover .action-text {
	color: #1D1D1F;
}
.no-results-action .action-underline {
	width: 100%;
	height: 2rpx;
	background-color: #8C7355;
	margin-top: 4rpx;
	transform-origin: center;
	transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), background-color 0.3s ease;
}
.no-results-action:hover .action-underline {
	transform: scaleX(0.4);
	background-color: #1D1D1F;
}

/* 无结果 ⇄ 列表 状态切换：先完整淡出再淡入，避免衣服突然闪现 */
.state-fade-enter-active,
.state-fade-leave-active {
	transition: opacity 0.4s ease, transform 0.4s ease;
}
.state-fade-leave-to {
	opacity: 0;
	transform: scale(0.98);
	pointer-events: none;
}
.state-fade-enter-from {
	opacity: 0;
	transform: translateY(24rpx);
}
.state-fade-enter-to,
.state-fade-leave-from {
	opacity: 1;
	transform: translateY(0) scale(1);
}
/* 列表容器进场时稍延迟，让「无结果」先离开再显示列表 */
.list-container {
	animation: list-container-enter 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.08s forwards;
	opacity: 0;
}
@keyframes list-container-enter {
	from {
		opacity: 0;
		transform: translateY(12rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

/* 列表进场：卡片错落淡入 */
.stagger-enter {
	animation: stagger-enter 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
	opacity: 0;
}
@keyframes stagger-enter {
	from {
		opacity: 0;
		transform: translateY(20rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
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


/* 模特照片上传模态框特有样式 */
.switch-option {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 0;
}

.switch-label {
  font-size: 28rpx;
  color: #1D1D1F;
}

.form-hint {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
  font-style: italic;
}

</style>
