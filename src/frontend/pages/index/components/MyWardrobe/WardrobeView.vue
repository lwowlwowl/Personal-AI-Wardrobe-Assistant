<template>
	<scroll-view class="wardrobe-container" scroll-y :show-scrollbar="false">
		<view class="wardrobe-inner">
			<!-- 添加上传状态提示 -->
			<view v-if="uploadLoading" class="upload-loading">
				<text>上传并打标中...</text>
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
							class="search-input" 
							type="text" 
							placeholder="Search your wardrobe..." 
							placeholder-class="search-placeholder"
							v-model="searchQuery"
						/>
						<input 
							v-else
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
								<text>Favourite</text>
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
								<text>Clothing type</text>
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
								<text>Color</text>
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
			<!-- 在 template 中的合适位置添加 -->
			<view v-if="showCategoryModal" class="category-modal-overlay" @click="closeCategoryModal">
			  <view class="category-modal" @click.stop>
			    <view class="modal-header">
			      <text class="modal-title">上传衣物</text>
			      <text class="close-btn" @click="closeCategoryModal">×</text>
			    </view>
			    
			    <view class="modal-content">
			      <view class="form-group">
			        <text class="form-label">衣物名称 *</text>
			        <input 
			          class="form-input" 
			          v-model="uploadFormData.name" 
			          placeholder="输入衣物名称"
			        />
			      </view>
			      
			      <view class="form-group">
			        <text class="form-label">主分类 (Category) *</text>
			        <view class="category-options">
			          <view 
			            v-for="opt in typeOptions" 
			            :key="opt.value"
			            class="category-option"
			            :class="{ active: uploadFormData.category === opt.value }"
			            @click="selectCategory(opt.value)"
			          >
			            <text>{{ opt.label }}</text>
			          </view>
			        </view>
			      </view>
			      <view class="form-group">
			        <text class="form-label">子分类 (SubCategory)</text>
			        <input 
			          class="form-input" 
			          v-model="uploadFormData.subcategory" 
			          placeholder="例如：T恤、衬衫、牛仔裤"
			        />
			      </view>
			      
			      <view class="form-group">
			        <text class="form-label">颜色</text>
			        <input 
			          class="form-input" 
			          v-model="uploadFormData.color" 
			          placeholder="输入颜色，如 red、navy blue"
			        />
			      </view>
			      
			      <view class="form-group">
			        <text class="form-label">季节</text>
			        <view class="season-options">
			          <view 
			            v-for="opt in seasonOptions" 
			            :key="opt.value"
			            class="season-option"
			            :class="{ active: uploadFormData.season === opt.value }"
			            @click="uploadFormData.season = opt.value"
			          >
			            <text>{{ opt.label }}</text>
			          </view>
			        </view>
			      </view>
			      
			      <view class="form-group">
			        <text class="form-label">品牌</text>
			        <input 
			          class="form-input" 
			          v-model="uploadFormData.brand" 
			          placeholder="输入品牌"
			        />
			      </view>
			      
			      <view class="form-group">
			        <text class="form-label">标签（用逗号分隔）</text>
			        <input 
			          class="form-input" 
			          v-model="uploadFormData.tags" 
			          placeholder="例如：休闲,通勤,舒适"
			        />
			      </view>
			      
			      <view class="form-group">
			        <text class="form-label">价格</text>
			        <input 
			          class="form-input" 
			          v-model="uploadFormData.price" 
			          placeholder="输入价格"
			          type="number"
			        />
			      </view>
			      
			      <view class="form-group">
			        <text class="form-label">描述</text>
			        <textarea 
			          class="form-textarea" 
			          v-model="uploadFormData.description" 
			          placeholder="输入衣物描述..."
			          maxlength="200"
			        />
			      </view>
			    </view>
			    
			    <view class="modal-actions">
			      <view class="btn-cancel" @click="closeCategoryModal">取消</view>
			      <view class="btn-confirm" @click="confirmUpload">确认并保存</view>
			    </view>
			  </view>
			</view>
			
			<view v-if="showModelUploadModal" class="category-modal-overlay" @click="closeModelUploadModal">
			    <view class="category-modal" @click.stop>
			      <view class="modal-header">
			        <text class="modal-title">上传模特照片</text>
			        <text class="close-btn" @click="closeModelUploadModal">×</text>
			      </view>
			      
			      <view class="modal-content">
			        <view class="form-group">
			          <text class="form-label">模特照片名称 *</text>
			          <input 
			            class="form-input" 
			            v-model="modelUploadFormData.photo_name" 
			            placeholder="输入模特照片名称"
			          />
			        </view>
			        
			        <view class="form-group">
			          <text class="form-label">描述</text>
			          <textarea 
			            class="form-textarea" 
			            v-model="modelUploadFormData.description" 
			            placeholder="输入模特照片描述..."
			            maxlength="200"
			          />
			        </view>
			        
			        <view class="form-group">
			          <view class="form-label">
			            <text>设置为主要模特</text>
			          </view>
			          <view class="switch-option">
			            <switch 
			              :checked="modelUploadFormData.is_primary" 
			              @change="modelUploadFormData.is_primary = $event.detail.value"
			              color="#9D8B70"
			            />
			            <text class="switch-label">设为默认模特照片</text>
			          </view>
			          <text class="form-hint">设置后将在虚拟试穿中默认使用此模特</text>
			        </view>
			      </view>
			      
			      <view class="modal-actions">
			        <view class="btn-cancel" @click="closeModelUploadModal">取消</view>
			        <view class="btn-confirm" @click="confirmModelUpload">确认上传</view>
			      </view>
			    </view>
			  </view>

			<view class="divider"></view>

			<transition name="view-switch" mode="out-in">
				<view :key="viewMode" class="view-switch-inner">
					<!-- Cloth Grid -->
					<template v-if="viewMode === 'Cloth'">
						<view v-if="displayList.length === 0" class="empty-state-wrap" :class="{ 'empty-state-has-filters': hasActiveFilters }">
							<template v-if="hasActiveFilters">
								<text class="empty-state-title">没有符合筛选条件的衣物</text>
								<text class="empty-state-hint">试试调整或清除筛选条件</text>
								<view class="empty-state-btn" @click="clearAllFilters">清除筛选</view>
							</template>
							<template v-else>
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
							</template>
						</view>
						<template v-else>
						<transition name="page-fade" mode="out-in">
							<view class="clothes-grid" :key="currentPage">
								<view 
									v-for="(item, index) in paginatedList" 
									:key="item.id" 
									class="cloth-card"
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
												  <text class="card-tag">In wardrobe</text>
											  </view>
											  <view class="card-overlay-bottom">
												  <text class="card-name" :title="item.name">{{ item.name || '未命名衣物' }}</text>
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
											{{ item.name || '未命名衣物' }}
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
						</template>
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
		<DeleteConfirmModal
			:visible="showDeleteModal"
			:title="deleteModalTitle"
			:content="deleteModalContent"
			@confirm="doDeleteConfirm"
			@cancel="handleDeleteCancel"
		/>
	</scroll-view>
