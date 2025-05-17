<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';
import api from '../api';
import { audioState } from '../audioState';

const processedFiles = ref([]);
const loading = ref(true);
const error = ref('');
const editingFile = ref(null);
const newDisplayName = ref('');

// 获取所有已处理的音频文件
const fetchProcessedFiles = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    const response = await api.getProcessedFiles();
    processedFiles.value = response.data;
  } catch (err) {
    error.value = '无法加载已处理音频文件列表';
  } finally {
    // 添加一个短暂的延迟，避免刷新过快导致闪烁
    setTimeout(() => {
      loading.value = false;
    }, 500); // 延迟500毫秒
  }
};

// 初始加载
onMounted(() => {
  fetchProcessedFiles();
});

// 添加新处理的文件到列表
const addNewProcessedFile = (file) => {
  processedFiles.value.push(file);
};

// 删除音频文件
const deleteFile = async (id) => {
  if (!confirm('确定要删除这个已处理的音频文件吗？')) return;

  try {
    await api.deleteProcessedAudio(id);
    processedFiles.value = processedFiles.value.filter(file => file.id !== id);
  } catch (err) {
    error.value = '删除文件时出错';
  }
};

// 删除所有已处理的音频文件
const deleteAllProcessedFiles = async () => {
  if (!confirm('确定要删除所有已处理的音频文件吗？此操作不可恢复！')) return;

  try {
    await api.deleteAllProcessedAudio();
    processedFiles.value = [];
  } catch (err) {
    error.value = '删除所有已处理文件时出错';
  }
};

// 开始编辑文件名
const startEdit = (file) => {
  editingFile.value = file.id;
  newDisplayName.value = file.displayName;
  
  // 聚焦将在指令中处理
};

// 保存编辑后的文件名
const saveEdit = async (file) => {
  if (!newDisplayName.value.trim()) {
    error.value = '显示名称不能为空';
    return;
  }

  try {
    const response = await api.updateProcessedAudio(file.id, {
      displayName: newDisplayName.value.trim()
    });

    const index = processedFiles.value.findIndex(f => f.id === file.id);
    if (index !== -1) {
      processedFiles.value[index].displayName = response.data.displayName;
    }

    editingFile.value = null;
    newDisplayName.value = '';
  } catch (err) {
    error.value = err.response?.data?.detail || '更新文件名时出错';
  }
};

// 取消编辑
const cancelEdit = () => {
  editingFile.value = null;
  newDisplayName.value = '';
};

// 下载音频文件
const downloadFile = (id, displayName) => {
  window.open(api.getDownloadUrl(id), '_blank');
};

// 格式化时长（移至组件内定义）
const formatDuration = (seconds) => {
  if (!seconds && seconds !== 0) return '未知';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 100); // 获取毫秒部分并转换为两位数
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
};

// 添加自动聚焦输入框的自定义指令
const vFocus = {
  mounted: (el) => el.focus()
};

// 导出组件方法和属性
defineExpose({
  addNewProcessedFile,
  fetchProcessedFiles
});
</script>

<template>
  <div class="processed-list-container">
    <h2>已处理音频文件列表</h2>

    <div v-if="loading" class="loading-indicator">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="processedFiles.length === 0" class="empty-state">
      <i class="empty-icon"></i>
      <p>没有已处理的音频文件。</p>
    </div>

    <div v-else>
      <div class="actions-bar">
        <div class="left-actions">
          <button
            @click="deleteAllProcessedFiles"
            class="delete-all-btn"
          >
            <i class="delete-icon"></i>
            删除所有已处理文件
          </button>
        </div>
        <button @click="fetchProcessedFiles" class="refresh-button">
          <i class="refresh-icon"></i> 刷新列表
        </button>
      </div>

      <div class="audio-list">
        <transition-group name="audio-item-transition">
          <div
            v-for="file in processedFiles"
            :key="file.id"
            class="audio-item"
          >
            <div class="audio-item-header">
              <div class="audio-info">
                <div v-if="editingFile === file.id" class="edit-name-form">
                  <input
                    type="text"
                    v-model="newDisplayName"
                    @keyup.enter="saveEdit(file)"
                    class="edit-name-input"
                    ref="editInput"
                    v-focus
                  />
                  <div class="edit-actions">
                    <button @click="saveEdit(file)" class="save-btn">保存</button>
                    <button @click="cancelEdit" class="cancel-btn">取消</button>
                  </div>
                </div>
                <div v-else class="audio-name-container">
                  <span class="audio-name">{{ file.displayName }}</span>
                  <button @click="startEdit(file)" class="edit-btn">
                    <i class="edit-icon"></i>重命名
                  </button>
                </div>
                <div class="audio-meta">
                  <span class="duration">
                    <i class="time-icon"></i>时长: {{ formatDuration(file.duration) }}
                    <template v-if="file.normalizeVolume">
                      <span class="normalize-badge" :title="`已标准化到 ${file.normalizeTargetDb} dB`">
                        <i class="volume-icon"></i>音量已标准化 ({{ file.normalizeTargetDb }} dB)
                      </span>
                    </template>
                  </span>
                  <span class="processed-badge">
                    <i class="check-icon"></i>已处理
                  </span>
                </div>
              </div>
            </div>

            <div class="audio-actions">
              <button @click="downloadFile(file.id, file.displayName)" class="download-btn">
                <i class="download-icon"></i>
                下载
              </button>
              <button @click="deleteFile(file.id)" class="delete-btn">
                <i class="delete-icon"></i>
                删除
              </button>
            </div>
          </div>
        </transition-group>
      </div>
    </div>

    <p v-if="error" class="error-message">
      <i class="error-icon"></i>
      <span>{{ error }}</span>
    </p>
  </div>
