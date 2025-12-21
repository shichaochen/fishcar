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

# 检查是否有本地修改
echo ""
echo "检查本地修改..."
LOCAL_CHANGES=$(git status --porcelain)
if [ -n "$LOCAL_CHANGES" ]; then
    echo "发现本地修改的文件:"
    git status --short
    echo ""
    
    # 检查配置文件是否有修改
    if git diff --quiet raspi/config/default.yaml 2>/dev/null; then
        CONFIG_CHANGED=false
    else
        CONFIG_CHANGED=true
        echo "⚠️  配置文件 raspi/config/default.yaml 有本地修改"
    fi
    
    if [ "$CONFIG_CHANGED" = true ]; then
        echo ""
        echo "正在备份配置文件..."
        BACKUP_FILE="raspi/config/default.yaml.$(date +%Y%m%d_%H%M%S).backup"
        cp raspi/config/default.yaml "$BACKUP_FILE"
        echo "✓ 配置文件已备份到: $BACKUP_FILE"
        echo ""
        echo "处理策略："
        echo "1. 暂存本地修改"
        echo "2. 拉取远程更新"
        echo "3. 尝试自动合并（如果失败会提示）"
        echo ""
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "已取消更新"
            exit 0
        fi
        
        # 暂存本地修改
        echo ""
        echo "暂存本地修改..."
        git stash push -m "本地配置修改 $(date +%Y-%m-%d_%H:%M:%S)"
        
        # 拉取更新
        echo ""
        echo "正在拉取远程更新..."
        git pull origin main
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✓ 代码更新成功！"
            echo ""
            echo "正在恢复本地配置修改..."
            git stash pop
            
            if [ $? -ne 0 ]; then
                echo ""
                echo "⚠️  配置文件合并有冲突，需要手动解决"
                echo "备份文件: $BACKUP_FILE"
                echo "当前文件: raspi/config/default.yaml"
                echo ""
                echo "请手动编辑配置文件解决冲突，或使用备份文件恢复"
            else
                echo "✓ 本地配置已自动合并"
            fi
        else
            echo ""
            echo "✗ 更新失败，正在恢复本地修改..."
            git stash pop
            exit 1
        fi
    else
        echo ""
        read -p "是否要暂存本地修改并更新? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash push -m "本地修改 $(date +%Y-%m-%d_%H:%M:%S)"
            git pull origin main
            if [ $? -eq 0 ]; then
                echo ""
                echo "✓ 代码更新成功！"
                echo "提示: 使用 'git stash pop' 恢复本地修改"
            else
                echo ""
                echo "✗ 更新失败，使用 'git stash pop' 恢复本地修改"
                exit 1
            fi
        else
            echo "已取消更新"
            exit 0
        fi
    fi
else
    echo "✓ 没有本地修改"
    echo ""
    read -p "是否要拉取远程更新? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "正在拉取远程更新..."
        git pull origin main
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✓ 代码更新成功！"
        else
            echo ""
            echo "✗ 代码更新失败"
            exit 1
        fi
    else
        echo "已取消更新"
        exit 0
    fi
fi

echo ""
echo "更新后的最新提交:"
git log --oneline -1
echo ""
echo "提示: 如果配置文件有更新，请检查重要配置项:"
echo "  - 串口路径: raspi/config/default.yaml -> serial.port"
echo "  - 摄像头分辨率: raspi/config/default.yaml -> camera.width/height"

