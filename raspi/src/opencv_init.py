"""
OpenCV 初始化模块
在所有其他模块导入 OpenCV 之前，设置 headless 模式环境变量
"""
import os
import sys

# 在导入 OpenCV 之前设置环境变量（避免 headless 模式下的 Qt 插件错误）
# 这些必须在导入 cv2 之前设置
if not os.environ.get("DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""
    os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "0"
    # 重定向 Qt 错误输出，避免显示错误信息
    os.environ["QT_LOGGING_RULES"] = "*.debug=false"

# 尝试导入 OpenCV，如果失败则使用替代方案
try:
    import cv2  # noqa: E402
except Exception as e:
    # 如果导入失败，尝试设置更多环境变量后重试
    if not os.environ.get("DISPLAY"):
        os.environ["QT_QPA_PLATFORM"] = "minimal"
        try:
            import cv2  # noqa: E402
        except Exception:
            # 最后的尝试：使用 dummy 后端
            os.environ["QT_QPA_PLATFORM"] = "dummy"
            import cv2  # noqa: E402

# 尝试设置 OpenCV 使用无头后端
try:
    cv2.setNumThreads(1)
except Exception:
    pass

