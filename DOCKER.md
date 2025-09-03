# 智能预约系统 Docker 部署指南

本文档介绍如何使用 Docker 部署和运行智能预约系统。

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 5GB 可用磁盘空间

## 🚀 快速启动

### 1. 生产环境部署

```bash
# 启动完整系统
./docker-start.sh
```

系统将在以下地址可用：
- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

### 2. 开发环境部署

```bash
# 启动开发环境（仅后端容器化）
./docker-dev.sh

# 前端本地开发
cd frontend
npm install
npm run dev
```

## 🛠️ 服务架构

### 生产环境服务

- **frontend**: Vue.js 前端应用 (Nginx)
- **backend**: FastAPI 后端服务
- **redis**: Redis 缓存服务
- **nginx**: 反向代理 (可选)

### 开发环境服务

- **backend**: FastAPI 后端服务 (热重载)
- **redis**: Redis 缓存服务

## 📁 目录结构

```
smart-reservation-system/
├── docker-compose.yml          # 生产环境配置
├── docker-compose.dev.yml      # 开发环境配置
├── .env.docker                 # Docker环境变量
├── .dockerignore              # Docker忽略文件
├── docker-start.sh            # 生产环境启动脚本
├── docker-stop.sh             # 停止脚本
├── docker-dev.sh              # 开发环境启动脚本
├── backend/
│   ├── Dockerfile             # 后端镜像构建文件
│   └── ...
├── frontend/
│   ├── Dockerfile             # 前端镜像构建文件
│   ├── nginx.conf             # Nginx配置
│   └── ...
└── nginx/                     # 反向代理配置（可选）
```

## ⚙️ 环境配置

### 环境变量

复制并编辑环境配置文件：

```bash
cp .env.docker .env
```

主要配置项：

```env
# 数据库
DATABASE_URL=sqlite:///./reservations.db

# JWT认证
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI API（可选）
OPENAI_API_KEY=your-openai-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Redis
REDIS_URL=redis://redis:6379/0
```

## 🔧 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
```

### 开发调试

```bash
# 进入后端容器
docker exec -it smart-reservation-backend bash

# 进入前端容器
docker exec -it smart-reservation-frontend sh

# 重新构建镜像
docker-compose build --no-cache

# 清理未使用的镜像
docker system prune -f
```

### 数据管理

```bash
# 备份数据库
docker cp smart-reservation-backend:/app/reservations.db ./backup/

# 恢复数据库
docker cp ./backup/reservations.db smart-reservation-backend:/app/

# 查看数据卷
docker volume ls

# 清理数据卷
docker-compose down -v
```

## 🔍 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8000
   ```

2. **服务启动失败**
   ```bash
   # 查看详细日志
   docker-compose logs backend
   docker-compose logs frontend
   ```

3. **数据库连接问题**
   ```bash
   # 检查数据库文件权限
   ls -la backend/reservations.db
   ```

4. **内存不足**
   ```bash
   # 检查系统资源
   docker stats
   ```

### 健康检查

系统提供了健康检查端点：

- 后端：http://localhost:8000/health
- 前端：http://localhost:3000/health

## 🚀 生产部署建议

### 1. 安全配置

- 修改默认密钥和密码
- 启用 HTTPS
- 配置防火墙规则
- 定期更新镜像

### 2. 性能优化

- 配置适当的资源限制
- 启用日志轮转
- 配置监控和告警
- 使用外部数据库

### 3. 备份策略

- 定期备份数据库
- 备份配置文件
- 测试恢复流程

## 📞 技术支持

如果遇到问题，请：

1. 查看日志文件
2. 检查系统资源
3. 验证网络连接
4. 参考故障排除指南

---

**注意**: 首次启动可能需要几分钟时间来下载镜像和初始化服务。