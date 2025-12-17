from __future__ import annotations

# 必须在导入 cv2 之前初始化
from . import opencv_init  # noqa: F401

import os
import time
from pathlib import Path
from typing import Optional

import cv2
from loguru import logger

from .aquarium_calibration import AquariumBounds
from .config_loader import VisualizationConfig
from .detector import DetectionResult
from .motion_mapping import MotionVector
from .trajectory_recorder import TrajectoryRecorder


class Visualizer:
    def __init__(
        self,
        config: VisualizationConfig,
        aquarium_bounds: Optional[AquariumBounds] = None,
        trajectory_recorder: Optional[TrajectoryRecorder] = None,
    ) -> None:
        self.config = config
        self.aquarium_bounds = aquarium_bounds
        self.trajectory_recorder = trajectory_recorder
        self._last_time = time.time()
        self._fps = 0.0
        self._display_available = False
        self._last_save_time = 0.0
        self._save_interval = 2.0  # 每2秒保存一次图像（headless 模式）
        self._save_path = Path.home() / "fishcar" / "raspi" / "logs" / "latest_detection.jpg"
        
        # 检测是否有显示环境
        if not config.enabled:
            self._display_available = False
        else:
            # 检查 DISPLAY 环境变量
            display = os.environ.get("DISPLAY")
            if not display:
                logger.warning("未检测到 DISPLAY 环境变量，自动禁用可视化（headless 模式）")
                logger.info("将在 headless 模式下定期保存检测图像到: {}", self._save_path)
                self._display_available = False
                # 自动禁用配置中的可视化
                self.config.enabled = False
                # 确保保存目录存在
                self._save_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # 尝试创建一个测试窗口来验证显示是否可用
                try:
                    # 设置 OpenCV 使用无头后端（如果可用）
                    # 但先尝试正常模式
                    self._display_available = True
                except Exception:
                    self._display_available = False
                    self.config.enabled = False
                    self._save_path.parent.mkdir(parents=True, exist_ok=True)

    def render(self, frame, detection: DetectionResult, vector: MotionVector) -> None:
        # 如果可视化被禁用，直接返回（不进行任何处理）
        if not self.config.enabled:
            return

        # 创建显示图像（无论是否有显示环境，都需要绘制用于保存）
        display = frame.copy()
        
        # 绘制小车轨迹
        if self.trajectory_recorder and self.config.show_trajectory:
            self._draw_trajectory(display)
        
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

        # 尝试显示窗口或保存图像
        if self._display_available:
            # 有显示环境：尝试显示窗口
            try:
                cv2.imshow(self.config.window_name, display)
                if cv2.waitKey(1) & 0xFF == 27:
                    logger.info("用户按下 ESC，建议终止程序")
            except (cv2.error, SystemError, OSError) as exc:
                # 如果显示失败，禁用后续的可视化尝试
                if self._display_available:
                    logger.warning("显示窗口失败，自动禁用可视化: {}", exc)
                    logger.info("程序将在无头模式下继续运行（无图形界面）")
                    self._display_available = False
                    self.config.enabled = False
                    self._save_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Headless 模式：定期保存带标注的图像
            current_time = time.time()
            if current_time - self._last_save_time >= self._save_interval:
                try:
                    cv2.imwrite(str(self._save_path), display)
                    self._last_save_time = current_time
                    logger.debug("已保存检测图像到: {}", self._save_path)
                except Exception as exc:
                    logger.warning("保存图像失败: {}", exc)

    def _draw_trajectory(self, display) -> None:
        """在画面上绘制小车轨迹"""
        if not self.trajectory_recorder:
            return
        
        points = self.trajectory_recorder.get_recent_points(500)  # 最多显示最近500个点
        if len(points) < 2:
            return
        
        h, w = display.shape[:2]
        
        # 获取轨迹边界
        min_x, min_y, max_x, max_y = self.trajectory_recorder.get_bounds()
        if max_x == min_x:
            max_x = min_x + 0.1
        if max_y == min_y:
            max_y = min_y + 0.1
        
        # 将归一化坐标转换为像素坐标
        def norm_to_pixel(nx: float, ny: float) -> tuple[int, int]:
            # 归一化坐标范围通常是 -1 到 1，映射到画面中心区域
            # 留出边距
            margin = 50
            px = int((nx + 1) / 2 * (w - 2 * margin) + margin)
            py = int((ny + 1) / 2 * (h - 2 * margin) + margin)
            return (px, py)
        
        # 绘制轨迹线（渐变色，越新越亮）
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            
            # 根据时间计算颜色（越新越亮）
            alpha = i / len(points)
            color_intensity = int(255 * (1 - alpha * 0.5))  # 从255到127
            
            pt1 = norm_to_pixel(p1.x, p1.y)
            pt2 = norm_to_pixel(p2.x, p2.y)
            
            # 只绘制激活的点
            if p1.active and p2.active:
                cv2.line(display, pt1, pt2, (0, color_intensity, 255 - color_intensity), 2)
        
        # 绘制当前位置
        if points:
            last = points[-1]
            if last.active:
                current_pos = norm_to_pixel(last.x, last.y)
                cv2.circle(display, current_pos, 6, (0, 255, 0), -1)
                cv2.circle(display, current_pos, 8, (0, 255, 0), 2)
        
        # 显示轨迹信息
        info_text = f"Trajectory: {len(points)} points"
        cv2.putText(display, info_text, (w - 200, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def close(self) -> None:
        if self.config.enabled and self._display_available:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass  # 忽略关闭窗口时的错误

