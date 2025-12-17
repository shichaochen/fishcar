#!/bin/bash
# 摄像头查找工具启动脚本
# 使用方法: bash find_camera.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$HOME/fishcar-venv"

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "错误: 虚拟环境不存在: $VENV_DIR"
    echo "请先运行安装脚本: bash $SCRIPT_DIR/install.sh"
    exit 1
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 切换到项目目录
cd "$SCRIPT_DIR"

# 运行查找工具（支持多种方式）
if [ -f "src/find_camera.py" ]; then
    python src/find_camera.py
elif [ -f "../raspi/src/find_camera.py" ]; then
    cd ..
    python -m raspi.src.find_camera
else
    echo "错误: 找不到 find_camera.py"
    exit 1
fi

