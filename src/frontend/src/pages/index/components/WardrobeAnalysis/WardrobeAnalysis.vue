<template>
	<view class="page">
		<!-- 展开视图：Activity report / Idle items（页面切换过渡） -->
		<transition name="page" mode="out-in">
			<ActivityReport v-if="expandedView === 'activity-report'" key="activity-report" :trend-value="activityPercentTarget" :is-increase="activityTrend === 'increase'" @back="expandedView = null" />
			<IdleItemsView v-else-if="expandedView === 'idle-items'" key="idle-items" :unworn-count="idleCount" @back="expandedView = null" />
			<view v-else key="bento" class="page-bento-wrap">
				<view v-if="filterOpen" class="filter-backdrop" @click="closeFilter"></view>

				<!-- Bento Grid -->
				<view class="bento-grid bento-grid-entering" :class="{ 'bento-grid-filter-open': filterOpen }" @click="filterOpen && closeFilter()">
					<!-- Activity -->
					<view class="card bento-activity">
						<text class="card-label">Wardrobe Activity</text>
						<view class="big-metric">
							<text class="metric-num">{{ activityPercent }}%</text>
							<view class="trend-badge" :class="{ 'trend-badge-decrease': activityTrend === 'decrease' }">
								<text class="metric-arrow" :class="{ 'metric-arrow-decrease': activityTrend === 'decrease' }">{{ activityTrend === 'increase' ? '↗' : '↘' }}</text>
							</view>
						</view>
						<text class="card-sub">{{ activityTrend === 'increase' ? 'Increase compared to last week' : 'Decrease compared to last week' }}</text>
						<text class="card-link" @click="goActivityReport">Activity report →</text>
					</view>

					<!-- Idle Rate -->
					<view class="card bento-idle">
						<text class="card-label">Idle Rate</text>
						<text class="metric-num">{{ idlePercent }}%</text>
						<text class="card-sub">You have {{ idleCount }} unworn items out of {{ totalItemsCount }} total.</text>
						<text class="card-link" @click="goIdleItems">See all idle items →</text>
					</view>

					<!-- Total Items（主卡） -->
					<view class="card card-elevation-main bento-total">
						<view class="card-row">
							<text class="card-label">Total Items</text>
							<view class="filter-trigger" @click.stop="toggleViewBy('total')">
								<text>{{ viewByTotalLabel }}</text>
								<ViewByFilter v-model="viewByTotal" :visible="filterOpen === 'total'" @apply="closeFilter" @reset="closeFilter" />
							</view>
						</view>
						<view class="chart-container">
							<!-- 显示加载状态 -->
							<view v-if="loadingTrend" class="loading-state">
								<text class="loading-text">加载趋势数据...</text>
							</view>
							<template v-else>
								<svg viewBox="0 0 300 120" class="line-svg">
									<defs>
										<linearGradient id="greenGradient" x1="0" x2="0" y1="0" y2="1">
											<stop offset="0%" stop-color="#7cb97c" stop-opacity="0.28" />
											<stop offset="40%" stop-color="#7cb97c" stop-opacity="0.18" />
											<stop offset="70%" stop-color="#7cb97c" stop-opacity="0.08" />
											<stop offset="100%" stop-color="#7cb97c" stop-opacity="0" />
										</linearGradient>
									</defs>
									<!-- 3 条水平虚线网格 -->
									<line x1="0" y1="35" x2="300" y2="35" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
									<line x1="0" y1="60" x2="300" y2="60" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
									<line x1="0" y1="85" x2="300" y2="85" stroke="#000" stroke-width="1" stroke-dasharray="6 6" opacity="0.06" />
									<path :d="smoothPathArea" fill="url(#greenGradient)" class="line-area" />
									<path :d="smoothPathStroke" fill="none" stroke="#7cb97c" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="line-stroke" pathLength="1" />
								</svg>
								<view class="chart-labels">
									<text v-for="year in lineYears" :key="year" class="chart-label">{{ year }}</text>
								</view>
								<!-- 显示统计信息 -->
								<view class="chart-stats" v-if="totalStats">
									<text class="stat-item">总数: {{ totalItemsCount }}</text>
									<text class="stat-item" v-if="totalStats.growth_rate">增长率: {{ totalStats.growth_rate }}%</text>
									<text class="stat-item" v-if="totalStats.projection">预测{{ totalStats.projection_year }}: {{ totalStats.projection }}</text>
								</view>
							</template>
						</view>
					</view>

					<!-- Most Worn -->
					<view class="card bento-worn">
						<view class="card-row">
							<text class="card-label">Most Worn Items</text>
							<view class="filter-trigger" @click.stop="toggleViewBy('worn')">
								<text>{{ viewByWornLabel }}</text>
								<ViewByFilter v-model="viewByWorn" :visible="filterOpen === 'worn'" @apply="closeFilter" @reset="closeFilter" />
							</view>
						</view>
						<view class="worn-list">
							<view v-if="loadingWorn" class="loading-state">
								<text class="loading-text">加载中...</text>
							</view>
							<template v-else>
								<view v-for="item in mostWornWithDot" :key="item.name" class="list-item">
									<view class="dot" :class="{ active: item.dotColor === '#5c6bc0', dark: item.dotColor === '#616161' }" :style="{ background: item.dotColor }"></view>
									<text class="item-title">{{ item.name }}</text>
									<text class="item-wears">{{ item.wears }} wears</text>
								</view>
							</template>
						</view>
					</view>

					<!-- ⭐ Top Color + Top Style 堆叠 -->
					<view class="bento-stats">
						<view class="mini-card">
							<text class="card-label-small">Top color</text>
							<text class="mini-value">{{ topColorName || 'Brown' }}</text>
							<text class="mini-sub">{{ topColorPercent }}%</text>
						</view>
						<view class="mini-card">
							<text class="card-label-small">Top style</text>
							<text class="mini-value">{{ topStyleName || 'Sporty' }}</text>
							<text class="mini-sub">{{ topStylePercent }}%</text>
						</view>
					</view>

					<!-- Suggested Additions -->
					<view class="card bento-suggested">
						<text class="card-label">Suggested Additions</text>
						<view class="suggest-list">
							<view v-for="sug in suggested" :key="sug.name" class="suggest-item" :class="{ 'suggest-item-expanded': expandedSuggestKeys.includes(sug.name) }">
								<view class="suggest-row">
									<image class="suggest-thumb" :src="sug.image" mode="aspectFill" />
									<view class="suggest-content">
										<text class="suggest-title">{{ sug.name }}</text>
										<view class="suggest-tags">
											<text v-for="tag in sug.tags" :key="tag" class="suggest-tag">{{ tag }}</text>
										</view>
									</view>
									<view class="suggest-expand-btn" @click.stop="toggleSuggest(sug.name)">
										<text class="suggest-plus">{{ expandedSuggestKeys.includes(sug.name) ? '−' : '＋' }}</text>
									</view>
								</view>
								<view class="suggest-detail">
									<text class="suggest-text">{{ sug.desc }}</text>
								</view>
							</view>
						</view>
					</view>

					<!-- ⭐ Category Breakdown（主卡） -->
					<view class="card card-elevation-main bento-category">
						<view class="card-row">
							<text class="card-label big-title">Category Breakdown</text>
							<view class="filter-trigger" @click="toggleCategoryType">
								<text>Type</text>
							</view>
						</view>
						<view class="donut-container">
							<svg viewBox="-100 -100 200 200" class="donut-svg" aria-hidden="true" @mouseleave="hoveredSegmentIndex = null">
								<path
									v-for="{ seg, originalIndex } in donutSegmentsForDraw"
									:key="originalIndex"
									:d="seg.path"
									:fill="seg.color"
									stroke="#ffffff"
									stroke-width="3.5"
									stroke-linecap="round"
									:class="['donut-path', { 'donut-path-enter': !donutEntranceDone, 'donut-path-hover': hoveredSegmentIndex === originalIndex }]"
									:style="{ animationDelay: donutEntranceDone ? undefined : originalIndex * 0.08 + 's' }"
									@mouseenter="hoveredSegmentIndex = originalIndex"
									@mouseleave="hoveredSegmentIndex = null"
								/>
								<circle cx="0" cy="0" r="52" fill="#ffffff" pointer-events="none" />
								<circle cx="0" cy="0" r="24" fill="none" stroke="#8d6e63" stroke-width="2" stroke-linecap="round" pathLength="100" stroke-dasharray="4 6" pointer-events="none" />
								<circle cx="0" cy="0" r="42" fill="none" stroke="#E5E0D8" stroke-width="2.5" stroke-linecap="round" pathLength="300" stroke-dasharray="3 9" pointer-events="none" />
							</svg>
							<view class="center-content">
								<view v-if="hoveredSegment" class="center-detail">
									<text class="center-detail-label">{{ hoveredSegment.label }}</text>
									<text class="center-detail-count">{{ hoveredSegment.value }} items</text>
								</view>
								<view v-else class="center-icon">
									<image src="/static/icons/icon-wardrobe.svg" mode="aspectFit" class="center-icon-img" />
								</view>
							</view>
							<view
								v-for="(seg, i) in donutSegments"
								:key="'lbl-' + i"
								:class="['floating-label', { 'floating-label-hover': hoveredSegmentIndex === i }]"
								:style="{ transform: `translate(${seg.labelY}px, ${-seg.labelX}px)`, textAlign: seg.align }"
							>
								<text class="label-text" :class="[seg.labelSize === 'xl' ? 'label-xl' : seg.labelSize === 'lg' ? 'label-lg' : 'label-sm']">{{ seg.label }}</text>
							</view>
						</view>
					</view>
				</view>
			</view>
		</transition>
	</view>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import ViewByFilter from './ViewByFilter.vue'
