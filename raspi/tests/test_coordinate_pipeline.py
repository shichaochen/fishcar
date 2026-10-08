"""坐标链路单元测试：透视变换标定 + 鱼缸边界接入运动映射。

使用合成数据验证（无需摄像头/模型）：
1. 单应矩阵把四个角点精确映射到 (0,0),(1,0),(1,1),(0,1)
2. 梯形（模拟倾斜俯视）的中心映射到约 (0.5, 0.5)
3. pixel_to_tank / tank_to_pixel 互逆
4. 边界内外判断正确
5. MecanumMapper 接入边界后：鱼在左→左移，鱼在中心→死区停车，鱼在缸外→停车
6. 未提供边界时回退到旧的全图归一化行为
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from src.aquarium_calibration import AquariumBounds, _compute_homography
from src.config_loader import MotionMappingConfig
from src.motion_mapping import MecanumMapper


def make_trapezoid_bounds() -> AquariumBounds:
    """模拟摄像头倾斜俯视：上边短、下边长（梯形）。"""
    return AquariumBounds(
        top_left=(200, 100),
        top_right=(440, 100),
        bottom_right=(520, 380),
        bottom_left=(120, 380),
    )


def make_config(**overrides):
    params = dict(
        deadzone=0.1,
        gain_x=0.8,
        gain_y=0.8,
        gain_rotation=0.0,
        max_speed=1.0,
        min_speed=0.15,
        invert_x=False,
        invert_y=False,
        reference_width=640,
        reference_height=480,
    )
    params.update(overrides)
    return MotionMappingConfig(**params)


class FakeDetection:
    """轻量替代 DetectionResult，避免拉入 ultralytics 重依赖。"""

    def __init__(self, center):
        self.has_target = center is not None
        self.center = center


def test_homography_maps_corners_exactly():
    b = make_trapezoid_bounds()
    for corner, expect in zip(
        [b.top_left, b.top_right, b.bottom_right, b.bottom_left],
        [(0, 0), (1, 0), (1, 1), (0, 1)],
    ):
        got = b.pixel_to_tank(corner)
        assert got is not None, f"角点 {corner} 应在边界内"
        assert abs(got[0] - expect[0]) < 1e-6, (corner, got, expect)
        assert abs(got[1] - expect[1]) < 1e-6, (corner, got, expect)


def test_homography_center_of_trapezoid():
    b = make_trapezoid_bounds()
    # 透视不是仿射变换：梯形顶点平均点不对应 (0.5, 0.5)。
    # 验证更本质的性质：归一化中心 (0.5, 0.5) 的逆映射落在四边形内、
    # 且在垂直对称轴上（梯形关于 x=320 对称）
    px, py = b.tank_to_pixel((0.5, 0.5))
    assert b.contains_point((px, py))
    assert abs(px - 320.0) < 1e-6, (px, py)
    # 无透视（轴对齐矩形）时，几何中心严格对应 (0.5, 0.5)
    rect = AquariumBounds((100, 100), (500, 100), (500, 400), (100, 400))
    got = rect.pixel_to_tank((300, 250))
    assert got is not None
    assert abs(got[0] - 0.5) < 1e-9 and abs(got[1] - 0.5) < 1e-9, got


def test_pixel_tank_roundtrip():
    b = make_trapezoid_bounds()
    rng = np.random.default_rng(42)
    for _ in range(20):
        # 在归一化坐标系内随机取点，经逆变换到像素再映射回来
        txn, tyn = rng.random(), rng.random()
        px, py = b.tank_to_pixel((txn, tyn))
        back = b.pixel_to_tank((px, py))
        assert back is not None
        assert abs(back[0] - txn) < 1e-6, (txn, back)
        assert abs(back[1] - tyn) < 1e-6, (tyn, back)


def test_contains_point():
    b = make_trapezoid_bounds()
    assert b.contains_point((320, 240))  # 缸内
    assert b.contains_point(b.top_left)  # 角点视为缸内
    assert not b.contains_point((10, 10))  # 缸外
    assert not b.contains_point((320, 470))  # 缸外


def test_compute_homography_rejects_degenerate():
    # 三点共线 → 退化
    src = np.array([[0, 0], [1, 0], [2, 0], [0, 1]], dtype=float)
    dst = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    try:
        _compute_homography(src, dst)
    except ValueError:
        return
    # 若未抛异常，至少验证映射是病态的（行列式接近 0）
    h = _compute_homography(src, dst)
    assert abs(np.linalg.det(h)) < 1e-6


def test_mapper_fish_left_of_center_moves_left():
    b = make_trapezoid_bounds()
    mapper = MecanumMapper(make_config(), b)
    # 鱼缸归一化 (0.25, 0.5) → 像素
    px, py = b.tank_to_pixel((0.25, 0.5))
    vec = mapper.calculate(FakeDetection((px, py)))
    assert vec.active
    assert vec.vx < 0, f"鱼在左，小车应左移，vx={vec.vx}"
    assert abs(vec.vy) < 1e-9


def test_mapper_fish_at_center_stops_in_deadzone():
    b = make_trapezoid_bounds()
    mapper = MecanumMapper(make_config(), b)
    px, py = b.tank_to_pixel((0.5, 0.5))
    vec = mapper.calculate(FakeDetection((px, py)))
    assert not vec.active
    assert vec.vx == 0.0 and vec.vy == 0.0


def test_mapper_fish_outside_tank_stops():
    b = make_trapezoid_bounds()
    mapper = MecanumMapper(make_config(), b)
    vec = mapper.calculate(FakeDetection((10.0, 10.0)))  # 缸外误检
    assert not vec.active
    assert vec.vx == 0.0 and vec.vy == 0.0 and vec.omega == 0.0


def test_mapper_no_detection_stops():
    b = make_trapezoid_bounds()
    mapper = MecanumMapper(make_config(), b)
    vec = mapper.calculate(FakeDetection(None))
    assert not vec.active


def test_mapper_without_bounds_falls_back_to_full_frame():
    mapper = MecanumMapper(make_config())  # 无边界
    # 全图中心 → 死区停车（旧行为）
    vec = mapper.calculate(FakeDetection((320.0, 240.0)))
    assert not vec.active
    # 全图左侧 → 左移（旧行为）
    vec = mapper.calculate(FakeDetection((64.0, 240.0)))
    assert vec.active and vec.vx < 0


def test_mapper_respects_min_speed_and_clip():
    b = make_trapezoid_bounds()
    mapper = MecanumMapper(make_config(), b)
    # 贴近左边缘：nx≈-1 → vx = -0.8（gain），未超 max_speed
    px, py = b.tank_to_pixel((0.02, 0.5))
    vec = mapper.calculate(FakeDetection((px, py)))
    assert vec.active
    assert -1.0 <= vec.vx < 0
    assert abs(vec.vx) >= 0.15 - 1e-9  # min_speed 钳位
