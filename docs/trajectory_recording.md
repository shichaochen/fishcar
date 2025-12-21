# 小车移动轨迹记录功能

## 功能说明

系统可以实时记录小车的移动轨迹，并在调试画面中可视化显示。轨迹数据包括：
- 位置坐标（通过速度积分得到）
- 速度信息（vx, vy, omega）
- 时间戳
- 激活状态

## 使用方法

### 1. 启用轨迹记录

在配置文件 `raspi/config/default.yaml` 中：

```yaml
# 轨迹记录
trajectory:
  enabled: true  # 启用轨迹记录
  max_points: 1000  # 最大记录点数
  sample_interval: 0.1  # 采样间隔（秒）
  save_path: "/home/pi/fishcar/raspi/logs/trajectory.json"  # 保存路径

# 可视化
visualization:
  show_trajectory: true  # 在画面中显示轨迹
```

### 2. 运行程序

正常启动程序后，轨迹会自动记录：

```bash
cd ~/fishcar/raspi
bash run.sh
```

### 3. 查看轨迹

在 OpenCV 窗口中可以看到：
- **轨迹线**：渐变色线条显示小车移动路径（越新越亮）
- **当前位置**：绿色圆点标记小车当前位置
- **轨迹信息**：画面右上角显示轨迹点数

### 4. 保存轨迹

程序退出时会自动保存轨迹数据到指定文件（如果配置了 `save_path`）。

## 轨迹数据格式

保存的 JSON 文件格式：

```json
{
  "points": [
    {
      "timestamp": 1234567890.123,
      "x": 0.5,
      "y": -0.3,
      "vx": 0.2,
      "vy": -0.1,
      "omega": 0.0,
      "active": true
    },
    ...
  ],
  "metadata": {
    "total_points": 500,
    "duration": 50.0
  }
}
```

## 坐标系统

- **位置坐标 (x, y)**：归一化坐标，范围 -1 到 1
  - (0, 0) = 起始位置
  - 通过速度积分计算得到
  - 考虑旋转影响（局部坐标系转全局坐标系）

- **速度 (vx, vy, omega)**：直接来自运动向量
  - vx, vy: 线速度（归一化）
  - omega: 角速度（归一化）

## 配置参数说明

### max_points
- 最大记录点数
- 超过此数量时，旧的点会被自动删除（FIFO）
- 建议值：500-2000

### sample_interval
- 采样间隔（秒）
- 控制轨迹点的密度
- 较小的值 = 更密集的轨迹点 = 更精确但占用更多内存
- 建议值：0.05-0.2 秒

### save_path
- 轨迹保存路径
- 设置为 `null` 则不自动保存
- 程序退出时自动保存
- 也可以手动调用 `trajectory_recorder.save()` 保存

## 高级用法

### 手动控制轨迹记录

在代码中可以：

```python
# 清空轨迹
trajectory_recorder.clear()

# 重置起始位置
trajectory_recorder.reset_position(x=0.0, y=0.0, theta=0.0)

# 手动保存
trajectory_recorder.save(Path("custom_path.json"))

# 加载历史轨迹
trajectory_recorder.load(Path("trajectory.json"))
```

### 分析轨迹数据

可以使用 Python 分析保存的轨迹数据：

```python
import json
import matplotlib.pyplot as plt

with open("trajectory.json") as f:
    data = json.load(f)

points = data["points"]
xs = [p["x"] for p in points]
ys = [p["y"] for p in points]

plt.plot(xs, ys)
plt.xlabel("X")
plt.ylabel("Y")
plt.title("Car Trajectory")
plt.grid(True)
plt.show()
```

## 注意事项

1. **内存使用**：轨迹点会占用内存，建议根据实际需求设置 `max_points`
2. **精度**：位置通过速度积分得到，长时间运行可能有累积误差
3. **坐标系**：轨迹坐标是归一化的，需要根据实际物理尺寸转换
4. **性能**：绘制大量轨迹点可能影响帧率，可以调整 `max_points` 或只显示最近的点

## 故障排除

### 轨迹不显示

- 检查 `trajectory.enabled` 是否为 `true`
- 检查 `visualization.show_trajectory` 是否为 `true`
- 确认小车有运动（轨迹只在激活时记录）

### 轨迹不准确

- 检查速度映射配置是否正确
- 调整 `sample_interval` 获得更密集的采样
- 检查是否有速度限制导致积分不准确

### 轨迹文件未保存

- 检查 `save_path` 是否配置
- 检查目录权限
- 确认程序正常退出（Ctrl+C 或 SIGTERM）