import ActivityReport from './ActivityReport.vue'
import IdleItemsView from './IdleItemsView.vue'
import { COLOR_HEX_BY_CODE } from '@/utils/wardrobeEnums.js'

// API基础URL
const API_BASE_URL = 'http://localhost:8000'

// ============ 状态变量 ============
const expandedView = ref(null)
const filterOpen = ref(null)
const viewByTotal = ref('yearly')
const viewByWorn = ref('yearly')
const hoveredSegmentIndex = ref(null)
const donutEntranceDone = ref(false)
const expandedSuggestKeys = ref([])

// 加载状态
const loadingTrend = ref(true)
const loadingWorn = ref(true)
const loadingStats = ref(true)

// 数据变量
const lineYears = ref(['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023'])
const lineData = ref([5, 12, 20, 18, 30, 60, 90, 106])
const totalItemsCount = ref(106)
const totalStats = ref(null)

// 活动趋势
const activityTrend = ref(Math.random() >= 0.5 ? 'increase' : 'decrease')
const activityPercentTarget = computed(() => (activityTrend.value === 'increase' ? 15 : 8))

// 闲置率相关
const idleCount = ref(0)           // 闲置数量（用于显示文字）

// 动画数值
const activityPercent = ref(0)
const idlePercent = ref(0)
const topColorPercent = ref(0)
const topStylePercent = ref(0)

// 颜色和风格
const topColorName = ref('Brown')
const topStyleName = ref('Sporty')

const loadingTopColor = ref(true)
const loadingTopStyle = ref(true)

const topColorData = ref({
    color_code: 'brown',
    color_name: 'Brown',
    percentage: 38
})

const topStyleData = ref({
    style_code: 'sporty',
    style_name: 'Sporty',
    percentage: 45
})

// 最常穿衣物
const mostWorn = ref([
	{ name: 'White Cotton T-shirt', wears: 35, color: 'white' },
	{ name: 'Classic Denim Jacket', wears: 28, color: 'blue' },
	{ name: 'Black Knit Top', wears: 27, color: 'black' },
	{ name: 'Khaki Chino Pants', wears: 24, color: 'brown' },
	{ name: 'Navy Striped Tee', wears: 22, color: 'navy' }
])

// 分类数据
const categoryData = ref([
	{ label: 'Top', value: 35, color: '#FCD568' },
	{ label: 'Bottom', value: 25, color: '#68C5FA' },
	{ label: 'Footwear', value: 10, color: '#A694F5' },
	{ label: 'Outerwear', value: 15, color: '#FF69B4' },
	{ label: 'Accessories', value: 15, color: '#E57373' }
])

// 推荐商品
const suggested = ref([
	{ name: 'Cream Knit Sweater', image: '/static/cloth_example.png', tags: ['Warm Layer', 'Minimal'], desc: 'Complements your white cotton tees; provides a clean seasonal outer layer.' },
	{ name: 'Dark Denim Overshirt', image: '/static/cloth_example.png', tags: ['Layering', 'Versatile'], desc: 'Pairs well with the classic denim jacket; adds structure and versatility.' },
	{ name: 'Khaki Casual Pants', image: '/static/cloth_example.png', tags: ['Neutral', 'Balance'], desc: 'Balances your black knit top and enhances overall color harmony.' }
])

