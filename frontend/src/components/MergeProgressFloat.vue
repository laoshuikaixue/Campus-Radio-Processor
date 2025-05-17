<template>
  <transition name="float-fade">
    <div v-if="visible" class="merge-float" :class="themeClass" :style="floatStyle">
      <div class="float-header" @click="toggleMinimize">
        <span v-if="!minimized">音频合并进度</span>
        <span v-else>合并中...</span>
        <span class="float-close" @click.stop="close">×</span>
      </div>
      <div v-show="!minimized" class="float-body">
        <div class="float-progress-bg">
          <div class="float-progress-bar" :style="{ width: `${progress}%` }"></div>
        </div>
        <div class="float-progress-text">{{ Math.floor(progress) }}%</div>
        <div class="float-status-text">{{ statusText }}</div>
        <div class="float-actions">
          <button v-if="canCancel" @click="cancelTask" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import api from '../api';

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

function toggleMinimize() {
  minimized.value = !minimized.value;
}
function close() {
  visible.value = false;
  emit('close');
  if (props.onClose) props.onClose();
}
function cancelTask() {
  emit('cancel');
  if (props.onCancel) props.onCancel();
}

const statusText = computed(() => {
  if (props.status === 'processing') return props.message || '正在合并...';
  if (props.status === 'completed') return props.message || '处理完成';
  if (props.status === 'failed') return props.message || '处理失败';
  if (props.status === 'cancelled') return props.message || '已取消';
  return '';
});

const themeClass = computed(() => {
  return document.body.classList.contains('dark') ? 'dark' : 'light';
});
const floatStyle = computed(() => ({
  right: '32px',
  bottom: '32px',
  position: 'fixed',
  zIndex: 9999,
  minWidth: minimized.value ? '180px' : '320px',
  maxWidth: '90vw',
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
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
  padding: 0;
  overflow: hidden;
  transition: box-shadow 0.2s;
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
  padding: 10px 16px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1rem;
}
.float-close {
  font-size: 1.2rem;
  cursor: pointer;
  margin-left: 10px;
}
.float-body {
  padding: 18px 20px 12px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.float-progress-bg {
  width: 100%;
  height: 14px;
  background: #e0e0e0;
  border-radius: 7px;
  overflow: hidden;
  margin-bottom: 8px;
}
.float-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #2196f3, #4caf50);
  border-radius: 7px;
  transition: width 0.3s;
}
.float-progress-text {
  font-weight: bold;
  color: var(--color-text, #222);
  margin-bottom: 6px;
}
.float-status-text {
  color: #888;
  font-size: 1rem;
  margin-bottom: 8px;
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
  border-radius: 6px;
  padding: 8px 20px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}
.cancel-btn:hover {
  background: #f57c00;
}
.float-fade-enter-active, .float-fade-leave-active {
  transition: opacity 0.3s;
}
.float-fade-enter-from, .float-fade-leave-to {
  opacity: 0;
}
</style> 