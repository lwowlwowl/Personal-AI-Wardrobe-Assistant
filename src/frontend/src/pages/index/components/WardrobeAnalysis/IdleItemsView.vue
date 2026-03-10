<template>
	<scroll-view class="expanded-page" scroll-y>
		<view class="expanded-content">
			<view class="expanded-header">
				<view class="back-btn" @click="emit('back')">
					<text class="back-arrow">��</text>
					<text class="back-text">Back</text>
				</view>
				<text class="expanded-title">Idle Items</text>
			</view>

			<view class="card summary-card">
				<text class="summary-stat">{{ stats.idle_items || unwornCount }}</text>
				<text class="summary-desc">unworn items out of {{ stats.total_items || 106 }} total ({{ idleRate }}% idle rate)</text>
			</view>

			<view class="card list-card">
				<text class="card-label">All idle items</text>
				<view class="filter-section">
					<text class="filter-section-label">Time</text>
					<view class="filter-chips">
						<view
							v-for="f in timeFilters"
							:key="'time-' + f.value"
							class="filter-chip"
							:class="{ active: activeTimeFilter === f.value }"
							@click="activeTimeFilter = f.value"
						>
							<text class="filter-chip-text">{{ f.label }}</text>
						</view>
					</view>
				</view>
				<view class="filter-section">
					<text class="filter-section-label">Season</text>
					<view class="filter-chips">
						<view
							v-for="f in seasonFilters"
							:key="'season-' + f.value"
							class="filter-chip"
							:class="{ active: activeSeasonFilter === f.value }"
							@click="activeSeasonFilter = f.value"
						>
							<text class="filter-chip-text">{{ f.label }}</text>
						</view>
					</view>
				</view>
				<view v-if="listReady && filteredItems.length > 0">
				<TransitionGroup name="list" tag="view" class="idle-list" appear>
					<view
						v-for="(item, index) in filteredItems"
						:key="item.name + '-' + item.season + '-' + item.type"
						class="idle-item-card"
						:style="{ '--stagger-delay': index * 100 + 'ms' }"
					>
						<view class="idle-item-thumb" :style="{ background: item.dotColor }">
							<image v-if="item.image" :src="item.image" mode="aspectFill" class="thumb-img" />
						</view>
						<view class="idle-item-content">
							<view class="idle-item-header">
								<view class="idle-status-badge" :class="'status-' + item.status.level">
									<view class="status-dot"></view>
									<text class="status-label">{{ item.status.label }}</text>
								</view>
							</view>
							<text class="idle-name">{{ item.name }}</text>
							<view class="idle-meta-wrap">
								<text class="idle-meta-label">Last worn:</text>
								<text class="idle-meta-value" :class="'meta-' + item.status.level">{{ item.lastWornDisplay }}</text>
							</view>
						</view>
						<view class="idle-item-action" hover-class="idle-item-action-hover" @click="wearToday(item)">
							<text class="action-icon"></text>
							<text class="action-text">Try today</text>
						</view>
					</view>
				</TransitionGroup>
				</view>
				<view v-else-if="listReady && filteredItems.length === 0 && unwornCount === 0" class="empty-state">
					<view class="empty-state-illus"></view>
					<text class="empty-state-title">Your wardrobe is well utilized!</text>
					<text class="empty-state-desc">No idle items today.</text>
				</view>
				<view v-else-if="listReady && filteredItems.length === 0 && unwornCount > 0" class="empty-state empty-state-filter">
					<view class="empty-state-illus"></view>
					<text class="empty-state-title">No items match your filters</text>
					<text class="empty-state-desc">Try changing Time or Season to see idle items.</text>
				</view>
				<view v-else class="idle-list idle-list-placeholder" style="min-height: 200rpx"></view>
			</view>
		</view>
	</scroll-view>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { TransitionGroup } from 'vue'
import { COLOR_HEX_BY_CODE } from '@/utils/wardrobeEnums.js'
import { SEASON_OPTIONS } from '@/utils/wardrobeEnums.js'

const BASE_URL = 'http://localhost:8000'
// ��ȡtoken�ĸ�������
function getToken() {
    // ���Զ�����ܵ�key
    const possibleKeys = ['auth_token', 'token', 'access_token', 'userToken']
    
    for (const key of possibleKeys) {
        const token = uni.getStorageSync(key)
        if (token) {
            console.log(`�� ${key} ��ȡ��token:`, token.substring(0, 20) + '...')
            return token
        }
    }
    
    console.log('���п��ܵ�key��û���ҵ�token')
    return null
}

