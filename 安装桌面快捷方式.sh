#!/bin/bash

# 桌面快捷方式安装脚本
# 将智能预约系统快捷方式添加到桌面和应用程序菜单

echo "正在安装智能预约系统桌面快捷方式..."

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查桌面快捷方式文件是否存在
if [ ! -f "智能预约系统.desktop" ]; then
    echo "❌ 桌面快捷方式文件不存在"
    exit 1
fi

# 确保快捷方式文件有执行权限
chmod +x "智能预约系统.desktop"

# 创建桌面目录（如果不存在）
if [ ! -d "$HOME/Desktop" ]; then
    mkdir -p "$HOME/Desktop"
    echo "✅ 创建桌面目录"
fi

# 创建应用程序目录（如果不存在）
if [ ! -d "$HOME/.local/share/applications" ]; then
    mkdir -p "$HOME/.local/share/applications"
    echo "✅ 创建应用程序目录"
fi

# 复制到桌面
cp "智能预约系统.desktop" "$HOME/Desktop/"
chmod +x "$HOME/Desktop/智能预约系统.desktop"
echo "✅ 已添加到桌面"

# 复制到应用程序菜单
cp "智能预约系统.desktop" "$HOME/.local/share/applications/"
echo "✅ 已添加到应用程序菜单"

# 更新桌面数据库
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications"
    echo "✅ 已更新应用程序数据库"
fi

# 检查图标文件
if [ -f "icon.svg" ]; then
    echo "✅ 图标文件存在"
else
    echo "⚠️  图标文件不存在，快捷方式可能显示默认图标"
fi

echo ""
echo "🎉 桌面快捷方式安装完成！"
echo ""
echo "现在您可以："
echo "1. 在桌面上找到'智能预约系统'图标并双击启动"
echo "2. 在应用程序菜单中找到'智能预约系统'并启动"
echo "3. 使用命令行: ./启动智能预约系统.sh"
echo ""
echo "如需卸载快捷方式，请运行: ./卸载桌面快捷方式.sh"