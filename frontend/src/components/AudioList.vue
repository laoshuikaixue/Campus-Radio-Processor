<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue';
import axios from 'axios';
import { audioState } from '../audioState';

const emit = defineEmits(['process-success']); // 用于通知父组件处理成功的事件（例如合并）

const audioFiles = ref([]); // 存储未处理音频文件列表
const loading = ref(true);
const error = ref(''); // 用于显示加载错误和上传结果/错误消息
const mergeDialogOpen = ref(false); // 合并对话框状态
const mergeOutputName = ref(''); // 合并输出文件名
const processingMerge = ref(false); // 合并处理状态
const editingFile = ref(null); // 正在编辑的文件ID
const newDisplayName = ref(''); // 新的显示名称
const mergeProgress = ref(0); // 合并过程进度
const mergeProgressInterval = ref(null); // 进度条模拟更新的定时器

// 添加处理状态文本提示
const processingStatusText = ref('');
const canCancelProcessing = ref(true); // 是否可以取消处理
// 新增取消处理API调用ID
const processingRequestId = ref(null);

// 获取所有未合并的音频文件
const fetchAudioFiles = async () => {
  loading.value = true;
  // error.value = ''; // 不在这里清除 error，以免上传成功/重复的提示消息闪没

  try {
    const response = await axios.get('http://localhost:8000/api/audio');
    audioFiles.value = response.data;
    console.log('文件列表获取成功:', audioFiles.value);
  } catch (err) {
    console.error('获取音频文件失败:', err);
    // 如果获取列表失败，设置错误消息
    error.value = '无法加载音频文件列表';
  } finally {
    loading.value = false;
  }
};

// 初始加载时获取文件列表
onMounted(() => {
  fetchAudioFiles();
});

// 处理上传结果并刷新列表的方法，由父组件 App.vue 调用
const processUploadedItems = (uploadedItems) => {
  console.log('AudioList received upload results:', uploadedItems);

  // 刷新列表，显示最新文件（会触发 fetchAudioFiles）
  fetchAudioFiles();

  // --- 构建上传结果提示消息 ---
  let successCount = 0;
  let duplicateMessages = [];
  let failedCount = 0; // 非HTTP错误，后端处理问题

  if (uploadedItems && Array.isArray(uploadedItems)) {
      uploadedItems.forEach(item => {
          if (item && item.isDuplicate === true) { // 检查是否存在且为 true
              const uploadedName = item.uploadedName || item.displayName || '未知文件';
              const existingId = item.id || '未知ID';
              duplicateMessages.push(`"${uploadedName}" (已存在，ID: ${existingId})`);
          } else if (item && item.id) { // 否则，如果item有效并且有id，认为是新上传成功
              successCount++;
          } else {
              failedCount++;
              console.warn('上传结果中发现格式异常的项:', item);
          }
      });
  } else {
      console.error('后端返回的上传结果格式异常:', uploadedItems);
      error.value = '上传处理完成，但解析结果失败。';
      return;
  }

  // 构建并设置提示消息
  let resultMessageParts = [];
  if (successCount > 0) {
    resultMessageParts.push(`${successCount} 个文件上传成功`);
  }
  if (duplicateMessages.length > 0) {
    resultMessageParts.push(`${duplicateMessages.length} 个文件重复：${duplicateMessages.join('；')}`); // 使用分号连接不同的重复项
  }
  if (failedCount > 0) {
      resultMessageParts.push(`${failedCount} 个文件处理失败`);
  }

  // 如果有任何结果信息，设置 error 变量来显示
  if (resultMessageParts.length > 0) {
      error.value = resultMessageParts.join('；') + '。'; // 使用分号连接不同的提示部分

      // 可以在几秒后清除消息
      setTimeout(() => {
          if (error.value === resultMessageParts.join('；') + '。') {
              error.value = '';
          }
      }, 8000); // 消息显示 8 秒
  } else if (uploadedItems.length === 0) {
        error.value = '上传操作完成，但没有文件被处理。';
         setTimeout(() => {
            if (error.value === '上传操作完成，但没有文件被处理。') {
                error.value = '';
            }
        }, 5000);
  }
};


// 删除音频文件
const deleteFile = async (id) => {
  if (!confirm('确定要删除这个音频文件吗？')) return;

  try {
    await axios.delete(`http://localhost:8000/api/audio/${id}`);
    fetchAudioFiles(); // 删除成功后刷新列表
    error.value = ''; // 清除可能的旧错误
  } catch (err) {
    console.error('删除文件失败:', err);
    error.value = err.response?.data?.detail || '删除文件时出错';
  }
};

