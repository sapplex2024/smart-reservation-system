import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

export interface ReportStatistics {
  period: {
    start_date: string
    end_date: string
  }
  summary: {
    total_reservations: number
    status_distribution: Record<string, number>
    type_distribution: Record<string, number>
  }
  trends: {
    daily_stats: Array<{ date: string; count: number }>
    hourly_stats: Array<{ hour: number; count: number }>
    popular_times: Array<{ hour: number; count: number }>
  }
  user_activity: Array<{
    username: string
    full_name: string
    reservation_count: number
  }>
  resource_usage: Array<{
    name: string
    type: string
    usage_count: number
  }>
}

export interface DashboardData {
  summary: {
    total_reservations: number
    status_distribution: Record<string, number>
    type_distribution: Record<string, number>
  }
  daily_trend: Array<{ date: string; count: number }>
  popular_times: Array<{ hour: number; count: number }>
  top_resources: Array<{
    name: string
    type: string
    usage_count: number
  }>
  top_users?: Array<{
    username: string
    full_name: string
    reservation_count: number
  }>
}

export interface QuickStats {
  today: number
  this_week: number
  this_month: number
  pending_count: number
  approved_count: number
}

export function useReports() {
  const authStore = useAuthStore()
  const loading = ref(false)
  const statistics = ref<ReportStatistics | null>(null)
  const dashboardData = ref<DashboardData | null>(null)
  const quickStats = ref<QuickStats | null>(null)
  
  // 获取统计数据
  const fetchStatistics = async (
    startDate?: string,
    endDate?: string
  ) => {
    if (!authStore.token) return
    
    try {
      loading.value = true
      
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      
      const response = await fetch(`/api/reports/statistics?${params}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      statistics.value = result.data
      
      return result.data
    } catch (error) {
      console.error('获取统计数据失败:', error)
      ElMessage.error('获取统计数据失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 获取仪表板数据
  const fetchDashboardData = async () => {
    if (!authStore.token) return
    
    try {
      loading.value = true
      
      const response = await fetch('/api/reports/dashboard', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      dashboardData.value = result.data
      
      return result.data
    } catch (error) {
      console.error('获取仪表板数据失败:', error)
      ElMessage.error('获取仪表板数据失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 获取快速统计
  const fetchQuickStats = async () => {
    if (!authStore.token) return
    
    try {
      const response = await fetch('/api/reports/quick-stats', {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      quickStats.value = result.data
      
      return result.data
    } catch (error) {
      console.error('获取快速统计失败:', error)
      throw error
    }
  }
  
  // 获取用户报表
  const fetchUserReport = async (userId: number, days = 30) => {
    if (!authStore.token) return
    
    try {
      loading.value = true
      
      const response = await fetch(`/api/reports/user/${userId}?days=${days}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      return result.data
    } catch (error) {
      console.error('获取用户报表失败:', error)
      ElMessage.error('获取用户报表失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 获取分析数据
  const fetchAnalytics = async (period: 'week' | 'month' | 'quarter' | 'year' = 'month') => {
    if (!authStore.token) return
    
    try {
      loading.value = true
      
      const response = await fetch(`/api/reports/analytics?period=${period}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      return result.data
    } catch (error) {
      console.error('获取分析数据失败:', error)
      ElMessage.error('获取分析数据失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 导出Excel
  const exportExcel = async (
    startDate?: string,
    endDate?: string,
    statusFilter?: string[]
  ) => {
    if (!authStore.token) return
    
    try {
      loading.value = true
      
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (statusFilter) {
        statusFilter.forEach(status => params.append('status_filter', status))
      }
      
      const response = await fetch(`/api/reports/export/excel?${params}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // 获取文件名
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = '预约数据.xlsx'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      // 下载文件
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      ElMessage.success('Excel文件导出成功')
    } catch (error) {
      console.error('导出Excel失败:', error)
      ElMessage.error('导出Excel失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 导出CSV
  const exportCsv = async (
    startDate?: string,
    endDate?: string,
    statusFilter?: string[]
  ) => {
    if (!authStore.token) return
    
    try {
      loading.value = true
      
      const params = new URLSearchParams()
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (statusFilter) {
        statusFilter.forEach(status => params.append('status_filter', status))
      }
      
      const response = await fetch(`/api/reports/export/csv?${params}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // 获取文件名
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = '预约数据.csv'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }
      
      // 下载文件
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      ElMessage.success('CSV文件导出成功')
    } catch (error) {
      console.error('导出CSV失败:', error)
      ElMessage.error('导出CSV失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 格式化状态标签
  const formatStatusLabel = (status: string) => {
    const statusMap: Record<string, string> = {
      'pending': '待审批',
    'approved': '已批准',
    'rejected': '已拒绝',
    'completed': '已完成',
    'cancelled': '已取消'
    }
    return statusMap[status] || status
  }
  
  // 格式化类型标签
  const formatTypeLabel = (type: string) => {
    const typeMap: Record<string, string> = {
      'meeting': '会议预约',
      'EQUIPMENT': '设备预约',
      'ROOM': '房间预约',
      'SERVICE': '服务预约'
    }
    return typeMap[type] || type
  }
  
  // 获取状态颜色
  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      'pending': '#e6a23c',
    'approved': '#67c23a',
    'rejected': '#f56c6c',
    'completed': '#909399',
    'cancelled': '#f56c6c'
    }
    return colorMap[status] || '#909399'
  }
  
  // 计算属性
  const totalReservations = computed(() => 
    statistics.value?.summary.total_reservations || 0
  )
  
  const statusDistribution = computed(() => 
    statistics.value?.summary.status_distribution || {}
  )
  
  const typeDistribution = computed(() => 
    statistics.value?.summary.type_distribution || {}
  )
  
  const dailyTrend = computed(() => 
    statistics.value?.trends.daily_stats || []
  )
  
  const popularTimes = computed(() => 
    statistics.value?.trends.popular_times || []
  )
  
  const topResources = computed(() => 
    statistics.value?.resource_usage.slice(0, 5) || []
  )
  
  const topUsers = computed(() => 
    statistics.value?.user_activity.slice(0, 5) || []
  )
  
  return {
    // 状态
    loading,
    statistics,
    dashboardData,
    quickStats,
    
    // 计算属性
    totalReservations,
    statusDistribution,
    typeDistribution,
    dailyTrend,
    popularTimes,
    topResources,
    topUsers,
    
    // 方法
    fetchStatistics,
    fetchDashboardData,
    fetchQuickStats,
    fetchUserReport,
    fetchAnalytics,
    exportExcel,
    exportCsv,
    formatStatusLabel,
    formatTypeLabel,
    getStatusColor
  }
}