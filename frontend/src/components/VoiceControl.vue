<template>
  <div class="voice-control">
    <!-- 语音输入按钮 -->
    <div class="voice-input-section">
      <el-button
        :type="isListening ? 'danger' : 'primary'"
        :icon="isListening ? VideoPause : Microphone"
        @click="toggleListening"
        :disabled="!isSupported"
        class="voice-btn"
        :class="{ 'listening': isListening, 'pulse': isListening }"
        size="large"
        circle
      >
      </el-button>
      
      <div class="voice-status">
        <span v-if="!isSupported" class="status-text error">
          浏览器不支持语音功能
        </span>
        <span v-else-if="isListening" class="status-text listening">
          正在听取语音...
        </span>
        <span v-else class="status-text">
          点击开始语音输入
        </span>
      </div>
    </div>
    
    <!-- 实时转录显示 -->
    <div v-if="transcript" class="transcript-display">
      <el-card shadow="hover" class="transcript-card">
        <div class="transcript-header">
          <el-icon><ChatDotRound /></el-icon>
          <span>语音识别结果</span>
          <el-button
            type="text"
            :icon="Close"
            @click="clearTranscript"
            size="small"
          />
        </div>
        <div class="transcript-content">
          {{ transcript }}
        </div>
        <div class="transcript-actions">
          <el-button
            type="primary"
            size="small"
            @click="sendTranscript"
            :disabled="!transcript.trim()"
          >
            发送
          </el-button>
          <el-button
            size="small"
            @click="insertTranscript"
            :disabled="!transcript.trim()"
          >
            插入到输入框
          </el-button>
        </div>
      </el-card>
    </div>
    
    <!-- 语音播放控制 -->
    <div class="voice-output-section">
      <el-button
        :type="isSpeaking ? 'warning' : 'success'"
        :icon="isSpeaking ? VideoPause : VideoPlay"
        @click="toggleSpeaking"
        :disabled="!isSupported || !lastMessage"
        size="small"
      >
        {{ isSpeaking ? '停止播放' : '播放回复' }}
      </el-button>
      
      <!-- 语音设置按钮 -->
      <el-button
        type="text"
        :icon="Setting"
        @click="showVoiceSettings = !showVoiceSettings"
        size="small"
        class="settings-btn"
      >
        语音设置
      </el-button>
    </div>
    
    <!-- 语音设置面板 -->
    <div v-if="showVoiceSettings" class="voice-settings-panel">
      <el-card shadow="hover" class="settings-card">
        <div class="settings-header">
          <el-icon><Setting /></el-icon>
          <span>语音设置</span>
          <el-button
            type="text"
            :icon="Close"
            @click="showVoiceSettings = false"
            size="small"
          />
        </div>
        
        <div class="settings-content">
          <div class="setting-item">
            <label>语音提供商</label>
            <el-select 
              v-model="selectedProvider" 
              @change="handleProviderChange"
              size="small"
              style="width: 150px"
            >
              <el-option 
                v-for="provider in availableProviders" 
                :key="provider.id"
                :label="provider.name" 
                :value="provider.id"
                :disabled="!provider.available"
              />
            </el-select>
          </div>
          
          <div v-if="selectedProvider === 'siliconflow'" class="setting-item">
            <label>语音模型</label>
            <el-select 
              v-model="selectedModel" 
              @change="handleModelChange"
              size="small"
              style="width: 200px"
            >
              <el-option 
                v-for="model in getAvailableModels" 
                :key="model.id"
                :label="model.name" 
                :value="model.id"
              />
            </el-select>
          </div>
          
          <div class="setting-item">
            <label>默认音色</label>
            <el-select 
              v-model="selectedVoice" 
              size="small"
              style="width: 150px"
            >
              <el-option 
                v-for="voice in availableVoices" 
                :key="voice.id"
                :label="voice.name" 
                :value="voice.id"
              />
            </el-select>
          </div>
          
          <div class="setting-item">
            <el-button
              type="primary"
              size="small"
              @click="testConnection"
              :loading="testingConnection"
            >
              测试连接
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
    
    <!-- 音频可视化 -->
    <div v-if="isListening" class="audio-visualizer">
      <div class="wave-container">
        <div 
          v-for="i in 5" 
          :key="i"
          class="wave-bar"
          :style="{ animationDelay: `${i * 0.1}s` }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { 
  Microphone, 
  VideoPause, 
  VideoPlay, 
  ChatDotRound, 
  Close,
  Setting
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useCloudSpeech } from '../composables/useCloudSpeech'

interface Props {
  modelValue?: string
  lastMessage?: string
  disabled?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'send-message', message: string): void
  (e: 'voice-start'): void
  (e: 'voice-end'): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  lastMessage: '',
  disabled: false
})

const emit = defineEmits<Emits>()

const {
  isListening,
  isSpeaking,
  isSupported,
  transcript,
  toggleListening: cloudToggleListening,
  toggleSpeaking: cloudToggleSpeaking,
  speak,
  stopSpeaking,
  init,
  availableProviders,
  selectedProvider,
  selectedModel,
  getAvailableModels,
  availableVoices,
  selectedVoice,
  switchProvider,
  testConnection: cloudTestConnection,
  loadProviders,
  loadVoices
} = useCloudSpeech()

