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

# 检测图形界面环境
if [ -z "$DISPLAY" ]; then
    # 检查是否有 X 服务器正在运行（树莓派通常使用 :0）
    if pgrep -x "Xorg" > /dev/null 2>&1 || [ -e "/tmp/.X11-unix/X0" ]; then
        # 检测到 X 服务器，设置 DISPLAY 环境变量
        export DISPLAY=:0
        echo "检测到图形界面，设置 DISPLAY=:0，将显示摄像头画面"
    else
        # 没有图形界面，使用无头模式（避免 OpenCV Qt 插件错误）
        export QT_QPA_PLATFORM=offscreen
        export QT_QPA_PLATFORM_PLUGIN_PATH=""
        export OPENCV_IO_ENABLE_OPENEXR=0
        export OPENCV_LOG_LEVEL=ERROR
        echo "未检测到图形界面环境，使用无头模式运行"
    fi
else
    echo "使用已设置的 DISPLAY=$DISPLAY"
fi

# 使用模块方式运行（推荐）
# 使用 -E 标志确保环境变量被正确传递
python -E -m src.main "$@"


