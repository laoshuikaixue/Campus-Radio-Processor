import axios from 'axios';
import config from './config';

// 创建获取最新baseURL的函数
const getBaseURL = () => {
  // 优先从localStorage获取，确保实时更新
  const savedUrl = localStorage.getItem('api_server_url');
  return savedUrl || config.API_BASE_URL;
};

// 创建axios实例的工厂函数
const createApiClient = () => {
  return axios.create({
    baseURL: getBaseURL(),
    headers: {
      'Content-Type': 'application/json'
    }
  });
};

// API服务对象
const api = {
  // 音频上传
  uploadFiles(formData, onProgress) {
    const client = createApiClient();
    return client.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    });
  },

  // 获取待处理音频列表
  getAudioFiles() {
    const client = createApiClient();
    return client.get('/api/audio');
  },

  // 获取已处理音频列表
  getProcessedFiles() {
    const client = createApiClient();
    return client.get('/api/processed');
  },

  // 删除单个待处理音频
  deleteAudio(id) {
    const client = createApiClient();
    return client.delete(`/api/audio/${id}`);
  },

  // 删除所有待处理音频
  deleteAllAudio() {
    const client = createApiClient();
    return client.delete('/api/audio/all');
  },

  // 删除单个已处理音频
  deleteProcessedAudio(id) {
    const client = createApiClient();
    return client.delete(`/api/processed/${id}`);
  },

  // 删除所有已处理音频
  deleteAllProcessedAudio() {
    const client = createApiClient();
    return client.delete('/api/processed/all');
  },

  // 更新待处理音频信息
  updateAudio(id, data) {
    const client = createApiClient();
    return client.put(`/api/audio/${id}`, data);
  },

  // 更新已处理音频信息
  updateProcessedAudio(id, data) {
    const client = createApiClient();
    return client.put(`/api/processed/${id}`, data);
  },

  // 合并音频文件
  mergeAudioFiles(data) {
    const client = createApiClient();
    return client.post('/api/merge', data);
  },

  // 取消处理
  cancelProcessing(data) {
    const client = createApiClient();
    return client.post('/api/cancel-processing', data);
  },

  // 检查处理状态
  checkProcessingStatus(data) {
    const client = createApiClient();
    return client.post('/api/check-processing-status', data);
  },

  // 重新排序音频文件
  reorderAudio(data) {
    const client = createApiClient();
    return client.post('/api/reorder', data);
  },

  // 获取下载地址
  getDownloadUrl(audioId) {
    return `${getBaseURL()}/api/download/${audioId}`;
  },
  
  // 轮询检查处理状态 - 当WebSocket连接不可靠时使用
  pollProcessingStatus(requestId, callback, interval = 3000, maxAttempts = 100) {
    let attempts = 0;
    
    const checkStatus = async () => {
      try {
        if (attempts >= maxAttempts) {
          console.log('达到最大轮询次数，停止轮询');
          return;
        }
        
        attempts++;
        
        const response = await this.checkProcessingStatus({ requestId });
        const status = response.data.status;
        
        // 调用回调函数，传递状态信息
        if (callback && typeof callback === 'function') {
          callback(response.data);
        }
        
        // 如果处理已完成或失败或取消，停止轮询
        if (status === 'completed' || status === 'failed' || status === 'cancelled') {
          console.log(`处理状态: ${status}，停止轮询`);
          return;
        }
        
        // 否则继续轮询
        setTimeout(checkStatus, interval);
      } catch (error) {
        console.error('轮询处理状态时出错:', error);
        setTimeout(checkStatus, interval * 2); // 出错时增加轮询间隔
      }
    };
    
    // 开始轮询
    checkStatus();
  }
};

export default api; 