// 删除所有音频文件
const deleteAllFiles = async () => {
  if (!confirm('确定要删除所有待处理音频文件吗？此操作不可恢复！')) return;

  try {
    await axios.delete('http://localhost:8000/api/audio/all');
    audioFiles.value = []; // 快速清空本地列表
    fetchAudioFiles(); // 确保状态一致
    error.value = ''; // 清除可能的旧错误
  } catch (err) {
    console.error('删除所有文件失败:', err);
    error.value = err.response?.data?.detail || '删除所有文件时出错';
  }
};

// 打开合并对话框
const openMergeDialog = () => {
  if (audioFiles.value.length < 2) {
    error.value = '列表中至少需要两个音频文件才能进行处理';
  } else {
     error.value = '';
     const now = new Date();
     const dateStr = now.toISOString().slice(0, 10); //YYYY-MM-DD
     const timeStr = now.toTimeString().slice(0, 5).replace(':', ''); //HHMM
     mergeOutputName.value = `合并音频_${dateStr}_${timeStr}`;
     mergeDialogOpen.value = true;
  }
};

// 关闭合并对话框
const closeMergeDialog = () => {
  // 如果正在处理，先确认取消
  if (processingMerge.value && canCancelProcessing.value) {
    if (confirm('处理尚未完成，确定要取消吗？')) {
      cancelProcessing();
    } else {
      return; // 用户不想取消，保持对话框打开
    }
  }
  
  mergeDialogOpen.value = false;
  mergeOutputName.value = '';
  error.value = ''; // 关闭对话框时清除消息
  processingStatusText.value = '';
  if (mergeProgressInterval.value) {
    clearInterval(mergeProgressInterval.value);
    mergeProgressInterval.value = null;
  }
};

// 合并/处理列表中的所有音频文件
const mergeSelectedFiles = async () => {
  if (audioFiles.value.length === 0) {
    error.value = '列表中没有文件可处理';
    return;
  }
  if (!mergeOutputName.value.trim()) {
    error.value = '请输入处理后的文件名';
    return;
  }

  processingMerge.value = true;
  error.value = ''; // 清除之前的错误或消息
  mergeProgress.value = 0; // 重置进度条
  processingStatusText.value = '正在准备处理任务...'; // 设置初始状态文本
  canCancelProcessing.value = true; // 重置可取消状态

  // 启动进度模拟
  startProgressSimulation();

  // 标记任务是否被取消
  let isCancelled = false;

  try {
    // 生成请求ID
    processingRequestId.value = Date.now().toString();
    
    processingStatusText.value = '正在提交处理任务...';
    const response = await axios.post('http://localhost:8000/api/merge', {
      audioIds: audioFiles.value.map(file => file.id), // 始终处理所有文件
      outputName: mergeOutputName.value.trim(),
      requestId: processingRequestId.value // 传递请求ID，用于后端识别取消请求
    });

    // 检查任务是否被取消 - 如果response.data中有status字段且为cancelled
    if (response.data && response.data.status === 'cancelled') {
      isCancelled = true;
      processingStatusText.value = '处理已取消';
      stopProgressSimulation();
      mergeProgress.value = 0;
      
      setTimeout(() => {
        if (mergeDialogOpen.value) {
          mergeDialogOpen.value = false;
        }
        processingRequestId.value = null;
      }, 1500);
      
      return;
    }

    // 只有在任务未被取消的情况下继续执行
    if (!isCancelled) {
      processingStatusText.value = '处理任务已完成';
      // 合并成功后，将进度直接设为100%
      mergeProgress.value = 100;
      stopProgressSimulation();
      canCancelProcessing.value = false; // 处理完成后不可取消

      emit('process-success', response.data); // 通知已处理文件列表的父组件

      // 稍等片刻再关闭对话框，让用户看到100%进度
      setTimeout(() => {
        mergeDialogOpen.value = false;
        processingRequestId.value = null; // 清空请求ID
        
        fetchAudioFiles(); // 刷新待处理列表

        // 显示处理成功提示
        if (response.data && response.data.displayName) {
          error.value = `文件 "${response.data.displayName}" 处理成功！`;
          setTimeout(() => { error.value = ''; }, 5000);
        }
      }, 800);
    }
  } catch (err) {
    console.error('处理文件失败:', err);
    stopProgressSimulation();
    mergeProgress.value = 0;
    error.value = err.response?.data?.detail || '处理音频文件时出错';
    processingStatusText.value = '处理失败';
    processingRequestId.value = null; // 清空请求ID
  } finally {
    processingMerge.value = false;
  }
};

