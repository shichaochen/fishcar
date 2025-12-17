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
# 必须在 Python 启动之前设置这些环境变量
if [ -z "$DISPLAY" ]; then
    export QT_QPA_PLATFORM=offscreen
    export QT_QPA_PLATFORM_PLUGIN_PATH=""
    export OPENCV_IO_ENABLE_OPENEXR=0
    # 禁用 OpenCV 的 GUI 后端
    export OPENCV_LOG_LEVEL=ERROR
    echo "检测到无图形界面环境，使用无头模式运行"
fi

# 使用模块方式运行（推荐）
# 使用 -E 标志确保环境变量被正确传递
python -E -m src.main "$@"



