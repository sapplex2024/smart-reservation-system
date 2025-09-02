<template>
  <div id="app">
    <el-container class="app-container">
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="app-title">
            <el-icon><ChatDotRound /></el-icon>
            智能预约系统
          </h1>
          <div class="header-right">
            <nav class="nav-menu" v-if="authStore.isAuthenticated">
              <router-link to="/" class="nav-link">
                <el-icon><ChatDotRound /></el-icon>
                对话
              </router-link>
              <router-link to="/reservation" class="nav-link">预约</router-link>
              <router-link to="/notifications" class="nav-link">
                <el-icon><Bell /></el-icon>
                通知
              </router-link>
              <router-link to="/reports" class="nav-link">
                <el-icon><DataAnalysis /></el-icon>
                报表
              </router-link>
              <router-link to="/settings" class="nav-link">
                <el-icon><Setting /></el-icon>
                设置
              </router-link>
              <router-link to="/logs" class="nav-link">
                <el-icon><Document /></el-icon>
                日志
              </router-link>
              <router-link to="/room-management" class="nav-link">会议室</router-link>
            </nav>
            
            <!-- 用户信息和退出按钮 -->
            <div class="user-section" v-if="authStore.isAuthenticated">
              <el-dropdown @command="handleUserCommand">
                <span class="user-info">
                  <el-icon><User /></el-icon>
                  {{ authStore.user?.full_name || authStore.user?.username }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="profile">
                      <el-icon><User /></el-icon>
                      个人资料
                    </el-dropdown-item>
                    <el-dropdown-item command="logout" divided>
                      <el-icon><SwitchButton /></el-icon>
                      退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            
            <!-- 未登录时显示登录链接 -->
            <div class="login-section" v-else>
              <router-link to="/login" class="nav-link login-btn">
                <el-icon><User /></el-icon>
                登录
              </router-link>
            </div>
          </div>
        </div>
      </el-header>
      
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Bell, DataAnalysis, Setting, Document, User, ArrowDown, SwitchButton } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 处理用户下拉菜单命令
const handleUserCommand = (command: string) => {
  if (command === 'logout') {
    handleLogout()
  } else if (command === 'profile') {
    // 可以添加个人资料页面
    ElMessage.info('个人资料功能开发中')
  }
}

// 退出登录
const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 初始化认证状态
onMounted(() => {
  authStore.init()
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 15px;
  max-width: 1400px;
  margin: 0 auto;
}

.app-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-menu {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  align-items: center;
}

.user-section {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: white;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
  background-color: rgba(255, 255, 255, 0.1);
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.login-section {
  display: flex;
  align-items: center;
}

.login-btn {
  background-color: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 8px 16px !important;
  border-radius: 6px;
  font-weight: 600;
}

.login-btn:hover {
  background-color: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 6px 10px;
  border-radius: 4px;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.nav-link.router-link-active {
  background-color: rgba(255, 255, 255, 0.3);
  font-weight: 600;
}

.app-main {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .nav-link {
    font-size: 13px;
    padding: 5px 8px;
  }
  
  .nav-menu {
    gap: 6px;
  }
  
  .header-right {
    gap: 15px;
  }
}

@media (max-width: 1000px) {
  .app-title {
    font-size: 18px;
  }
  
  .nav-link {
    font-size: 12px;
    padding: 4px 6px;
  }
  
  .nav-menu {
    gap: 4px;
  }
  
  .header-content {
    padding: 0 10px;
  }
  
  .header-right {
    gap: 10px;
  }
  
  .user-info {
    padding: 6px 10px;
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .nav-menu {
    display: none;
  }
  
  .header-right {
    gap: 8px;
  }
  
  .user-info {
    padding: 6px 8px;
    font-size: 12px;
  }
}
</style>