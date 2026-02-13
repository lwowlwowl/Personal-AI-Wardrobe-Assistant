<template>
	<view v-if="visible" class="modal-mask" @click="close">
		<view 
			class="modal-wrap" 
			:class="{ 'modal-enter': isEnter, 'modal-leave': isLeave }"
			@click.stop
		>
			<view class="modal-content">
				<view v-if="openField" class="dropdown-backdrop" @click="openField = null"></view>
				<view class="modal-head">
					<view class="close-btn" @click="close">
						<image src="/static/icons/icon-close-red.svg" mode="aspectFit" class="icon-close"></image>
					</view>
				</view>

				<view class="modal-body">
					<view class="image-section">
						<image :src="item.image" mode="aspectFill" class="main-img" />
					</view>
					<view class="info-section">
						<view class="info-row">
							<text class="label">Name:</text>
							<input 
								class="info-input" 
								v-model="editName" 
								placeholder="Item name"
								@blur="emitField('name', editName)"
							/>
						</view>
						<view class="info-row info-row-select">
							<text class="label">Type:</text>
							<view class="select-trigger" @click="openField = openField === 'type' ? null : 'type'">
								<text class="select-value">{{ typeDisplayText }}</text>
								<image :src="openField === 'type' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="select-arrow"></image>
							</view>
							<view v-if="openField === 'type'" class="select-dropdown">
								<view 
									v-for="opt in typeOptions" 
									:key="opt.value" 
									class="select-option" 
									:class="{ active: editTypes.includes(opt.value) }"
									@click="toggleOption('type', opt)"
								>{{ opt.label }}</view>
								<view class="select-apply" @click="applyField('type')">Apply</view>
							</view>
						</view>
						<view class="info-row info-row-readonly">
							<text class="label">Added on:</text>
							<text class="value">{{ item.date || '—' }}</text>
						</view>
						<view class="info-row info-row-select">
							<text class="label">Color:</text>
							<view class="select-trigger" @click="openField = openField === 'color' ? null : 'color'">
								<text class="select-value">{{ colorDisplayText }}</text>
								<image :src="openField === 'color' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="select-arrow"></image>
							</view>
							<view v-if="openField === 'color'" class="select-dropdown">
								<view 
									v-for="opt in colorOptions" 
									:key="opt.value" 
									class="select-option" 
									:class="{ active: editColors.includes(opt.value) }"
									@click="toggleOption('color', opt)"
								>{{ opt.label }}</view>
								<view class="select-apply" @click="applyField('color')">Apply</view>
							</view>
						</view>
						<view class="info-row info-row-select">
							<text class="label">Season:</text>
							<view class="select-trigger" @click="openField = openField === 'season' ? null : 'season'">
								<text class="select-value">{{ seasonDisplayText }}</text>
								<image :src="openField === 'season' ? '/static/icons/icon-arrow-up.svg' : '/static/icons/icon-arrow-down.svg'" mode="aspectFit" class="select-arrow"></image>
							</view>
							<view v-if="openField === 'season'" class="select-dropdown">
								<view 
									v-for="opt in seasonOptions" 
									:key="opt.value" 
									class="select-option" 
									:class="{ active: editSeasons.includes(opt.value) }"
									@click="toggleOption('season', opt)"
								>{{ opt.label }}</view>
								<view class="select-apply" @click="applyField('season')">Apply</view>
							</view>
						</view>
						<view class="info-row info-row-favourite">
							<text class="label">Favourite:</text>
							<view class="hearts">
								<view 
									v-for="k in 3" 
									:key="k" 
									class="heart-wrap" 
									@click="setFavourite(k)"
								>
									<image 
										:src="editFavourite >= k ? '/static/icons/icon-heart-filled.svg' : '/static/icons/icon-heart.svg'" 
										mode="aspectFit" 
										class="heart-icon"
									/>
								</view>
							</view>
						</view>
					</view>
				</view>

				<view class="tags-section">
					<text class="tags-title">Similar Tags:</text>
					<view class="tags-list">
						<view class="tag-placeholder" v-for="n in 5" :key="n"></view>
					</view>
				</view>

				<view class="action-bar">
					<view class="btn try-on-btn" @click="handleTryOn">
						<text>Virtual Try-on</text>
						<image src="/static/icons/icon-tryon.svg" mode="aspectFit" class="icon-camera"></image>
					</view>
					<view class="btn delete-btn" @click="handleDelete">Delete</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { watch, ref, nextTick, computed } from 'vue'
