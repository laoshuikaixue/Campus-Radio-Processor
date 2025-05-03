import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import config from './config'

// 从localStorage中加载API服务器URL（如果存在）
const savedApiUrl = localStorage.getItem('api_server_url');
if (savedApiUrl) {
  // 动态更新配置
  config.API_BASE_URL = savedApiUrl;
}

createApp(App).mount('#app')
