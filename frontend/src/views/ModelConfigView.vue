<template>
  <div class="model-config-view">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>模型配置管理</span>
        </div>
      </template>
      
      <div class="config-section">
        <h3>API连接配置</h3>
        <el-form :model="apiConfig" label-width="120px">
          <el-form-item label="API密钥">
            <el-input 
              v-model="apiConfig.apiKey" 
              placeholder="请输入API密钥"
              type="password"
              show-password
            />
          </el-form-item>
          <el-form-item label="API地址">
            <el-input 
              v-model="apiConfig.apiUrl" 
              placeholder="请输入API地址"
            />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input 
              v-model="apiConfig.modelName" 
              placeholder="请输入模型名称"
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              @click="testConnection" 
              :loading="testing"
            >
              测试连接
            </el-button>
            <el-button 
              type="success" 
              @click="saveConfig" 
              :loading="saving"
            >
              保存配置
            </el-button>
          </el-form-item>
        </el-form>
        <div v-if="connectionResult" class="result">
          <el-tag :type="connectionResult.success ? 'success' : 'danger'">
            {{ connectionResult.message }}
          </el-tag>
        </div>
      </div>
      
      <el-divider />
      
      <div class="config-section">
        <h3>模型测试</h3>
        <el-input 
          v-model="testText" 
          placeholder="输入测试文本"
          style="margin-bottom: 10px;"
        />
        <div class="button-group">
          <el-button 
            type="success" 
            @click="testModel" 
            :loading="modelTesting"
            :disabled="!testText.trim()"
          >
            测试模型
          </el-button>
        </div>
        <div v-if="modelResult" class="result">
          <el-tag :type="modelResult.success ? 'success' : 'danger'">
            {{ modelResult.message }}
          </el-tag>
        </div>
        <div v-if="modelResponse" class="model-response">
          <h4>模型响应：</h4>
          <el-input 
            v-model="modelResponse" 
            type="textarea" 
            :rows="4" 
            readonly
          />
        </div>
      </div>
      
      <el-divider />
      
      <div class="config-section">
        <h3>模型管理</h3>
        <div class="button-group">
          <el-button 
            type="primary" 
            @click="loadModels" 
            :loading="modelsLoading"
          >
            刷新模型列表
          </el-button>
          <el-button 
            type="success" 
            @click="showAddModel = true"
          >
            添加模型
          </el-button>
        </div>
        
        <el-table 
          :data="models" 
          style="width: 100%; margin-top: 15px;"
          v-loading="modelsLoading"
        >
          <el-table-column prop="name" label="模型名称" />
          <el-table-column prop="provider" label="提供商" />
          <el-table-column prop="status" label="状态">
            <template #default="scope">
              <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
                {{ scope.row.status === 'active' ? '激活' : '未激活' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button 
                size="small" 
                type="primary" 
                @click="setActiveModel(scope.row)"
                :disabled="scope.row.status === 'active'"
              >
                激活
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click="deleteModel(scope.row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
    
    <!-- 添加模型对话框 -->
    <el-dialog 
      v-model="showAddModel" 
      title="添加模型" 
      width="500px"
    >
      <el-form :model="newModel" label-width="100px">
        <el-form-item label="模型名称" required>
          <el-input v-model="newModel.name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="提供商" required>
          <el-select v-model="newModel.provider" placeholder="请选择提供商">
            <el-option label="OpenAI" value="openai" />
            <el-option label="硅基流动" value="siliconflow" />
            <el-option label="阿里云" value="aliyun" />
            <el-option label="百度" value="baidu" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="API地址" required>
          <el-input v-model="newModel.apiUrl" placeholder="请输入API地址" />
        </el-form-item>
        <el-form-item label="API密钥" required>
          <el-input 
            v-model="newModel.apiKey" 
            placeholder="请输入API密钥"
            type="password"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddModel = false">取消</el-button>
        <el-button type="primary" @click="addModel" :loading="adding">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// 接口定义
interface ApiConfig {
  apiKey: string
  apiUrl: string
  modelName: string
}

interface Model {
  id: string
  name: string
  provider: string
  apiUrl: string
  apiKey: string
  status: 'active' | 'inactive'
  createdAt: string
}

// 响应式数据
const testing = ref(false)
const saving = ref(false)
const modelTesting = ref(false)
const modelsLoading = ref(false)
const adding = ref(false)
const showAddModel = ref(false)

const testText = ref('你好，这是一个模型测试。')
const modelResponse = ref('')
const models = ref<Model[]>([])

const apiConfig = ref<ApiConfig>({
  apiKey: '',
  apiUrl: 'https://api.siliconflow.cn/v1/chat/completions',
  modelName: 'Qwen/Qwen2.5-7B-Instruct'
})

const newModel = ref<Partial<Model>>({
  name: '',
  provider: '',
  apiUrl: '',
  apiKey: ''
})

const connectionResult = ref<{success: boolean, message: string} | null>(null)
const modelResult = ref<{success: boolean, message: string} | null>(null)

// 测试API连接
const testConnection = async () => {
  if (!apiConfig.value.apiKey || !apiConfig.value.apiUrl) {
    ElMessage.warning('请先填写API配置信息')
    return
  }
  
  testing.value = true
  connectionResult.value = null
  
  try {
    const response = await axios.post(apiConfig.value.apiUrl, {
      model: apiConfig.value.modelName,
      messages: [{ role: 'user', content: '测试连接' }],
      max_tokens: 10
    }, {
      headers: {
        'Authorization': `Bearer ${apiConfig.value.apiKey}`,
        'Content-Type': 'application/json'
      },
      timeout: 10000
    })
    
    connectionResult.value = {
      success: true,
      message: 'API连接成功'
    }
  } catch (error: any) {
    connectionResult.value = {
      success: false,
      message: `连接失败: ${error.response?.data?.error?.message || error.message}`
    }
  } finally {
    testing.value = false
  }
}

// 保存配置
const saveConfig = async () => {
  if (!apiConfig.value.apiKey || !apiConfig.value.apiUrl || !apiConfig.value.modelName) {
    ElMessage.warning('请填写完整的配置信息')
    return
  }
  
  saving.value = true
  
  try {
    // 这里可以调用后端API保存配置
    localStorage.setItem('modelConfig', JSON.stringify(apiConfig.value))
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

// 测试模型
const testModel = async () => {
  if (!testText.value.trim()) return
  if (!apiConfig.value.apiKey || !apiConfig.value.apiUrl) {
    ElMessage.warning('请先配置并测试API连接')
    return
  }
  
  modelTesting.value = true
  modelResult.value = null
  modelResponse.value = ''
  
  try {
    const response = await axios.post(apiConfig.value.apiUrl, {
      model: apiConfig.value.modelName,
      messages: [{ role: 'user', content: testText.value }],
      max_tokens: 500
    }, {
      headers: {
        'Authorization': `Bearer ${apiConfig.value.apiKey}`,
        'Content-Type': 'application/json'
      }
    })
    
    modelResponse.value = response.data.choices[0].message.content
    modelResult.value = {
      success: true,
      message: '模型测试成功'
    }
  } catch (error: any) {
    modelResult.value = {
      success: false,
      message: `测试失败: ${error.response?.data?.error?.message || error.message}`
    }
  } finally {
    modelTesting.value = false
  }
}

// 加载模型列表
const loadModels = async () => {
  modelsLoading.value = true
  
  try {
    // 模拟数据，实际应该从后端获取
    const savedModels = localStorage.getItem('savedModels')
    if (savedModels) {
      models.value = JSON.parse(savedModels)
    } else {
      models.value = [
        {
          id: '1',
          name: 'Qwen2.5-7B-Instruct',
          provider: 'siliconflow',
          apiUrl: 'https://api.siliconflow.cn/v1/chat/completions',
          apiKey: '***',
          status: 'active' as const,
          createdAt: new Date().toISOString()
        }
      ]
    }
  } catch (error) {
    ElMessage.error('加载模型列表失败')
  } finally {
    modelsLoading.value = false
  }
}

// 添加模型
const addModel = async () => {
  if (!newModel.value.name || !newModel.value.provider || !newModel.value.apiUrl || !newModel.value.apiKey) {
    ElMessage.warning('请填写完整的模型信息')
    return
  }
  
  adding.value = true
  
  try {
    const model: Model = {
      id: Date.now().toString(),
      name: newModel.value.name!,
      provider: newModel.value.provider!,
      apiUrl: newModel.value.apiUrl!,
      apiKey: newModel.value.apiKey!,
      status: 'inactive',
      createdAt: new Date().toISOString()
    }
    
    models.value.push(model)
    localStorage.setItem('savedModels', JSON.stringify(models.value))
    
    // 重置表单
    newModel.value = {
      name: '',
      provider: '',
      apiUrl: '',
      apiKey: ''
    }
    
    showAddModel.value = false
    ElMessage.success('模型添加成功')
  } catch (error) {
    ElMessage.error('模型添加失败')
  } finally {
    adding.value = false
  }
}

// 激活模型
const setActiveModel = async (model: Model) => {
  try {
    // 将所有模型设为未激活
    models.value.forEach(m => m.status = 'inactive')
    // 激活选中的模型
    model.status = 'active'
    
    // 更新API配置
    apiConfig.value = {
      apiKey: model.apiKey,
      apiUrl: model.apiUrl,
      modelName: model.name
    }
    
    localStorage.setItem('savedModels', JSON.stringify(models.value))
    localStorage.setItem('modelConfig', JSON.stringify(apiConfig.value))
    
    ElMessage.success(`已激活模型: ${model.name}`)
  } catch (error) {
    ElMessage.error('激活模型失败')
  }
}

// 删除模型
const deleteModel = async (model: Model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = models.value.findIndex(m => m.id === model.id)
    if (index > -1) {
      models.value.splice(index, 1)
      localStorage.setItem('savedModels', JSON.stringify(models.value))
      ElMessage.success('模型删除成功')
    }
  } catch {
    // 用户取消删除
  }
}

// 初始化
onMounted(async () => {
  // 加载保存的配置
  const savedConfig = localStorage.getItem('modelConfig')
  if (savedConfig) {
    apiConfig.value = JSON.parse(savedConfig)
  }
  
  // 加载模型列表
  await loadModels()
})
</script>

<style scoped>
.model-config-view {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 18px;
}

.config-section {
  margin-bottom: 20px;
}

.config-section h3 {
  margin-bottom: 15px;
  color: #409eff;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.result {
  margin-top: 10px;
}

.model-response {
  margin-top: 15px;
}

.model-response h4 {
  margin-bottom: 10px;
  color: #67c23a;
}

.el-form-item {
  margin-bottom: 18px;
}

.el-table {
  margin-top: 15px;
}

.el-dialog .el-form-item {
  margin-bottom: 15px;
}
</style>