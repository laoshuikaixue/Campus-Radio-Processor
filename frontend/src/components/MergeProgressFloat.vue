<template>
  <transition name="float-fade-scale">
    <div v-if="visible" class="merge-float" :class="themeClass" :style="floatStyle">
      <div class="float-header" @click="toggleMinimize">
        <span v-if="!minimized">音频合并进度</span>
        <span v-else>{{ minimizedStatusText }}</span>
        <span class="float-close" @click.stop="close">×</span>
      </div>
      <transition name="float-body-fade">
        <div v-show="!minimized" class="float-body">
          <div class="float-progress-bg">
            <div class="float-progress-bar" :style="progressBarStyle"></div>
          </div>
          <div class="float-progress-text">{{ Math.floor(progress) }}%</div>
          <div class="float-status-text">{{ detailedStatusText }}</div>
          <div class="float-actions">
            <button v-if="canCancel" @click="cancelTaskAnimated" class="cancel-btn" :class="{ ripple: rippleActive }">
              <span>取消</span>
            </button>
          </div>
        </div>
      </transition>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import api from '../api';
import { mergeTaskStore } from '../store/mergeTask';

const props = defineProps({
  modelValue: Boolean,
  progress: Number,
  status: String,
  message: String,
  canCancel: Boolean,
  onCancel: Function,
  onClose: Function,
});
const emit = defineEmits(['close', 'cancel']);

const minimized = ref(false);
const visible = ref(true);
const rippleActive = ref(false);

function toggleMinimize() {
  minimized.value = !minimized.value;
}
function close() {
  visible.value = false;
  emit('close');
  if (props.onClose) props.onClose();
}
function cancelTaskAnimated(e) {
  rippleActive.value = false;
  void e?.target?.offsetWidth; // 强制重绘
  rippleActive.value = true;
  setTimeout(() => {
    rippleActive.value = false;
    emit('cancel');
    if (props.onCancel) props.onCancel();
  }, 220);
}

// 详细状态文本（展开时显示）
const detailedStatusText = computed(() => {
  if (props.status === 'processing') {
    if (mergeTaskStore.totalFilesCount > 0 && mergeTaskStore.currentFileIndex > 0) {
       // 显示处理文件进度和阶段
       return `处理文件 (${mergeTaskStore.currentFileIndex}/${mergeTaskStore.totalFilesCount}): ${props.message || '正在处理...'}`;
    } else {
       // 只显示阶段或消息
       return props.message || props.stage || '正在处理...';
    }
  } else if (props.status === 'completed') {
    return props.message || '处理完成';
  } else if (props.status === 'failed') {
    return props.message || '处理失败';
  } else if (props.status === 'cancelled') {
    return props.message || '已取消';
  }
  return '';
});

// 最小化状态文本
const minimizedStatusText = computed(() => {
  if (props.status === 'processing') {
     if (mergeTaskStore.totalFilesCount > 0 && mergeTaskStore.currentFileIndex > 0) {
        return `合并中 (${mergeTaskStore.currentFileIndex}/${mergeTaskStore.totalFilesCount})...`;
     } else {
        return '合并中...';
     }
  } else if (props.status === 'completed') {
    return '完成';
  } else if (props.status === 'failed') {
    return '失败';
  } else if (props.status === 'cancelled') {
    return '取消';
  }
  return '进度';
});

const themeClass = computed(() => {
  return document.body.classList.contains('dark') ? 'dark' : 'light';
});

const floatStyle = computed(() => ({
  right: '32px',
  bottom: '32px',
  position: 'fixed',
  zIndex: 9999,
  minWidth: minimized.value ? '180px' : '360px', // 略微调整展开宽度
  maxWidth: '95vw',
  transition: 'min-width 0.35s cubic-bezier(.4,1.4,.6,1), max-width 0.35s cubic-bezier(.4,1.4,.6,1)', // 添加max-width过渡
}));

