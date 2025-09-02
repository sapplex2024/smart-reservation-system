#!/bin/bash

# 智能预约系统启动脚本
# 作者：系统开发团队
# 版本：1.0

echo "正在启动智能预约系统..."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python3，请先安装Python3"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "错误：未找到Node.js，请先安装Node.js"
    exit 1
fi

# 启动后端服务
echo "启动后端服务..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "检查并安装Python依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "初始化数据库..."
python scripts/init_db.py

# 启动后端服务（后台运行）
echo "启动FastAPI后端服务..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务已启动，PID: $BACKEND_PID"

# 返回项目根目录
cd ..

# 启动前端服务
echo "启动前端服务..."
cd frontend

# 安装前端依赖
echo "检查并安装前端依赖..."
npm install

# 启动前端开发服务器（后台运行）
echo "启动Vue.js前端服务..."
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端服务已启动，PID: $FRONTEND_PID"

# 返回项目根目录
cd ..

# 创建PID文件
echo $BACKEND_PID > backend.pid
echo $FRONTEND_PID > frontend.pid

echo "系统启动完成！"
echo "前端访问地址: http://localhost:3000"
echo "后端API地址: http://localhost:8000"
echo "API文档地址: http://localhost:8000/docs"
echo ""
echo "要停止服务，请运行: ./停止智能预约系统.sh"
echo "查看日志: tail -f logs/backend.log 或 tail -f logs/frontend.log"

# 等待3秒后自动打开浏览器
sleep 3
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000
elif command -v gnome-open &> /dev/null; then
    gnome-open http://localhost:3000
fi

echo "按Ctrl+C退出监控模式"
# 保持脚本运行，监控服务状态
while true; do
    sleep 10
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "警告：后端服务已停止"
        break
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "警告：前端服务已停止"
        break
    fi
done