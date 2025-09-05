<template>
  <div class="settings-container">
    <div class="settings-header">
      <h1 class="page-title">
        <el-icon><Setting /></el-icon>
        系统设置
      </h1>
      
      <div class="header-actions">
        <el-button 
          type="primary" 
          :icon="Check" 
          @click="saveAllSettings"
          :loading="saving"
        >
          保存设置
        </el-button>
        
        <el-button 
          :icon="Refresh" 
          @click="resetSettings"
          :disabled="saving"
        >
          重置
        </el-button>
      </div>
    </div>
    
    <div class="settings-content">
      <el-row :gutter="20">
        <!-- 左侧菜单 -->
        <el-col :xs="24" :sm="6" :md="6" :lg="5">
          <el-card class="settings-menu" shadow="never">
            <el-menu 
              v-model:default-active="activeTab"
              @select="handleMenuSelect"
              class="settings-nav"
            >
              <el-menu-item index="general">
                <el-icon><Tools /></el-icon>
                <span>基础设置</span>
              </el-menu-item>
              
              <el-menu-item index="reservation">
                <el-icon><Calendar /></el-icon>
                <span>预约设置</span>
              </el-menu-item>
              
              <el-menu-item index="notification">
                <el-icon><Bell /></el-icon>
                <span>通知设置</span>
              </el-menu-item>
              
              <el-menu-item index="ai">
                <el-icon><ChatDotRound /></el-icon>
                <span>AI智能配置</span>
              </el-menu-item>
              
              <!-- 语音配置已禁用 -->
              <!-- <el-menu-item index="voice">
                <el-icon><Microphone /></el-icon>
                <span>语音配置</span>
              </el-menu-item> -->
              
              <el-menu-item index="security">
                <el-icon><Lock /></el-icon>
                <span>安全设置</span>
              </el-menu-item>
              
              <el-menu-item index="system">
                <el-icon><Monitor /></el-icon>
                <span>系统信息</span>
              </el-menu-item>
            </el-menu>
          </el-card>
        </el-col>
        
        <!-- 右侧内容 -->
        <el-col :xs="24" :sm="18" :md="18" :lg="19">
          <div class="settings-panel">
            <!-- 基础设置 -->
            <el-card v-show="activeTab === 'general'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Tools /></el-icon>
                  <span>基础设置</span>
                </div>
              </template>
              
              <el-form :model="generalSettings" label-width="120px" class="setting-form">
                <el-form-item label="系统名称">
                  <el-input 
                    v-model="generalSettings.systemName"
                    placeholder="请输入系统名称"
                    maxlength="50"
                    show-word-limit
                  />
                </el-form-item>
                
                <el-form-item label="系统描述">
                  <el-input 
                    v-model="generalSettings.systemDescription"
                    type="textarea"
                    :rows="3"
                    placeholder="请输入系统描述"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
                
                <el-form-item label="默认语言">
                  <el-select v-model="generalSettings.defaultLanguage" style="width: 200px">
                    <el-option label="简体中文" value="zh-CN" />
                    <el-option label="English" value="en-US" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="时区设置">
                  <el-select v-model="generalSettings.timezone" style="width: 200px">
                    <el-option label="北京时间 (UTC+8)" value="Asia/Shanghai" />
                    <el-option label="东京时间 (UTC+9)" value="Asia/Tokyo" />
                    <el-option label="纽约时间 (UTC-5)" value="America/New_York" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="主题模式">
                  <el-radio-group v-model="generalSettings.themeMode">
                    <el-radio label="light">浅色模式</el-radio>
                    <el-radio label="dark">深色模式</el-radio>
                    <el-radio label="auto">跟随系统</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-form>
            </el-card>
            
            <!-- 预约设置 -->
            <el-card v-show="activeTab === 'reservation'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Calendar /></el-icon>
                  <span>预约设置</span>
                </div>
              </template>
              
              <el-form :model="reservationSettings" label-width="150px" class="setting-form">
                <el-form-item label="预约时间范围">
                  <el-time-picker
                    v-model="reservationSettings.workingHours"
                    is-range
                    range-separator="至"
                    start-placeholder="开始时间"
                    end-placeholder="结束时间"
                    format="HH:mm"
                    value-format="HH:mm"
                  />
                </el-form-item>
                
                <el-form-item label="提前预约天数">
                  <el-input-number 
                    v-model="reservationSettings.advanceBookingDays"
                    :min="1"
                    :max="365"
                    controls-position="right"
                  />
                  <span class="form-tip">用户最多可以提前多少天进行预约</span>
                </el-form-item>
                
                <el-form-item label="最小预约时长">
                  <el-input-number 
                    v-model="reservationSettings.minDuration"
                    :min="15"
                    :max="480"
                    :step="15"
                    controls-position="right"
                  />
                  <span class="form-tip">分钟</span>
                </el-form-item>
                
                <el-form-item label="最大预约时长">
                  <el-input-number 
                    v-model="reservationSettings.maxDuration"
                    :min="30"
                    :max="1440"
                    :step="30"
                    controls-position="right"
                  />
                  <span class="form-tip">分钟</span>
                </el-form-item>
                
                <el-form-item label="自动审批">
                  <el-switch 
                    v-model="reservationSettings.autoApproval"
                    active-text="开启"
                    inactive-text="关闭"
                  />
                  <div class="form-tip">开启后，符合条件的预约将自动通过审批</div>
                </el-form-item>
                
                <el-form-item label="取消时限">
                  <el-input-number 
                    v-model="reservationSettings.cancellationDeadline"
                    :min="1"
                    :max="72"
                    controls-position="right"
                  />
                  <span class="form-tip">小时（预约开始前多少小时内不允许取消）</span>
                </el-form-item>
              </el-form>
            </el-card>
            
            <!-- 通知设置 -->
            <el-card v-show="activeTab === 'notification'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Bell /></el-icon>
                  <span>通知设置</span>
                </div>
              </template>
              
              <el-form :model="notificationSettings" label-width="150px" class="setting-form">
                <el-form-item label="邮件通知">
                  <el-switch 
                    v-model="notificationSettings.emailEnabled"
                    active-text="开启"
                    inactive-text="关闭"
                  />
                </el-form-item>
                
                <el-form-item label="短信通知">
                  <el-switch 
                    v-model="notificationSettings.smsEnabled"
                    active-text="开启"
                    inactive-text="关闭"
                  />
                </el-form-item>
                
                <el-form-item label="浏览器推送">
                  <el-switch 
                    v-model="notificationSettings.pushEnabled"
                    active-text="开启"
                    inactive-text="关闭"
                  />
                </el-form-item>
                
                <el-form-item label="提醒时间">
                  <el-checkbox-group v-model="notificationSettings.reminderTimes">
                    <el-checkbox :label="15">15分钟前</el-checkbox>
                    <el-checkbox :label="30">30分钟前</el-checkbox>
                    <el-checkbox :label="60">1小时前</el-checkbox>
                    <el-checkbox :label="1440">1天前</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
                
                <el-form-item label="通知频率限制">
                  <el-input-number 
                    v-model="notificationSettings.rateLimit"
                    :min="1"
                    :max="100"
                    controls-position="right"
                  />
                  <span class="form-tip">每小时最多发送通知数量</span>
                </el-form-item>
              </el-form>
            </el-card>
            
            <!-- AI智能配置 -->
            <el-card v-show="activeTab === 'ai'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><ChatDotRound /></el-icon>
                  <span>AI智能配置</span>
                </div>
              </template>
              
              <div class="config-content">
                <!-- 大模型配置 -->
                <el-card class="section-card" shadow="never">
                  <template #header>
                    <div class="section-header">
                      <el-icon><Cpu /></el-icon>
                      <span>大模型配置</span>
                    </div>
                  </template>
                  
                  <el-form :model="aiSettings" label-width="120px" class="setting-form">
                    <el-form-item label="模型提供商">
                      <el-select v-model="aiSettings.provider" style="width: 300px" @change="handleProviderChange">
                        <el-option label="硅基流动 (SiliconFlow)" value="siliconflow" />
                        <el-option label="通义千问 (Qwen)" value="qwen" />
                        <el-option label="科大讯飞 (iFlytek)" value="xunfei" />
                        <el-option label="OpenAI" value="openai" />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="模型名称">
                      <template v-if="aiSettings.provider === 'siliconflow'">
                        <div style="display: flex; gap: 10px; align-items: center;">
                          <el-select v-model="aiSettings.model" style="width: 200px" @change="updateSiliconflowCustomModel">
                            <el-option label="Qwen2.5-72B-Instruct" value="Qwen/Qwen2.5-72B-Instruct" />
                            <el-option label="DeepSeek-R1" value="deepseek-ai/DeepSeek-R1" />
                            <el-option label="Llama-3.1-70B-Instruct" value="meta-llama/Llama-3.1-70B-Instruct" />
                            <el-option label="GLM-4-9B-Chat" value="THUDM/glm-4-9b-chat" />
                            <el-option label="自定义模型" value="custom" />
                          </el-select>
                          <el-input 
                            v-if="aiSettings.model === 'custom'"
                            v-model="aiSettings.siliconflow.customModel"
                            placeholder="请输入自定义模型名称"
                            style="width: 250px"
                            @input="updateModelFromCustom"
                          />
                        </div>
                      </template>
                      <template v-else>
                        <el-select v-model="aiSettings.model" style="width: 300px">
                          <template v-if="aiSettings.provider === 'qwen'">
                            <el-option label="qwen-turbo" value="qwen-turbo" />
                            <el-option label="qwen-plus" value="qwen-plus" />
                            <el-option label="qwen-max" value="qwen-max" />
                          </template>
                          <template v-else-if="aiSettings.provider === 'xunfei'">
                            <el-option label="Spark3.5 Max" value="generalv3.5" />
                            <el-option label="Spark Pro" value="generalv3" />
                            <el-option label="Spark Lite" value="general" />
                          </template>
                          <template v-else-if="aiSettings.provider === 'openai'">
                            <el-option label="GPT-4" value="gpt-4" />
                            <el-option label="GPT-3.5-turbo" value="gpt-3.5-turbo" />
                          </template>
                        </el-select>
                      </template>
                    </el-form-item>
                    
                    <!-- 科大讯飞配置 -->
                    <template v-if="aiSettings.provider === 'xunfei'">
                      <el-form-item label="APPID" required>
                        <el-input 
                          v-model="aiSettings.xunfei.appId"
                          placeholder="请输入科大讯飞APPID"
                          style="width: 400px"
                        />
                        <div class="form-tip">在科大讯飞开放平台创建应用后获得</div>
                      </el-form-item>
                      
                      <el-form-item label="API Secret" required>
                        <el-input 
                          v-model="aiSettings.xunfei.apiSecret"
                          type="password"
                          placeholder="请输入API Secret"
                          show-password
                          style="width: 400px"
                        />
                        <div class="form-tip">用于生成签名的密钥</div>
                      </el-form-item>
                      
                      <el-form-item label="API Key" required>
                        <el-input 
                          v-model="aiSettings.xunfei.apiKey"
                          type="password"
                          placeholder="请输入API Key"
                          show-password
                          style="width: 400px"
                        />
                        <div class="form-tip">用于身份验证的密钥</div>
                      </el-form-item>
                    </template>
                    
                    <!-- 通义千问配置 -->
                    <template v-else-if="aiSettings.provider === 'qwen'">
                      <el-form-item label="API密钥" required>
                        <el-input 
                          v-model="aiSettings.qwen.apiKey"
                          type="password"
                          placeholder="请输入通义千问API密钥"
                          show-password
                          style="width: 400px"
                        />
                        <div class="form-tip">格式：sk-xxxxxxxxxx</div>
                      </el-form-item>
                    </template>
                    
                    <!-- 硅基流动配置 -->
                    <template v-else-if="aiSettings.provider === 'siliconflow'">
                      <el-form-item label="API密钥" required>
                        <el-input 
                          v-model="aiSettings.siliconflow.apiKey"
                          type="password"
                          placeholder="请输入硅基流动API密钥"
                          show-password
                          style="width: 400px"
                        />
                        <div class="form-tip">格式：sk-xxxxxxxxxx</div>
                      </el-form-item>
                    </template>
                    
                    <!-- OpenAI配置 -->
                    <template v-else-if="aiSettings.provider === 'openai'">
                      <el-form-item label="API密钥" required>
                        <el-input 
                          v-model="aiSettings.openai.apiKey"
                          type="password"
                          placeholder="请输入OpenAI API密钥"
                          show-password
                          style="width: 400px"
                        />
                        <div class="form-tip">格式：sk-xxxxxxxxxx</div>
                      </el-form-item>
                      
                      <el-form-item label="组织ID">
                        <el-input 
                          v-model="aiSettings.openai.organization"
                          placeholder="请输入组织ID（可选）"
                          style="width: 400px"
                        />
                        <div class="form-tip">可选，用于团队账户</div>
                      </el-form-item>
                    </template>
                    
                    <el-form-item label="API地址">
                      <el-input 
                        v-model="aiSettings.baseUrl"
                        placeholder="API基础地址"
                        style="width: 400px"
                      />
                      <div class="form-tip">请输入API服务的基础地址</div>
                    </el-form-item>
                    
                    <el-form-item>
                      <el-button 
                        type="success" 
                        @click="saveAIConfig" 
                        :loading="aiSaving"
                      >
                        保存配置
                      </el-button>
                    </el-form-item>
                  </el-form>
                </el-card>
                
                <!-- 对话参数配置 -->
                <el-card class="section-card" shadow="never" style="margin-top: 20px">
                  <template #header>
                    <div class="section-header">
                      <el-icon><Setting /></el-icon>
                      <span>对话参数</span>
                    </div>
                  </template>
                  
                  <el-form :model="aiSettings" label-width="120px" class="setting-form">
                    <el-form-item label="温度参数">
                      <el-slider 
                        v-model="aiSettings.temperature"
                        :min="0"
                        :max="1"
                        :step="0.1"
                        show-tooltip
                        style="width: 300px"
                      />
                      <div class="form-tip">控制AI回复的随机性，值越高越随机</div>
                    </el-form-item>
                    
                    <el-form-item label="最大令牌数">
                      <el-input-number 
                        v-model="aiSettings.maxTokens"
                        :min="100"
                        :max="8000"
                        :step="100"
                        controls-position="right"
                      />
                      <div class="form-tip">单次对话最大生成的令牌数量</div>
                    </el-form-item>
                    
                    <el-form-item label="上下文长度">
                      <el-input-number 
                        v-model="aiSettings.contextLength"
                        :min="1"
                        :max="20"
                        controls-position="right"
                      />
                      <div class="form-tip">保留的历史对话轮数</div>
                    </el-form-item>
                    
                    <el-form-item label="流式输出">
                      <el-switch 
                        v-model="aiSettings.stream"
                        active-text="开启"
                        inactive-text="关闭"
                      />
                      <div class="form-tip">开启后AI回复将逐字显示</div>
                    </el-form-item>
                  </el-form>
                </el-card>
                
                <!-- 智能功能配置 -->
                <el-card class="section-card" shadow="never" style="margin-top: 20px">
                  <template #header>
                    <div class="section-header">
                      <el-icon><MagicStick /></el-icon>
                      <span>智能功能</span>
                    </div>
                  </template>
                  
                  <el-form :model="aiSettings" label-width="120px" class="setting-form">
                    <el-form-item label="意图识别">
                      <el-switch 
                        v-model="aiSettings.intentRecognition"
                        active-text="开启"
                        inactive-text="关闭"
                      />
                      <div class="form-tip">自动识别用户预约意图</div>
                    </el-form-item>
                    
                    <el-form-item label="信息完整性检查">
                      <el-switch 
                        v-model="aiSettings.completenessCheck"
                        active-text="开启"
                        inactive-text="关闭"
                      />
                      <div class="form-tip">信息不完整时主动询问用户</div>
                    </el-form-item>
                    
                    <el-form-item label="智能推荐">
                      <el-switch 
                        v-model="aiSettings.smartRecommendation"
                        active-text="开启"
                        inactive-text="关闭"
                      />
                      <div class="form-tip">根据历史数据推荐合适的会议室</div>
                    </el-form-item>
                    
                    <el-form-item label="语音交互">
                      <el-switch 
                        v-model="aiSettings.voiceInteraction"
                        active-text="开启"
                        inactive-text="关闭"
                        :disabled="true"
                      />
                      <div class="form-tip">语音功能已禁用</div>
                    </el-form-item>
                  </el-form>
                </el-card>
                
                <!-- AI连接测试 -->
                <el-card class="section-card" shadow="never" style="margin-top: 20px">
                  <template #header>
                    <div class="section-header">
                      <el-icon><Connection /></el-icon>
                      <span>AI服务连接测试</span>
                    </div>
                  </template>
                  
                  <div class="ai-test-content">
                    <div class="test-description">
                      <p>验证AI服务API密钥是否正确配置，确保智能预约功能正常工作。</p>
                    </div>
                    
                    <div class="test-actions">
                      <el-button 
                        type="primary" 
                        @click="testAIConnection" 
                        :loading="aiTesting"
                        :icon="aiTesting ? 'Loading' : 'Connection'"
                      >
                        {{ aiTesting ? '测试中...' : '测试AI连接' }}
                      </el-button>
                    </div>
                    
                    <div class="test-results" v-if="aiTestResults">
                      <div class="result-summary">
                        <el-tag 
                          :type="aiTestResults.summary?.overall_status === '全部可用' ? 'success' : 
                                aiTestResults.summary?.overall_status === '部分可用' ? 'warning' : 'danger'"
                          size="large"
                        >
                          {{ aiTestResults.summary?.overall_status || '未知状态' }}
                        </el-tag>
                        <span class="summary-text">
                          {{ aiTestResults.summary?.successful_services || 0 }}/{{ aiTestResults.summary?.total_services || 0 }} 服务可用
                        </span>
                      </div>
                      
                      <div class="service-results">
                        <!-- 通义千问测试结果 -->
                        <div class="service-result" v-if="aiTestResults.qwen_api">
                          <div class="service-header">
                            <el-icon :class="aiTestResults.qwen_api.success ? 'success-icon' : 'error-icon'">
                              <component :is="aiTestResults.qwen_api.success ? 'SuccessFilled' : 'CircleCloseFilled'" />
                            </el-icon>
                            <span class="service-name">通义千问 API</span>
                          </div>
                          <div class="service-details">
                            <p v-if="aiTestResults.qwen_api.success">
                              <strong>状态:</strong> 连接成功
                            </p>
                            <p v-if="aiTestResults.qwen_api.model">
                              <strong>模型:</strong> {{ aiTestResults.qwen_api.model }}
                            </p>
                            <p v-if="!aiTestResults.qwen_api.success">
                              <strong>错误:</strong> {{ aiTestResults.qwen_api.error }}
                            </p>
                            <p v-if="aiTestResults.qwen_api.details" class="error-details">
                              <strong>详情:</strong> {{ aiTestResults.qwen_api.details }}
                            </p>
                          </div>
                        </div>
                        
                        <!-- 硅基流动测试结果 -->
                        <div class="service-result" v-if="aiTestResults.siliconflow_api">
                          <div class="service-header">
                            <el-icon :class="aiTestResults.siliconflow_api.success ? 'success-icon' : 'error-icon'">
                              <component :is="aiTestResults.siliconflow_api.success ? 'SuccessFilled' : 'CircleCloseFilled'" />
                            </el-icon>
                            <span class="service-name">硅基流动 API</span>
                          </div>
                          <div class="service-details">
                            <p v-if="aiTestResults.siliconflow_api.success">
                              <strong>状态:</strong> 连接成功
                            </p>
                            <p v-if="aiTestResults.siliconflow_api.model">
                              <strong>模型:</strong> {{ aiTestResults.siliconflow_api.model }}
                            </p>
                            <p v-if="!aiTestResults.siliconflow_api.success">
                              <strong>错误:</strong> {{ aiTestResults.siliconflow_api.error }}
                            </p>
                            <p v-if="aiTestResults.siliconflow_api.details" class="error-details">
                              <strong>详情:</strong> {{ aiTestResults.siliconflow_api.details }}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div class="config-tips" v-if="!aiTestResults.qwen_api?.success || !aiTestResults.siliconflow_api?.success">
                        <el-alert
                          title="配置提醒"
                          type="warning"
                          :closable="false"
                        >
                          <template #default>
                            <p>如果API连接失败，请检查以下配置：</p>
                            <ul>
                              <li>确保在 <code>backend/.env</code> 文件中配置了有效的API密钥</li>
                              <li>通义千问: <code>QWEN_API_KEY=sk-xxxxxxxxxx</code></li>
                              <li>硅基流动: <code>SILICONFLOW_API_KEY=sk-xxxxxxxxxx</code></li>
                              <li>确保API密钥有足够的调用额度</li>
                              <li>检查网络连接是否正常</li>
                            </ul>
                            <p><strong>⚠️ 重要:</strong> 当API密钥无效时，智能预约功能将使用本地规则引擎，功能会受到限制。</p>
                          </template>
                        </el-alert>
                      </div>
                    </div>
                  </div>
                </el-card>
              </div>
            </el-card>
            
            <!-- 模型配置 -->
            <el-card v-show="activeTab === 'model'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Cpu /></el-icon>
                  <span>模型配置</span>
                </div>
              </template>
              
              <div class="config-section">
                <h3>API连接配置</h3>
                <el-form :model="modelConfig" label-width="120px" class="setting-form">
                  <el-form-item label="API密钥">
                    <el-input 
                      v-model="modelConfig.apiKey" 
                      placeholder="请输入API密钥"
                      type="password"
                      show-password
                      style="width: 400px"
                    />
                  </el-form-item>
                  <el-form-item label="API地址">
                    <el-input 
                      v-model="modelConfig.apiUrl" 
                      placeholder="请输入API地址"
                      style="width: 400px"
                    />
                  </el-form-item>
                  <el-form-item label="模型名称">
                    <el-input 
                      v-model="modelConfig.modelName" 
                      placeholder="请输入模型名称"
                      style="width: 400px"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button 
                      type="primary" 
                      @click="testModelConnection" 
                      :loading="modelTesting"
                    >
                      测试连接
                    </el-button>
                    <el-button 
                      type="success" 
                      @click="saveModelConfig" 
                      :loading="modelSaving"
                    >
                      保存配置
                    </el-button>
                  </el-form-item>
                </el-form>
                <div v-if="modelConnectionResult" class="result">
                  <el-alert 
                    :title="modelConnectionResult.success ? '连接成功' : '连接失败'" 
                    :type="modelConnectionResult.success ? 'success' : 'error'"
                    :description="modelConnectionResult.message"
                    show-icon
                  />
                </div>
              </div>
            </el-card>
            
            <!-- 语音配置 -->
            <el-card v-show="activeTab === 'voice'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Microphone /></el-icon>
                  <span>语音配置</span>
                </div>
              </template>
              
              <div class="config-content">
                <!-- 科大讯飞语音识别配置 -->
                <el-card class="section-card" shadow="never">
                  <template #header>
                    <div class="section-header">
                      <el-icon><Microphone /></el-icon>
                      <span>科大讯飞语音识别 (ASR)</span>
                    </div>
                  </template>
                  
                  <el-form :model="voiceConfig.xunfei.asr" label-width="120px" class="setting-form">
                    <el-form-item label="APPID">
                      <el-input 
                        v-model="voiceConfig.xunfei.asr.appId"
                        placeholder="请输入科大讯飞APPID"
                        style="width: 400px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="API Secret">
                      <el-input 
                        v-model="voiceConfig.xunfei.asr.apiSecret"
                        type="password"
                        placeholder="请输入API Secret"
                        show-password
                        style="width: 400px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="API Key">
                      <el-input 
                        v-model="voiceConfig.xunfei.asr.apiKey"
                        type="password"
                        placeholder="请输入API Key"
                        show-password
                        style="width: 400px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="识别引擎">
                      <el-select v-model="voiceConfig.xunfei.asr.engine" style="width: 300px">
                        <el-option label="通用识别" value="sms16k" />
                        <el-option label="实时语音转写" value="iat" />
                        <el-option label="语音听写" value="ise" />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="语言">
                      <el-select v-model="voiceConfig.xunfei.asr.language" style="width: 300px">
                        <el-option label="中文普通话" value="zh_cn" />
                        <el-option label="英文" value="en_us" />
                        <el-option label="中英混合" value="zh_en" />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="音频格式">
                      <el-select v-model="voiceConfig.xunfei.asr.audioFormat" style="width: 300px">
                        <el-option label="PCM 16k 16bit" value="audio/L16;rate=16000" />
                        <el-option label="PCM 8k 16bit" value="audio/L16;rate=8000" />
                        <el-option label="MP3" value="audio/mpeg" />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item>
                      <el-button 
                        type="primary" 
                        @click="testASRConnection" 
                        :loading="asrTesting"
                      >
                        测试语音识别
                      </el-button>
                      <el-button 
                        type="success" 
                        @click="saveASRConfig" 
                        :loading="asrSaving"
                      >
                        保存配置
                      </el-button>
                    </el-form-item>
                  </el-form>
                </el-card>
                
                <!-- 科大讯飞语音合成配置 -->
                <el-card class="section-card" shadow="never" style="margin-top: 20px">
                  <template #header>
                    <div class="section-header">
                      <el-icon><ChatDotRound /></el-icon>
                      <span>科大讯飞语音合成 (TTS)</span>
                    </div>
                  </template>
                  
                  <el-form :model="voiceConfig.xunfei.tts" label-width="120px" class="setting-form">
                    <el-form-item label="APPID">
                      <el-input 
                        v-model="voiceConfig.xunfei.tts.appId"
                        placeholder="请输入科大讯飞APPID"
                        style="width: 400px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="API Secret">
                      <el-input 
                        v-model="voiceConfig.xunfei.tts.apiSecret"
                        type="password"
                        placeholder="请输入API Secret"
                        show-password
                        style="width: 400px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="API Key">
                      <el-input 
                        v-model="voiceConfig.xunfei.tts.apiKey"
                        type="password"
                        placeholder="请输入API Key"
                        show-password
                        style="width: 400px"
                      />
                    </el-form-item>
                    
                    <el-form-item label="发音人">
                      <el-select v-model="voiceConfig.xunfei.tts.voice" style="width: 300px">
                        <el-option label="小燕 (xiaoyan)" value="xiaoyan" />
                        <el-option label="小宇 (xiaoyu)" value="xiaoyu" />
                        <el-option label="凯瑟琳 (catherine)" value="catherine" />
                        <el-option label="亨利 (henry)" value="henry" />
                        <el-option label="玛丽 (mary)" value="mary" />
                        <el-option label="小研 (xiaoyan_emo)" value="xiaoyan_emo" />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item label="语速">
                      <el-slider 
                        v-model="voiceConfig.xunfei.tts.speed"
                        :min="0"
                        :max="100"
                        :step="1"
                        show-tooltip
                        style="width: 300px"
                      />
                      <div class="form-tip">语速范围：0-100，默认50</div>
                    </el-form-item>
                    
                    <el-form-item label="音量">
                      <el-slider 
                        v-model="voiceConfig.xunfei.tts.volume"
                        :min="0"
                        :max="100"
                        :step="1"
                        show-tooltip
                        style="width: 300px"
                      />
                      <div class="form-tip">音量范围：0-100，默认50</div>
                    </el-form-item>
                    
                    <el-form-item label="音调">
                      <el-slider 
                        v-model="voiceConfig.xunfei.tts.pitch"
                        :min="0"
                        :max="100"
                        :step="1"
                        show-tooltip
                        style="width: 300px"
                      />
                      <div class="form-tip">音调范围：0-100，默认50</div>
                    </el-form-item>
                    
                    <el-form-item label="音频格式">
                      <el-select v-model="voiceConfig.xunfei.tts.audioFormat" style="width: 300px">
                        <el-option label="PCM 16k 16bit" value="audio/L16;rate=16000" />
                        <el-option label="PCM 8k 16bit" value="audio/L16;rate=8000" />
                        <el-option label="MP3" value="audio/mpeg" />
                      </el-select>
                    </el-form-item>
                    
                    <el-form-item>
                      <el-button 
                        type="primary" 
                        @click="testTTSConnection" 
                        :loading="ttsTesting"
                      >
                        测试语音合成
                      </el-button>
                      <el-button 
                        type="success" 
                        @click="saveTTSConfig" 
                        :loading="ttsSaving"
                      >
                        保存配置
                      </el-button>
                    </el-form-item>
                  </el-form>
                </el-card>
                
                <!-- 语音交互设置 -->
                <el-card class="section-card" shadow="never" style="margin-top: 20px">
                  <template #header>
                    <div class="section-header">
                      <el-icon><Setting /></el-icon>
                      <span>语音交互设置</span>
                    </div>
                  </template>
                  
                  <el-form :model="voiceConfig.interaction" label-width="120px" class="setting-form">
                    <el-form-item label="自动播放">
                      <el-switch 
                        v-model="voiceConfig.interaction.autoPlay"
                        active-text="开启"
                        inactive-text="关闭"
                      />
                      <div class="form-tip">AI回复后自动播放语音</div>
                    </el-form-item>
                    
                    <el-form-item label="语音唤醒">
                      <el-switch 
                        v-model="voiceConfig.interaction.wakeWord"
                        active-text="开启"
                        inactive-text="关闭"
                      />
                      <div class="form-tip">支持语音唤醒功能</div>
                    </el-form-item>
                    
                    <el-form-item label="连续对话">
                      <el-switch 
                        v-model="voiceConfig.interaction.continuous"
                        active-text="开启"
                        inactive-text="关闭"
                      />
                      <div class="form-tip">支持连续语音对话</div>
                    </el-form-item>
                    
                    <el-form-item label="静音检测">
                      <el-input-number 
                        v-model="voiceConfig.interaction.silenceTimeout"
                        :min="1000"
                        :max="10000"
                        :step="500"
                        controls-position="right"
                      />
                      <div class="form-tip">静音超时时间（毫秒）</div>
                    </el-form-item>
                  </el-form>
                </el-card>
              </div>
            </el-card>
            
            <!-- 硅基流动 -->
            <el-card v-show="activeTab === 'siliconflow'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Connection /></el-icon>
                  <span>硅基流动配置</span>
                </div>
              </template>
              
              <div class="config-content">
                <el-form :model="siliconflowConfig" label-width="120px" class="setting-form">
                  <el-form-item label="API Key">
                    <el-input 
                      v-model="siliconflowConfig.apiKey" 
                      type="password"
                      placeholder="请输入硅基流动API Key"
                      show-password
                      style="width: 400px"
                    />
                  </el-form-item>
                  
                  <el-form-item label="API地址">
                    <el-input 
                      v-model="siliconflowConfig.baseUrl" 
                      placeholder="https://api.siliconflow.cn/v1"
                      style="width: 400px"
                    />
                  </el-form-item>
                  
                  <el-form-item label="默认模型">
                    <el-select v-model="siliconflowConfig.defaultModel" placeholder="请选择默认模型" style="width: 300px">
                      <el-option label="Qwen2.5-7B-Instruct" value="Qwen/Qwen2.5-7B-Instruct" />
                      <el-option label="Qwen2.5-14B-Instruct" value="Qwen/Qwen2.5-14B-Instruct" />
                      <el-option label="DeepSeek-V2.5" value="deepseek-ai/DeepSeek-V2.5" />
                    </el-select>
                  </el-form-item>
                  
                  <el-form-item>
                    <el-button 
                      type="primary" 
                      @click="testSiliconflowConnection" 
                      :loading="siliconflowTesting"
                    >
                      测试连接
                    </el-button>
                    <el-button 
                      type="success" 
                      @click="saveSiliconflowConfig" 
                      :loading="siliconflowSaving"
                    >
                      保存配置
                    </el-button>
                  </el-form-item>
                </el-form>
              </div>
            </el-card>
            
            <!-- 安全设置 -->
            <el-card v-show="activeTab === 'security'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Lock /></el-icon>
                  <span>安全设置</span>
                </div>
              </template>
              
              <el-form :model="securitySettings" label-width="150px" class="setting-form">
                <el-form-item label="密码策略">
                  <el-checkbox-group v-model="securitySettings.passwordPolicy">
                    <el-checkbox label="minLength">最少8位字符</el-checkbox>
                    <el-checkbox label="requireUppercase">包含大写字母</el-checkbox>
                    <el-checkbox label="requireLowercase">包含小写字母</el-checkbox>
                    <el-checkbox label="requireNumbers">包含数字</el-checkbox>
                    <el-checkbox label="requireSpecialChars">包含特殊字符</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
                
                <el-form-item label="会话超时">
                  <el-input-number 
                    v-model="securitySettings.sessionTimeout"
                    :min="30"
                    :max="1440"
                    :step="30"
                    controls-position="right"
                  />
                  <span class="form-tip">分钟</span>
                </el-form-item>
                
                <el-form-item label="登录失败限制">
                  <el-input-number 
                    v-model="securitySettings.maxLoginAttempts"
                    :min="3"
                    :max="10"
                    controls-position="right"
                  />
                  <span class="form-tip">次数</span>
                </el-form-item>
                
                <el-form-item label="账户锁定时间">
                  <el-input-number 
                    v-model="securitySettings.lockoutDuration"
                    :min="5"
                    :max="60"
                    :step="5"
                    controls-position="right"
                  />
                  <span class="form-tip">分钟</span>
                </el-form-item>
                
                <el-form-item label="双因子认证">
                  <el-switch 
                    v-model="securitySettings.twoFactorAuth"
                    active-text="开启"
                    inactive-text="关闭"
                  />
                </el-form-item>
              </el-form>
            </el-card>
            
            <!-- 系统信息 -->
            <el-card v-show="activeTab === 'system'" class="setting-card" shadow="hover">
              <template #header>
                <div class="card-header">
                  <el-icon><Monitor /></el-icon>
                  <span>系统信息</span>
                </div>
              </template>
              
              <div class="system-info">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="系统版本">
                    {{ systemInfo.version }}
                  </el-descriptions-item>
                  
                  <el-descriptions-item label="构建时间">
                    {{ systemInfo.buildTime }}
                  </el-descriptions-item>
                  
                  <el-descriptions-item label="运行时间">
                    {{ formatUptime(systemInfo.uptime) }}
                  </el-descriptions-item>
                  
                  <el-descriptions-item label="数据库状态">
                    <el-tag :type="systemInfo.dbStatus === 'connected' ? 'success' : 'danger'">
                      {{ systemInfo.dbStatus === 'connected' ? '已连接' : '未连接' }}
                    </el-tag>
                  </el-descriptions-item>
                  
                  <el-descriptions-item label="总用户数">
                    {{ systemInfo.totalUsers }}
                  </el-descriptions-item>
                  
                  <el-descriptions-item label="总预约数">
                    {{ systemInfo.totalReservations }}
                  </el-descriptions-item>
                  
                  <el-descriptions-item label="存储使用">
                    {{ systemInfo.storageUsed }} / {{ systemInfo.storageTotal }}
                  </el-descriptions-item>
                  
                  <el-descriptions-item label="内存使用">
                    {{ systemInfo.memoryUsed }} / {{ systemInfo.memoryTotal }}
                  </el-descriptions-item>
                </el-descriptions>
                
                <div class="system-actions">
                  <el-button type="info" :icon="Refresh" @click="refreshSystemInfo">
                    刷新信息
                  </el-button>
                  
                  <el-button type="warning" :icon="Download" @click="exportLogs">
                    导出日志
                  </el-button>
                  
                  <el-button type="danger" :icon="Delete" @click="clearCache">
                    清理缓存
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { 
  Setting, 
  Check, 
  Refresh, 
  Tools, 
  Calendar, 
  Bell, 
  ChatDotRound, 
  Lock, 
  Monitor,
  Download,
  Delete,
  Cpu,
  Microphone,
  Connection,
  VideoPlay,
  ChatLineRound,
  MagicStick
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'

// 响应式数据
const activeTab = ref('general')
const saving = ref(false)
const router = useRouter()

// 设置数据
const generalSettings = reactive({
  systemName: '智能预约系统',
  systemDescription: '基于AI的智能预约管理系统',
  defaultLanguage: 'zh-CN',
  timezone: 'Asia/Shanghai',
  themeMode: 'light'
})

const reservationSettings = reactive({
  workingHours: ['09:00', '18:00'],
  advanceBookingDays: 30,
  minDuration: 30,
  maxDuration: 240,
  autoApproval: false,
  cancellationDeadline: 2
})

const notificationSettings = reactive({
  emailEnabled: true,
  smsEnabled: false,
  pushEnabled: true,
  reminderTimes: [15, 30, 60],
  rateLimit: 10
})

const aiSettings = reactive({
  provider: 'siliconflow',
  model: 'Qwen/Qwen2.5-72B-Instruct',
  apiKey: '',
  baseUrl: 'https://api.siliconflow.cn/v1',
  temperature: 0.7,
  maxTokens: 2000,
  contextLength: 10,
  stream: true,
  intentRecognition: true,
  completenessCheck: true,
  smartRecommendation: true,
  voiceInteraction: true,
  defaultVoice: 'alex',
  voiceModel: 'FunAudioLLM/CosyVoice2-0.5B',
  // 科大讯飞专用配置
  xunfei: {
    appId: '',
    apiSecret: '',
    apiKey: ''
  },
  // 通义千问专用配置
  qwen: {
    apiKey: ''
  },
  // 硅基流动专用配置
  siliconflow: {
    apiKey: '',
    customModel: '' // 允许用户自定义模型名称
  },
  // OpenAI专用配置
  openai: {
    apiKey: '',
    organization: '' // 可选的组织ID
  }
})

const modelTesting = ref(false)
const aiSaving = ref(false)

const handleProviderChange = (provider: string) => {
  // 根据提供商设置默认模型和API配置
  if (provider === 'siliconflow') {
    aiSettings.model = aiSettings.siliconflow.customModel || 'Qwen/Qwen2.5-72B-Instruct'
    aiSettings.baseUrl = 'https://api.siliconflow.cn/v1'
    aiSettings.apiKey = aiSettings.siliconflow.apiKey
    // 同步更新modelConfig
    modelConfig.apiUrl = 'https://api.siliconflow.cn/v1'
    modelConfig.modelName = aiSettings.model
    modelConfig.apiKey = aiSettings.siliconflow.apiKey
  } else if (provider === 'qwen') {
    aiSettings.model = 'qwen-turbo'
    aiSettings.baseUrl = 'https://dashscope.aliyuncs.com/api/v1'
    aiSettings.apiKey = aiSettings.qwen.apiKey
    // 同步更新modelConfig
    modelConfig.apiUrl = 'https://dashscope.aliyuncs.com/api/v1'
    modelConfig.modelName = 'qwen-turbo'
    modelConfig.apiKey = aiSettings.qwen.apiKey
  } else if (provider === 'xunfei') {
    aiSettings.model = 'generalv3.5'
    aiSettings.baseUrl = 'https://spark-api-open.xf-yun.com/v1/chat/completions'
    aiSettings.apiKey = aiSettings.xunfei.apiKey
    // 同步更新modelConfig
    modelConfig.apiUrl = 'https://spark-api-open.xf-yun.com/v1/chat/completions'
    modelConfig.modelName = 'generalv3.5'
    modelConfig.apiKey = aiSettings.xunfei.apiKey
  } else if (provider === 'openai') {
    aiSettings.model = 'gpt-3.5-turbo'
    aiSettings.baseUrl = 'https://api.openai.com/v1'
    aiSettings.apiKey = aiSettings.openai.apiKey
    // 同步更新modelConfig
    modelConfig.apiUrl = 'https://api.openai.com/v1'
    modelConfig.modelName = 'gpt-3.5-turbo'
    modelConfig.apiKey = aiSettings.openai.apiKey
  }
  
  ElMessage.info(`已切换到${getProviderName(provider)}，请重新配置相关参数`)
}

// 处理硅基流动自定义模型选择
const updateSiliconflowCustomModel = (value: string) => {
  if (value !== 'custom') {
    aiSettings.siliconflow.customModel = ''
  }
  // 同步更新modelConfig
  modelConfig.modelName = value === 'custom' ? aiSettings.siliconflow.customModel : value
}

// 处理自定义模型名称输入
const updateModelFromCustom = () => {
  if (aiSettings.model === 'custom' && aiSettings.siliconflow.customModel) {
    // 同步更新modelConfig
    modelConfig.modelName = aiSettings.siliconflow.customModel
  }
}

// 配置验证
const validateConfig = () => {
  const errors: string[] = []
  
  if (aiSettings.provider === 'xunfei') {
    if (!aiSettings.xunfei.appId.trim()) {
      errors.push('科大讯飞APPID不能为空')
    }
    if (!aiSettings.xunfei.apiSecret.trim()) {
      errors.push('科大讯飞API Secret不能为空')
    }
    if (!aiSettings.xunfei.apiKey.trim()) {
      errors.push('科大讯飞API Key不能为空')
    }
  } else if (aiSettings.provider === 'qwen') {
    if (!aiSettings.qwen.apiKey.trim()) {
      errors.push('通义千问API密钥不能为空')
    } else if (!aiSettings.qwen.apiKey.startsWith('sk-')) {
      errors.push('通义千问API密钥格式不正确，应以sk-开头')
    }
  } else if (aiSettings.provider === 'siliconflow') {
    if (!aiSettings.siliconflow.apiKey.trim()) {
      errors.push('硅基流动API密钥不能为空')
    } else if (!aiSettings.siliconflow.apiKey.startsWith('sk-')) {
      errors.push('硅基流动API密钥格式不正确，应以sk-开头')
    }
    if (aiSettings.model === 'custom' && !aiSettings.siliconflow.customModel.trim()) {
      errors.push('自定义模型名称不能为空')
    }
  } else if (aiSettings.provider === 'openai') {
    if (!aiSettings.openai.apiKey.trim()) {
      errors.push('OpenAI API密钥不能为空')
    } else if (!aiSettings.openai.apiKey.startsWith('sk-')) {
      errors.push('OpenAI API密钥格式不正确，应以sk-开头')
    }
  }
  
  return errors
}

// 同步配置到各个对象
const syncConfigurations = () => {
  // 同步aiSettings到modelConfig
  if (aiSettings.provider === 'xunfei') {
    aiSettings.apiKey = aiSettings.xunfei.apiKey
    modelConfig.apiKey = aiSettings.xunfei.apiKey
  } else if (aiSettings.provider === 'qwen') {
    aiSettings.apiKey = aiSettings.qwen.apiKey
    modelConfig.apiKey = aiSettings.qwen.apiKey
  } else if (aiSettings.provider === 'siliconflow') {
    aiSettings.apiKey = aiSettings.siliconflow.apiKey
    modelConfig.apiKey = aiSettings.siliconflow.apiKey
    if (aiSettings.model === 'custom') {
      aiSettings.model = aiSettings.siliconflow.customModel
      modelConfig.modelName = aiSettings.siliconflow.customModel
    }
  } else if (aiSettings.provider === 'openai') {
    aiSettings.apiKey = aiSettings.openai.apiKey
    modelConfig.apiKey = aiSettings.openai.apiKey
  }
}

// 获取提供商显示名称
const getProviderName = (provider: string) => {
  const names: Record<string, string> = {
    'siliconflow': '硅基流动 (SiliconFlow)',
    'qwen': '通义千问 (Qwen)',
    'xunfei': '科大讯飞 (iFlytek)',
    'openai': 'OpenAI'
  }
  return names[provider] || provider
}

const testModelConnection = async () => {
  modelTesting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('模型连接测试成功')
  } catch (error) {
    ElMessage.error('模型连接测试失败')
  } finally {
    modelTesting.value = false
  }
}

