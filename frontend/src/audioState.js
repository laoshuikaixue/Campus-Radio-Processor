import { ref } from 'vue';

// 全局共享的音频状态（极简版，仅用于兼容现有代码结构）
export const audioState = {
  currentPlayingId: ref(null),
  isPlaying: ref(false),
  playbackProgress: ref(0),
  currentTime: ref('0:00'),
  remainingTime: ref('0:00'),
  
  // 重置状态
  resetState() {
    this.currentPlayingId.value = null;
    this.isPlaying.value = false;
    this.playbackProgress.value = 0;
    this.currentTime.value = '0:00';
    this.remainingTime.value = '0:00';
  }
}; 