import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  css: {
    preprocessorOptions: {
      scss: {
        // Vite 5.x 仍以 sass.render（legacy API）编译；在升级至支持 modern API 的构建链之前，先静音此弃用提示
        silenceDeprecations: ['legacy-js-api']
      }
    }
  }
})