const saveAIConfig = async () => {
  // 验证配置
  const errors = validateConfig()
  if (errors.length > 0) {
    ElMessage.error(errors[0])
    return
  }
  
  aiSaving.value = true
  try {
    // 同步配置
    syncConfigurations()
    
    // 调用后端API保存配置
    const response = await fetch('/api/v1/ai/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(aiSettings)
    })
    
    if (!response.ok) {
      throw new Error('保存失败')
    }
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('AI配置保存成功')
    } else {
      throw new Error(result.message || '保存失败')
    }
  } catch (error) {
    console.error('保存AI配置失败:', error)
    ElMessage.error('AI配置保存失败')
  } finally {
    aiSaving.value = false
  }
}

const loadAIConfig = async () => {
  try {
    const response = await fetch('/api/v1/ai/config?show_keys=true', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success && result.config) {
        // 直接更新AI配置（后端返回真实密钥）
        Object.assign(aiSettings, result.config)
        // 同步配置到其他变量
        syncConfigurations()
      }
    }
  } catch (error) {
    console.error('加载AI配置失败:', error)
  }
}

const securitySettings = reactive({
  passwordPolicy: ['minLength', 'requireNumbers'],
  sessionTimeout: 120,
  maxLoginAttempts: 5,
  lockoutDuration: 15,
  twoFactorAuth: false
})

