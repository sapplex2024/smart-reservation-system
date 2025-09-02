@echo off
chcp 65001 >nul

echo 正在停止智能预约系统...

:: 停止后端服务
echo 停止后端服务...
taskkill /f /im "python.exe" /fi "WINDOWTITLE eq 后端服务" >nul 2>&1
taskkill /f /im "uvicorn.exe" >nul 2>&1

:: 停止前端服务
echo 停止前端服务...
taskkill /f /im "node.exe" /fi "WINDOWTITLE eq 前端服务" >nul 2>&1
taskkill /f /im "npm.exe" >nul 2>&1

:: 清理可能残留的进程
echo 清理残留进程...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "uvicorn"') do (
    taskkill /f /pid %%i >nul 2>&1
)

for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo csv ^| find "vite"') do (
    taskkill /f /pid %%i >nul 2>&1
)

echo 智能预约系统已完全停止
echo.
echo 按任意键退出...
pause >nul