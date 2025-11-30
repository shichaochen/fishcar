#!/bin/bash
# FishCar Raspberry Pi 安装脚本
# 使用方法: bash install.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "FishCar Raspberry Pi 安装脚本"
echo "=========================================="

# 检查是否为 root 用户（部分操作需要）
if [ "$EUID" -eq 0 ]; then 
   echo "请不要使用 root 用户运行此脚本"
   exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="$HOME/fishcar"

echo "项目目录: $PROJECT_DIR"
echo "安装目录: $INSTALL_DIR"
echo ""

# 1. 更新系统（可选，如果遇到锁定可以跳过）
echo "[1/7] 更新系统包..."
SKIP_UPDATE=false
if [ "$1" == "--skip-update" ]; then
    SKIP_UPDATE=true
    echo "跳过系统更新（使用 --skip-update 参数）"
fi

if [ "$SKIP_UPDATE" = false ]; then
    # 检查 apt 是否被锁定
    if sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1; then
        echo "⚠️  警告: apt 正在被其他进程使用"
        echo "正在等待 apt 解锁（最多等待 60 秒）..."
        timeout=60
        while [ $timeout -gt 0 ] && (sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1); do
            sleep 1
            timeout=$((timeout - 1))
            echo -n "."
        done
        echo ""
        if [ $timeout -eq 0 ]; then
            echo "⚠️  apt 仍然被锁定，跳过系统更新步骤"
            echo "提示: 可以稍后手动运行 'sudo apt update && sudo apt upgrade -y'"
            SKIP_UPDATE=true
        fi
    fi
    
    if [ "$SKIP_UPDATE" = false ]; then
        sudo apt update || {
            echo "⚠️  更新失败，继续安装其他组件..."
        }
        sudo apt upgrade -y || {
            echo "⚠️  升级失败，继续安装其他组件..."
        }
    fi
fi

# 2. 安装系统依赖
echo "[2/7] 安装系统依赖..."
# 检查并等待 apt 解锁
if sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1; then
    echo "等待 apt 解锁..."
    timeout=30
    while [ $timeout -gt 0 ] && (sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 || sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1); do
        sleep 1
        timeout=$((timeout - 1))
    done
fi

sudo apt install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    libopencv-dev \
    libopencv-contrib-dev \
    git \
    screen \
    v4l-utils \
    usbutils || {
    echo "⚠️  部分依赖安装失败，请检查错误信息"
    echo "可以稍后手动运行: sudo apt install -y python3 python3-venv python3-dev python3-pip libopencv-dev libopencv-contrib-dev git screen v4l-utils usbutils"
}

# 3. 将用户添加到 dialout 组（串口权限）
echo "[3/7] 配置串口权限..."
sudo usermod -a -G dialout $USER
echo "已将用户 $USER 添加到 dialout 组（需要重新登录生效）"

# 4. 复制项目文件到安装目录
echo "[4/7] 复制项目文件..."
if [ -d "$INSTALL_DIR" ]; then
    echo "目录 $INSTALL_DIR 已存在，备份为 ${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

mkdir -p "$INSTALL_DIR"
cp -r "$PROJECT_DIR/raspi"/* "$INSTALL_DIR/"
echo "文件已复制到 $INSTALL_DIR"

# 5. 创建虚拟环境
echo "[5/7] 创建 Python 虚拟环境..."
VENV_DIR="$HOME/fishcar-venv"
if [ -d "$VENV_DIR" ]; then
    echo "虚拟环境已存在，跳过创建"
else
    python3 -m venv "$VENV_DIR"
    echo "虚拟环境已创建: $VENV_DIR"
fi

# 6. 安装 Python 依赖
echo "[6/7] 安装 Python 依赖..."
source "$VENV_DIR/bin/activate"

# 升级 pip
pip install --upgrade pip setuptools wheel

# 安装 PyTorch（CPU 版本，适合树莓派）
echo "安装 PyTorch (CPU 版本)..."
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu

# 安装其他依赖
echo "安装其他依赖..."
pip install -r "$INSTALL_DIR/requirements.txt"

# 7. 创建必要的目录和文件
echo "[7/7] 创建必要的目录..."
mkdir -p "$INSTALL_DIR/models"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/config"

# 检查模型文件
if [ ! -f "$INSTALL_DIR/models/best.pt" ]; then
    echo ""
    echo "⚠️  警告: 未找到模型文件 best.pt"
    echo "请将训练好的 YOLO 模型文件复制到: $INSTALL_DIR/models/best.pt"
fi

# 检查配置文件
if [ ! -f "$INSTALL_DIR/config/default.yaml" ]; then
    echo "⚠️  警告: 配置文件不存在，请检查安装"
fi

# 8. 配置串口设备（可选）
echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 将 YOLO 模型文件 best.pt 复制到: $INSTALL_DIR/models/"
echo "2. 检查并修改配置文件: $INSTALL_DIR/config/default.yaml"
echo "   - 串口设备路径 (默认: /dev/ttyACM0)"
echo "   - 摄像头参数"
echo "   - 运动映射参数"
echo ""
echo "3. 重新登录以应用串口权限更改，或运行:"
echo "   newgrp dialout"
echo ""
echo "4. 运行程序："
echo "   source $VENV_DIR/bin/activate"
echo "   python $INSTALL_DIR/src/main.py"
echo ""
echo "5. 如需后台运行，使用 screen："
echo "   screen -S fishcar"
echo "   source $VENV_DIR/bin/activate"
echo "   python $INSTALL_DIR/src/main.py"
echo "   (按 Ctrl+A 然后 D 退出 screen，使用 screen -r fishcar 重新连接)"
echo ""