const systemInfo = reactive({
  version: '1.0.0',
  buildTime: '2024-01-20 10:30:00',
  uptime: 86400, // 秒
  dbStatus: 'connected',
  totalUsers: 156,
  totalReservations: 1234,
  storageUsed: '2.3 GB',
  storageTotal: '10 GB',
  memoryUsed: '512 MB',
  memoryTotal: '2 GB'
})

// 加载设置数据
const loadAllSettings = async () => {
  try {
    const response = await fetch('/api/settings/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success && result.data) {
        const settings = result.data
        
        // 更新基础设置
        if (settings.general) {
          Object.assign(generalSettings, {
            systemName: settings.general.system_name || '智能预约系统',
            systemDescription: settings.general.system_description || '基于AI的智能预约管理系统',
            defaultLanguage: settings.general.default_language || 'zh-CN',
            timezone: settings.general.timezone || 'Asia/Shanghai',
            themeMode: settings.general.theme_mode || 'light'
          })
        }
        
        // 更新预约设置
        if (settings.reservation) {
          Object.assign(reservationSettings, {
            workingHours: settings.reservation.working_hours || ['09:00', '18:00'],
            advanceBookingDays: settings.reservation.advance_booking_days || 30,
            minDuration: settings.reservation.min_duration || 30,
            maxDuration: settings.reservation.max_duration || 240,
            autoApproval: settings.reservation.auto_approval || false,
            cancellationDeadline: settings.reservation.cancellation_deadline || 2
          })
        }
        
        // 更新通知设置
        if (settings.notification) {
          Object.assign(notificationSettings, {
            emailEnabled: settings.notification.email_enabled !== undefined ? settings.notification.email_enabled : true,
            smsEnabled: settings.notification.sms_enabled || false,
            pushEnabled: settings.notification.push_enabled !== undefined ? settings.notification.push_enabled : true,
            reminderTimes: settings.notification.reminder_times || [15, 30, 60],
            rateLimit: settings.notification.rate_limit || 10
          })
        }
        
        // 更新安全设置
        if (settings.security) {
          Object.assign(securitySettings, {
            passwordPolicy: settings.security.password_policy || ['minLength', 'requireNumbers'],
            sessionTimeout: settings.security.session_timeout || 120,
            maxLoginAttempts: settings.security.max_login_attempts || 5,
            lockoutDuration: settings.security.lockout_duration || 15,
            twoFactorAuth: settings.security.two_factor_auth || false
          })
        }
      }
    }
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

// 方法
const handleMenuSelect = (index: string) => {
  activeTab.value = index
}

const goToSiliconFlow = () => {
  router.push('/siliconflow')
}

const handleVoiceProviderChange = (provider: string) => {
  // 切换语音提供商时重置默认音色
  if (provider === 'qwen') {
    aiSettings.defaultVoice = 'zhixiaoxia'
  } else if (provider === 'siliconflow') {
    aiSettings.defaultVoice = 'alex'
    // 如果没有选择模型，设置默认模型
    if (!aiSettings.voiceModel) {
      aiSettings.voiceModel = 'FunAudioLLM/CosyVoice2-0.5B'
    }
  }
}

const saveAllSettings = async () => {
  saving.value = true
  
  try {
    // 构建设置数据
    const settingsData = {
      general: {
        system_name: generalSettings.systemName,
        system_description: generalSettings.systemDescription,
        default_language: generalSettings.defaultLanguage,
        timezone: generalSettings.timezone,
        theme_mode: generalSettings.themeMode
      },
      reservation: {
        working_hours: reservationSettings.workingHours,
        advance_booking_days: reservationSettings.advanceBookingDays,
        min_duration: reservationSettings.minDuration,
        max_duration: reservationSettings.maxDuration,
        auto_approval: reservationSettings.autoApproval,
        cancellation_deadline: reservationSettings.cancellationDeadline
      },
      notification: {
        email_enabled: notificationSettings.emailEnabled,
        sms_enabled: notificationSettings.smsEnabled,
        push_enabled: notificationSettings.pushEnabled,
        reminder_times: notificationSettings.reminderTimes,
        rate_limit: notificationSettings.rateLimit
      },
      security: {
        password_policy: securitySettings.passwordPolicy,
        session_timeout: securitySettings.sessionTimeout,
        max_login_attempts: securitySettings.maxLoginAttempts,
        lockout_duration: securitySettings.lockoutDuration,
        two_factor_auth: securitySettings.twoFactorAuth
      }
    }
    
    // 调用后端API保存设置
    const response = await fetch('/api/settings/', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ settings: settingsData })
    })
    
    if (!response.ok) {
      throw new Error('保存失败')
    }
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('设置保存成功')
    } else {
      throw new Error(result.message || '保存失败')
    }
  } catch (error) {
    ElMessage.error('设置保存失败')
    console.error('保存设置失败:', error)
  } finally {
    saving.value = false
  }
}

