@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 正在启动智能预约系统...

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

:: 检查Node.js环境
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

:: 创建日志目录
if not exist "logs" mkdir logs

:: 启动后端服务
echo 启动后端服务...
cd backend

:: 检查虚拟环境
if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 安装依赖
echo 检查并安装Python依赖...
pip install -r requirements.txt

:: 初始化数据库
echo 初始化数据库...
python scripts\init_db.py

:: 启动后端服务
echo 启动FastAPI后端服务...
start "后端服务" /min cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ..\logs\backend.log 2>&1"

:: 等待后端服务启动
timeout /t 5 /nobreak >nul

:: 返回项目根目录
cd ..

:: 启动前端服务
echo 启动前端服务...
cd frontend

:: 安装前端依赖
echo 检查并安装前端依赖...
npm install

:: 启动前端开发服务器
echo 启动Vue.js前端服务...
start "前端服务" /min cmd /c "npm run dev > ..\logs\frontend.log 2>&1"

:: 返回项目根目录
cd ..

echo 系统启动完成！
echo 前端访问地址: http://localhost:3000
echo 后端API地址: http://localhost:8000
echo API文档地址: http://localhost:8000/docs
echo.
echo 要停止服务，请运行: 停止智能预约系统.bat
echo 查看日志: type logs\backend.log 或 type logs\frontend.log
echo.

:: 等待3秒后自动打开浏览器
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo 按任意键退出...
pause >nul