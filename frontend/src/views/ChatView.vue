<template>
  <div class="chat-container">
    <!-- 主对话区域 -->
    <div class="chat-main">
      <div class="chat-header">
        <div class="header-left">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能预约助手</span>
          <el-tag v-if="isLoading" type="success" size="small" class="status-tag">
            <el-icon class="loading-icon"><Loading /></el-icon>
            思考中...
          </el-tag>
        </div>
        <div class="header-actions">
          <el-tooltip content="快捷操作" placement="bottom">
            <el-button 
              type="text" 
              size="small" 
              :icon="Lightning" 
              @click="toggleSidebar"
              class="header-btn"
              :class="{ active: showSidebar }"
            />
          </el-tooltip>
          <el-tooltip content="搜索消息" placement="bottom">
            <el-button 
              type="text" 
              size="small" 
              :icon="Search" 
              @click="showSearchDialog = true"
              class="header-btn"
            />
          </el-tooltip>
          <el-tooltip content="主题切换" placement="bottom">
            <el-button 
              type="text" 
              size="small" 
              :icon="isDarkMode ? Sunny : Moon" 
              @click="toggleTheme"
              class="header-btn"
            />
          </el-tooltip>
          <el-tooltip content="清空对话" placement="bottom">
            <el-button 
              type="text" 
              size="small" 
              :icon="Delete" 
              @click="clearChat"
              class="header-btn clear-btn"
            />
          </el-tooltip>
        </div>
      </div>
      
      <div class="chat-messages" ref="messagesContainer">
        <div 
          v-for="message in messages" 
          :key="message.id"
          :class="['message', message.role]"
        >
          <div class="message-avatar">
            <el-avatar 
              :icon="message.role === 'user' ? User : Service" 
              :style="{ backgroundColor: message.role === 'user' ? '#409EFF' : '#67C23A' }"
            />
          </div>
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.content)"></div>
            <div class="message-footer">
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
              <div class="message-actions">
                <el-tooltip content="复制消息" placement="top">
                  <el-button 
                    type="text" 
                    size="small" 
                    :icon="CopyDocument" 
                    @click="copyMessage(message.content)"
                    class="action-btn"
                  />
                </el-tooltip>
                <el-tooltip v-if="message.role === 'assistant'" content="朗读消息" placement="top">
                  <el-button 
                    type="text" 
                    size="small" 
                    :icon="isSpeaking ? VideoPause : VideoPlay" 
                    @click="speak(message.content)"
                    class="action-btn"
                  />
                </el-tooltip>
                <el-tooltip content="删除消息" placement="top">
                  <el-button 
                    type="text" 
                    size="small" 
                    :icon="Delete" 
                    @click="deleteMessage(message.id)"
                    class="action-btn delete-btn"
                  />
                </el-tooltip>
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="isLoading" class="message assistant">
          <div class="message-avatar">
            <el-avatar :icon="Service" style="background-color: #67C23A" />
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 智能语音录制组件 -->
      <div class="input-container">
        <UnifiedInputInterface
          v-model="inputMessage"
          :disabled="isLoading"
          :suggestions="smartSuggestions"
          @message-sent="handleUnifiedMessage"
          @voice-start="handleVoiceStart"
          @voice-end="handleVoiceEnd"
          @suggestion-applied="handleSuggestionApplied"
        />
      </div>
    </div>
    
    <!-- 可折叠侧边栏 -->
    <transition name="sidebar">
      <div v-show="showSidebar" class="sidebar" @click.self="closeSidebar">
        <div class="sidebar-content">
          <!-- 快捷操作面板 -->
          <div class="panel quick-actions">
            <div class="panel-header">
              <el-icon><Lightning /></el-icon>
              <span>快捷操作</span>
              <el-button 
                type="text" 
                size="small" 
                :icon="Close" 
                @click="closeSidebar"
                class="close-btn"
              />
            </div>
            
            <div class="quick-buttons">
              <el-button 
                v-for="action in quickActions" 
                :key="action.text"
                @click="sendQuickMessage(action.text)"
                :disabled="isLoading"
                class="quick-btn"
              >
                {{ action.text }}
              </el-button>
            </div>
          </div>
          
          <!-- 语音设置面板 -->
          <div class="panel voice-settings">
            <div class="panel-header">
              <el-icon><Setting /></el-icon>
              <span>语音设置</span>
            </div>
            
            <div class="settings-content">
              <div class="setting-item">
                <el-switch
                  v-model="autoPlayVoice"
                  active-text="自动播放回复"
                  inactive-text="手动播放"
                  :disabled="isSpeaking"
                />
              </div>
              
              <div class="setting-item">
                 <el-button
                   v-if="isSpeaking"
                   type="warning"
                   size="small"
                   @click="stopSpeaking"
                   :icon="VideoPause"
                 >
                   停止播放
                 </el-button>
                 <el-button
                   v-else-if="lastAssistantMessage"
                   type="success"
                   size="small"
                   @click="playLastMessage"
                   :icon="VideoPlay"
                 >
                   播放回复
                 </el-button>
                 <span v-else class="voice-status">
                   暂无回复可播放
                 </span>
               </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- 搜索对话框 -->
    <el-dialog
      v-model="showSearchDialog"
      title="搜索消息"
      width="500px"
      :before-close="() => showSearchDialog = false"
    >
      <el-input
        placeholder="输入关键词搜索消息..."
        prefix-icon="Search"
        clearable
      />
      <div class="search-results">
        <!-- 搜索结果将在这里显示 -->
      </div>
      <template #footer>
        <el-button @click="showSearchDialog = false">取消</el-button>
        <el-button type="primary" @click="showSearchDialog = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from 'vue'
