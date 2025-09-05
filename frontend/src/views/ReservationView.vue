<template>
  <div class="reservation-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <el-icon class="header-icon"><Calendar /></el-icon>
          <div>
            <h1 class="page-title">会议室预约管理</h1>
            <p class="page-subtitle">管理您的会议室预约</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            新建预约
          </el-button>
          <el-button :icon="Refresh" @click="refreshData">
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon meeting-room">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.meeting }}</div>
            <div class="stat-label">会议室预约</div>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon total">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.total }}</div>
            <div class="stat-label">总预约数</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-content">
        <div class="filter-left">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索预约信息..."
            :prefix-icon="Search"
            clearable
            class="search-input"
            @input="handleSearch"
          />
          <el-select
            v-model="filterType"
            placeholder="预约类型"
            clearable
            class="filter-select"
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="会议室" value="meeting" />
          </el-select>
          <el-select
            v-model="filterStatus"
            placeholder="预约状态"
            clearable
            class="filter-select"
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="待审批" value="pending" />
            <el-option label="已批准" value="approved" />
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
            class="date-picker"
            @change="handleDateFilter"
          />
        </div>
      </div>
    </el-card>

    <!-- 预约列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="paginatedReservations"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        stripe
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="reservation_number" label="预约编号" width="120" />
        <el-table-column prop="title" label="预约标题" min-width="150" />
        <el-table-column prop="type" label="预约类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)" size="small">
              {{ formatTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_name" label="申请人" width="120" />
        <el-table-column label="预约时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time, row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ formatStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatCreatedAt(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewReservation(row)">查看</el-button>
            <el-button 
              v-if="row.status === 'pending'"
              size="small" 
              type="success" 
              @click="confirmReservation(row)"
            >
              确认
            </el-button>
            <el-button 
              v-if="['pending', 'approved'].includes(row.status)"
              size="small" 
              type="danger" 
              @click="cancelReservation(row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalReservations"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新建预约对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建预约"
      width="600px"
      @close="handleCloseCreate"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="预约类型" prop="type">
          <el-select v-model="createForm.type" placeholder="请选择预约类型">
            <el-option label="会议室" value="meeting" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="预约标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入预约标题" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="createForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入预约描述"
          />
        </el-form-item>
        
        <el-form-item label="开始时间" prop="start_time">
          <el-date-picker
            v-model="createForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        
        <el-form-item label="结束时间" prop="end_time">
          <el-date-picker
            v-model="createForm.end_time"
            type="datetime"
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCloseCreate">取消</el-button>
          <el-button type="primary" :loading="creating" @click="handleCreateReservation">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 预约详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="预约详情"
      width="500px"
    >
      <div v-if="selectedReservation" class="detail-content">
        <div class="detail-item">
          <span class="detail-label">预约编号：</span>
          <span class="detail-value">{{ selectedReservation.reservation_number || selectedReservation.id }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">预约类型：</span>
          <el-tag :type="getTypeTagType(selectedReservation.type)" size="small">
            {{ formatTypeLabel(selectedReservation.type) }}
          </el-tag>
        </div>
        <div class="detail-item">
          <span class="detail-label">预约标题：</span>
          <span class="detail-value">{{ selectedReservation.title }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">申请人：</span>
          <span class="detail-value">{{ selectedReservation.user_name }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">预约时间：</span>
          <span class="detail-value">{{ formatDateTime(selectedReservation.start_time, selectedReservation.end_time) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">预约状态：</span>
          <el-tag :type="getStatusTagType(selectedReservation.status)" size="small">
            {{ formatStatusLabel(selectedReservation.status) }}
          </el-tag>
        </div>
        <div v-if="selectedReservation.resource_name" class="detail-item">
          <span class="detail-label">预约资源：</span>
          <span class="detail-value">{{ selectedReservation.resource_name }}</span>
        </div>
        <div v-if="selectedReservation.description" class="detail-item">
          <span class="detail-label">描述：</span>
          <span class="detail-value">{{ selectedReservation.description }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  Calendar,
  Plus,
  Refresh,
  OfficeBuilding,
  User,
  Van,
  DataAnalysis,
  Search
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useReservations, type Reservation, type ReservationCreate } from '@/composables/useReservations'

// 使用组合式函数
const {
  loading,
  reservations,
  stats,
  fetchReservations,
  createReservation,
  cancelReservation: cancelReservationAPI,
  fetchStats,
  formatTypeLabel,
  formatStatusLabel,
  getTypeTagType,
  getStatusTagType
} = useReservations()

// 响应式数据
const creating = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedReservation = ref<Reservation | null>(null)
const selectedReservations = ref<Reservation[]>([])

// 搜索和筛选
const searchKeyword = ref('')
const filterType = ref('')
const filterStatus = ref('')
const dateRange = ref<[string, string] | null>(null)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalReservations = ref(0)

// 新建预约表单
const createFormRef = ref<FormInstance>()
const createForm = reactive<ReservationCreate>({
  type: 'meeting',
  title: '',
  description: '',
  start_time: '',
  end_time: ''
})

const createRules: FormRules = {
  type: [{ required: true, message: '请选择预约类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入预约标题', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

// 计算属性
const filteredReservations = computed(() => {
  let filtered = reservations.value
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(item => 
      item.title.toLowerCase().includes(keyword) ||
      item.user_name.toLowerCase().includes(keyword) ||
      item.id.toString().toLowerCase().includes(keyword)
    )
  }
  
  // 类型筛选
  if (filterType.value) {
    filtered = filtered.filter(item => item.type === filterType.value)
  }
  
  // 状态筛选
  if (filterStatus.value) {
    filtered = filtered.filter(item => item.status === filterStatus.value)
  }
  
  // 日期范围筛选
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value
    filtered = filtered.filter(item => {
      const itemDate = item.start_time.split(' ')[0]
      return itemDate >= startDate && itemDate <= endDate
    })
  }
  
  totalReservations.value = filtered.length
  return filtered
})

const paginatedReservations = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredReservations.value.slice(start, end)
})

// 方法
const refreshData = async () => {
  try {
    await loadReservations()
    await fetchStats()
    ElMessage.success('数据已刷新')
  } catch (error) {
    ElMessage.error('刷新失败')
  }
}

const loadReservations = async () => {
  try {
    await fetchReservations(1, 100) // 获取数据用于前端筛选
  } catch (error) {
    console.error('加载预约数据失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleFilter = () => {
  currentPage.value = 1
}

const handleDateFilter = () => {
  currentPage.value = 1
}

const handleSelectionChange = (selection: Reservation[]) => {
  selectedReservations.value = selection
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

const viewReservation = (reservation: Reservation) => {
  selectedReservation.value = reservation
  showDetailDialog.value = true
}

const confirmReservation = async (reservation: Reservation) => {
  try {
    await ElMessageBox.confirm('确认此预约？', '确认操作', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 这里应该调用API更新状态，暂时直接修改
    reservation.status = 'approved'
    ElMessage.success('预约已确认')
    await fetchStats()
  } catch {
    // 用户取消
  }
}

const cancelReservation = async (reservation: Reservation) => {
  try {
    await ElMessageBox.confirm('取消此预约？', '取消操作', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const success = await cancelReservationAPI(reservation.id)
    if (success) {
      await loadReservations()
      await fetchStats()
    }
  } catch {
    // 用户取消
  }
}

const handleCreateReservation = async () => {
  if (!createFormRef.value) return
  
  try {
    await createFormRef.value.validate()
    creating.value = true
    
    const result = await createReservation(createForm)
    if (result) {
      await loadReservations()
      await fetchStats()
      handleCloseCreate()
    }
  } catch (error) {
    console.error('创建预约失败:', error)
  } finally {
    creating.value = false
  }
}

const handleCloseCreate = () => {
  showCreateDialog.value = false
  createFormRef.value?.resetFields()
  Object.assign(createForm, {
    type: 'meeting',
    title: '',
    description: '',
    start_time: '',
    end_time: ''
  })
}

// 辅助方法
const formatDateTime = (startTime: string, endTime: string) => {
  const start = new Date(startTime).toLocaleString('zh-CN')
  const end = new Date(endTime).toLocaleString('zh-CN')
  return `${start} - ${end}`
}

const formatCreatedAt = (createdAt: string) => {
  return new Date(createdAt).toLocaleString('zh-CN')
}

// 生命周期
onMounted(async () => {
  await loadReservations()
  await fetchStats()
})
</script>

<style scoped>
.reservation-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  font-size: 32px;
  color: #409eff;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-subtitle {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: #909399;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  overflow: hidden;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.stat-icon.meeting-room {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.visitor {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.vehicle {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.total {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-left {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.search-input {
  width: 240px;
}

.filter-select {
  width: 140px;
}

.date-picker {
  width: 240px;
}

.table-card {
  border-radius: 12px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.detail-content {
  padding: 20px 0;
}

.detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.detail-label {
  width: 100px;
  font-weight: 500;
  color: #606266;
}

.detail-value {
  flex: 1;
  color: #303133;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>