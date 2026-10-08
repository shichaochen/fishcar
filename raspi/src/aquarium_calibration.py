"""
鱼缸边界标定模块
支持手动标定和从配置文件加载边界坐标
"""
from __future__ import annotations

# 必须在导入 cv2 之前初始化
try:
    from . import opencv_init  # noqa: F401
except ImportError:
    # 如果作为独立模块导入，直接设置环境变量
    import os
    if not os.environ.get("DISPLAY"):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import cv2  # 仅交互式标定 UI 需要；坐标数学为纯 numpy
except ImportError:  # pragma: no cover
    cv2 = None  # type: ignore[assignment]


def _compute_homography(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """用 DLT 直接线性变换求解单应矩阵 H（3x3），将 src 点映射到 dst 点。

    纯 numpy 实现，不依赖 cv2，保证坐标数学在任何环境可测试。
    src/dst: shape (4, 2)，按左上、右上、右下、左下顺序对应。
    """
    if src.shape != (4, 2) or dst.shape != (4, 2):
        raise ValueError("src 和 dst 都必须是 4 个点的 (4, 2) 数组")
    rows = []
    for (x, y), (xp, yp) in zip(src.astype(np.float64), dst.astype(np.float64)):
        rows.append([-x, -y, -1, 0, 0, 0, xp * x, xp * y, xp])
        rows.append([0, 0, 0, -x, -y, -1, yp * x, yp * y, yp])
    _, _, vt = np.linalg.svd(np.asarray(rows, dtype=np.float64))
    h = vt[-1].reshape(3, 3)
    if abs(h[2, 2]) < 1e-12:
        raise ValueError("退化的角点配置，无法求解单应矩阵")
    return h / h[2, 2]


def _apply_homography(h: np.ndarray, point: tuple[float, float]) -> Optional[tuple[float, float]]:
    """对单个点应用单应矩阵，返回归一化后的 (x, y)。"""
    x, y = point
    p = h @ np.array([x, y, 1.0], dtype=np.float64)
    if abs(p[2]) < 1e-12:
        return None
    return (float(p[0] / p[2]), float(p[1] / p[2]))


@dataclass
class AquariumBounds:
    """鱼缸边界（四个角点，按左上、右上、右下、左下顺序）"""
    top_left: tuple[int, int]
    top_right: tuple[int, int]
    bottom_right: tuple[int, int]
    bottom_left: tuple[int, int]
    _homography: Optional[np.ndarray] = field(default=None, repr=False, compare=False)

    def to_array(self) -> np.ndarray:
        """转换为numpy数组，用于透视变换"""
        return np.array([
            self.top_left,
            self.top_right,
            self.bottom_right,
            self.bottom_left
        ], dtype=np.float32)

    def get_homography(self) -> np.ndarray:
        """获取像素坐标 → 鱼缸归一化坐标 [0,1]x[0,1] 的单应矩阵（惰性计算并缓存）。"""
        if self._homography is None:
            src = self.to_array().astype(np.float64)
            dst = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float64)
            self._homography = _compute_homography(src, dst)
        return self._homography

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

    def pixel_to_tank(self, point: tuple[float, float]) -> Optional[tuple[float, float]]:
        """将像素坐标经透视变换映射为鱼缸归一化坐标 [0,1]x[0,1]。

        左上为 (0,0)，右下为 (1,1)。点在四边形外时返回 None。
        这是坐标链路的核心：消除摄像头俯视角度带来的透视畸变。
        """
        mapped = _apply_homography(self.get_homography(), point)
        if mapped is None:
            return None
        xn, yn = mapped
        # 允许微小的浮点误差
        eps = 1e-6
        if not (-eps <= xn <= 1.0 + eps and -eps <= yn <= 1.0 + eps):
            return None
        return (min(max(xn, 0.0), 1.0), min(max(yn, 0.0), 1.0))

    def tank_to_pixel(self, point: tuple[float, float]) -> tuple[float, float]:
        """将鱼缸归一化坐标映射回像素坐标（用于可视化叠加）。"""
        h_inv = np.linalg.inv(self.get_homography())
        mapped = _apply_homography(h_inv, point)
        assert mapped is not None  # 逆变换恒有定义
        return mapped

    def contains_point(self, point: tuple[float, float]) -> bool:
        """检查点是否在鱼缸边界（四边形）内"""
        return self.pixel_to_tank(point) is not None

    def normalize_point(self, point: tuple[float, float]) -> Optional[tuple[float, float]]:
        """
        将像素坐标转换为相对于鱼缸边界的归一化坐标 (0-1)。
        返回 (x_norm, y_norm)，如果点在边界外返回 None。

        注：旧实现用外接矩形近似，现已改为透视变换，精度更高。
        接口保持不变，调用方可无缝升级。
        """
        return self.pixel_to_tank(point)


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

    def interactive_calibrate(self, frame: "cv2.typing.MatLike") -> Optional[AquariumBounds]:
        """
        交互式标定：在图像上点击四个角点
        顺序：左上、右上、右下、左下
        """
        if cv2 is None:
            raise RuntimeError("交互式标定需要 OpenCV，请先安装 opencv-python")
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