// ============ 计算属性 ============
const viewByTotalLabel = computed(() => viewByToLabel(viewByTotal.value))
const viewByWornLabel = computed(() => viewByToLabel(viewByWorn.value))

const mostWornWithDot = computed(() =>
	mostWorn.value.map((item) => ({
		...item,
		dotColor: COLOR_HEX_BY_CODE[item.color] || '#cccccc'
	}))
)

const smoothPathStroke = computed(() => getSvgPath(lineData.value, 300, 120, false))
const smoothPathArea = computed(() => getSvgPath(lineData.value, 300, 120, true))

// 圆环图相关计算
const donutSegments = computed(() => {
	let startAngle = 0
	const total = categoryData.value.reduce((a, b) => a + b.value, 0)
	const r1 = 52
	const maxValue = Math.max(...categoryData.value.map((d) => d.value), 1)
	const baseRadius = 76
	const radiusRange = 24
	const defaultLabelGap = 95

	return categoryData.value.map((item) => {
		const r2 = baseRadius + (item.value / maxValue) * radiusRange
		const sliceAngle = (item.value / total) * 2 * Math.PI
		const endAngle = startAngle + sliceAngle

		const x1 = Math.cos(startAngle) * r2
		const y1 = Math.sin(startAngle) * r2
		const x2 = Math.cos(endAngle) * r2
		const y2 = Math.sin(endAngle) * r2
		const x3 = Math.cos(endAngle) * r1
		const y3 = Math.sin(endAngle) * r1
		const x4 = Math.cos(startAngle) * r1
		const y4 = Math.sin(startAngle) * r1

		const largeArc = sliceAngle > Math.PI ? 1 : 0
		const path = `M ${x4} ${y4} L ${x1} ${y1} A ${r2} ${r2} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${r1} ${r1} 0 ${largeArc} 0 ${x4} ${y4} Z`

		const midAngle = startAngle + sliceAngle / 2
		const labelAngle = midAngle
		const labelR = r2 + defaultLabelGap
		const labelX = Math.cos(labelAngle) * labelR
		const labelY = Math.sin(labelAngle) * labelR
		const align = Math.cos(labelAngle) > 0 ? 'left' : 'right'
		const labelSize = item.value >= 30 ? 'xl' : item.value >= 20 ? 'lg' : 'sm'

		startAngle = endAngle
		return { ...item, path, labelX, labelY, align, labelSize }
	})
})

const donutSegmentsForDraw = computed(() => {
	const list = donutSegments.value.map((seg, originalIndex) => ({ seg, originalIndex }))
	const hovered = hoveredSegmentIndex.value
	if (hovered == null) return list
	const [item] = list.splice(hovered, 1)
	list.push(item)
	return list
})

const hoveredSegment = computed(() => {
	const i = hoveredSegmentIndex.value
	if (i == null) return null
	return donutSegments.value[i] ?? null
})

// ============ 工具函数 ============
function viewByToLabel(v) {
	return v === 'yearly' ? 'Yearly' : v === 'monthly' ? 'Monthly' : 'Daily'
}

function getSvgPath(data, width, height, isArea) {
  // 数据验证
  if (!data || !Array.isArray(data) || data.length === 0) {
    console.warn('数据无效，返回空路径', data)
    return ''
  }
  
  // 过滤掉无效数据（null、undefined、NaN）
  const validData = data.filter(val => val !== null && val !== undefined && !isNaN(val) && isFinite(val))
  
  if (validData.length === 0) {
    console.warn('没有有效数据', data)
    return ''
  }
  
  // 如果有效数据少于2个，无法绘制曲线
  if (validData.length < 2) {
    console.warn('有效数据不足2个，无法绘制曲线', validData)
    return ''
  }
  
  if (!data || !Array.isArray(data) || data.length === 0) {
      return ''
    }
    
    // 如果只有1个数据点，返回一条水平线
	if (data.length === 1) {
	  const padding = 10
	  const chartH = height - padding * 2
	  const max = Math.max(data[0], 1)
	  const y = height - padding - (data[0] / max) * chartH
	  
	  // 返回一条从左到右的水平线
	  if (isArea) {
		return `M 0,${y} L ${width},${y} L ${width},${height} L 0,${height} Z`
	  } else {
		return `M 0,${y} L ${width},${y}`
	  }
	}
  
  // 计算最大值，确保不为0
  const max = Math.max(...validData, 1)
  if (max === 0) {
    console.warn('最大值为0，无法计算比例')
    return ''
  }
  
  const padding = 10
  const chartH = height - padding * 2
  const stepX = width / (validData.length - 1)
  
  // 计算点坐标，确保所有值都是有效数字
  const points = validData.map((val, i) => {
    const x = i * stepX
    const y = height - padding - (val / max) * chartH
    
    // 验证坐标有效性
    if (isNaN(x) || isNaN(y) || !isFinite(x) || !isFinite(y)) {
      console.error('无效的坐标计算:', { i, val, x, y })
      return null
    }
    return [x, y]
  }).filter(point => point !== null) // 过滤无效点
  
  if (points.length < 2) {
    console.warn('有效点不足2个，无法绘制')
    return ''
  }
  
  // 构建路径
  let d = `M ${points[0][0]},${points[0][1]}`
  
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i]
    const p1 = points[i + 1]
    const midX = (p0[0] + p1[0]) / 2
    const cp1x = p0[0] + (midX - p0[0]) * 0.6
    const cp2x = midX + (p1[0] - midX) * 0.4
    d += ` C ${cp1x},${p0[1]} ${cp2x},${p1[1]} ${p1[0]},${p1[1]}`
  }
  
  if (isArea) {
    d += ` L ${width},${height} L 0,${height} Z`
  }
  
  return d
}

