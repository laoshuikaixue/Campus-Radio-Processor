<script setup>
import { ref, onMounted, computed } from 'vue';
import config from '../config';

const serverUrl = ref(config.API_BASE_URL);
const isConfigOpen = ref(false);
const testStatus = ref('');
const isTesting = ref(false);
const isDarkMode = ref(false);

// 保存配置到localStorage
const saveConfig = () => {
  localStorage.setItem('api_server_url', serverUrl.value);
  // 直接刷新页面以应用新配置
  window.location.reload();
};

// 测试API连接
const testConnection = async () => {
  testStatus.value = '';
  isTesting.value = true;
  
  try {
    const response = await fetch(`${serverUrl.value}/`);
    if (response.ok) {
      testStatus.value = '连接成功！';
    } else {
      testStatus.value = '连接失败：服务器返回错误';
    }
  } catch (error) {
    testStatus.value = `连接失败：${error.message}`;
  } finally {
    isTesting.value = false;
  }
};

// 重置为默认设置
const resetToDefault = () => {
  serverUrl.value = 'http://localhost:8000';
  localStorage.removeItem('api_server_url');
};

// 切换深色模式
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value;
  applyTheme();
};

// 应用主题设置
const applyTheme = () => {
  document.documentElement.classList.toggle('dark-mode', isDarkMode.value);
  localStorage.setItem('dark_mode', isDarkMode.value ? 'true' : 'false');
};

// 创建暗色模式样式
const createDarkModeStyles = () => {
  if (!document.getElementById('dark-mode-styles')) {
    const style = document.createElement('style');
    style.id = 'dark-mode-styles';
    style.textContent = `
      :root.dark-mode {
        --primary-color: #4dabf7;
        --secondary-color: #40c057;
        --danger-color: #fa5252;
        --warning-color: #fcc419;
        --info-color: #15aabf;
        --text-color: #e9ecef;
        --secondary-text-color: #adb5bd;
        --light-bg: #212529;
        --dark-bg: #343a40;
        --border-color: #495057;
        --card-bg: #2b3035;
        --box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.25);
        
        /* 弹窗相关变量 */
        --dialog-title-color: #4dabf7;
        --dialog-title-border: #495057;
        --dialog-bg: #2c3034;
      }
      
      :root.dark-mode body {
        color: var(--text-color);
        background-color: var(--light-bg);
      }
      
      :root.dark-mode .app-header h1 {
        background: linear-gradient(90deg, #4dabf7, #40c057);
        background-clip: text;
        -webkit-background-clip: text;
      }
      
      :root.dark-mode .content-section {
        background-color: var(--card-bg);
        border-color: var(--border-color);
      }
      
      :root.dark-mode .content-section h2 {
        color: #e9ecef;
        border-bottom-color: #495057;
      }
      
      :root.dark-mode input, 
      :root.dark-mode select, 
      :root.dark-mode textarea {
        background-color: #343a40;
        color: #e9ecef;
        border-color: #495057;
      }
      
      :root.dark-mode .audio-item {
        background-color: #343a40;
        border-color: #495057;
      }
      
      :root.dark-mode .audio-item:hover {
        background-color: #3b4248;
      }
      
      :root.dark-mode .background-processing-status {
        background-color: #2c3034;
        border-color: #495057;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      }
      
      :root.dark-mode .background-progress-text {
        color: #e9ecef;
      }
      
      :root.dark-mode .background-processing-info span {
        color: #4dabf7;
      }
      
      :root.dark-mode .app-footer {
        color: var(--secondary-text-color);
        border-color: var(--border-color);
      }
      
      :root.dark-mode .github-link {
        background-color: #343a40;
        color: #e9ecef;
        border-color: #495057;
      }
      
      :root.dark-mode .github-link:hover {
        background-color: #4dabf7;
        color: white;
      }
      
      /* 上传组件深色模式样式 */
      :root.dark-mode .uploader-container {
        background-color: #2c3034;
        border-color: #495057;
      }
      
      :root.dark-mode .uploader-container.dragging {
        border-color: #40c057;
        background-color: #2a3a2e;
      }
      
      :root.dark-mode .file-label {
        background-color: #343a40;
        border-color: #495057;
        color: #e9ecef;
      }
      
      :root.dark-mode .file-label:hover:not(.disabled) {
        border-color: #4dabf7;
        background-color: #3b4248;
      }
      
      :root.dark-mode .error-message {
        background-color: #442a2d;
        border-color: #dc3545;
        color: #ffb0b8;
      }
      
      :root.dark-mode .upload-info {
        color: #adb5bd;
      }
      
      :root.dark-mode .progress-bar-bg {
        background-color: #495057;
      }
      
      :root.dark-mode .merge-dialog {
        background-color: #2c3034;
        color: #e9ecef;
      }
      
      :root.dark-mode .merge-dialog h3 {
        color: #4dabf7;
        border-bottom: 1px solid #495057;
        padding-bottom: 10px;
        margin-bottom: 15px;
      }
      
      :root.dark-mode .merge-form input {
        background-color: #343a40;
        color: #e9ecef;
        border-color: #495057;
      }
      
      :root.dark-mode .merge-progress-bar-bg {
        background-color: #495057;
      }
      
      :root.dark-mode .merge-progress-text {
        color: #e9ecef;
      }
      
      :root.dark-mode .processing-status-text {
        color: #adb5bd;
      }
      
      :root.dark-mode .audio-list-container,
      :root.dark-mode .processed-list-container {
        background-color: #2c3034;
      }
      
      :root.dark-mode .empty-state,
      :root.dark-mode .loading-indicator {
        color: #adb5bd;
      }
      
      :root.dark-mode .test-result {
        color: #e9ecef;
      }
    `;
    document.head.appendChild(style);
  }
};

