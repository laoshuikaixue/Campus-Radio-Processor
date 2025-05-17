<template>
  <div class="task-bar" :class="themeClass" v-if="tasks.length > 0">
    <div class="task-bar-title">后台任务</div>
    <div class="task-bar-list">
      <div v-for="t in tasks" :key="t.requestId" class="task-bar-item" :class="{ active: t.requestId === currentId }" @click="setCurrent(t.requestId)">
        <div class="task-bar-info">
          <span class="task-bar-status" :class="t.status">{{ statusText(t) }}</span>
          <span class="task-bar-name">{{ t.fileInfo?.displayName || t.stage || '音频处理' }}</span>
        </div>
        <div class="task-bar-progress-bg">
          <div class="task-bar-progress" :style="{ width: `${t.progress || 0}%` }"></div>
        </div>
      </div>
    </div>
    <button class="task-bar-clear" @click="clear">清空任务</button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { taskStatusStore, TaskStatus } from '../store/taskStatus';

const tasks = computed(() => taskStatusStore.tasks);
const currentId = computed(() => taskStatusStore.currentTask?.requestId);

function setCurrent(id) {
  taskStatusStore.setCurrentTask(id);
}
function clear() {
  taskStatusStore.clear();
}
function statusText(t) {
  if (t.status === TaskStatus.PROCESSING) return '进行中';
  if (t.status === TaskStatus.COMPLETED) return '已完成';
  if (t.status === TaskStatus.FAILED) return '失败';
  if (t.status === TaskStatus.CANCELLED) return '已取消';
  return '';
}
const themeClass = computed(() => {
  return document.body.classList.contains('dark') ? 'dark' : 'light';
});
</script>

<style scoped>
.task-bar {
  position: fixed;
  right: 24px;
  bottom: 24px;
  min-width: 260px;
  max-width: 340px;
  background: var(--color-bg, #fff);
  color: var(--color-text, #222);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.13);
  padding: 16px 18px 12px 18px;
  z-index: 9998;
}
.task-bar.dark {
  --color-bg: #23272e;
  --color-text: #f1f1f1;
}
.task-bar.light {
  --color-bg: #fff;
  --color-text: #222;
}
.task-bar-title {
  font-weight: bold;
  font-size: 1.1rem;
  margin-bottom: 10px;
}
.task-bar-list {
  max-height: 220px;
  overflow-y: auto;
}
.task-bar-item {
  padding: 8px 0 6px 0;
  border-bottom: 1px solid #ececec;
  cursor: pointer;
  transition: background 0.2s;
}
.task-bar-item:last-child {
  border-bottom: none;
}
.task-bar-item.active {
  background: rgba(33,150,243,0.08);
}
.task-bar-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 2px;
}
.task-bar-status {
  font-size: 0.95em;
  font-weight: bold;
  padding: 2px 8px;
  border-radius: 8px;
  background: #e0e0e0;
  color: #1976d2;
}
.task-bar-status.processing { background: #e3f2fd; color: #1976d2; }
.task-bar-status.completed { background: #e8f5e9; color: #388e3c; }
.task-bar-status.failed { background: #ffebee; color: #d32f2f; }
.task-bar-status.cancelled { background: #fff3e0; color: #ff9800; }
.task-bar-name {
  flex: 1;
  font-size: 1em;
  color: var(--color-text, #222);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-bar-progress-bg {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 2px;
}
.task-bar-progress {
  height: 100%;
  background: linear-gradient(90deg, #2196f3, #4caf50);
  border-radius: 4px;
  transition: width 0.3s;
}
.task-bar-clear {
  margin-top: 10px;
  background: #f5f5f5;
  color: #555;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 6px 18px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
  width: 100%;
}
.task-bar-clear:hover {
  background: #e0e0e0;
}
</style> 