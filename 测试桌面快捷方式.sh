#!/bin/bash

# 测试桌面快捷方式
echo "=== 桌面快捷方式测试 ==="

# 检查桌面文件是否存在
if [ -f ~/Desktop/智能预约系统.desktop ]; then
    echo "✅ 桌面快捷方式文件存在"
    ls -la ~/Desktop/智能预约系统.desktop
else
    echo "❌ 桌面快捷方式文件不存在"
fi

# 检查文件权限
echo ""
echo "=== 文件权限检查 ==="
stat ~/Desktop/智能预约系统.desktop 2>/dev/null || echo "无法获取文件状态"

# 检查桌面环境
echo ""
echo "=== 桌面环境信息 ==="
echo "桌面环境: $XDG_CURRENT_DESKTOP"
echo "会话类型: $XDG_SESSION_TYPE"
echo "显示服务器: $XDG_SESSION_DESKTOP"

# 检查是否可以执行
echo ""
echo "=== 快捷方式验证 ==="
desktop-file-validate ~/Desktop/智能预约系统.desktop 2>&1 || echo "验证失败"

echo ""
echo "=== 建议解决方案 ==="
echo "1. 右键点击桌面快捷方式，选择'允许启动'"
echo "2. 或者双击快捷方式时选择'信任并启动'"
echo "3. 如果仍然不显示，请重启桌面环境或注销重新登录"
echo "4. 也可以直接运行: ./启动智能预约系统.sh"