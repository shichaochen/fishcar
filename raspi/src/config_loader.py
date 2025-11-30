from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CameraConfig:
    device_index: int
    width: int
    height: int
    fps: int
    flip_x: bool
    flip_y: bool
    perspective_correction: bool


@dataclass(frozen=True)
class DetectorConfig:
    weights_path: str
    conf_threshold: float
    iou_threshold: float
    classes: list | None
    max_detections: int
    smoothing: dict


@dataclass(frozen=True)
class MotionMappingConfig:
    deadzone: float
    gain_x: float
    gain_y: float
    gain_rotation: float
    max_speed: float
    min_speed: float
    invert_x: bool
    invert_y: bool
    reference_width: int
    reference_height: int


@dataclass(frozen=True)
class SerialConfig:
    port: str
    baudrate: int
    timeout: float
    heartbeat_interval: float
    watchdog_timeout: float


@dataclass(frozen=True)
class VisualizationConfig:
    enabled: bool
    window_name: str
    show_vectors: bool
    show_fps: bool
    show_aquarium_bounds: bool
    show_relative_coords: bool


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    file: str


@dataclass(frozen=True)
class AppConfig:
    camera: CameraConfig
    detector: DetectorConfig
    motion_mapping: MotionMappingConfig
    serial: SerialConfig
    visualization: VisualizationConfig
    logging: LoggingConfig
    calibration_path: str


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    camera = CameraConfig(**raw["camera"])
    detector = DetectorConfig(**raw["detector"])
    motion_mapping = MotionMappingConfig(**raw["motion_mapping"])
    serial = SerialConfig(**raw["serial"])
    
    # 可视化配置（支持新字段的默认值）
    viz_raw = raw.get("visualization", {})
    visualization = VisualizationConfig(
        enabled=viz_raw.get("enabled", True),
        window_name=viz_raw.get("window_name", "FishCar Tracker"),
        show_vectors=viz_raw.get("show_vectors", True),
        show_fps=viz_raw.get("show_fps", True),
        show_aquarium_bounds=viz_raw.get("show_aquarium_bounds", True),
        show_relative_coords=viz_raw.get("show_relative_coords", True),
    )
    
    logging = LoggingConfig(**raw["logging"])
    calibration_path = raw.get("calibration_path", str(path.parent / "calibration.json"))

    return AppConfig(
        camera=camera,
        detector=detector,
        motion_mapping=motion_mapping,
        serial=serial,
        visualization=visualization,
        logging=logging,
        calibration_path=calibration_path,
    )

