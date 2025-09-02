<template>
  <div class="reports-container">
    <div class="reports-header">
      <h1 class="page-title">
        <el-icon><DataAnalysis /></el-icon>
        数据报表
      </h1>
      
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="handleDateRangeChange"
        />
        
        <el-button 
          type="primary" 
          :icon="Refresh" 
          @click="refreshData"
          :loading="loading"
        >
          刷新数据
        </el-button>
        
        <el-dropdown @command="handleExport">
          <el-button type="success" :icon="Download">
            导出数据
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="excel">
                <el-icon><Document /></el-icon>
                导出Excel
              </el-dropdown-item>
              <el-dropdown-item command="csv">
                <el-icon><Tickets /></el-icon>
                导出CSV
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 快速统计卡片 -->
    <div class="quick-stats">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6" :md="6" :lg="6">
          <el-card class="stat-card today">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Calendar /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ quickStats?.today || 0 }}</div>
                <div class="stat-label">今日预约</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6" :md="6" :lg="6">
          <el-card class="stat-card week">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Timer /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ quickStats?.this_week || 0 }}</div>
                <div class="stat-label">本周预约</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6" :md="6" :lg="6">
          <el-card class="stat-card month">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Histogram /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ quickStats?.this_month || 0 }}</div>
                <div class="stat-label">本月预约</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6" :md="6" :lg="6">
          <el-card class="stat-card pending">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ quickStats?.pending_count || 0 }}</div>
                <div class="stat-label">待审批</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <!-- 预约趋势图 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>预约趋势</span>
                <el-tag type="info" size="small">最近7天</el-tag>
              </div>
            </template>
            
            <div class="chart-container" ref="trendChartRef">
              <div v-if="loading" class="chart-loading">
                <el-skeleton :rows="3" animated />
              </div>
              <div v-else-if="!dailyTrend.length" class="chart-empty">
                <el-empty description="暂无数据" :image-size="80" />
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 状态分布图 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>状态分布</span>
                <el-tag type="success" size="small">实时数据</el-tag>
              </div>
            </template>
            
            <div class="chart-container" ref="statusChartRef">
              <div v-if="loading" class="chart-loading">
                <el-skeleton :rows="3" animated />
              </div>
              <div v-else-if="!Object.keys(statusDistribution).length" class="chart-empty">
                <el-empty description="暂无数据" :image-size="80" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px">
        <!-- 热门时间段 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>热门时间段</span>
                <el-tag type="warning" size="small">TOP 5</el-tag>
              </div>
            </template>
            
            <div class="popular-times">
              <div v-if="loading" class="chart-loading">
                <el-skeleton :rows="5" animated />
              </div>
              <div v-else-if="!popularTimes.length" class="chart-empty">
                <el-empty description="暂无数据" :image-size="80" />
              </div>
              <div v-else class="time-list">
                <div 
                  v-for="(time, index) in popularTimes" 
                  :key="time.hour"
                  class="time-item"
                >
                  <div class="time-rank">{{ index + 1 }}</div>
                  <div class="time-info">
                    <div class="time-period">{{ formatHour(time.hour) }}</div>
                    <div class="time-count">{{ time.count }} 次预约</div>
                  </div>
                  <div class="time-bar">
                    <div 
                      class="time-progress" 
                      :style="{ width: `${(time.count / popularTimes[0].count) * 100}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 资源使用排行 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>资源使用排行</span>
                <el-tag type="primary" size="small">TOP 5</el-tag>
              </div>
            </template>
            
            <div class="resource-ranking">
              <div v-if="loading" class="chart-loading">
                <el-skeleton :rows="5" animated />
              </div>
              <div v-else-if="!topResources.length" class="chart-empty">
                <el-empty description="暂无数据" :image-size="80" />
              </div>
              <div v-else class="resource-list">
                <div 
                  v-for="(resource, index) in topResources" 
                  :key="resource.name"
                  class="resource-item"
                >
                  <div class="resource-rank">{{ index + 1 }}</div>
                  <div class="resource-info">
                    <div class="resource-name">{{ resource.name }}</div>
                    <div class="resource-type">{{ formatTypeLabel(resource.type) }}</div>
                  </div>
                  <div class="resource-count">{{ resource.usage_count }}</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 详细统计表格 -->
    <el-card class="table-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>详细统计</span>
          <div class="table-actions">
            <el-select 
              v-model="selectedPeriod" 
              @change="handlePeriodChange"
              style="width: 120px"
            >
              <el-option label="本周" value="week" />
              <el-option label="本月" value="month" />
              <el-option label="本季度" value="quarter" />
              <el-option label="本年" value="year" />
            </el-select>
          </div>
        </div>
      </template>
      
      <div class="statistics-grid">
        <div class="stat-section">
          <h4>状态统计</h4>
          <el-table :data="statusTableData" size="small">
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag :color="getStatusColor(row.status)" effect="light">
                  {{ formatStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="count" label="数量" align="right" />
            <el-table-column prop="percentage" label="占比" align="right">
              <template #default="{ row }">
                {{ row.percentage }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div class="stat-section">
          <h4>类型统计</h4>
          <el-table :data="typeTableData" size="small">
            <el-table-column prop="type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag type="info" effect="light">
                  {{ formatTypeLabel(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="count" label="数量" align="right" />
            <el-table-column prop="percentage" label="占比" align="right">
              <template #default="{ row }">
                {{ row.percentage }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { 
  DataAnalysis, 
  Refresh, 
  Download, 
  ArrowDown,
  Document,
  Tickets,
  Calendar,
  Timer,
  Histogram,
  Clock
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useReports } from '@/composables/useReports'
import * as echarts from 'echarts'

const {
  loading,
  statistics,
  quickStats,
  totalReservations,
  statusDistribution,
  typeDistribution,
  dailyTrend,
  popularTimes,
  topResources,
  fetchStatistics,
  fetchQuickStats,
  fetchAnalytics,
  exportExcel,
  exportCsv,
  formatStatusLabel,
  formatTypeLabel,
  getStatusColor
} = useReports()

// 本地状态
const dateRange = ref<[string, string] | null>(null)
const selectedPeriod = ref('month')
const trendChartRef = ref<HTMLElement>()
const statusChartRef = ref<HTMLElement>()

// 图表实例
let trendChart: echarts.ECharts | null = null
let statusChart: echarts.ECharts | null = null

// 计算属性
const statusTableData = computed(() => {
  const total = totalReservations.value
  if (total === 0) return []
  
  return Object.entries(statusDistribution.value).map(([status, count]) => ({
    status,
    count,
    percentage: ((count / total) * 100).toFixed(1)
  }))
})

const typeTableData = computed(() => {
  const total = totalReservations.value
  if (total === 0) return []
  
  return Object.entries(typeDistribution.value).map(([type, count]) => ({
    type,
    count,
    percentage: ((count / total) * 100).toFixed(1)
  }))
})

// 方法
const refreshData = async () => {
  await Promise.all([
    fetchQuickStats(),
    fetchStatistics(
      dateRange.value?.[0],
      dateRange.value?.[1]
    )
  ])
  
  await nextTick()
  initCharts()
}

const handleDateRangeChange = () => {
  refreshData()
}

const handlePeriodChange = async () => {
  await fetchAnalytics(selectedPeriod.value as any)
  await nextTick()
  initCharts()
}

const handleExport = async (command: string) => {
  try {
    if (command === 'excel') {
      await exportExcel(
        dateRange.value?.[0],
        dateRange.value?.[1]
      )
    } else if (command === 'csv') {
      await exportCsv(
        dateRange.value?.[0],
        dateRange.value?.[1]
      )
    }
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const formatHour = (hour: number) => {
  return `${hour.toString().padStart(2, '0')}:00 - ${(hour + 1).toString().padStart(2, '0')}:00`
}

// 初始化图表
const initCharts = () => {
  initTrendChart()
  initStatusChart()
}

// 初始化趋势图表
const initTrendChart = () => {
  if (!trendChartRef.value || !dailyTrend.value.length) return
  
  if (trendChart) {
    trendChart.dispose()
  }
  
  trendChart = echarts.init(trendChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dailyTrend.value.map(item => item.date),
      axisLine: {
        lineStyle: {
          color: '#e4e7ed'
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#e4e7ed'
        }
      }
    },
    series: [{
      name: '预约数量',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: {
        color: '#409eff',
        width: 3
      },
      itemStyle: {
        color: '#409eff'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [{
            offset: 0,
            color: 'rgba(64, 158, 255, 0.3)'
          }, {
            offset: 1,
            color: 'rgba(64, 158, 255, 0.1)'
          }]
        }
      },
      data: dailyTrend.value.map(item => item.count)
    }]
  }
  
  trendChart.setOption(option)
}

// 初始化状态分布图表
const initStatusChart = () => {
  if (!statusChartRef.value || !Object.keys(statusDistribution.value).length) return
  
  if (statusChart) {
    statusChart.dispose()
  }
  
  statusChart = echarts.init(statusChartRef.value)
  
  const data = Object.entries(statusDistribution.value).map(([status, count]) => ({
    name: formatStatusLabel(status),
    value: count,
    itemStyle: {
      color: getStatusColor(status)
    }
  }))
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: {
        fontSize: 12
      }
    },
    series: [{
      name: '预约状态',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['60%', '50%'],
      avoidLabelOverlap: false,
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: '18',
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data
    }]
  }
  
  statusChart.setOption(option)
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  trendChart?.resize()
  statusChart?.resize()
}

// 生命周期
onMounted(async () => {
  await refreshData()
  
  window.addEventListener('resize', handleResize)
})

// 清理
const cleanup = () => {
  trendChart?.dispose()
  statusChart?.dispose()
  window.removeEventListener('resize', handleResize)
}

// 组件卸载时清理
import { onUnmounted } from 'vue'
onUnmounted(cleanup)
</script>

<style scoped>
.reports-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.reports-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
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
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.quick-stats {
  margin-bottom: 20px;
}

.stat-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-card.today .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.week .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.month .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card.pending .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-card {
  height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.chart-container {
  height: 320px;
  width: 100%;
}

.chart-loading,
.chart-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.popular-times,
.resource-ranking {
  height: 320px;
  overflow-y: auto;
}

.time-list,
.resource-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 10px 0;
}

.time-item,
.resource-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.time-item:hover,
.resource-item:hover {
  background: #e9ecef;
  transform: translateX(5px);
}

.time-rank,
.resource-rank {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.time-info,
.resource-info {
  flex: 1;
  min-width: 0;
}

.time-period,
.resource-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.time-count,
.resource-type {
  font-size: 12px;
  color: #909399;
}

.resource-count {
  font-size: 18px;
  font-weight: bold;
  color: #409eff;
}

.time-bar {
  width: 60px;
  height: 6px;
  background: #e4e7ed;
  border-radius: 3px;
  overflow: hidden;
}

.time-progress {
  height: 100%;
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
  transition: width 0.3s ease;
}

.table-card {
  margin-top: 20px;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
}

.stat-section h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .reports-container {
    padding: 10px;
  }
  
  .reports-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .chart-card {
    height: 300px;
  }
  
  .chart-container {
    height: 220px;
  }
  
  .popular-times,
  .resource-ranking {
    height: 220px;
  }
  
  .statistics-grid {
    grid-template-columns: 1fr;
  }
}
</style>