// 修改动画函数，允许从外部传入目标值
function animateCountUp(refVal, targetRef, duration = 800, delay = 0) {
  const startVal = 0
  const start = () => {
    const t0 = performance.now()
    
    // 获取目标值（可能是响应式引用）
    const getTarget = () => {
      if (typeof targetRef === 'function') {
        return targetRef()
      } else if (targetRef && targetRef.value !== undefined) {
        return targetRef.value
      } else {
        return targetRef
      }
    }
    
    function tick(now) {
      const target = getTarget()
      const elapsed = now - t0
      const t = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3)
      refVal.value = Math.round(startVal + (target - startVal) * eased)
      if (t < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }
  if (delay > 0) setTimeout(start, delay)
  else start()
}

// ============ Token调试函数 ============
const debugStorage = () => {
	console.log('===== Storage调试信息 =====')
	
	// 检查所有可能的token存储key
	const possibleKeys = [
		'token',
		'access_token',
		'userToken',
		'user_token',
		'auth_token',
		'Authorization',
		'authorization'
	]
	
	possibleKeys.forEach(key => {
		try {
			const value = uni.getStorageSync(key)
			if (value) {
				console.log(`找到token在key[${key}]:`, value.substring(0, 20) + '...')
			} else {
				console.log(`key[${key}] 没有token`)
			}
		} catch (e) {
			console.log(`读取key[${key}]失败:`, e)
		}
	})
	
	// 检查所有storage内容
	try {
		const allStorage = {}
		const keys = uni.getStorageInfoSync().keys
		console.log('所有storage keys:', keys)
		keys.forEach(key => {
			const value = uni.getStorageSync(key)
			allStorage[key] = typeof value === 'string' ? value.substring(0, 30) + '...' : value
		})
		console.log('storage内容:', allStorage)
	} catch (e) {
		console.log('获取所有storage失败:', e)
	}
}

// 获取token的改进版本
const getToken = () => {
	console.log('开始获取token...')
	
	// 尝试所有可能的key
	const possibleKeys = [
		'token',
		'access_token',
		'userToken',
		'user_token',
		'auth_token',
		'Authorization',
		'authorization'
	]
	
	for (const key of possibleKeys) {
		try {
			const value = uni.getStorageSync(key)
			if (value && typeof value === 'string' && value.length > 10) {
				console.log(`成功从key[${key}]获取token:`, value.substring(0, 20) + '...')
				return value
			}
		} catch (e) {
			console.log(`从key[${key}]获取token失败:`, e)
		}
	}
	
	// 尝试从vuex或全局变量获取（如果存在）
	if (uni.$uvi && uni.$uvi.store) {
		console.log('尝试从uni.$uvi获取token')
		// 这里可以根据你的实际情况调整
	}
	
	console.log('未找到任何token')
	return null
}

// 检查是否已登录
const isLoggedIn = () => {
	const token = getToken()
	return !!token
}

// ============ API 请求函数 ============
const apiRequest = async (url, method = 'GET', data = {}) => {
  const token = getToken()
  
  if (!token) {
    console.warn('未找到token，使用模拟数据')
    return null
  }

  try {
    // 构建 URL，将 token 作为查询参数
    const queryParams = new URLSearchParams({
      ...data,
      token: token
    })
    
    const fullUrl = `${API_BASE_URL}${url}?${queryParams.toString()}`
    
    const res = await uni.request({
      url: fullUrl,
      method: method,
      header: {
        'Content-Type': 'application/json'
      },
      timeout: 10000
    })

    if (res.statusCode === 200) {
      return res.data
    } else if (res.statusCode === 401) {
      console.warn('token无效或过期')
      uni.showToast({
        title: '登录已过期，请重新登录',
        icon: 'none'
      })
      return null
    }
    
    return null
  } catch (error) {
    console.error('API请求异常:', error)
    return null
  }
}

// 获取趋势数据
const fetchTrendData = async () => {
  console.log('开始获取趋势数据, viewBy:', viewByTotal.value)
  loadingTrend.value = true
  
  try {
    const response = await apiRequest('/api/analysis/total-items/trend', 'GET', {
      view_by: viewByTotal.value
    })

    console.log('趋势数据响应:', response)

    if (response && response.success && response.data) {
      const data = response.data
      console.log('趋势数据成功:', data)
      
      // 检查数据是否有效
      if (data.labels && data.labels.length > 0 && data.values && data.values.length > 0) {
        // 设置年份标签
        lineYears.value = data.labels
        // 设置折线图数据（使用累计值）
        lineData.value = data.values
        totalItemsCount.value = data.total_count
        totalStats.value = data.statistics
        
        console.log('折线图数据更新:', {
          labels: lineYears.value,
          values: lineData.value,
          totalCount: totalItemsCount.value
        })
      } else {
        console.warn('趋势数据为空，使用模拟数据')
        // 使用模拟数据
        setMockTrendData()
      }
    } else {
      console.log('API返回数据格式异常，使用模拟数据')
      setMockTrendData()
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
    setMockTrendData()
  } finally {
    loadingTrend.value = false
  }
}

// 设置模拟数据函数
const setMockTrendData = () => {
  if (viewByTotal.value === 'yearly') {
    lineYears.value = ['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023']
    lineData.value = [5, 12, 20, 18, 30, 60, 90, 106]
  } else if (viewByTotal.value === 'monthly') {
    // 生成最近12个月的标签
    const months = []
    const data = []
    const now = new Date()
    for (let i = 11; i >= 0; i--) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
      months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
      data.push(Math.floor(Math.random() * 20) + 5)
    }
    lineYears.value = months
    lineData.value = data
  } else if (viewByTotal.value === 'daily') {
    // 生成最近30天的标签
    const days = []
    const data = []
    const now = new Date()
    for (let i = 29; i >= 0; i--) {
      const d = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
      days.push(`${d.getMonth() + 1}/${d.getDate()}`)
      data.push(Math.floor(Math.random() * 5) + 1)
    }
    lineYears.value = days
    lineData.value = data
  }
  
  totalItemsCount.value = lineData.value[lineData.value.length - 1] || 0
}

const testApiConnection = async () => {
  try {
    const res = await uni.request({
      url: API_BASE_URL + '/api/health',
      method: 'GET',
      timeout: 5000
    })
    console.log('API 连接测试:', res)
    return res.statusCode === 200
  } catch (error) {
    console.error('API 连接失败:', error)
    return false
  }
}

// 获取概览数据
const fetchSummaryData = async () => {
	console.log('开始获取概览数据')
	loadingStats.value = true
	
	try {
		const response = await apiRequest('/api/analysis/total-items/summary', 'GET')
		
		console.log('概览数据响应:', response)

		if (response && response.data) {
			const data = response.data
			console.log('概览数据成功:', data)
			
			if (data.total_items) {
				totalItemsCount.value = data.total_items
			}
		}
	} catch (error) {
		console.error('获取概览数据失败:', error)
	} finally {
		loadingStats.value = false
	}
}

// ============ 事件处理函数 ============
function toggleViewBy(which) {
	filterOpen.value = filterOpen.value === which ? null : which
}

function closeFilter() {
	filterOpen.value = null
}

function toggleCategoryType() {
	console.log('切换分类类型')
}

function goActivityReport() {
	expandedView.value = 'activity-report'
}

function goIdleItems() {
	expandedView.value = 'idle-items'
}

function toggleSuggest(key) {
	const arr = expandedSuggestKeys.value
	const i = arr.indexOf(key)
	if (i >= 0) {
		expandedSuggestKeys.value = arr.filter((k) => k !== key)
	} else {
		expandedSuggestKeys.value = [...arr, key]
	}
}

// ============ 生命周期和监听 ============
// 监听视图切换
watch(viewByTotal, (newVal, oldVal) => {
	console.log('viewByTotal changed:', oldVal, '->', newVal)
	if (isLoggedIn()) {
		fetchTrendData()
	}
})

watch(viewByWorn, (newVal, oldVal) => {
  console.log('========== viewByWorn 变化 ==========')
  console.log('旧值:', oldVal)
  console.log('新值:', newVal)
  console.log('登录状态:', isLoggedIn())
  if (isLoggedIn()) {
  	fetchMostWornItems()
  }
})

// 添加分类数据加载状态
const loadingCategory = ref(true)

// 获取分类分布数据
const fetchCategoryDistribution = async () => {
  console.log('开始获取分类分布数据')
  loadingCategory.value = true
  
  try {
    const token = getToken()
    if (!token) {
      console.log('未登录，使用模拟数据')
      return
    }
    
    const response = await apiRequest('/api/analysis/total-items/category-distribution', 'GET')
    
    console.log('分类分布响应:', response)
    
    if (response && response.success && response.data) {
      // 更新分类数据
      categoryData.value = response.data
      console.log('分类数据更新成功:', categoryData.value)
    } else {
      console.log('使用默认分类数据')
      // 保留默认的模拟数据
    }
  } catch (error) {
    console.error('获取分类分布数据失败:', error)
  } finally {
    loadingCategory.value = false
  }
}

// ============ 闲置率相关API ============
const loadingIdleRate = ref(true)

// 获取闲置率数据
const fetchIdleRate = async () => {
  console.log('开始获取闲置率数据')
  loadingIdleRate.value = true
  
  try {
    const token = getToken()
    if (!token) {
      console.log('未登录，使用模拟数据')
      // 模拟数据：假设总数为3，闲置数为3，闲置率100%
      totalItemsCount.value = 3
      idleCount.value = 3
      // 触发百分比动画到100
      animateCountUp(idlePercent, 100, 800)
      return
    }
    
    const response = await apiRequest('/api/analysis/idle-rate', 'GET', {
      days: 30
    })
    
    console.log('闲置率响应:', response)
    
    if (response && response.success && response.data) {
      const data = response.data
      
      // 更新数据
      totalItemsCount.value = data.total_items
      idleCount.value = data.idle_items
      
      // 动画更新百分比到真实值
      animateCountUp(idlePercent, data.idle_rate, 800)
      
      console.log('闲置率数据更新成功:', {
        总数量: data.total_items,
        闲置数量: data.idle_items,
        闲置百分比: data.idle_rate + '%'
      })
    } else {
      console.log('API返回数据异常，使用模拟数据')
      // 使用模拟数据
      totalItemsCount.value = 106
      idleCount.value = 23  // 假设23件闲置
      animateCountUp(idlePercent, (23/106 * 100).toFixed(1), 800)
    }
  } catch (error) {
    console.error('获取闲置率数据失败:', error)
    // 出错时使用模拟数据
    totalItemsCount.value = 106
    idleCount.value = 23
    animateCountUp(idlePercent, (23/106 * 100).toFixed(1), 800)
  } finally {
    loadingIdleRate.value = false
  }
}

// 获取最常用颜色
const fetchTopColor = async () => {
    console.log('开始获取颜色统计')
    loadingTopColor.value = true
    
    try {
        const response = await apiRequest('/api/analysis/top-color', 'GET')
        
        console.log('颜色统计响应:', response)
        
        if (response && response.success && response.data) {
            const data = response.data
            
            // 更新数据
            topColorData.value = data.top_color
            topColorName.value = data.top_color.color_name
            // 动画更新百分比
            animateCountUp(topColorPercent, data.top_color.percentage, 800)
            
            console.log('颜色数据更新成功:', data.top_color)
        } else {
            console.log('使用默认颜色数据')
        }
    } catch (error) {
        console.error('获取颜色统计失败:', error)
    } finally {
        loadingTopColor.value = false
    }
}

// 获取最常用风格
const fetchTopStyle = async () => {
    console.log('开始获取风格统计')
    loadingTopStyle.value = true
    
    try {
        const response = await apiRequest('/api/analysis/top-style', 'GET')
        
        console.log('风格统计响应:', response)
        
        if (response && response.success && response.data) {
            const data = response.data
            
            // 更新数据
            topStyleData.value = data.top_style
            topStyleName.value = data.top_style.style_name
            // 动画更新百分比
            animateCountUp(topStylePercent, data.top_style.percentage, 800)
            
            console.log('风格数据更新成功:', data.top_style)
        } else {
            console.log('使用默认风格数据')
        }
    } catch (error) {
        console.error('获取风格统计失败:', error)
    } finally {
        loadingTopStyle.value = false
    }
}

// 获取最常穿衣物（支持时间范围）
const fetchMostWornItems = async () => {
  console.log('========== 开始获取最常穿物品 ==========')
  console.log('time_range:', viewByWorn.value)
  loadingWorn.value = true
  
  try {
    const token = getToken()
    
    if (token) {
      const response = await apiRequest('/api/analysis/most-worn', 'GET', {
        time_range: viewByWorn.value,
        limit: 5
      })

      console.log('API原始响应:', response)

      if (response && response.success) {
        if (response.data && response.data.items) {
          console.log('原始items数据:', response.data.items)
          
          // 检查每个item的wears值
          response.data.items.forEach((item, index) => {
            console.log(`Item ${index}:`, item.name, 'wears =', item.wears, '类型:', typeof item.wears)
          })
          
          // 更新数据 - 使用更安全的方式
          const newItems = response.data.items.map(item => {
            // 确保wears是数字
            const wearsValue = parseInt(item.wears) || 0
            console.log(`处理物品 ${item.name}: 原始wears=${item.wears}, 处理后=${wearsValue}`)
            
            return {
              name: item.name,
              wears: wearsValue,
              color: item.color || 'gray'
            }
          })
          
          console.log('处理后的newItems:', newItems)
          mostWorn.value = newItems
          
        } else {
          console.warn('API返回数据格式异常:', response)
          setMockWornData(viewByWorn.value)
        }
      } else {
        console.warn('API请求失败:', response)
        setMockWornData(viewByWorn.value)
      }
    } else {
      console.log('未登录，使用模拟数据')
      setMockWornData(viewByWorn.value)
    }
  } catch (error) {
    console.error('获取最常穿物品异常:', error)
    setMockWornData(viewByWorn.value)
  } finally {
    loadingWorn.value = false
    console.log('最终的mostWorn.value:', mostWorn.value)
    console.log('========== 获取结束 ==========')
  }
}

// 设置模拟数据
const setMockWornData = (timeRange) => {
  if (timeRange === 'yearly') {
    mostWorn.value = [
      { name: 'White Cotton T-shirt', wears: 35, color: 'white' },
      { name: 'Classic Denim Jacket', wears: 28, color: 'blue' },
      { name: 'Black Knit Top', wears: 27, color: 'black' },
      { name: 'Khaki Chino Pants', wears: 24, color: 'brown' },
      { name: 'Navy Striped Tee', wears: 22, color: 'navy' }
    ]
  } else if (timeRange === 'monthly') {
    mostWorn.value = [
      { name: 'White Cotton T-shirt', wears: 8, color: 'white' },
      { name: 'Black Knit Top', wears: 6, color: 'black' },
      { name: 'Classic Denim Jacket', wears: 5, color: 'blue' },
      { name: 'Navy Striped Tee', wears: 4, color: 'navy' },
      { name: 'Khaki Chino Pants', wears: 3, color: 'brown' }
    ]
  } else { // daily
    mostWorn.value = [
      { name: 'White Cotton T-shirt', wears: 1, color: 'white' },
      { name: 'Black Knit Top', wears: 0, color: 'black' },
      { name: 'Classic Denim Jacket', wears: 0, color: 'blue' },
      { name: 'Khaki Chino Pants', wears: 0, color: 'brown' },
      { name: 'Navy Striped Tee', wears: 0, color: 'navy' }
    ]
  }
}

onMounted(() => {
  console.log('WardrobeAnalysis mounted')
  
  // 先调试storage
  debugStorage()
  
  // 获取token
  const token = getToken()
  console.log('最终获取到的token:', token ? token.substring(0, 20) + '...' : 'null')
  
  // 先显示模拟数据，然后尝试获取真实数据
  setTimeout(() => { 
    donutEntranceDone.value = true 
  }, 800)
  
  // // 数字滚动动画 - 先使用默认值（后续会被真实数据覆盖）
  // const countUpDelay = 320
  // animateCountUp(activityPercent, activityPercentTarget, 800, countUpDelay)
  // animateCountUp(idlePercent, idleCount, 800, countUpDelay + 60)  
  // animateCountUp(topColorPercent, 38, 800, countUpDelay + 120)
  // animateCountUp(topStylePercent, 45, 800, countUpDelay + 180)
  
  // 尝试获取真实数据（如果已登录）
  if (token) {
    console.log('用户已登录，开始获取真实数据')
    
    // 先测试API是否可访问
    uni.request({
      url: API_BASE_URL + '/api/health',
      method: 'GET',
      success: (res) => {
        console.log('健康检查响应:', res.data)
        if (res.statusCode === 200) {
          console.log('服务器连接正常')
          
          // 获取所有数据
          Promise.all([
            fetchTrendData(),
            fetchSummaryData(),
            fetchMostWornItems(),
            fetchCategoryDistribution(),
            fetchIdleRate(), // 新增：获取闲置率数据
			fetchTopColor(),
			fetchTopStyle(),
          ]).then(() => {
            console.log('所有数据获取完成')
            
            // 数据加载完成后，重新触发动画（让数值平滑变化到新值）
            animateCountUp(activityPercent, activityPercentTarget, 400)
            animateCountUp(idlePercent, idleCount, 400)  // 重新动画到真实值
          }).catch(error => {
            console.error('获取数据失败:', error)
          })
        } else {
          console.log('服务器连接异常')
          uni.showToast({
            title: '无法连接到服务器',
            icon: 'none'
          })
        }
      },
      fail: (error) => {
        console.error('健康检查失败:', error)
        uni.showToast({
          title: '服务器连接失败',
          icon: 'none'
        })
      }
    })
  } else {
    console.log('用户未登录，使用模拟数据')
    uni.showToast({
      title: '使用演示数据',
      icon: 'none',
      duration: 2000
    })
  }
})
</script>

<style scoped>
/* 原有的样式保持不变，只添加调试相关的样式 */
.loading-state {
	display: flex;
	justify-content: center;
	align-items: center;
	min-height: 180rpx;
}

.loading-text {
	color: #999;
	font-size: 28rpx;
}

.chart-stats {
	margin-top: 20rpx;
	display: flex;
	flex-wrap: wrap;
	gap: 20rpx;
	font-size: 24rpx;
	color: #666;
}

.stat-item {
	background: #f5f5f3;
	padding: 6rpx 16rpx;
	border-radius: 20rpx;
}

/* 其他样式保持不变，从原文件复制 */
.page {
	background: #F6F5F1;
	padding: 30rpx;
	position: relative;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
	min-height: 100%;
	box-sizing: border-box;
}
.page-bento-wrap {
	display: block;
}

.filter-backdrop {
	position: fixed;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
	z-index: 15;
	background: transparent;
}
.filter-backdrop:active { opacity: 0; }

.bento-grid {
	display: grid;
	gap: 24rpx;
	grid-template-columns: 1.3fr 1.3fr 1.35fr 1.35fr;
	grid-template-rows: 0.65fr 0.65fr 0.45fr 1.35fr;
	overflow: visible;
	position: relative;
}
.bento-grid-filter-open {
	z-index: 20;
}

.bento-grid-entering > * {
	opacity: 0;
	animation: bento-item-enter 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.bento-grid-entering > *:nth-child(1) { animation-delay: 0s; }
.bento-grid-entering > *:nth-child(2) { animation-delay: 0.07s; }
.bento-grid-entering > *:nth-child(3) { animation-delay: 0.14s; }
.bento-grid-entering > *:nth-child(4) { animation-delay: 0.21s; }
.bento-grid-entering > *:nth-child(5) { animation-delay: 0.28s; }
.bento-grid-entering > *:nth-child(6) { animation-delay: 0.35s; }
.bento-grid-entering > *:nth-child(7) { animation-delay: 0.42s; }
@keyframes bento-item-enter {
	from {
		opacity: 0;
		transform: translateY(16rpx);
	}
	to {
		opacity: 1;
		transform: translateY(0);
	}
}

.card {
	background: #FFFEFB;
	border-radius: 20rpx;
	padding: 28rpx 32rpx;
	box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05), 0 1rpx 4rpx rgba(0, 0, 0, 0.04);
	display: flex;
	flex-direction: column;
	overflow: visible;
	transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}
.card:hover {
	transform: translateY(-4rpx);
	box-shadow: 0 12rpx 32rpx rgba(0, 0, 0, 0.08), 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.card-elevation-main {
	box-shadow: 0 12rpx 40rpx rgba(0, 0, 0, 0.08), 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}
.card-elevation-main:hover {
	box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.1), 0 6rpx 16rpx rgba(0, 0, 0, 0.06);
}

.card-label {
	font-size: 30rpx;
	font-family: "Semi Bold";
	font-weight: 700;
	color: #1d1d1f;
	margin-bottom: 12rpx;
}

.big-title {
	font-size: 40rpx;
	font-weight: 900;
}

.card-sub {
	margin-top: 10rpx;
	font-size: 28rpx;
	color: #777;
	line-height: 1.45;
}

.card-link {
	margin-top: 16rpx;
	display: inline-block;
	font-size: 22rpx;
	color: #9c6b2f;
	font-weight: 600;
	transition: opacity 0.15s ease, transform 0.15s ease;
}
.card-link:active {
	opacity: 0.75;
	transform: scale(0.98);
}

.bento-activity,
.bento-idle {
	display: flex;
	flex-direction: column;
}
.bento-activity .card-link,
.bento-idle .card-link {
	margin-top: auto;
	padding-top: 20rpx;
	border-top: 1rpx solid rgba(0, 0, 0, 0.04);
}

.metric-num {
	font-size: 86.4rpx;
	font-weight: 700;
	font-family: "Medium";
	color: #1d1d1f;
	line-height: 1;
	margin-right: 12rpx;
}

.big-metric {
	display: flex;
	align-items: center;
	gap: 10rpx;
	margin-top: 8rpx;
	margin-bottom: 8rpx;
}

.trend-badge {
	background: rgba(124, 185, 124, 0.15);
	padding: 6rpx 14rpx;
	border-radius: 50%;
	width: 44rpx;
	height: 44rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 2rpx 8rpx rgba(124, 185, 124, 0.2);
}
.trend-badge-decrease {
	background: rgba(200, 100, 80, 0.18);
	box-shadow: 0 2rpx 8rpx rgba(180, 85, 65, 0.22);
}

.metric-arrow {
	color: #5a9d5a;
	font-size: 28rpx;
	font-weight: bold;
	line-height: 1;
}
.metric-arrow-decrease {
	color: #b85541;
}

.card-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16rpx;
}

