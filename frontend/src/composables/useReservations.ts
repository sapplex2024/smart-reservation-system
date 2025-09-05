import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

export interface Reservation {
  id: number
  reservation_number?: string  // 添加预约编号字段
  type: 'meeting' | 'visitor' | 'vehicle'
  title: string
  description?: string
  start_time: string
  end_time: string
  status: 'pending' | 'approved' | 'rejected' | 'cancelled' | 'completed'
  resource_name?: string
  user_name: string
  participants?: string[]
  details?: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface ReservationCreate {
  type: 'meeting' | 'visitor' | 'vehicle'
  title: string
  description?: string
  start_time: string
  end_time: string
  resource_id?: number
  participants?: string[]
  details?: Record<string, any>
}

export interface ReservationUpdate {
  title?: string
  description?: string
  start_time?: string
  end_time?: string
  resource_id?: number
  participants?: string[]
  details?: Record<string, any>
}

export interface PaginatedReservations {
  items: Reservation[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ReservationStats {
  total: number
  meeting: number
  visitor: number
  vehicle: number
  pending: number
  approved: number
  completed: number
}

export function useReservations() {
  const authStore = useAuthStore()
  const loading = ref(false)
  const reservations = ref<Reservation[]>([])
  const stats = ref<ReservationStats>({
    total: 0,
    meeting: 0,
    visitor: 0,
    vehicle: 0,
    pending: 0,
    approved: 0,
    completed: 0
  })

  // 获取预约列表
  const fetchReservations = async (
    page = 1,
    size = 20,
    status?: string,
    startDate?: string,
    endDate?: string,
    reservationType?: string
  ): Promise<PaginatedReservations | null> => {
    try {
      loading.value = true

      const params = new URLSearchParams()
      params.append('page', page.toString())
      params.append('size', size.toString())
      if (status) params.append('status', status)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)
      if (reservationType) params.append('reservation_type', reservationType)

      const response = await fetch(`/api/v1/reservations/?${params}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      reservations.value = result.items
      
      return result
    } catch (error) {
      console.error('获取预约列表失败:', error)
      ElMessage.error('获取预约列表失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取单个预约详情
  const fetchReservation = async (id: number): Promise<Reservation | null> => {
    try {
      loading.value = true

      const response = await fetch(`/api/v1/reservations/${id}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('获取预约详情失败:', error)
      ElMessage.error('获取预约详情失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建预约
  const createReservation = async (reservation: ReservationCreate): Promise<Reservation | null> => {
    try {
      loading.value = true

      const response = await fetch('/api/v1/reservations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reservation)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      ElMessage.success('预约创建成功')
      return result
    } catch (error) {
      console.error('创建预约失败:', error)
      ElMessage.error(`创建预约失败: ${error instanceof Error ? error.message : '未知错误'}`)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新预约
  const updateReservation = async (id: number, updates: ReservationUpdate): Promise<Reservation | null> => {
    try {
      loading.value = true

      const response = await fetch(`/api/v1/reservations/${id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      ElMessage.success('预约更新成功')
      return result
    } catch (error) {
      console.error('更新预约失败:', error)
      ElMessage.error(`更新预约失败: ${error instanceof Error ? error.message : '未知错误'}`)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 取消预约
  const cancelReservation = async (id: number): Promise<boolean> => {
    try {
      loading.value = true

      const response = await fetch(`/api/v1/reservations/${id}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      ElMessage.success('预约已取消')
      return true
    } catch (error) {
      console.error('取消预约失败:', error)
      ElMessage.error(`取消预约失败: ${error instanceof Error ? error.message : '未知错误'}`)
      return false
    } finally {
      loading.value = false
    }
  }

  // 获取预约统计
  const fetchStats = async (): Promise<ReservationStats | null> => {
    try {
      // 获取当前用户的所有预约
      const result = await fetchReservations(1, 100) // 获取数据用于统计
      if (!result) return null

      const allReservations = result.items
      const statsData: ReservationStats = {
        total: allReservations.length,
        meeting: allReservations.filter(r => r.type === 'meeting').length,
        visitor: allReservations.filter(r => r.type === 'visitor').length,
        vehicle: allReservations.filter(r => r.type === 'vehicle').length,
        pending: allReservations.filter(r => r.status === 'pending').length,
        approved: allReservations.filter(r => r.status === 'approved').length,
        completed: allReservations.filter(r => r.status === 'completed').length
      }

      stats.value = statsData
      return statsData
    } catch (error) {
      console.error('获取预约统计失败:', error)
      return null
    }
  }

  // 格式化预约类型标签
  const formatTypeLabel = (type: string): string => {
    const labels = {
      'meeting': '会议室',
      'visitor': '访客',
      'vehicle': '车辆'
    }
    return labels[type as keyof typeof labels] || type
  }

  // 格式化预约状态标签
  const formatStatusLabel = (status: string): string => {
    // 如果后端已经返回中文状态，直接返回
    if (['待审批', '已批准', '已拒绝', '已取消', '已完成'].includes(status)) {
      return status
    }
    
    // 兼容英文状态的映射（备用）
    const labels = {
      'pending': '待审批',
      'approved': '已批准',
      'rejected': '已拒绝',
      'cancelled': '已取消',
      'completed': '已完成'
    }
    return labels[status as keyof typeof labels] || status
  }

  // 获取类型标签样式
  const getTypeTagType = (type: string): string => {
    const types = {
      'meeting': 'primary',
      'visitor': 'success',
      'vehicle': 'warning'
    }
    return types[type as keyof typeof types] || ''
  }

  // 获取状态标签样式
  const getStatusTagType = (status: string): string => {
    // 支持中文状态
    const chineseTypes = {
      '待审批': 'warning',
      '已批准': 'success',
      '已拒绝': 'danger',
      '已取消': 'info',
      '已完成': 'success'
    }
    
    // 如果是中文状态，直接返回对应样式
    if (chineseTypes[status as keyof typeof chineseTypes]) {
      return chineseTypes[status as keyof typeof chineseTypes]
    }
    
    // 兼容英文状态的映射（备用）
    const types = {
      'pending': 'warning',
      'approved': 'success',
      'rejected': 'danger',
      'cancelled': 'info',
      'completed': 'success'
    }
    return types[status as keyof typeof types] || ''
  }

  return {
    loading,
    reservations,
    stats,
    fetchReservations,
    fetchReservation,
    createReservation,
    updateReservation,
    cancelReservation,
    fetchStats,
    formatTypeLabel,
    formatStatusLabel,
    getTypeTagType,
    getStatusTagType
  }
}