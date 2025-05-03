<script setup>
import { ref } from 'vue';
import axios from 'axios';

const props = defineProps({
  onUploadSuccess: Function // 上传成功后的回调函数
});

const files = ref([]); // 存储选中的文件列表
const uploading = ref(false); // 指示是否正在上传
const errorMessage = ref(''); // 错误消息，由这个组件控制显示
const isDragging = ref(false); // 指示文件是否正在拖拽到区域上
const uploadProgress = ref(0); // 上传进度百分比 (0-100)

// 允许的音频文件MIME类型和常见扩展名
const validTypes = [
  'audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp3', 'audio/ogg',
  'audio/vorbis', 'audio/aac', 'audio/mp4', 'audio/webm'
];
const commonExtensions = ['mp3', 'wav', 'ogg', 'aac', 'm4a', 'flac'];

// 检查文件类型是否有效
const isValidFileType = (file) => {
  const fileExtension = file.name.split('.').pop().toLowerCase();
  return validTypes.includes(file.type) || commonExtensions.includes(fileExtension);
}

// 处理文件选择对话框选择的文件
const handleFileChange = (event) => {
  errorMessage.value = ''; // 清除之前的错误消息
  const selectedFiles = event.target.files;

  files.value = []; // 文件选择替换现有列表
  uploadProgress.value = 0; // 重置进度条

  for (let i = 0; i < selectedFiles.length; i++) {
    const file = selectedFiles[i];
    if (isValidFileType(file)) {
      files.value.push(file);
    } else {
      errorMessage.value = `文件 "${file.name}" 类型无效。请上传有效的音频文件。`;
      files.value = []; // 如果有无效文件，清空列表
      event.target.value = ''; // 清空文件输入框的值
      return; // 发现无效文件立即停止处理
    }
  }
  event.target.value = ''; // 清空文件输入框的值
};

// 处理文件拖拽到区域上
const handleDragOver = (event) => {
  event.preventDefault();
  event.stopPropagation();
  isDragging.value = true;
};

// 处理文件拖拽离开区域
const handleDragLeave = (event) => {
  event.preventDefault();
  event.stopPropagation();
  isDragging.value = false;
};

// 处理文件在区域上释放（拖放完成）
const handleDrop = (event) => {
  event.preventDefault();
  event.stopPropagation();
  isDragging.value = false;
  errorMessage.value = ''; // 清除之前的错误消息
  uploadProgress.value = 0; // 重置进度条

  const droppedFiles = event.dataTransfer.files;

  for (let i = 0; i < droppedFiles.length; i++) {
    const file = droppedFiles[i];
    if (isValidFileType(file)) {
      files.value.push(file); // 拖放是添加到现有列表
    } else {
      errorMessage.value = `文件 "${file.name}" 类型无效。请上传有效的音频文件。`;
    }
  }
  document.getElementById('audio-file').value = ''; // 清空文件输入框的值
};

// 上传文件到服务器
const uploadFiles = async () => {
  if (files.value.length === 0) {
    errorMessage.value = '请先选择文件';
    return;
  }

  uploading.value = true;
  errorMessage.value = '';
  uploadProgress.value = 0;

  try {
    const formData = new FormData();
    files.value.forEach(file => {
      formData.append('files', file);
    });

    // 使用axios上传文件，设置进度监听
    const response = await axios.post('http://localhost:8000/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          // 计算上传进度百分比 (0-100)
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      }
    });

    // 上传成功，清空选择的文件
    files.value = [];
    uploadProgress.value = 100;

    // 如果父组件提供了上传成功的回调，调用它并传递上传结果
    if (props.onUploadSuccess && typeof props.onUploadSuccess === 'function') {
      props.onUploadSuccess(response.data);
    }
  } catch (error) {
    // 处理HTTP错误
    if (error.response) {
      errorMessage.value = error.response.data.detail || '上传失败';
    } else {
      errorMessage.value = '网络错误，请检查连接后重试';
    }
  } finally {
    uploading.value = false;
  }
};

// 用于显示选中的文件名称
const selectedFileNames = () => {
  if (files.value.length === 0) {
    return '选择或拖拽音频文件 (支持多个)';
  } else if (files.value.length === 1) {
    return files.value[0].name;
  } else {
    return `${files.value.length} 个文件已选中`;
  }
};
</script>

