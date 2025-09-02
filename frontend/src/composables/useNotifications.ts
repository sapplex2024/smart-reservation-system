import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

export interface Notification {
  id: number
  type: string
  title: string
  message: string
  data: any
  created_at: string
  read: boolean
}

export interface NotificationStats {
  total_count: number
  unread_count: number
  read_count: number
  type_stats: Record<string, { total: number; unread: number }>
}

export function useNotifications() {
  const authStore = useAuthStore()
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const stats = ref<NotificationStats | null>(null)
  
  // 轮询间隔（毫秒）
  const POLL_INTERVAL = 30000 // 30秒
  let pollTimer: number | null = null
  
  // 计算属性
  const unreadNotifications = computed(() => 
    notifications.value.filter(n => !n.read)
  )
  
  const readNotifications = computed(() => 
    notifications.value.filter(n => n.read)
  )
  
  // 获取通知列表
  const fetchNotifications = async (unreadOnly = false, limit = 20) => {
    if (!authStore.token) return
    
    try {
      loading.value = true
      const params = new URLSearchParams({
        unread_only: unreadOnly.toString(),
        limit: limit.toString()
      })
      
      const response = await fetch(`/api/notifications?${params}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      notifications.value = data
      
    } catch (error) {
      console.error('获取通知失败:', error)
      ElMessage.error('获取通知失败')
    } finally {
      loading.value = false
    }
  }
  
  // 获取未读通知数量
  const fetchUnreadCount = async () => {
    if (!authStore.token) return
    
    try {
      const response = await fetch('/api/notifications/unread-count', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      unreadCount.value = data.unread_count
      
    } catch (error) {
      console.error('获取未读数量失败:', error)
    }
  }
  
  // 标记通知为已读
  const markAsRead = async (notificationId: number) => {
    if (!authStore.token) return
    
    try {
      const response = await fetch(`/api/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // 更新本地状态
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
      
    } catch (error) {
      console.error('标记已读失败:', error)
      ElMessage.error('标记已读失败')
    }
  }
  
  // 标记所有通知为已读
  const markAllAsRead = async () => {
    if (!authStore.token) return
    
    try {
      const response = await fetch('/api/notifications/mark-all-read', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      // 更新本地状态
      notifications.value.forEach(n => n.read = true)
      unreadCount.value = 0
      
      ElMessage.success(data.message)
      
    } catch (error) {
      console.error('批量标记已读失败:', error)
      ElMessage.error('批量标记已读失败')
    }
  }
  
  // 获取通知统计
  const fetchStats = async () => {
    if (!authStore.token) return
    
    try {
      const response = await fetch('/api/notifications/stats', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      stats.value = data
      
    } catch (error) {
      console.error('获取统计信息失败:', error)
    }
  }
  
  // 创建测试通知
  const createTestNotification = async () => {
    if (!authStore.token) return
    
    try {
      const response = await fetch('/api/notifications/test', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      ElMessage.success(data.message)
      
      // 刷新通知列表
      await fetchNotifications()
      await fetchUnreadCount()
      
    } catch (error) {
      console.error('创建测试通知失败:', error)
      ElMessage.error('创建测试通知失败')
    }
  }
  
  // 显示桌面通知
  const showDesktopNotification = (notification: Notification) => {
    // 检查浏览器是否支持通知
    if (!('Notification' in window)) {
      return
    }
    
    // 检查通知权限
    if (Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        tag: `notification-${notification.id}`
      })
    } else if (Notification.permission !== 'denied') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          new Notification(notification.title, {
            body: notification.message,
            icon: '/favicon.ico',
            tag: `notification-${notification.id}`
          })
        }
      })
    }
  }
  
  // 显示应用内通知
  const showInAppNotification = (notification: Notification) => {
    const typeMap: Record<string, any> = {
      'status_change': 'info',
      'reminder': 'warning',
      'approval_request': 'success',
      'cancellation': 'error'
    }
    
    ElNotification({
      title: notification.title,
      message: notification.message,
      type: typeMap[notification.type] || 'info',
      duration: 5000,
      onClick: () => {
        markAsRead(notification.id)
      }
    })
  }
  
  // 格式化通知时间
  const formatNotificationTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (minutes < 1) {
      return '刚刚'
    } else if (minutes < 60) {
      return `${minutes}分钟前`
    } else if (hours < 24) {
      return `${hours}小时前`
    } else if (days < 7) {
      return `${days}天前`
    } else {
      return date.toLocaleDateString('zh-CN')
    }
  }
  
  // 开始轮询
  const startPolling = () => {
    if (pollTimer) return
    
    pollTimer = setInterval(async () => {
      await fetchUnreadCount()
      
      // 如果有新的未读通知，获取最新通知
      const currentUnreadCount = unreadCount.value
      if (currentUnreadCount > 0) {
        const latestNotifications = await fetchNotifications(true, 5)
        // 这里可以添加逻辑来检测新通知并显示桌面通知
      }
    }, POLL_INTERVAL)
  }
  
  // 停止轮询
  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }
  
  // 初始化
  const init = async () => {
    if (authStore.token) {
      await fetchNotifications()
      await fetchUnreadCount()
      startPolling()
    }
  }
  
  // 生命周期
  onMounted(() => {
    init()
  })
  
  onUnmounted(() => {
    stopPolling()
  })
  
  return {
    // 状态
    notifications,
    unreadCount,
    loading,
    stats,
    
    // 计算属性
    unreadNotifications,
    readNotifications,
    
    // 方法
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    fetchStats,
    createTestNotification,
    showDesktopNotification,
    showInAppNotification,
    formatNotificationTime,
    startPolling,
    stopPolling,
    init
  }
}