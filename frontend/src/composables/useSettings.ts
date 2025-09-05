import { ref, reactive } from 'vue'
import { useAuthStore } from '@/stores/auth'

// 设置数据接口
export interface SystemSettings {
  general: {
    site_name: string
    site_description: string
    timezone: string
    language: string
    theme: string
    logo_url: string
    contact_email: string
    contact_phone: string
  }
  appointment: {
    max_advance_days: number
    min_advance_hours: number
    max_duration_hours: number
    default_duration_minutes: number
    auto_approve: boolean
    allow_cancellation: boolean
    cancellation_deadline_hours: number
    working_hours_start: string
    working_hours_end: string
    working_days: string[]
    break_time_start: string
    break_time_end: string
  }
  notification: {
    email_enabled: boolean
    sms_enabled: boolean
    push_enabled: boolean
    reminder_hours_before: number
    admin_notifications: boolean
    user_notifications: boolean
    notification_templates: {
      appointment_confirmed: string
      appointment_cancelled: string
      appointment_reminder: string
    }
  }
  ai: {
    provider: string
    api_key: string
    model: string
    temperature: number
    max_tokens: number
    voice_enabled: boolean
    voice_provider: string
    voice_model: string
    auto_response: boolean
    response_delay_ms: number
  }
  security: {
    session_timeout_minutes: number
    max_login_attempts: number
    password_min_length: number
    password_require_uppercase: boolean
    password_require_lowercase: boolean
    password_require_numbers: boolean
    password_require_symbols: boolean
    two_factor_enabled: boolean
    ip_whitelist: string[]
    rate_limit_requests: number
    rate_limit_window_minutes: number
  }
}

export interface SystemInfo {
  version: string
  uptime: string
  total_users: number
  total_appointments: number
  active_sessions: number
  memory_usage: {
    used: number
    total: number
    percentage: number
  }
  disk_usage: {
    used: number
    total: number
    percentage: number
  }
  database_size: number
  last_backup: string
}

export function useSettings() {
  const authStore = useAuthStore()
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  const settings = reactive<SystemSettings>({
    general: {
      site_name: '智能预约系统',
      site_description: '基于AI的智能预约管理平台',
      timezone: 'Asia/Shanghai',
      language: 'zh-CN',
      theme: 'light',
      logo_url: '',
      contact_email: 'admin@example.com',
      contact_phone: '400-000-0000'
    },
    appointment: {
      max_advance_days: 30,
      min_advance_hours: 2,
      max_duration_hours: 8,
      default_duration_minutes: 60,
      auto_approve: false,
      allow_cancellation: true,
      cancellation_deadline_hours: 24,
      working_hours_start: '09:00',
      working_hours_end: '18:00',
      working_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
      break_time_start: '12:00',
      break_time_end: '13:00'
    },
    notification: {
      email_enabled: true,
      sms_enabled: false,
      push_enabled: true,
      reminder_hours_before: 24,
      admin_notifications: true,
      user_notifications: true,
      notification_templates: {
        appointment_confirmed: '您的预约已确认，时间：{datetime}',
        appointment_cancelled: '您的预约已取消，时间：{datetime}',
        appointment_reminder: '提醒：您有预约即将开始，时间：{datetime}'
      }
    },
    ai: {
      provider: 'xunfei',
      api_key: '',
      model: 'qwen-turbo',
      temperature: 0.7,
      max_tokens: 2000,
      voice_enabled: true,
      voice_provider: 'aliyun',
      voice_model: 'sambert-zhichu-v1',
      auto_response: true,
      response_delay_ms: 1000
    },
    security: {
      session_timeout_minutes: 480,
      max_login_attempts: 5,
      password_min_length: 8,
      password_require_uppercase: true,
      password_require_lowercase: true,
      password_require_numbers: true,
      password_require_symbols: false,
      two_factor_enabled: false,
      ip_whitelist: [],
      rate_limit_requests: 100,
      rate_limit_window_minutes: 15
    }
  })

  const systemInfo = ref<SystemInfo>({
    version: '1.0.0',
    uptime: '0天0小时0分钟',
    total_users: 0,
    total_appointments: 0,
    active_sessions: 0,
    memory_usage: {
      used: 0,
      total: 0,
      percentage: 0
    },
    disk_usage: {
      used: 0,
      total: 0,
      percentage: 0
    },
    database_size: 0,
    last_backup: '从未备份'
  })

  // 获取所有设置
  const getSettings = async () => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch('/api/settings/', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('获取设置失败')
      }
      
      const data = await response.json()
      Object.assign(settings, data)
      
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取设置失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取特定类别的设置
  const getCategorySettings = async (category: string) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch(`/api/settings/${category}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error(`获取${category}设置失败`)
      }
      
      const data = await response.json()
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取设置失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 更新设置
  const updateSettings = async (category: string, newSettings: any) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch(`/api/settings/${category}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify(newSettings)
      })
      
      if (!response.ok) {
        throw new Error('更新设置失败')
      }
      
      const data = await response.json()
      
      // 更新本地设置
      if (settings[category as keyof SystemSettings]) {
        Object.assign(settings[category as keyof SystemSettings], newSettings)
      }
      
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新设置失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 重置设置
  const resetSettings = async (category: string) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch(`/api/settings/${category}/reset`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('重置设置失败')
      }
      
      const data = await response.json()
      
      // 更新本地设置
      if (settings[category as keyof SystemSettings]) {
        Object.assign(settings[category as keyof SystemSettings], data)
      }
      
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '重置设置失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 导出设置
  const exportSettings = async () => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch('/api/settings/export', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('导出设置失败')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `settings_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      
    } catch (err) {
      error.value = err instanceof Error ? err.message : '导出设置失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 导入设置
  const importSettings = async (file: File) => {
    try {
      loading.value = true
      error.value = null
      
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/settings/import', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        },
        body: formData
      })
      
      if (!response.ok) {
        throw new Error('导入设置失败')
      }
      
      const data = await response.json()
      Object.assign(settings, data)
      
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '导入设置失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 验证设置
  const validateSettings = async (category: string, settingsData: any) => {
    try {
      const response = await fetch(`/api/settings/${category}/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authStore.token}`
        },
        body: JSON.stringify(settingsData)
      })
      
      if (!response.ok) {
        throw new Error('验证设置失败')
      }
      
      const data = await response.json()
      return data
    } catch (err) {
      throw err
    }
  }

  // 获取系统信息
  const getSystemInfo = async () => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch('/api/settings/system-info', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('获取系统信息失败')
      }
      
      const data = await response.json()
      systemInfo.value = data
      
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '获取系统信息失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 获取公共设置（无需认证）
  const getPublicSettings = async () => {
    try {
      const response = await fetch('/api/settings/public')
      
      if (!response.ok) {
        throw new Error('获取公共设置失败')
      }
      
      const data = await response.json()
      return data
    } catch (err) {
      throw err
    }
  }

  // 清理缓存
  const clearCache = async () => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch('/api/settings/clear-cache', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('清理缓存失败')
      }
      
      return await response.json()
    } catch (err) {
      error.value = err instanceof Error ? err.message : '清理缓存失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  // 导出日志
  const exportLogs = async () => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch('/api/settings/export-logs', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('导出日志失败')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `logs_${new Date().toISOString().split('T')[0]}.zip`
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

  return {
    settings,
    systemInfo,
    loading,
    error,
    getSettings,
    getCategorySettings,
    updateSettings,
    resetSettings,
    exportSettings,
    importSettings,
    validateSettings,
    getSystemInfo,
    getPublicSettings,
    clearCache,
    exportLogs
  }
}