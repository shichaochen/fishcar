"""
小车移动轨迹记录模块
记录小车的位置、速度等信息，并支持可视化绘制
"""
from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import numpy as np

from .motion_mapping import MotionVector


@dataclass
class TrajectoryPoint:
    """轨迹点数据"""
    timestamp: float
    x: float  # 位置 x（归一化坐标 -1 到 1）
    y: float  # 位置 y（归一化坐标 -1 到 1）
    vx: float  # 速度 x
    vy: float  # 速度 y
    omega: float  # 角速度
    active: bool  # 是否激活


class TrajectoryRecorder:
    """轨迹记录器"""
    
    def __init__(
        self,
        max_points: int = 1000,
        sample_interval: float = 0.1,  # 采样间隔（秒）
        save_path: Optional[Path] = None,
    ) -> None:
        self.max_points = max_points
        self.sample_interval = sample_interval
        self.save_path = save_path
        
        # 使用 deque 存储轨迹点（自动限制最大数量）
        self.points: deque[TrajectoryPoint] = deque(maxlen=max_points)
        
        # 当前位置（通过速度积分得到）
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0  # 角度（弧度）
        
        # 上次采样时间
        self.last_sample_time = time.monotonic()
        
        # 是否启用记录
        self.enabled = True
        
    def update(self, vector: MotionVector) -> None:
        """更新轨迹（根据运动向量积分得到位置）"""
        if not self.enabled:
            return
            
        now = time.monotonic()
        dt = now - self.last_sample_time
        
        # 采样间隔控制
        if dt < self.sample_interval:
            return
            
        self.last_sample_time = now
        
        # 如果小车激活，更新位置
        if vector.active:
            # 简单的欧拉积分（可以改进为更精确的方法）
            # 考虑旋转的影响
            cos_theta = np.cos(self.current_theta)
            sin_theta = np.sin(self.current_theta)
            
            # 将速度从局部坐标系转换到全局坐标系
            vx_global = vector.vx * cos_theta - vector.vy * sin_theta
            vy_global = vector.vx * sin_theta + vector.vy * cos_theta
            
            # 积分得到位置
            self.current_x += vx_global * dt
            self.current_y += vy_global * dt
            self.current_theta += vector.omega * dt
            
            # 限制角度范围
            self.current_theta = np.fmod(self.current_theta, 2 * np.pi)
        else:
            # 小车停止，位置不变
            pass
        
        # 创建轨迹点
        point = TrajectoryPoint(
            timestamp=now,
            x=self.current_x,
            y=self.current_y,
            vx=vector.vx,
            vy=vector.vy,
            omega=vector.omega,
            active=vector.active,
        )
        
        self.points.append(point)
    
    def get_points(self) -> list[TrajectoryPoint]:
        """获取所有轨迹点"""
        return list(self.points)
    
    def get_recent_points(self, count: int = 100) -> list[TrajectoryPoint]:
        """获取最近的轨迹点"""
        return list(self.points)[-count:]
    
    def clear(self) -> None:
        """清空轨迹"""
        self.points.clear()
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0
        self.last_sample_time = time.monotonic()
    
    def reset_position(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0) -> None:
        """重置起始位置"""
        self.current_x = x
        self.current_y = y
        self.current_theta = theta
    
    def save(self, path: Optional[Path] = None) -> None:
        """保存轨迹到文件"""
        save_to = path or self.save_path
        if save_to is None:
            return
        
        data = {
            "points": [asdict(p) for p in self.points],
            "metadata": {
                "total_points": len(self.points),
                "duration": self.points[-1].timestamp - self.points[0].timestamp if len(self.points) > 1 else 0.0,
            }
        }
        
        save_to.parent.mkdir(parents=True, exist_ok=True)
        with save_to.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    def load(self, path: Path) -> None:
        """从文件加载轨迹"""
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.points.clear()
        for p_data in data["points"]:
            point = TrajectoryPoint(**p_data)
            self.points.append(point)
        
        # 设置当前位置为最后一个点
        if self.points:
            last = self.points[-1]
            self.current_x = last.x
            self.current_y = last.y
    
    def get_bounds(self) -> tuple[float, float, float, float]:
        """获取轨迹边界 (min_x, min_y, max_x, max_y)"""
        if not self.points:
            return (0.0, 0.0, 0.0, 0.0)
        
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        
        return (min(xs), min(ys), max(xs), max(ys))



