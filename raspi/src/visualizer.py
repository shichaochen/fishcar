from __future__ import annotations

import time
from typing import Optional

import cv2
from loguru import logger

from .aquarium_calibration import AquariumBounds
from .config_loader import VisualizationConfig
from .detector import DetectionResult
from .motion_mapping import MotionVector


class Visualizer:
    def __init__(self, config: VisualizationConfig, aquarium_bounds: Optional[AquariumBounds] = None) -> None:
        self.config = config
        self.aquarium_bounds = aquarium_bounds
        self._last_time = time.time()
        self._fps = 0.0

    def render(self, frame, detection: DetectionResult, vector: MotionVector) -> None:
        if not self.config.enabled:
            return

        display = frame.copy()
        
        # 绘制鱼缸边界
        if self.config.show_aquarium_bounds and self.aquarium_bounds:
            bounds_pts = self.aquarium_bounds.to_array().astype(int)
            cv2.polylines(display, [bounds_pts], True, (255, 255, 0), 2)
            # 标注四个角点
            labels = ["TL", "TR", "BR", "BL"]
            for i, (pt, label) in enumerate(zip(bounds_pts, labels)):
                cv2.circle(display, tuple(pt), 5, (255, 255, 0), -1)
                cv2.putText(display, label, (pt[0] + 5, pt[1] - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # 绘制检测结果
        relative_coords = None
        if detection.has_target and detection.bbox:
            x1, y1, x2, y2 = detection.bbox
            cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if detection.center:
                cx, cy = detection.center
                cv2.circle(display, (int(cx), int(cy)), 4, (0, 0, 255), -1)
                
                # 计算相对坐标
                if self.aquarium_bounds and self.config.show_relative_coords:
                    relative_coords = self.aquarium_bounds.normalize_point((cx, cy))
                    if relative_coords:
                        x_norm, y_norm = relative_coords
                        # 在检测框上方显示相对坐标
                        coord_text = f"Rel: ({x_norm:.2f}, {y_norm:.2f})"
                        text_size = cv2.getTextSize(coord_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        cv2.rectangle(display, (x1, y1 - text_size[1] - 5), 
                                     (x1 + text_size[0] + 5, y1), (0, 0, 0), -1)
                        cv2.putText(display, coord_text, (x1 + 2, y1 - 5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 显示速度向量
        if self.config.show_vectors:
            text = f"vx={vector.vx:.2f} vy={vector.vy:.2f} ω={vector.omega:.2f}"
            cv2.putText(display, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # 如果有相对坐标，也显示
            if relative_coords:
                rel_text = f"Rel Coords: ({relative_coords[0]:.3f}, {relative_coords[1]:.3f})"
                cv2.putText(display, rel_text, (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        # 显示FPS
        if self.config.show_fps:
            now = time.time()
            dt = now - self._last_time
            self._fps = 1.0 / dt if dt > 0 else 0.0
            self._last_time = now
            y_pos = 60 if not (self.config.show_vectors and relative_coords) else 80
            cv2.putText(display, f"FPS: {self._fps:.1f}", (10, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        try:
            cv2.imshow(self.config.window_name, display)
            if cv2.waitKey(1) & 0xFF == 27:
                logger.info("用户按下 ESC，建议终止程序")
        except cv2.error as exc:
            logger.error("显示窗口失败: {}", exc)

    def close(self) -> None:
        if self.config.enabled:
            cv2.destroyAllWindows()

