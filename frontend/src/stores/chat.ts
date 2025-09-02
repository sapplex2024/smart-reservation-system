import { defineStore } from 'pinia'
import axios from 'axios'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface ChatResponse {
  response: string
  session_id: string
  intent?: string
  entities?: any
  suggestions?: string[]
  reservation_created?: boolean
  audio_url?: string
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as ChatMessage[],
    isLoading: false,
    sessionId: null as string | null
  }),

  actions: {
    async sendMessage(
      content: string, 
      options?: {
        voiceEnabled?: boolean
        voiceProvider?: string
        voiceModel?: string
      }
    ): Promise<ChatResponse> {
      this.isLoading = true
      
      try {
        const response = await axios.post('/api/chat/', {
          message: content,
          session_id: this.sessionId,
          voice_enabled: options?.voiceEnabled || false,
          voice_provider: options?.voiceProvider || 'qwen',
          voice_model: options?.voiceModel
        })
        
        if (response.data.session_id && !this.sessionId) {
          this.sessionId = response.data.session_id
        }
        
        return response.data
      } catch (error) {
        console.error('Chat API error:', error)
        throw new Error('发送消息失败')
      } finally {
        this.isLoading = false
      }
    },

    async getChatHistory(): Promise<ChatMessage[]> {
      if (!this.sessionId) return []
      
      try {
        const response = await axios.get(`/api/chat/history/${this.sessionId}`)
        this.messages = response.data.messages || []
        return this.messages
      } catch (error) {
        console.error('Get chat history error:', error)
        return []
      }
    },

    clearChat() {
      this.messages = []
      this.sessionId = null
    }
  }
})