.filter-trigger {
	display: inline-flex;
	align-items: center;
	gap: 4rpx;
	font-size: 24rpx;
	color: #6b6b6b;
	padding: 8rpx 14rpx;
	border-radius: 16rpx;
	background: #f5f5f3;
	border: 1rpx solid rgba(0, 0, 0, 0.06);
	position: relative;
	transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}
.filter-trigger:active {
	background: #ebebe8;
	border-color: rgba(0, 0, 0, 0.08);
	transform: scale(0.98);
}

.chart-container {
	flex: 1;
	min-height: 0;
	display: flex;
	flex-direction: column;
	padding-top: 28rpx;
}

.line-svg {
	width: 100%;
	height: 100%;
	min-height: 180rpx;
	display: block;
}

.line-stroke {
	stroke-dasharray: 1;
	stroke-dashoffset: 1;
	animation: drawLine 600ms ease-out forwards;
}

@keyframes drawLine {
	to {
		stroke-dashoffset: 0;
	}
}

.chart-labels {
	display: flex;
	justify-content: space-between;
	font-size: 20rpx;
	color: #b0b0b0;
	margin-top: 12rpx;
	font-weight: 400;
}

.bento-worn {
	display: flex;
	flex-direction: column;
}

.bento-worn .card-row {
	margin-bottom: 20rpx;
}

