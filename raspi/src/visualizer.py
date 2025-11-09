from __future__ import annotations

import time

import cv2
from loguru import logger

from .config_loader import VisualizationConfig
from .detector import DetectionResult
from .motion_mapping import MotionVector


class Visualizer:
    def __init__(self, config: VisualizationConfig) -> None:
        self.config = config
        self._last_time = time.time()
        self._fps = 0.0

    def render(self, frame, detection: DetectionResult, vector: MotionVector) -> None:
        if not self.config.enabled:
            return

        display = frame.copy()
        if detection.has_target and detection.bbox:
            x1, y1, x2, y2 = detection.bbox
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if detection.center:
                cx, cy = detection.center
                cv2.circle(display, (int(cx), int(cy)), 4, (0, 0, 255), -1)

        if self.config.show_vectors:
            text = f"vx={vector.vx:.2f} vy={vector.vy:.2f} ω={vector.omega:.2f}"
            cv2.putText(display, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if self.config.show_fps:
            now = time.time()
            dt = now - self._last_time
            self._fps = 1.0 / dt if dt > 0 else 0.0
            self._last_time = now
            cv2.putText(display, f"FPS: {self._fps:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        try:
            cv2.imshow(self.config.window_name, display)
            if cv2.waitKey(1) & 0xFF == 27:
                logger.info("用户按下 ESC，建议终止程序")
        except cv2.error as exc:
            logger.error("显示窗口失败: {}", exc)

    def close(self) -> None:
        if self.config.enabled:
            cv2.destroyAllWindows()

