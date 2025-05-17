import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import config from './config'
import { mergeTaskStore } from './store/mergeTask';
import api from './api';

// 从localStorage中加载API服务器URL（如果存在）
const savedApiUrl = localStorage.getItem('api_server_url');
if (savedApiUrl) {
  // 动态更新配置
  config.API_BASE_URL = savedApiUrl;
}

let pollTimer = null;

function startPollingMergeStatus() {
  if (!mergeTaskStore.requestId) return;
  stopPollingMergeStatus();
  pollTimer = setInterval(async () => {
    try {
      const res = await api.checkProcessingStatus({ requestId: mergeTaskStore.requestId });
      if (res.data) {
        mergeTaskStore.status = res.data.status;
        mergeTaskStore.progress = res.data.progress || (res.data.status === 'completed' ? 100 : 0);
        mergeTaskStore.message = res.data.message || '';
        mergeTaskStore.currentFileIndex = res.data.currentFileIndex || 0;
        mergeTaskStore.totalFilesCount = res.data.totalFilesCount || 0;
        mergeTaskStore.show = true;
        if (res.data.status === 'completed' || res.data.status === 'failed' || res.data.status === 'cancelled') {
          stopPollingMergeStatus();
        }
      }
    } catch (e) {
      // 网络异常等，忽略
    }
  }, 800);
}
function stopPollingMergeStatus() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}
// 合并任务发起后自动开始轮询
mergeTaskStore.__startPolling = startPollingMergeStatus;
mergeTaskStore.__stopPolling = stopPollingMergeStatus;

createApp(App).mount('#app')