.worn-list {
	display: flex;
	flex-direction: column;
	gap: 28rpx;
	margin-top: 12rpx;
	flex: 1;
}

.list-item {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-bottom: 15rpx;
	min-height: 44rpx;
}
.item-wears {
	font-size: 26rpx;
	font-weight: 600;
	color: #666;
	letter-spacing: 0.02em;
	flex-shrink: 0;
	width: 140rpx;
	text-align: right;
}

.dot {
	width: 30rpx;
	height: 30rpx;
	border-radius: 50%;
	flex-shrink: 0;
	margin-top: 2rpx;
	border: 2.5rpx solid rgba(255, 255, 255, 0.95);
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15), inset 0 1rpx 3rpx rgba(255, 255, 255, 0.6);
}

.dot.active {
	background: #4a7bd0;
}

.dot.dark {
	background: #444;
}

.item-title {
	flex: 1;
	min-width: 0;
	font-size: 28rpx;
	font-weight: 600;
	font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
	color: #1d1d1f;
	line-height: 1.4;
	letter-spacing: -0.01em;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.bento-worn .card-link {
	margin-top: auto;
	padding-top: 24rpx;
	border-top: 1rpx solid rgba(0, 0, 0, 0.05);
}

.bento-stats {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.mini-card {
	background: #FFFEFB;
	border-radius: 16rpx;
	padding: 18rpx 20rpx;
	box-shadow: none;
	border: 1rpx solid rgba(0, 0, 0, 0.06);
	display: flex;
	flex-direction: column;
	position: relative;
	transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}
.mini-card:hover,
.mini-card:active {
	background: #f5f4f1;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
	transform: translateY(-2rpx);
}

.card-label-small {
	font-size: 24rpx;
	font-weight: 500;
	color: #888;
	display: block;
	letter-spacing: 0.02em;
}

.mini-value {
	font-size: 36rpx;
	font-weight: 800;
	margin-top: 6rpx;
	color: #7a4e18;
	display: block;
	letter-spacing: 0.01em;
}

.mini-sub {
	font-size: 22rpx;
	font-weight: 400;
	color: #999;
	margin-top: 4rpx;
	display: block;
}

.bento-suggested {
	display: flex;
	flex-direction: column;
	padding: 20rpx 24rpx 24rpx;
	background: #FFFEFB;
	border-radius: 20rpx;
	border: 1rpx solid rgba(141, 110, 99, 0.12);
}

.bento-suggested .card-label {
	margin-bottom: 16rpx;
	font-size: 32rpx;
	font-weight: 800;
	color: #1d1d1f;
	letter-spacing: 0.02em;
}

.suggest-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	margin-top: 15rpx;
}

.suggest-item {
	display: flex;
	flex-direction: column;
	overflow: hidden;
	border-radius: 16rpx;
	background: #FFFEFB;
	border: 1rpx solid rgba(141, 110, 99, 0.12);
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
	transition: box-shadow 0.25s ease, transform 0.2s ease;
}
.suggest-item:hover {
	box-shadow: 0 6rpx 20rpx rgba(0, 0, 0, 0.08);
}
.suggest-item:active {
	transform: scale(0.99);
}

.suggest-row {
	display: flex;
	align-items: center;
	gap: 20rpx;
	padding: 16rpx 18rpx;
	min-height: 0;
}

.suggest-thumb {
	width: 88rpx;
	height: 88rpx;
	border-radius: 12rpx;
	flex-shrink: 0;
	background: #f5f2ee;
}

.suggest-content {
	flex: 1;
	min-width: 0;
}

.suggest-title {
	display: block;
	font-size: 28rpx;
	font-weight: 700;
	color: #1d1d1f;
	letter-spacing: 0.02em;
	line-height: 1.35;
	margin-bottom: 8rpx;
}

.suggest-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 8rpx;
}

