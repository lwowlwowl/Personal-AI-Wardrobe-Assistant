// 在 frontend/ 目录下创建 tools/request.js
const BASE_URL = 'http://localhost:3000'  // 你的 FastAPI 地址

export const request = (options) => {
  return new Promise((resolve, reject) => {
    // 处理 URL，添加 baseURL
    if (options.url && !options.url.startsWith('http')) {
      options.url = BASE_URL + (options.url.startsWith('/') ? '' : '/') + options.url
    }
    
    uni.request({
      ...options,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(res)
        }
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}

// 也可以封装常用方法
export const get = (url, data = {}) => {
  return request({ url, method: 'GET', data })
}

export const post = (url, data = {}) => {
  return request({ url, method: 'POST', data, header: { 'Content-Type': 'application/json' } })
}