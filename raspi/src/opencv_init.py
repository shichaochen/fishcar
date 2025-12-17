"""
OpenCV 初始化模块
在所有其他模块导入 OpenCV 之前，设置 headless 模式环境变量
"""
import os

# 在导入 OpenCV 之前设置环境变量（避免 headless 模式下的 Qt 插件错误）
if not os.environ.get("DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    # 也尝试设置其他可能的环境变量
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""
    # 禁用 OpenCV 的 GUI 后端
    os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "0"

# 现在可以安全地导入 OpenCV
import cv2  # noqa: E402

# 尝试设置 OpenCV 使用无头后端
try:
    # 如果可能，禁用 GUI 功能
    cv2.setNumThreads(1)
except Exception:
    pass