.suggest-tag {
	font-size: 20rpx;
	padding: 4rpx 12rpx;
	border-radius: 8rpx;
	background: rgba(141, 110, 99, 0.12);
	color: #6d4c41;
	font-weight: 500;
}

.suggest-expand-btn {
	width: 48rpx;
	height: 48rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(184, 107, 31, 0.1);
	flex-shrink: 0;
	transition: background 0.2s ease;
}
.suggest-item:hover .suggest-expand-btn,
.suggest-expand-btn:active {
	background: rgba(184, 107, 31, 0.2);
}

.suggest-plus {
	font-size: 28rpx;
	font-weight: 600;
	color: #8d6e63;
	line-height: 1;
}

.suggest-detail {
	max-height: 0;
	overflow: hidden;
	transition: max-height 0.35s ease-out;
}
.suggest-item-expanded .suggest-detail {
	max-height: 200rpx;
}

.suggest-text {
	display: block;
	font-size: 24rpx;
	font-weight: 400;
	color: #666;
	line-height: 1.5;
	padding: 0 18rpx 18rpx 18rpx;
	margin-top: -8rpx;
	padding-left: 126rpx;
}

.donut-container {
	flex: 1;
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 40rpx 20rpx;
	min-height: 320rpx;
}

.donut-svg {
	width: 100%;
	height: 100%;
	max-height: 800rpx;
	overflow: visible;
	transform: rotate(-90deg);
}

