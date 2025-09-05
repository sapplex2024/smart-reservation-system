<template>
  <div class="login-container">
    <div class="login-background">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
    
    <el-card class="login-card">
      <div class="login-header">
        <div class="logo">
          <el-icon class="logo-icon"><OfficeBuilding /></el-icon>
          <h1 class="logo-text">智能预约系统</h1>
        </div>
        <p class="login-subtitle">欢迎使用智能预约管理平台</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="large"
            class="login-input"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="large"
            class="login-input"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <div class="login-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-link type="primary" :underline="false">忘记密码？</el-link>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="demo-section">
        <el-divider>演示账号</el-divider>
        <div class="demo-accounts">
          <el-button 
            v-for="account in demoAccounts" 
            :key="account.username"
            @click="fillDemoAccount(account)"
            size="small"
            type="info"
            plain
          >
            {{ account.label }}
          </el-button>
        </div>
      </div>
      
      <div class="register-section">
        <el-divider>还没有账号？</el-divider>
        <el-button 
          type="success" 
          plain 
          @click="showRegisterDialog = true"
          class="register-btn"
        >
          注册新账号
        </el-button>
      </div>
    </el-card>
    
    <!-- 注册对话框 -->
    <el-dialog v-model="showRegisterDialog" title="用户注册" width="500px">
      <el-form 
        :model="registerForm" 
        :rules="registerRules" 
        ref="registerFormRef"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="registerForm.username" 
            placeholder="请输入用户名"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input 
            v-model="registerForm.email" 
            placeholder="请输入邮箱"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="全名" prop="full_name">
          <el-input 
            v-model="registerForm.full_name" 
            placeholder="请输入全名"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="公司名称" prop="company_name">
          <el-input 
            v-model="registerForm.company_name" 
            placeholder="请输入公司名称"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="联系电话" prop="phone">
          <el-input 
            v-model="registerForm.phone" 
            placeholder="请输入联系电话"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="registerForm.password" 
            type="password" 
            placeholder="请输入密码"
            show-password
            clearable
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="registerForm.confirmPassword" 
            type="password" 
            placeholder="请再次输入密码"
            show-password
            clearable
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showRegisterDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRegister" :loading="registering">
          注册
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  OfficeBuilding,
  User,
  Lock,
  ChatDotRound,
  Link,
  Calendar,
  DataAnalysis
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const registering = ref(false)
const rememberMe = ref(false)
const showRegisterDialog = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  full_name: '',
  company_name: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const demoAccounts = [
  { username: 'admin', password: 'admin123', label: '管理员' },
  { username: 'manager', password: 'manager123', label: '经理' },
  { username: 'demo', password: 'demo123', label: '演示用户' },
  { username: 'employee', password: 'employee123', label: '员工' }
]

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ]
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入全名', trigger: 'blur' }
  ],
  company_name: [
    { required: true, message: '请输入公司名称', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入联系电话', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    loading.value = true
    
    const result = await authStore.login(loginForm.username, loginForm.password)
    
    if (result.success) {
      ElMessage.success(`欢迎回来，${authStore.user?.full_name || loginForm.username}！`)
      router.push('/')
    } else {
      ElMessage.error(result.error || '登录失败')
    }
    
  } catch (error: any) {
    console.error('登录失败:', error)
    ElMessage.error('登录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  try {
    await registerFormRef.value.validate()
    registering.value = true
    
    const result = await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      full_name: registerForm.full_name,
      company_name: registerForm.company_name,
      phone: registerForm.phone,
      password: registerForm.password
    })
    
    if (result.success) {
      ElMessage.success('注册成功！请登录')
      showRegisterDialog.value = false
      resetRegisterForm()
    } else {
      ElMessage.error(result.error || '注册失败')
    }
    
  } catch (error: any) {
    console.error('注册失败:', error)
    ElMessage.error('注册失败，请稍后重试')
  } finally {
    registering.value = false
  }
}

const fillDemoAccount = (account: { username: string; password: string }) => {
  loginForm.username = account.username
  loginForm.password = account.password
}

const resetRegisterForm = () => {
  registerForm.username = ''
  registerForm.email = ''
  registerForm.full_name = ''
  registerForm.password = ''
  registerForm.confirmPassword = ''
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: 10%;
  animation-delay: 2s;
}

.shape-3 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 20%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 16px;
}

.logo-icon {
  font-size: 32px;
  color: #667eea;
}

.logo-text {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.login-form {
  margin-bottom: 24px;
}

.login-input :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e4e7ed;
  transition: all 0.3s ease;
}

.login-input :deep(.el-input__wrapper):hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.login-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  border-color: #667eea;
}

.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.login-button {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.demo-section {
  margin-top: 20px;
  text-align: center;
}

.demo-accounts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.register-section {
  margin-top: 20px;
  text-align: center;
}

.register-btn {
  width: 100%;
}

:deep(.el-divider__text) {
  background-color: rgba(255, 255, 255, 0.95);
  color: #909399;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 16px;
  }
  
  .login-card {
    padding: 32px 24px;
  }
  
  .bg-shape {
    display: none;
  }
}

@media (max-width: 480px) {
  .login-card {
    padding: 24px 20px;
  }
  
  .logo {
    flex-direction: column;
    gap: 8px;
  }
  
  .logo-text {
    font-size: 20px;
  }
  
  .demo-accounts {
    flex-direction: column;
  }
}
</style>