// 取消处理任务
const cancelProcessing = async () => {
  if (!processingRequestId.value || !canCancelProcessing.value) return;
  
  try {
    processingStatusText.value = '正在取消处理...';
    await axios.post('http://localhost:8000/api/cancel-processing', {
      requestId: processingRequestId.value
    });
    
    stopProgressSimulation();
    mergeProgress.value = 0;
    processingStatusText.value = '处理已取消';
    
    // 设置标记表示任务已取消
    const taskCancelled = true;
    
    setTimeout(() => {
      if (!mergeDialogOpen.value) return; // 如果对话框已关闭，不执行
      processingMerge.value = false;
      processingRequestId.value = null;
      
      // 如果对话框还打开着，1.5秒后自动关闭
      setTimeout(() => {
        if (mergeDialogOpen.value) {
          mergeDialogOpen.value = false;
        }
      }, 1500);
    }, 500);
    
    return taskCancelled; // 返回取消状态
  } catch (err) {
    console.error('取消处理失败:', err);
    error.value = '取消处理任务失败';
    return false;
  }
};

// 开始进度条模拟更新
const startProgressSimulation = () => {
  // 清除可能存在的旧定时器
  if (mergeProgressInterval.value) {
    clearInterval(mergeProgressInterval.value);
  }
  
  // 设置一个模拟的进度更新
  // 进度会先快后慢，模拟实际处理过程
  mergeProgressInterval.value = setInterval(() => {
    if (mergeProgress.value < 90) {
      // 非线性增长：当进度越高，增长越慢
      const increment = (90 - mergeProgress.value) / 20;
      mergeProgress.value += Math.max(0.5, increment);
      
      // 根据进度更新状态文本
      if (mergeProgress.value > 10 && mergeProgress.value <= 30) {
        processingStatusText.value = '正在分析音频文件...';
      } else if (mergeProgress.value > 30 && mergeProgress.value <= 60) {
        processingStatusText.value = '正在处理音频数据...';
      } else if (mergeProgress.value > 60 && mergeProgress.value < 90) {
        processingStatusText.value = '正在合成最终音频...';
      }
    }
  }, 300);
};

// 停止进度条模拟更新
const stopProgressSimulation = () => {
  if (mergeProgressInterval.value) {
    clearInterval(mergeProgressInterval.value);
    mergeProgressInterval.value = null;
  }
};

// 组件卸载时清除定时器
onUnmounted(() => {
  stopProgressSimulation();
  // 音频播放器的清理由CustomAudioPlayer组件自行处理
});

// 开始编辑文件名
const startEdit = (file) => {
  editingFile.value = file.id;
  newDisplayName.value = file.displayName;
  error.value = ''; // 清除可能的旧错误
  
  // 聚焦将在指令中处理
};

// 保存编辑后的文件名
const saveEdit = async (file) => {
  if (!newDisplayName.value.trim()) {
    error.value = '显示名称不能为空';
    return;
  }

  try {
    const response = await axios.put(`http://localhost:8000/api/audio/${file.id}`, {
      displayName: newDisplayName.value.trim()
    });

    const index = audioFiles.value.findIndex(f => f.id === file.id);
    if (index !== -1) {
      audioFiles.value[index].displayName = response.data.displayName;
    }

    editingFile.value = null;
    newDisplayName.value = '';
    error.value = ''; // 清除错误
    // 可以在这里显示重命名成功提示
    // error.value = `文件 "${response.data.displayName}" 重命名成功！`;
    // setTimeout(() => { error.value = ''; }, 3000);
  } catch (err) {
    console.error('更新文件名失败:', err);
    error.value = err.response?.data?.detail || '更新文件名时出错';
  }
};

// 取消编辑
const cancelEdit = () => {
  editingFile.value = null;
  newDisplayName.value = '';
  error.value = ''; // 清除可能的错误
};

// 下载音频文件
const downloadFile = (id, displayName) => {
  window.open(`http://localhost:8000/api/download/${id}`, '_blank');
};

// 格式化时长（移至组件内定义）
const formatDuration = (seconds) => {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '未知';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 100); // 获取毫秒部分并转换为两位数
  return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
};

// 拖拽排序相关
const draggedItem = ref(null);

const onDragStart = (file) => {
  draggedItem.value = file;
};

const onDragOver = (event) => {
  event.preventDefault();
};

