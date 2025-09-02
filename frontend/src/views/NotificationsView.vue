<template>
  <div class="notifications-container">
    <div class="notifications-header">
      <h1 class="page-title">
        <el-icon><Bell /></el-icon>
        通知管理
      </h1>
      
      <div class="header-actions">
        <el-button 
          type="primary" 
          :icon="Refresh" 
          @click="refreshNotifications"
          :loading="loading"
        >
          刷新
        </el-button>
        
        <el-button 
          v-if="unreadCount > 0"
          type="success" 
          :icon="Check" 
          @click="handleMarkAllRead"
        >
          全部标记已读
        </el-button>
        
        <el-button 
          type="info" 
          :icon="DataAnalysis" 
          @click="showStats = !showStats"
        >
          统计信息
        </el-button>
        
        <el-button 
          type="warning" 
          :icon="Plus" 
          @click="createTest"
        >
          测试通知
        </el-button>
      </div>
    </div>
    
    <!-- 统计信息卡片 -->
    <el-card v-if="showStats && stats" class="stats-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>通知统计</span>
          <el-button type="text" :icon="Close" @click="showStats = false" />
        </div>
      </template>
      
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-number">{{ stats.total_count }}</div>
          <div class="stat-label">总通知数</div>
        </div>
        <div class="stat-item">
          <div class="stat-number unread">{{ stats.unread_count }}</div>
          <div class="stat-label">未读通知</div>
        </div>
        <div class="stat-item">
          <div class="stat-number read">{{ stats.read_count }}</div>
          <div class="stat-label">已读通知</div>
        </div>
      </div>
      
      <el-divider>按类型统计</el-divider>
      
      <div class="type-stats">
        <div 
          v-for="(stat, type) in stats.type_stats" 
          :key="type"
          class="type-stat-item"
        >
          <div class="type-name">{{ getTypeLabel(type) }}</div>
          <div class="type-numbers">
            <span class="total">总计: {{ stat.total }}</span>
            <span class="unread">未读: {{ stat.unread }}</span>
          </div>
        </div>
      </div>
    </el-card>
    
    <!-- 过滤器 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <el-radio-group v-model="filterType" @change="handleFilterChange">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="unread">未读</el-radio-button>
          <el-radio-button label="read">已读</el-radio-button>
        </el-radio-group>
        
        <el-select 
          v-model="selectedType" 
          placeholder="按类型筛选" 
          clearable
          @change="handleFilterChange"
          style="width: 150px"
        >
          <el-option label="状态变更" value="status_change" />
          <el-option label="预约提醒" value="reminder" />
          <el-option label="审批请求" value="approval_request" />
          <el-option label="取消通知" value="cancellation" />
        </el-select>
      </div>
    </el-card>
    
    <!-- 通知列表 -->
    <el-card class="notifications-list" shadow="never">
      <div v-if="loading && notifications.length === 0" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <el-empty 
        v-else-if="filteredNotifications.length === 0" 
        description="暂无通知"
        :image-size="100"
      />
      
      <div v-else class="notification-items">
        <div 
          v-for="notification in filteredNotifications" 
          :key="notification.id"
          class="notification-item"
          :class="{ 'unread': !notification.read }"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-icon">
            <el-icon :class="getTypeIconClass(notification.type)">
              <component :is="getTypeIcon(notification.type)" />
            </el-icon>
          </div>
          
          <div class="notification-content">
            <div class="notification-header">
              <h4 class="notification-title">{{ notification.title }}</h4>
              <div class="notification-meta">
                <el-tag 
                  :type="getTypeTagType(notification.type)" 
                  size="small"
                >
                  {{ getTypeLabel(notification.type) }}
                </el-tag>
                <span class="notification-time">
                  {{ formatNotificationTime(notification.created_at) }}
                </span>
              </div>
            </div>
            
            <p class="notification-message">{{ notification.message }}</p>
            
            <div v-if="notification.data" class="notification-data">
              <el-descriptions :column="2" size="small" border>
                <el-descriptions-item 
                  v-for="(value, key) in notification.data" 
                  :key="key"
                  :label="key"
                >
                  {{ value }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          
          <div class="notification-actions">
            <el-button 
              v-if="!notification.read"
              type="primary" 
              size="small" 
              :icon="Check"
              @click.stop="markAsRead(notification.id)"
            >
              标记已读
            </el-button>
            
            <el-dropdown @command="handleActionCommand">
              <el-button type="text" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    :command="{ action: 'desktop', notification }"
                  >
                    显示桌面通知
                  </el-dropdown-item>
                  <el-dropdown-item 
                    :command="{ action: 'inapp', notification }"
                  >
                    显示应用通知
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
      
      <!-- 加载更多 -->
      <div v-if="notifications.length > 0" class="load-more">
        <el-button 
          type="text" 
          @click="loadMore"
          :loading="loading"
        >
          加载更多
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  Bell, 
  Refresh, 
  Check, 
  DataAnalysis, 
  Plus, 
  Close,
  MoreFilled,
  InfoFilled,
  WarningFilled,
  SuccessFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNotifications } from '@/composables/useNotifications'
