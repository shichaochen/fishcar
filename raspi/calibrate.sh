#!/bin/bash
# FishCar 标定工具启动脚本
# 使用方法: bash calibrate.sh 或 ./calibrate.sh

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

# 使用模块方式运行标定工具
python -m src.calibrate_aquarium "$@"



