import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

export interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
  resultIndex: number
}

export interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message: string
}

export interface SpeechRecognition extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  start(): void
  stop(): void
  abort(): void
  addEventListener(type: 'result', listener: (event: SpeechRecognitionEvent) => void): void
  addEventListener(type: 'error', listener: (event: SpeechRecognitionErrorEvent) => void): void
  addEventListener(type: 'start', listener: () => void): void
  addEventListener(type: 'end', listener: () => void): void
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition
    webkitSpeechRecognition: new () => SpeechRecognition
  }
}

export function useSpeech() {
  const isListening = ref(false)
  const isSpeaking = ref(false)
  const isSupported = ref(false)
  const transcript = ref('')
  
  let recognition: SpeechRecognition | null = null
  let synthesis: SpeechSynthesis | null = null
  
  // 检查浏览器支持
  const checkSupport = () => {
    const speechRecognitionSupported = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window
    const speechSynthesisSupported = 'speechSynthesis' in window
    isSupported.value = speechRecognitionSupported && speechSynthesisSupported
    return isSupported.value
  }
  
  // 初始化语音识别
  const initSpeechRecognition = () => {
    if (!checkSupport()) {
      ElMessage.warning('您的浏览器不支持语音功能，请使用Chrome或Edge浏览器')
      return false
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    recognition = new SpeechRecognition()
    
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'zh-CN'
    
    recognition.addEventListener('start', () => {
      isListening.value = true
      transcript.value = ''
    })
    
    recognition.addEventListener('result', (event: SpeechRecognitionEvent) => {
      let finalTranscript = ''
      let interimTranscript = ''
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalTranscript += result[0].transcript
        } else {
          interimTranscript += result[0].transcript
        }
      }
      
      transcript.value = finalTranscript || interimTranscript
    })
    
    recognition.addEventListener('end', () => {
      isListening.value = false
    })
    
    recognition.addEventListener('error', (event: SpeechRecognitionErrorEvent) => {
      isListening.value = false
      console.error('语音识别错误:', event.error)
      
      switch (event.error) {
        case 'no-speech':
          ElMessage.warning('没有检测到语音，请重试')
          break
        case 'audio-capture':
          ElMessage.error('无法访问麦克风，请检查权限设置')
          break
        case 'not-allowed':
          ElMessage.error('麦克风权限被拒绝，请在浏览器设置中允许麦克风访问')
          break
        case 'network':
          ElMessage.error('网络错误，请检查网络连接')
          break
        case 'aborted':
          // 用户主动停止，不显示错误消息
          break
        default:
          ElMessage.error(`语音识别错误: ${event.error}`)
      }
    })
    
    synthesis = window.speechSynthesis
    return true
  }
  
  // 开始语音识别
  const startListening = () => {
    if (!recognition && !initSpeechRecognition()) {
      return
    }
    
    if (isListening.value) {
      return
    }
    
    try {
      recognition?.start()
    } catch (error) {
      console.error('启动语音识别失败:', error)
      ElMessage.error('启动语音识别失败，请重试')
    }
  }
  
  // 停止语音识别
  const stopListening = () => {
    if (recognition) {
      try {
        recognition.stop()
        recognition.abort() // 强制停止
      } catch (error) {
        console.error('停止语音识别失败:', error)
      }
      isListening.value = false
    }
  }
  
  // 语音合成
  const speak = (text: string, options?: {
    rate?: number
    pitch?: number
    volume?: number
    voice?: SpeechSynthesisVoice
  }) => {
    if (!synthesis) {
      ElMessage.warning('语音合成功能不可用')
      return
    }
    
    // 停止当前播放
    synthesis.cancel()
    
    const utterance = new SpeechSynthesisUtterance(text)
    
    // 设置语音参数
    utterance.rate = options?.rate || 1
    utterance.pitch = options?.pitch || 1
    utterance.volume = options?.volume || 1
    utterance.lang = 'zh-CN'
    
    // 如果指定了语音，使用指定的语音
    if (options?.voice) {
      utterance.voice = options.voice
    } else {
      // 尝试使用中文语音
      const voices = synthesis.getVoices()
      const chineseVoice = voices.find(voice => 
        voice.lang.includes('zh') || voice.name.includes('Chinese')
      )
      if (chineseVoice) {
        utterance.voice = chineseVoice
      }
    }
    
    utterance.addEventListener('start', () => {
      isSpeaking.value = true
    })
    
    utterance.addEventListener('end', () => {
      isSpeaking.value = false
    })
    
    utterance.addEventListener('error', (event) => {
      isSpeaking.value = false
      console.error('语音合成错误:', event.error)
      ElMessage.error('语音播放失败')
    })
    
    synthesis.speak(utterance)
  }
  
  // 停止语音播放
  const stopSpeaking = () => {
    if (synthesis) {
      synthesis.cancel()
      isSpeaking.value = false
    }
  }
  
  // 获取可用的语音列表
  const getVoices = (): SpeechSynthesisVoice[] => {
    return synthesis?.getVoices() || []
  }
  
  // 获取中文语音列表
  const getChineseVoices = computed(() => {
    return getVoices().filter(voice => 
      voice.lang.includes('zh') || voice.name.includes('Chinese')
    )
  })
  
  return {
    isListening,
    isSpeaking,
    isSupported,
    transcript,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    getVoices,
    getChineseVoices,
    initSpeechRecognition
  }
}