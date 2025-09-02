import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 阿里云语音服务接口
export interface CloudVoice {
  id: string
  name: string
  gender: 'male' | 'female'
  language: string
  provider?: string
  model?: string
  full_id?: string
}

export interface VoiceProvider {
  id: string
  name: string
  description: string
  available: boolean
}

export function useCloudSpeech() {
  const isListening = ref(false)
  const isSpeaking = ref(false)
  const isSupported = ref(true)
  const transcript = ref('')
  const availableVoices = ref<CloudVoice[]>([])
  const selectedVoice = ref('zhixiaoxia')
  const availableProviders = ref<VoiceProvider[]>([])
  const selectedProvider = ref('qwen')
  const selectedModel = ref('')
  
  let mediaRecorder: MediaRecorder | null = null
  let audioChunks: Blob[] = []
  let currentAudio: HTMLAudioElement | null = null
  
  const API_BASE_URL = 'http://localhost:8000/api/voice'
  
  // 加载语音提供商列表
  const loadProviders = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/providers`)
      availableProviders.value = response.data.providers || []
      
      // 选择第一个可用的提供商
      const availableProvider = availableProviders.value.find(p => p.available)
      if (availableProvider && !availableProviders.value.find(p => p.id === selectedProvider.value && p.available)) {
        selectedProvider.value = availableProvider.id
      }
      
    } catch (error) {
      console.error('加载语音提供商失败:', error)
      ElMessage.error('加载语音提供商失败，请检查后端服务是否启动')
    }
  }
  
  // 加载可用语音列表
  const loadVoices = async (provider?: string) => {
    try {
      const targetProvider = provider || selectedProvider.value
      const response = await axios.get(`${API_BASE_URL}/voices`, {
        params: targetProvider ? { provider: targetProvider } : {}
      })
      availableVoices.value = response.data.voices || []
      
      // 如果当前选择的语音不在列表中，选择第一个可用的
      if (availableVoices.value.length > 0 && 
          !availableVoices.value.find(v => v.id === selectedVoice.value)) {
        selectedVoice.value = availableVoices.value[0].id
      }
      
      // 设置默认模型（硅基流动）
      if (targetProvider === 'siliconflow' && availableVoices.value.length > 0) {
        const firstVoice = availableVoices.value[0]
        if (firstVoice.model && !selectedModel.value) {
          selectedModel.value = firstVoice.model
        }
      }
      
    } catch (error) {
      console.error('加载语音列表失败:', error)
      ElMessage.error('加载语音列表失败，请检查后端服务是否启动')
    }
  }
  
  // 测试API连接
  const testConnection = async (provider?: string) => {
    try {
      const targetProvider = provider || selectedProvider.value
      const response = await axios.post(`${API_BASE_URL}/test-connection`, {
        provider: targetProvider
      })
      
      if (response.data.success) {
        ElMessage.success(`${targetProvider === 'siliconflow' ? '硅基流动' : '通义千问'}API连接成功`)
      } else {
        ElMessage.error(response.data.message || 'API连接失败')
      }
      
      return response.data.success
    } catch (error) {
      console.error('API连接测试失败:', error)
      ElMessage.error('API连接测试失败，请检查后端服务是否启动')
      return false
    }
  }
  
  // 开始录音
  const startListening = async () => {
    if (isListening.value) {
      stopListening()
      return
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      audioChunks = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
        await processAudioForASR(audioBlob)
        
        // 停止所有音轨
        stream.getTracks().forEach(track => track.stop())
      }
      
      mediaRecorder.start()
      isListening.value = true
      transcript.value = '正在录音...'
      
    } catch (error) {
      console.error('启动录音失败:', error)
      ElMessage.error('无法访问麦克风，请检查权限设置')
    }
  }
  
  // 停止录音
  const stopListening = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop()
    }
    isListening.value = false
  }
  
  // 处理音频进行语音识别
  const processAudioForASR = async (audioBlob: Blob) => {
    try {
      transcript.value = '正在识别...'
      
      const formData = new FormData()
      formData.append('audio', audioBlob, 'recording.webm')
      
      const response = await axios.post(`${API_BASE_URL}/asr`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 30000 // 30秒超时
      })
      
      if (response.data.success && response.data.text) {
        transcript.value = response.data.text
        ElMessage.success('语音识别成功')
      } else {
        transcript.value = '识别失败'
        ElMessage.error('语音识别失败')
      }
      
    } catch (error) {
      console.error('语音识别失败:', error)
      transcript.value = '识别失败'
      
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          ElMessage.error('语音识别超时，请重试')
        } else if (error.response?.status === 500) {
          ElMessage.error('语音识别服务暂时不可用，请稍后重试')
        } else {
          ElMessage.error('语音识别失败，请重试')
        }
      } else {
        ElMessage.error('语音识别失败，请重试')
      }
    }
  }
  
  // 文本转语音
  const speak = async (text: string, voice?: string, provider?: string, model?: string) => {
    if (!text.trim()) {
      ElMessage.warning('文本内容不能为空')
      return
    }
    
    try {
      // 停止当前播放
      stopSpeaking()
      
      isSpeaking.value = true
      
      const targetProvider = provider || selectedProvider.value
      const targetVoice = voice || selectedVoice.value
      const targetModel = model || selectedModel.value
      
      const requestData: any = {
        text: text.trim(),
        voice: targetVoice,
        provider: targetProvider
      }
      
      // 硅基流动需要模型参数
      if (targetProvider === 'siliconflow' && targetModel) {
        requestData.model = targetModel
      }
      
      const response = await axios.post(`${API_BASE_URL}/tts`, requestData, {
        responseType: 'blob',
        timeout: 30000 // 30秒超时
      })
      
      // 创建音频URL并播放
      const audioUrl = URL.createObjectURL(response.data)
      currentAudio = new Audio(audioUrl)
      
      currentAudio.onended = () => {
        isSpeaking.value = false
        URL.revokeObjectURL(audioUrl)
        currentAudio = null
      }
      
      currentAudio.onerror = () => {
        isSpeaking.value = false
        URL.revokeObjectURL(audioUrl)
        currentAudio = null
        ElMessage.error('音频播放失败')
      }
      
      await currentAudio.play()
      
    } catch (error) {
      console.error('语音合成失败:', error)
      isSpeaking.value = false
      
      if (axios.isAxiosError(error)) {
        if (error.code === 'ECONNABORTED') {
          ElMessage.error('语音合成超时，请重试')
        } else if (error.response?.status === 500) {
          ElMessage.error('语音合成服务暂时不可用，请稍后重试')
        } else {
          ElMessage.error('语音合成失败，请重试')
        }
      } else {
        ElMessage.error('语音合成失败，请重试')
      }
    }
  }
  
  // 停止语音播放
  const stopSpeaking = () => {
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.currentTime = 0
      currentAudio = null
    }
    isSpeaking.value = false
  }
  
  // 切换录音状态
  const toggleListening = () => {
    if (isListening.value) {
      stopListening()
    } else {
      startListening()
    }
  }
  
  // 切换播放状态
  const toggleSpeaking = (text: string) => {
    if (isSpeaking.value) {
      stopSpeaking()
    } else {
      speak(text)
    }
  }
  
  // 获取中文语音列表
  const getChineseVoices = computed(() => {
    return availableVoices.value.filter(voice => 
      voice.language.includes('zh')
    )
  })
  
  // 切换语音提供商
  const switchProvider = async (providerId: string) => {
    selectedProvider.value = providerId
    selectedModel.value = '' // 重置模型选择
    await loadVoices(providerId)
  }
  
  // 获取当前提供商的可用模型
  const getAvailableModels = computed(() => {
    if (selectedProvider.value === 'siliconflow') {
      const models = [...new Set(availableVoices.value.map(v => v.model).filter(Boolean))]
      return models.map(model => ({
        id: model,
        name: model?.split('/').pop() || model
      }))
    }
    return []
  })
  
  // 初始化
  const init = async () => {
    await loadProviders()
    await loadVoices()
    return await testConnection()
  }
  
  return {
    isListening,
    isSpeaking,
    isSupported,
    transcript,
    availableVoices,
    selectedVoice,
    availableProviders,
    selectedProvider,
    selectedModel,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    toggleListening,
    toggleSpeaking,
    getChineseVoices,
    getAvailableModels,
    loadVoices,
    loadProviders,
    switchProvider,
    testConnection,
    init
  }
}