import { 
  ChatDotRound, 
  User, 
  Service, 
  Promotion, 
  Delete, 
  Lightning,
  Setting,
  VideoPause,
  VideoPlay,
  Search,
  Moon,
  Sunny,
  Loading,
  CopyDocument,
  Close
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { useChatStore } from '../stores/chat'
import UnifiedInputInterface from '../components/UnifiedInputInterface.vue'
import { useSpeech } from '../composables/useSpeech'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const chatStore = useChatStore()
const messages = ref<Message[]>([])
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const showSearchDialog = ref(false)
const isDarkMode = ref(false)
const showSidebar = ref(false)

// 使用chatStore中的isLoading状态
const isLoading = computed(() => chatStore.isLoading)

// 语音功能
const { speak, stopSpeaking, isSpeaking } = useSpeech()
const autoPlayVoice = ref(false) // 是否自动播放AI回复

const quickActions = [
  { text: '预约会议室' },
  { text: '查看我的预约' },
  { text: '取消预约' },
  { text: '预约访客' },
  { text: '预约停车位' }
]

// 智能建议
const smartSuggestions = ref([
  '我要预约明天上午10点的会议室',
  '查看我今天的预约',
  '帮助'
])

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return
  
  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: inputMessage.value,
    timestamp: new Date()
  }
  
  messages.value.push(userMessage)
  const messageText = inputMessage.value
  inputMessage.value = ''
  
  await scrollToBottom()
  
  try {
    const response = await chatStore.sendMessage(messageText, {
      voiceEnabled: autoPlayVoice.value,
      voiceProvider: 'qwen', // 可以从设置中获取
      voiceModel: undefined
    })
    
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.response,
      timestamp: new Date()
    }
    
    messages.value.push(assistantMessage)
    await scrollToBottom()
    
    // 播放AI回复语音
    if (autoPlayVoice.value) {
      if (response.audio_url) {
        // 如果后端返回了语音URL，直接播放
        const audio = new Audio(response.audio_url)
        audio.play().catch(error => {
          console.error('音频播放失败:', error)
          // 回退到本地TTS
          setTimeout(() => {
            speak(response.response)
          }, 500)
        })
      } else {
        // 使用本地TTS
        setTimeout(() => {
          speak(response.response)
        }, 500)
      }
    }
    
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请稍后重试')
    // 确保在错误情况下也能重新输入
    inputMessage.value = messageText
  }
}

const sendQuickMessage = (text: string) => {
  inputMessage.value = text
  sendMessage()
}

const handleEnter = (event: KeyboardEvent) => {
  if (!event.shiftKey) {
    sendMessage()
  }
}

const clearChat = () => {
  messages.value = []
  ElMessage.success('对话已清空')
}

