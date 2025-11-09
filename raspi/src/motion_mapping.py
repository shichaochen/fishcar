from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config_loader import MotionMappingConfig
from .detector import DetectionResult


@dataclass
class MotionVector:
    vx: float
    vy: float
    omega: float
    active: bool


class MecanumMapper:
    def __init__(self, config: MotionMappingConfig) -> None:
        self.config = config

    def calculate(self, detection: DetectionResult) -> MotionVector:
        if not detection.has_target or detection.center is None:
            return MotionVector(0.0, 0.0, 0.0, False)

        cx, cy = detection.center
        # 使用归一化坐标，范围 [-1, 1]
        nx = self._normalize(
            coord=cx,
            reference=self.config.reference_width,
        ) * (-1 if self.config.invert_x else 1)
        ny = self._normalize(
            coord=cy,
            reference=self.config.reference_height,
        ) * (-1 if self.config.invert_y else 1)

        if abs(nx) < self.config.deadzone and abs(ny) < self.config.deadzone:
            return MotionVector(0.0, 0.0, 0.0, False)

        vx = np.clip(nx * self.config.gain_x, -self.config.max_speed, self.config.max_speed)
        vy = np.clip(ny * self.config.gain_y, -self.config.max_speed, self.config.max_speed)
        omega = np.clip(self.config.gain_rotation, -self.config.max_speed, self.config.max_speed)

        vx = self._apply_min_speed(vx)
        vy = self._apply_min_speed(vy)

        return MotionVector(vx, vy, omega, True)

    @staticmethod
    def _normalize(coord: float, reference: int) -> float:
        if reference == 0:
            return 0.0
        return coord / reference * 2 - 1

    def _apply_min_speed(self, value: float) -> float:
        if value == 0.0:
            return value
        sign = 1 if value > 0 else -1
        return sign * max(abs(value), self.config.min_speed)

