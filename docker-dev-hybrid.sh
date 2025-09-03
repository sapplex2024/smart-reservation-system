#!/bin/bash

# Docker混合开发环境脚本（仅Redis容器化）

set -e

echo "🔧 启动智能预约系统混合开发环境..."

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

echo "📁 创建必要的目录..."
mkdir -p backend/logs
mkdir -p backend/static

# 启动Redis容器
echo "🚀 启动Redis容器..."
sudo docker compose -f docker-compose.dev-simple.yml up -d

echo "⏳ 等待Redis启动..."
sleep 3

# 显示服务状态
echo "🔍 Redis容器状态:"
sudo docker compose -f docker-compose.dev-simple.yml ps

# 启动后端服务（本地）
echo "🚀 启动后端服务（本地）..."
cd backend
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3.12 -m venv venv
fi

source venv/bin/activate
echo "📦 安装后端依赖..."
pip install -r requirements.txt

# 更新环境变量以使用Docker Redis
export REDIS_URL="redis://localhost:6379/0"
export DATABASE_URL="sqlite:///./reservations.db"
export SECRET_KEY="dev-secret-key"
export DEVELOPMENT="true"
export DEBUG="true"

echo "🔧 初始化数据库..."
python scripts/init_db.py

echo "🚀 启动后端API服务..."
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
echo "后端服务已启动，PID: $BACKEND_PID"

cd ..

# 启动前端服务（本地）
echo "🚀 启动前端服务（本地）..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

echo "🚀 启动前端开发服务..."
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
echo "前端服务已启动，PID: $FRONTEND_PID"

cd ..

echo ""
echo "✅ 混合开发环境已启动！"
echo "🔧 后端API地址: http://localhost:8000"
echo "📊 API文档地址: http://localhost:8000/docs"
echo "🌐 前端地址: http://localhost:3000"
echo "🗄️  Redis地址: localhost:6379"
echo ""
echo "💡 开发提示:"
echo "📝 查看后端日志: tail -f logs/backend.log"
echo "📝 查看前端日志: tail -f logs/frontend.log"
echo "📝 查看Redis日志: sudo docker compose -f docker-compose.dev-simple.yml logs -f redis"
echo "🔄 重启后端: kill \$(cat backend.pid) && cd backend && source venv/bin/activate && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 & echo \$! > ../backend.pid"
echo "🔄 重启前端: kill \$(cat frontend.pid) && cd frontend && nohup npm run dev > ../logs/frontend.log 2>&1 & echo \$! > ../frontend.pid"
echo "🛑 停止开发环境: ./停止智能预约系统.sh && sudo docker compose -f docker-compose.dev-simple.yml down"
echo "🐚 进入Redis容器: sudo docker exec -it smart-reservation-redis-dev redis-cli"
echo ""