import { TYPE_OPTIONS, COLOR_OPTIONS, SEASON_OPTIONS, TYPE_LABEL_BY_CODE, COLOR_LABEL_BY_CODE, SEASON_LABEL_BY_CODE, codesToLabels } from '@/utils/wardrobeEnums.js'

const props = defineProps({
	visible: {
		type: Boolean,
		default: false
	},
	item: {
		type: Object,
		default: () => ({})
	}
})

const emit = defineEmits(['update:visible', 'try-on', 'delete', 'update'])

const isEnter = ref(false)
const isLeave = ref(false)

const typeOptions = TYPE_OPTIONS
const colorOptions = COLOR_OPTIONS
const seasonOptions = SEASON_OPTIONS

const editName = ref('')
const editTypes = ref([])
const editColors = ref([])
const editSeasons = ref([])
const editFavourite = ref(0)
const openField = ref(null)

function parseMulti (str) {
	if (!str || typeof str !== 'string') return []
	return str.split(/[,/]+/).map(s => s.trim()).filter(Boolean)
}

const typeDisplayText = computed(() => codesToLabels(editTypes.value, TYPE_LABEL_BY_CODE))
const colorDisplayText = computed(() => codesToLabels(editColors.value, COLOR_LABEL_BY_CODE))
const seasonDisplayText = computed(() => codesToLabels(editSeasons.value, SEASON_LABEL_BY_CODE))

watch(() => props.item, (val) => {
	if (!val) return
	editName.value = val.name || ''
	editTypes.value = parseMulti(val.type)
	editColors.value = parseMulti(val.color)
	editSeasons.value = parseMulti(val.season)
	const f = val.favourite
	editFavourite.value = typeof f === 'number' && f >= 0 && f <= 3 ? f : 0
	openField.value = null
}, { immediate: true, deep: true })

watch(() => props.visible, (v) => {
	if (v) {
		isLeave.value = false
		nextTick(() => {
			isEnter.value = true
			editName.value = props.item?.name || ''
			editTypes.value = parseMulti(props.item?.type)
			editColors.value = parseMulti(props.item?.color)
			editSeasons.value = parseMulti(props.item?.season)
			const f = props.item?.favourite
			editFavourite.value = typeof f === 'number' && f >= 0 && f <= 3 ? f : 0
		})
	} else {
		isEnter.value = false
		isLeave.value = true
		openField.value = null
	}
}, { immediate: true })

const close = () => {
	isEnter.value = false
	isLeave.value = true
	setTimeout(() => {
		emit('update:visible', false)
		isLeave.value = false
	}, 280)
}

// DetailModal.vue - 修改 emitField 函数
const emitField = async (field, value) => {
  if (!props.item?.id) return
  
  let processedValue = value
  if (field === 'name') {
    processedValue = (value || '').trim()
  }
  
  await updateField(field, processedValue)
}

const toggleOption = (field, opt) => {
  const code = opt && typeof opt === 'object' && 'value' in opt ? opt.value : opt
  const arr = field === 'type' ? editTypes.value : 
              field === 'color' ? editColors.value : 
              editSeasons.value
  
  const i = arr.indexOf(code)
  if (i >= 0) {
    arr.splice(i, 1)
    console.log(`移除${field}:`, code, '当前数组:', arr)
  } else {
    arr.push(code)
    console.log(`添加${field}:`, code, '当前数组:', arr)
  }
}

// DetailModal.vue - 修改 applyField 函数
const applyField = async (field) => {
  if (!props.item?.id) return
  
  // 根据字段类型获取对应的数组
  let arr
  switch (field) {
    case 'type':
      arr = editTypes.value
      break
    case 'color':
      arr = editColors.value
      break
    case 'season':
      arr = editSeasons.value
      break
    default:
      return
  }
  
  // 将数组转换为逗号分隔的字符串
  const value = arr.join(',')
  
  // 如果值为空，设置为空字符串而不是跳过
  if (arr.length === 0) {
    await updateField(field, '')
    openField.value = null
    return
  }
  
  await updateField(field, value)
  openField.value = null
}

