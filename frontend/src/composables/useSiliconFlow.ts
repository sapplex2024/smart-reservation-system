import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

// 模型信息接口
export interface ModelInfo {
  id: string
  name: string
  description: string
  provider: string
  type: string
  max_tokens: number
  pricing?: {
    input: number
    output: number
  }
}

// API测试请求接口
export interface APITestRequest {
  api_key: string
  base_url: string
  model: string
  message?: string
  max_tokens?: number
  temperature?: number
}

// API测试响应接口
export interface APITestResponse {
  success: boolean
  response?: string
  error?: string
  latency?: number
  tokens_used?: number
}

// 硅基流动配置接口
export interface SiliconFlowConfig {
  api_key: string
  base_url: string
  default_model: string
  max_tokens: string
  temperature: string
  stream: string
}

// API使用统计接口
export interface APIUsage {
  total_requests: number
  total_tokens: number
  total_cost: number
  today_requests: number
  today_tokens: number
  today_cost: number
  popular_models: Array<{
    model: string
    requests: number
    percentage: number
  }>
}

export function useSiliconFlow() {
  const authStore = useAuthStore()
  
  // 获取认证头
  const getAuthHeaders = () => {
    return {
      'Authorization': `Bearer ${authStore.token}`,
      'Content-Type': 'application/json'
    }
  }
  
  const models = ref<ModelInfo[]>([])
  const config = ref<SiliconFlowConfig>({
    api_key: '',
    base_url: 'https://api.siliconflow.cn/v1',
    default_model: 'Qwen/Qwen2.5-72B-Instruct',
    max_tokens: '4096',
    temperature: '0.7',
    stream: 'true'
  })
  const usage = ref<APIUsage | null>(null)
  const loading = ref(false)
  const testResult = ref<APITestResponse | null>(null)
  
  // 获取可用模型列表
  const fetchModels = async () => {
    try {
      loading.value = true
      const response = await fetch('/api/siliconflow/models', {
        headers: getAuthHeaders()
      })
      
      if (response.ok) {
        models.value = await response.json()
      } else {
        throw new Error('获取模型列表失败')
      }
    } catch (error) {
      console.error('获取模型列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 获取配置
  const fetchConfig = async () => {
    try {
      loading.value = true
      const response = await fetch('/api/siliconflow/config', {
        headers: getAuthHeaders()
      })
      
      if (response.ok) {
        config.value = await response.json()
      } else {
        throw new Error('获取配置失败')
      }
    } catch (error) {
      console.error('获取配置失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 更新配置
  const updateConfig = async (newConfig: Partial<SiliconFlowConfig>) => {
    try {
      loading.value = true
      const response = await fetch('/api/siliconflow/config', {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newConfig)
      })
      
      if (response.ok) {
        // 更新本地配置
        Object.assign(config.value, newConfig)
        return await response.json()
      } else {
        const error = await response.json()
        throw new Error(error.detail || '更新配置失败')
      }
    } catch (error) {
      console.error('更新配置失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 测试API连接
  const testAPIConnection = async (testRequest: APITestRequest) => {
    try {
      loading.value = true
      testResult.value = null
      
      const response = await fetch('/api/siliconflow/test', {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(testRequest)
      })
      
      if (response.ok) {
        testResult.value = await response.json()
        return testResult.value
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'API测试失败')
      }
    } catch (error) {
      console.error('API测试失败:', error)
      testResult.value = {
        success: false,
        error: error instanceof Error ? error.message : '未知错误'
      }
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 获取使用统计
  const fetchUsage = async () => {
    try {
      loading.value = true
      const response = await fetch('/api/siliconflow/usage', {
        headers: getAuthHeaders()
      })
      
      if (response.ok) {
        usage.value = await response.json()
      } else {
        throw new Error('获取使用统计失败')
      }
    } catch (error) {
      console.error('获取使用统计失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 格式化价格
  const formatPrice = (price: number) => {
    return `¥${price.toFixed(4)}/1K tokens`
  }
  
  // 格式化延迟
  const formatLatency = (latency: number) => {
    return `${(latency * 1000).toFixed(0)}ms`
  }
  
  // 获取模型提供商颜色
  const getProviderColor = (provider: string) => {
    const colors: Record<string, string> = {
      'Alibaba': 'orange',
      'DeepSeek': 'blue',
      'Meta': 'purple',
      'Microsoft': 'cyan',
      'THUDM': 'green'
    }
    return colors[provider] || 'gray'
  }
  
  // 获取模型类型图标
  const getModelTypeIcon = (type: string) => {
    const icons: Record<string, string> = {
      'chat': 'chatbubble-outline',
      'completion': 'document-text-outline',
      'embedding': 'layers-outline'
    }
    return icons[type] || 'help-outline'
  }
  
  return {
    // 响应式数据
    models,
    config,
    usage,
    loading,
    testResult,
    
    // 方法
    fetchModels,
    fetchConfig,
    updateConfig,
    testAPIConnection,
    fetchUsage,
    
    // 工具函数
    formatPrice,
    formatLatency,
    getProviderColor,
    getModelTypeIcon
  }
}