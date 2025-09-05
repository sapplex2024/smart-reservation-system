<template>
  <div class="silicon-flow-view">
    <div class="page-header">
      <h1 class="page-title">硅基流动模型管理</h1>
      <p class="page-subtitle">管理硅基流动AI模型和API配置</p>
    </div>
    
    <div class="container">
      <!-- 统计卡片 -->
      <div class="stats-grid" v-if="usage">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-value">{{ usage.total_requests.toLocaleString() }}</div>
            <div class="stat-label">总请求数</div>
          </div>
        </el-card>
        
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-value">{{ usage.total_tokens.toLocaleString() }}</div>
            <div class="stat-label">总Token数</div>
          </div>
        </el-card>
        
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-value">¥{{ usage.total_cost.toFixed(2) }}</div>
            <div class="stat-label">总费用</div>
          </div>
        </el-card>
        
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-value">{{ usage.today_requests }}</div>
            <div class="stat-label">今日请求</div>
          </div>
        </el-card>
      </div>
      
      <!-- 功能按钮 -->
      <div class="action-buttons">
        <el-button type="primary" @click="openConfigModal" :icon="Setting">
          API配置
        </el-button>
        
        <el-button type="success" @click="openTestModal" :icon="Lightning">
          连接测试
        </el-button>
          
          <el-button @click="refreshData" :icon="Refresh">
            刷新数据
          </el-button>
        </div>
        
        <!-- 模型列表 -->
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>可用模型</h3>
              <p>硅基流动支持的AI模型列表</p>
            </div>
          </template>
          
          <div v-if="loading" class="loading-container" v-loading="loading">
            <p>加载中...</p>
          </div>
          
          <div v-else-if="models.length === 0" class="empty-state">
            <el-icon size="48"><CloudOffline /></el-icon>
            <p>暂无可用模型</p>
          </div>
            
            <div v-else class="models-grid">
              <div 
                v-for="model in models" 
                :key="model.id" 
                class="model-card"
                :class="{ 'selected': config.default_model === model.id }"
                @click="selectModel(model.id)"
              >
                <div class="model-header">
                  <div class="model-info">
                    <el-icon><Cpu /></el-icon>
                    <div>
                      <h3>{{ model.name }}</h3>
                      <el-tag :type="getProviderColor(model.provider)" size="small">
                        {{ model.provider }}
                      </el-tag>
                    </div>
                  </div>
                  
                  <el-checkbox 
                    :model-value="config.default_model === model.id"
                    @change="selectModel(model.id)"
                  ></el-checkbox>
                </div>
                
                <p class="model-description">{{ model.description }}</p>
                
                <div class="model-details">
                  <div class="detail-item">
                    <span class="label">最大Token:</span>
                    <span class="value">{{ model.max_tokens.toLocaleString() }}</span>
                  </div>
                  
                  <div class="detail-item" v-if="model.pricing">
                    <span class="label">输入价格:</span>
                    <span class="value">{{ formatPrice(model.pricing.input) }}</span>
                  </div>
                  
                  <div class="detail-item" v-if="model.pricing">
                    <span class="label">输出价格:</span>
                    <span class="value">{{ formatPrice(model.pricing.output) }}</span>
                  </div>
                </div>
              </div>
            </div>
        </el-card>
        
        <!-- 热门模型统计 -->
        <el-card v-if="usage && usage.popular_models.length > 0" shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>热门模型</h3>
              <p>使用频率统计</p>
            </div>
          </template>
            <div class="popular-models">
              <div 
                v-for="model in usage.popular_models" 
                :key="model.model"
                class="popular-model-item"
              >
                <div class="model-name">{{ model.model }}</div>
                <div class="usage-bar">
                  <div 
                    class="usage-fill" 
                    :style="{ width: model.percentage + '%' }"
                  ></div>
                </div>
                <div class="usage-stats">
                  <span>{{ model.requests }} 次</span>
                  <span>{{ model.percentage }}%</span>
                </div>
              </div>
            </div>
        </el-card>
      </div>
      
      <!-- API配置对话框 -->
      <el-dialog
        v-model="configModalOpen"
        title="API配置"
        width="500px"
        @close="configModalOpen = false"
      >
        <el-form :model="tempConfig" label-width="100px">
          <el-form-item label="API Key">
            <el-input 
              v-model="tempConfig.api_key" 
              type="password"
              placeholder="请输入硅基流动API Key"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="API地址">
            <el-input 
              v-model="tempConfig.base_url" 
              placeholder="https://api.siliconflow.cn/v1"
            />
          </el-form-item>
          
          <el-form-item label="默认模型">
            <el-select v-model="tempConfig.default_model" placeholder="请选择默认模型">
              <el-option 
                v-for="model in models" 
                :key="model.id" 
                :label="model.name"
                :value="model.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="最大Token数">
            <el-input-number 
              v-model="tempConfig.max_tokens"
              placeholder="4096"
              :min="1"
              :max="32000"
            />
          </el-form-item>
          
          <el-form-item label="温度参数">
            <el-slider 
              v-model="tempConfig.temperature" 
              :min="0" 
              :max="2" 
              :step="0.1"
              show-input
            />
          </el-form-item>
          
          <el-form-item label="流式输出">
            <el-switch v-model="tempConfig.stream" />
          </el-form-item>
        </el-form>
        
        <template #footer>
          <el-button @click="configModalOpen = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="saveConfig" 
            :loading="loading"
          >
            保存配置
          </el-button>
        </template>
      </el-dialog>
      
      <!-- API测试对话框 -->
      <el-dialog
        v-model="testModalOpen"
        title="API连接测试"
        width="600px"
        @close="testModalOpen = false"
      >
        <el-form :model="testRequest" label-width="100px">
          <el-form-item label="API Key">
            <el-input 
              v-model="testRequest.api_key" 
              type="password"
              placeholder="请输入API Key"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="API地址">
            <el-input 
              v-model="testRequest.base_url" 
              placeholder="https://api.siliconflow.cn/v1"
            />
          </el-form-item>
          
          <el-form-item label="测试模型">
            <el-select v-model="testRequest.model" placeholder="请选择模型">
              <el-option 
                v-for="model in models" 
                :key="model.id" 
                :label="model.name"
                :value="model.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="测试消息">
            <el-input 
              v-model="testRequest.message" 
              type="textarea"
              placeholder="你好，请介绍一下你自己。"
              :rows="3"
            />
          </el-form-item>
        </el-form>
        
        <template #footer>
          <el-button @click="testModalOpen = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="runTest" 
            :loading="loading"
          >
            开始测试
          </el-button>
        </template>
            
        
        <!-- 测试结果 -->
        <div v-if="testResult" class="test-result" style="margin-top: 20px;">
          <el-alert
            :type="testResult.success ? 'success' : 'error'"
            :title="testResult.success ? '测试成功' : '测试失败'"
            show-icon
          >
            <div v-if="testResult.success">
              <div class="test-stats">
                <div v-if="testResult.latency">
                  <strong>响应时间:</strong> {{ formatLatency(testResult.latency) }}
                </div>
                <div v-if="testResult.tokens_used">
                  <strong>使用Token:</strong> {{ testResult.tokens_used }}
                </div>
              </div>
              
              <div class="response-content" style="margin-top: 10px;">
                <strong>模型响应:</strong>
                <p>{{ testResult.response }}</p>
              </div>
            </div>
            
            <div v-else class="error-content">
              <strong>错误信息:</strong>
              <p>{{ testResult.error }}</p>
            </div>
          </el-alert>
        </div>
      </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting, Lightning, Refresh, Cloudy, Close,
  SuccessFilled, CircleCloseFilled, ChatDotRound,
  Document, Files, QuestionFilled
} from '@element-plus/icons-vue'