const updateField = async (field, value) => {
  try {
   uni.showLoading({
         title: '更新中...',
         mask: true
       })
       
       const token = uni.getStorageSync('auth_token')
       if (!token) {
         uni.showToast({
           title: '请先登录',
           icon: 'none'
         })
         return false
       }
    
    // 添加字段映射
    const fieldMapping = {
      'type': 'category',
      'color': 'color',
      'season': 'season',
      'name': 'name',
      'favourite': 'is_favorite'
    }
    
    const backendField = fieldMapping[field] || field
       
       const res = await new Promise((resolve, reject) => {
         uni.request({
           url: `http://localhost:8000/api/clothing/${props.item.id}?token=${encodeURIComponent(token)}`,
           method: 'PUT',
           header: {
             'Content-Type': 'application/x-www-form-urlencoded'
           },
           data: {
             [backendField]: value  // ✅ 使用映射后的字段名
           },
           success: resolve,
           fail: reject
         })
       })
    
    if (res.statusCode === 200 && res.data?.success) {
      // 更新成功后，通知父组件
      emit('update', { 
        id: props.item.id, 
        field, 
        value 
      })
	  
        if (field === 'type') {
		  editTypes.value = parseMulti(value)
		} else if (field === 'color') {
		  editColors.value = parseMulti(value)
		} else if (field === 'season') {
		  editSeasons.value = parseMulti(value)
		} else if (field === 'name') {
		  editName.value = value
		}
		
      // 根据字段显示不同的成功提示
      const fieldLabels = {
        'type': '类别',
        'color': '颜色',
        'season': '季节',
        'name': '名称',
        'favourite': '收藏等级'
      }
	  
	
      
      uni.showToast({
        title: `${fieldLabels[field] || field}更新成功`,
        icon: 'success',
        duration: 1200
      })
      
      return true
    } else {
      throw new Error(res.data?.message || '更新失败')
    }
  } catch (error) {
    console.error(`更新${field}失败:`, error)
    uni.showToast({
      title: error?.message || '网络请求失败',
      icon: 'none'
    })
    return false
  } finally {
    uni.hideLoading()
  }
}

// 添加清除所有选项的功能
const clearField = (field) => {
  switch (field) {
    case 'type':
      editTypes.value = []
      break
    case 'color':
      editColors.value = []
      break
    case 'season':
      editSeasons.value = []
      break
  }
}


const updateFavoriteLevel = async (clothingId, level) => {
  const token = uni.getStorageSync('auth_token')
  if (!token) {
    uni.showToast({
      title: '请先登录',
      icon: 'none'
    })
    return null
  }
  
  try {
    console.log('发送收藏请求:', {
      clothingId,
      level
    })
    
    const res = await new Promise((resolve, reject) => {
      uni.request({
        // ✅ 同时传递 token 和 target_level 作为 URL 查询参数
        url: `http://localhost:8000/api/clothing/${clothingId}/toggle-favorite?token=${encodeURIComponent(token)}&target_level=${level}`,
        method: 'POST',
        data: {},  // 空的请求体
        header: {
          'Content-Type': 'application/json'
          // ⚠️ 注意：这里不要加 Authorization header，因为 token 已经在 URL 中了
        },
        success: (res) => {
          console.log('收藏响应:', {
            statusCode: res.statusCode,
            data: res.data
          })
          resolve(res)
        },
        fail: (err) => {
          console.error('收藏请求失败:', err)
          reject(err)
        }
      })
    })
    
    if (res.statusCode === 200) {
      return res.data
    } else {
      throw new Error(res.data?.message || `请求失败: ${res.statusCode}`)
    }
    
  } catch (error) {
    console.error('API请求错误:', error)
    throw error
  }
}

