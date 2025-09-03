#!/bin/bash

# 智能预约系统本地开发环境启动脚本
# 使用本地Python环境和Redis服务

echo "=== 智能预约系统本地开发环境启动 ==="

# 检查Redis服务状态
echo "检查Redis服务状态..."
if ! systemctl is-active --quiet redis-server; then
    echo "启动Redis服务..."
    sudo systemctl start redis-server
    sleep 2
fi

if systemctl is-active --quiet redis-server; then
    echo "✓ Redis服务运行正常"
else
    echo "✗ Redis服务启动失败"
    exit 1
fi

# 进入后端目录
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 设置环境变量
export DATABASE_URL="sqlite:///./reservations.db"
export SECRET_KEY="dev-secret-key-12345"
export ALGORITHM="HS256"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"
export DEVELOPMENT="true"
export DEBUG="true"
export REDIS_URL="redis://localhost:6379"
export API_HOST="0.0.0.0"
export API_PORT="8000"

# 初始化数据库
echo "初始化数据库..."
python scripts/init_db.py

# 创建管理员用户
echo "创建管理员用户..."
python init_admin.py

echo "\n=== 启动后端API服务 ==="
echo "后端服务地址: http://localhost:8000"
echo "API文档地址: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务"
echo "\n开始启动..."

# 启动后端服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload