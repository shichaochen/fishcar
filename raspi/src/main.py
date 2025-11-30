import argparse
import signal
import sys
import time
from pathlib import Path

from loguru import logger

# 支持直接运行和模块导入两种方式
try:
    from .aquarium_calibration import AquariumBounds, AquariumCalibrator
    from .camera import CameraStream
    from .config_loader import load_config
    from .detector import FishDetector
    from .logging_utils import setup_logging
    from .motion_mapping import MecanumMapper
    from .serial_comm import SerialBridge
    from .safety import SafetyManager
    from .visualizer import Visualizer
except ImportError:
    # 如果相对导入失败，尝试绝对导入（直接运行脚本时）
    import os
    # 添加父目录到路径
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.aquarium_calibration import AquariumBounds, AquariumCalibrator
    from src.camera import CameraStream
    from src.config_loader import load_config
    from src.detector import FishDetector
    from src.logging_utils import setup_logging
    from src.motion_mapping import MecanumMapper
    from src.serial_comm import SerialBridge
    from src.safety import SafetyManager
    from src.visualizer import Visualizer


class Application:
    def __init__(self, config_path: Path) -> None:
        self.config = load_config(config_path)
        setup_logging(self.config.logging)
        self.camera = CameraStream(self.config.camera)
        self.detector = FishDetector(self.config.detector)
        self.mapper = MecanumMapper(self.config.motion_mapping)
        self.serial = SerialBridge(self.config.serial)
        self.safety = SafetyManager(self.config.serial.watchdog_timeout)
        
        # 加载鱼缸边界标定
        calibrator = AquariumCalibrator(Path(self.config.calibration_path))
        aquarium_bounds = calibrator.load_from_config()
        if aquarium_bounds:
            logger.info("已加载鱼缸边界标定数据")
        else:
            logger.warning("未找到鱼缸边界标定数据，运行标定工具进行标定")
        
        self.visualizer = Visualizer(self.config.visualization, aquarium_bounds)
        self._running = False

    def start(self) -> None:
        logger.info("启动 FishCar 控制系统")
        self._running = True
        self.camera.open()
        self.serial.open()
        self._loop()

    def shutdown(self) -> None:
        if not self._running:
            return
        logger.info("正在关闭系统")
        self._running = False
        self.serial.stop()
        self.camera.close()
        self.visualizer.close()
        logger.info("已安全退出")

    def _loop(self) -> None:
        last_heartbeat = time.monotonic()
        while self._running:
            frame = self.camera.read()
            if frame is None:
                logger.warning("未获取到帧，稍候重试")
                time.sleep(0.01)
                continue

            result = self.detector.detect(frame)
            mapped = self.mapper.calculate(result)
            safe_vector = self.safety.apply(mapped, self.serial.read_status())
            self.serial.send_vector(safe_vector)

            now = time.monotonic()
            if (
                self.serial.config.heartbeat_interval > 0
                and now - last_heartbeat >= self.serial.config.heartbeat_interval
            ):
                self.serial.send_heartbeat()
                last_heartbeat = now

            self.visualizer.render(frame, result, safe_vector)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FishCar Raspberry Pi 控制程序")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("/home/pi/fishcar/raspi/config/default.yaml"),
        help="配置文件路径",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = Application(args.config)

    def handle_exit(signum: int, frame) -> None:  # type: ignore[override]
        logger.warning("收到信号 {sign}, 准备退出", sign=signum)
        app.shutdown()
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, handle_exit)

    try:
        app.start()
    except KeyboardInterrupt:
        handle_exit(signal.SIGINT, None)
    except Exception as exc:  # noqa: BLE001
        logger.exception("运行时出现未捕获异常: {}", exc)
        app.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()

