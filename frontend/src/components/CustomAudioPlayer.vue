<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { Howl } from 'howler';

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  title: {
    type: String,
    default: '音频文件'
  },
  showTitle: {
    type: Boolean,
    default: false
  },
  showDownload: {
    type: Boolean,
    default: false
  }
});

const isPlaying = ref(false);
const duration = ref(0);
const currentTime = ref(0);
const progress = ref(0);
const sound = ref(null);
const seekPosition = ref(0);
const error = ref(null);
const isLoaded = ref(false);

// 创建Howl实例
const initSound = () => {
  console.log('初始化音频播放器:', props.src);
  
  // 先销毁现有实例（如果有）
  if (sound.value) {
    sound.value.unload();
  }

  // 重置状态
  isLoaded.value = false;
  duration.value = 0;
  error.value = null;

  try {
    // 创建新的Howl实例
    sound.value = new Howl({
      src: [props.src],
      html5: true, // 使用HTML5 Audio
      preload: true,
      format: ['mp3', 'wav', 'ogg'],
      onplay: () => {
        console.log('音频开始播放');
        isPlaying.value = true;
        // 开始更新进度
        updateProgress();
      },
      onpause: () => {
        console.log('音频暂停');
        isPlaying.value = false;
      },
      onstop: () => {
        isPlaying.value = false;
        currentTime.value = 0;
        progress.value = 0;
      },
      onend: () => {
        isPlaying.value = false;
        currentTime.value = 0;
        progress.value = 0;
      },
      onload: () => {
        // 获取音频文件总时长
        console.log('音频加载完成，时长:', sound.value.duration());
        duration.value = sound.value.duration();
        isLoaded.value = true;
        error.value = null;
      },
      onloaderror: (id, err) => {
        console.error('加载音频失败:', err);
        error.value = '无法加载音频文件';
        isLoaded.value = false;
      }
    });
  } catch (e) {
    console.error('创建Howl实例失败:', e);
    error.value = '初始化播放器失败';
  }
};

// 切换播放/暂停
const togglePlay = () => {
  console.log('点击播放/暂停按钮');
  
  if (!sound.value) {
    console.log('播放器未初始化，重新初始化');
    initSound();
  }
  
  if (!isLoaded.value) {
    console.log('音频尚未加载完成');
    return;
  }
  
  try {
    if (sound.value.playing()) {
      console.log('当前正在播放，执行暂停');
      sound.value.pause();
    } else {
      console.log('当前已暂停，执行播放');
      sound.value.play();
    }
  } catch (e) {
    console.error('播放/暂停操作失败:', e);
    error.value = '播放操作失败';
  }
};

// 更新进度信息
const updateProgress = () => {
  if (sound.value && isPlaying.value) {
    try {
      currentTime.value = sound.value.seek() || 0;
      if (duration.value > 0) {
        progress.value = (currentTime.value / duration.value) * 100;
      }
      
      // 如果还在播放，继续更新
      if (isPlaying.value) {
        requestAnimationFrame(updateProgress);
      }
    } catch (e) {
      console.error('更新进度失败:', e);
    }
  }
};

// 跳转到指定位置
const seek = (event) => {
  console.log('点击进度条');
  
  if (!sound.value || !isLoaded.value) {
    console.log('音频未加载，无法跳转');
    return;
  }
  
  try {
    const container = event.currentTarget;
    const rect = container.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const percentage = x / rect.width;
    
    console.log('点击进度条位置:', percentage);
    
    // 计算新位置
    const seekTime = duration.value * percentage;
    console.log('跳转到时间点:', seekTime, '秒, 总时长:', duration.value);
    
    if (seekTime >= 0 && seekTime <= duration.value) {
      sound.value.seek(seekTime);
      
      // 更新UI
      currentTime.value = seekTime;
      progress.value = percentage * 100;
      console.log('跳转成功, 当前进度:', progress.value, '%');
    }
  } catch (e) {
    console.error('跳转操作失败:', e);
  }
};

// 格式化时间显示
const formatTime = (secs) => {
  if (!secs || isNaN(secs)) return '0:00';
  
  const minutes = Math.floor(secs / 60) || 0;
  const seconds = Math.floor(secs % 60) || 0;
  
  return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
};

// 下载音频
const downloadAudio = () => {
  window.open(props.src, '_blank');
};

// 监听src属性变化，重新初始化播放器
watch(() => props.src, (newSrc, oldSrc) => {
  console.log('音频源变更:', oldSrc, '->', newSrc);
  if (newSrc && newSrc !== oldSrc) {
    // 重置状态
    isPlaying.value = false;
    currentTime.value = 0;
    progress.value = 0;
    
    // 初始化音频
    initSound();
  }
});

// 组件挂载时初始化
onMounted(() => {
  console.log('音频播放器组件挂载');
  if (props.src) {
    initSound();
  }
});

// 组件卸载时销毁Howl实例
onUnmounted(() => {
  console.log('音频播放器组件卸载');
  if (sound.value) {
    sound.value.unload();
    sound.value = null;
  }
});
</script>

<template>
  <div class="custom-audio-player" :class="{ 'error': error }">
    <div v-if="showTitle" class="player-title">{{ title }}</div>
    
    <div class="player-controls">
      <!-- 播放/暂停按钮 -->
      <button @click="togglePlay" class="play-button" :class="{ 'playing': isPlaying }">
        <i :class="isPlaying ? 'pause-icon' : 'play-icon'"></i>
      </button>
      
      <!-- 进度条 -->
      <div class="progress-container" @mousedown="seek">
        <div class="progress-bar">
          <div class="progress-current" :style="{ width: `${progress}%` }"></div>
        </div>
        
        <!-- 时间显示 -->
        <div class="time-display">
          <span class="current-time">{{ formatTime(currentTime) }}</span>
          <span class="duration">{{ formatTime(duration) }}</span>
        </div>
      </div>
      
      <!-- 下载按钮 -->
      <button v-if="showDownload" @click="downloadAudio" class="download-button">
        <i class="download-icon"></i>
      </button>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="error" class="player-error">
      {{ error }}
    </div>
  </div>
</template>

<style scoped>
.custom-audio-player {
  width: 100%;
  max-width: 350px;
  background: #f5f5f5;
  border-radius: 8px;
  padding: 12px;
  font-family: Arial, sans-serif;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  margin: 10px 0;
}

.player-title {
  font-size: 14px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.play-button {
  width: 36px;
  height: 36px;
  background: #673ab7;
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.play-button:hover {
  background: #5e35b1;
  transform: scale(1.05);
}

.play-button.playing {
  background: #f44336;
}

.play-icon::before {
  content: "▶";
  font-size: 14px;
}

.pause-icon::before {
  content: "⏸";
  font-size: 14px;
}

.progress-container {
  flex: 1;
  cursor: pointer;
}

.progress-bar {
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.progress-current {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(90deg, #673ab7, #9c27b0);
  border-radius: 4px;
  transition: width 0.1s linear;
}

.time-display {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.download-button {
  width: 36px;
  height: 36px;
  background: #4caf50;
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.download-button:hover {
  background: #43a047;
  transform: scale(1.05);
}

.download-icon::before {
  content: "↓";
  font-size: 16px;
  font-weight: bold;
}

.player-error {
  margin-top: 8px;
  color: #f44336;
  font-size: 12px;
}

.custom-audio-player.error .progress-bar {
  background: #ffcdd2;
}
</style> 