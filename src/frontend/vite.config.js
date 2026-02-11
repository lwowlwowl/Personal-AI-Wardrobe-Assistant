import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni' // 1. 必须改用 UniApp 专用插件

export default defineConfig({
  plugins: [
    uni(), // 2. 替换掉原来的 vue()
  ],
  server: {
    port: 5173,
    proxy: {
      // 代理API请求
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      // 代理图片请求
      '/GRP_CODE/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