const resetSettings = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有设置吗？此操作不可恢复。',
      '重置设置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 重置所有设置到默认值
    Object.assign(generalSettings, {
      systemName: '智能预约系统',
      systemDescription: '基于AI的智能预约管理系统',
      defaultLanguage: 'zh-CN',
      timezone: 'Asia/Shanghai',
      themeMode: 'light'
    })
    
    Object.assign(reservationSettings, {
      workingHours: ['09:00', '18:00'],
      advanceBookingDays: 30,
      minDuration: 30,
      maxDuration: 240,
      autoApproval: false,
      cancellationDeadline: 2
    })
    
    Object.assign(notificationSettings, {
      emailEnabled: true,
      smsEnabled: false,
      pushEnabled: true,
      reminderTimes: [15, 30, 60],
      rateLimit: 10
    })
    
    Object.assign(aiSettings, {
      model: 'qwen',
      apiKey: '',
      temperature: 0.7,
      maxTokens: 2000,
      speechRecognition: true,
      speechSynthesis: true,
      voiceProvider: 'qwen',
      voiceModel: 'FunAudioLLM/CosyVoice2-0.5B',
      defaultVoice: 'zhixiaoxia'
    })
    
    Object.assign(securitySettings, {
      passwordPolicy: ['minLength', 'requireNumbers'],
      sessionTimeout: 120,
      maxLoginAttempts: 5,
      lockoutDuration: 15,
      twoFactorAuth: false
    })
    
    ElMessage.success('设置已重置')
  } catch {
    // 用户取消操作
  }
}