</template>

<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import DetailModal from './DetailModal.vue'
import ModelDetailModal from './ModelDetailModal.vue'
import DeleteConfirmModal from './DeleteConfirmModal.vue'
import { TYPE_OPTIONS, SEASON_OPTIONS } from '@/utils/wardrobeEnums.js'
import {
  API_BASE_URL,
  authVerify,
  getClothingList,
  uploadClothing,
  deleteClothing,
  updateClothing,
  getModelPhotos,
  uploadModelPhoto,
  deleteModelPhoto,
  setModelPhotoPrimary,
  updateModelPhoto
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

onMounted(async () => {
  // 页面加载时检查认证状态
  await checkAuthStatus()
  
  // 如果已登录，加载用户数据
  if (isLoggedIn.value) {
    await loadClothingData()
  }
})

// ============ 上传相关状态 ============
const uploadLoading = ref(false)
const uploadError = ref('')
const showCategoryModal = ref(false)
const selectedImageFile = ref(null)
/** 上传并打标成功后要编辑的衣物 id，确认时走 update 而非再次上传 */
const createdItemIdForEdit = ref(null)

const uploadFormData = ref({
  name: '',
  category: '',   // 后端 9 个主分类之一
  subcategory: '', // 用户可自由输入的子分类
  color: '',
  season: '',
  brand: '',
  tags: '',
  description: '',
  price: '',
  purchase_date: ''
})

// ============ 认证相关方法 ============

/**
 * 检查认证状态
 */
async function checkAuthStatus() {
  if (!userToken.value) {
    isLoggedIn.value = false
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
    console.error('验证token失败:', error)
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
  updateAuthState?.(false)
}

onMounted(async () => {
  await checkAuthStatus()
  if (isLoggedIn.value) {
    await loadClothingData()
  }
})

const testSimpleUpload = async () => {
  try {
    console.log('开始衣物上传...')
    
    // 1. 检查登录状态
    if (!isLoggedIn.value) {
      uni.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return
    }
    
    console.log('用户已登录，token:', userToken.value.substring(0, 20) + '...')
    
    // 2. 选择图片
    const chooseResult = await uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera']
    })
    
    console.log('选择的图片:', chooseResult)
    
    if (!chooseResult.tempFilePaths || chooseResult.tempFilePaths.length === 0) {
      uni.showToast({ title: '未选择图片', icon: 'none' })
      return
    }
    
    const tempFilePath = chooseResult.tempFilePaths[0]
    console.log('临时文件路径:', tempFilePath)
    
    // 3. 获取文件信息
    const fileInfo = await uni.getFileInfo({
      filePath: tempFilePath
    })
    console.log('文件信息:', fileInfo)
    
    // 检查文件大小（后端限制10MB）
    if (fileInfo.size > 10 * 1024 * 1024) {
      uni.showToast({
        title: '文件大小不能超过10MB',
        icon: 'none'
      })
      return
    }
    
    // 4. 立即上传并让后端打标，显示加载中（使用 uni 原生 loading 确保用户可见）
    uploadLoading.value = true
    createdItemIdForEdit.value = null
    uni.showLoading({ title: '上传并打标中...', mask: true })
    try {
      const result = await uploadClothing({
        token: userToken.value,
        filePath: tempFilePath,
        formData: {
          name: '',
          category: '',
          subcategory: '',
          color: '',
          season: '',
          brand: '',
          tags: '',
          description: '',
          price: '',
          purchase_date: ''
        }
      })
      if (result.statusCode !== 200 || !result.data?.success) {
        throw new Error(result.data?.message || result.data?.detail || '上传失败')
      }
      const data = result.data?.data || result.data
      const raw = data.auto_label || {}
      // 用后端返回的数据（含打标结果）预填表单
      const tagParts = [raw.style, raw.occasion].filter(Boolean).map(String)
      uploadFormData.value = {
        name: data.name || raw.subcategory || raw.category || '未命名',
        category: raw.category || data.category || '',
        subcategory: raw.subcategory || '',
        color: typeof raw.color === 'string' ? raw.color : (raw.color || ''),
        season: Array.isArray(raw.season) ? (raw.season[0] || '') : (raw.season || ''),
        brand: raw.brand || '',
        tags: tagParts.join(','),
        description: raw.description || '',
        price: uploadFormData.value.price || '',
        purchase_date: uploadFormData.value.purchase_date || ''
      }
      createdItemIdForEdit.value = data.id
      showCategoryModal.value = true
    } catch (err) {
      const msg = err.message || err.errMsg || '上传失败'
      uni.showToast({ title: msg, icon: 'none' })
    } finally {
      uploadLoading.value = false
      uni.hideLoading()
    }
    
  } catch (error) {
    console.error('选择图片异常:', error)
    uni.showToast({
      title: '选择图片失败',
      icon: 'none'
    })
  }
}

