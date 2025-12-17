from __future__ import annotations

# 必须在导入 cv2 之前初始化
from . import opencv_init  # noqa: F401

from collections import deque
from dataclasses import dataclass
from pathlib import Path
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
        weights_path_str = config.weights_path
        
        # 检查是否是预训练模型名称（如 yolov8n.pt）
        is_pretrained = weights_path_str in ['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt', 'yolov8l.pt', 'yolov8x.pt']
        
        if is_pretrained:
            # 直接使用预训练模型
            logger.info(f"使用预训练模型: {weights_path_str}")
            self.model = YOLO(weights_path_str)
            self._filter_fish_only = (self.config.classes is None)
            if self._filter_fish_only:
                logger.info("自动设置检测类别为 fish (ID: 15)")
        else:
            # 检查文件是否存在
            weights_path = Path(weights_path_str)
            if not weights_path.exists():
                logger.warning(f"模型文件不存在: {weights_path}")
                logger.info("自动切换到 YOLOv8n 预训练模型（COCO 数据集，包含 fish 类别）")
                logger.info("提示: COCO 数据集中 fish 的类别 ID 是 15")
                # 使用 YOLOv8n (nano) 版本，适合树莓派
                self.model = YOLO('yolov8n.pt')
                # 如果配置中没有指定类别，自动设置为 fish (15)
                if self.config.classes is None:
                    logger.info("自动设置检测类别为 fish (ID: 15)")
                    self._filter_fish_only = True
                else:
                    self._filter_fish_only = False
            else:
                try:
                    self.model = YOLO(str(weights_path))
                    self._filter_fish_only = False
                    logger.info(f"已加载自定义模型: {weights_path}")
                except Exception as e:
                    logger.error(f"加载模型失败: {e}")
                    logger.info("回退到 YOLOv8n 预训练模型")
                    self.model = YOLO('yolov8n.pt')
                    self._filter_fish_only = (self.config.classes is None)
                    if self._filter_fish_only:
                        logger.info("自动设置检测类别为 fish (ID: 15)")
        
        self.history: Deque[tuple[float, float]] = deque(maxlen=5)

    def detect(self, frame: cv2.typing.MatLike) -> DetectionResult:
        # 如果使用预训练模型且需要过滤 fish，设置类别
        classes = self.config.classes
        if self._filter_fish_only and classes is None:
            classes = [15]  # COCO 数据集中 fish 的类别 ID
        
        detections = self.model.predict(
            source=frame,
            conf=self.config.conf_threshold,
            iou=self.config.iou_threshold,
            classes=classes,
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

        # 选择置信度最高的检测框
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

