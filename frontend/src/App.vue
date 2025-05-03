<script setup>
import { ref } from 'vue';
import AudioUploader from './components/AudioUploader.vue'; // 导入音频上传组件
import AudioList from './components/AudioList.vue'; // 导入待处理音频列表组件
import ProcessedAudioList from './components/ProcessedAudioList.vue'; // 导入已处理音频列表组件

const audioListRef = ref(null); // 创建对待处理列表组件实例的引用
const processedAudioListRef = ref(null); // 创建对已处理列表组件实例的引用

// 处理 AudioUploader 上传成功后的回调函数
// AudioUploader 组件会通过 props 将后端返回的上传结果列表传递给这个方法
const handleUploadSuccess = (uploadedItems) => {
  console.log("App.vue 接收到上传成功通知", uploadedItems);
  // 调用 AudioList 组件的方法来处理上传结果并刷新列表
  // 假设 AudioList 组件有一个名为 processUploadedItems 的方法来接收并处理上传成功的项
  if (audioListRef.value && audioListRef.value.processUploadedItems) {
    audioListRef.value.processUploadedItems(uploadedItems);
  } else {
      console.error("AudioList 组件引用或 processUploadedItems 方法不可用.");
      // 如果无法调用特定处理方法，至少尝试刷新待处理列表
      if (audioListRef.value && audioListRef.value.fetchAudioFiles) {
          audioListRef.value.fetchAudioFiles();
      }
  }
};

// 处理 AudioList 或 ProcessedAudioList 完成处理（例如合并）后的回调函数
// ProcessedAudioList 也应该会触发 'process-success' 事件
const handleProcessSuccess = (processedItem) => {
  console.log("App.vue 接收到处理成功通知", processedItem);
  // 处理成功后，通常需要刷新 已处理列表ProcessedAudioList
  // 假设 ProcessedAudioList 组件有一个名为 fetchProcessedFiles 的方法来刷新列表
  if (processedAudioListRef.value && processedAudioListRef.value.fetchProcessedFiles) {
      processedAudioListRef.value.fetchProcessedFiles();
  } else {
       console.error("ProcessedAudioList 组件引用或 fetchProcessedFiles 方法不可用.");
  }
  // 同时，如果处理（合并）成功，原始文件可能从待处理列表移除，所以也需要刷新 待处理列表AudioList
    if (audioListRef.value && audioListRef.value.fetchAudioFiles) {
      audioListRef.value.fetchAudioFiles();
  } else {
       console.error("AudioList 组件引用或 fetchAudioFiles 方法不可用.");
  }
};
</script>

<template>
  <div class="app-container">
    <header class="app-header">
      <h1>校园广播站音频处理系统</h1>
    </header>

    <main class="app-content">
      <section class="content-section upload-section">
          <h2>上传音频文件</h2>
          <AudioUploader :onUploadSuccess="handleUploadSuccess" />
      </section>

      <section class="content-section pending-section">
          <h2>待处理音频列表</h2>
          <AudioList ref="audioListRef" @process-success="handleProcessSuccess" />
      </section>

      <section class="content-section processed-section">
          <h2>已处理音频列表</h2>
          <ProcessedAudioList ref="processedAudioListRef" />
      </section>
    </main>

    <footer class="app-footer">
      <p>校园广播站音频处理系统 | Powered By LaoShui @ {{ new Date().getFullYear() }}</p>
    </footer>
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
  text-align: center;
  margin-bottom: calc(var(--spacing-unit) * 2); /* 头部下方更多空间 */
  padding-bottom: var(--spacing-unit);
  border-bottom: 1px solid var(--border-color); /* 分隔线 */
  animation: slide-down 0.5s ease-out;
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
</style>
