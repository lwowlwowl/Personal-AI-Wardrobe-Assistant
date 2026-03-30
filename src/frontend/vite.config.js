import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  css: {
    preprocessorOptions: {
      scss: {
        // Vite 5.x still compiles via sass.render (legacy API); silence until the toolchain supports the modern API
        silenceDeprecations: ['legacy-js-api']
      }
    }
  }
})
