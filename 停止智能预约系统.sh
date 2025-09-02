#!/bin/bash

# 智能预约系统停止脚本
# 作者：系统开发团队
# 版本：1.0

echo "正在停止智能预约系统..."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 停止后端服务
if [ -f "backend.pid" ]; then
    BACKEND_PID=$(cat backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 2
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "强制停止后端服务..."
            kill -9 $BACKEND_PID
        fi
        echo "后端服务已停止"
    else
        echo "后端服务未运行"
    fi
    rm -f backend.pid
else
    echo "未找到后端服务PID文件"
fi

# 停止前端服务
if [ -f "frontend.pid" ]; then
    FRONTEND_PID=$(cat frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 2
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "强制停止前端服务..."
            kill -9 $FRONTEND_PID
        fi
        echo "前端服务已停止"
    else
        echo "前端服务未运行"
    fi
    rm -f frontend.pid
else
    echo "未找到前端服务PID文件"
fi

# 清理可能残留的进程
echo "清理残留进程..."
pkill -f "uvicorn app.main:app"
pkill -f "npm run dev"
pkill -f "vite"

echo "智能预约系统已完全停止"