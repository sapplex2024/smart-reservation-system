import { ref, onUnmounted } from 'vue'

export interface SpeechRecognitionResult {
  transcript: string
  confidence: number
  isFinal: boolean
}

export interface SpeechSynthesisOptions {
  text: string
  voice?: string
  rate?: number
  pitch?: number
  volume?: number
}

export function useSpeech() {
  const isListening = ref(false)
  const isSpeaking = ref(false)
  const isSupported = ref(false)
  const transcript = ref('')
  const error = ref<string | null>(null)

  let recognition: any = null
  let synthesis: SpeechSynthesis | null = null
  let currentUtterance: SpeechSynthesisUtterance | null = null

  // 检查浏览器支持
  const checkSupport = () => {
    const hasRecognition = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window
    const hasSynthesis = 'speechSynthesis' in window
    isSupported.value = hasRecognition && hasSynthesis
    return isSupported.value
  }

  // 初始化语音识别
  const initRecognition = () => {
    if (!checkSupport()) {
      error.value = '浏览器不支持语音识别功能'
      return false
    }

    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    recognition = new SpeechRecognition()
    
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'zh-CN'

    recognition.onstart = () => {
      isListening.value = true
      error.value = null
    }

    recognition.onresult = (event: any) => {
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
    }

    recognition.onerror = (event: any) => {
      error.value = `语音识别错误: ${event.error}`
      isListening.value = false
    }

    recognition.onend = () => {
      isListening.value = false
    }

    return true
  }

  // 初始化语音合成
  const initSynthesis = () => {
    if ('speechSynthesis' in window) {
      synthesis = window.speechSynthesis
      return true
    }
    return false
  }

  // 开始语音识别
  const startListening = () => {
    if (!recognition && !initRecognition()) {
      return false
    }

    try {
      transcript.value = ''
      recognition.start()
      return true
    } catch (err) {
      error.value = '启动语音识别失败'
      return false
    }
  }

  // 停止语音识别
  const stopListening = () => {
    if (recognition && isListening.value) {
      recognition.stop()
    }
  }

  // 语音合成
  const speak = (options: SpeechSynthesisOptions) => {
    if (!synthesis && !initSynthesis()) {
      error.value = '浏览器不支持语音合成功能'
      return false
    }

    // 停止当前播放
    if (currentUtterance) {
      synthesis!.cancel()
    }

    currentUtterance = new SpeechSynthesisUtterance(options.text)
    
    // 设置语音参数
    currentUtterance.lang = 'zh-CN'
    currentUtterance.rate = options.rate || 1
    currentUtterance.pitch = options.pitch || 1
    currentUtterance.volume = options.volume || 1

    // 如果指定了语音，尝试使用
    if (options.voice) {
      const voices = synthesis!.getVoices()
      const selectedVoice = voices.find(voice => 
        voice.name.includes(options.voice!) || voice.lang.includes('zh')
      )
      if (selectedVoice) {
        currentUtterance.voice = selectedVoice
      }
    }

    currentUtterance.onstart = () => {
      isSpeaking.value = true
    }

    currentUtterance.onend = () => {
      isSpeaking.value = false
      currentUtterance = null
    }

    currentUtterance.onerror = (event) => {
      error.value = `语音合成错误: ${event.error}`
      isSpeaking.value = false
      currentUtterance = null
    }

    synthesis!.speak(currentUtterance)
    return true
  }

  // 停止语音合成
  const stopSpeaking = () => {
    if (synthesis && isSpeaking.value) {
      synthesis.cancel()
      isSpeaking.value = false
      currentUtterance = null
    }
  }

  // 获取可用语音列表
  const getVoices = () => {
    if (!synthesis && !initSynthesis()) {
      return []
    }
    return synthesis!.getVoices().filter(voice => voice.lang.includes('zh'))
  }

  // 清理资源
  const cleanup = () => {
    stopListening()
    stopSpeaking()
    recognition = null
    synthesis = null
    currentUtterance = null
  }

  // 组件卸载时清理
  onUnmounted(() => {
    cleanup()
  })

  // 初始化
  checkSupport()

  return {
    // 状态
    isListening,
    isSpeaking,
    isSupported,
    transcript,
    error,
    
    // 方法
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    getVoices,
    cleanup
  }
}