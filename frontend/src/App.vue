<script setup>
import { ref, watch } from 'vue';
import AudioUploader from './components/AudioUploader.vue'; // 导入音频上传组件
import AudioList from './components/AudioList.vue'; // 导入待处理音频列表组件
import ProcessedAudioList from './components/ProcessedAudioList.vue'; // 导入已处理音频列表组件
import ServerConfig from './components/ServerConfig.vue'; // 导入服务器配置组件
import MergeProgressFloat from './components/MergeProgressFloat.vue';
import { mergeTaskStore } from './store/mergeTask';

const audioListRef = ref(null); // 创建对待处理列表组件实例的引用
const processedAudioListRef = ref(null); // 创建对已处理列表组件实例的引用

// 合并任务完成后刷新已处理音频列表
watch(() => mergeTaskStore.status, (val) => {
  if (val === 'completed' && processedAudioListRef.value && processedAudioListRef.value.fetchProcessedFiles) {
    processedAudioListRef.value.fetchProcessedFiles();
  }
});

function handleMergeCancel() {
  // 取消合并任务
  if (mergeTaskStore.requestId) {
    import('./api').then(api => {
      api.default.cancelProcessing({ requestId: mergeTaskStore.requestId });
    });
  }
}
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <h1>校园广播站音频处理系统</h1>
        <ServerConfig />
      </div>
    </header>

    <main class="app-content">
      <section class="content-section upload-section">
          <h2>上传音频文件</h2>
          <AudioUploader />
      </section>

      <section class="content-section pending-section">
          <h2>待处理音频列表</h2>
          <AudioList ref="audioListRef" />
      </section>

      <section class="content-section processed-section">
          <h2>已处理音频列表</h2>
          <ProcessedAudioList ref="processedAudioListRef" />
      </section>
    </main>

    <footer class="app-footer">
      <p>校园广播站音频处理系统 | Powered By LaoShui @ {{ new Date().getFullYear() }} | 
        <a href="https://github.com/laoshuikaixue/Campus-Radio-Processor" target="_blank" class="github-link">
          https://github.com/laoshuikaixue/Campus-Radio-Processor
        </a>
      </p>
    </footer>

    <!-- 合并进度浮窗 -->
    <MergeProgressFloat
      v-if="mergeTaskStore.show"
      :progress="mergeTaskStore.progress"
      :status="mergeTaskStore.status"
      :message="mergeTaskStore.message"
      :can-cancel="mergeTaskStore.status === 'processing'"
      :on-cancel="handleMergeCancel"
      :on-close="() => mergeTaskStore.reset()"
    />
  </div>
</template>

<style>
/* 全局样式 */
:root {
  --primary-color: #007bff; /* 现代蓝色 */
  --secondary-color: #28a745; /* 现代绿色 */
  --danger-color: #dc3545; /* 现代红色 */
  --warning-color: #ffc107; /* 现代黄色/橙色 */
  --info-color: #17a2b8; /* 现代青色 */
  --text-color: #343a40; /* 更深的文本颜色以提高对比度 */
  --secondary-text-color: #6c757d; /* 用于次要信息的浅色文本 */
  --light-bg: #f8f9fa; /* 非常浅的灰色背景 */
  --dark-bg: #e9ecef; /* 略深的灰色背景以形成对比 */
  --border-color: #dee2e6; /* 浅灰色边框 */
  --card-bg: #ffffff; /* 用于卡片/部分的白色背景 */
  --box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.08); /* 微妙的阴影 */
  --border-radius: 0.25rem; /* 小的边框圆角 */
  --spacing-unit: 1rem; /* 基本间距单位 */
}

body {
  margin: 0;
  font-family: 'Roboto', sans-serif; /* 使用 Roboto，一种常见的现代字体 */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text-color);
  background-color: var(--light-bg);
  line-height: 1.6;
  padding-top: 0; /* 移除默认的 body 内边距 */
}

h1, h2, h3, h4, h5, h6 {
    color: var(--text-color);
    margin-top: 0;
    margin-bottom: var(--spacing-unit);
    font-weight: 500; /* 标题使用略轻的字体粗细 */
}

p {
    margin-top: 0;
    margin-bottom: var(--spacing-unit);
}

/* 添加全局 box-sizing 以便于布局 */
*, *::before, *::after {
    box-sizing: border-box;
}
</style>