// DetailModal.vue - 修改 setFavourite 函数
const setFavourite = async (level) => {
  if (!props.item?.id) {
    console.error('衣物ID不存在')
    return
  }
  
  const token = uni.getStorageSync('auth_token')
  if (!token) {
    uni.showToast({
      title: '请先登录',
      icon: 'none'
    })
    return
  }
  
  try {
    const next = editFavourite.value === level ? Math.max(0, level - 1) : level
    console.log('准备更新收藏:', {
      clothingId: props.item.id,
      currentLevel: editFavourite.value,
      targetLevel: next
    })
    
    uni.showLoading({
      title: '更新中...',
      mask: true
    })
    
    const response = await updateFavoriteLevel(props.item.id, next)
    console.log('更新收藏响应:', response)
    
    if (response && response.success === true) {
      // ✅ 关键修复：处理不同的后端返回格式
      let newLevel = 0
      
      // 情况1：后端返回 is_favorite（可能是0/1或true/false）
      if (response.data?.is_favorite !== undefined) {
        // 如果是布尔值，转换为0/1
        if (typeof response.data.is_favorite === 'boolean') {
          newLevel = response.data.is_favorite ? 1 : 0
        } else {
          // 如果是数字，直接使用
          newLevel = Number(response.data.is_favorite)
        }
      } 
      // 情况2：后端返回 favourite
      else if (response.data?.favourite !== undefined) {
        newLevel = Number(response.data.favourite)
      }
      // 情况3：后端返回 level
      else if (response.data?.level !== undefined) {
        newLevel = Number(response.data.level)
      }
      // 情况4：如果没有返回等级，使用我们发送的目标等级
      else {
        newLevel = next
      }
      
      // 确保值在0-3范围内
      newLevel = Math.min(3, Math.max(0, newLevel))
      
      console.log('处理后的收藏等级:', newLevel)
      
      // 更新本地状态
      editFavourite.value = newLevel
      
      // 通知父组件更新
      emit('update', { 
        id: props.item.id, 
        field: 'favourite', 
        value: newLevel 
      })
	  
	  console.log('更新完成:', {
	    clothingId: props.item.id,
	    currentLevel: editFavourite.value,
	  })
      
      const favoriteLabels = {
        0: '不喜欢',
        1: '一般',
        2: '喜欢',
        3: '非常喜欢'
      }
      uni.showToast({
        title: favoriteLabels[newLevel] || '更新成功',
        icon: 'success',
        duration: 1200
      })
    }
  } catch (error) {
    console.error('更新收藏等级失败:', error)
    uni.showToast({
      title: error?.message || '网络请求失败',
      icon: 'none'
    })
  } finally {
    uni.hideLoading()
  }
}
const handleTryOn = () => {
	emit('try-on', props.item)
}

const handleDelete = async () => {
  try {
    const result = await uni.showModal({
      title: '确认删除',
      content: '确定要删除这件衣物吗？',
      confirmText: '删除',
      confirmColor: '#ff4444',
      cancelText: '取消'
    })
    
    if (result.confirm) {
      emit('delete', props.item.id)
    }
  } catch (error) {
    console.error('删除确认失败:', error)
  }
}
</script>

<style scoped>
.modal-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.4);
	backdrop-filter: blur(4px);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 999;
	animation: mask-fade-in 0.28s ease;
}

@keyframes mask-fade-in {
	from { opacity: 0; }
	to { opacity: 1; }
}

.modal-wrap {
	width: 92%;
	max-width: 820px;
	max-height: 92vh;
	display: flex;
	justify-content: center;
	align-items: center;
	transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1),
	            opacity 0.28s ease;
}

.modal-wrap.modal-enter {
	animation: modal-zoom-in 0.32s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.modal-wrap.modal-leave {
	animation: modal-zoom-out 0.24s ease forwards;
}

@keyframes modal-zoom-in {
	from {
		opacity: 0;
		transform: scale(0.92) translateY(20rpx);
	}
	to {
		opacity: 1;
		transform: scale(1) translateY(0);
	}
}

@keyframes modal-zoom-out {
	from {
		opacity: 1;
		transform: scale(1) translateY(0);
	}
	to {
		opacity: 0;
		transform: scale(0.95) translateY(16rpx);
	}
}

.modal-content {
	width: 100%;
	max-height: 92vh;
	overflow-y: auto;
	background-color: #FDFBF7;
	border-radius: 24rpx;
	padding: 48rpx 48rpx 5rpx 48rpx;
	position: relative;
	box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.12);
	border: 2rpx solid rgba(0, 0, 0, 0.08);
}

.dropdown-backdrop {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 5;
	cursor: default;
}

.modal-head {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 88rpx;
	display: flex;
	justify-content: flex-end;
	align-items: center;
	padding: 0 24rpx;
	z-index: 6;
}

.close-btn {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
}

.icon-close {
	width: 44rpx;
	height: 44rpx;
}

.modal-body {
	display: flex;
	margin-top: 24rpx;
	gap: 40rpx;
}

.image-section {
	flex: 1;
	min-width: 0;
	width: 0;
	aspect-ratio: 4 / 5;
	border-radius: 16rpx;
	overflow: hidden;
	background: #F5F0E6;
}

.image-section .main-img {
	width: 100%;
	height: 100%;
	display: block;
	object-fit: cover;
}

.info-section {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	justify-content: center;
	font-family: "Bodoni MT", "Noto Serif", "Songti SC", serif;
}