// 添加分类选择方法
const selectCategory = (category) => {
  uploadFormData.value.category = category
}

// 确认：编辑模式下为 update，否则不再走上传（上传已在选图后完成）
const confirmUpload = async () => {
  if (createdItemIdForEdit.value == null) {
    closeCategoryModal()
    return
  }
  if (!uploadFormData.value.category) {
    uni.showToast({ title: '请选择主分类', icon: 'none' })
    return
  }
  if (!uploadFormData.value.name || !uploadFormData.value.name.trim()) {
    uni.showToast({ title: '请输入衣物名称', icon: 'none' })
    return
  }
  try {
    uni.showLoading({ title: '保存中...', mask: true })
    const seasonVal = uploadFormData.value.season
    const seasonPayload = seasonVal ? JSON.stringify(Array.isArray(seasonVal) ? seasonVal : [seasonVal]) : undefined
    const result = await updateClothing(userToken.value, createdItemIdForEdit.value, {
      name: uploadFormData.value.name.trim(),
      category: uploadFormData.value.category,
      subcategory: uploadFormData.value.subcategory || undefined,
      color: uploadFormData.value.color || undefined,
      season: seasonPayload,
      brand: uploadFormData.value.brand || undefined,
      tags: uploadFormData.value.tags || undefined,
      description: uploadFormData.value.description || undefined,
      price: uploadFormData.value.price !== '' ? uploadFormData.value.price : undefined
    })
    uni.hideLoading()
    if (result.statusCode === 200 && result.data?.success !== false) {
      uni.showToast({ title: '保存成功', icon: 'success' })
      closeCategoryModal()
      createdItemIdForEdit.value = null
      loadClothingData()
    } else {
      uni.showToast({ title: result.data?.message || '保存失败', icon: 'none' })
    }
  } catch (err) {
    uni.hideLoading()
    uni.showToast({ title: err.message || err.errMsg || '网络错误', icon: 'none' })
  }
}

// 重置上传表单
const resetUploadForm = () => {
  uploadFormData.value = {
    name: '',
    category: '',
    subcategory: '',
    color: '',
    season: '',
    brand: '',
    tags: '',
    description: '',
    price: '',
    purchase_date: ''
  }
}

// 关闭模态框
const closeCategoryModal = () => {
  showCategoryModal.value = false
  selectedImageFile.value = null
  createdItemIdForEdit.value = null
  resetUploadForm()
}