</template>

<style scoped>
.processed-list-container {
  background-color: #ffffff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
  margin-top: 20px;
}

h2 {
  margin-top: 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.loading-indicator, .empty-state {
  text-align: center;
  padding: 30px;
  color: #666;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid #2196f3;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-icon::before {
  content: "📂";
  font-size: 2rem;
  margin-bottom: 10px;
  opacity: 0.5;
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.left-actions {
  display: flex;
  gap: 10px;
}

.delete-all-btn {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.delete-all-btn:hover {
  background-color: #d32f2f;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.audio-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 交互动画效果 */
.audio-item-transition-enter-active,
.audio-item-transition-leave-active {
  transition: all 0.5s ease;
}

.audio-item-transition-enter-from,
.audio-item-transition-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

.audio-item-transition-leave-active {
  position: absolute;
  width: 100%;
}

.audio-item {
  display: flex;
  flex-direction: column;
  background-color: #f9f9f9;
  border-radius: 10px;
  padding: 15px;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
}

@media (min-width: 768px) {
  .audio-item {
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
  }
  .audio-actions {
    margin-top: 0;
  }
}

.audio-item:hover {
  background-color: #f0f7ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.06);
}

.audio-item-header {
  display: flex;
  align-items: flex-start;
  flex: 1;
  margin-bottom: 10px;
}

@media (min-width: 768px) {
  .audio-item-header {
    margin-bottom: 0;
    align-items: center;
  }
}

.audio-info {
  flex: 1;
}

.audio-name-container {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
}

.audio-name {
  font-weight: bold;
  margin-right: 10px;
  word-break: break-word;
}

.edit-btn, .save-btn, .cancel-btn {
  background: none;
  border: none;
  font-size: 0.8rem;
  color: #2196f3;
  cursor: pointer;
  padding: 2px 5px;
  line-height: 1;
  transition: all 0.2s ease;
}

.edit-btn:hover, .save-btn:hover {
  text-decoration: underline;
  transform: translateY(-1px);
}

.cancel-btn {
  color: #f44336;
}

.cancel-btn:hover {
  text-decoration: underline;
}

.edit-name-form {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 5px;
}

.edit-name-input {
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  transition: border-color 0.3s ease;
}

.edit-name-input:focus {
  border-color: #2196f3;
  outline: none;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.edit-actions {
  display: flex;
  gap: 10px;
}

.audio-meta {
  font-size: 0.85rem;
  color: #666;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.processed-badge {
  display: inline-flex;
  align-items: center;
  color: #4caf50;
  font-weight: 500;
}

.normalize-badge {
  display: inline-flex;
  align-items: center;
  color: #2196f3;
  font-weight: 500;
  font-size: 0.8rem;
  margin-left: 5px;
  padding: 2px 6px;
  background-color: rgba(33, 150, 243, 0.1);
  border-radius: 4px;
  transition: all 0.3s ease;
}

.normalize-badge:hover {
  background-color: rgba(33, 150, 243, 0.2);
}

.audio-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-shrink: 0;
  margin-top: 10px;
}

.download-btn, .delete-btn {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  font-weight: 500;
}

.download-btn {
  background-color: #4caf50;
  color: white;
}

.download-btn:hover {
  background-color: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.delete-btn {
  background-color: #f44336;
  color: white;
}

.delete-btn:hover {
  background-color: #d32f2f;
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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

/* 图标样式 */
.delete-icon::before {
  content: "🗑️";
  margin-right: 8px;
}

.edit-icon::before {
  content: "✏️";
  margin-right: 5px;
}

.time-icon::before {
  content: "⏱️";
  margin-right: 5px;
}

.check-icon::before {
  content: "✅";
  margin-right: 5px;
}

.download-icon::before {
  content: "💾";
  margin-right: 5px;
}

.volume-icon::before {
  content: "🔊";
  margin-right: 5px;
}

/* 刷新按钮样式 (与AudioList.vue中保持一致) */
.refresh-button {
  background-color: #6c757d; /* 灰色背景 */
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s;
  display: flex;
  align-items: center;
}

.refresh-button:hover:not(:disabled) {
  background-color: #5a6268;
}

.refresh-icon::before {
  content: "🔄"; /* 刷新图标 */
  margin-right: 5px;
}
</style>