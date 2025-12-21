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

# 创建测试脚本
cat > /tmp/test_camera_temp.py << 'EOF'
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.camera import CameraStream
from src.config_loader import load_config
import cv2

config_path = Path("/home/pi/fishcar/raspi/config/default.yaml")
config = load_config(config_path)

print("正在打开摄像头...")
camera = CameraStream(config.camera)
camera.open()

print("正在读取画面...")
frame = None
for i in range(10):
    frame = camera.read()
    if frame is not None:
        break
    print(f"  尝试 {i+1}/10...")

if frame is None:
    print("错误: 无法读取摄像头画面")
    camera.close()
    sys.exit(1)

print(f"成功获取画面，尺寸: {frame.shape[1]}x{frame.shape[0]}")

output_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/test_camera.jpg"
cv2.imwrite(output_path, frame)
print(f"图片已保存到: {output_path}")

camera.close()
print("摄像头已关闭")
EOF

# 运行测试
python /tmp/test_camera_temp.py "$OUTPUT_IMAGE"

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

# 清理临时文件
rm -f /tmp/test_camera_temp.py

