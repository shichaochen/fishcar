#!/usr/bin/env python3
"""
鱼缸边界标定工具
使用方法: python calibrate_aquarium.py [--config config.yaml]
"""
import argparse
import sys
from pathlib import Path

import cv2
from loguru import logger

try:
    from .aquarium_calibration import AquariumCalibrator
    from .camera import CameraStream
    from .config_loader import load_config
except ImportError:
    # 如果作为独立脚本运行
    _script_dir = Path(__file__).parent
    _project_dir = _script_dir.parent
    sys.path.insert(0, str(_project_dir))
    from src.aquarium_calibration import AquariumCalibrator
    from src.camera import CameraStream
    from src.config_loader import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="鱼缸边界标定工具")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("/home/pi/fishcar/raspi/config/default.yaml"),
        help="配置文件路径",
    )
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    calibration_path = Path(config.calibration_path)
    
    logger.info("启动鱼缸边界标定工具")
    logger.info("标定数据将保存到: {}", calibration_path)
    
    # 初始化摄像头
    camera = CameraStream(config.camera)
    camera.open()
    
    # 获取一帧用于标定
    logger.info("正在获取摄像头画面...")
    frame = None
    for _ in range(30):  # 等待几帧让摄像头稳定
        frame = camera.read()
        if frame is not None:
            break
    
    if frame is None:
        logger.error("无法获取摄像头画面")
        camera.close()
        sys.exit(1)
    
    logger.info("摄像头画面已获取，尺寸: {}x{}", frame.shape[1], frame.shape[0])
    
    # 创建标定器
    calibrator = AquariumCalibrator(calibration_path)
    
    # 交互式标定
    logger.info("请在图像上点击四个角点：左上、右上、右下、左下")
    bounds = calibrator.interactive_calibrate(frame)
    
    if bounds:
        # 保存标定数据
        calibrator.save_to_config(bounds)
        logger.info("标定完成！")
        logger.info("边界矩形: {}", bounds.get_rect())
    else:
        logger.warning("标定已取消")
    
    camera.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

