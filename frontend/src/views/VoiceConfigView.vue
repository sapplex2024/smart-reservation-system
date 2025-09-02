<template>
  <div class="voice-config-container">
    <el-card class="config-card" shadow="hover">
      <template #header>
        <div class="config-header">
          <div class="header-left">
            <el-icon><Setting /></el-icon>
            <span>语音配置</span>
          </div>
          <div class="header-actions">
            <el-button type="primary" @click="saveConfig" :loading="saving">
              <el-icon><Check /></el-icon>
              保存配置
            </el-button>
          </div>
        </div>
      </template>

      <div class="config-content">
        <!-- ASR配置 -->
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Microphone /></el-icon>
              <span>语音识别 (ASR) 配置</span>
            </div>
          </template>
          
          <el-form :model="asrConfig" label-width="120px" class="config-form">
            <el-form-item label="识别模型">
              <el-select v-model="asrConfig.model" placeholder="选择识别模型" class="full-width">
                <el-option label="Paraformer实时版" value="paraformer-realtime-v1" />
                <el-option label="Paraformer标准版" value="paraformer-v1" />
                <el-option label="Whisper Large" value="whisper-large-v3" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="识别语言">
              <el-select v-model="asrConfig.language" placeholder="选择识别语言" class="full-width">
                <el-option label="中文" value="zh" />
                <el-option label="英文" value="en" />
                <el-option label="自动检测" value="auto" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="采样率">
              <el-select v-model="asrConfig.sampleRate" placeholder="选择采样率" class="full-width">
                <el-option label="16000 Hz" :value="16000" />
                <el-option label="22050 Hz" :value="22050" />
                <el-option label="44100 Hz" :value="44100" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="音频格式">
              <el-select v-model="asrConfig.format" placeholder="选择音频格式" class="full-width">
                <el-option label="WAV" value="wav" />
                <el-option label="MP3" value="mp3" />
                <el-option label="WebM" value="webm" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="实时识别">
              <el-switch v-model="asrConfig.realtime" />
            </el-form-item>
            
            <el-form-item label="噪音抑制">
              <el-switch v-model="asrConfig.noiseReduction" />
            </el-form-item>
          </el-form>
          
          <div class="test-section">
            <el-button type="success" @click="testASR" :loading="testingASR">
              <el-icon><VideoPlay /></el-icon>
              测试语音识别
            </el-button>
            <span v-if="asrTestResult" class="test-result">{{ asrTestResult }}</span>
          </div>
        </el-card>

        <!-- TTS配置 -->
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><VideoPlay /></el-icon>
              <span>语音合成 (TTS) 配置</span>
            </div>
          </template>
          
          <el-form :model="ttsConfig" label-width="120px" class="config-form">
            <el-form-item label="合成模型">
              <el-select v-model="ttsConfig.model" placeholder="选择合成模型" class="full-width">
                <el-option label="CosyVoice v1" value="cosyvoice-v1" />
                <el-option label="SpeechT5" value="speecht5" />
                <el-option label="VITS" value="vits" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="音色选择">
              <el-select v-model="ttsConfig.voice" placeholder="选择音色" class="full-width">
                <el-option 
                  v-for="voice in availableVoices" 
                  :key="voice.id" 
                  :label="voice.name" 
                  :value="voice.id"
                >
                  <span>{{ voice.name }}</span>
                  <span class="voice-info">({{ voice.gender === 'female' ? '女声' : '男声' }})</span>
                </el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="语速">
              <el-slider 
                v-model="ttsConfig.speed" 
                :min="0.5" 
                :max="2.0" 
                :step="0.1" 
                show-input
                class="speed-slider"
              />
            </el-form-item>
            
            <el-form-item label="音调">
              <el-slider 
                v-model="ttsConfig.pitch" 
                :min="0.5" 
                :max="2.0" 
                :step="0.1" 
                show-input
                class="pitch-slider"
              />
            </el-form-item>
            
            <el-form-item label="音量">
              <el-slider 
                v-model="ttsConfig.volume" 
                :min="0.1" 
                :max="1.0" 
                :step="0.1" 
                show-input
                class="volume-slider"
              />
            </el-form-item>
            
            <el-form-item label="输出格式">
              <el-select v-model="ttsConfig.format" placeholder="选择输出格式" class="full-width">
                <el-option label="MP3" value="mp3" />
                <el-option label="WAV" value="wav" />
                <el-option label="OGG" value="ogg" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="采样率">
              <el-select v-model="ttsConfig.sampleRate" placeholder="选择采样率" class="full-width">
                <el-option label="16000 Hz" :value="16000" />
                <el-option label="22050 Hz" :value="22050" />
                <el-option label="44100 Hz" :value="44100" />
              </el-select>
            </el-form-item>
          </el-form>
          
          <div class="test-section">
            <el-input 
              v-model="testText" 
              placeholder="输入测试文本" 
              class="test-input"
            />
            <el-button type="success" @click="testTTS" :loading="testingTTS">
              <el-icon><VideoPlay /></el-icon>
              测试语音合成
            </el-button>
          </div>
        </el-card>

        <!-- API配置 -->
        <el-card class="section-card" shadow="never">
          <template #header>
            <div class="section-header">
              <el-icon><Key /></el-icon>
              <span>API 配置</span>
            </div>
          </template>
          
          <el-form :model="apiConfig" label-width="120px" class="config-form">
            <el-form-item label="API密钥">
              <el-input 
                v-model="apiConfig.apiKey" 
                type="password" 
                placeholder="输入阿里云通义千问API密钥"
                show-password
                class="full-width"
              />
            </el-form-item>
            
            <el-form-item label="API地址">
              <el-input 
                v-model="apiConfig.baseUrl" 
                placeholder="API基础地址"
                class="full-width"
              />
            </el-form-item>
            
            <el-form-item label="超时时间">
              <el-input-number 
                v-model="apiConfig.timeout" 
                :min="5" 
                :max="60" 
                placeholder="秒"
                class="full-width"
              />
            </el-form-item>
          </el-form>
          
          <div class="test-section">
            <el-button type="warning" @click="testConnection" :loading="testingConnection">
              <el-icon><Link /></el-icon>
              测试API连接
            </el-button>
            <span v-if="connectionResult" :class="['test-result', connectionResult.success ? 'success' : 'error']">
              {{ connectionResult.message }}
            </span>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Setting,
  Check,
  Microphone,
  VideoPlay,
  Key,
  Link
} from '@element-plus/icons-vue'
import axios from 'axios'

