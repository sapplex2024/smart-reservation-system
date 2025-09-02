<template>
  <div class="logs-view">
    <div class="logs-header">
      <h1>日志管理</h1>
      <div class="header-actions">
        <el-button @click="refreshLogs" :disabled="loading" :icon="Refresh">
          刷新
        </el-button>
        <el-button @click="showExportModal = true" :disabled="loading" :icon="Download">
          导出
        </el-button>
        <el-button @click="showCleanupModal = true" type="warning" :disabled="loading" :icon="Delete">
          清理
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <el-card shadow="hover">
        <div class="stat-item">
          <el-icon color="#409eff" size="24"><Document /></el-icon>
          <div>
            <h3>{{ stats.total_logs }}</h3>
            <p>总日志数</p>
          </div>
        </div>
      </el-card>
      
      <el-card shadow="hover">
        <div class="stat-item">
          <el-icon color="#e6a23c" size="24"><Warning /></el-icon>
          <div>
            <h3>{{ stats.recent_errors }}</h3>
            <p>最近错误</p>
          </div>
        </div>
      </el-card>
      
      <el-card shadow="hover">
        <div class="stat-item">
          <el-icon color="#67c23a" size="24"><View /></el-icon>
          <div>
            <h3>{{ stats.level_stats.ACCESS || 0 }}</h3>
            <p>访问日志</p>
          </div>
        </div>
      </el-card>
      
      <el-card shadow="hover">
        <div class="stat-item">
          <el-icon color="#909399" size="24"><Lock /></el-icon>
          <div>
            <h3>{{ stats.level_stats.SECURITY || 0 }}</h3>
            <p>安全日志</p>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 过滤器 -->
    <el-card>
      <template #header>
        <span>筛选条件</span>
      </template>
      <div class="filters-grid">
        <el-form-item label="日志级别">
          <el-select v-model="filters.level" placeholder="选择日志级别" clearable>
            <el-option label="全部级别" value="" />
            <el-option v-for="level in levels" :key="level" :label="level" :value="level" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="日志类别">
          <el-select v-model="filters.category" placeholder="选择日志类别" clearable>
            <el-option label="全部类别" value="" />
            <el-option v-for="category in categories" :key="category" :label="category" :value="category" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="开始时间">
          <el-date-picker 
            v-model="filters.start_date" 
            type="datetime" 
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        
        <el-form-item label="结束时间">
          <el-date-picker 
            v-model="filters.end_date" 
            type="datetime" 
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </div>
      
      <div class="filter-actions">
        <el-button type="primary" @click="applyFilters" :disabled="loading" :icon="Search">
          搜索
        </el-button>
        <el-button @click="clearFilters" :icon="Close">
          清除
        </el-button>
      </div>
    </el-card>

    <!-- 日志列表 -->
    <el-card>
      <template #header>
        <span>日志记录</span>
      </template>
      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" size="24"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="logs.length === 0" class="empty-state">
        <el-icon size="48" color="#909399"><Document /></el-icon>
        <p>暂无日志记录</p>
      </div>
        
        <div v-else class="logs-list">
          <div 
            v-for="log in logs" 
            :key="log.id" 
            class="log-item"
            :class="`log-${log.level.toLowerCase()}`"
          >
            <div class="log-header">
              <div class="log-level">
                <el-icon 
                  :color="getLevelColor(log.level)"
                  size="16"
                >
                  <component :is="getLevelIcon(log.level)" />
                </el-icon>
                <span class="level-text">{{ log.level }}</span>
              </div>
              <div class="log-time">{{ formatTime(log.created_at) }}</div>
            </div>
            
            <div class="log-content">
              <div class="log-message">{{ log.message }}</div>
              <div class="log-meta">
                <span v-if="log.category" class="log-category">
                  分类: {{ log.category }}
                </span>
                <span v-if="log.user_id" class="log-user">
                  用户ID: {{ log.user_id }}
                </span>
              </div>
              
              <div v-if="log.extra_data" class="log-extra">
                <el-button 
                  text 
                  size="small" 
                  @click="toggleExtraData(log.id)"
                  :icon="ArrowDown"
                >
                  详细信息
                </el-button>
                <div v-if="expandedLogs.has(log.id)" class="extra-data">
                  <pre>{{ JSON.stringify(parseExtraData(log.extra_data), null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div v-if="logs.length > 0" class="pagination">
          <el-button 
            text 
            :disabled="currentPage === 1" 
            @click="changePage(currentPage - 1)"
            :icon="ArrowLeft"
          >
            上一页
          </el-button>
          
          <span class="page-info">第 {{ currentPage }} 页</span>
          
          <el-button 
            text 
            :disabled="logs.length < pageSize" 
            @click="changePage(currentPage + 1)"
          >
            下一页
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
    </el-card>

    <!-- 导出模态框 -->
    <el-dialog v-model="showExportModal" title="导出日志" width="500px">
      <el-form class="export-form">
        <el-form-item label="导出格式">
          <el-select v-model="exportFormat" placeholder="选择格式">
            <el-option label="JSON" value="json" />
            <el-option label="CSV" value="csv" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="开始时间">
          <el-date-picker 
            v-model="exportFilters.start_date" 
            type="datetime" 
            placeholder="选择开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
        
        <el-form-item label="结束时间">
          <el-date-picker 
            v-model="exportFilters.end_date" 
            type="datetime" 
            placeholder="选择结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="export-actions">
          <el-button type="primary" @click="handleExport" :disabled="loading" :icon="Download">
            导出
          </el-button>
          <el-button @click="showExportModal = false">
            取消
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 清理模态框 -->
    <el-dialog v-model="showCleanupModal" title="清理日志" width="400px">
      <el-form class="cleanup-form">
        <el-form-item label="保留天数">
          <el-input-number 
            v-model="daysToKeep" 
            placeholder="保留天数"
            :min="1"
            :max="365"
          />
        </el-form-item>
        
        <el-alert
          type="warning"
          :closable="false"
          show-icon
        >
          将删除 {{ daysToKeep }} 天前的所有日志记录，此操作不可恢复。
        </el-alert>
      </el-form>
      
      <template #footer>
        <div class="cleanup-actions">
          <el-button type="warning" @click="handleCleanup" :disabled="loading" :icon="Delete">
            确认清理
          </el-button>
          <el-button @click="showCleanupModal = false">
            取消
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh,
  Download,
  Delete,
  Document,
  Warning,
  View,
  Lock,
  Search,
  Close,
  DocumentCopy,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Loading,
  InfoFilled,
  CircleCloseFilled,
  QuestionFilled
} from '@element-plus/icons-vue'
import { useLogs, type LogFilters } from '@/composables/useLogs'

const {
  logs,
  stats,
  levels,
  categories,
  loading,
  error,
  getLogs,
  getLogStats,
  exportLogs,
  cleanupOldLogs,
  getLogLevels,
  getLogCategories,
  getLevelColor,
  getLevelIcon,
  formatTime,
  parseExtraData
} = useLogs()

// 响应式数据
const filters = reactive<LogFilters>({
  level: '',
  category: '',
  start_date: '',
  end_date: ''
})

const exportFilters = reactive<LogFilters>({
  start_date: '',
  end_date: ''
})

const showExportModal = ref(false)
const showCleanupModal = ref(false)
const exportFormat = ref<'json' | 'csv'>('json')
const daysToKeep = ref(30)
const currentPage = ref(1)
const pageSize = ref(50)
const expandedLogs = ref(new Set<number>())

// 方法
const refreshLogs = async () => {
  try {
    await Promise.all([
      getLogs(filters, pageSize.value, (currentPage.value - 1) * pageSize.value),
      getLogStats(),
      getLogLevels(),
      getLogCategories()
    ])
  } catch (err) {
    ElMessage.error('刷新失败: ' + (err instanceof Error ? err.message : '未知错误'))
  }
}

const applyFilters = async () => {
  currentPage.value = 1
  try {
    await getLogs(filters, pageSize.value, 0)
  } catch (err) {
    ElMessage.error('搜索失败: ' + (err instanceof Error ? err.message : '未知错误'))
  }
}

const clearFilters = () => {
  filters.level = ''
  filters.category = ''
  filters.start_date = ''
  filters.end_date = ''
  applyFilters()
}

const changePage = async (page: number) => {
  currentPage.value = page
  try {
    await getLogs(filters, pageSize.value, (page - 1) * pageSize.value)
  } catch (err) {
    ElMessage.error('加载失败: ' + (err instanceof Error ? err.message : '未知错误'))
  }
}

const handleExport = async () => {
  try {
    await exportLogs(exportFormat.value, exportFilters)
    showExportModal.value = false
    ElMessage.success('导出成功')
  } catch (err) {
    ElMessage.error('导出失败: ' + (err instanceof Error ? err.message : '未知错误'))
  }
}

const handleCleanup = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${daysToKeep.value} 天前的所有日志吗？此操作不可恢复。`,
      '确认清理',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const result = await cleanupOldLogs(daysToKeep.value)
    showCleanupModal.value = false
    ElMessage.success(`清理完成，删除了 ${result.deleted_count} 条日志`)
    
    // 刷新数据
    await refreshLogs()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('清理失败: ' + (err instanceof Error ? err.message : '未知错误'))
    }
  }
}

const toggleExtraData = (logId: number) => {
  if (expandedLogs.value.has(logId)) {
    expandedLogs.value.delete(logId)
  } else {
    expandedLogs.value.add(logId)
  }
}

// 生命周期
onMounted(() => {
  refreshLogs()
})
</script>

<style scoped>
.logs-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.logs-header h1 {
  margin: 0;
  color: var(--ion-color-primary);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-item ion-icon {
  font-size: 2rem;
}

.stat-item h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: bold;
}

.stat-item p {
  margin: 0;
  color: var(--ion-color-medium);
  font-size: 0.9rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 15px;
}

.filter-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  gap: 15px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  gap: 15px;
  color: var(--ion-color-medium);
}

.empty-state ion-icon {
  font-size: 4rem;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.log-item {
  border: 1px solid var(--ion-color-light);
  border-radius: 8px;
  padding: 15px;
  background: var(--ion-color-light-tint);
}

.log-item.log-error {
  border-left: 4px solid var(--ion-color-danger);
}

.log-item.log-warning {
  border-left: 4px solid var(--ion-color-warning);
}

.log-item.log-info {
  border-left: 4px solid var(--ion-color-primary);
}

.log-item.log-access {
  border-left: 4px solid var(--ion-color-success);
}

.log-item.log-security {
  border-left: 4px solid var(--ion-color-secondary);
}

.log-item.log-api {
  border-left: 4px solid var(--ion-color-tertiary);
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.log-level {
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-text {
  font-weight: bold;
  font-size: 0.9rem;
}

.log-time {
  color: var(--ion-color-medium);
  font-size: 0.85rem;
}

.log-message {
  font-size: 1rem;
  line-height: 1.4;
  margin-bottom: 8px;
}

.log-meta {
  display: flex;
  gap: 15px;
  font-size: 0.85rem;
  color: var(--ion-color-medium);
  margin-bottom: 8px;
}

.log-extra {
  margin-top: 10px;
}

.extra-data {
  margin-top: 10px;
  padding: 10px;
  background: var(--ion-color-light);
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.8rem;
  overflow-x: auto;
}

.extra-data pre {
  margin: 0;
  white-space: pre-wrap;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 20px;
  padding: 20px;
}

.page-info {
  font-weight: bold;
  color: var(--ion-color-primary);
}

.export-form,
.cleanup-form {
  padding: 20px;
}

.export-actions,
.cleanup-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .logs-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .filters-grid {
    grid-template-columns: 1fr;
  }
  
  .log-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .log-meta {
    flex-direction: column;
    gap: 5px;
  }
}
</style>