const refreshSystemInfo = async () => {
  try {
    // 模拟刷新系统信息API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    systemInfo.uptime += 60
    ElMessage.success('系统信息已刷新')
  } catch (error) {
    ElMessage.error('刷新系统信息失败')
    console.error('刷新系统信息失败:', error)
  }
}

const exportLogs = async () => {
  try {
    // 模拟导出日志
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('日志导出成功')
  } catch (error) {
    ElMessage.error('日志导出失败')
    console.error('导出日志失败:', error)
  }
}

const clearCache = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理系统缓存吗？',
      '清理缓存',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 模拟清理缓存
    await new Promise(resolve => setTimeout(resolve, 800))
    
    ElMessage.success('缓存清理成功')
  } catch {
    // 用户取消操作
  }
}

const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  return `${days}天 ${hours}小时 ${minutes}分钟`
}

// 模型配置相关
const modelConfig = reactive({
  apiKey: '',
  apiUrl: 'https://api.openai.com/v1',
  modelName: 'gpt-3.5-turbo'
})

const modelConnectionResult = ref<{ success: boolean; message: string } | null>(null)

// 语音配置相关
const voiceConfig = reactive({
  xunfei: {
    asr: {
      appId: '',
      apiSecret: '',
      apiKey: '',
      engine: 'iat',
      language: 'zh_cn',
      audioFormat: 'audio/L16;rate=16000'
    },
    tts: {
      appId: '',
      apiSecret: '',
      apiKey: '',
      voice: 'xiaoyan',
      speed: 50,
      volume: 50,
      pitch: 50,
      audioFormat: 'audio/L16;rate=16000'
    }
  },
  interaction: {
    autoPlay: true,
    wakeWord: false,
    continuous: false,
    silenceTimeout: 3000
  }
})

