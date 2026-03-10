// frontend/utils/request.js
const BASE_URL = 'http://localhost:8000'

export const request = (options) => {
  return new Promise((resolve, reject) => {
    // 1. 处理 URL
    if (options.url && !options.url.startsWith('http')) {
      options.url = BASE_URL + (options.url.startsWith('/') ? '' : '/') + options.url
    }

    // 2. 核心：从本地缓存获取 Token 并清洗逻辑
    // 统一使用 App.vue 中的 'auth_token' 键名
    let token = uni.getStorageSync('token') || uni.getStorageSync('auth_token') || ''
    if (token) {
        token = token.trim().replace(/^"|"$/g, '')
    }

    // 3. 自动注入 header
    options.header = {
      ...options.header,
      'token': token
    }

  uni.request({
    url: 'http://127.0.0.1:8000/api/virtual-try-on/generate',
    method: 'POST',
    // 💡 关键修改 1：确保 header 声明为 json
    header: {
        'content-type': 'application/json',
        'token': token
    },
    // 💡 关键修改 2：只发送后端定义的必需字段
    data: {
     person_image: personImgName.value,
     clothing_image: clothingImgName.value
     // 如果后端报错说少了 token，再把 token: token 加回这里
    },
    success: (res) => {
     console.log('API Response Detail:', res.data) // 这里会显示到底是哪个参数错了
     isLoading.value = false

     if (res.statusCode === 200 && res.data && res.data.success) {
      resultImg.value = res.data.data.result_image
      uni.showToast({ title: 'Generation completed!', icon: 'success' })
     } else {
      // 如果还是 422，这里会打印出后端返回的具体错误原因
      const errorMsg = res.data?.detail?.[0]?.msg || res.data?.message || '参数校验失败'
      uni.showToast({
       title: errorMsg,
       icon: 'none'
      })
     }
    },
    fail: (err) => {
     isLoading.value = false
     uni.showToast({ title: 'Network error', icon: 'none' })
    }
   })
  })
}

export const get = (url, data = {}) => request({ url, method: 'GET', data })
export const post = (url, data = {}) => request({ url, method: 'POST', data, header: { 'Content-Type': 'application/json' } })