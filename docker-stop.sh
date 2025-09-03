#!/bin/bash

# Docker环境停止脚本

set -e

echo "🛑 停止智能预约系统 Docker 环境..."

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 停止所有服务
echo "⏹️  停止所有服务..."
docker-compose down

# 显示停止的容器
echo "📋 已停止的服务:"
docker-compose ps -a

echo "✅ 智能预约系统已停止！"
echo ""
echo "💡 其他操作:"
echo "🔄 重新启动: ./docker-start.sh"
echo "🗑️  清理数据: docker-compose down -v"
echo "🧹 清理镜像: docker-compose down --rmi all"
echo "📝 查看日志: docker-compose logs"