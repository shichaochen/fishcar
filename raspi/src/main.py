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
    from .trajectory_recorder import TrajectoryRecorder
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
    from src.trajectory_recorder import TrajectoryRecorder
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
        
        # 初始化轨迹记录器
        trajectory_recorder = None
        if self.config.trajectory.enabled:
            save_path = Path(self.config.trajectory.save_path) if self.config.trajectory.save_path else None
            trajectory_recorder = TrajectoryRecorder(
                max_points=self.config.trajectory.max_points,
                sample_interval=self.config.trajectory.sample_interval,
                save_path=save_path,
            )
            logger.info("轨迹记录已启用 (max_points={}, interval={}s)", 
                        self.config.trajectory.max_points, 
                        self.config.trajectory.sample_interval)
        
        self.trajectory_recorder = trajectory_recorder
        self.visualizer = Visualizer(self.config.visualization, aquarium_bounds, trajectory_recorder)
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
        
        # 保存轨迹
        if self.trajectory_recorder and self.trajectory_recorder.points:
            logger.info("保存轨迹数据 ({} 个点)", len(self.trajectory_recorder.points))
            self.trajectory_recorder.save()
        
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
            
            # 更新轨迹记录
            if self.trajectory_recorder:
                self.trajectory_recorder.update(safe_vector)

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
    
    # 自动检测配置文件路径（相对于脚本位置）
    script_dir = Path(__file__).parent
    # 尝试多个可能的路径
    possible_config_paths = [
        script_dir.parent / "config" / "default.yaml",  # raspi/config/default.yaml
        script_dir.parent.parent / "raspi" / "config" / "default.yaml",  # fishcar/raspi/config/default.yaml
        Path("/home/pi/fishcar/raspi/config/default.yaml"),  # 绝对路径
        Path.home() / "fishcar" / "raspi" / "config" / "default.yaml",  # ~/fishcar/raspi/config/default.yaml
    ]
    
    default_config = None
    for path in possible_config_paths:
        if path.exists():
            default_config = path
            break
    
    if default_config is None:
        # 如果都找不到，使用第一个作为默认值（会报错但提示更清楚）
        default_config = possible_config_paths[0]
    
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=default_config,
        help=f"配置文件路径（默认: {default_config}）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # 检查配置文件是否存在
    if not args.config.exists():
        logger.error("配置文件不存在: {}", args.config)
        logger.error("请确保配置文件存在，或使用 -c 参数指定配置文件路径")
        logger.error("示例: python main.py -c /path/to/config.yaml")
        sys.exit(1)
    
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

