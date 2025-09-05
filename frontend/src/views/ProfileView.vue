<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="profile-header">
          <el-icon class="profile-icon"><User /></el-icon>
          <span class="profile-title">个人资料</span>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="6" animated />
      </div>
      
      <div v-else-if="userProfile" class="profile-content">
        <el-descriptions :column="1" size="large" border>
          <el-descriptions-item label="用户名">
            <el-tag type="primary">{{ userProfile.username }}</el-tag>
          </el-descriptions-item>
          
          <el-descriptions-item label="全名">
            {{ userProfile.full_name }}
          </el-descriptions-item>
          
          <el-descriptions-item label="邮箱">
            <el-link :href="`mailto:${userProfile.email}`" type="primary">
              {{ userProfile.email }}
            </el-link>
          </el-descriptions-item>
          
          <el-descriptions-item label="公司名称">
            {{ userProfile.company_name || '未填写' }}
          </el-descriptions-item>
          
          <el-descriptions-item label="联系电话">
            <span v-if="userProfile.phone">
              <el-link :href="`tel:${userProfile.phone}`" type="success">
                {{ userProfile.phone }}
              </el-link>
            </span>
            <span v-else class="text-muted">未填写</span>
          </el-descriptions-item>
          
          <el-descriptions-item label="用户角色">
            <el-tag :type="getRoleType(userProfile.role)">{{ getRoleLabel(userProfile.role) }}</el-tag>
          </el-descriptions-item>
          
          <el-descriptions-item label="注册时间">
            {{ formatDate(userProfile.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="profile-actions">
          <el-button type="primary" @click="showEditDialog = true">
            <el-icon><Edit /></el-icon>
            编辑资料
          </el-button>
          <el-button @click="refreshProfile">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
      
      <div v-else class="error-container">
        <el-empty description="无法加载个人资料">
          <el-button type="primary" @click="fetchProfile">重新加载</el-button>
        </el-empty>
      </div>
    </el-card>
    
    <!-- 编辑资料对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑个人资料" width="500px">
      <el-form 
        :model="editForm" 
        :rules="editRules" 
        ref="editFormRef"
        label-width="100px"
      >
        <el-form-item label="全名" prop="full_name">
          <el-input 
            v-model="editForm.full_name" 
            placeholder="请输入全名"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="公司名称" prop="company_name">
          <el-input 
            v-model="editForm.company_name" 
            placeholder="请输入公司名称"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="联系电话" prop="phone">
          <el-input 
            v-model="editForm.phone" 
            placeholder="请输入联系电话"
            clearable
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateProfile" :loading="updating">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Edit, Refresh } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore, type User as UserType } from '../stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const updating = ref(false)
const showEditDialog = ref(false)
const userProfile = ref<UserType | null>(null)
const editFormRef = ref<FormInstance>()

const editForm = reactive({
  full_name: '',
  company_name: '',
  phone: ''
})

const editRules: FormRules = {
  full_name: [
    { required: true, message: '请输入全名', trigger: 'blur' }
  ],
  company_name: [
    { required: true, message: '请输入公司名称', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ]
}

const fetchProfile = async () => {
  try {
    loading.value = true
    
    const response = await fetch('/api/auth/me', {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    })
    
    if (!response.ok) {
      throw new Error('获取个人资料失败')
    }
    
    const data = await response.json()
    userProfile.value = data
    
    // 填充编辑表单
    editForm.full_name = data.full_name || ''
    editForm.company_name = data.company_name || ''
    editForm.phone = data.phone || ''
    
  } catch (error) {
    console.error('获取个人资料失败:', error)
    ElMessage.error('获取个人资料失败')
  } finally {
    loading.value = false
  }
}

const handleUpdateProfile = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    updating.value = true
    
    const response = await fetch('/api/auth/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify(editForm)
    })
    
    if (!response.ok) {
      throw new Error('更新个人资料失败')
    }
    
    const data = await response.json()
    userProfile.value = data
    authStore.user = data // 更新store中的用户信息
    
    ElMessage.success('个人资料更新成功')
    showEditDialog.value = false
    
  } catch (error) {
    console.error('更新个人资料失败:', error)
    ElMessage.error('更新个人资料失败')
  } finally {
    updating.value = false
  }
}

const refreshProfile = () => {
  fetchProfile()
}

const getRoleType = (role: string) => {
  const roleTypes: Record<string, string> = {
    'ADMIN': 'danger',
    'MANAGER': 'warning',
    'EMPLOYEE': 'success',
    'VISITOR': 'info'
  }
  return roleTypes[role] || 'info'
}

const getRoleLabel = (role: string) => {
  const roleLabels: Record<string, string> = {
    'ADMIN': '管理员',
    'MANAGER': '经理',
    'EMPLOYEE': '员工',
    'VISITOR': '访客'
  }
  return roleLabels[role] || role
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchProfile()
})
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-icon {
  font-size: 20px;
  color: #409eff;
}

.profile-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.loading-container {
  padding: 20px;
}

.profile-content {
  padding: 20px 0;
}

.profile-actions {
  margin-top: 30px;
  text-align: center;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.error-container {
  padding: 40px 20px;
  text-align: center;
}

.text-muted {
  color: #909399;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: #606266;
}

:deep(.el-descriptions__content) {
  color: #303133;
}
</style>