<template>
  <div
    class="uploader-container"
    :class="{ 'dragging': isDragging }"
    @dragover.prevent="handleDragOver"
    @dragleave.prevent="handleDragLeave"
    @drop.prevent="handleDrop"
  >
    <h2>上传音频文件</h2>

    <div class="upload-form">
      <div class="file-input-container">
        <input
          type="file"
          id="audio-file"
          accept="audio/*"
          multiple
          @change="handleFileChange"
          :disabled="uploading"
        />
        <label for="audio-file" class="file-label" :class="{ 'disabled': uploading }">
          <i class="upload-icon"></i>
          <span>{{ selectedFileNames() }}</span>
        </label>
      </div>

      <button
        @click="uploadFiles"
        :disabled="files.length === 0 || uploading"
        class="upload-button"
        :class="{ 'uploading': uploading }"
      >
        <span v-if="!uploading">上传</span>
        <span v-else>上传中...</span>
      </button>
    </div>

    <div v-if="uploading || uploadProgress > 0" class="progress-container">
        <div class="progress-bar-bg">
          <div class="progress-bar" :style="{ width: uploadProgress + '%' }">
            <div class="progress-pulse" v-if="uploading"></div>
          </div>
        </div>
        <div class="progress-text">{{ uploadProgress }}%</div>
    </div>

    <div v-if="errorMessage" class="error-message">
      <i class="error-icon"></i>
      <span>{{ errorMessage }}</span>
    </div>

    <div class="upload-info">
      <p>支持的格式: MP3, WAV, OGG 等音频格式</p>
    </div>
  </div>
</template>

<style scoped>
.uploader-container {
  background-color: #f8f9fb;
  border: 2px dashed #ccc;
  border-radius: 12px;
  padding: 25px;
  margin-bottom: 20px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
  text-align: center;
  transition: all 0.3s ease;
}

.uploader-container.dragging {
  border-color: #4caf50;
  background-color: #e8f5e9;
  transform: scale(1.01);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

h2 {
  margin-top: 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin: 20px 0;
  align-items: center;
}

.file-input-container {
  position: relative;
  width: 100%;
  max-width: 500px;
}

input[type="file"] {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  overflow: hidden;
}

.file-label {
  display: block;
  padding: 12px 18px;
  background-color: #ffffff;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  transition: all 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  position: relative;
  font-weight: 500;
}

.file-label:hover {
  border-color: #2196f3;
  background-color: #f0f7ff;
  transform: translateY(-2px);
}

.file-label.disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
  opacity: 0.7;
}

.upload-icon::before {
  content: "📁";
  margin-right: 8px;
}

.upload-button {
  padding: 12px 24px;
  background-color: #2196f3;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  min-width: 120px;
  position: relative;
  overflow: hidden;
}

.upload-button:hover:not(:disabled) {
  background-color: #0b7dda;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.upload-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.upload-button.uploading {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    opacity: 1;
  }
}

.progress-container {
  margin: 15px 0;
  width: 100%;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.progress-bar-bg {
  height: 12px;
  background-color: #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #2196f3, #4caf50);
  border-radius: 6px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-pulse {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 15px;
  background: rgba(255, 255, 255, 0.3);
  animation: pulse-animation 1.5s infinite;
}

@keyframes pulse-animation {
  0% {
    transform: translateX(0);
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: translateX(-100px);
    opacity: 0;
  }
}

.progress-text {
  text-align: center;
  margin-top: 5px;
  font-weight: bold;
  color: #555;
}

.error-message {
  color: #f44336;
  margin: 10px 0;
  padding: 12px 15px;
  border: 1px solid #f44336;
  background-color: #ffebee;
  border-radius: 6px;
  display: flex;
  align-items: center;
  animation: shake 0.5s ease-in-out;
}

.error-icon::before {
  content: "⚠️";
  margin-right: 8px;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.upload-info {
  margin-top: 15px;
  font-size: 0.9rem;
  color: #666;
}

/* 响应式样式 */
@media (max-width: 768px) {
  .uploader-container {
    padding: 15px;
  }
  
  .file-label, .upload-button {
    padding: 10px 15px;
  }
}
</style>
