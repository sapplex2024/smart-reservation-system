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
    <div class="input-container">
      <!-- 文字输入区域 -->
      <div class="text-input-area">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="1"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="输入消息..."
          @keydown.enter="handleEnter"
          :disabled="isLoading"
          class="unified-input"
          ref="textInput"
        />
      </div>

      <!-- 控制按钮区域 -->
      <div class="control-buttons">
        <!-- 发送按钮 -->
        <button 
          @click="sendMessage" 
          :disabled="!inputMessage.trim() || isLoading"
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
    <div class="status-indicator" v-if="isLoading">
      <div class="status-content">
        <div class="status-spinner"></div>
        <span class="status-text">发送中...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'

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
  'suggestion-applied'
])

// Refs
const textInput = ref(null)
const isLoading = ref(false)

// 计算属性
const inputMessage = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 方法
const sendMessage = async () => {
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

.send-btn {
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

.send-btn:hover {
  transform: translateY(-2px) scale(1.05);
}

.send-btn:disabled {
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
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .input-container {
    padding: 12px;
  }
  
  .send-btn {
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