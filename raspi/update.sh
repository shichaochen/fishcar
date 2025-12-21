#!/bin/bash
# 更新 FishCar 项目代码
# 使用方法: bash update.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR/.."

echo "=========================================="
echo "更新 FishCar 项目代码"
echo "=========================================="

# 检查项目目录是否存在
if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "错误: 项目目录不存在或不是 git 仓库: $PROJECT_DIR"
    echo "请确保项目已通过 git clone 安装"
    exit 1
fi

# 切换到项目目录
cd "$PROJECT_DIR"

# 显示当前状态
echo ""
echo "当前分支:"
git branch --show-current

echo ""
echo "远程仓库状态:"
git remote -v

echo ""
echo "正在拉取最新代码..."
git fetch origin

echo ""
echo "当前本地提交:"
git log --oneline -1

echo ""
echo "远程最新提交:"
git log --oneline -1 origin/main

echo ""
read -p "是否要合并远程更改? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "正在合并远程更改..."
    git pull origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ 代码更新成功！"
        echo ""
        echo "更新后的最新提交:"
        git log --oneline -1
        echo ""
        echo "提示: 如果配置文件有更新，请检查并合并:"
        echo "  raspi/config/default.yaml"
    else
        echo ""
        echo "✗ 代码更新失败，可能有冲突需要手动解决"
        exit 1
    fi
else
    echo "已取消更新"
    exit 0
fi