// 语音设置面板状态
const showVoiceSettings = ref(false)
const testingConnection = ref(false)

// 初始化云端语音功能
init().then(success => {
  if (!success) {
    ElMessage.warning('云端语音服务连接失败，部分功能可能不可用')
  }
})

// 切换语音识别
const toggleListening = () => {
  if (props.disabled) return
  
  cloudToggleListening()
  
  if (isListening.value) {
    emit('voice-start')
  } else {
    emit('voice-end')
  }
}

// 切换语音播放
const toggleSpeaking = () => {
  if (props.lastMessage) {
    cloudToggleSpeaking(props.lastMessage)
  }
}

// 清空转录结果
const clearTranscript = () => {
  transcript.value = ''
}

// 发送转录结果
const sendTranscript = () => {
  if (transcript.value.trim()) {
    emit('send-message', transcript.value.trim())
    clearTranscript()
  }
}

// 将转录结果插入到输入框
const insertTranscript = () => {
  if (transcript.value.trim()) {
    const currentValue = props.modelValue
    const newValue = currentValue ? `${currentValue} ${transcript.value.trim()}` : transcript.value.trim()
    emit('update:modelValue', newValue)
    clearTranscript()
    ElMessage.success('语音内容已插入到输入框')
  }
}

// 处理语音提供商变更
const handleProviderChange = async (provider: string) => {
  try {
    await switchProvider(provider)
    ElMessage.success(`已切换到${provider === 'qwen' ? '通义千问' : '硅基流动'}语音服务`)
  } catch (error) {
    ElMessage.error('切换语音提供商失败')
    console.error('切换语音提供商失败:', error)
  }
}

// 处理语音模型变更
const handleModelChange = (model: string) => {
  selectedModel.value = model
  ElMessage.success('语音模型已更新')
}

// 测试语音连接
const testConnection = async () => {
  testingConnection.value = true
  try {
    await cloudTestConnection(selectedProvider.value)
  } catch (error) {
    console.error('测试连接失败:', error)
  } finally {
    testingConnection.value = false
  }
}

// 监听语音识别状态变化
watch(isListening, (newValue) => {
  if (newValue) {
    emit('voice-start')
  } else {
    emit('voice-end')
  }
})
</script>

<style scoped>
.voice-control {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  margin-bottom: 16px;
}

.voice-input-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.voice-btn {
  width: 60px;
  height: 60px;
  font-size: 24px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.voice-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

.voice-btn.listening {
  animation: pulse 1.5s infinite;
  background: linear-gradient(45deg, #ff6b6b, #ee5a24);
  border-color: #ff6b6b;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7);
  }
  70% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(255, 107, 107, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 107, 107, 0);
  }
}

.voice-status {
  text-align: center;
}

.status-text {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.status-text.listening {
  color: #ff6b6b;
  animation: blink 1s infinite;
}

.status-text.error {
  color: #f56565;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.5; }
}

.transcript-display {
  margin-top: 16px;
}

.transcript-card {
  border: 2px solid #e3f2fd;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
}

.transcript-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #2c3e50;
}

.transcript-content {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #409eff;
  font-size: 16px;
  line-height: 1.5;
  color: #2c3e50;
  margin-bottom: 12px;
  min-height: 40px;
}

.transcript-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.voice-output-section {
  display: flex;
  justify-content: center;
}

.audio-visualizer {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60px;
  margin-top: 16px;
}

.wave-container {
  display: flex;
  align-items: center;
  gap: 4px;
}

.wave-bar {
  width: 4px;
  height: 20px;
  background: linear-gradient(to top, #409eff, #67c23a);
  border-radius: 2px;
  animation: wave 1.2s ease-in-out infinite;
}

@keyframes wave {
  0%, 40%, 100% {
    transform: scaleY(0.4);
  }
  20% {
    transform: scaleY(1);
  }
}

.wave-bar:nth-child(1) { animation-delay: 0s; }
.wave-bar:nth-child(2) { animation-delay: 0.1s; }
.wave-bar:nth-child(3) { animation-delay: 0.2s; }
.wave-bar:nth-child(4) { animation-delay: 0.3s; }
.wave-bar:nth-child(5) { animation-delay: 0.4s; }

/* 语音设置面板样式 */
.voice-settings-panel {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 1000;
  margin-top: 8px;
}

.settings-card {
  width: 300px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
}

.settings-header span {
  margin-left: 8px;
  flex: 1;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.setting-item label {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
  min-width: 80px;
}

.settings-btn {
  margin-left: 8px;
  color: #666;
}

.settings-btn:hover {
  color: #409eff;
}

.voice-output-section {
  position: relative;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .voice-control {
    padding: 12px;
  }
  
  .voice-btn {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }
  
  .transcript-actions {
    flex-direction: column;
  }
}
</style>