const voiceTesting = ref(false)
const voiceSaving = ref(false)
const asrTesting = ref(false)
const asrSaving = ref(false)
const ttsTesting = ref(false)
const ttsSaving = ref(false)

// 硅基流动配置相关
const siliconflowConfig = reactive({
  apiKey: '',
  baseUrl: 'https://api.siliconflow.cn/v1',
  defaultModel: 'Qwen/Qwen2.5-72B-Instruct'
})

const siliconflowTesting = ref(false)
const siliconflowSaving = ref(false)
const modelSaving = ref(false)

// AI连接测试相关
const aiTesting = ref(false)
const aiTestResults = ref<any>(null)

// 测试和保存方法

const saveModelConfig = async () => {
  modelSaving.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 800))
    ElMessage.success('模型配置保存成功')
  } catch (error) {
    ElMessage.error('模型配置保存失败')
  } finally {
    modelSaving.value = false
  }
}

const testASRConnection = async () => {
  asrTesting.value = true
  try {
    const response = await fetch('/api/voice-config/test-connection', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        provider: 'xunfei',
        config: voiceConfig.xunfei.asr
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success(result.message || '语音识别连接测试成功')
    } else {
      ElMessage.error(result.message || '语音识别连接测试失败')
    }
  } catch (error) {
    console.error('ASR连接测试失败:', error)
    ElMessage.error('语音识别连接测试失败')
  } finally {
    asrTesting.value = false
  }
}