.donut-path {
	transform-origin: 50% 50%;
	transition: opacity 0.25s ease, transform 0.25s ease;
	cursor: pointer;
}
.donut-path.donut-path-enter {
	animation: donut-segment-enter 0.5s ease-out backwards;
}
.donut-path:hover,
.donut-path.donut-path-hover {
	opacity: 0.9;
	transform: scale(1.02);
}
@keyframes donut-segment-enter {
	from {
		opacity: 0;
		transform: scale(0.4);
	}
	to {
		opacity: 1;
		transform: scale(1);
	}
}

.center-content {
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	pointer-events: none;
	width: 140rpx;
	height: 140rpx;
	border-radius: 50%;
	background: #fff;
	box-shadow: 0 6rpx 20rpx rgba(0, 0, 0, 0.06);
	display: flex;
	align-items: center;
	justify-content: center;
}

.center-icon {
	display: flex;
	align-items: center;
	justify-content: center;
}

.center-icon-img {
	width: 64rpx;
	height: 64rpx;
	opacity: 0.8;
}

.center-detail {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 0 16rpx;
}

.center-detail-label {
	font-size: 28rpx;
	font-weight: 700;
	color: #1d1d1f;
	text-align: center;
	letter-spacing: 0.02em;
}

.center-detail-count {
	font-size: 16rpx;
	font-weight: 500;
	color: #666;
	margin-top: 6rpx;
	text-align: center;
}

.floating-label {
	position: absolute;
	top: 50%;
	left: 50%;
	pointer-events: none;
	width: 120rpx;
	margin-left: -60rpx;
	margin-top: -10rpx;
	display: flex;
	justify-content: center;
	align-items: center;
	transition: transform 0.2s ease;
}
.floating-label.floating-label-hover .label-text {
	color: #5d4037;
	transform: scale(1.08);
}

.label-text {
	font-weight: 700;
	color: #8d6e63;
	font-family: "Didot", "Bodoni MT", serif;
	line-height: 1.2;
	transition: color 0.2s ease, transform 0.2s ease;
}

.label-xl { font-size: 72rpx; }
.label-lg { font-size: 54rpx; }
.label-sm { font-size: 32rpx; }

.bento-activity { grid-column: 1; grid-row: 1; }
.bento-idle     { grid-column: 2; grid-row: 1; }
.bento-total    { grid-column: 3 / 5; grid-row: 1 / 3; }
.bento-worn     { grid-column: 1; grid-row: 2 / 4; }
.bento-stats    { grid-column: 2; grid-row: 2; }
.bento-suggested{ grid-column: 1 / 3; grid-row: 4; }
.bento-category { grid-column: 3 / 5; grid-row: 3 / 5; }

@media (max-width: 1024px) {
	.page { padding: 24rpx; }
	.bento-grid {
		grid-template-columns: 1fr 1fr;
		grid-template-rows: auto auto auto auto auto auto;
	}
	.bento-activity { grid-column: 1; grid-row: 1; }
	.bento-idle { grid-column: 2; grid-row: 1; }
	.bento-total { grid-column: 1 / -1; grid-row: 2; }
	.bento-category { grid-column: 1 / -1; grid-row: 3; min-height: 480rpx; }
	.bento-worn { grid-column: 1; grid-row: 4; }
	.bento-stats { grid-column: 2; grid-row: 4; }
	.bento-suggested { grid-column: 1 / -1; grid-row: 5; }
}

@media (max-width: 600px) {
	.page { padding: 20rpx; }
	.bento-grid {
		grid-template-columns: 1fr;
		gap: 20rpx;
	}
	.bento-activity { grid-column: 1; grid-row: 1; }
	.bento-idle { grid-column: 1; grid-row: 2; }
	.bento-total { grid-column: 1; grid-row: 3; }
	.bento-category { grid-column: 1; grid-row: 4; min-height: 420rpx; }
	.bento-worn { grid-column: 1; grid-row: 5; }
	.bento-stats { grid-column: 1; grid-row: 6; }
	.bento-suggested { grid-column: 1; grid-row: 7; }
}
</style>

<style>
.page-enter-active,
.page-leave-active {
	transition: opacity 220ms ease, transform 220ms ease;
}
.page-enter-from,
.page-leave-to {
	opacity: 0;
	transform: translateY(10px);
}
</style>