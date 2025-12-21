#!/usr/bin/env python3
"""
鱼缸边界标定工具
使用方法: python calibrate_aquarium.py [--config config.yaml]
"""
import argparse
import os
import sys
from pathlib import Path

# 在导入 cv2 之前设置环境变量
if not os.environ.get("DISPLAY"):
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import cv2
from loguru import logger

try:
    from .aquarium_calibration import AquariumBounds, AquariumCalibrator
    from .camera import CameraStream
    from .config_loader import load_config
except ImportError:
    # 如果作为独立脚本运行
    _script_dir = Path(__file__).parent
    _project_dir = _script_dir.parent
    sys.path.insert(0, str(_project_dir))
    from src.aquarium_calibration import AquariumBounds, AquariumCalibrator
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
    parser.add_argument(
        "--save-image",
        type=Path,
        help="保存摄像头画面到图片文件（用于无图形界面环境）",
    )
    parser.add_argument(
        "--from-image",
        type=Path,
        help="从图片文件加载进行标定（需要图形界面）",
    )
    parser.add_argument(
        "--manual",
        nargs=8,
        type=int,
        metavar=("TL_X", "TL_Y", "TR_X", "TR_Y", "BR_X", "BR_Y", "BL_X", "BL_Y"),
        help="手动输入四个角点坐标（左上、右上、右下、左下）",
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
    
    # 如果只是保存图片
    if args.save_image:
        cv2.imwrite(str(args.save_image), frame)
        logger.info("图片已保存到: {}", args.save_image)
        logger.info("请在有图形界面的环境中使用 --from-image 参数进行标定")
        logger.info("或使用 --manual 参数手动输入坐标")
        camera.close()
        return
    
    # 如果从图片文件加载
    if args.from_image:
        frame = cv2.imread(str(args.from_image))
        if frame is None:
            logger.error("无法加载图片: {}", args.from_image)
            sys.exit(1)
        logger.info("从图片加载，尺寸: {}x{}", frame.shape[1], frame.shape[0])
        camera.close()  # 关闭摄像头
    
    # 创建标定器
    calibrator = AquariumCalibrator(calibration_path)
    
    # 手动输入坐标模式
    if args.manual:
        if len(args.manual) != 8:
            logger.error("需要8个坐标值（4个点，每个点x和y）")
            sys.exit(1)
        
        tl_x, tl_y, tr_x, tr_y, br_x, br_y, bl_x, bl_y = args.manual
        bounds = AquariumBounds(
            top_left=(tl_x, tl_y),
            top_right=(tr_x, tr_y),
            bottom_right=(br_x, br_y),
            bottom_left=(bl_x, bl_y)
        )
        calibrator.save_to_config(bounds)
        logger.info("标定完成！")
        logger.info("边界矩形: {}", bounds.get_rect())
        if not args.from_image:
            camera.close()
        return
    
    # 检查是否有图形界面
    has_display = os.environ.get("DISPLAY") is not None
    if not has_display:
        logger.warning("检测到无图形界面环境（无 DISPLAY 变量）")
        logger.info("")
        logger.info("=" * 60)
        logger.info("无图形界面标定方法：")
        logger.info("=" * 60)
        logger.info("")
        logger.info("方法1（推荐）：保存图片后手动标定")
        logger.info("  步骤1: python -m raspi.src.calibrate_aquarium --save-image /tmp/aquarium_frame.jpg")
        logger.info("  步骤2: 将图片传输到有图形界面的电脑")
        logger.info("  步骤3: 在有图形界面的电脑上运行:")
        logger.info("         python -m raspi.src.calibrate_aquarium --from-image /path/to/aquarium_frame.jpg")
        logger.info("")
        logger.info("方法2：手动输入坐标")
        logger.info("  python -m raspi.src.calibrate_aquarium --manual TL_X TL_Y TR_X TR_Y BR_X BR_Y BL_X BL_Y")
        logger.info("  例如: python -m raspi.src.calibrate_aquarium --manual 100 50 600 50 600 400 100 400")
        logger.info("")
        logger.info("方法3：直接编辑配置文件")
        logger.info("  nano {}", calibration_path)
        logger.info("")
        logger.info("详细说明请参考: docs/calibration_headless.md")
        logger.info("")
        logger.info("=" * 60)
        logger.info("")
        logger.info("自动保存图片到 /tmp/aquarium_frame.jpg...")
        cv2.imwrite("/tmp/aquarium_frame.jpg", frame)
        logger.info("✓ 图片已保存到: /tmp/aquarium_frame.jpg")
        logger.info("")
        logger.info("请使用以下命令之一继续标定：")
        logger.info("  1. 传输图片到有图形界面的电脑进行标定")
        logger.info("  2. 使用 --manual 参数手动输入坐标")
        logger.info("  3. 直接编辑配置文件: {}", calibration_path)
        camera.close()
        sys.exit(0)
    
    # 交互式标定（需要图形界面）
    try:
        logger.info("请在图像上点击四个角点：左上、右上、右下、左下")
        bounds = calibrator.interactive_calibrate(frame)
        
        if bounds:
            # 保存标定数据
            calibrator.save_to_config(bounds)
            logger.info("标定完成！")
            logger.info("边界矩形: {}", bounds.get_rect())
        else:
            logger.warning("标定已取消")
    except cv2.error as e:
        logger.error("图形界面错误: {}", e)
        logger.error("")
        logger.error("请使用以下方法之一：")
        logger.error("1. 使用 --save-image 保存图片，然后在有图形界面的环境中标定")
        logger.error("2. 使用 --manual 参数手动输入坐标")
        logger.error("3. 直接编辑配置文件: {}", calibration_path)
        logger.error("")
        logger.error("详细说明请参考: docs/calibration_headless.md")
        sys.exit(1)
    finally:
        if not args.from_image:
            camera.close()
        try:
            cv2.destroyAllWindows()
        except:
            pass


if __name__ == "__main__":
    main()