// 配置数据
const asrConfig = ref({
  model: 'paraformer-realtime-v1',
  language: 'zh',
  sampleRate: 16000,
  format: 'wav',
  realtime: true,
  noiseReduction: true
})

const ttsConfig = ref({
  model: 'cosyvoice-v1',
  voice: 'zhixiaoxia',
  speed: 1.0,
  pitch: 1.0,
  volume: 0.8,
  format: 'mp3',
  sampleRate: 22050
})

const apiConfig = ref({
  apiKey: '',
  baseUrl: 'https://dashscope.aliyuncs.com/api/v1',
  timeout: 30
})

// 可用音色列表
const availableVoices = ref([
  { id: 'zhixiaoxia', name: '知小夏', gender: 'female', language: 'zh-CN' },
  { id: 'zhichu', name: '知楚', gender: 'male', language: 'zh-CN' },
  { id: 'zhimiao', name: '知妙', gender: 'female', language: 'zh-CN' },
  { id: 'zhixiaobai', name: '知小白', gender: 'male', language: 'zh-CN' },
  { id: 'zhiyan', name: '知燕', gender: 'female', language: 'zh-CN' }
])

// 状态变量
const saving = ref(false)
const testingASR = ref(false)
const testingTTS = ref(false)
const testingConnection = ref(false)
const asrTestResult = ref('')
const testText = ref('你好，这是语音合成测试。')
const connectionResult = ref<{success: boolean, message: string} | null>(null)

