#!/bin/bash

# Docker开发环境脚本

set -e

echo "🔧 启动智能预约系统开发环境..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建开发环境的docker-compose文件
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'

services:
  # 后端开发服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: smart-reservation-backend-dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./reservations.db
      - SECRET_KEY=dev-secret-key
      - ALGORITHM=HS256
      - ACCESS_TOKEN_EXPIRE_MINUTES=30
      - DEVELOPMENT=true
      - DEBUG=true
    volumes:
      - ./backend:/app
      - ./backend/reservations.db:/app/reservations.db
      - ./backend/logs:/app/logs
    networks:
      - smart-reservation-network
    restart: unless-stopped
    command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Redis服务
  redis:
    image: redis:7-alpine
    container_name: smart-reservation-redis-dev
    ports:
      - "6379:6379"
    networks:
      - smart-reservation-network
    restart: unless-stopped

networks:
  smart-reservation-network:
    driver: bridge
EOF

echo "📁 创建必要的目录..."
mkdir -p backend/logs
mkdir -p backend/static

# 启动开发环境
echo "🚀 启动开发环境..."
docker compose -f docker-compose.dev.yml up -d

echo "⏳ 等待服务启动..."
sleep 5

# 显示服务状态
echo "🔍 服务状态:"
docker compose -f docker-compose.dev.yml ps

echo ""
echo "✅ 开发环境已启动！"
echo "🔧 后端API地址: http://localhost:8000"
echo "📊 API文档地址: http://localhost:8000/docs"
echo "🗄️  Redis地址: localhost:6379"
echo ""
echo "💡 开发提示:"
echo "📝 查看后端日志: docker compose -f docker-compose.dev.yml logs -f backend"
echo "🔄 重启后端: docker compose -f docker-compose.dev.yml restart backend"
echo "🛑 停止开发环境: docker compose -f docker-compose.dev.yml down"
echo "🐚 进入后端容器: docker exec -it smart-reservation-backend-dev bash"
echo ""
echo "📂 前端开发请在本地运行:"
echo "   cd frontend && npm install && npm run dev"