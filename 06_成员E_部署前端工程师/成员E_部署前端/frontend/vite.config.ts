import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true, // 监听 0.0.0.0, 允许局域网通过 http://<本机IP>:5173 访问
    port: 5173,
    strictPort: true, // 端口被占直接报错, 避免换了端口别人找不到
    // 忽略编辑器/工具产生的临时文件, 避免 Windows 文件监听 EBUSY 崩溃
    watch: {
      ignored: ['**/.tmpdir/**', '**/*.tmp', '**/node_modules/**'],
    },
    // 开发环境代理: /api -> 后端 FastAPI
    // 前端用相对路径 /api 请求 → 浏览器发给"页面所在主机":5173 → vite 转给 8000
    // 这样局域网内其他电脑访问也能正确拿到后端数据(无需各自配置地址)
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
