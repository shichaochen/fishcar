from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

import numpy as np

from .config_loader import MotionMappingConfig

if TYPE_CHECKING:  # 仅类型注解，避免运行时拉入 detector → ultralytics 重依赖
    from .aquarium_calibration import AquariumBounds
    from .detector import DetectionResult


@dataclass
class MotionVector:
    vx: float
    vy: float
    omega: float
    active: bool


class MecanumMapper:
    """将鱼目标位置映射为麦克纳姆底盘速度向量。

    若提供 aquarium_bounds，则用透视变换把像素坐标映射到鱼缸归一化
    坐标 [0,1]x[0,1] 后再计算速度；否则回退到旧的全图归一化行为
    （兼容未标定的情况）。
    """

    def __init__(
        self,
        config: MotionMappingConfig,
        aquarium_bounds: Optional["AquariumBounds"] = None,
    ) -> None:
        self.config = config
        self.aquarium_bounds = aquarium_bounds

    def set_aquarium_bounds(self, bounds: Optional["AquariumBounds"]) -> None:
        """运行时更新/清除鱼缸边界（例如重新标定后）。"""
        self.aquarium_bounds = bounds

    def calculate(self, detection: "DetectionResult") -> MotionVector:
        if not detection.has_target or detection.center is None:
            return MotionVector(0.0, 0.0, 0.0, False)

        cx, cy = detection.center

        if self.aquarium_bounds is not None:
            tank_pt = self.aquarium_bounds.pixel_to_tank((cx, cy))
            if tank_pt is None:
                # 目标在鱼缸之外：视为误检，停车而非乱跑
                return MotionVector(0.0, 0.0, 0.0, False)
            # 鱼缸归一化坐标 [0,1] → 速度坐标 [-1,1]（鱼缸中心为 0）
            nx = tank_pt[0] * 2.0 - 1.0
            ny = tank_pt[1] * 2.0 - 1.0
        else:
            # 兼容旧行为：相对全图归一化
            nx = self._normalize(coord=cx, reference=self.config.reference_width)
            ny = self._normalize(coord=cy, reference=self.config.reference_height)

        nx *= (-1 if self.config.invert_x else 1)
        ny *= (-1 if self.config.invert_y else 1)

        # 逐轴死区：任一轴在死区内则该轴速度置零，避免浮点噪声被 min_speed 放大
        if abs(nx) < self.config.deadzone:
            nx = 0.0
        if abs(ny) < self.config.deadzone:
            ny = 0.0
        if nx == 0.0 and ny == 0.0:
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