// 加载衣物数据的方法
// 修改 loadClothingData，在加载时自动应用修复
const loadClothingData = async () => {
  try {
    if (!isLoggedIn.value) return
    const queryParams = {
      token: userToken.value,
      // 后端分页只用于限制最大返回数量，这里一次拉取尽量多的数据，前端再做分页
      page: 1,
      page_size: 100,
      order_by: 'created_at',
      order_desc: true
    }
    
    
    console.log('=== 加载衣物数据（带自动修复）===')
    
    const response = await getClothingList({
      token: userToken.value,
      page: queryParams.page,
      page_size: queryParams.page_size,
      order_by: 'created_at',
      order_desc: true
    })
    
    if (response.statusCode === 200 && response.data.success) {
      const items = response.data.data.items || []
      console.log(`获取到 ${items.length} 件衣物`)
      
      // 第一步：构建初始数据
      const initialItems = items.map(item => {
        // 构建图片URL - 关键：对相对路径添加API基础URL
        let imageUrl = ''
        
        if (item.image_url) {
          if (item.image_url.startsWith('/')) {
            // 相对路径：添加API基础URL
            imageUrl = `${API_BASE_URL}${item.image_url}`
            console.log(`衣物 ${item.id}: 相对路径 -> ${imageUrl}`)
          } else if (item.image_url.startsWith('http')) {
            // 完整URL
            imageUrl = item.image_url
            console.log(`衣物 ${item.id}: 完整URL -> ${imageUrl}`)
          } else {
            // 其他格式
            imageUrl = `${API_BASE_URL}/${item.image_url}`
            console.log(`衣物 ${item.id}: 其他格式 -> ${imageUrl}`)
          }
        } else {
          // 没有图片URL
          imageUrl = 'https://placehold.co/400x500/f5f0e6/8c7b60?text=No+Image'
        }
        
        // 后端 season 为数组 ["autumn","winter"]，前端筛选/详情用逗号分隔字符串，此处统一成字符串
        const seasonVal = item.season
        const seasonStr = Array.isArray(seasonVal) ? seasonVal.join(',') : (seasonVal || '')

        const tagsArr = (item.tags || []).map((t) => (typeof t === 'string' ? t : (t?.tag || t))).filter(Boolean)
        return {
          id: item.id,
          name: item.name || '未命名衣物',
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
      clothes.value = await applyImageUrlFixes(initialItems)
      
      console.log(`✅ 数据加载完成，共 ${clothes.value.length} 件衣物`)
      
      // 第三步：验证修复结果
      await verifyImageLoads()
      
    }
    
  } catch (error) {
    console.error('加载衣物数据失败:', error)
  }
}

// 应用URL修复
const applyImageUrlFixes = async (items) => {
  console.log('应用图片URL修复...')
  
  const fixedItems = []
  
  for (const item of items) {
    // 复制item
    const fixedItem = { ...item }
    
    // 如果标记为需要修复，或者当前URL可能是相对路径
    if (item._needsFix || item.image.startsWith('/')) {
      console.log(`检查衣物 ${item.id} 的图片URL: ${item.image}`)
      
      // 尝试修复
      const fixedUrl = await getWorkingImageUrl(item)
      
      if (fixedUrl !== item.image) {
        console.log(`  修复: ${item.image} -> ${fixedUrl}`)
        fixedItem.image = fixedUrl
        fixedItem._wasFixed = true
        fixedItem._originalImage = item.image
      }
    }
    
    fixedItems.push(fixedItem)
  }
  
  console.log(`修复完成: ${fixedItems.filter(item => item._wasFixed).length} 个URL被修复`)
  return fixedItems
}

// 获取可工作的图片URL
const getWorkingImageUrl = async (item) => {
  const candidates = []
  
  // 候选方案1：当前URL
  candidates.push(item.image)
  
  // 候选方案2：添加API基础URL（如果当前是相对路径）
  if (item.image.startsWith('/')) {
    candidates.push(`${API_BASE_URL}${item.image}`)
  }
  
  // 候选方案3：使用原始路径（如果不同）
  if (item._rawImageUrl && item._rawImageUrl !== item.image) {
    candidates.push(item._rawImageUrl)
    // 如果是相对路径，也尝试添加API基础URL
    if (item._rawImageUrl.startsWith('/')) {
      candidates.push(`${API_BASE_URL}${item._rawImageUrl}`)
    }
  }
  
  // 候选方案4：添加缓存破坏
  if (item.image.includes('?')) {
    candidates.push(`${item.image.split('?')[0]}?t=${Date.now()}`)
  } else {
    candidates.push(`${item.image}?t=${Date.now()}`)
  }
  
  console.log(`为衣物 ${item.id} 测试候选URL:`, candidates)
  
  // 测试每个候选URL
  for (const candidate of candidates) {
    const isWorking = await testImageUrlAsync(candidate)
    if (isWorking) {
      console.log(`  ✅ 找到可用的URL: ${candidate}`)
      return candidate
    }
  }
  
  // 所有候选都失败，返回原始URL
  console.log(`  ❌ 所有候选URL都失败，使用原始URL`)
  return item.image
}

// 验证图片加载
const verifyImageLoads = async () => {
  console.log('验证图片加载...')
  
  const results = []
  
  for (const item of clothes.value) {
    const isAccessible = await testImageUrlAsync(item.image)
    results.push({
      id: item.id,
      name: item.name,
      url: item.image,
      accessible: isAccessible,
      wasFixed: item._wasFixed || false
    })
  }
  
  const accessibleCount = results.filter(r => r.accessible).length
  const inaccessibleCount = results.filter(r => !r.accessible).length
  const fixedCount = results.filter(r => r.wasFixed).length
  
  console.log(`验证结果: ${accessibleCount} 张可访问, ${inaccessibleCount} 张不可访问`)
  console.log(`其中 ${fixedCount} 张经过修复`)
  
  // 显示不可访问的图片
  if (inaccessibleCount > 0) {
    console.log('不可访问的图片:')
    results.filter(r => !r.accessible).forEach(r => {
      console.log(`  ID: ${r.id}, 名称: ${r.name}`)
      console.log(`  URL: ${r.url}`)
    })
  }
  
  return results
}

// 修改为可重用的修复函数
const fixImageUrlForItem = (item) => {
  console.log(`尝试修复衣物 ${item.id} 的图片URL...`)
  console.log('原始URL:', item.image)
  console.log('原始raw URL:', item._rawImageUrl)
  
  const original = item._rawImageUrl || item.image
  let fixedUrl = item.image
  
  // 方案1：如果原始路径是相对路径，添加API基础URL
  if (original && original.startsWith('/') && !original.startsWith('http')) {
    const fullUrl = `${API_BASE_URL}${original}`
    console.log(`方案1: 添加API基础URL -> ${fullUrl}`)
    
    // 测试这个URL
    const testResult = testImageUrl(fullUrl)
    if (testResult) {
      fixedUrl = fullUrl
      console.log(`✅ 方案1成功！`)
    } else {
      console.log(`❌ 方案1失败`)
    }
  }
  
  // 方案2：如果已经是http URL但无法访问，尝试其他修复
  if (fixedUrl === item.image && original && original.startsWith('http')) {
    // 尝试添加缓存破坏
    const cacheBusterUrl = `${original}?t=${Date.now()}`
    console.log(`方案2: 添加缓存破坏 -> ${cacheBusterUrl}`)
    
    const testResult = testImageUrl(cacheBusterUrl)
    if (testResult) {
      fixedUrl = cacheBusterUrl
      console.log(`✅ 方案2成功！`)
    }
  }

  
  // 如果URL有变化，返回修复后的URL
  if (fixedUrl !== item.image) {
    console.log(`修复成功: ${item.image} -> ${fixedUrl}`)
    return fixedUrl
  }
  
  console.log(`无法修复，保持原URL: ${item.image}`)
  return item.image
}

// 测试单个URL的函数
const testImageUrl = (url) => {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      console.log(`  ✅ URL可访问: ${url}`)
      resolve(true)
    }
    img.onerror = () => {
      console.log(`  ❌ URL不可访问: ${url}`)
      resolve(false)
    }
    img.src = url
    // 设置超时
    setTimeout(() => {
      if (!img.complete) {
        console.log(`  ⏱️ URL测试超时: ${url}`)
        resolve(false)
      }
    }, 3000)
  })
}

