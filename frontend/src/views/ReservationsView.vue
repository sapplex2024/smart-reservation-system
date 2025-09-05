<template>
  <div class="reservations-container">
    <el-card class="reservations-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <el-icon><Calendar /></el-icon>
          <span>我的预约</span>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            新建预约
          </el-button>
        </div>
      </template>
      
      <div class="filters">
        <el-select v-model="filterType" placeholder="预约类型" clearable>
          <el-option label="全部" value="" />
          <el-option label="会议" value="meeting" />
        </el-select>
        
        <el-select v-model="filterStatus" placeholder="状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="待确认" value="pending" />
          <el-option label="已确认" value="confirmed" />
          <el-option label="已完成" value="completed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>
        
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
        
        <el-button type="primary" :icon="Search" @click="loadReservations">
          搜索
        </el-button>
      </div>
      
      <el-table :data="filteredReservations" v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">{{ getTypeLabel(row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="resource_name" label="资源" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusColor(row.status)">{{ getStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="viewReservation(row)">详情</el-button>
            <el-button 
              v-if="row.status === 'pending' || row.status === 'confirmed'"
              size="small" 
              type="danger" 
              @click="cancelReservation(row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadReservations"
          @current-change="loadReservations"
        />
      </div>
    </el-card>
    
    <!-- 创建预约对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建预约" width="600px">
      <el-form :model="newReservation" label-width="100px">
        <el-form-item label="预约类型">
          <el-select v-model="newReservation.type" placeholder="请选择预约类型">
            <el-option label="会议" value="meeting" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标题">
          <el-input v-model="newReservation.title" placeholder="请输入预约标题" />
        </el-form-item>
        
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="newReservation.start_time"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="newReservation.end_time"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        
        <el-form-item label="资源">
          <el-select v-model="newReservation.resource_id" placeholder="请选择资源">
            <el-option 
              v-for="resource in availableResources" 
              :key="resource.id"
              :label="resource.name"
              :value="resource.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input 
            v-model="newReservation.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入预约描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createReservation" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  Calendar, 
  Plus, 
  Search 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

interface Reservation {
  id: string
  title: string
  type: string
  start_time: string
  end_time: string
  resource_id: string
  resource_name: string
  status: string
  description: string
}

interface Resource {
  id: string
  name: string
  type: string
}

const reservations = ref<Reservation[]>([])
const availableResources = ref<Resource[]>([])
const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)

const filterType = ref('')
const filterStatus = ref('')
const dateRange = ref<[string, string] | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const newReservation = ref({
  type: '',
  title: '',
  start_time: '',
  end_time: '',
  resource_id: '',
  description: ''
})

const filteredReservations = computed(() => {
  let filtered = reservations.value
  
  if (filterType.value) {
    filtered = filtered.filter(r => r.type === filterType.value)
  }
  
  if (filterStatus.value) {
    filtered = filtered.filter(r => r.status === filterStatus.value)
  }
  
  if (dateRange.value) {
    const [start, end] = dateRange.value
    filtered = filtered.filter(r => {
      const startTime = new Date(r.start_time).toISOString().split('T')[0]
      return startTime >= start && startTime <= end
    })
  }
  
  return filtered
})

const loadReservations = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/reservations', {
      params: {
        page: currentPage.value,
        size: pageSize.value,
        type: filterType.value || undefined,
        status: filterStatus.value || undefined,
        start_date: dateRange.value?.[0],
        end_date: dateRange.value?.[1]
      }
    })
    
    reservations.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('加载预约失败:', error)
    ElMessage.error('加载预约失败')
  } finally {
    loading.value = false
  }
}

const loadResources = async () => {
  try {
    const response = await axios.get('/api/reservations/resources')
    availableResources.value = response.data || []
  } catch (error) {
    console.error('加载资源失败:', error)
  }
}

const createReservation = async () => {
  creating.value = true
  try {
    await axios.post('/api/reservations', newReservation.value)
    ElMessage.success('预约创建成功')
    showCreateDialog.value = false
    resetForm()
    loadReservations()
  } catch (error) {
    console.error('创建预约失败:', error)
    ElMessage.error('创建预约失败')
  } finally {
    creating.value = false
  }
}

const cancelReservation = async (reservation: Reservation) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消预约"${reservation.title}"吗？`,
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/reservations/${reservation.id}`)
    ElMessage.success('预约已取消')
    loadReservations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消预约失败:', error)
      ElMessage.error('取消预约失败')
    }
  }
}

const viewReservation = (reservation: Reservation) => {
  ElMessageBox.alert(
    `类型: ${getTypeLabel(reservation.type)}\n开始时间: ${formatDateTime(reservation.start_time)}\n结束时间: ${formatDateTime(reservation.end_time)}\n资源: ${reservation.resource_name}\n状态: ${getStatusLabel(reservation.status)}\n描述: ${reservation.description || '无'}`,
    reservation.title,
    {
      confirmButtonText: '确定'
    }
  )
}

const resetForm = () => {
  newReservation.value = {
    type: '',
    title: '',
    start_time: '',
    end_time: '',
    resource_id: '',
    description: ''
  }
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    meeting: '会议',
    visitor: '访客',
    parking: '停车'
  }
  return labels[type] || type
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    meeting: 'primary',
    visitor: 'success',
    parking: 'warning'
  }
  return colors[type] || ''
}

const getStatusLabel = (status: string) => {
  // 如果后端已经返回中文状态，直接返回
  if (['待审批', '已批准', '已拒绝', '已取消', '已完成'].includes(status)) {
    return status
  }
  
  // 兼容英文状态的映射（备用）
  const labels: Record<string, string> = {
    pending: '待审批',
    approved: '已批准',
    rejected: '已拒绝',
    cancelled: '已取消',
    completed: '已完成'
  }
  return labels[status] || status
}

const getStatusColor = (status: string) => {
  // 支持中文状态
  const chineseColors: Record<string, string> = {
    '待审批': 'warning',
    '已批准': 'success',
    '已拒绝': 'danger',
    '已取消': 'info',
    '已完成': 'success'
  }
  
  // 如果是中文状态，直接返回对应颜色
  if (chineseColors[status]) {
    return chineseColors[status]
  }
  
  // 兼容英文状态的映射（备用）
  const colors: Record<string, string> = {
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    cancelled: 'info',
    completed: 'success'
  }
  return colors[status] || ''
}

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN')
}

onMounted(() => {
  loadReservations()
  loadResources()
})
</script>

<style scoped>
.reservations-container {
  max-width: 1200px;
  margin: 0 auto;
}

.reservations-card {
  min-height: calc(100vh - 140px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
}

.card-header button {
  margin-left: auto;
}

.filters {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.filters .el-select,
.filters .el-date-picker {
  width: 200px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

@media (max-width: 768px) {
  .filters {
    flex-direction: column;
  }
  
  .filters .el-select,
  .filters .el-date-picker {
    width: 100%;
  }
}
</style>