<style scoped>
/* App.vue 布局样式 */
.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: calc(var(--spacing-unit) * 2); /* 更多内边距 */
  display: flex;
  flex-direction: column;
  min-height: 100vh; /* 确保容器至少占据完整的视口高度 */
}

.app-header {
  margin-bottom: calc(var(--spacing-unit) * 2); /* 头部下方更多空间 */
  padding-bottom: var(--spacing-unit);
  border-bottom: 1px solid var(--border-color); /* 分隔线 */
  animation: slide-down 0.5s ease-out;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.app-header h1 {
  color: var(--primary-color);
  font-size: 2.5rem; /* 更大的标题字体 */
  margin: 0;
  font-weight: 700; /* 标题使用更粗的字体 */
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  background: linear-gradient(90deg, var(--primary-color), #28a745);
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
}

.app-content {
  flex-grow: 1; /* 允许内容区域扩展 */
  display: flex;
  flex-direction: column;
  gap: calc(var(--spacing-unit) * 1.5); /* 增加不同部分之间的间距 */
  animation: fade-in 0.6s ease-out;
}

/* 单个内容部分的样式 */
.content-section {
    background-color: var(--card-bg); /* 卡片背景色 */
    padding: calc(var(--spacing-unit) * 1.5); /* 内边距 */
    border-radius: var(--border-radius); /* 圆角 */
    box-shadow: var(--box-shadow); /* 应用微妙的阴影 */
    border: 1px solid var(--border-color); /* 微妙的边框 */
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.content-section:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.content-section h2 {
    font-size: 1.5rem; /* 略大的部分标题字体 */
    margin-bottom: var(--spacing-unit);
    padding-bottom: var(--spacing-unit) * 0.5;
    border-bottom: 1px solid var(--dark-bg); /* 部分标题下方的分隔线 */
    color: var(--secondary-text-color); /* 部分标题使用柔和的颜色 */
    font-weight: 600; /* 增加标题字重 */
    letter-spacing: 0.5px; /* 增加字间距提高可读性 */
}


.app-footer {
  margin-top: calc(var(--spacing-unit) * 3); /* 底部上方更多空间 */
  text-align: center;
  font-size: 0.9rem;
  color: var(--secondary-text-color); /* 底部文本使用柔和的颜色 */
  padding: var(--spacing-unit) 0;
  border-top: 1px solid var(--border-color); /* 分隔线 */
  animation: fade-in 0.8s ease-out;
}

.app-footer p {
    margin: 0; /* 移除默认的段落外边距 */
}

.github-link {
    display: inline-flex;
    align-items: center;
    color: #24292e;
    text-decoration: none;
    padding: 5px 10px;
    background-color: #f6f8fa;
    border-radius: 6px;
    border: 1px solid #e1e4e8;
    transition: all 0.3s ease;
    font-weight: 500;
    margin-left: 5px;
}

.github-link:hover {
    background-color: #0366d6;
    color: white;
    border-color: #0366d6;
    transform: translateY(-2px);
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
}

/* 动画效果 */
@keyframes fade-in {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

@keyframes slide-down {
  0% { 
    opacity: 0;
    transform: translateY(-20px);
  }
  100% { 
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式调整 */
@media (max-width: 768px) {
  .app-container {
    padding: var(--spacing-unit); /* 在小屏幕上减少内边距 */
  }

  .app-header h1 {
    font-size: 2rem; /* 调整头部字体大小 */
    text-align: center;
    margin-bottom: 0.5rem;
  }
  
  .header-content {
    justify-content: center;
  }

  .content-section {
      padding: var(--spacing-unit); /* 减少部分内边距 */
  }

  .content-section h2 {
      font-size: 1.3rem; /* 调整部分标题字体大小 */
  }
}

@media (max-width: 480px) {
    .app-header h1 {
        font-size: 1.8rem;
    }

    .content-section h2 {
        font-size: 1.2rem;
    }
}
</style>

<style>
/* 全局动画和交互效果 */
.page-transition-enter-active,
.page-transition-leave-active {
  transition: opacity 0.3s ease;
}

.page-transition-enter-from,
.page-transition-leave-to {
  opacity: 0;
}

/* 按钮和交互元素的统一过渡效果 */
button, a, .interactive {
  transition: all 0.3s ease;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 保证全局深浅色适配 */
body.dark {
  background: #181a20;
  color: #f1f1f1;
}
body.light {
  background: #fff;
  color: #222;
}
</style>
