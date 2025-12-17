#!/bin/bash
# FishCar 启动脚本
# 使用方法: bash run.sh 或 ./run.sh

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

# 如果未设置 DISPLAY，使用无头模式（避免 OpenCV Qt 插件错误）
if [ -z "$DISPLAY" ]; then
    export QT_QPA_PLATFORM=offscreen
    echo "检测到无图形界面环境，使用无头模式运行"
fi

# 使用模块方式运行（推荐）
python -m src.main "$@"