// ����¼״̬
function checkLoginStatus() {
  const token = getToken()
  if (!token) {
    console.error('δ��⵽token����ת��¼ҳ')
    uni.showModal({
      title: 'δ��¼',
      content: '���ȵ�¼',
      success: (res) => {
        if (res.confirm) {
          goToLogin()
        }
      }
    })
    return false
  }
  return true
}

// ��ת����¼ҳ
function goToLogin() {
  // ���浱ǰҳ�棬��¼����Է���  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  if (currentPage) {
    uni.setStorageSync('redirectUrl', currentPage.route)
  }
  
  uni.navigateTo({
    url: '/pages/login/login'
  })
}

// �޸�request���������Ӹ���ϸ�Ĵ�����
// �޸�ԭ���� request ���������� method ����
async function request(url, params = {}, method = 'GET') {
  try {
    // �ȼ���¼״̬
    if (!checkLoginStatus()) {
      throw new Error('Please log in')
    }
    
    const token = getToken()
    
    // ������������
    let fullUrl = `${BASE_URL}${url}`
    let requestOptions = {
      method: method,
      header: {
        'Content-Type': 'application/json'
      }
    }
    
    if (method === 'GET') {
      // GET ���󣺲������� URL ��ѯ�ַ���
      const queryParams = new URLSearchParams()
      queryParams.append('token', token)
      
      Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
          queryParams.append(key, params[key])
        }
      })
      
      const queryString = queryParams.toString()
      fullUrl = queryString ? `${fullUrl}?${queryString}` : fullUrl
      
    } else {
      // POST/PUT/DELETE ����token ���ڲ�ѯ���������ݷ��� body
      const queryParams = new URLSearchParams()
      queryParams.append('token', token)
      fullUrl = `${fullUrl}?${queryParams.toString()}`
      
      // ����в�������Ϊ�����巢��      if (Object.keys(params).length > 0) {
        requestOptions.data = params
    
    }
    
    console.log(`�������� [${method}]:`, fullUrl)
    console.log('ʹ�õ�token:', token.substring(0, 20) + '...')
    if (method !== 'GET') {
      console.log('������:', requestOptions.data)
    }
    
    const res = await uni.request({
      url: fullUrl,
      ...requestOptions
    })
    
    console.log('��Ӧ״̬��:', res.statusCode)
    console.log('��Ӧ����:', res.data)
    
    if (res.statusCode === 401) {
      console.error('401δ��Ȩ�����token����ת��¼')
      uni.removeStorageSync('auth_token')
      checkLoginStatus()
      throw new Error('��¼�ѹ��ڣ������µ�¼')
    }
    
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return res.data
    } else {
      throw new Error(res.data?.message || `����ʧ��: ${res.statusCode}`)
    }
  } catch (error) {
    console.error('����ʧ��:', error)
    throw error
  }
}

// ��ӿ�ݷ���
async function requestGet(url, params = {}) {
  return request(url, params, 'GET')
}

async function requestPost(url, data = {}) {
  return request(url, data, 'POST')
}

async function requestPut(url, data = {}) {
  return request(url, data, 'PUT')
}

async function requestDelete(url, params = {}) {
  return request(url, params, 'DELETE')
}

// �������API
const analysisApi = {
	// ��ȡ�����ʸ���
	getIdleRate(days = 30) {
		return request('/api/analysis/idle-rate', { days })
	},
	
	// ��ȡ������Ʒ�����б�
	getIdleItems(params) {
		const {
			page = 1,
			pageSize = 20,
			timeFilter = null,
			seasonFilter = null
		} = params
		
		const requestParams = {
			page,
			page_size: pageSize
		}
		
		if (timeFilter && timeFilter !== 'all') {
			requestParams.time_filter = timeFilter
		}
		
		if (seasonFilter && seasonFilter !== 'all') {
			requestParams.season_filter = seasonFilter
		}
		
		return request('/api/analysis/idle-items/detail', requestParams)
	}
}