const formatMessage = (content: string) => {
  return marked(content)
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 语音相关方法
const lastAssistantMessage = computed(() => {
  const assistantMessages = messages.value.filter(msg => msg.role === 'assistant')
  return assistantMessages.length > 0 ? assistantMessages[assistantMessages.length - 1].content : ''
})

const handleVoiceMessage = (message: string) => {
  inputMessage.value = message
  sendMessage()
}

const handleVoiceStart = () => {
  // 语音开始时的处理逻辑
  console.log('语音识别开始')
}

const handleVoiceEnd = () => {
  // 语音结束时的处理逻辑
  console.log('语音识别结束')
}

// 智能语音消息处理
const handleSmartVoiceMessage = (data: any) => {
  // 处理智能语音消息
  if (data.message) {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: data.message,
      timestamp: new Date()
    }
    messages.value.push(userMessage)
  }
  
  if (data.response) {
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: data.response,
      timestamp: new Date()
    }
    messages.value.push(assistantMessage)
    
    // 自动播放回复
    if (autoPlayVoice.value && data.response) {
      setTimeout(() => {
        speak(data.response)
      }, 500)
    }
  }
  
  scrollToBottom()
}

// 预约创建成功处理
const handleReservationCreated = (reservation: any) => {
  ElMessage.success('预约创建成功！')
  console.log('预约详情:', reservation)
  
  // 可以在这里添加更多处理逻辑，比如刷新预约列表等
}

// 统一消息处理（替代原来的sendMessage和handleSmartVoiceMessage）
const handleUnifiedMessage = async (message: string) => {
  if (!message.trim() || isLoading.value) return
  
  const userMessage: Message = {
    id: Date.now().toString(),
    role: 'user',
    content: message,
    timestamp: new Date()
  }
  
  messages.value.push(userMessage)
  await scrollToBottom()
  
  try {
    const response = await chatStore.sendMessage(message, {
      voiceEnabled: autoPlayVoice.value,
      voiceProvider: 'qwen',
      voiceModel: undefined
    })
    
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: response.response,
      timestamp: new Date()
    }
    
    messages.value.push(assistantMessage)
    await scrollToBottom()
    
    // 播放AI回复语音
    if (autoPlayVoice.value) {
      if (response.audio_url) {
        const audio = new Audio(response.audio_url)
        audio.play().catch(error => {
          console.error('音频播放失败:', error)
          setTimeout(() => {
            speak(response.response)
          }, 500)
        })
      } else {
        setTimeout(() => {
          speak(response.response)
        }, 500)
      }
    }
    
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请稍后重试')
  }
}

// 建议应用处理
const handleSuggestionApplied = (suggestion: string) => {
  console.log('应用建议:', suggestion)
  // 可以在这里添加更多逻辑，比如更新建议列表等
}

// 手动播放最新回复
const playLastMessage = () => {
  if (lastAssistantMessage.value) {
    speak(lastAssistantMessage.value)
  }
}

// 复制消息
const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('消息已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 删除消息
const deleteMessage = (messageId: string) => {
  const index = messages.value.findIndex(msg => msg.id === messageId)
  if (index > -1) {
    messages.value.splice(index, 1)
    ElMessage.success('消息已删除')
  }
}

// 主题切换
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  ElMessage.success(`已切换到${isDarkMode.value ? '深色' : '浅色'}主题`)
}

// 侧边栏控制
const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
}

const closeSidebar = () => {
  showSidebar.value = false
}

onMounted(() => {
  // 添加欢迎消息
  messages.value.push({
    id: 'welcome',
    role: 'assistant',
    content: '您好！我是智能预约助手，可以帮您预约会议室、访客接待和停车位。请告诉我您需要什么帮助？',
    timestamp: new Date()
  })
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.chat-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="%23ffffff" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
  pointer-events: none;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 0;
  box-shadow: none;
  position: relative;
  overflow: hidden;
}

.input-container {
  position: sticky;
  bottom: 0;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  padding: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin-top: auto;
  z-index: 10;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.95);
  color: #333;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(20px);
  position: sticky;
  top: 0;
  z-index: 20;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-btn {
  background: transparent;
  border: none;
  color: #666;
  border-radius: 8px;
  padding: 8px;
  transition: all 0.3s ease;
}

.header-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  transform: translateY(-1px);
}

