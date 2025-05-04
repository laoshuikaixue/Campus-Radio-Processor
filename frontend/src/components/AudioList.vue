<script setup>
import { ref, onMounted, computed, onUnmounted, onBeforeUnmount, watch } from 'vue';
import api from '../api';
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
// 音量标准化选项
const normalizeVolume = ref(false); // 是否启用音量标准化
const normalizeTargetDb = ref(-3.0); // 标准化目标dB
// 新增取消处理API调用ID
const processingRequestId = ref(null);

// 创建变量跟踪后台处理状态
const backgroundProcessing = ref(false);
const backgroundProcessProgress = ref(0);
const backgroundProcessStatusText = ref('');
const backgroundProcessOutputName = ref('');
const backgroundProcessingId = ref(null); // 专门用于后台处理的请求ID

// 获取所有未合并的音频文件
const fetchAudioFiles = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    const response = await api.getAudioFiles();
    audioFiles.value = response.data;
  } catch (err) {
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
  // 检查是否有上传结果
  if (!uploadedItems || uploadedItems.length === 0) {
    return;
  }
  
  // 根据情况执行操作：
  // 1. 如果有重复文件被检测到，显示相应的消息
  // 2. 无论是否有新文件，都强制刷新列表
  
  let hasDuplicates = uploadedItems.some(item => item.isDuplicate);
  
  if (hasDuplicates) {
    const duplicateNames = uploadedItems
      .filter(item => item.isDuplicate)
      .map(item => item.uploadedName || item.originalName)
      .join(', ');
    
    error.value = `以下文件已存在，已忽略: ${duplicateNames}`;
  }
  
  // 刷新文件列表
  fetchAudioFiles();
};

// 删除音频文件
const deleteFile = async (id) => {
  if (!confirm('确定要删除这个音频文件吗？')) return;

  try {
    await api.deleteAudio(id);
    audioFiles.value = audioFiles.value.filter(file => file.id !== id);
  } catch (err) {
    error.value = '删除文件时出错';
  }
};

