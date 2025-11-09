# Raspberry Pi 模块

该目录包含 Raspberry Pi 5 端的实时检测与运动控制代码。

## 运行步骤

1. 激活虚拟环境并安装依赖：
   ```bash
   source ~/fishcar-venv/bin/activate
   pip install -r /home/pi/fishcar/raspi/requirements.txt
   ```
2. 将训练好的 YOLO 模型 `best.pt` 放置在 `/home/pi/fishcar/raspi/models/`。
3. 配置串口与摄像头参数，修改 `raspi/config/default.yaml`。
4. 运行主程序：
   ```bash
   python /home/pi/fishcar/raspi/src/main.py
   ```

## 目录说明

- `src/`：核心 Python 源码。
- `config/`：配置文件（YAML、JSON）。
- `models/`：YOLO 权重文件。
- `tests/`：单元测试与模拟脚本。
- `logs/`：运行日志输出（需在 `config` 中配置路径）。

## 日志与调试

运行时会在控制台输出检测结果与串口状态，并可选写入 `logs/`。必要时启用 `--debug` 选项或在配置中打开 `debug_overlay`。

