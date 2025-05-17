// 任务状态全局管理
import { reactive } from 'vue';

// 任务状态类型定义
export const TaskStatus = {
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
};

// 任务队列和当前任务状态
export const taskStatusStore = reactive({
  tasks: [], // { requestId, status, progress, stage, fileInfo, message }
  currentTask: null, // 当前弹窗显示的任务
  wsConnected: false,
  addTask(task) {
    // 如果已存在则更新，否则添加
    const idx = this.tasks.findIndex(t => t.requestId === task.requestId);
    if (idx !== -1) {
      this.tasks[idx] = { ...this.tasks[idx], ...task };
    } else {
      this.tasks.push(task);
    }
    // 如果没有当前任务，自动设为当前
    if (!this.currentTask || this.currentTask.requestId === task.requestId) {
      this.currentTask = this.tasks.find(t => t.requestId === task.requestId);
    }
  },
  updateTask(requestId, update) {
    const idx = this.tasks.findIndex(t => t.requestId === requestId);
    if (idx !== -1) {
      this.tasks[idx] = { ...this.tasks[idx], ...update };
      if (this.currentTask && this.currentTask.requestId === requestId) {
        this.currentTask = this.tasks[idx];
      }
    }
  },
  setCurrentTask(requestId) {
    this.currentTask = this.tasks.find(t => t.requestId === requestId) || null;
  },
  removeTask(requestId) {
    this.tasks = this.tasks.filter(t => t.requestId !== requestId);
    if (this.currentTask && this.currentTask.requestId === requestId) {
      this.currentTask = null;
    }
  },
  clear() {
    this.tasks = [];
    this.currentTask = null;
  }
}); 