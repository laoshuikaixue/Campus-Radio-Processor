<template>
  <div v-if="task" class="task-modal-overlay" :class="themeClass">
    <div class="task-modal">
      <h3>音频处理进度</h3>
      <div class="task-info">
        <div class="task-progress-bar-bg">
          <div class="task-progress-bar" :style="{ width: `${task.progress || 0}%` }"></div>
        </div>
        <div class="task-progress-text">{{ Math.floor(task.progress || 0) }}%</div>
        <div class="task-status-text">{{ statusText }}</div>
      </div>
      <div class="task-actions">
        <button v-if="canCancel" @click="cancelTask" class="cancel-btn">取消处理</button>
        <button @click="$emit('close')" class="close-btn">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { taskStatusStore, TaskStatus } from '../store/taskStatus';
import api from '../api';

const props = defineProps({
  modelValue: Boolean,
});
const emit = defineEmits(['close']);

const task = computed(() => taskStatusStore.currentTask);

const statusText = computed(() => {
  if (!task.value) return '';
  if (task.value.status === TaskStatus.PROCESSING) {
    return task.value.message || '正在处理...';
  } else if (task.value.status === TaskStatus.COMPLETED) {
    return task.value.message || '处理完成';
  } else if (task.value.status === TaskStatus.FAILED) {
    return task.value.message || '处理失败';
  } else if (task.value.status === TaskStatus.CANCELLED) {
    return task.value.message || '已取消';
  }
  return '';
});

const canCancel = computed(() => task.value && task.value.status === TaskStatus.PROCESSING);

const themeClass = computed(() => {
  // 通过body的class判断深浅色
  return document.body.classList.contains('dark') ? 'dark' : 'light';
});

async function cancelTask() {
  if (!task.value) return;
  await api.cancelProcessing({ requestId: task.value.requestId });
}
</script>

<style scoped>
.task-modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.task-modal {
  background: var(--color-bg, #fff);
  color: var(--color-text, #222);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
  padding: 32px 28px 24px 28px;
  min-width: 320px;
  max-width: 90vw;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.task-modal.dark {
  --color-bg: #23272e;
  --color-text: #f1f1f1;
}
.task-modal.light {
  --color-bg: #fff;
  --color-text: #222;
}
.task-info {
  width: 100%;
  margin: 18px 0 10px 0;
  text-align: center;
}
.task-progress-bar-bg {
  width: 100%;
  height: 14px;
  background: #e0e0e0;
  border-radius: 7px;
  overflow: hidden;
  margin-bottom: 8px;
}
.task-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #2196f3, #4caf50);
  border-radius: 7px;
  transition: width 0.3s;
}
.task-progress-text {
  font-weight: bold;
  color: var(--color-text, #222);
  margin-bottom: 6px;
}
.task-status-text {
  color: #888;
  font-size: 1rem;
  margin-bottom: 8px;
}
.task-actions {
  display: flex;
  gap: 18px;
  margin-top: 10px;
}
.cancel-btn {
  background: #ff9800;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 20px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}
.cancel-btn:hover {
  background: #f57c00;
}
.close-btn {
  background: #f5f5f5;
  color: #555;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 8px 20px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}
.close-btn:hover {
  background: #e0e0e0;
}
</style> 