const clothingApi = {
	// ��¼���� - ע�������� POST ����
	recordWear(clothingId) {
		// �޸ģ�ʹ�� POST ������������Ҫ���ݿ����ݻ���ȷ��������
		return requestWithMethod(`/api/clothing/${clothingId}/record-wear`, 'POST', {})
	}
}

const props = defineProps({
	unwornCount: { type: Number, default: 3 }
})
const emit = defineEmits(['back'])

// ============ ״̬���� ============
const loading = ref(true)
const error = ref('')
const listLoading = ref(false)

// ͳ������
const stats = ref({
	total_items: 0,
	idle_items: 0,
	idle_rate: 0,
	most_idle_items: []
})

// ��ҳ
const currentPage = ref(1)
const pageSize = ref(20)
const hasMore = ref(false)
const totalPages = ref(1)

const idleRatePercent = computed(() => Math.round((props.unwornCount / 106) * 100))

const idleItems = ref([])

/** Idle status: only Never worn or Over a year (no 5 weeks, 2 months, etc.) */
// �޸� getIdleStatus ����
function getIdleStatus(item) {
  console.log('������Ʒ����״̬:', {
    id: item.id,
    name: item.name,
    wear_count: item.wear_count,
    last_worn_date: item.last_worn_date
  })
  
  if (item.wear_count === 0) {
    console.log('�� ״̬: never (��δ����)')
    return { level: 'never', label: 'Never worn' }
  }
  
  if (item.last_worn_date) {
    const lastWorn = new Date(item.last_worn_date)
    const now = new Date()
    const monthsDiff = (now.getFullYear() - lastWorn.getFullYear()) * 12 + 
                      (now.getMonth() - lastWorn.getMonth())
    
    console.log('���������', item.last_worn_date)
    console.log('�������', monthsDiff)
    
    if (monthsDiff >= 12) {
      console.log('�� ״̬: over_year (����һ��)')
      return { level: 'over_year', label: 'Over a year ago' }
    }
  } else {
    console.log('last_worn_date Ϊ null')
  }
  
  console.log('�� ״̬: within_year (һ����)')
  return { level: 'within_year', label: 'Within a year' }
}

/** Last worn display: Never for never worn, raw value (e.g. 14 months ago) for over a year */
function getLastWornDisplay(item, status) {
	if (status.level === 'never') return 'Never'
	if (status.level === 'over_year' && item.last_worn_date) {
		const lastWorn = new Date(item.last_worn_date)
		const now = new Date()
		const monthsDiff = (now.getFullYear() - lastWorn.getFullYear()) * 12 + 
						  (now.getMonth() - lastWorn.getMonth())
		return `${monthsDiff} months ago`
	}
	return ''
}

// ============ API���� ============
async function fetchData() {
	loading.value = true
	error.value = ''
	
	try {
		// ���л�ȡ�������ݺ��б�����
		const [statsRes, listRes] = await Promise.all([
			fetchIdleRate(),
			fetchIdleItems(1)
		])
		
		if (!statsRes?.success) {
			throw new Error(statsRes?.message || '��ȡͳ������ʧ��')
		}
		
		if (!listRes?.success) {
			throw new Error(listRes?.message || '��ȡ��Ʒ�б�ʧ��')
		}
		
	} catch (err) {
		console.error('���ݼ���ʧ��:', err)
		error.value = err.message || '����ʧ�ܣ�������'
	} finally {
		loading.value = false
	}
}

async function fetchIdleRate() {
	try {
		const res = await analysisApi.getIdleRate(30)
		if (res.success) {
			stats.value = res.data
		}
		return res
	} catch (err) {
		console.error('��ȡ������ʧ��:', err)
		throw err
	}
}

// ���ͼƬURL������
function getFullImageUrl(imageUrl) {
  if (!imageUrl) return null
  
  // �Ѿ�������URL
  if (imageUrl.startsWith('http')) return imageUrl
  
  // �������/Personal-AI-Wardrobe-Assistant ��ͷ��·��
  if (imageUrl.startsWith('/Personal-AI-Wardrobe-Assistant')) {
    return `${BASE_URL}${imageUrl}`
  }
  
  // �������/uploads ��ͷ��·��
  if (imageUrl.startsWith('/uploads')) {
    return `${BASE_URL}${imageUrl}`
  }
  
  // ��������·�����������ϴ�Ŀ¼�µ��ļ�
  return `${BASE_URL}/Personal-AI-Wardrobe-Assistant/uploads/${imageUrl}`
}