const onDrop = async (targetFile) => {
  if (!draggedItem.value || draggedItem.value.id === targetFile.id) {
    draggedItem.value = null;
    return;
  }

  const sourceIndex = audioFiles.value.findIndex(file => file.id === draggedItem.value.id);
  const targetIndex = audioFiles.value.findIndex(file => file.id === targetFile.id);

  if (sourceIndex === -1 || targetIndex === -1) {
      console.error("拖拽源或目标文件未找到");
      draggedItem.value = null;
      return;
  }

  const newOrderList = [...audioFiles.value];
  const [movedItem] = newOrderList.splice(sourceIndex, 1);
  newOrderList.splice(targetIndex, 0, movedItem);

  newOrderList.forEach((file, index) => {
      file.order = index + 1;
  });

  audioFiles.value = newOrderList;

  try {
    await axios.post('http://localhost:8000/api/reorder', {
      newOrder: audioFiles.value.map(file => file.id)
    });
    error.value = ''; // 清除可能的旧错误
  } catch (err) {
    console.error('更新排序失败:', err);
    error.value = err.response?.data?.detail || '更新音频排序时出错';
    fetchAudioFiles(); // 如果失败，回退到后端的状态
  } finally {
    draggedItem.value = null;
  }
};

// 暴露方法给父组件 App.vue 使用
defineExpose({
  fetchAudioFiles, // 暴露获取列表方法
  processUploadedItems // 暴露处理上传结果的方法
});

// 添加自动聚焦输入框的自定义指令
const vFocus = {
  mounted: (el) => el.focus()
};
</script>

<template>
  <div class="audio-list-container">
    <h2>待处理音频文件列表</h2>

    <p v-if="error" class="error-message">{{ error }}</p>

    <div v-if="loading" class="loading-indicator">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="audioFiles.length === 0" class="empty-state">
      <i class="empty-icon"></i>
      <p>没有待处理的音频文件。请上传一些音频文件开始使用。</p>
    </div>

    <div v-else>
      <div class="actions-bar">
        <div class="left-actions">
          <button
            @click="openMergeDialog"
            :disabled="audioFiles.length < 2 || processingMerge"
            class="merge-button"
          >
            <i class="merge-icon"></i>
            处理全部 {{ audioFiles.length }} 个文件
          </button>
          <button
            @click="deleteAllFiles"
            class="delete-all-btn"
            :disabled="processingMerge"
          >
            <i class="delete-icon"></i>
            删除所有待处理文件
          </button>
        </div>
      </div>

      <div class="audio-list">
        <transition-group name="audio-item-transition">
          <div
            v-for="file in audioFiles"
            :key="file.id"
            class="audio-item"
            :class="{ 'selected': false }"
            draggable="true"
            @dragstart="onDragStart(file)"
            @dragover="onDragOver"
            @drop="onDrop(file)"
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
                  </span>
                  <span class="order">
                    <i class="order-icon"></i>顺序: {{ file.order }}
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

    <div v-if="mergeDialogOpen" class="merge-dialog-overlay">
      <div class="merge-dialog">
        <h3>处理音频文件</h3>

        <div class="merge-form">
          <label for="merge-name">处理后的文件名:</label>
          <input
            type="text"
            id="merge-name"
            v-model="mergeOutputName"
            :disabled="processingMerge"
          />
        </div>

        <div class="selected-files-info">
          <p>即将处理列表中的全部文件 ({{ audioFiles.length }}个):</p>
          <ul>
            <li v-for="file in audioFiles" :key="file.id">
              {{ file.displayName }}
            </li>
          </ul>
        </div>

        <!-- 添加处理进度条 -->
        <div v-if="processingMerge || mergeProgress > 0" class="merge-progress-container">
          <div class="merge-progress-bar-bg">
            <div class="merge-progress-bar" :style="{ width: mergeProgress + '%' }">
              <div class="merge-progress-pulse" v-if="processingMerge"></div>
            </div>
          </div>
          <div class="merge-progress-text">{{ Math.floor(mergeProgress) }}%</div>
          <!-- 添加处理状态文本 -->
          <div class="processing-status-text" v-if="processingStatusText">{{ processingStatusText }}</div>
        </div>

        <div class="dialog-actions">
          <button
            @click="mergeSelectedFiles"
            :disabled="processingMerge || !mergeOutputName.trim()"
            class="confirm-btn"
            v-if="!processingMerge"
          >
            处理
          </button>
          <!-- 添加取消处理按钮 -->
          <button
            v-else
            @click="cancelProcessing"
            :disabled="!canCancelProcessing"
            class="cancel-processing-btn"
          >
            取消处理
          </button>
          <button
            @click="closeMergeDialog"
            :disabled="processingMerge && !canCancelProcessing"
            class="cancel-btn"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.audio-list-container {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h2 {
  margin-top: 0;
  color: #333;
  font-size: 1.5rem;
}

.error-message {
  color: #f44336;
  margin: 10px 0;
  padding: 10px;
  border: 1px solid #f44336;
  background-color: #ffebee;
  border-radius: 4px;
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
  flex-wrap: wrap;
  gap: 10px;
}

.left-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.merge-button {
  background-color: #2196f3;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s;
}

.merge-button:hover:not(:disabled) {
  background-color: #0b7dda;
}

.merge-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.delete-all-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s;
}