const progressBarStyle = computed(() => ({
  width: `${props.progress}%`,
  // 调整进度条过渡，使其更平滑
  transition: 'width 1s linear', // 使用线性过渡，持续时间长一些
  background: `linear-gradient(90deg, #2196f3, #4caf50 ${props.progress}%)`,
}));

// 自动关闭逻辑
watch(() => props.status, (val) => {
  if (val === 'completed' || val === 'failed' || val === 'cancelled') {
    setTimeout(() => close(), 2500);
  }
});
</script>

<style scoped>
.merge-float {
  background: var(--color-bg, #fff);
  color: var(--color-text, #222);
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  padding: 0;
  overflow: hidden;
  transition: box-shadow 0.25s, background 0.25s;
  will-change: box-shadow, background, transform;
}
.merge-float.dark {
  --color-bg: #23272e;
  --color-text: #f1f1f1;
}
.merge-float.light {
  --color-bg: #fff;
  --color-text: #222;
}
.float-header {
  background: linear-gradient(90deg, #2196f3, #4caf50);
  color: #fff;
  font-weight: bold;
  padding: 12px 20px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.08rem;
  user-select: none;
}
.float-close {
  font-size: 1.3rem;
  cursor: pointer;
  margin-left: 10px;
  transition: color 0.2s;
}
.float-close:hover {
  color: #ff9800;
}
.float-body {
  padding: 22px 26px 16px 26px;
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: float-body-fadein 0.5s;
}
@keyframes float-body-fadein {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: none; }
}
.float-progress-bg {
  width: 100%;
  height: 16px;
  background: #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 10px;
  transition: background 0.3s;
}
.float-progress-bar {
  height: 100%;
  border-radius: 8px;
  /* 进度条过渡改为线性 */
  transition: width 1s linear, background 0.5s;
  background: linear-gradient(90deg, #2196f3, #4caf50);
  will-change: width, background;
}
.float-progress-text {
  font-weight: bold;
  color: var(--color-text, #222);
  margin-bottom: 6px;
  font-size: 1.1rem;
  letter-spacing: 1px;
  transition: color 0.2s;
}
.float-status-text {
  color: #888;
  font-size: 1rem;
  margin-bottom: 8px;
  transition: color 0.2s;
  text-align: center; /* 居中文本 */
}
.float-song-text {
  /* 移除此样式块，不再单独显示歌曲名 */
}
.float-actions {
  display: flex;
  gap: 18px;
  margin-top: 10px;
}
.cancel-btn {
  background: #ff9800;
  color: #fff;
  border: none;
  border-radius: 7px;
  padding: 10px 28px;
  font-weight: bold;
  cursor: pointer;
  font-size: 1.05rem;
  box-shadow: 0 2px 8px rgba(255,152,0,0.08);
  position: relative;
  overflow: hidden;
  transition: background 0.18s, transform 0.18s;
}
.cancel-btn:hover {
  background: #f57c00;
  transform: scale(1.04);
}
.cancel-btn.ripple::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 180%;
  height: 180%;
  background: rgba(255,255,255,0.25);
  border-radius: 50%;
  transform: translate(-50%, -50%) scale(0.1);
  animation: ripple-zoom 0.22s linear;
  pointer-events: none;
}
@keyframes ripple-zoom {
  to {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0;
  }
}
.float-fade-scale-enter-active, .float-fade-scale-leave-active {
  transition: opacity 0.35s cubic-bezier(.4,1.4,.6,1), transform 0.35s cubic-bezier(.4,1.4,.6,1);
}
.float-fade-scale-enter-from, .float-fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.85);
}
.float-fade-scale-leave-active {
  pointer-events: none;
}
.float-body-fade-enter-active, .float-body-fade-leave-active {
  transition: opacity 0.25s cubic-bezier(.4,1.4,.6,1);
}
.float-body-fade-enter-from, .float-body-fade-leave-to {
  opacity: 0;
}
</style> 