async function fetchIdleItems(page = 1, append = false) {
  console.log(`\n=== fetchIdleItems ��ʼ, page=${page}, append=${append} ===`)
  
  listLoading.value = true
  
  try {
    let timeFilter = activeTimeFilter.value
    if (timeFilter === 'all') timeFilter = null
    
    const res = await analysisApi.getIdleItems({
      page,
      pageSize: pageSize.value,
      timeFilter,
      seasonFilter: activeSeasonFilter.value !== 'all' ? activeSeasonFilter.value : null
    })
    
    console.log('fetchIdleItems �յ���Ӧ:', res)
    
    if (res && res.success) {
      const items = (res.data?.items || []).map(item => {
        // ���� dotColor���Ӽ���ӳ�䣩
        const seasonColorMap = {
          'spring': '#A8E6CF',  // ����
          'summer': '#FFD93D',  // ����
          'autumn': '#B85C3A',  // ����
          'winter': '#96C3EB',  // ����
          'all': '#B0B0B0'      // ��ɫ
        }
        
        //  ��ӡÿ����Ʒ��ͼƬ��Ϣ
        console.log('��Ʒ����:', {
          id: item.id,
          name: item.name,
          image_url: item.image_url,
          image: item.image,
          fullImageUrl: item.image_url ? `${BASE_URL}${item.image_url}` : null
        })
		
		// ����ͼƬURL
		const fullImageUrl = getFullImageUrl(item.image_url)
			console.log('ͼƬURL����:', {
			original: item.image_url,
			full: fullImageUrl
		})
        
        return {
          ...item,
          // �ֶ�ӳ�䣺���image_url �� ǰ�� image
          image: fullImageUrl,  //  �ؼ���ӳ��ͼƬ�ֶ�
          // ����ֱ��ƴ������URL
          // image: item.image_url ? `${BASE_URL}${item.image_url}` : null,
          // ���dotColor��������û���ṩ��
          dotColor: item.dotColor || seasonColorMap[item.season] || '#f0f0f0',
          // ȷ����Щ�ֶδ���
          lastWorn: item.last_worn_date,
          wearCount: item.wear_count
        }
      })
      
      console.log('������items:', items.map(i => ({
        name: i.name,
        hasImage: !!i.image,
        imageUrl: i.image
      })))
      
      const pagination = res.data?.pagination || {}
      
      if (append) {
        idleItems.value = [...idleItems.value, ...items]
      } else {
        idleItems.value = items
      }
      
      currentPage.value = pagination.page || page
      totalPages.value = pagination.total_pages || 1
      hasMore.value = currentPage.value < totalPages.value
    }
    
    return res
  } catch (err) {
    console.error('fetchIdleItems �쳣:', err)
    throw err
  } finally {
    listLoading.value = false
  }
}

// ============ �¼����� ============
async function handleTimeFilterChange(value) {
	activeTimeFilter.value = value
	await fetchIdleItems(1, false)
}

async function handleSeasonFilterChange(value) {
	activeSeasonFilter.value = value
	await fetchIdleItems(1, false)
}

async function loadMore() {
	if (!hasMore.value || listLoading.value) return
	
	const nextPage = currentPage.value + 1
	await fetchIdleItems(nextPage, true)
}

const idleItemsWithStatus = computed(() =>
  idleItems.value.map((item) => {
    // Ӧ�ô�������item����
    const status = getIdleStatus(item)  // ��Ϊ���� item
    return { 
      ...item, 
      status, 
      lastWornDisplay: getLastWornDisplay(item, status),  // ͬ����Ҫ�޸�
      sortOrder: getSortOrder(item.last_worn_date)  // ʹ����ȷ���ֶ���
    }
  })
  .filter((item) => item.status.level !== 'within_year')
)

/** ����˳��Never = 0�������ȣ���Ȼ��ʱ�䵹�� */
function getSortOrder(lastWorn) {
	if (!lastWorn || lastWorn === '��') return 0
	const months = lastWorn.match(/(\d+)\s*month/i)?.[1]
	const weeks = lastWorn.match(/(\d+)\s*week/i)?.[1]
	if (months) return parseInt(months) * 4
	if (weeks) return parseInt(weeks)
	return 999
}

