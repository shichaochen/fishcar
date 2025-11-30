"""
鱼缸边界标定模块
支持手动标定和从配置文件加载边界坐标
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


@dataclass
class AquariumBounds:
    """鱼缸边界（四个角点，按左上、右上、右下、左下顺序）"""
    top_left: tuple[int, int]
    top_right: tuple[int, int]
    bottom_right: tuple[int, int]
    bottom_left: tuple[int, int]

    def to_array(self) -> np.ndarray:
        """转换为numpy数组，用于透视变换"""
        return np.array([
            self.top_left,
            self.top_right,
            self.bottom_right,
            self.bottom_left
        ], dtype=np.float32)

    def get_rect(self) -> tuple[int, int, int, int]:
        """获取边界矩形 (x, y, width, height)"""
        x_coords = [self.top_left[0], self.top_right[0], 
                   self.bottom_right[0], self.bottom_left[0]]
        y_coords = [self.top_left[1], self.top_right[1], 
                   self.bottom_right[1], self.bottom_left[1]]
        x = int(min(x_coords))
        y = int(min(y_coords))
        w = int(max(x_coords) - x)
        h = int(max(y_coords) - y)
        return (x, y, w, h)

    def contains_point(self, point: tuple[float, float]) -> bool:
        """检查点是否在鱼缸边界内"""
        x, y = point
        # 使用射线法判断点是否在多边形内
        corners = [
            self.top_left, self.top_right,
            self.bottom_right, self.bottom_left
        ]
        n = len(corners)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = corners[i]
            xj, yj = corners[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside

    def normalize_point(self, point: tuple[float, float]) -> Optional[tuple[float, float]]:
        """
        将像素坐标转换为相对于鱼缸边界的归一化坐标 (0-1)
        返回 (x_norm, y_norm)，如果点在边界外返回 None
        """
        if not self.contains_point(point):
            return None

        # 获取边界矩形
        x, y, w, h = self.get_rect()
        
        # 计算相对坐标
        x_norm = (point[0] - x) / w if w > 0 else 0.0
        y_norm = (point[1] - y) / h if h > 0 else 0.0
        
        return (x_norm, y_norm)


class AquariumCalibrator:
    """鱼缸边界标定器"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.points: list[tuple[int, int]] = []
        self.bounds: Optional[AquariumBounds] = None

    def load_from_config(self) -> Optional[AquariumBounds]:
        """从配置文件加载边界"""
        if not self.config_path.exists():
            return None
        
        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            if "aquarium_bounds" not in data:
                return None
            
            bounds_data = data["aquarium_bounds"]
            return AquariumBounds(
                top_left=tuple(bounds_data["top_left"]),
                top_right=tuple(bounds_data["top_right"]),
                bottom_right=tuple(bounds_data["bottom_right"]),
                bottom_left=tuple(bounds_data["bottom_left"])
            )
        except Exception as e:
            print(f"加载标定配置失败: {e}")
            return None

    def save_to_config(self, bounds: AquariumBounds) -> None:
        """保存边界到配置文件"""
        data = {}
        if self.config_path.exists():
            try:
                with self.config_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass
        
        data["aquarium_bounds"] = {
            "top_left": list(bounds.top_left),
            "top_right": list(bounds.top_right),
            "bottom_right": list(bounds.bottom_right),
            "bottom_left": list(bounds.bottom_left)
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"标定数据已保存到: {self.config_path}")

    def interactive_calibrate(self, frame: cv2.typing.MatLike) -> Optional[AquariumBounds]:
        """
        交互式标定：在图像上点击四个角点
        顺序：左上、右上、右下、左下
        """
        self.points = []
        display = frame.copy()
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                if len(self.points) < 4:
                    self.points.append((x, y))
                    cv2.circle(display, (x, y), 5, (0, 255, 0), -1)
                    cv2.putText(display, f"Point {len(self.points)}", 
                               (x + 10, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.imshow("Calibration", display)
                    
                    if len(self.points) == 4:
                        # 自动确定四个角点
                        points_array = np.array(self.points, dtype=np.float32)
                        
                        # 使用更简单的方法：左上(x+y最小)、右上(x-y最大)、右下(x+y最大)、左下(x-y最小)
                        sums = points_array.sum(axis=1)
                        diffs = points_array[:, 0] - points_array[:, 1]
                        
                        top_left_idx = int(np.argmin(sums))
                        bottom_right_idx = int(np.argmax(sums))
                        top_right_idx = int(np.argmax(diffs))
                        bottom_left_idx = int(np.argmin(diffs))
                        
                        bounds = AquariumBounds(
                            top_left=tuple(points_array[top_left_idx].astype(int)),
                            top_right=tuple(points_array[top_right_idx].astype(int)),
                            bottom_right=tuple(points_array[bottom_right_idx].astype(int)),
                            bottom_left=tuple(points_array[bottom_left_idx].astype(int))
                        )
                        
                        # 绘制边界
                        bounds_pts = bounds.to_array().astype(int)
                        cv2.polylines(display, [bounds_pts], True, (255, 0, 0), 2)
                        cv2.putText(display, "Press SPACE to confirm, ESC to cancel", 
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                        cv2.imshow("Calibration", display)
                        self.bounds = bounds

        cv2.namedWindow("Calibration")
        cv2.setMouseCallback("Calibration", mouse_callback)
        
        cv2.putText(display, "Click 4 corners: Top-Left, Top-Right, Bottom-Right, Bottom-Left", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow("Calibration", display)
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                cv2.destroyWindow("Calibration")
                return None
            elif key == 32 and self.bounds is not None:  # SPACE
                cv2.destroyWindow("Calibration")
                return self.bounds