// 计算主题图标
const themeIcon = computed(() => {
  return isDarkMode.value ? 'moon-icon' : 'sun-icon';
});

// 组件加载时尝试从localStorage读取配置
onMounted(() => {
  // 读取API服务器配置
  const savedUrl = localStorage.getItem('api_server_url');
  if (savedUrl) {
    serverUrl.value = savedUrl;
  }
  
  // 读取主题配置
  const savedDarkMode = localStorage.getItem('dark_mode');
  if (savedDarkMode !== null) {
    isDarkMode.value = savedDarkMode === 'true';
  }
  
  // 应用保存的主题设置
  applyTheme();
  
  // 创建暗色模式样式
  createDarkModeStyles();
});
</script>

<template>
  <div class="server-config-container">
    <div class="server-config">
      <!-- 主题切换按钮 -->
      <button class="theme-toggle" @click="toggleDarkMode" :title="isDarkMode ? '切换到浅色模式' : '切换到深色模式'">
        <i :class="themeIcon"></i>
      </button>
      
      <!-- 设置按钮 -->
      <button class="config-toggle" @click="isConfigOpen = !isConfigOpen">
        <i class="settings-icon"></i>服务器
      </button>
      
      <!-- 设置面板 -->
      <div class="config-panel" v-if="isConfigOpen">
        <h3>后端服务器配置</h3>
        
        <div class="input-group">
          <label for="server-url">API服务器地址:</label>
          <input 
            type="text" 
            id="server-url" 
            v-model="serverUrl" 
            placeholder="例如: http://localhost:8000"
          />
        </div>
        
        <div class="button-group">
          <button class="test-button" @click="testConnection" :disabled="isTesting">
            {{ isTesting ? '测试中...' : '测试连接' }}
          </button>
          <button class="save-button" @click="saveConfig">保存配置</button>
          <button class="reset-button" @click="resetToDefault">重置默认</button>
        </div>
        
        <div class="test-result" v-if="testStatus">
          {{ testStatus }}
        </div>
        
        <div class="config-info">
          <p>注意: 保存后将刷新页面以应用新配置。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.server-config-container {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.5rem;
}

.server-config {
  position: relative;
  display: flex;
  gap: 0.5rem;
}

.config-toggle, .theme-toggle {
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.config-toggle:hover, .theme-toggle:hover {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.theme-toggle {
  width: 2.5rem;
  height: 2.5rem;
  padding: 0;
  justify-content: center;
}

.settings-icon, .sun-icon, .moon-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  margin-right: 5px;
  background-repeat: no-repeat;
  background-size: contain;
}

.settings-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 512 512'%3E%3Cpath d='M495.9 166.6c3.2 8.7 .5 18.4-6.4 24.6l-43.3 39.4c1.1 8.3 1.7 16.8 1.7 25.4s-.6 17.1-1.7 25.4l43.3 39.4c6.9 6.2 9.6 15.9 6.4 24.6c-4.4 11.9-9.7 23.3-15.8 34.3l-4.7 8.1c-6.6 11-14 21.4-22.1 31.2c-5.9 7.2-15.7 9.6-24.5 6.8l-55.7-17.7c-13.4 10.3-28.2 18.9-44 25.4l-12.5 57.1c-2 9.1-9 16.3-18.2 17.8c-13.8 2.3-28 3.5-42.5 3.5s-28.7-1.2-42.5-3.5c-9.2-1.5-16.2-8.7-18.2-17.8l-12.5-57.1c-15.8-6.5-30.6-15.1-44-25.4L83.1 425.9c-8.8 2.8-18.6 .3-24.5-6.8c-8.1-9.8-15.5-20.2-22.1-31.2l-4.7-8.1c-6.1-11-11.4-22.4-15.8-34.3c-3.2-8.7-.5-18.4 6.4-24.6l43.3-39.4C64.6 273.1 64 264.6 64 256s.6-17.1 1.7-25.4L22.4 191.2c-6.9-6.2-9.6-15.9-6.4-24.6c4.4-11.9 9.7-23.3 15.8-34.3l4.7-8.1c6.6-11 14-21.4 22.1-31.2c5.9-7.2 15.7-9.6 24.5-6.8l55.7 17.7c13.4-10.3 28.2-18.9 44-25.4l12.5-57.1c2-9.1 9-16.3 18.2-17.8C227.3 1.2 241.5 0 256 0s28.7 1.2 42.5 3.5c9.2 1.5 16.2 8.7 18.2 17.8l12.5 57.1c15.8 6.5 30.6 15.1 44 25.4l55.7-17.7c8.8-2.8 18.6-.3 24.5 6.8c8.1 9.8 15.5 20.2 22.1 31.2l4.7 8.1c6.1 11 11.4 22.4 15.8 34.3zM256 336c44.2 0 80-35.8 80-80s-35.8-80-80-80s-80 35.8-80 80s35.8 80 80 80z'/%3E%3C/svg%3E");
}

