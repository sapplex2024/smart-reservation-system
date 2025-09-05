import { ref, computed } from 'vue'
import { useSettings } from './useSettings'

export interface CloudSpeechConfig {
  provider: 'xunfei' | 'baidu' | 'tencent'
  appId?: string
  apiKey?: string
  apiSecret?: string
  wsUrl?: string
}

export interface VoiceMessage {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: number
  audioUrl?: string
}

export function useCloudSpeech() {
  const { settings } = useSettings()
  
  const isConnected = ref(false)
  const isRecording = ref(false)
  const isPlaying = ref(false)
  const error = ref<string | null>(null)
  const transcript = ref('')
  const messages = ref<VoiceMessage[]>([])
  
  let websocket: WebSocket | null = null
  let mediaRecorder: MediaRecorder | null = null
  let audioChunks: Blob[] = []
  
  // 当前配置
  const config = computed<CloudSpeechConfig>(() => ({
    provider: (settings as any).voice?.provider || 'xunfei',
    appId: (settings as any).voice?.xunfei?.appId || '',
    apiKey: (settings as any).voice?.xunfei?.apiKey || '',
    apiSecret: (settings as any).voice?.xunfei?.apiSecret || '',
    wsUrl: 'ws://localhost:8000/api/voice/chat'
  }))
  
  // 连接WebSocket
  const connect = async () => {
    try {
      if (websocket?.readyState === WebSocket.OPEN) {
        return true
      }
      
      websocket = new WebSocket(config.value.wsUrl!)
      
      websocket.onopen = () => {
        isConnected.value = true
        error.value = null
        console.log('语音聊天WebSocket连接成功')
      }
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleWebSocketMessage(data)
        } catch (err) {
          console.error('解析WebSocket消息失败:', err)
        }
      }
      
      websocket.onerror = (event) => {
        error.value = '语音服务连接错误'
        console.error('WebSocket错误:', event)
      }
      
      websocket.onclose = () => {
        isConnected.value = false
        console.log('语音聊天WebSocket连接关闭')
      }
      
      return true
    } catch (err) {
      error.value = '连接语音服务失败'
      console.error('连接WebSocket失败:', err)
      return false
    }
  }
  
  // 处理WebSocket消息
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'transcript':
        transcript.value = data.text
        break
        
      case 'final_transcript':
        if (data.text) {
          addMessage('user', data.text)
          transcript.value = ''
        }
        break
        
      case 'ai_response':
        if (data.text) {
          addMessage('assistant', data.text)
        }
        break
        
      case 'audio_response':
        if (data.audio_url) {
          playAudio(data.audio_url)
        }
        break
        
      case 'error':
        error.value = data.message || '语音处理错误'
        break
        
      default:
        console.log('未知消息类型:', data.type)
    }
  }
  
  // 添加消息
  const addMessage = (type: 'user' | 'assistant', content: string, audioUrl?: string) => {
    const message: VoiceMessage = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: Date.now(),
      audioUrl
    }
    messages.value.push(message)
  }
  
  // 开始录音
  const startRecording = async () => {
    try {
      if (!isConnected.value && !(await connect())) {
        return false
      }
      
      // 发送开始录音信号
      if (websocket?.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          type: 'start_recording',
          config: {
            provider: config.value.provider,
            appId: config.value.appId,
            apiKey: config.value.apiKey,
            apiSecret: config.value.apiSecret
          }
        }))
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      })
      
      // 尝试使用WAV格式，如果不支持则使用WebM
      let mimeType = 'audio/wav'
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm;codecs=opus'
      }
      
      mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType
      })
      
      audioChunks = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
          console.log(`音频数据块: ${event.data.size}字节`)
        }
      }
      
      mediaRecorder.onstart = () => {
        isRecording.value = true
        error.value = null
      }
      
      mediaRecorder.onstop = async () => {
        isRecording.value = false
        // 停止所有音轨
        stream.getTracks().forEach(track => track.stop())
        
        // 合并所有音频数据块并发送
        if (audioChunks.length > 0 && websocket?.readyState === WebSocket.OPEN) {
          try {
            const audioBlob = new Blob(audioChunks, { type: mimeType })
            console.log(`发送完整音频: ${audioBlob.size}字节, 格式: ${mimeType}`)
            
            const reader = new FileReader()
            reader.onload = () => {
              const arrayBuffer = reader.result as ArrayBuffer
              const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)))
              websocket!.send(JSON.stringify({
                type: 'audio_complete',
                audio_data: base64,
                format: mimeType.includes('wav') ? 'wav' : 'webm'
              }))
            }
            reader.readAsArrayBuffer(audioBlob)
          } catch (err) {
            console.error('发送音频数据失败:', err)
          }
        }
      }
      
      mediaRecorder.start(1000) // 每1000ms发送一次数据，确保数据块足够大
      return true
      
    } catch (err) {
      error.value = '启动录音失败，请检查麦克风权限'
      console.error('录音失败:', err)
      return false
    }
  }
  
  // 停止录音
  const stopRecording = () => {
    if (mediaRecorder && isRecording.value) {
      mediaRecorder.stop()
      
      // 发送录音结束信号
      if (websocket?.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          type: 'stop_recording'
        }))
      }
    }
  }
  
  // 播放音频
  const playAudio = async (audioUrl: string) => {
    try {
      isPlaying.value = true
      const audio = new Audio(audioUrl)
      
      audio.onended = () => {
        isPlaying.value = false
      }
      
      audio.onerror = () => {
        isPlaying.value = false
        error.value = '音频播放失败'
      }
      
      await audio.play()
    } catch (err) {
      isPlaying.value = false
      error.value = '音频播放失败'
      console.error('播放音频失败:', err)
    }
  }
  
  // 发送文本消息
  const sendTextMessage = (text: string) => {
    if (!text.trim()) return
    
    addMessage('user', text)
    
    if (websocket?.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'text_message',
        text: text.trim()
      }))
    } else {
      error.value = '语音服务未连接'
    }
  }
  
  // 清空消息
  const clearMessages = () => {
    messages.value = []
  }
  
  // 断开连接
  const disconnect = () => {
    if (websocket) {
      websocket.close()
      websocket = null
    }
    
    if (mediaRecorder && isRecording.value) {
      stopRecording()
    }
    
    isConnected.value = false
    isRecording.value = false
    isPlaying.value = false
  }
  
  return {
    // 状态
    isConnected,
    isRecording,
    isPlaying,
    error,
    transcript,
    messages,
    config,
    
    // 方法
    connect,
    disconnect,
    startRecording,
    stopRecording,
    sendTextMessage,
    clearMessages,
    playAudio
  }
}