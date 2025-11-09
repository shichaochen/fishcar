from __future__ import annotations

import time

from .motion_mapping import MotionVector
from .serial_comm import ArduinoStatus


class SafetyManager:
    def __init__(self, watchdog_timeout: float) -> None:
        self.watchdog_timeout = watchdog_timeout

    def apply(self, vector: MotionVector, status: ArduinoStatus) -> MotionVector:
        if time.monotonic() - status.timestamp > self.watchdog_timeout:
            return MotionVector(0.0, 0.0, 0.0, False)

        vx, vy = vector.vx, vector.vy
        if status.limits.get("front") and vy > 0:
            vy = 0.0
        if status.limits.get("rear") and vy < 0:
            vy = 0.0
        if status.limits.get("left") and vx < 0:
            vx = 0.0
        if status.limits.get("right") and vx > 0:
            vx = 0.0

        if vx == 0.0 and vy == 0.0:
            return MotionVector(0.0, 0.0, vector.omega, False)

        return MotionVector(vx, vy, vector.omega, vector.active)

