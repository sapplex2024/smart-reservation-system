import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

// 日志数据接口
export interface SystemLog {
  id: number
  level: string
  message: string
  category: string
  user_id?: number
  extra_data?: string
  created_at: string
}

export interface LogStats {
  total_logs: number
  level_stats: Record<string, number>
  category_stats: Record<string, number>
  recent_errors: number
}

export interface LogFilters {
  level?: string
  category?: string
  user_id?: number
  start_date?: string
  end_date?: string
}

export function useLogs() {
  const authStore = useAuthStore()
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  const logs = ref<SystemLog[]>([])
  const stats = ref<LogStats>({
    total_logs: 0,
    level_stats: {},
    category_stats: {},
    recent_errors: 0
  })
  
  const levels = ref<string[]>(['INFO', 'WARNING', 'ERROR', 'ACCESS', 'SECURITY', 'API'])
  const categories = ref<string[]>([])
  
  // 获取日志列表
  const getLogs = async (filters: LogFilters = {}, limit = 100, offset = 0) => {
    try {
      loading.value = true
      error.value = null
      
      const params = new URLSearchParams()
      if (filters.level) params.append('level', filters.level)
      if (filters.category) params.append('category', filters.category)
      if (filters.user_id) params.append('user_id', filters.user_id.toString())
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)
      params.append('limit', limit.toString())
      params.append('offset', offset.toString())
      
      const response = await fetch(`/api/logs/?${params.toString()}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('获取日志失败')
      }
      
      const data = await response.json()
      logs.value = data
      
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取日志失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 获取日志统计
  const getLogStats = async (start_date?: string, end_date?: string) => {
    try {
      loading.value = true
      error.value = null
      
      const params = new URLSearchParams()
      if (start_date) params.append('start_date', start_date)
      if (end_date) params.append('end_date', end_date)
      
      const response = await fetch(`/api/logs/stats/?${params.toString()}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('获取日志统计失败')
      }
      
      const data = await response.json()
      stats.value = data
      
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取日志统计失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 导出日志
  const exportLogs = async (format: 'json' | 'csv' = 'json', filters: LogFilters = {}) => {
    try {
      loading.value = true
      error.value = null
      
      const exportData = {
        format,
        start_date: filters.start_date || null,
        end_date: filters.end_date || null,
        level: filters.level || null,
        category: filters.category || null
      }
      
      const response = await fetch('/api/logs/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify(exportData)
      })
      
      if (!response.ok) {
        throw new Error('导出日志失败')
      }
      
      // 下载文件
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `logs_${new Date().toISOString().split('T')[0]}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : '导出日志失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 清理旧日志
  const cleanupOldLogs = async (daysToKeep = 30) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch(`/api/logs/cleanup?days_to_keep=${daysToKeep}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('清理日志失败')
      }
      
      const data = await response.json()
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '清理日志失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 获取日志级别
  const getLogLevels = async () => {
    try {
      const response = await fetch('/api/logs/levels/', {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('获取日志级别失败')
      }
      
      const data = await response.json()
      levels.value = data.levels
      
      return data.levels
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取日志级别失败'
      throw err
    }
  }
  
  // 获取日志类别
  const getLogCategories = async () => {
    try {
      const response = await fetch('/api/logs/categories/', {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('获取日志类别失败')
      }
      
      const data = await response.json()
      categories.value = data.categories
      
      return data.categories
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取日志类别失败'
      throw err
    }
  }
  
  // 获取最近错误
  const getRecentErrors = async (hours = 24) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch(`/api/logs/recent-errors?hours=${hours}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('获取最近错误失败')
      }
      
      const data = await response.json()
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取最近错误失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 格式化日志级别颜色
  const getLevelColor = (level: string) => {
    const colors = {
      'INFO': 'blue',
      'WARNING': 'orange',
      'ERROR': 'red',
      'ACCESS': 'green',
      'SECURITY': 'purple',
      'API': 'cyan'
    }
    return colors[level as keyof typeof colors] || 'gray'
  }
  
  // 格式化日志级别图标
  const getLevelIcon = (level: string) => {
    const icons = {
      'INFO': 'InfoFilled',
      'WARNING': 'Warning',
      'ERROR': 'CircleCloseFilled',
      'ACCESS': 'View',
      'SECURITY': 'Lock',
      'API': 'DocumentCopy'
    }
    return icons[level as keyof typeof icons] || 'QuestionFilled'
  }
  
  // 格式化时间
  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }
  
  // 解析额外数据
  const parseExtraData = (extraData: string | null) => {
    if (!extraData) return null
    try {
      return JSON.parse(extraData)
    } catch {
      return extraData
    }
  }
  
  return {
    logs,
    stats,
    levels,
    categories,
    loading,
    error,
    getLogs,
    getLogStats,
    exportLogs,
    cleanupOldLogs,
    getLogLevels,
    getLogCategories,
    getRecentErrors,
    getLevelColor,
    getLevelIcon,
    formatTime,
    parseExtraData
  }
}