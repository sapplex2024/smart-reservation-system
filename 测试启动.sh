#!/bin/bash

# 智能预约系统启动测试脚本
# 用于快速验证系统是否能正常启动

echo "开始测试智能预约系统启动..."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查必要文件
echo "检查必要文件..."
if [ ! -f "启动智能预约系统.sh" ]; then
    echo "❌ 启动脚本不存在"
    exit 1
fi

if [ ! -f "停止智能预约系统.sh" ]; then
    echo "❌ 停止脚本不存在"
    exit 1
fi

if [ ! -f "智能预约系统.desktop" ]; then
    echo "❌ 桌面快捷方式不存在"
    exit 1
fi

echo "✅ 所有启动文件存在"

# 检查权限
echo "检查文件权限..."
if [ ! -x "启动智能预约系统.sh" ]; then
    echo "❌ 启动脚本没有执行权限"
    chmod +x "启动智能预约系统.sh"
    echo "✅ 已修复启动脚本权限"
fi

if [ ! -x "停止智能预约系统.sh" ]; then
    echo "❌ 停止脚本没有执行权限"
    chmod +x "停止智能预约系统.sh"
    echo "✅ 已修复停止脚本权限"
fi

if [ ! -x "智能预约系统.desktop" ]; then
    echo "❌ 桌面快捷方式没有执行权限"
    chmod +x "智能预约系统.desktop"
    echo "✅ 已修复桌面快捷方式权限"
fi

echo "✅ 所有文件权限正常"

# 检查环境
echo "检查运行环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    echo "请安装Python3: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
echo "✅ Python3 已安装: $(python3 --version)"

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "请安装Node.js: https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js 已安装: $(node --version)"

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi
echo "✅ npm 已安装: $(npm --version)"

# 检查项目结构
echo "检查项目结构..."
if [ ! -d "backend" ]; then
    echo "❌ backend 目录不存在"
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo "❌ frontend 目录不存在"
    exit 1
fi

if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ backend/requirements.txt 不存在"
    exit 1
fi

if [ ! -f "frontend/package.json" ]; then
    echo "❌ frontend/package.json 不存在"
    exit 1
fi

echo "✅ 项目结构完整"

# 检查端口占用
echo "检查端口占用..."
if lsof -i :3000 &> /dev/null; then
    echo "⚠️  端口3000被占用，可能需要停止现有服务"
else
    echo "✅ 端口3000可用"
fi

if lsof -i :8000 &> /dev/null; then
    echo "⚠️  端口8000被占用，可能需要停止现有服务"
else
    echo "✅ 端口8000可用"
fi

echo ""
echo "🎉 系统启动测试完成！"
echo ""
echo "启动方式："
echo "1. 命令行启动: ./启动智能预约系统.sh"
echo "2. 桌面快捷方式: 双击 智能预约系统.desktop"
echo "3. 复制到桌面: cp 智能预约系统.desktop ~/Desktop/"
echo ""
echo "访问地址："
echo "- 前端: http://localhost:3000"
echo "- 后端: http://localhost:8000"
echo "- API文档: http://localhost:8000/docs"
echo ""
echo "默认账户: admin / admin123"
echo ""
echo "如需帮助，请查看 启动说明.md 文件"