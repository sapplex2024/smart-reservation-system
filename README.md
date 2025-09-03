# 智能预约系统 (Smart Reservation System)

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/sapplex2024/smart-reservation-system/releases/tag/v0.3.0)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/vue.js-3.4+-green.svg)](https://vuejs.org/)

一个基于AI驱动的智能预约管理系统，支持会议室、设备和服务的智能预约与管理。

## ✨ 主要特性

### 🤖 智能预约助手
- **自然语言理解**：支持自然语言预约请求，如"明天上午10点预约大会议室"
- **Function Calling**：大模型可直接调用系统功能，实现智能预约操作
- **智能匹配**：基于人数、设备需求等条件智能推荐最适合的资源
- **多轮对话**：支持上下文记忆的连续对话，提供更自然的交互体验

### 🔧 多模型集成
- **多提供商支持**：集成通义千问、讯飞星火、硅基流动、OpenAI等主流AI服务
- **统一管理**：统一的配置界面管理不同AI提供商的API密钥和参数
- **智能切换**：支持根据需求自动选择最适合的AI模型

### 📊 预约管理
- **资源管理**：支持会议室、设备、服务等多种资源类型
- **状态跟踪**：实时跟踪预约状态（待审批、已批准、已拒绝、已取消、已完成）
- **冲突检测**：自动检测时间冲突，避免重复预约
- **批量操作**：支持批量审批、取消等操作

### 📈 数据分析
- **使用统计**：详细的预约使用情况统计和分析
- **趋势分析**：预约趋势图表，帮助优化资源配置
- **用户报表**：个人和部门级别的预约报表

### 🔒 权限管理
- **角色控制**：支持管理员、经理、普通用户等多级权限
- **安全认证**：JWT令牌认证，确保系统安全
- **操作日志**：完整的操作日志记录和审计

## 🚀 快速开始

### 环境要求

- **后端**：Python 3.11+
- **前端**：Node.js 16+
- **数据库**：SQLite（默认）或 PostgreSQL
- **其他**：Redis（可选，用于缓存）

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/sapplex2024/smart-reservation-system.git
cd smart-reservation-system
```

#### 2. 后端设置
```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 4. 访问系统
- 前端界面：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 默认账户

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部权限 |
| 经理 | manager | manager123 | 管理权限 |
| 用户 | user1 | user123 | 基础权限 |

## 🐳 Docker 部署

### 开发环境
```bash
# 启动开发环境
./docker-dev.sh
```

### 生产环境
```bash
# 构建并启动生产环境
docker-compose up -d
```

## 📖 使用指南

### 智能预约示例

1. **自然语言预约**
   ```
   用户："我要预约明天下午2点的大会议室，大概10个人开会，需要投影仪"
   系统："好的，我为您找到了大会议室A，明天14:00-15:00可用，配备投影仪，已为您预约成功"
   ```

2. **智能推荐**
   ```
   用户："需要一个能容纳20人的会议室，要有电视"
   系统："根据您的需求，推荐以下会议室：
         1. 大会议室A - 容纳25人，配备75寸电视
         2. 培训室B - 容纳30人，配备投影仪和电视"
   ```

### AI配置

1. 进入系统设置 → AI配置
2. 选择AI提供商（通义千问、硅基流动等）
3. 配置API密钥和参数
4. 测试连接确保配置正确

### 资源管理

1. 添加会议室、设备等资源
2. 设置资源属性（容量、设备、位置等）
3. 配置预约规则和权限

## 🛠️ 技术架构

### 后端技术栈
- **框架**：FastAPI
- **数据库**：SQLAlchemy + SQLite/PostgreSQL
- **认证**：JWT
- **AI集成**：多提供商SDK
- **异步处理**：asyncio

### 前端技术栈
- **框架**：Vue.js 3 + TypeScript
- **UI组件**：Element Plus
- **状态管理**：Pinia
- **路由**：Vue Router
- **构建工具**：Vite

### 系统架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (Vue.js)  │────│  后端 (FastAPI)  │────│   数据库 (SQLite) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   AI服务集成     │
                       │ (多提供商支持)    │
                       └─────────────────┘
```

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解详细的版本更新记录。

### v0.3.0 主要更新
- ✨ 增强智能预约助手，支持Function Calling
- 🔧 集成硅基流动API，统一多模型管理
- 📊 改进资源匹配算法和实体提取
- 🎨 修复预约状态中文显示问题
- ⚡ 优化系统性能和用户体验

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们

- 项目地址：https://github.com/sapplex2024/smart-reservation-system
- 问题反馈：https://github.com/sapplex2024/smart-reservation-system/issues
- 邮箱：support@smartreservation.com

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和用户！

---

**智能预约系统** - 让预约管理更智能、更高效！