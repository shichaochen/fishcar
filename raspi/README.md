# Raspberry Pi 模块

该目录包含 Raspberry Pi 5 端的实时检测与运动控制代码。

## 运行步骤

1. 激活虚拟环境并安装依赖：
   ```bash
   source ~/fishcar-venv/bin/activate
   pip install -r /home/pi/fishcar/raspi/requirements.txt
   ```
2. **准备 YOLO 模型**（二选一）：
   - **选项A**：使用自定义模型 - 将训练好的 `best.pt` 放置在 `/home/pi/fishcar/raspi/models/`
   - **选项B**：使用预训练模型 - 如果模型文件不存在，系统会自动使用 YOLOv8n 预训练模型（COCO 数据集，包含 fish 类别）
     - 首次运行会自动下载模型（需要网络连接）
     - 可以在配置文件中设置：`weights_path: "yolov8n.pt"` 或 `"yolov8s.pt"`
   - 更多模型选项请参考：`docs/fish_detection_models.md`
3. 配置串口与摄像头参数，修改 `raspi/config/default.yaml`。
4. **（可选）运行鱼缸边界标定工具**：
   ```bash
   # 方法1：使用启动脚本（推荐）
   cd ~/fishcar/raspi
   bash calibrate.sh
   
   # 方法2：使用模块方式
   cd ~/fishcar
   source ~/fishcar-venv/bin/activate
   python -m raspi.src.calibrate_aquarium
   ```
   在摄像头画面上点击四个角点（左上、右上、右下、左下），按 SPACE 确认保存。
   标定后会在调试画面中显示鱼缸边界和鱼的相对坐标。
5. 运行主程序：
   ```bash
   # 方法1：使用启动脚本（推荐）
   cd ~/fishcar/raspi
   bash run.sh
   
   # 方法2：使用模块方式
   cd ~/fishcar
   source ~/fishcar-venv/bin/activate
   python -m raspi.src.main
   
   # 方法3：直接运行（已修复导入问题）
   cd ~/fishcar/raspi
   source ~/fishcar-venv/bin/activate
   python src/main.py
   ```

## 目录说明

- `src/`：核心 Python 源码。
- `config/`：配置文件（YAML、JSON）。
- `models/`：YOLO 权重文件。
- `tests/`：单元测试与模拟脚本。
- `logs/`：运行日志输出（需在 `config` 中配置路径）。

## 日志与调试

运行时会在控制台输出检测结果与串口状态，并可选写入 `logs/`。必要时启用 `--debug` 选项或在配置中打开 `debug_overlay`。

### 鱼缸边界标定

系统支持在调试画面中显示鱼缸边界，并实时显示鱼相对于鱼缸边界的归一化坐标（0-1范围）。

- **标定工具**：
  - 使用启动脚本：`bash ~/fishcar/raspi/calibrate.sh`
  - 或模块方式：`python -m raspi.src.calibrate_aquarium`
- **详细说明**：参考 `docs/aquarium_calibration.md`
- **显示效果**：
  - 黄色线条绘制鱼缸边界
  - 检测框上方显示相对坐标：`Rel: (x, y)`
  - 画面左上角显示相对坐标：`Rel Coords: (x, y)`

与 Arduino 的通信采用简单文本协议：

- Raspberry Pi 发送 `V <vx> <vy> <omega>`，内部根据速度向量缩放到 -127~127。
- Arduino 返回 `STATUS front=0 back=0 left=0 right=0` 以及碰撞提示，用于 `SafetyManager` 判断限位。
- 配置信息（串口端口、波特率等）可在 `config/default.yaml` 中调整。

