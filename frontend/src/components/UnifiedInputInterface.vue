<template>
  <div class="unified-input-interface">
    <!-- 智能建议区域 -->
    <div class="smart-suggestions" v-if="suggestions.length > 0 && !isListening">
      <div class="suggestions-header">
        <span class="suggestions-icon">💡</span>
        <span>智能建议</span>
      </div>
      <div class="suggestions-list">
        <button 
          v-for="(suggestion, index) in suggestions" 
          :key="index"
          @click="applySuggestion(suggestion)"
          class="suggestion-btn"
        >
          {{ suggestion }}
        </button>
      </div>
    </div>

    <!-- 主输入区域 -->
    <div class="input-container" :class="{ 'voice-active': isListening, 'processing': isProcessing }">
      <!-- 语音可视化区域 -->
      <div class="voice-visualization" v-if="isListening">
        <div class="voice-wave">
          <div class="wave-bar" v-for="i in 7" :key="i" :style="{ animationDelay: i * 0.1 + 's' }"></div>
        </div>
        <div class="voice-status-text">正在聆听...</div>
      </div>

      <!-- 实时转录显示 -->
      <div class="real-time-transcript" v-if="currentTranscript && isListening">
        <div class="transcript-content">
          <span class="transcript-icon">🎤</span>
          <span class="transcript-text">{{ currentTranscript }}</span>
        </div>
      </div>

      <!-- 文字输入区域 -->
      <div class="text-input-area" v-if="!isListening">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="1"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="输入消息或点击麦克风使用语音输入..."
          @keydown.enter="handleEnter"
          :disabled="isLoading || isProcessing"
          class="unified-input"
          ref="textInput"
        />
      </div>

      <!-- 控制按钮区域 -->
      <div class="control-buttons">
        <!-- 语音按钮 -->
        <button 
          @click="toggleRecording" 
          :disabled="isProcessing"
          :class="['voice-btn', { 
            'recording': isListening, 
            'pulse': !isListening && !isProcessing,
            'disabled': isProcessing 
          }]"
          :title="isListening ? '停止录音' : '开始语音输入'"
        >
          <div class="btn-icon">
            <svg v-if="!isListening" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 6h12v12H6z"/>
            </svg>
          </div>
        </button>

        <!-- 发送按钮 -->
        <button 
          @click="sendMessage" 
          :disabled="!inputMessage.trim() || isLoading || isProcessing"
          :class="['send-btn', { 'active': inputMessage.trim() }]"
          title="发送消息"
        >
          <div class="btn-icon">
            <svg v-if="!isLoading" width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
            <div v-else class="loading-spinner"></div>
          </div>
        </button>
      </div>
    </div>

    <!-- 状态指示器 -->
    <div class="status-indicator" v-if="isProcessing || isLoading">
      <div class="status-content">
        <div class="status-spinner"></div>
        <span class="status-text">
          {{ isProcessing ? '正在处理语音...' : '发送中...' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useCloudSpeech } from '@/composables/useCloudSpeech'

// Props
const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  suggestions: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits([
  'update:modelValue',
  'message-sent',
  'voice-start',
  'voice-end',
  'suggestion-applied'
])

// Refs
const textInput = ref(null)
const isLoading = ref(false)
const isProcessing = ref(false)

// 语音相关
const {
  isListening,
  transcript: currentTranscript,
  startListening,
  stopListening,
  toggleListening
} = useCloudSpeech()

// 计算属性
const inputMessage = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 方法
const toggleRecording = async () => {
  if (isListening.value) {
    stopListening()
    emit('voice-end')
  } else {
    emit('voice-start')
    await startListening()
  }
}

const sendMessage = async () => {
  if (isListening.value) {
    stopListening()
    return
  }
  
  if (!inputMessage.value.trim()) return
  
  isLoading.value = true
  try {
    emit('message-sent', inputMessage.value.trim())
    inputMessage.value = ''
  } finally {
    isLoading.value = false
    await nextTick()
    textInput.value?.focus()
  }
}

const handleEnter = (event) => {
  if (!event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const applySuggestion = (suggestion) => {
  inputMessage.value = suggestion
  emit('suggestion-applied', suggestion)
  nextTick(() => {
    textInput.value?.focus()
  })
}

// 监听语音转录结果
watch(currentTranscript, (newTranscript) => {
  if (newTranscript && !isListening.value) {
    inputMessage.value = newTranscript
  }
})

// 监听语音状态变化
watch(isListening, (listening) => {
  isProcessing.value = false
  if (!listening && currentTranscript.value) {
    isProcessing.value = true
    setTimeout(() => {
      isProcessing.value = false
    }, 1000)
  }
})
</script>

<style scoped>
.unified-input-interface {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.input-container {
  background: #ffffff;
  border: 2px solid #e1e8ed;
  border-radius: 20px;
  padding: 16px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.input-container:hover {
  border-color: #667eea;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
}

.input-container.voice-active {
  border-color: #ff6b6b;
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  box-shadow: 0 8px 32px rgba(255, 107, 107, 0.3);
}

.input-container.processing {
  border-color: #ffa726;
  background: linear-gradient(135deg, #ffd54f 0%, #ffecb3 100%);
}

/* 语音可视化 */
.voice-visualization {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.voice-wave {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
}

.wave-bar {
  width: 4px;
  height: 20px;
  background: linear-gradient(to top, #ff6b6b, #ff8e8e);
  border-radius: 2px;
  animation: wave 1.5s ease-in-out infinite;
}

.voice-status-text {
  color: #d63031;
  font-weight: 600;
  font-size: 16px;
}

/* 实时转录 */
.real-time-transcript {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  backdrop-filter: blur(10px);
}

.transcript-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.transcript-icon {
  font-size: 16px;
}

.transcript-text {
  color: #2d3436;
  font-style: italic;
  flex: 1;
}

/* 文字输入区域 */
.text-input-area {
  margin-bottom: 12px;
}

.unified-input {
  border: none;
  background: transparent;
}

.unified-input :deep(.el-textarea__inner) {
  border: none;
  background: transparent;
  resize: none;
  font-size: 16px;
  line-height: 1.5;
  padding: 0;
  box-shadow: none;
}

.unified-input :deep(.el-textarea__inner):focus {
  box-shadow: none;
}

/* 控制按钮 */
.control-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  align-items: center;
}

.voice-btn, .send-btn {
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.voice-btn {
  background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
  color: white;
  box-shadow: 0 4px 16px rgba(116, 185, 255, 0.3);
}

.voice-btn.recording {
  background: linear-gradient(135deg, #ff6b6b 0%, #e17055 100%);
  animation: pulse-recording 2s ease-in-out infinite;
}

.voice-btn.processing {
  background: linear-gradient(135deg, #ffa726 0%, #ff9800 100%);
}

.voice-btn.pulse {
  animation: gentle-pulse 3s ease-in-out infinite;
}

.send-btn {
  background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
  color: white;
  box-shadow: 0 4px 16px rgba(0, 184, 148, 0.3);
  opacity: 0.6;
  transform: scale(0.9);
}

.send-btn.has-content {
  opacity: 1;
  transform: scale(1);
}

.voice-btn:hover, .send-btn:hover {
  transform: translateY(-2px) scale(1.05);
}

.voice-btn:disabled, .send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* 智能建议 */
.smart-suggestions {
  margin-bottom: 16px;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
}

.suggestions-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #495057;
}

.suggestions-icon {
  font-size: 16px;
}

.suggestions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-btn {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 14px;
  color: #495057;
  cursor: pointer;
  transition: all 0.3s ease;
}

.suggestion-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-1px);
}

/* 状态指示器 */
.status-indicator {
  margin-top: 12px;
  text-align: center;
}

.status-content {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 20px;
  padding: 8px 16px;
}

.status-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top: 2px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.status-text {
  font-size: 14px;
  color: #666;
}

/* 动画 */
@keyframes wave {
  0%, 100% { height: 20px; }
  50% { height: 35px; }
}

@keyframes pulse-recording {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 4px 16px rgba(255, 107, 107, 0.3);
  }
  50% { 
    transform: scale(1.1);
    box-shadow: 0 8px 32px rgba(255, 107, 107, 0.5);
  }
}

@keyframes gentle-pulse {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 4px 16px rgba(116, 185, 255, 0.3);
  }
  50% { 
    transform: scale(1.02);
    box-shadow: 0 6px 20px rgba(116, 185, 255, 0.4);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .input-container {
    padding: 12px;
  }
  
  .voice-btn, .send-btn {
    width: 44px;
    height: 44px;
  }
  
  .suggestions-list {
    flex-direction: column;
  }
  
  .suggestion-btn {
    text-align: left;
  }
}
</style>