.delete-all-btn:hover {
  background-color: #d32f2f;
}

.audio-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.audio-item {
  display: flex;
  flex-direction: column;
  background-color: #f9f9f9;
  border-radius: 10px;
  padding: 15px;
  transition: all 0.3s ease;
  border: 1px solid #e0e0e0;
  cursor: grab;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
  position: relative;
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
}

.edit-btn:hover, .save-btn:hover {
  text-decoration: underline;
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
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.edit-actions {
  display: flex;
  gap: 10px;
}

.audio-meta {
  font-size: 0.85rem;
  color: #666;
  display: flex;
  gap: 10px;
}

.audio-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

.download-btn, .delete-btn {
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

/* 合并对话框样式 */
.merge-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  overflow: hidden; /* 防止滚动 */
}

.merge-dialog {
  position: fixed; /* 使用fixed定位 */
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%); /* 确保居中 */
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  animation: fade-in 0.3s ease;
  z-index: 1001; /* 确保在最上层 */
  max-height: 80vh; /* 限制最大高度 */
  overflow-y: auto; /* 内容过多时可滚动 */
}

.merge-dialog h3 {
  margin-top: 0;
  color: #333;
}

.merge-form {
  margin: 15px 0;
}

.merge-form label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.merge-form input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.selected-files-info {
  margin: 15px 0;
  max-height: 150px;
  overflow-y: auto;
}

.selected-files-info ul {
  padding-left: 20px;
  margin: 5px 0;
}

.selected-files-info li {
    border: none;
    padding: 2px 0;
    background-color: transparent;
}

.dialog-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.confirm-btn, .cancel-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
}

.confirm-btn {
  background-color: #2196f3;
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background-color: #0b7dda;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.confirm-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.cancel-btn {
  background-color: #f5f5f5;
  color: #555;
  border: 1px solid #ddd;
}

.cancel-btn:hover:not(:disabled) {
  background-color: #e0e0e0;
}

.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 添加处理进度条样式 */
.merge-progress-container {
  margin: 20px 0;
  width: 100%;
}

.merge-progress-bar-bg {
  height: 12px;
  background-color: #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.merge-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #2196f3, #4caf50);
  border-radius: 6px;
  transition: width 0.3s ease;
  position: relative;
}

.merge-progress-pulse {
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

.merge-progress-text {
  text-align: center;
  margin-top: 5px;
  font-weight: bold;
  color: #555;
}

@media (max-width: 768px) {
  .actions-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  .left-actions {
    flex-direction: column;
    gap: 8px;
    width: 100%;
  }
  .left-actions button {
    width: 100%;
    text-align: center;
  }

  .audio-item-header {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 10px;
  }

  .select-container {
    margin-bottom: 10px;
  }

  .audio-actions {
    margin-top: 10px;
    justify-content: flex-start;
  }

  .edit-name-form {
    width: 100%;
  }

  .audio-name-container {
      flex-direction: column;
      align-items: flex-start;
      gap: 5px;
  }
  .audio-name {
      margin-right: 0;
  }
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

/* 按钮和图标样式 */
.merge-icon::before {
  content: "🔄";
  margin-right: 8px;
}

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

.order-icon::before {
  content: "📋";
  margin-right: 5px;
}

.download-icon::before {
  content: "💾";
  margin-right: 5px;
}

/* 改进按钮样式 */
.merge-button, .delete-all-btn {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
  border: none;
}

.merge-button {
  background-color: #2196f3;
  color: white;
}

.merge-button:hover:not(:disabled) {
  background-color: #0b7dda;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.delete-all-btn {
  background-color: #f44336;
  color: white;
}

.delete-all-btn:hover:not(:disabled) {
  background-color: #d32f2f;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
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

.processing-status-text {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #555;
  text-align: center;
  animation: fade-in 0.3s ease;
}

.cancel-processing-btn {
  background-color: #ff9800;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 10px 20px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
}

.cancel-processing-btn:hover:not(:disabled) {
  background-color: #f57c00;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.cancel-processing-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>
