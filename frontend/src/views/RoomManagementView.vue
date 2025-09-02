<template>
  <div class="room-management-view">
    <div class="page-header">
      <h1 class="page-title">会议室管理</h1>
      <p class="page-subtitle">管理会议室资源，配置数量、名称、位置等信息</p>
    </div>

    <!-- 操作栏 -->
    <el-card class="action-card" shadow="hover">
      <div class="action-bar">
        <div class="search-section">
          <el-input
            v-model="searchQuery"
            placeholder="搜索会议室名称或位置"
            style="width: 300px;"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <div class="button-section">
          <el-button
            type="primary"
            @click="showCreateDialog = true"
            :icon="Plus"
          >
            添加会议室
          </el-button>
          <el-button
            type="success"
            @click="loadRooms"
            :loading="loading"
            :icon="Refresh"
          >
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 会议室列表 -->
    <el-card class="table-card" shadow="hover">
      <el-table
        :data="filteredRooms"
        v-loading="loading"
        style="width: 100%"
        empty-text="暂无会议室数据"
      >
        <el-table-column prop="name" label="会议室名称" width="200">
          <template #default="scope">
            <div class="room-name">
              <el-icon class="room-icon"><OfficeBuilding /></el-icon>
              <span>{{ scope.row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="capacity" label="容量" width="100">
          <template #default="scope">
            <el-tag type="info">{{ scope.row.capacity }}人</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="位置" width="200" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="features" label="设备" width="200">
          <template #default="scope">
            <div class="features-tags">
              <el-tag
                v-for="feature in getFeaturesList(scope.row.features)"
                :key="feature"
                size="small"
                style="margin-right: 5px; margin-bottom: 2px;"
              >
                {{ feature }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="is_available" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_available ? 'success' : 'danger'">
              {{ scope.row.is_available ? '可用' : '不可用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click="editRoom(scope.row)"
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              :type="scope.row.is_available ? 'warning' : 'success'"
              @click="toggleRoomStatus(scope.row)"
            >
              {{ scope.row.is_available ? '禁用' : '启用' }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteRoom(scope.row)"
              :icon="Delete"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑会议室对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingRoom ? '编辑会议室' : '添加会议室'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="roomFormRef"
        :model="roomForm"
        :rules="roomRules"
        label-width="100px"
      >
        <el-form-item label="会议室名称" prop="name">
          <el-input
            v-model="roomForm.name"
            placeholder="请输入会议室名称"
          />
        </el-form-item>
        <el-form-item label="容量" prop="capacity">
          <el-input-number
            v-model="roomForm.capacity"
            :min="1"
            :max="100"
            placeholder="请输入容量"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input
            v-model="roomForm.location"
            placeholder="请输入会议室位置"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="roomForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入会议室描述"
          />
        </el-form-item>
        <el-form-item label="设备">
          <el-checkbox-group v-model="selectedFeatures">
            <el-checkbox label="投影仪">投影仪</el-checkbox>
            <el-checkbox label="白板">白板</el-checkbox>
            <el-checkbox label="电视">电视</el-checkbox>
            <el-checkbox label="音响">音响</el-checkbox>
            <el-checkbox label="视频会议">视频会议</el-checkbox>
            <el-checkbox label="空调">空调</el-checkbox>
            <el-checkbox label="WiFi">WiFi</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch
            v-model="roomForm.is_available"
            active-text="可用"
            inactive-text="不可用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveRoom"
          :loading="saving"
        >
          {{ editingRoom ? '更新' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  Search,
  Plus,
  Refresh,
  Edit,
  Delete,
  OfficeBuilding
} from '@element-plus/icons-vue'
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// 接口定义
interface Room {
  id: number
  name: string
  type: string
  capacity: number
  location: string
  description: string
  features: Record<string, boolean>
  is_available: boolean
  created_at: string
}

interface RoomForm {
  name: string
  capacity: number
  location: string
  description: string
  is_available: boolean
}

// 响应式数据
const authStore = useAuthStore()
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const editingRoom = ref<Room | null>(null)
const searchQuery = ref('')
const rooms = ref<Room[]>([])
const selectedFeatures = ref<string[]>([])

const roomFormRef = ref<FormInstance>()
const roomForm = ref<RoomForm>({
  name: '',
  capacity: 10,
  location: '',
  description: '',
  is_available: true
})

// 表单验证规则
const roomRules = {
  name: [
    { required: true, message: '请输入会议室名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  capacity: [
    { required: true, message: '请输入容量', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: '容量必须在 1 到 100 之间', trigger: 'blur' }
  ],
  location: [
    { required: true, message: '请输入位置', trigger: 'blur' }
  ]
}

// 计算属性
const filteredRooms = computed(() => {
  if (!searchQuery.value) return rooms.value
  
  const query = searchQuery.value.toLowerCase()
  return rooms.value.filter(room => 
    room.name.toLowerCase().includes(query) ||
    room.location.toLowerCase().includes(query)
  )
})

// 方法
const loadRooms = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/resources/', {
      params: {
        resource_type: 'meeting_room'
      },
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    rooms.value = response.data
  } catch (error: any) {
    ElMessage.error(`加载会议室列表失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    loading.value = false
  }
}

const getFeaturesList = (features: Record<string, boolean>) => {
  if (!features) return []
  return Object.entries(features)
    .filter(([_, enabled]) => enabled)
    .map(([feature, _]) => feature)
}

const editRoom = (room: Room) => {
  editingRoom.value = room
  roomForm.value = {
    name: room.name,
    capacity: room.capacity,
    location: room.location,
    description: room.description || '',
    is_available: room.is_available
  }
  selectedFeatures.value = getFeaturesList(room.features)
  showCreateDialog.value = true
}

const resetForm = () => {
  editingRoom.value = null
  roomForm.value = {
    name: '',
    capacity: 10,
    location: '',
    description: '',
    is_available: true
  }
  selectedFeatures.value = []
  roomFormRef.value?.resetFields()
}

const saveRoom = async () => {
  if (!roomFormRef.value) return
  
  try {
    await roomFormRef.value.validate()
  } catch {
    return
  }
  
  saving.value = true
  
  try {
    // 构建特性对象
    const features: Record<string, boolean> = {}
    const allFeatures = ['投影仪', '白板', '电视', '音响', '视频会议', '空调', 'WiFi']
    allFeatures.forEach(feature => {
      features[feature] = selectedFeatures.value.includes(feature)
    })
    
    const roomData = {
      ...roomForm.value,
      type: 'meeting_room',
      features
    }
    
    if (editingRoom.value) {
      // 更新会议室
      await axios.put(`/api/resources/${editingRoom.value.id}`, roomData, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      ElMessage.success('会议室更新成功')
    } else {
      // 创建会议室
      await axios.post('/api/resources/', roomData, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
      ElMessage.success('会议室添加成功')
    }
    
    showCreateDialog.value = false
    await loadRooms()
  } catch (error: any) {
    ElMessage.error(`保存失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    saving.value = false
  }
}

const toggleRoomStatus = async (room: Room) => {
  try {
    const action = room.is_available ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}会议室 "${room.name}" 吗？`,
      `确认${action}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.put(`/api/resources/${room.id}`, {
        is_available: !room.is_available
      }, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
    
    ElMessage.success(`会议室${action}成功`)
    await loadRooms()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`操作失败: ${error.response?.data?.detail || error.message}`)
    }
  }
}

const deleteRoom = async (room: Room) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除会议室 "${room.name}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/resources/${room.id}`, {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      })
    ElMessage.success('会议室删除成功')
    await loadRooms()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`删除失败: ${error.response?.data?.detail || error.message}`)
    }
  }
}

// 初始化
onMounted(() => {
  loadRooms()
})
</script>

<style scoped>
.room-management-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.action-card {
  margin-bottom: 20px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.button-section {
  display: flex;
  gap: 10px;
}

.table-card {
  margin-bottom: 20px;
}

.room-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.room-icon {
  color: #409eff;
}

.features-tags {
  display: flex;
  flex-wrap: wrap;
}

.el-form-item {
  margin-bottom: 18px;
}

.el-dialog .el-form-item {
  margin-bottom: 15px;
}

@media (max-width: 768px) {
  .room-management-view {
    padding: 10px;
  }
  
  .action-bar {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .search-section {
    width: 100%;
  }
  
  .search-section .el-input {
    width: 100% !important;
  }
}
</style>