.header-btn.active {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

.clear-btn:hover {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

.status-tag {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
  min-height: 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(102, 126, 234, 0.3) transparent;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

.message {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.5s ease-out;
  position: relative;
}

.message.user {
  flex-direction: row-reverse;
}

.message.assistant {
  justify-content: flex-start;
}

.message::before {
  content: '';
  position: absolute;
  width: 2px;
  height: 0;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 1px;
  animation: messageLineGrow 0.3s ease-out 0.2s forwards;
}

.message.user::before {
  right: 60px;
}

.message.assistant::before {
  left: 60px;
}

@keyframes messageLineGrow {
  to { height: 100%; }
}

.message-avatar {
  margin: 0 12px;
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  min-width: 80px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.message-content:hover {
  transform: translateY(-2px);
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  background: #ffffff;
  padding: 16px 20px;
  border-radius: 20px;
  word-wrap: break-word;
  line-height: 1.4;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: relative;
  font-size: 14px;
  transition: all 0.3s ease;
}

.message-text:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px 20px 8px 20px;
  position: relative;
  overflow: hidden;
}

.message.user .message-text::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 25%, transparent 25%, transparent 50%, rgba(255, 255, 255, 0.1) 50%, rgba(255, 255, 255, 0.1) 75%, transparent 75%);
  background-size: 20px 20px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.message.user .message-text:hover::before {
  opacity: 1;
}

.message.assistant .message-text {
  background: rgba(245, 247, 250, 0.9);
  color: #333;
  border-radius: 20px 20px 20px 8px;
  border: 1px solid rgba(228, 231, 237, 0.6);
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
  opacity: 0.7;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 18px 18px 18px 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e9ecef;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #999;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

/* 原chat-input相关样式已移除，现在使用UnifiedInputInterface组件 */

/* 侧边栏样式 */
.sidebar {
  position: fixed;
  top: 0;
  right: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(5px);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 20px;
}

.sidebar-content {
  width: 400px;
  max-width: 90vw;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.3);
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.sidebar-enter-active,
.sidebar-leave-active {
  transition: all 0.3s ease;
}

.sidebar-enter-from,
.sidebar-leave-to {
  opacity: 0;
}

.sidebar-enter-from .sidebar-content,
.sidebar-leave-to .sidebar-content {
  transform: translateX(100%);
}

/* 面板样式 */
.panel {
  background: transparent;
  border: none;
  box-shadow: none;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  font-weight: 600;
  font-size: 16px;
  color: #333;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.panel-header .el-icon {
  margin-right: 8px;
  color: #667eea;
}

.close-btn {
  background: transparent;
  border: none;
  color: #999;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}



.quick-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 20px 24px;
}

.quick-btn {
  padding: 12px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border: 1px solid rgba(102, 126, 234, 0.2);
  color: #667eea;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-btn:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.voice-settings {
  width: 100%;
  height: fit-content;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}



.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px 24px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.voice-status {
  font-size: 12px;
  color: #6c757d;
  background: #f8f9fa;
  padding: 4px 8px;
  border-radius: 12px;
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.message:hover .message-actions {
  opacity: 1;
}

.action-btn {
  padding: 2px 4px;
  min-height: 20px;
  font-size: 12px;
  color: #999;
}

.action-btn:hover {
  color: #409EFF;
}

.delete-btn:hover {
  color: #f56c6c;
}

.search-results {
  max-height: 300px;
  overflow-y: auto;
  margin-top: 16px;
}

/* 自定义滚动条 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .chat-header {
    padding: 12px 16px;
    font-size: 14px;
  }
  
  .header-actions {
    gap: 4px;
  }
  
  .header-btn {
    padding: 6px;
  }
  
  .chat-messages {
    padding: 16px;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .message-text {
    padding: 12px 16px;
    font-size: 13px;
  }
  
  .input-container {
    padding: 16px;
  }
  
  .sidebar-content {
    width: 350px;
    margin: 10px;
  }
  
  .quick-buttons {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 16px 20px;
  }
  
  .quick-btn {
    padding: 10px 14px;
    font-size: 13px;
  }
  
  .panel-header {
    padding: 16px 20px 12px;
    font-size: 14px;
  }
  
  .settings-content {
    padding: 16px 20px;
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .sidebar {
    padding: 10px;
  }
  
  .sidebar-content {
    width: 100%;
    margin: 0;
    border-radius: 16px;
  }
  
  .message-content {
    max-width: 90%;
  }
}
</style>