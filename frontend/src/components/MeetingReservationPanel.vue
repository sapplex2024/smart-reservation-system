<template>
  <div class="meeting-reservation-panel">
    <el-card class="panel-card" shadow="hover">
      <template #header>
        <div class="panel-header">
          <el-icon><Calendar /></el-icon>
          <span>会议室预约面板</span>
          <div class="header-actions">
            <el-date-picker
              v-model="selectedDate"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="loadReservations"
            />
            <el-button type="primary" :icon="Refresh" @click="loadReservations">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计信息 -->
      <div class="stats-section">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-number">{{ stats.total }}</div>
              <div class="stat-label">总预约数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-number">{{ stats.confirmed }}</div>
              <div class="stat-label">已确认</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-number">{{ stats.inProgress }}</div>
              <div class="stat-label">进行中</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card">
              <div class="stat-number">{{ stats.available }}</div>
              <div class="stat-label">可用会议室</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 时间轴视图 -->
      <div class="timeline-section">
        <h3>今日预约时间轴</h3>
        <div class="timeline-container">
          <div class="time-axis">
            <div 
              v-for="hour in timeHours" 
              :key="hour"
              class="time-slot"
              :class="{ 'current-hour': isCurrentHour(hour) }"
            >
              <div class="time-label">{{ formatHour(hour) }}</div>
            </div>
          </div>
          
          <div class="rooms-timeline">
            <div 
              v-for="room in rooms" 
              :key="room.id"
              class="room-timeline"
            >
              <div class="room-info">
                <div class="room-name">{{ room.name }}</div>
                <div class="room-capacity">{{ room.capacity }}人</div>
                <div class="room-status" :class="getRoomStatusClass(room)">
                  {{ getRoomStatusText(room) }}
                </div>
              </div>
              
              <div class="timeline-slots">
                <div 
                  v-for="hour in timeHours" 
                  :key="hour"
                  class="timeline-slot"
                  :class="getSlotClass(room.id, hour)"
                  @click="handleSlotClick(room, hour)"
                >
                  <div 
                    v-if="getReservationAtTime(room.id, hour)"
                    class="reservation-block"
                    :title="getReservationTooltip(room.id, hour)"
                  >
                    <div class="reservation-title">
                      {{ getReservationAtTime(room.id, hour)?.title }}
                    </div>
                    <div class="reservation-time">
                      {{ getReservationAtTime(room.id, hour) ? formatReservationTime(getReservationAtTime(room.id, hour)!) : '' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 预约列表 -->
      <div class="reservations-list">
        <h3>当日预约详情</h3>
        <el-table :data="todayReservations" v-loading="loading" max-height="400">
          <el-table-column prop="title" label="会议主题" min-width="150" />
          <el-table-column prop="resource_name" label="会议室" width="120" />
          <el-table-column label="时间" width="200">
            <template #default="{ row }">
              {{ formatDateTime(row.start_time) }} - {{ formatTime(row.end_time) }}
            </template>
          </el-table-column>
          <el-table-column prop="user_name" label="预约人" width="100" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusColor(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="参与人数" width="100">
            <template #default="{ row }">
              {{ row.participants?.length || 0 }}人
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" @click="viewReservationDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 预约详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="预约详情" width="600px">
      <div v-if="selectedReservation" class="reservation-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="预约编号">{{ selectedReservation.id }}</el-descriptions-item>
          <el-descriptions-item label="会议主题">{{ selectedReservation.title }}</el-descriptions-item>
          <el-descriptions-item label="会议室">{{ selectedReservation.resource_name }}</el-descriptions-item>
          <el-descriptions-item label="预约人">{{ selectedReservation.user_name }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDateTime(selectedReservation.start_time) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatDateTime(selectedReservation.end_time) }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusColor(selectedReservation.status)">
              {{ getStatusLabel(selectedReservation.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="参与人数">{{ selectedReservation.participants?.length || 0 }}人</el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedReservation.description" class="description-section">
          <h4>会议描述</h4>
          <p>{{ selectedReservation.description }}</p>
        </div>
        
        <div v-if="selectedReservation.participants?.length" class="participants-section">
          <h4>参与人员</h4>
          <el-tag v-for="participant in selectedReservation.participants" :key="participant" class="participant-tag">
            {{ participant }}
          </el-tag>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Calendar, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

// 接口定义
interface Reservation {
  id: number
  title: string
  description?: string
  start_time: string
  end_time: string
  status: string
  resource_name?: string
  user_name: string
  participants: string[]
  details: any
  created_at: string
}

interface Room {
  id: number
  name: string
  type: string
  capacity: number
  location?: string
  is_available: boolean
  features?: any
}

// 响应式数据
const loading = ref(false)
const selectedDate = ref(new Date().toISOString().split('T')[0])
const reservations = ref<Reservation[]>([])
const rooms = ref<Room[]>([])
const showDetailDialog = ref(false)
const selectedReservation = ref<Reservation | null>(null)

// 统计数据
const stats = reactive({
  total: 0,
  confirmed: 0,
  inProgress: 0,
  available: 0
})

// 时间轴小时数组（8:00 - 22:00）
const timeHours = Array.from({ length: 15 }, (_, i) => i + 8)

// 计算属性
const todayReservations = computed(() => {
  const today = selectedDate.value
  return reservations.value.filter(reservation => {
    const reservationDate = reservation.start_time.split('T')[0]
    return reservationDate === today
  })
})

// 方法
const loadReservations = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/reservations/', {
      params: {
        start_date: selectedDate.value,
        end_date: selectedDate.value,
        size: 100
      }
    })
    reservations.value = response.data.items || []
    updateStats()
  } catch (error) {
    console.error('加载预约数据失败:', error)
    ElMessage.error('加载预约数据失败')
  } finally {
    loading.value = false
  }
}

const loadRooms = async () => {
  try {
    const response = await axios.get('/api/resources/', {
      params: {
        resource_type: 'meeting_room',
        limit: 50
      }
    })
    rooms.value = response.data || []
    updateStats()
  } catch (error) {
    console.error('加载会议室数据失败:', error)
    ElMessage.error('加载会议室数据失败')
  }
}

const updateStats = () => {
  const today = selectedDate.value
  const todayRes = reservations.value.filter(r => r.start_time.split('T')[0] === today)
  
  stats.total = todayRes.length
  stats.confirmed = todayRes.filter(r => r.status === 'confirmed').length
  stats.inProgress = todayRes.filter(r => {
    const now = new Date()
    const start = new Date(r.start_time)
    const end = new Date(r.end_time)
    return now >= start && now <= end && r.status === 'confirmed'
  }).length
  stats.available = rooms.value.filter(r => r.is_available).length
}

const isCurrentHour = (hour: number) => {
  const now = new Date()
  return now.getHours() === hour && now.toISOString().split('T')[0] === selectedDate.value
}

const formatHour = (hour: number) => {
  return `${hour.toString().padStart(2, '0')}:00`
}

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatReservationTime = (reservation: Reservation) => {
  const start = formatTime(reservation.start_time)
  const end = formatTime(reservation.end_time)
  return `${start}-${end}`
}

const getRoomStatusClass = (room: Room) => {
  if (!room.is_available) return 'status-unavailable'
  
  const now = new Date()
  const currentHour = now.getHours()
  const hasCurrentReservation = reservations.value.some(r => {
    if (r.resource_name !== room.name) return false
    const start = new Date(r.start_time)
    const end = new Date(r.end_time)
    return now >= start && now <= end && r.status === 'confirmed'
  })
  
  if (hasCurrentReservation) return 'status-busy'
  return 'status-available'
}

const getRoomStatusText = (room: Room) => {
  if (!room.is_available) return '维护中'
  
  const now = new Date()
  const hasCurrentReservation = reservations.value.some(r => {
    if (r.resource_name !== room.name) return false
    const start = new Date(r.start_time)
    const end = new Date(r.end_time)
    return now >= start && now <= end && r.status === 'confirmed'
  })
  
  if (hasCurrentReservation) return '使用中'
  return '空闲'
}

const getSlotClass = (roomId: number, hour: number) => {
  const room = rooms.value.find(r => r.id === roomId)
  if (!room) return ''
  
  const reservation = getReservationAtTime(roomId, hour)
  if (reservation) {
    return `slot-reserved slot-${reservation.status}`
  }
  
  return 'slot-available'
}

const getReservationAtTime = (roomId: number, hour: number) => {
  const room = rooms.value.find(r => r.id === roomId)
  if (!room) return null
  
  return reservations.value.find(r => {
    if (r.resource_name !== room.name) return false
    const start = new Date(r.start_time)
    const end = new Date(r.end_time)
    const slotTime = new Date(selectedDate.value + ` ${hour}:00:00`)
    return slotTime >= start && slotTime < end
  })
}

const getReservationTooltip = (roomId: number, hour: number) => {
  const reservation = getReservationAtTime(roomId, hour)
  if (!reservation) return ''
  
  return `${reservation.title}\n${formatReservationTime(reservation)}\n预约人: ${reservation.user_name}`
}

const getStatusColor = (status: string) => {
  // 支持中文状态
  const chineseColorMap: Record<string, string> = {
    '待审批': 'warning',
    '已批准': 'success',
    '已拒绝': 'danger',
    '已取消': 'info',
    '已完成': 'success'
  }
  
  // 如果是中文状态，直接返回对应颜色
  if (chineseColorMap[status]) {
    return chineseColorMap[status]
  }
  
  // 兼容英文状态的映射（备用）
  const colorMap: Record<string, string> = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'cancelled': 'info',
    'completed': 'success'
  }
  return colorMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  // 如果后端已经返回中文状态，直接返回
  if (['待审批', '已批准', '已拒绝', '已取消', '已完成'].includes(status)) {
    return status
  }
  
  // 兼容英文状态的映射（备用）
  const labelMap: Record<string, string> = {
    'pending': '待审批',
    'approved': '已批准',
    'rejected': '已拒绝',
    'cancelled': '已取消',
    'completed': '已完成'
  }
  return labelMap[status] || status
}

const handleSlotClick = (room: Room, hour: number) => {
  const reservation = getReservationAtTime(room.id, hour)
  if (reservation) {
    viewReservationDetail(reservation)
  } else {
    // 可以在这里添加快速预约功能
    ElMessage.info(`点击了 ${room.name} 的 ${formatHour(hour)} 时段`)
  }
}

const viewReservationDetail = (reservation: Reservation) => {
  selectedReservation.value = reservation
  showDetailDialog.value = true
}

// 生命周期
onMounted(() => {
  loadRooms()
  loadReservations()
  
  // 每分钟刷新一次数据
  setInterval(() => {
    loadReservations()
  }, 60000)
})
</script>

<style scoped>
.meeting-reservation-panel {
  padding: 20px;
}

.panel-card {
  border-radius: 12px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 18px;
  font-weight: 600;
}

.panel-header .el-icon {
  margin-right: 8px;
  color: #409eff;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stats-section {
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.timeline-section {
  margin-bottom: 24px;
}

.timeline-section h3 {
  margin-bottom: 16px;
  color: #303133;
}

.timeline-container {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.time-axis {
  display: flex;
  background: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.time-slot {
  flex: 1;
  padding: 8px 4px;
  text-align: center;
  border-right: 1px solid #e4e7ed;
  font-size: 12px;
  color: #606266;
}

.time-slot.current-hour {
  background: #409eff;
  color: white;
  font-weight: bold;
}

.time-slot:last-child {
  border-right: none;
}

.rooms-timeline {
  max-height: 400px;
  overflow-y: auto;
}

.room-timeline {
  display: flex;
  border-bottom: 1px solid #e4e7ed;
}

.room-timeline:last-child {
  border-bottom: none;
}

.room-info {
  width: 150px;
  padding: 12px;
  background: #fafafa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.room-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.room-capacity {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.room-status {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  text-align: center;
}

.status-available {
  background: #f0f9ff;
  color: #67c23a;
}

.status-busy {
  background: #fef0f0;
  color: #f56c6c;
}

.status-unavailable {
  background: #f5f5f5;
  color: #909399;
}

.timeline-slots {
  display: flex;
  flex: 1;
}

.timeline-slot {
  flex: 1;
  height: 60px;
  border-right: 1px solid #e4e7ed;
  position: relative;
  cursor: pointer;
  transition: background-color 0.2s;
}

.timeline-slot:hover {
  background: #f0f9ff;
}

.timeline-slot:last-child {
  border-right: none;
}

.slot-available {
  background: #ffffff;
}

.slot-reserved {
  background: #e6f7ff;
}

.slot-confirmed {
  background: #f6ffed;
}

.slot-pending {
  background: #fff7e6;
}

.reservation-block {
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  background: #409eff;
  color: white;
  border-radius: 4px;
  padding: 4px;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

.reservation-title {
  font-weight: 600;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reservation-time {
  font-size: 10px;
  opacity: 0.9;
}

.reservations-list h3 {
  margin-bottom: 16px;
  color: #303133;
}

.reservation-detail {
  padding: 16px 0;
}

.description-section,
.participants-section {
  margin-top: 20px;
}

.description-section h4,
.participants-section h4 {
  margin-bottom: 12px;
  color: #303133;
  font-size: 16px;
}

.description-section p {
  color: #606266;
  line-height: 1.6;
}

.participant-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .room-info {
    width: 120px;
  }
  
  .timeline-slot {
    height: 50px;
  }
}
</style>