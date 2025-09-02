<template>
  <div class="smart-voice-recorder">
    <div class="voice-interface">
      <div class="voice-status" :class="{ active: isListening, processing: isProcessing }">
        <div class="voice-wave" v-if="isListening">
          <div class="wave-bar" v-for="i in 5" :key="i"></div>
        </div>
        <div class="voice-icon" v-else>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </div>
      </div>
      
      <div class="voice-controls">
        <button 
          @click="toggleRecording" 
          :disabled="isProcessing"
          class="voice-btn"
          :class="{ recording: isListening, processing: isProcessing }"
        >
          {{ isListening ? '停止录音' : isProcessing ? '处理中...' : '开始语音预约' }}
        </button>
        
        <button 
          v-if="!isListening && !isProcessing"
          @click="startConversation"
          class="conversation-btn"
        >
          开始对话
        </button>
      </div>
    </div>

    <!-- 对话历史 -->
    <div class="conversation-history" v-if="conversationHistory.length > 0">
      <div 
        v-for="(message, index) in conversationHistory" 
        :key="index"
        class="message"
        :class="{ user: message.type === 'user', assistant: message.type === 'assistant' }"
      >
        <div class="message-content">
          <div class="message-text">{{ message.text }}</div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
        
        <!-- 语音播放按钮 -->
        <button 
          v-if="message.type === 'assistant' && message.audioUrl"
          @click="playAudio(message.audioUrl)"
          class="play-audio-btn"
        >
          🔊
        </button>
      </div>
    </div>

    <!-- 实时转录显示 -->
    <div class="real-time-transcript" v-if="currentTranscript">
      <div class="transcript-label">实时识别：</div>
      <div class="transcript-text">{{ currentTranscript }}</div>
    </div>

    <!-- 预约结果显示 -->
    <div class="reservation-result" v-if="reservationResult">
      <div class="result-header" :class="{ success: reservationResult.success, error: !reservationResult.success }">
        {{ reservationResult.success ? '✅ 预约成功' : '❌ 预约失败' }}
      </div>
      <div class="result-details">{{ reservationResult.message }}</div>
      <div class="result-data" v-if="reservationResult.data">
        <p><strong>会议室：</strong>{{ reservationResult.data.room_name }}</p>
        <p><strong>时间：</strong>{{ reservationResult.data.start_time }} - {{ reservationResult.data.end_time }}</p>
        <p><strong>访客：</strong>{{ reservationResult.data.visitor_name }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useCloudSpeech } from '@/composables/useCloudSpeech'
import { useChatStore } from '@/stores/chat'

interface ConversationMessage {
  type: 'user' | 'assistant'
  text: string
  timestamp: Date
  audioUrl?: string
}

interface ReservationResult {
  success: boolean
  message: string
  data?: any
}

const emit = defineEmits<{
  reservationCompleted: [data: any]
}>()

const chatStore = useChatStore()
const { startListening, stopListening, isListening, transcript } = useCloudSpeech()

const isProcessing = ref(false)
const currentTranscript = ref('')
const conversationHistory = ref<ConversationMessage[]>([])
const reservationResult = ref<ReservationResult | null>(null)
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<Blob[]>([])
const isInConversation = ref(false)

// 语音识别和对话处理
const toggleRecording = async () => {
  if (isListening.value) {
    await stopListening()
    await processVoiceInput()
  } else {
    currentTranscript.value = ''
    reservationResult.value = null
    await startListening()
  }
}

// 开始对话模式
const startConversation = () => {
  isInConversation.value = true
  conversationHistory.value = []
  addAssistantMessage('您好！我是智能预约助手，请告诉我您的预约需求。您可以说："我要预约明天下午2点的会议室"')
}

// 处理语音输入
const processVoiceInput = async () => {
  if (!transcript.value) return
  
  isProcessing.value = true
  const userMessage = transcript.value
  
  // 添加用户消息到对话历史
  addUserMessage(userMessage)
  
  try {
    // 调用智能意图识别服务
    const response = await fetch('/api/chat/smart-reservation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        message: userMessage,
        conversation_history: conversationHistory.value.slice(-10), // 保留最近10条对话
        use_voice: true
      })
    })
    
    const result = await response.json()
    
    if (result.success) {
      // 处理助手回复
      await handleAssistantResponse(result)
      
      // 如果预约完成，显示结果
      if (result.reservation_completed) {
        reservationResult.value = {
          success: true,
          message: result.message,
          data: result.reservation_data
        }
        isInConversation.value = false
        emit('reservationCompleted', result.reservation_data)
      }
    } else {
      addAssistantMessage(result.message || '抱歉，我无法理解您的请求，请重新描述。')
    }
  } catch (error) {
    console.error('处理语音输入失败:', error)
    addAssistantMessage('抱歉，处理您的请求时出现错误，请稍后重试。')
  } finally {
    isProcessing.value = false
  }
}