import { useSiliconFlow } from '@/composables/useSiliconFlow'
import type { SiliconFlowConfig, APITestRequest } from '@/composables/useSiliconFlow'

const {
  models, config, usage, loading, testResult,
  fetchModels, fetchConfig, updateConfig, testAPIConnection, fetchUsage,
  formatPrice, formatLatency, getProviderColor, getModelTypeIcon
} = useSiliconFlow()

// 模态框状态
const configModalOpen = ref(false)
const testModalOpen = ref(false)

// 临时配置
const tempConfig = reactive<SiliconFlowConfig>({
  api_key: '',
  base_url: 'https://api.siliconflow.cn/v1',
  default_model: 'Qwen/Qwen2.5-72B-Instruct',
  max_tokens: '4096',
  temperature: '0.7',
  stream: 'true'
})

// 测试请求
const testRequest = reactive<APITestRequest>({
  api_key: '',
  base_url: 'https://api.siliconflow.cn/v1',
  model: 'Qwen/Qwen2.5-72B-Instruct',
  message: '你好，请介绍一下你自己。',
  max_tokens: 100,
  temperature: 0.7
})

// 打开配置模态框
const openConfigModal = () => {
  // 复制当前配置到临时配置
  Object.assign(tempConfig, config.value)
  configModalOpen.value = true
}

