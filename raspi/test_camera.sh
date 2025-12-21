#!/bin/bash
# 测试摄像头并保存一张图片
# 使用方法: bash test_camera.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$HOME/fishcar-venv"
OUTPUT_IMAGE="$SCRIPT_DIR/logs/test_camera.jpg"

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "错误: 虚拟环境不存在: $VENV_DIR"
    echo "请先运行安装脚本: bash $SCRIPT_DIR/install.sh"
    exit 1
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 确保输出目录存在
mkdir -p "$SCRIPT_DIR/logs"

# 切换到 raspi 目录
cd "$SCRIPT_DIR"

# 使用模块方式运行（与 run.sh 相同的方式）
python -m src.calibrate_aquarium --save-image "$OUTPUT_IMAGE"

if [ $? -eq 0 ]; then
    echo ""
    echo "=" * 60
    echo "摄像头测试成功！"
    echo "图片已保存到: $OUTPUT_IMAGE"
    echo ""
    echo "查看图片的方法："
    echo "1. 使用 scp 下载到本地:"
    echo "   scp pi@raspberrypi:$OUTPUT_IMAGE ."
    echo "2. 在树莓派上使用图片查看器（如果有图形界面）"
    echo "3. 检查文件是否存在:"
    echo "   ls -lh $OUTPUT_IMAGE"
    echo "=" * 60
else
    echo "摄像头测试失败，请检查："
    echo "1. 摄像头是否已连接"
    echo "2. 运行: bash find_camera.sh"
    echo "3. 检查权限: groups | grep video"
fi


