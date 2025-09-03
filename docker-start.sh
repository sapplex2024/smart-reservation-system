#!/bin/bash

# Docker环境启动脚本

set -e

echo "🚀 启动智能预约系统 Docker 环境..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p backend/logs
mkdir -p backend/static
mkdir -p nginx/ssl

# 复制环境配置文件
if [ ! -f .env ]; then
    echo "📋 复制环境配置文件..."
    cp .env.docker .env
fi

# 构建并启动服务
echo "🔨 构建 Docker 镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose ps

# 显示服务URL
echo ""
echo "✅ 智能预约系统已启动！"
echo "📱 前端访问地址: http://localhost:3000"
echo "🔧 后端API地址: http://localhost:8000"
echo "📊 API文档地址: http://localhost:8000/docs"
echo ""
echo "📝 查看日志: docker-compose logs -f"
echo "🛑 停止服务: docker-compose down"
echo "🔄 重启服务: docker-compose restart"
echo ""

# 检查服务健康状态
echo "🏥 检查服务健康状态..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✅ 后端服务健康检查通过"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  后端服务健康检查超时，请检查日志"
    fi
    sleep 2
done

for i in {1..30}; do
    if curl -f http://localhost:3000/health &> /dev/null; then
        echo "✅ 前端服务健康检查通过"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  前端服务健康检查超时，请检查日志"
    fi
    sleep 2
done

echo "🎉 系统启动完成！"