.sun-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 512 512'%3E%3Cpath d='M361.5 1.2c5 2.1 8.6 6.6 9.6 11.9L391 121l107.9 19.8c5.3 1 9.8 4.6 11.9 9.6s1.5 10.7-1.6 15.2L446.9 256l62.3 90.3c3.1 4.5 3.7 10.2 1.6 15.2s-6.6 8.6-11.9 9.6L391 391 371.1 498.9c-1 5.3-4.6 9.8-9.6 11.9s-10.7 1.5-15.2-1.6L256 446.9l-90.3 62.3c-4.5 3.1-10.2 3.7-15.2 1.6s-8.6-6.6-9.6-11.9L121 391 13.1 371.1c-5.3-1-9.8-4.6-11.9-9.6s-1.5-10.7 1.6-15.2L65.1 256 2.8 165.7c-3.1-4.5-3.7-10.2-1.6-15.2s6.6-8.6 11.9-9.6L121 121 140.9 13.1c1-5.3 4.6-9.8 9.6-11.9s10.7-1.5 15.2 1.6L256 65.1 346.3 2.8c4.5-3.1 10.2-3.7 15.2-1.6zM160 256a96 96 0 1 1 192 0 96 96 0 1 1 -192 0zm224 0a128 128 0 1 0 -256 0 128 128 0 1 0 256 0z'/%3E%3C/svg%3E");
  margin-right: 0;
}

.moon-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='white' viewBox='0 0 384 512'%3E%3Cpath d='M223.5 32C100 32 0 132.3 0 256S100 480 223.5 480c60.6 0 115.5-24.2 155.8-63.4c5-4.9 6.3-12.5 3.1-18.7s-10.1-9.7-17-8.5c-9.8 1.7-19.8 2.6-30.1 2.6c-96.9 0-175.5-78.8-175.5-176c0-65.8 36-123.1 89.3-153.3c6.1-3.5 9.2-10.5 7.7-17.3s-7.3-11.9-14.3-12.5c-6.3-.5-12.6-.8-19-.8z'/%3E%3C/svg%3E");
  margin-right: 0;
}

.config-panel {
  position: absolute;
  top: 100%;
  right: 0;
  background-color: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px; /* 增大圆角 */
  padding: 1.25rem; /* 增大内边距 */
  margin-top: 0.5rem;
  box-shadow: var(--box-shadow);
  z-index: 1000;
  width: 350px;
  color: var(--text-color);
}

.input-group {
  margin-bottom: 1rem;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.input-group input {
  width: 100%;
  padding: 0.75rem; /* 增大输入框内边距 */
  border: 1px solid var(--border-color);
  border-radius: 6px; /* 增大输入框圆角 */
  background-color: var(--dark-bg);
  color: var(--text-color);
  font-size: 1rem; /* 增大字体 */
  transition: border-color 0.3s, box-shadow 0.3s;
}

.input-group input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(77, 171, 247, 0.2);
  outline: none;
}

.button-group {
  display: flex;
  gap: 0.75rem; /* 增大按钮间距 */
  margin-bottom: 1rem;
}

.test-button, .save-button, .reset-button {
  padding: 0.6rem 1.2rem; /* 增大按钮内边距 */
  border: none;
  border-radius: 6px; /* 增大按钮圆角 */
  cursor: pointer;
  font-size: 0.95rem; /* 增大字体 */
  font-weight: 500;
  transition: all 0.2s ease;
}

.test-button {
  background-color: var(--info-color);
  color: white;
  flex: 1;
}

.test-button:hover:not(:disabled) {
  background-color: #1098a8;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.test-button:disabled {
  background-color: var(--secondary-text-color);
  cursor: not-allowed;
}

.save-button {
  background-color: var(--secondary-color);
  color: white;
  flex: 1;
}

.save-button:hover {
  background-color: #37b24d;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.reset-button {
  background-color: var(--secondary-text-color);
  color: white;
  flex: 1;
}

.reset-button:hover {
  background-color: #868e96;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.test-result {
  padding: 0.75rem; /* 增大内边距 */
  margin-bottom: 1rem;
  border-radius: 6px; /* 增大圆角 */
  background-color: var(--dark-bg);
  font-size: 0.95rem; /* 增大字体 */
  font-weight: 500;
}

.config-info {
  font-size: 0.85rem;
  color: var(--secondary-text-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .server-config {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  
  .config-panel {
    width: 100%;
    max-width: 350px;
  }
}

@media (max-width: 480px) {
  .config-toggle span {
    display: none;
  }
  
  .config-panel {
    width: calc(100vw - 2rem);
    right: -1rem;
  }
}
</style> 