// 删除所有音频文件
const deleteAllFiles = async () => {
  if (!confirm('确定要删除所有音频文件吗？此操作不可恢复！')) return;

  try {
    await api.deleteAllAudio();
    audioFiles.value = [];
  } catch (err) {
    error.value = '删除所有文件时出错';
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
  // 如果正在处理，切换到后台处理模式
  if (processingMerge.value && canCancelProcessing.value) {
    // 设置后台处理状态
    backgroundProcessing.value = true;
    backgroundProcessProgress.value = mergeProgress.value;
    backgroundProcessStatusText.value = processingStatusText.value;
    backgroundProcessOutputName.value = mergeOutputName.value;
    // 保存请求ID到后台处理专用变量
    backgroundProcessingId.value = processingRequestId.value;
    console.log('后台处理已启动，requestId:', backgroundProcessingId.value);

    // 关闭弹窗，但保持处理继续进行
    mergeDialogOpen.value = false;
    return;
  }
  
  // 非处理状态下，正常关闭对话框
  mergeDialogOpen.value = false;
  mergeOutputName.value = '';
  error.value = ''; // 关闭对话框时清除消息
  processingStatusText.value = '';
  if (mergeProgressInterval.value) {
    clearInterval(mergeProgressInterval.value);
    mergeProgressInterval.value = null;
  }
  
  // 移除DOM中的弹窗
  removeDialogFromBody();
};

// 后台处理完成时的回调
const onBackgroundProcessComplete = (result) => {
  backgroundProcessing.value = false;
  backgroundProcessProgress.value = 0;
  backgroundProcessStatusText.value = '';
  backgroundProcessOutputName.value = '';
  backgroundProcessingId.value = null; // 清除后台处理ID

  // 显示处理完成提示
  if (result && result.displayName) {
    error.value = `文件 "${result.displayName}" 处理成功！`;
    setTimeout(() => { error.value = ''; }, 5000);
  }
  
  // 刷新列表
  fetchAudioFiles();
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
  
  // 立即更新弹窗内容，切换按钮状态
  updateDialogContent();

  // 启动进度模拟
  startProgressSimulation();

  // 标记任务是否被取消
  let isCancelled = false;

  try {
    // 生成请求ID
    processingRequestId.value = Date.now().toString();
    
    processingStatusText.value = '正在提交处理任务...';
    updateDialogContent(); // 更新状态文本
    
    const response = await api.mergeAudioFiles({
      audioIds: audioFiles.value.map(file => file.id),
      outputName: mergeOutputName.value.trim(),
      requestId: processingRequestId.value,
      normalizeVolume: normalizeVolume.value,
      normalizeTargetDb: normalizeTargetDb.value
    });

    // 检查任务是否被取消 - 如果response.data中有status字段且为cancelled
    if (response.data && response.data.status === 'cancelled') {
      isCancelled = true;
      processingStatusText.value = '处理已取消';
      updateDialogContent(); // 更新状态文本
      
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
      
      // 更新弹窗内容
      updateDialogContent();

      emit('process-success', response.data); // 通知已处理文件列表的父组件

      // 如果在弹窗中显示，等待关闭弹窗
      if (mergeDialogOpen.value) {
        // 不再自动关闭弹窗，而是等待用户点击"在后台继续处理"
        fetchAudioFiles(); // 刷新待处理列表

        // 显示处理成功提示
        if (response.data && response.data.displayName) {
          processingStatusText.value = `文件 "${response.data.displayName}" 处理成功！`;
          // 更新弹窗状态文本
          updateDialogContent();
        }
      } else if (backgroundProcessing.value) {
        // 如果是后台处理，调用完成回调
        onBackgroundProcessComplete(response.data);
      }
    }
  } catch (err) {
    console.error('处理文件失败:', err);
    stopProgressSimulation();
    mergeProgress.value = 0;
    error.value = err.response?.data?.detail || '处理音频文件时出错';
    processingStatusText.value = '处理失败';
    processingRequestId.value = null; // 清空请求ID
    
    // 更新弹窗状态
    updateDialogContent();

    // 如果是后台处理，更新后台处理状态
    if (!mergeDialogOpen.value && backgroundProcessing.value) {
      backgroundProcessing.value = false;
      backgroundProcessProgress.value = 0;
      backgroundProcessStatusText.value = '处理失败';
      setTimeout(() => { backgroundProcessStatusText.value = ''; }, 3000);
    }
  } finally {
    processingMerge.value = false;
    // 不在这里关闭弹窗，而是更新弹窗状态
    updateDialogContent();
  }
};

// 取消处理任务
const cancelProcessing = async () => {
  if (!processingRequestId.value || !canCancelProcessing.value) return;
  
  try {
    processingStatusText.value = '正在取消处理...';
    updateDialogContent(); // 立即更新弹窗显示取消中状态
    
    await api.cancelProcessing({
      requestId: processingRequestId.value
    });
    
    stopProgressSimulation();
    mergeProgress.value = 0;
    processingStatusText.value = '处理已取消';
    // 显示取消成功的视觉提示
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
      progressContainer.classList.add('canceled');
    }
    
    // 更新弹窗内容显示取消状态
    updateDialogContent();
    
    // 设置标记表示任务已取消
    const taskCancelled = true;
    
    // 更新按钮状态，但不自动关闭弹窗
    processingMerge.value = false; 
    canCancelProcessing.value = false;
    
    // 给用户一段时间查看取消结果，不自动关闭
    setTimeout(() => {
      if (!mergeDialogOpen.value) return; // 如果对话框已关闭，不执行
      
      // 显示一个明显的成功取消提示
      const statusText = document.getElementById('status-text');
      if (statusText) {
        statusText.textContent = '任务已成功取消！';
        statusText.classList.add('cancel-success');
      }
      
      // 更新弹窗内容
      updateDialogContent();
      
      // 清理请求ID
      processingRequestId.value = null;
    }, 500);
    
    return taskCancelled; // 返回取消状态
  } catch (err) {
    console.error('取消处理失败:', err);
    error.value = '取消处理任务失败';
    processingStatusText.value = '取消处理失败，请重试';
    updateDialogContent();
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
      
      // 同步更新后台进度
      if (backgroundProcessing.value) {
        backgroundProcessProgress.value = mergeProgress.value;
      }
      
      // 根据进度更新状态文本
      if (mergeProgress.value > 10 && mergeProgress.value <= 30) {
        processingStatusText.value = '正在分析音频文件...';
        if (backgroundProcessing.value) {
          backgroundProcessStatusText.value = '正在分析音频文件...';
        }
      } else if (mergeProgress.value > 30 && mergeProgress.value <= 60) {
        processingStatusText.value = '正在处理音频数据...';
        if (backgroundProcessing.value) {
          backgroundProcessStatusText.value = '正在处理音频数据...';
        }
      } else if (mergeProgress.value > 60 && mergeProgress.value < 90) {
        processingStatusText.value = '正在合成最终音频...';
        if (backgroundProcessing.value) {
          backgroundProcessStatusText.value = '正在合成最终音频...';
        }
      }
      
      // 更新弹窗进度，但不重新创建弹窗
      if (mergeDialogOpen.value) {
        updateDialogContent();
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
    const response = await api.updateAudio(file.id, {
      displayName: newDisplayName.value.trim()
    });

    const index = audioFiles.value.findIndex(f => f.id === file.id);
    if (index !== -1) {
      audioFiles.value[index].displayName = response.data.displayName;
    }

    editingFile.value = null;
    newDisplayName.value = '';
    error.value = '';
  } catch (err) {
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
    await api.reorderAudio({
      newOrder: audioFiles.value.map(file => file.id)
    });
    error.value = '';
  } catch (err) {
    error.value = err.response?.data?.detail || '更新音频排序时出错';
    fetchAudioFiles();
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

// 添加取消后台处理方法
const cancelBackgroundProcessing = async () => {
  if (!backgroundProcessing.value || !canCancelProcessing.value) return;
  
  try {
    console.log('尝试取消后台处理，requestId:', backgroundProcessingId.value);
    
    // 如果没有requestId，显示错误并返回
    if (!backgroundProcessingId.value) {
      error.value = '无法取消处理：缺少处理任务ID';
      return;
    }
    
    await api.cancelProcessing({
      requestId: backgroundProcessingId.value
    });
    
    console.log('后台处理取消成功');
    
    // 取消成功后重置状态
    backgroundProcessing.value = false;
    backgroundProcessProgress.value = 0;
    backgroundProcessOutputName.value = '';
    backgroundProcessStatusText.value = '';
    backgroundProcessingId.value = null;
    canCancelProcessing.value = false;
    
    // 刷新文件列表，以防有些状态变化
    fetchAudioFiles();
    
    error.value = '后台处理已取消';
  } catch (err) {
    console.error('取消后台处理失败:', err);
    error.value = '取消后台处理失败，请稍后再试';
  }
};

// 组件卸载前移除可能添加到body的弹窗
onBeforeUnmount(() => {
  removeDialogFromBody();
});

// 监听弹窗状态变化，动态添加/移除弹窗到body
watch(mergeDialogOpen, (newVal) => {
  if (newVal) {
    addDialogToBody();
  } else {
    removeDialogFromBody();
  }
});

// 在body中动态创建弹窗元素
const addDialogToBody = () => {
  // 确保之前的弹窗已移除
  removeDialogFromBody();
  
  // 创建弹窗容器
  const overlay = document.createElement('div');
  overlay.id = 'merge-dialog-overlay';
  overlay.className = 'merge-dialog-overlay';
  
  // 创建弹窗内容
  const dialog = document.createElement('div');
  dialog.className = 'merge-dialog';
  dialog.id = 'merge-dialog';
  
  // 设置弹窗内容
  dialog.innerHTML = `
    <h3>处理音频文件</h3>
    
    <div class="merge-form">
      <div class="form-group">
        <label for="merge-name">处理后的文件名:</label>
        <input
          type="text"
          id="merge-name"
          value="${mergeOutputName.value}"
          ${processingMerge.value ? 'disabled' : ''}
        />
      </div>
      
      <div class="form-group normalize-options">
        <div class="checkbox-container">
          <input
            type="checkbox"
            id="normalize-volume"
            ${normalizeVolume.value ? 'checked' : ''}
            ${processingMerge.value ? 'disabled' : ''}
          />
          <label for="normalize-volume">音量标准化</label>
        </div>
        
        <div class="db-control" id="db-control" style="${normalizeVolume.value ? '' : 'opacity: 0.5; pointer-events: none;'}">
          <label for="normalize-target-db">目标音量 (dB):</label>
          <input
            type="number"
            id="normalize-target-db"
            value="${normalizeTargetDb.value}"
            step="0.5"
            min="-20"
            max="0"
            ${!normalizeVolume.value || processingMerge.value ? 'disabled' : ''}
          />
        </div>
      </div>
    </div>
    
    <div class="selected-files-info">
      <p>即将处理列表中的全部文件 (${audioFiles.value.length}个):</p>
      <ul>
        ${audioFiles.value.map(file => `<li>${file.displayName}</li>`).join('')}
      </ul>
    </div>
    
    <div class="estimation-info">
      <p>预估合成音频时长：${
        formatDuration(audioFiles.value.reduce((total, file) => total + (file.duration || 0), 0))
      }</p>
    </div>
    
    <div id="progress-container" class="merge-progress-container" ${(processingMerge.value || mergeProgress.value > 0) ? '' : 'style="display:none;"'}>
      <div class="merge-progress-bar-bg">
        <div id="progress-bar" class="merge-progress-bar" style="width: ${mergeProgress.value}%">
          <div class="merge-progress-pulse" ${processingMerge.value ? '' : 'style="display:none;"'}></div>
        </div>
      </div>
      <div id="progress-text" class="merge-progress-text">${Math.floor(mergeProgress.value)}%</div>
      <div id="status-text" class="processing-status-text" ${processingStatusText.value ? '' : 'style="display:none;"'}>${processingStatusText.value}</div>
    </div>
    
    <div class="dialog-actions">
      ${!processingMerge.value ? `
        <button id="confirm-merge-btn" ${(!mergeOutputName.value.trim() || processingMerge.value) ? 'disabled' : ''} class="confirm-btn">
          处理
        </button>
      ` : `
        <button id="cancel-process-btn" ${!canCancelProcessing.value ? 'disabled' : ''} class="cancel-processing-btn">
          取消处理
        </button>
      `}
      
      <button id="close-dialog-btn" ${(processingMerge.value && !canCancelProcessing.value) ? 'disabled' : ''} class="cancel-btn">
        ${processingMerge.value ? '在后台继续处理' : '关闭'}
      </button>
    </div>
  `;
  
  // 将弹窗添加到body
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);
  
  // 添加事件监听
  document.getElementById('merge-name')?.addEventListener('input', (e) => {
    mergeOutputName.value = e.target.value;
  });
  
  // 音量标准化复选框事件
  document.getElementById('normalize-volume')?.addEventListener('change', (e) => {
    normalizeVolume.value = e.target.checked;
    
    // 更新目标dB输入框状态
    const dbControl = document.getElementById('db-control');
    const dbInput = document.getElementById('normalize-target-db');
    
    if (dbControl) {
      dbControl.style.opacity = normalizeVolume.value ? '1' : '0.5';
      dbControl.style.pointerEvents = normalizeVolume.value ? 'auto' : 'none';
    }
    
    if (dbInput) {
      dbInput.disabled = !normalizeVolume.value || processingMerge.value;
    }
  });
  
  // 目标dB值输入事件
  document.getElementById('normalize-target-db')?.addEventListener('input', (e) => {
    // 将输入值限制在[-20, 0]范围内
    let value = parseFloat(e.target.value);
    if (isNaN(value)) value = -3.0;
    value = Math.max(-20, Math.min(0, value));
    
    normalizeTargetDb.value = value;
    e.target.value = value; // 确保显示值反映实际使用值
  });
  
  document.getElementById('confirm-merge-btn')?.addEventListener('click', () => {
    mergeSelectedFiles();
  });
  
  document.getElementById('cancel-process-btn')?.addEventListener('click', () => {
    cancelProcessing();
  });
  
  document.getElementById('close-dialog-btn')?.addEventListener('click', () => {
    // 如果正在处理并且可以取消，则切换到后台处理模式
    if (processingMerge.value && canCancelProcessing.value) {
      closeMergeDialog();
    } else {
      // 正常关闭前先添加退出动画
      const dialog = document.getElementById('merge-dialog');
      if (dialog) {
        dialog.classList.add('dialog-exit');
        // 等待动画完成后调用关闭方法
        setTimeout(() => {
          closeMergeDialog();
        }, 280);
      } else {
        closeMergeDialog();
      }
    }
  });
  
  // 如果正在处理，开始更新进度
  if (processingMerge.value) {
    startDialogProgressUpdates();
  }
};

// 更新弹窗中的进度条和状态，无需重新创建整个弹窗
const updateDialogContent = () => {
  if (!mergeDialogOpen.value) return;
  
  const progressContainer = document.getElementById('progress-container');
  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');
  const statusText = document.getElementById('status-text');
  const progressPulse = document.querySelector('#progress-bar .merge-progress-pulse');
  const closeButton = document.getElementById('close-dialog-btn');
  const confirmButton = document.getElementById('confirm-merge-btn');
  const cancelProcessButton = document.getElementById('cancel-process-btn');
  const actionsContainer = document.querySelector('.dialog-actions');
  
  if (!progressContainer || !progressBar || !progressText || !statusText || !actionsContainer) return;
  
  // 确保进度容器显示
  if (processingMerge.value || mergeProgress.value > 0) {
    progressContainer.style.display = '';
  } else {
    progressContainer.style.display = 'none';
  }
  
  // 更新进度条
  progressBar.style.width = `${mergeProgress.value}%`;
  
  // 更新进度文本
  progressText.textContent = `${Math.floor(mergeProgress.value)}%`;
  
  // 更新状态文本
  if (processingStatusText.value) {
    statusText.textContent = processingStatusText.value;
    statusText.style.display = '';
  } else {
    statusText.style.display = 'none';
  }
  
  // 更新脉动效果
  if (progressPulse) {
    progressPulse.style.display = processingMerge.value ? '' : 'none';
  }
  
  // 更新按钮文本
  if (closeButton) {
    closeButton.textContent = processingMerge.value ? '在后台继续处理' : '关闭';
    closeButton.disabled = (processingMerge.value && !canCancelProcessing.value);
  }
  
  // 更新处理/取消按钮
  if (processingMerge.value) {
    // 如果正在处理，显示取消按钮，隐藏确认按钮
    if (confirmButton) {
      confirmButton.style.display = 'none';
    }
    
    // 如果没有取消按钮，创建一个
    if (!cancelProcessButton) {
      const cancelBtn = document.createElement('button');
      cancelBtn.id = 'cancel-process-btn';
      cancelBtn.className = 'cancel-processing-btn';
      cancelBtn.textContent = '取消处理';
      cancelBtn.disabled = !canCancelProcessing.value;
      cancelBtn.addEventListener('click', () => {
        cancelProcessing();
      });
      
      // 在关闭按钮之前插入取消按钮
      if (closeButton && closeButton.parentNode) {
        closeButton.parentNode.insertBefore(cancelBtn, closeButton);
      }
    } else {
      cancelProcessButton.style.display = '';
      cancelProcessButton.disabled = !canCancelProcessing.value;
    }
  } else {
    // 如果不在处理，显示确认按钮，隐藏取消按钮
    if (cancelProcessButton) {
      cancelProcessButton.style.display = 'none';
    }
    
    if (confirmButton) {
      confirmButton.style.display = '';
      confirmButton.disabled = !mergeOutputName.value.trim() || processingMerge.value;
    }
  }
};

// 开始定期更新弹窗进度
const startDialogProgressUpdates = () => {
  updateDialogContent();
  
  // 定期更新，但不太频繁以避免性能问题
  setTimeout(() => {
    if (mergeDialogOpen.value && processingMerge.value) {
      updateDialogContent();
      startDialogProgressUpdates();
    }
  }, 200);
};

// 从body中移除弹窗
const removeDialogFromBody = () => {
  const overlay = document.getElementById('merge-dialog-overlay');
  if (overlay) {
    const dialog = document.getElementById('merge-dialog');
    if (dialog) {
      // 添加退出动画
      dialog.classList.add('dialog-exit');
      // 等待动画完成后删除元素
      setTimeout(() => {
        overlay.remove();
      }, 300); // 动画持续时间
    } else {
      overlay.remove();
    }
  }
};
</script>

<template>
  <div class="audio-list-container">
    <h2>待处理音频文件列表</h2>

    <p v-if="error" class="error-message">{{ error }}</p>

    <!-- 添加后台处理状态指示器 -->
    <div v-if="backgroundProcessing" class="background-processing-status">
      <div class="background-processing-info">
        <span>正在后台处理: {{ backgroundProcessOutputName }}</span>
        <div class="background-progress-bar-bg">
          <div class="background-progress-bar" :style="{ width: `${backgroundProcessProgress}%` }">
            <div class="background-progress-pulse" v-if="backgroundProcessProgress < 100"></div>
          </div>
        </div>
        <div class="background-progress-text">{{ Math.floor(backgroundProcessProgress) }}% - {{ backgroundProcessStatusText }}</div>
        <!-- 添加取消后台处理按钮 -->
        <button @click="cancelBackgroundProcessing" class="cancel-background-btn" :disabled="!canCancelProcessing">
          取消处理
        </button>
      </div>
    </div>

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
  </div>
</template>

<style>
/* 全局弹窗样式，确保直接附加到body时也能正确显示 */
.merge-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 9999;
  overflow: hidden;
  animation: fade-in 0.3s ease;
}

.merge-dialog {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(1);
  background-color: var(--dialog-bg, white);
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  animation: dialog-enter 0.4s ease;
  z-index: 10000;
  max-height: 80vh;
  overflow-y: auto;
}

@keyframes dialog-enter {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

@keyframes dialog-exit {
  from {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.8);
  }
}

.dialog-exit {
  animation: dialog-exit 0.3s ease forwards;
}

.merge-dialog h3 {
  margin-top: 0;
  color: var(--dialog-title-color, #2196f3);
  font-weight: bold;
  border-bottom: 1px solid var(--dialog-title-border, #e0e0e0);
  padding-bottom: 10px;
  margin-bottom: 15px;
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

.estimation-info {
  margin: 15px 0;
  padding: 10px;
  background-color: #f0f7ff;
  border-radius: 6px;
  border-left: 4px solid #2196f3;
}

.estimation-info p {
  margin: 0;
  color: #333;
  font-weight: 500;
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

.processing-status-text {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #555;
  text-align: center;
  animation: fade-in 0.3s ease;
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

.delete-icon::before {
  content: "🗑️";
  margin-right: 8px;
}

/* 按钮和图标样式 */
.merge-icon::before {
  content: "🔄";
  margin-right: 8px;
}

/* 合并对话框样式 */
.merge-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 9999;
  overflow: hidden;
  animation: fade-in 0.3s ease;
}

.merge-dialog {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) scale(1);
  background-color: var(--dialog-bg, white);
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  animation: dialog-enter 0.4s ease;
  z-index: 10000;
  max-height: 80vh;
  overflow-y: auto;
}

@keyframes dialog-enter {
  from {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
}

@keyframes dialog-exit {
  from {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.8);
  }
}

.dialog-exit {
  animation: dialog-exit 0.3s ease forwards;
}

.merge-dialog h3 {
  margin-top: 0;
  color: var(--dialog-title-color, #2196f3);
  font-weight: bold;
  border-bottom: 1px solid var(--dialog-title-border, #e0e0e0);
  padding-bottom: 10px;
  margin-bottom: 15px;
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

.processing-status-text {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #555;
  text-align: center;
  animation: fade-in 0.3s ease;
}

/* 添加取消成功的视觉提示样式 */
.cancel-success {
  color: #ff9800 !important;
  font-weight: bold !important;
  font-size: 1.1rem !important;
  margin-top: 15px !important;
  animation: pulse 1.5s infinite !important;
}

.canceled .merge-progress-bar {
  background: linear-gradient(90deg, #ff9800, #ff5722) !important;
}

@keyframes pulse {
  0% { opacity: 0.7; }
  50% { opacity: 1; }
  100% { opacity: 0.7; }
}
</style>

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

/* 后台处理状态样式 */
.background-processing-status {
  background-color: #f0f8ff;
  border: 1px solid #c3e0fd;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 4px rgba(33, 150, 243, 0.1);
}

.background-processing-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.background-processing-info span {
  font-weight: bold;
  color: #1976d2;
}

.background-progress-bar-bg {
  height: 12px;
  background-color: #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.background-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #2196f3, #4caf50);
  border-radius: 6px;
  transition: width 0.3s ease;
  position: relative;
}

.background-progress-pulse {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 15px;
  background: rgba(255, 255, 255, 0.3);
  animation: pulse-animation 1.5s infinite;
}

.background-progress-text {
  font-weight: bold;
  color: #555;
  margin-bottom: 10px;
}

.cancel-background-btn {
  background-color: #ff9800;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 15px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.3s ease;
  align-self: flex-start;
}

.cancel-background-btn:hover:not(:disabled) {
  background-color: #f57c00;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.cancel-background-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* 按钮和图标样式 */
.merge-icon::before {
  content: "🔄";
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

/* 添加取消成功的视觉提示样式 */
.cancel-success {
  color: #ff9800 !important;
  font-weight: bold !important;
  font-size: 1.1rem !important;
  margin-top: 15px !important;
  animation: pulse 1.5s infinite !important;
}

.canceled .merge-progress-bar {
  background: linear-gradient(90deg, #ff9800, #ff5722) !important;
}

@keyframes pulse {
  0% { opacity: 0.7; }
  50% { opacity: 1; }
  100% { opacity: 0.7; }
}
</style>