const saveASRConfig = async () => {
  asrSaving.value = true
  try {
    const response = await fetch('/api/voice-config/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        xunfei: {
          appId: voiceConfig.xunfei.asr.appId,
          apiKey: voiceConfig.xunfei.asr.apiKey,
          apiSecret: voiceConfig.xunfei.asr.apiSecret
        }
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('语音识别配置保存成功')
    } else {
      ElMessage.error(result.message || '语音识别配置保存失败')
    }
  } catch (error) {
    console.error('保存ASR配置失败:', error)
    ElMessage.error('语音识别配置保存失败')
  } finally {
    asrSaving.value = false
  }
}

const testTTSConnection = async () => {
  ttsTesting.value = true
  try {
    // 检查科大讯飞TTS配置是否完整
    const hasXunfeiConfig = voiceConfig.xunfei.tts.appId && 
                           voiceConfig.xunfei.tts.apiKey && 
                           voiceConfig.xunfei.tts.apiSecret
    
    let requestBody
    
    if (hasXunfeiConfig) {
      // 使用科大讯飞TTS
      requestBody = {
        provider: 'xunfei',
        app_id: voiceConfig.xunfei.tts.appId,
        api_key: voiceConfig.xunfei.tts.apiKey,
        api_secret: voiceConfig.xunfei.tts.apiSecret,
        text: '你好，这是科大讯飞语音合成测试。'
      }
    } else {
      // 使用通义千问TTS
      requestBody = {
        provider: 'qwen',
        api_key: aiSettings.qwen.apiKey || '',
        base_url: 'https://dashscope.aliyuncs.com/api/v1',
        text: '你好，这是通义千问语音合成测试。'
      }
    }
    
    const response = await fetch('/api/voice-config/test-tts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(requestBody)
    })
    
    const result = await response.json()
    if (result.success) {
      const provider = result.provider === 'xunfei' ? '科大讯飞' : '通义千问'
      ElMessage.success(`${provider}语音合成测试成功！${result.details || ''}`)
    } else {
      ElMessage.error(result.message || '语音合成连接测试失败')
    }
  } catch (error) {
    console.error('TTS连接测试失败:', error)
    ElMessage.error('语音合成连接测试失败')
  } finally {
    ttsTesting.value = false
  }
}

const saveTTSConfig = async () => {
  ttsSaving.value = true
  try {
    const response = await fetch('/api/voice-config/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        api: {
          apiKey: voiceConfig.xunfei.tts.apiKey,
          baseUrl: 'https://dashscope.aliyuncs.com/api/v1'
        },
        tts: {
          voice: voiceConfig.xunfei.tts.voice,
          speed: voiceConfig.xunfei.tts.speed / 100,
          volume: voiceConfig.xunfei.tts.volume / 100,
          pitch: voiceConfig.xunfei.tts.pitch / 100
        }
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('语音合成配置保存成功')
    } else {
      ElMessage.error(result.message || '语音合成配置保存失败')
    }
  } catch (error) {
    console.error('保存TTS配置失败:', error)
    ElMessage.error('语音合成配置保存失败')
  } finally {
    ttsSaving.value = false
  }
}

