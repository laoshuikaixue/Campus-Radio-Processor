// 合并任务全局状态管理
import { reactive } from 'vue';

export const mergeTaskStore = reactive({
  requestId: null, // 当前合并任务ID
  status: null,    // processing/completed/failed/cancelled
  progress: 0,     // 进度百分比
  stage: '',       // 当前阶段（如merging/normalizing/exporting等）
  message: '',     // 阶段描述信息
  show: false,     // 是否显示进度浮窗
  reset() {
    this.requestId = null;
    this.status = null;
    this.progress = 0;
    this.stage = '';
    this.message = '';
    this.show = false;
  },
}); 