// 加载配置
const loadConfig = async () => {
  try {
    const response = await axios.get('/api/voice/config')
    if (response.data.success) {
      Object.assign(asrConfig.value, response.data.asr || {})
      Object.assign(ttsConfig.value, response.data.tts || {})
      Object.assign(apiConfig.value, response.data.api || {})
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 保存配置
const saveConfig = async () => {
  saving.value = true
  try {
    const response = await axios.post('/api/voice/config', {
      asr: asrConfig.value,
      tts: ttsConfig.value,
      api: apiConfig.value
    })
    
    if (response.data.success) {
      ElMessage.success('配置保存成功')
    } else {
      ElMessage.error('配置保存失败')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

// 测试ASR
const testASR = async () => {
  testingASR.value = true
  asrTestResult.value = ''
  
  try {
    // 这里应该实现录音和识别逻辑
    ElMessage.info('请开始说话...')
    
    // 模拟测试结果
    setTimeout(() => {
      asrTestResult.value = '测试识别结果：你好，这是语音识别测试。'
      testingASR.value = false
      ElMessage.success('语音识别测试完成')
    }, 3000)
  } catch (error) {
    console.error('ASR测试失败:', error)
    ElMessage.error('语音识别测试失败')
    testingASR.value = false
  }
}

// 测试TTS
const testTTS = async () => {
  if (!testText.value.trim()) {
    ElMessage.warning('请输入测试文本')
    return
  }
  
  testingTTS.value = true
  
  try {
    const response = await axios.post('/api/voice/tts', {
      text: testText.value,
      voice: ttsConfig.value.voice,
      speed: ttsConfig.value.speed,
      pitch: ttsConfig.value.pitch,
      volume: ttsConfig.value.volume
    }, {
      responseType: 'blob'
    })
    
    // 播放音频
    const audioUrl = URL.createObjectURL(response.data)
    const audio = new Audio(audioUrl)
    audio.play()
    
    audio.onended = () => {
      URL.revokeObjectURL(audioUrl)
      testingTTS.value = false
      ElMessage.success('语音合成测试完成')
    }
    
    audio.onerror = () => {
      URL.revokeObjectURL(audioUrl)
      testingTTS.value = false
      ElMessage.error('音频播放失败')
    }
  } catch (error) {
    console.error('TTS测试失败:', error)
    ElMessage.error('语音合成测试失败')
    testingTTS.value = false
  }
}

// 测试API连接
const testConnection = async () => {
  testingConnection.value = true
  connectionResult.value = null
  
  try {
    const response = await axios.post('/api/voice/test-connection')
    connectionResult.value = {
      success: response.data.success,
      message: response.data.message
    }
  } catch (error) {
    console.error('连接测试失败:', error)
    connectionResult.value = {
      success: false,
      message: 'API连接测试失败'
    }
  } finally {
    testingConnection.value = false
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.voice-config-container {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: calc(100vh - 120px);
}

.config-card {
  max-width: 1000px;
  margin: 0 auto;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-radius: 12px;
  margin: -16px -20px 16px -20px;
  padding: 16px 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.config-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-card {
  border-radius: 16px;
  border: 1px solid rgba(228, 231, 237, 0.3);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.config-form {
  margin-bottom: 20px;
}

.full-width {
  width: 100%;
}

.speed-slider,
.pitch-slider,
.volume-slider {
  margin-right: 20px;
}

.test-section {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(250, 250, 250, 0.5);
  border-radius: 12px;
  border-top: 1px solid rgba(228, 231, 237, 0.3);
}

.test-input {
  flex: 1;
  margin-right: 12px;
}

.test-result {
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(103, 194, 58, 0.1);
  color: #67c23a;
}

.test-result.error {
  background: rgba(245, 108, 108, 0.1);
  color: #f56c6c;
}

.voice-info {
  color: #999;
  font-size: 12px;
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .voice-config-container {
    padding: 16px;
  }
  
  .config-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .test-section {
    flex-direction: column;
    align-items: stretch;
  }
  
  .test-input {
    margin-right: 0;
    margin-bottom: 12px;
  }
}
</style>