// 处理助手回复
const handleAssistantResponse = async (result: any) => {
  const message = result.message
  addAssistantMessage(message)
  
  // 如果有语音合成需求，生成语音
  if (result.generate_speech) {
    try {
      const audioResponse = await fetch('/api/voice/text-to-speech', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          text: message,
          voice: 'default'
        })
      })
      
      if (audioResponse.ok) {
        const audioBlob = await audioResponse.blob()
        const audioUrl = URL.createObjectURL(audioBlob)
        
        // 更新最后一条助手消息，添加音频URL
        const lastMessage = conversationHistory.value[conversationHistory.value.length - 1]
        if (lastMessage && lastMessage.type === 'assistant') {
          lastMessage.audioUrl = audioUrl
        }
        
        // 自动播放语音回复
        playAudio(audioUrl)
      }
    } catch (error) {
      console.error('语音合成失败:', error)
    }
  }
}

// 添加用户消息
const addUserMessage = (text: string) => {
  conversationHistory.value.push({
    type: 'user',
    text,
    timestamp: new Date()
  })
}

// 添加助手消息
const addAssistantMessage = (text: string) => {
  conversationHistory.value.push({
    type: 'assistant',
    text,
    timestamp: new Date()
  })
}

// 播放音频
const playAudio = (audioUrl: string) => {
  const audio = new Audio(audioUrl)
  audio.play().catch(error => {
    console.error('播放音频失败:', error)
  })
}

// 格式化时间
const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 监听实时转录
watch(transcript, (newTranscript) => {
  currentTranscript.value = newTranscript
})

onMounted(() => {
  // 初始化语音功能
})

onUnmounted(() => {
  // 清理资源
  conversationHistory.value.forEach(message => {
    if (message.audioUrl) {
      URL.revokeObjectURL(message.audioUrl)
    }
  })
})
</script>

<style scoped>
.smart-voice-recorder {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.voice-interface {
  text-align: center;
  margin-bottom: 20px;
}

.voice-status {
  width: 120px;
  height: 120px;
  margin: 0 auto 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transition: all 0.3s ease;
}

.voice-status.active {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  animation: pulse 1.5s infinite;
}

.voice-status.processing {
  background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
  animation: spin 2s linear infinite;
}

.voice-wave {
  display: flex;
  align-items: center;
  gap: 3px;
}

.wave-bar {
  width: 4px;
  height: 20px;
  background: white;
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

.wave-bar:nth-child(2) { animation-delay: 0.1s; }
.wave-bar:nth-child(3) { animation-delay: 0.2s; }
.wave-bar:nth-child(4) { animation-delay: 0.3s; }
.wave-bar:nth-child(5) { animation-delay: 0.4s; }

.voice-controls {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.voice-btn, .conversation-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.voice-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.voice-btn.recording {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
}

.voice-btn.processing {
  background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
  cursor: not-allowed;
}

.conversation-btn {
  background: linear-gradient(135deg, #2ed573 0%, #7bed9f 100%);
  color: white;
}

.conversation-history {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 8px;
}

.message {
  margin-bottom: 15px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 18px;
  position: relative;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message.assistant .message-content {
  background: #e9ecef;
  color: #333;
}

.message-text {
  margin-bottom: 5px;
}

.message-time {
  font-size: 12px;
  opacity: 0.7;
}

.play-audio-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: background 0.3s ease;
}

.play-audio-btn:hover {
  background: rgba(0, 0, 0, 0.1);
}

.real-time-transcript {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.transcript-label {
  font-weight: 600;
  color: #856404;
  margin-bottom: 5px;
}

.transcript-text {
  color: #533f03;
  font-style: italic;
}

.reservation-result {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-top: 20px;
}

.result-header {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
}

.result-header.success {
  color: #28a745;
}

.result-header.error {
  color: #dc3545;
}

.result-details {
  margin-bottom: 15px;
  color: #666;
}

.result-data p {
  margin: 5px 0;
  color: #333;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes wave {
  0%, 100% { height: 20px; }
  50% { height: 35px; }
}
</style>