.info-row {
	display: flex;
	align-items: center;
	margin-bottom: 22rpx;
	font-size: 32rpx;
	color: #1D1D1F;
	line-height: 1.45;
}

.info-row .label {
	font-weight: 600;
	margin-right: 12rpx;
	flex-shrink: 0;
}

.info-row .value {
	font-weight: 400;
}

.info-input {
	flex: 1;
	min-width: 0;
	font-size: 32rpx;
	color: #1D1D1F;
	font-weight: 400;
	font-family: "Bodoni MT", "Noto Serif", "Songti SC", serif;
	background: transparent;
	border: none;
	border-bottom: 1rpx solid transparent;
	border-radius: 0;
	padding: 4rpx 0;
	outline: none;
	transition: border-color 0.2s;
}

.info-input:focus {
	border-bottom-color: rgba(29, 29, 31, 0.25);
}

.info-input::placeholder {
	color: #AAA;
}

.info-row-select {
	position: relative;
	align-items: flex-start;
}

.info-row-favourite {
	align-items: center;
}

.hearts {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.heart-wrap {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 8rpx;
	cursor: pointer;
	transition: transform 0.2s, opacity 0.2s;
}

.heart-wrap:active {
	transform: scale(0.92);
	opacity: 0.85;
}

.heart-icon {
	width: 40rpx;
	height: 40rpx;
}

.select-trigger {
	display: flex;
	align-items: flex-start;
	gap: 8rpx;
	min-height: 44rpx;
	padding: 6rpx 12rpx;
	margin: -6rpx -12rpx;
	border-radius: 12rpx;
	cursor: pointer;
	transition: background 0.2s;
	flex: 1;
	min-width: 0;
}

.select-trigger:active {
	background: rgba(0, 0, 0, 0.05);
}

.select-value {
	flex: 1;
	min-width: 0;
	font-weight: 400;
	color: #1D1D1F;
	white-space: normal;
	word-break: break-word;
	line-height: 1.45;
}

.select-arrow {
	width: 24rpx;
	height: 24rpx;
	flex-shrink: 0;
	opacity: 0.6;
}

.select-dropdown {
	position: absolute;
	left: 0;
	right: 0;
	top: 100%;
	margin-top: 8rpx;
	background: #FFF;
	border-radius: 16rpx;
	padding: 16rpx;
	box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
	border: 2rpx solid #E8E4DC;
	z-index: 10;
	max-height: 280rpx;
	overflow-y: auto;
}

.select-option {
	padding: 16rpx 20rpx;
	font-size: 28rpx;
	color: #1D1D1F;
	border-radius: 12rpx;
	margin-bottom: 4rpx;
	transition: background 0.2s;
	cursor: pointer;
}

.select-option:last-of-type {
	margin-bottom: 0;
}

.select-option.active {
	background: #FFF9F1;
	font-weight: 600;
}

.select-apply {
	margin-top: 16rpx;
	padding: 16rpx;
	text-align: center;
	font-weight: 600;
	font-size: 28rpx;
	color: #9D8B70;
	background: #F5F0E6;
	border-radius: 12rpx;
	cursor: pointer;
	transition: opacity 0.2s;
}

.select-apply:active {
	opacity: 0.85;
}

.tags-section {
	margin-top: 32rpx;
}

.tags-title {
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 26rpx;
	color: #1D1D1F;
	margin-bottom: 16rpx;
	display: block;
}

.tags-list {
	display: flex;
	gap: 16rpx;
	flex-wrap: wrap;
}

.tag-placeholder {
	width: 80rpx;
	aspect-ratio: 4 / 5;
	background-color: #E8E4DC;
	border-radius: 8rpx;
}

.action-bar {
	display: flex;
	border-top: 2rpx solid rgba(0, 0, 0, 0.12);
	margin-top: 52rpx;
	padding-top: 0;
}

.action-bar .btn {
	flex: 1;
	text-align: center;
	padding: 28rpx 0;
	font-family: "Didot", "Bodoni MT", "Noto Serif", "Songti SC", serif;
	font-size: 30rpx;
	cursor: pointer;
	transition: background 0.2s ease;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
}

.action-bar .btn:active {
	opacity: 0.85;
}

.try-on-btn {
	border-right: 2rpx solid rgba(0, 0, 0, 0.12);
	font-weight: 600;
	color: #1D1D1F;
}

.icon-camera {
	width: 36rpx;
	height: 36rpx;
}

.delete-btn {
	color: #1D1D1F;
	font-weight: 600;
}
</style>