/** Time filter: All / Never worn / Over a year */
const timeFilters = [
	{ label: 'All', value: 'all' },
	{ label: 'Never worn', value: 'never' },
	{ label: 'Over a year', value: 'over_year' }
]

const activeTimeFilter = ref('all')

/** Season filter: All / Spring / Summer / Autumn / Winter */
const seasonFilters = [
	{ label: 'All', value: 'all' },
	...SEASON_OPTIONS.map((o) => ({ label: o.label, value: o.value }))
]
const activeSeasonFilter = ref('all')

const listReady = ref(false)

watch([activeTimeFilter, activeSeasonFilter], () => {
	// ɸѡ�仯ʱ���õ���һҳ
	fetchIdleItems(1, false)
})

function setMockData() {
  console.log('����mock����...')
  
  // ����mock����
  const mockItems = [
    { 
      id: 1,
      name: 'Olive Cargo Pants', 
      color: 'olive', 
      season: 'autumn', 
      type: 'bottoms',
      wear_count: 0,
      last_worn_date: null,
      dotColor: '#808000'
    },
    { 
      id: 2,
      name: 'Navy Blazer', 
      color: 'navy', 
      season: 'winter', 
      type: 'outerwear',
      wear_count: 0,
      last_worn_date: null,
      dotColor: '#000080'
    },
    { 
      id: 3,
      name: 'Black Tailored Trousers', 
      color: 'black', 
      season: 'autumn', 
      type: 'bottoms',
      wear_count: 0,
      last_worn_date: null,
      dotColor: '#000000'
    },
    { 
      id: 4,
      name: 'Brown Cardigan', 
      color: 'brown', 
      season: 'winter', 
      type: 'outerwear',
      wear_count: 5,
      last_worn_date: '2023-01-15',
      dotColor: '#8B4513'
    },
    { 
      id: 5,
      name: 'Wool Coat', 
      color: 'navy', 
      season: 'winter', 
      type: 'outerwear',
      wear_count: 3,
      last_worn_date: '2022-11-20',
      dotColor: '#000080'
    },
    { 
      id: 6,
      name: 'Leather Jacket', 
      color: 'brown', 
      season: 'autumn', 
      type: 'outerwear',
      wear_count: 2,
      last_worn_date: '2022-10-10',
      dotColor: '#8B4513'
    }
  ]
  
  idleItems.value = mockItems
  console.log('mock����������ɣ���Ʒ����', idleItems.value.length)
  listReady.value = true
}

onMounted(() => {
	setMockData()
	fetchData()
})

const idleRate = computed(() => {
	if (stats.value.total_items === 0) return 0
	return Math.round((stats.value.idle_items / stats.value.total_items) * 100)
})

const filteredItems = computed(() => {
	if (props.unwornCount === 0) return []
	let list = [...idleItemsWithStatus.value]
	
	if (activeTimeFilter.value === 'never') {
		list = list.filter((item) => item.status.level === 'never')
	} else if (activeTimeFilter.value === 'over_year') {
		list = list.filter((item) => item.status.level === 'over_year')
	}
	
	if (activeSeasonFilter.value !== 'all') {
		list = list.filter((item) => item.season === activeSeasonFilter.value)
	}
	
	list = list.sort((a, b) => b.sortOrder - a.sortOrder)
	return list
})

async function wearToday(item) {
	console.log('=== ���Լ�¼���� ===')
	console.log('��Ʒ��Ϣ:', {
		id: item.id,
		name: item.name,
		current_wear_count: item.wear_count,
		last_worn: item.last_worn_date
	})
	
	try {
		// ����¼״̬
		if (!checkLoginStatus()) {
			console.log('δ��¼���޷���¼')
			return
		}
		
		// ��ʾ������
		uni.showLoading({
			title: '��¼��...',
			mask: true
		})
		
		// ���ú��API
		console.log(`����API: /api/clothing/${item.id}/record-wear`)
		const res = await clothingApi.recordWear(item.id)
		console.log('API��Ӧ:', res)
		
		if (res && res.success) {
			uni.hideLoading()
			uni.showToast({
				title: `�Ѽ�¼ "${item.name}"`,
				icon: 'success',
				duration: 2000
			})
			
			// ���±�������
			console.log('��¼�ɹ���ˢ���б�')
			await updateItemAfterWear(item.id)
			
		} else {
			throw new Error(res?.message || '��¼ʧ��')
		}
		
	} catch (error) {
		console.error('��¼����ʧ��:', error)
		uni.hideLoading()
		uni.showModal({
			title: '��¼ʧ��',
			content: error.message || '���Ժ�����',
			showCancel: false
		})
	}
}