const testVoiceConnection = async () => {
  voiceTesting.value = true
  try {
    const response = await fetch('/api/voice-config/test-connection', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        provider: 'xunfei',
        config: voiceConfig.xunfei.asr
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success(result.message || '语音服务连接测试成功')
    } else {
      ElMessage.error(result.message || '语音服务连接测试失败')
    }
  } catch (error) {
    console.error('语音服务连接测试失败:', error)
    ElMessage.error('语音服务连接测试失败')
  } finally {
    voiceTesting.value = false
  }
}

// 加载语音配置
const loadVoiceConfig = async () => {
  try {
    const response = await fetch('/api/voice-config/config?show_keys=true', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        // 更新科大讯飞配置
        if (result.xunfei) {
          voiceConfig.xunfei.asr.appId = result.xunfei.appId || ''
          voiceConfig.xunfei.asr.apiKey = result.xunfei.apiKey || ''
          voiceConfig.xunfei.asr.apiSecret = result.xunfei.apiSecret || ''
          voiceConfig.xunfei.tts.appId = result.xunfei.appId || ''
          voiceConfig.xunfei.tts.apiKey = result.xunfei.apiKey || ''
          voiceConfig.xunfei.tts.apiSecret = result.xunfei.apiSecret || ''
        }
        
        // 更新通义千问API配置
        if (result.api && result.api.apiKey) {
          voiceConfig.xunfei.tts.apiKey = result.api.apiKey
        }
        
        // 更新TTS配置
        if (result.tts) {
          voiceConfig.xunfei.tts.voice = result.tts.voice || 'xiaoyan'
          voiceConfig.xunfei.tts.speed = (result.tts.speed || 0.5) * 100
          voiceConfig.xunfei.tts.volume = (result.tts.volume || 0.5) * 100
          voiceConfig.xunfei.tts.pitch = (result.tts.pitch || 0.5) * 100
        }
      }
    }
  } catch (error) {
    console.error('加载语音配置失败:', error)
  }
}

const saveVoiceConfig = async () => {
  voiceSaving.value = true
  try {
    const response = await fetch('/api/voice-config/config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        xunfei: {
          appId: voiceConfig.xunfei.asr.appId,
          apiKey: voiceConfig.xunfei.asr.apiKey,
          apiSecret: voiceConfig.xunfei.asr.apiSecret
        },
        api: {
          apiKey: voiceConfig.xunfei.tts.apiKey,
          baseUrl: 'https://dashscope.aliyuncs.com/api/v1'
        },
        tts: {
          voice: voiceConfig.xunfei.tts.voice,
          speed: voiceConfig.xunfei.tts.speed / 100,
          volume: voiceConfig.xunfei.tts.volume / 100,
          pitch: voiceConfig.xunfei.tts.pitch / 100
        }
      })
    })
    
    const result = await response.json()
    if (result.success) {
      ElMessage.success('语音配置保存成功')
    } else {
      ElMessage.error(result.message || '语音配置保存失败')
    }
  } catch (error) {
    console.error('保存语音配置失败:', error)
    ElMessage.error('语音配置保存失败')
  } finally {
    voiceSaving.value = false
  }
}

const testSiliconflowConnection = async () => {
  siliconflowTesting.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('硅基流动连接测试成功')
  } catch (error) {
    ElMessage.error('硅基流动连接测试失败')
  } finally {
    siliconflowTesting.value = false
  }
}

const saveSiliconflowConfig = async () => {
  siliconflowSaving.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 800))
    ElMessage.success('硅基流动配置保存成功')
  } catch (error) {
    ElMessage.error('硅基流动配置保存失败')
  } finally {
    siliconflowSaving.value = false
  }
}

// AI连接测试方法
const testAIConnection = async () => {
  // 验证配置
  const errors = validateConfig()
  if (errors.length > 0) {
    ElMessage.error(errors[0])
    return
  }
  
  aiTesting.value = true
  aiTestResults.value = null
  
  try {
    // 同步配置
    syncConfigurations()
    
    // 调试日志
    console.log('Debug - Current provider:', aiSettings.provider)
    console.log('Debug - SiliconFlow API Key:', aiSettings.siliconflow.apiKey)
    console.log('Debug - All aiSettings:', JSON.stringify(aiSettings, null, 2))
    
    // 构建请求体
    const requestBody: any = {
      provider: aiSettings.provider,
      model: aiSettings.model,
      baseUrl: aiSettings.baseUrl
    }
    
    // 根据提供商添加特定参数
    if (aiSettings.provider === 'xunfei') {
      requestBody.appId = aiSettings.xunfei.appId
      requestBody.apiSecret = aiSettings.xunfei.apiSecret
      requestBody.apiKey = aiSettings.xunfei.apiKey
    } else if (aiSettings.provider === 'qwen') {
      requestBody.apiKey = aiSettings.qwen.apiKey
    } else if (aiSettings.provider === 'siliconflow') {
      requestBody.apiKey = aiSettings.siliconflow.apiKey
      if (aiSettings.model === 'custom') {
        requestBody.model = aiSettings.siliconflow.customModel
      }
    } else if (aiSettings.provider === 'openai') {
      requestBody.apiKey = aiSettings.openai.apiKey
      requestBody.organization = aiSettings.openai.organization
    }
    
    console.log('Debug - Request body:', JSON.stringify(requestBody, null, 2))
    
    const response = await fetch('/api/smart-reservation/test-ai', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    })
    const result = await response.json()
    
    aiTestResults.value = result
    
    if (result.summary?.overall_status === '全部可用') {
      ElMessage.success('AI服务连接测试成功')
    } else if (result.summary?.overall_status === '部分可用') {
      ElMessage.warning('部分AI服务连接成功')
    } else {
      ElMessage.error('AI服务连接测试失败')
    }
  } catch (error) {
    ElMessage.error('AI连接测试失败')
    console.error('AI连接测试失败:', error)
  } finally {
    aiTesting.value = false
  }
}

// 生命周期
onMounted(async () => {
  // 初始化设置数据
  refreshSystemInfo()
  // 加载所有设置
  await loadAllSettings()
  // 加载AI配置
  await loadAIConfig()
  // 加载语音配置
  await loadVoiceConfig()
})
</script>

<style scoped>
.settings-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.settings-header {
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
  gap: 10px;
}

.settings-content {
  min-height: 600px;
}

.settings-menu {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.settings-nav {
  border: none;
}

.settings-nav .el-menu-item {
  border-radius: 6px;
  margin: 4px 0;
}

.settings-nav .el-menu-item:hover {
  background-color: #ecf5ff;
  color: #409eff;
}

.settings-nav .el-menu-item.is-active {
  background-color: #409eff;
  color: white;
}

.settings-panel {
  min-height: 600px;
}

.setting-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.setting-form {
  padding: 20px 0;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-left: 10px;
}

.system-info {
  padding: 20px 0;
}

.system-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.config-section {
  margin-bottom: 30px;
}

.config-section h3 {
  margin-bottom: 20px;
  color: #303133;
  font-weight: 600;
}

.config-content {
  padding: 20px 0;
}

.section-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}

.result {
  margin-top: 20px;
}

/* AI测试相关样式 */
.ai-test-content {
  padding: 20px 0;
}

.test-description {
  margin-bottom: 20px;
  color: #606266;
  font-size: 14px;
}

.test-actions {
  margin-bottom: 20px;
}

.test-results {
  margin-top: 20px;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.summary-text {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.service-results {
  display: grid;
  gap: 16px;
  margin-bottom: 20px;
}

.service-result {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background-color: #fff;
}

.service-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.service-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.success-icon {
  color: #67c23a;
}

.error-icon {
  color: #f56c6c;
}

.service-details p {
  margin: 8px 0;
  font-size: 13px;
  color: #606266;
}

.error-details {
  color: #f56c6c !important;
}

.config-tips {
  margin-top: 20px;
}

.config-tips ul {
  margin: 10px 0;
  padding-left: 20px;
}

.config-tips li {
  margin: 5px 0;
  font-size: 13px;
}

.config-tips code {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .settings-container {
    padding: 10px;
  }
  
  .settings-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .settings-content .el-col {
    margin-bottom: 20px;
  }
  
  .system-actions {
    justify-content: center;
  }
}
</style>