// 修复所有图片URL
const fixAllImageUrls = async () => {
  console.log('开始修复所有图片URL...')
  
  const total = clothes.value.length
  console.log(`需要修复 ${total} 张图片`)
  
  // 用于跟踪修复结果
  const results = {
    total: total,
    fixed: 0,
    failed: 0,
    unchanged: 0
  }
  
  // 依次修复每张图片
  for (let i = 0; i < clothes.value.length; i++) {
    const item = clothes.value[i]
    console.log(`\n修复进度: ${i + 1}/${total} (ID: ${item.id})`)
    
    // 保存原始URL
    const originalUrl = item.image
    
    // 尝试修复
    const fixedUrl = await fixImageUrlForItemAsync(item)
    
    // 如果URL有变化，更新数据
    if (fixedUrl !== originalUrl) {
      clothes.value[i].image = fixedUrl
      clothes.value[i]._originalUrl = originalUrl // 保存原始URL用于调试
      clothes.value[i]._fixed = true
      clothes.value[i]._fixedAt = new Date().toISOString()
      results.fixed++
      console.log(`✅ 已修复`)
    } else {
      results.unchanged++
      console.log(`⏭️ 无需修复`)
    }
    
    // 小延迟避免请求过于密集
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  
  // 强制更新视图
  clothes.value = [...clothes.value]
  
  console.log('\n📊 修复结果:')
  console.log(`总数: ${results.total}`)
  console.log(`修复成功: ${results.fixed}`)
  console.log(`无需修复: ${results.unchanged}`)
  console.log(`修复失败: ${results.failed}`)
  
  // 显示通知
  uni.showToast({
    title: `修复完成: ${results.fixed}张图片已修复`,
    icon: 'success',
    duration: 3000
  })
  
  return results
}

// 异步版本的修复函数
const fixImageUrlForItemAsync = async (item) => {
  const original = item._rawImageUrl || item.image
  let currentBestUrl = item.image
  
  // 方案1：添加API基础URL（针对相对路径）
  if (original && original.startsWith('/') && !original.startsWith('http')) {
    const candidateUrl = `${API_BASE_URL}${original}`
    console.log(`测试方案1: ${candidateUrl}`)
    
    const isAccessible = await testImageUrlAsync(candidateUrl)
    if (isAccessible) {
      console.log(`✅ 方案1可用`)
      return candidateUrl
    }
  }
  
  // 方案2：当前URL添加缓存破坏
  if (currentBestUrl) {
    const cacheBusterUrl = currentBestUrl.includes('?') 
      ? `${currentBestUrl}&t=${Date.now()}`
      : `${currentBestUrl}?t=${Date.now()}`
    
    console.log(`测试方案2: ${cacheBusterUrl}`)
    const isAccessible = await testImageUrlAsync(cacheBusterUrl)
    if (isAccessible) {
      console.log(`✅ 方案2可用`)
      return cacheBusterUrl
    }
  }
  
  // 方案3：尝试直接使用原始路径（如果当前是完整URL但原始是相对路径）
  if (currentBestUrl.startsWith('http') && original && original.startsWith('/')) {
    console.log(`测试方案4: ${original}`)
    const isAccessible = await testImageUrlAsync(original)
    if (isAccessible) {
      console.log(`✅ 方案4可用`)
      return original
    }
  }
  
  // 所有方案都失败，返回原URL
  return currentBestUrl
}

// 异步测试URL
const testImageUrlAsync = (url) => {
  return new Promise((resolve) => {
    const img = new Image()
    
    // 设置超时
    const timeout = setTimeout(() => {
      img.onload = img.onerror = null
      console.log(`  ⏱️ 测试超时: ${url}`)
      resolve(false)
    }, 5000)
    
    img.onload = () => {
      clearTimeout(timeout)
      console.log(`  ✅ 可访问: ${url} (${img.width}x${img.height})`)
      resolve(true)
    }
    
    img.onerror = () => {
      clearTimeout(timeout)
      console.log(`  ❌ 不可访问: ${url}`)
      resolve(false)
    }
    
    img.src = url
  })
}

const handleDeleteItem = (id) => {
  deletePayload.value = { type: 'cloth', id }
  showDeleteModal.value = true
}

const doDeleteClothing = async (id) => {
  try {
    console.log('=== 开始删除衣物 ===', id)
    uni.showLoading({ title: '删除中...', mask: true })
    const response = await deleteClothing(userToken.value, id)
    uni.hideLoading()
    const notFound = response.statusCode === 404 ||
      (response.data && (
        String(response.data.detail || '').includes('不存在') ||
        String(response.data.message || '').includes('不存在')
      ))
    if (response.statusCode === 200 && response.data && response.data.success) {
      clothes.value = clothes.value.filter((c) => c.id !== id)
      uni.showToast({ title: '删除成功', icon: 'success', duration: 2000 })
      if (selectedItem.value && selectedItem.value.id === id) {
        showModal.value = false
        selectedItem.value = {}
      }
      if (paginatedList.value.some(item => item.id === id)) {
        await loadClothingData()
      }
    } else if (notFound) {
      clothes.value = clothes.value.filter((c) => c.id !== id)
      if (selectedItem.value && selectedItem.value.id === id) {
        showModal.value = false
        selectedItem.value = {}
      }
      uni.showToast({ title: '已从列表中移除', icon: 'none', duration: 2000 })
    } else {
      uni.showToast({
        title: response.data?.message || response.data?.detail || '删除失败',
        icon: 'none',
        duration: 3000
      })
    }
  } catch (error) {
    uni.hideLoading()
    console.error('删除衣物失败:', error)
    const errMsg = String(error?.message || error?.errMsg || error?.detail || '')
    const isNotFound = error?.statusCode === 404 || errMsg.includes('不存在')
    if (isNotFound) {
      clothes.value = clothes.value.filter((c) => c.id !== id)
      if (selectedItem.value && selectedItem.value.id === id) {
        showModal.value = false
        selectedItem.value = {}
      }
      uni.showToast({ title: '已从列表中移除', icon: 'none', duration: 2000 })
    } else {
      uni.showToast({ title: '删除失败：网络错误', icon: 'none', duration: 3000 })
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
const modelUploadLoading = ref(false)
const modelUploadError = ref('')
const showModelUploadModal = ref(false)
const selectedModelImageFile = ref(null)

// 模特照片表单数据
const modelUploadFormData = ref({
  photo_name: '',
  description: '',
  is_primary: false
})

// 从后端加载的模特照片数据
const models = ref([])
const defaultModelId = ref(null)

// 当前选中的模特照片（用于编辑）
const selectedModel = ref({})
const showModelModal = ref(false)

// ============ 模特照片相关方法 ============

/**
 * 加载模特照片数据
 */
const loadModelPhotos = async () => {
  try {
    if (!isLoggedIn.value) return
    const queryParams = {
      token: userToken.value,
      page: modelCurrentPage.value,
      page_size: PAGE_SIZE,
      order_by: 'created_at',
      order_desc: true,
      is_active: true
    }
    
    
    console.log('=== 加载模特照片数据 ===')
    
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
      console.log(`获取到 ${photos.length} 张模特照片`)
      
      // 转换数据格式
      models.value = photos.map(photo => {
        // 构建图片URL
        let imageUrl = ''
        
        if (photo.image_url) {
          if (photo.image_url.startsWith('/')) {
            // 相对路径：添加API基础URL
            imageUrl = `${API_BASE_URL}${photo.image_url}`
          } else if (photo.image_url.startsWith('http')) {
            // 完整URL
            imageUrl = photo.image_url
          } else {
            // 其他格式
            imageUrl = `${API_BASE_URL}/${photo.image_url}`
          }
        } else {
          // 没有图片URL
          imageUrl = 'https://placehold.co/400x500/f5f0e6/8c7b60?text=No+Image'
        }
        
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
      
      // 查找主要模特照片
      const primaryModel = models.value.find(model => model.is_primary)
      if (primaryModel) {
        defaultModelId.value = primaryModel.id
      } else if (models.value.length > 0) {
        // 如果没有设置主要模特，使用第一张
        defaultModelId.value = models.value[0].id
      }
      
      console.log(`✅ 模特照片加载完成，共 ${models.value.length} 张，默认ID: ${defaultModelId.value}`)
      
    } else {
      console.error('加载模特照片失败:', response.data?.message)
    }
    
  } catch (error) {
    console.error('加载模特照片数据失败:', error)
  }
}

/**
 * 打开模特照片上传模态框
 */
const openModelUpload = async () => {
  try {
    console.log('开始模特照片上传...')
    
    // 1. 检查登录状态
    if (!isLoggedIn.value) {
      uni.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return
    }
    
    // 2. 选择图片
    const chooseResult = await uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera']
    })
    
    console.log('选择的模特图片:', chooseResult)
    
    if (!chooseResult.tempFilePaths || chooseResult.tempFilePaths.length === 0) {
      uni.showToast({ title: '未选择图片', icon: 'none' })
      return
    }
    
    const tempFilePath = chooseResult.tempFilePaths[0]
    console.log('临时文件路径:', tempFilePath)
    
    // 3. 获取文件信息
    const fileInfo = await uni.getFileInfo({
      filePath: tempFilePath
    })
    console.log('文件信息:', fileInfo)
    
    // 检查文件大小（后端限制10MB）
    if (fileInfo.size > 10 * 1024 * 1024) {
      uni.showToast({
        title: '文件大小不能超过10MB',
        icon: 'none'
      })
      return
    }
    
    // 4. 存储图片文件路径
    selectedModelImageFile.value = tempFilePath
    
    // 5. 重置表单数据
    resetModelUploadForm()
    
    // 6. 显示模特照片上传模态框
    showModelUploadModal.value = true
    
  } catch (error) {
    console.error('选择模特图片异常:', error)
    uni.showToast({
      title: '选择图片失败',
      icon: 'none'
    })
  }
}

/**
 * 重置模特照片上传表单
 */
const resetModelUploadForm = () => {
  modelUploadFormData.value = {
    photo_name: '',
    description: '',
    is_primary: false
  }
}

/**
 * 确认上传模特照片
 */
const confirmModelUpload = async () => {
  // 验证必填字段
  if (!modelUploadFormData.value.photo_name) {
    uni.showToast({
      title: '请输入模特照片名称',
      icon: 'none'
    })
    return
  }
  
  if (!selectedModelImageFile.value) {
    uni.showToast({
      title: '未选择图片',
      icon: 'none'
    })
    return
  }
  
  try {
    // 显示加载提示
    uni.showLoading({
      title: '上传中...',
      mask: true
    })
    
    // 执行上传
    await performModelUpload(selectedModelImageFile.value)
    
  } catch (error) {
    console.error('上传模特照片失败:', error)
    uni.hideLoading()
    uni.showToast({
      title: '上传失败',
      icon: 'none'
    })
  }
}

/**
 * 执行模特照片上传的实际方法
 */
const performModelUpload = async (filePath) => {
  try {
    const result = await uploadModelPhoto({
      token: userToken.value,
      filePath,
      formData: modelUploadFormData.value
    })
    uni.showToast({ title: '模特照片上传成功！', icon: 'success' })
    closeModelUploadModal()
    selectedModelImageFile.value = null
    loadModelPhotos()
    return result
  } catch (err) {
    const errorMsg = err.message || err.errMsg || '网络错误'
    uni.showToast({ title: errorMsg, icon: 'none' })
    throw err
  } finally {
    uni.hideLoading()
  }
}

/**
 * 关闭模特照片上传模态框
 */
const closeModelUploadModal = () => {
  showModelUploadModal.value = false
  selectedModelImageFile.value = null
  resetModelUploadForm()
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
    console.log('=== 开始删除模特照片 ===', id)
    uni.showLoading({ title: '删除中...', mask: true })
    const response = await deleteModelPhoto(userToken.value, id, false)
    uni.hideLoading()
    if (response.statusCode === 200 && response.data.success) {
      const modelIndex = models.value.findIndex((m) => m.id === id)
      if (modelIndex !== -1) models.value[modelIndex].is_active = false
      uni.showToast({ title: '删除成功', icon: 'success', duration: 2000 })
      if (selectedModel.value && selectedModel.value.id === id) {
        showModelModal.value = false
        selectedModel.value = {}
      }
      loadModelPhotos()
    } else {
      uni.showToast({
        title: response.data?.message || '删除失败',
        icon: 'none',
        duration: 3000
      })
    }
  } catch (error) {
    uni.hideLoading()
    console.error('删除模特照片失败:', error)
    uni.showToast({ title: '删除失败：网络错误', icon: 'none', duration: 3000 })
  }
}

/**
 * 设置默认模特照片
 */
const handleSetDefaultModel = async (id) => {
  try {
    console.log('设置默认模特照片:', id)
    
    // 显示加载提示
    uni.showLoading({
      title: '设置中...',
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
        title: '已设置为主要模特照片',
        icon: 'success',
        duration: 2000
      })
      
    } else {
      const errorMsg = response.data?.message || '设置失败'
      uni.showToast({
        title: errorMsg,
        icon: 'none',
        duration: 3000
      })
    }
    
  } catch (error) {
    uni.hideLoading()
    console.error('设置默认模特照片失败:', error)
    uni.showToast({
      title: '设置失败：网络错误',
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
    console.log('更新模特照片:', { id, field, value })
    
    // 如果是is_primary字段，使用专门的API
    if (field === 'is_primary' && value === true) {
      await handleSetDefaultModel(id)
      return
    }
    
    // 显示加载提示
    uni.showLoading({
      title: '更新中...',
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
        title: '更新成功',
        icon: 'success',
        duration: 2000
      })
      
    } else {
      const errorMsg = response.data?.message || '更新失败'
      uni.showToast({
        title: errorMsg,
        icon: 'none',
        duration: 3000
      })
    }
    
  } catch (error) {
    uni.hideLoading()
    console.error('更新模特照片失败:', error)
    uni.showToast({
      title: '更新失败：网络错误',
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
  // 页面加载时检查认证状态
  await checkAuthStatus()
  
  // 如果已登录，加载数据
  if (isLoggedIn.value) {
    await loadClothingData()
    await loadModelPhotos() // 加载模特照片数据
  }
  
  watch(viewMode, (newMode) => {
      console.log(`viewMode切换为: ${newMode}`)
      activeFilter.value = null
      if (newMode === 'Model' && isLoggedIn.value) {
        loadModelPhotos()
      } else if (newMode === 'Cloth' && isLoggedIn.value) {
        loadClothingData()
      }
    })
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

/** 一键清除所有筛选条件 */
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
	currentPage.value = 1
}

const hasActiveFilters = computed(() =>
	appliedFavouriteLevels.value.length > 0 ||
	appliedDate.value != null ||
	appliedTypes.value.length > 0 ||
	appliedColors.value.length > 0 ||
	appliedSeasons.value.length > 0
)

const openDetail = (item) => {
	selectedItem.value = { ...item }
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
			uni.showToast({ title: res.data?.message || '更新失败', icon: 'none' })
		}
	} catch (err) {
		clothes.value[idx] = prev
		selectedItem.value = { ...prev }
		uni.showToast({ title: '网络错误，未同步到后端', icon: 'none' })
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
		uni.showToast({ title: '请拖入图片文件', icon: 'none' })
		return
	}
	// 仅 Cloth 模式支持拖拽上传；且必须走后端打标，绝不往列表里塞假数据
	if (viewMode.value !== 'Cloth') {
		uni.showToast({ title: '请在「Cloth」模式下拖拽上传衣物', icon: 'none' })
		return
	}
	if (!isLoggedIn.value) {
		uni.showToast({ title: '请先登录', icon: 'none' })
		return
	}
	if (file.size > 10 * 1024 * 1024) {
		uni.showToast({ title: '文件大小不能超过10MB', icon: 'none' })
		return
	}
	uploadLoading.value = true
	createdItemIdForEdit.value = null
	uni.showLoading({ title: '上传并打标中...', mask: true })
	let blobUrl = null
	try {
		let result = null
		try {
			result = await uploadClothing({
				token: userToken.value,
				file,
				formData: {
					name: '', category: '', subcategory: '', color: '', season: '',
					brand: '', tags: '', description: '', price: '', purchase_date: ''
				}
			})
		} catch (e1) {
			// 若 fetch 失败（如 CORS），尝试用 blob URL 走 uni.uploadFile
			blobUrl = URL.createObjectURL(file)
			result = await uploadClothing({
				token: userToken.value,
				filePath: blobUrl,
				formData: {
					name: '', category: '', subcategory: '', color: '', season: '',
					brand: '', tags: '', description: '', price: '', purchase_date: ''
				}
			})
		}
		if (!result || result.statusCode !== 200 || !result.data?.success) {
			throw new Error(result?.data?.message || result?.data?.detail || '上传失败')
		}
		const data = result.data?.data || result.data
		const raw = (data.auto_label && data.auto_label._raw) || data.auto_label || {}
		const tagParts = [raw.style, raw.occasion].filter(Boolean).map(String)
		uploadFormData.value = {
			name: data.name || raw.subcategory || raw.category || '未命名',
			category: raw.category || data.category || '',
			subcategory: raw.subcategory || '',
			color: typeof raw.color === 'string' ? raw.color : (raw.color || ''),
			season: Array.isArray(raw.season) ? (raw.season[0] || '') : (raw.season || ''),
			brand: raw.brand || '',
			tags: tagParts.join(','),
			description: raw.description || '',
			price: uploadFormData.value.price || '',
			purchase_date: uploadFormData.value.purchase_date || ''
		}
		createdItemIdForEdit.value = data.id
		showCategoryModal.value = true
	} catch (err) {
		const msg = err?.message || err?.errMsg || '上传失败'
		uni.showToast({ title: msg, icon: 'none' })
	} finally {
		if (blobUrl) URL.revokeObjectURL(blobUrl)
		uploadLoading.value = false
		uni.hideLoading()
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
					type: 'top',
					subcategory: '',
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

/* 有筛选时的简洁空状态 */
.empty-state-wrap.empty-state-has-filters .empty-state-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #1D1D1F;
	margin-bottom: 16rpx;
}
.empty-state-wrap.empty-state-has-filters .empty-state-hint {
	font-size: 26rpx;
	color: #8a8376;
	margin-bottom: 32rpx;
}
.empty-state-btn {
	padding: 18rpx 40rpx;
	border-radius: 24rpx;
	background: #8C7355;
	color: #FFF;
	font-size: 28rpx;
	font-weight: 600;
	cursor: pointer;
	transition: transform 0.2s ease, opacity 0.2s ease;
}
.empty-state-btn:hover {
	transform: translateY(-2rpx);
}
.empty-state-btn:active {
	opacity: 0.9;
	transform: translateY(0);
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

/* 分类选择模态框样式 */
.category-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.category-modal {
  width: 90%;
  max-width: 750rpx;
  max-height: 85vh;
  background: #FFF;
  border-radius: 24rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 32rpx;
  border-bottom: 2rpx solid #E8E4DC;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #FDFBF7;
}

.modal-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #1D1D1F;
  font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
}

.close-btn {
  font-size: 48rpx;
  color: #999;
  cursor: pointer;
  padding: 0 12rpx;
  line-height: 1;
}

.modal-content {
  flex: 1;
  padding: 32rpx;
  overflow-y: auto;
  max-height: calc(85vh - 200rpx);
  /* 确保内容不会被截断 */
  overflow-x: hidden;
}

/* 确保输入框有足够的点击区域 */
.form-input {
  width: 100%;
  padding: 20rpx 24rpx;
  border: 2rpx solid #E8E4DC;
  border-radius: 12rpx;
  font-size: 28rpx;
  color: #1D1D1F;
  background: #FFF;
  box-sizing: border-box;
  /* 添加这些确保可点击 */
  min-height: 80rpx;
  line-height: 40rpx;
  position: relative;
  z-index: 1;
  /* 确保在uni-app中正常 */
  -webkit-user-select: auto !important;
  user-select: auto !important;
}

.form-textarea {
  width: 100%;
  height: 160rpx;
  padding: 20rpx 24rpx;
  border: 2rpx solid #E8E4DC;
  border-radius: 12rpx;
  font-size: 28rpx;
  color: #1D1D1F;
  background: #FFF;
  resize: none;
  box-sizing: border-box;
  /* 添加这些确保可点击 */
  min-height: 160rpx;
  position: relative;
  z-index: 1;
  -webkit-user-select: auto !important;
  user-select: auto !important;
}

.form-group {
  margin-bottom: 32rpx;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 28rpx;
  color: #1D1D1F;
  margin-bottom: 16rpx;
  font-weight: 500;
}

.form-label::after {
  content: ' *';
  color: #ff4444;
}

.form-label:not(:has(+ *[required]))::after {
  content: '';
}

.form-input {
  width: 100%;
  padding: 20rpx 24rpx;
  border: 2rpx solid #E8E4DC;
  border-radius: 12rpx;
  font-size: 28rpx;
  color: #1D1D1F;
  background: #FFF;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: #9D8B70;
  outline: none;
}

.category-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16rpx;
}

.category-option {
  padding: 24rpx 12rpx;
  border: 2rpx solid #E8E4DC;
  border-radius: 12rpx;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 26rpx;
}

.category-option.active {
  background: #FFF9F1;
  border-color: #9D8B70;
  color: #9D8B70;
  font-weight: 600;
  box-shadow: 0 4rpx 12rpx rgba(157, 139, 112, 0.2);
}

.color-options,
.season-options {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.color-option,
.season-option {
  padding: 16rpx 24rpx;
  border: 2rpx solid #E8E4DC;
  border-radius: 8rpx;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 24rpx;
  flex-shrink: 0;
}

.color-option.active,
.season-option.active {
  background: #FFF9F1;
  border-color: #9D8B70;
  color: #9D8B70;
  font-weight: 600;
}

.form-textarea {
  width: 100%;
  height: 160rpx;
  padding: 20rpx 24rpx;
  border: 2rpx solid #E8E4DC;
  border-radius: 12rpx;
  font-size: 28rpx;
  color: #1D1D1F;
  background: #FFF;
  resize: none;
  box-sizing: border-box;
}

.modal-actions {
  padding: 32rpx;
  border-top: 2rpx solid #E8E4DC;
  display: flex;
  gap: 24rpx;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 24rpx;
  text-align: center;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #F5F5F5;
  color: #666;
  border: 2rpx solid #E8E4DC;
}

.btn-confirm {
  background: #9D8B70;
  color: #FFF;
  border: 2rpx solid #9D8B70;
}

.btn-cancel:active {
  background: #E8E4DC;
  transform: translateY(2rpx);
}

.btn-confirm:active {
  background: #8b7a62;
  transform: translateY(2rpx);
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
