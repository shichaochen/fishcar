from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

import cv2
import numpy as np
from loguru import logger
from ultralytics import YOLO

from .config_loader import DetectorConfig


@dataclass
class DetectionResult:
    has_target: bool
    center: Optional[tuple[float, float]]
    bbox: Optional[tuple[int, int, int, int]]
    confidence: Optional[float]


class FishDetector:
    def __init__(self, config: DetectorConfig) -> None:
        self.config = config
        self.model = YOLO(config.weights_path)
        self.history: Deque[tuple[float, float]] = deque(maxlen=5)

    def detect(self, frame: cv2.typing.MatLike) -> DetectionResult:
        detections = self.model.predict(
            source=frame,
            conf=self.config.conf_threshold,
            iou=self.config.iou_threshold,
            classes=self.config.classes,
            verbose=False,
            max_det=self.config.max_detections,
        )
        if not detections:
            logger.debug("YOLO 未返回结果")
            return DetectionResult(False, None, None, None)

        boxes = detections[0].boxes
        if boxes is None or boxes.shape[0] == 0:
            logger.debug("未检测到目标")
            return DetectionResult(False, None, None, None)

        box = boxes[0].cpu().numpy()
        x1, y1, x2, y2 = box.xyxy[0]
        conf = float(box.conf[0])
        center = ((x1 + x2) / 2, (y1 + y2) / 2)

        if self.config.smoothing.get("enabled", False):
            center = self._smooth(center)

        bbox = (int(x1), int(y1), int(x2), int(y2))
        return DetectionResult(True, center, bbox, conf)

    def _smooth(self, point: tuple[float, float]) -> tuple[float, float]:
        alpha = self.config.smoothing.get("alpha", 0.6)
        if not self.history:
            self.history.append(point)
            return point

        last = self.history[-1]
        smoothed = (
            alpha * point[0] + (1 - alpha) * last[0],
            alpha * point[1] + (1 - alpha) * last[1],
        )
        self.history.append(smoothed)
        return smoothed

