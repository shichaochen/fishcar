from __future__ import annotations

# 必须在导入 cv2 之前初始化
from . import opencv_init  # noqa: F401

import cv2
from loguru import logger

from .config_loader import CameraConfig


class CameraStream:
    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self.cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        logger.info("打开摄像头 index={}", self.config.device_index)
        self.cap = cv2.VideoCapture(self.config.device_index)
        if not self.cap.isOpened():
            msg = f"无法打开摄像头 index={self.config.device_index}"
            logger.error(msg)
            raise RuntimeError(msg)

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
        
        # 验证实际分辨率
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        logger.info("摄像头已打开 - 分辨率: {}x{}, FPS: {:.1f}", actual_width, actual_height, actual_fps)
        
        # 尝试读取一帧来验证摄像头是否真的工作
        ret, test_frame = self.cap.read()
        if not ret or test_frame is None:
            logger.warning("摄像头打开成功，但无法读取图像帧")
        else:
            logger.info("摄像头测试成功 - 图像尺寸: {}x{}", test_frame.shape[1], test_frame.shape[0])

    def read(self) -> cv2.typing.MatLike | None:
        if self.cap is None:
            logger.error("摄像头未初始化")
            return None

        success, frame = self.cap.read()
        if not success:
            logger.warning("摄像头读取失败")
            return None

        if self.config.flip_x:
            frame = cv2.flip(frame, 1)
        if self.config.flip_y:
            frame = cv2.flip(frame, 0)

        return frame

    def close(self) -> None:
        if self.cap is not None:
            logger.info("关闭摄像头")
            self.cap.release()
            self.cap = None

