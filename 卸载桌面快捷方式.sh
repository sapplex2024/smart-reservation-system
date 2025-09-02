#!/bin/bash

# 桌面快捷方式卸载脚本
# 从桌面和应用程序菜单中移除智能预约系统快捷方式

echo "正在卸载智能预约系统桌面快捷方式..."

# 从桌面移除
if [ -f "$HOME/Desktop/智能预约系统.desktop" ]; then
    rm "$HOME/Desktop/智能预约系统.desktop"
    echo "✅ 已从桌面移除"
else
    echo "ℹ️  桌面上没有找到快捷方式"
fi

# 从应用程序菜单移除
if [ -f "$HOME/.local/share/applications/智能预约系统.desktop" ]; then
    rm "$HOME/.local/share/applications/智能预约系统.desktop"
    echo "✅ 已从应用程序菜单移除"
else
    echo "ℹ️  应用程序菜单中没有找到快捷方式"
fi

# 更新桌面数据库
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications"
    echo "✅ 已更新应用程序数据库"
fi

echo ""
echo "🎉 桌面快捷方式卸载完成！"
echo ""
echo "您仍然可以使用以下方式启动系统："
echo "1. 命令行: ./启动智能预约系统.sh"
echo "2. 重新安装快捷方式: ./安装桌面快捷方式.sh"