import type { Notification } from '@/composables/useNotifications'

const {
  notifications,
  unreadCount,
  loading,
  stats,
  fetchNotifications,
  fetchStats,
  markAsRead,
  markAllAsRead,
  createTestNotification,
  showDesktopNotification,
  showInAppNotification,
  formatNotificationTime
} = useNotifications()

// 本地状态
const showStats = ref(false)
const filterType = ref('all')
const selectedType = ref('')
const currentLimit = ref(20)

// 计算属性
const filteredNotifications = computed(() => {
  let filtered = notifications.value
  
  // 按读取状态过滤
  if (filterType.value === 'unread') {
    filtered = filtered.filter(n => !n.read)
  } else if (filterType.value === 'read') {
    filtered = filtered.filter(n => n.read)
  }
  
  // 按类型过滤
  if (selectedType.value) {
    filtered = filtered.filter(n => n.type === selectedType.value)
  }
  
  return filtered
})

// 方法
const refreshNotifications = async () => {
  await fetchNotifications(false, currentLimit.value)
  await fetchStats()
}

const handleFilterChange = () => {
  // 重新获取通知
  const unreadOnly = filterType.value === 'unread'
  fetchNotifications(unreadOnly, currentLimit.value)
}

const handleMarkAllRead = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要将所有 ${unreadCount.value} 条未读通知标记为已读吗？`,
      '批量操作确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await markAllAsRead()
    await refreshNotifications()
  } catch {
    // 用户取消操作
  }
}

const createTest = async () => {
  await createTestNotification()
}

const handleNotificationClick = async (notification: Notification) => {
  if (!notification.read) {
    await markAsRead(notification.id)
  }
}

const handleActionCommand = ({ action, notification }: { action: string, notification: Notification }) => {
  if (action === 'desktop') {
    showDesktopNotification(notification)
  } else if (action === 'inapp') {
    showInAppNotification(notification)
  }
}

const loadMore = () => {
  currentLimit.value += 20
  fetchNotifications(filterType.value === 'unread', currentLimit.value)
}

// 工具方法
const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'status_change': '状态变更',
    'reminder': '预约提醒',
    'approval_request': '审批请求',
    'cancellation': '取消通知'
  }
  return labels[type] || type
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, any> = {
    'status_change': InfoFilled,
    'reminder': WarningFilled,
    'approval_request': SuccessFilled,
    'cancellation': CircleCloseFilled
  }
  return icons[type] || InfoFilled
}

const getTypeIconClass = (type: string) => {
  const classes: Record<string, string> = {
    'status_change': 'info-icon',
    'reminder': 'warning-icon',
    'approval_request': 'success-icon',
    'cancellation': 'error-icon'
  }
  return classes[type] || 'info-icon'
}

const getTypeTagType = (type: string) => {
  const types: Record<string, any> = {
    'status_change': 'info',
    'reminder': 'warning',
    'approval_request': 'success',
    'cancellation': 'danger'
  }
  return types[type] || 'info'
}

// 生命周期
onMounted(async () => {
  await refreshNotifications()
})
</script>

<style scoped>
.notifications-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.stat-number.unread {
  color: #f56c6c;
}

.stat-number.read {
  color: #67c23a;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.type-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.type-stat-item {
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  background: #fff;
}

.type-name {
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.type-numbers {
  display: flex;
  gap: 15px;
  font-size: 14px;
}

.type-numbers .total {
  color: #409eff;
}

.type-numbers .unread {
  color: #f56c6c;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notifications-list {
  min-height: 400px;
}

.loading-container {
  padding: 20px;
}

.notification-items {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 20px;
  border-bottom: 1px solid #ebeef5;
  cursor: pointer;
  transition: all 0.3s ease;
}

.notification-item:hover {
  background-color: #f8f9fa;
}

.notification-item.unread {
  background-color: #f0f9ff;
  border-left: 4px solid #409eff;
}

.notification-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: #f0f0f0;
}

.notification-icon .info-icon {
  color: #409eff;
}

.notification-icon .warning-icon {
  color: #e6a23c;
}

.notification-icon .success-icon {
  color: #67c23a;
}

.notification-icon .error-icon {
  color: #f56c6c;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.notification-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.notification-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.notification-message {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.notification-data {
  margin-top: 10px;
}

.notification-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.load-more {
  text-align: center;
  padding: 20px;
  border-top: 1px solid #ebeef5;
}

@media (max-width: 768px) {
  .notifications-container {
    padding: 10px;
  }
  
  .notifications-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .filter-row {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .type-stats {
    grid-template-columns: 1fr;
  }
  
  .notification-item {
    flex-direction: column;
    gap: 10px;
  }
  
  .notification-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .notification-actions {
    align-self: stretch;
    justify-content: center;
  }
}
</style>