// 打开测试模态框
const openTestModal = () => {
  // 使用当前配置初始化测试请求
  testRequest.api_key = config.value.api_key
  testRequest.base_url = config.value.base_url
  testRequest.model = config.value.default_model
  testModalOpen.value = true
}

// 选择模型
const selectModel = async (modelId: string) => {
  try {
    await updateConfig({ default_model: modelId })
    ElMessage.success('默认模型已更新')
  } catch (error) {
    ElMessage.error('更新模型失败')
  }
}

// 保存配置
const saveConfig = async () => {
  try {
    await updateConfig(tempConfig)
    configModalOpen.value = false
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  }
}

// 运行测试
const runTest = async () => {
  try {
    await testAPIConnection(testRequest)
    
    if (testResult.value?.success) {
      ElMessage.success('API连接测试成功')
    }
  } catch (error) {
    // 错误已经在testResult中处理
  }
}

// 刷新数据
const refreshData = async () => {
  try {
    await Promise.all([
      fetchModels(),
      fetchConfig(),
      fetchUsage()
    ])
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  }
}

// 页面加载时获取数据
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.container {
  padding: 16px;
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  margin: 0;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: var(--ion-color-primary);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--ion-color-medium);
  margin-top: 4px;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: var(--ion-color-medium);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: var(--ion-color-medium);
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.model-card {
  border: 2px solid var(--ion-color-light);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.model-card:hover {
  border-color: var(--ion-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.model-card.selected {
  border-color: var(--ion-color-primary);
  background-color: var(--ion-color-primary-tint);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.model-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.model-info ion-icon {
  font-size: 24px;
  color: var(--ion-color-primary);
  margin-top: 4px;
}

.model-info h3 {
  margin: 0 0 8px 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.model-description {
  color: var(--ion-color-medium);
  font-size: 0.9rem;
  line-height: 1.4;
  margin-bottom: 16px;
}

.model-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-item .label {
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}

.detail-item .value {
  font-size: 0.9rem;
  font-weight: 500;
}

.popular-models {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.popular-model-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-name {
  flex: 1;
  font-weight: 500;
  font-size: 0.9rem;
}

.usage-bar {
  flex: 2;
  height: 8px;
  background-color: var(--ion-color-light);
  border-radius: 4px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  background-color: var(--ion-color-primary);
  transition: width 0.3s ease;
}

.usage-stats {
  display: flex;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--ion-color-medium);
}

.modal-content {
  padding: 16px;
}

.modal-buttons {
  margin-top: 24px;
}

.test-result {
  margin-top: 24px;
}

.test-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 0.9rem;
}

.response-content,
.error-content {
  margin-top: 12px;
}

.response-content p,
.error-content p {
  background-color: var(--ion-color-light);
  padding: 12px;
  border-radius: 8px;
  margin: 8px 0 0 0;
  font-family: monospace;
  font-size: 0.9rem;
  line-height: 1.4;
  white-space: pre-wrap;
}

@media (max-width: 768px) {
  .models-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .action-buttons {
    grid-template-columns: 1fr;
  }
}
</style>