async function updateItemAfterWear(clothingId) {
	try {
		// ���»�ȡ��ǰҳ�����ݣ�ȷ���������£�
		await fetchIdleItems(currentPage.value, false)
		
		// ��ѡ��ͬʱ����ͳ�����ݣ������ʵȣ�
		await fetchIdleRate()
		
	} catch (error) {
		console.error('���±�������ʧ��:', error)
	}
}

</script>

<style scoped>
.expanded-page {
	background: #F6F5F1;
	height: 100vh;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	box-sizing: border-box;
}
.expanded-content {
	padding: 24rpx 30rpx 40rpx;
}

.expanded-header {
	display: flex;
	align-items: center;
	gap: 20rpx;
	margin-bottom: 28rpx;
}

.back-btn {
	display: inline-flex;
	align-items: center;
	gap: 6rpx;
	padding: 10rpx 16rpx;
	border-radius: 14rpx;
	background: rgba(0, 0, 0, 0.04);
	transition: background 0.2s ease, transform 0.15s ease;
}
.back-btn:active { transform: scale(0.98); }

.back-arrow { font-size: 28rpx; color: #1d1d1f; font-weight: 600; }
.back-text { font-size: 26rpx; color: #1d1d1f; font-weight: 600; }

.expanded-title {
	font-size: 36rpx;
	font-weight: 800;
	color: #1d1d1f;
	letter-spacing: 0.02em;
}

.card {
	background: #FFFEFB;
	border-radius: 32rpx;
	padding: 28rpx 32rpx;
	box-shadow: 0 6rpx 24rpx rgba(0, 0, 0, 0.06), 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
	margin-bottom: 24rpx;
	transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.summary-card {
	text-align: center;
	padding: 32rpx;
}
.summary-stat {
	font-size: 64rpx;
	font-weight: 800;
	color: #1d1d1f;
	display: block;
	line-height: 1.2;
}
.summary-desc {
	font-size: 26rpx;
	color: #777;
	margin-top: 10rpx;
	display: block;
}

.card-label {
	font-size: 30rpx;
	font-weight: 700;
	color: #1d1d1f;
	margin-bottom: 20rpx;
	display: block;
}

.filter-section {
	margin-bottom: 20rpx;
}
.filter-section:last-of-type {
	margin-bottom: 24rpx;
	padding-bottom: 20rpx;
	border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
}
.filter-section-label {
	font-size: 24rpx;
	color: #888;
	font-weight: 600;
	display: block;
	margin-bottom: 12rpx;
}
.filter-chips {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
}
.filter-chip {
	padding: 5rpx 20rpx;
	border-radius: 24rpx;
	background: rgba(0, 0, 0, 0.04);
	border: 1rpx solid transparent;
	transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
	cursor: pointer;
}
.filter-chip:active { transform: scale(0.98); }
.filter-chip.active {
	background: rgba(184, 107, 31, 0.15);
	border-color: rgba(184, 107, 31, 0.3);
}
.filter-chip-text {
	font-size: 26rpx;
	font-weight: 600;
	color: #1d1d1f;
}
.filter-chip.active .filter-chip-text {
	color: #7a4e18;
}

.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 60rpx 40rpx;
	text-align: center;
}
.empty-state-illus {
	font-size: 80rpx;
	line-height: 1;
	margin-bottom: 24rpx;
	width: 120rpx;
	height: 120rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: linear-gradient(135deg, rgba(184, 107, 31, 0.08) 0%, rgba(184, 107, 31, 0.04) 100%);
	border-radius: 50%;
}
.empty-state-title {
	font-size: 32rpx;
	font-weight: 700;
	color: #1d1d1f;
	line-height: 1.4;
	margin-bottom: 12rpx;
}
.empty-state-desc {
	font-size: 26rpx;
	color: #777;
	line-height: 1.5;
}

.idle-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	position: relative;
}
.idle-item-card {
	display: flex;
	align-items: center;
	gap: 20rpx;
	padding: 24rpx;
	background: #FFFEFB;
	border-radius: 24rpx;
	border: 1rpx solid rgba(0, 0, 0, 0.06);
	box-shadow: 0 6rpx 20rpx rgba(0, 0, 0, 0.06), 0 2rpx 6rpx rgba(0, 0, 0, 0.03);
	transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}
.idle-item-card:hover {
	background: #FFFEFB;
	transform: translateY(-6rpx);
	box-shadow: 0 12rpx 36rpx rgba(0, 0, 0, 0.08), 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.idle-item-thumb {
	width: 120rpx;
	height: 120rpx;
	border-radius: 12rpx;
	flex-shrink: 0;
	background: #f0f0f0;
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
}
.thumb-img {
	width: 100%;
	height: 100%;
}

.idle-item-content {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}
.idle-item-header {
	margin-bottom: 4rpx;
}
.idle-status-badge {
	display: inline-flex;
	align-items: center;
	gap: 8rpx;
	padding: 6rpx 12rpx;
	border-radius: 14rpx;
	font-size: 22rpx;
	font-weight: 500;
}
.status-dot {
	width: 8rpx;
	height: 8rpx;
	border-radius: 50%;
}
.status-never .status-dot {
	background: rgba(180, 120, 120, 0.8);
}
.status-over_year .status-dot {
	background: rgba(140, 120, 160, 0.8);
}
.status-label { font-size: 22rpx; }
.status-never {
	background: rgba(220, 180, 180, 0.2);
	color: #a06767;
}
.status-over_year {
	background: rgba(200, 180, 220, 0.2);
	color: #7a6a8a;
}

.idle-name {
	font-size: 28rpx;
	font-weight: 700;
	color: #1d1d1f;
	line-height: 1.3;
	margin-bottom: 4rpx;
}
.idle-meta-wrap {
	display: flex;
	align-items: baseline;
	gap: 8rpx;
	margin-top: 6rpx;
}
.idle-meta-label {
	font-size: 24rpx;
	color: #888;
	font-weight: 500;
}
.idle-meta-value {
	font-size: 26rpx;
	font-weight: 700;
	padding: 4rpx 10rpx;
	border-radius: 8rpx;
}
.meta-never {
	color: #a06767;
	background: rgba(220, 180, 180, 0.15);
}
.meta-over_year {
	color: #7a6a8a;
	background: rgba(200, 180, 220, 0.15);
}

.idle-item-action {
	display: inline-flex;
	align-items: center;
	gap: 8rpx;
	padding: 10rpx 16rpx;
	background: transparent;
	border: 1rpx solid rgba(184, 107, 31, 0.2);
	border-radius: 16rpx;
	flex-shrink: 0;
	transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}
.idle-item-action:hover,
.idle-item-action-hover {
	background: #8a6b3a;
	border-color: #8a6b3a;
}
.idle-item-action:hover .action-icon,
.idle-item-action:hover .action-text,
.idle-item-action-hover .action-icon,
.idle-item-action-hover .action-text {
	color: #fff;
	opacity: 1;
}
.idle-item-action:active {
	background: rgba(184, 107, 31, 0.06);
	border-color: rgba(184, 107, 31, 0.3);
	transform: scale(0.98);
}
.idle-item-action:active:hover,
.idle-item-action-hover:active {
	background: #7a5e32;
	border-color: #7a5e32;
}
.action-icon {
	font-size: 20rpx;
	color: #9a7b4a;
	opacity: 0.85;
	transition: color 0.2s ease, opacity 0.2s ease;
}
.action-text {
	font-size: 24rpx;
	font-weight: 500;
	color: #8a6b3a;
	white-space: nowrap;
	transition: color 0.2s ease, opacity 0.2s ease;
}

/* TransitionGroup: stagger enter + smooth rearrange (use :deep for scoped) */
:deep(.list-enter-active),
:deep(.list-appear-active),
:deep(.list-leave-active) {
	transition: opacity 400ms ease, transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1);
}
:deep(.list-enter-active),
:deep(.list-appear-active) {
	transition-delay: var(--stagger-delay);
}
:deep(.list-enter-from),
:deep(.list-appear-from),
:deep(.list-leave-to) {
	opacity: 0;
	transform: translateY(12rpx);
}
:deep(.list-move) {
	transition: transform 400ms ease;
}
:deep(.list-leave-active) {
	position: absolute;
	width: calc(100% - 0rpx);
}
</style>