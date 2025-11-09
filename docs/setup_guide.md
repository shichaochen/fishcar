# 搭建指南

## 1. 硬件准备

- Raspberry Pi 5（推荐 8 GB RAM）、Type-C 供电适配器。
- USB 摄像头，固定在距离鱼缸 25–35 cm 的俯视位置。
- 四轮麦克纳姆底盘、电机驱动板、12 V 电池组。
- Arduino UNO/Nano，4 个微动开关及防抖电路。
- 杂项：杜邦线、固定支架、散热片/风扇、防水措施。

## 2. Raspberry Pi 环境

1. 刷写 Raspberry Pi OS 64-bit，完成初始配置。
2. 更新系统：
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. 安装依赖包：
   ```bash
   sudo apt install -y python3-venv python3-dev libopencv-dev git screen
   ```
4. 创建虚拟环境并安装 Python 依赖：
   ```bash
   python3 -m venv ~/fishcar-venv
   source ~/fishcar-venv/bin/activate
   pip install -r /home/pi/fishcar/raspi/requirements.txt
   ```
5. 将 `best.pt` 放入 `/home/pi/fishcar/raspi/models/`。

## 3. Arduino 环境

1. 安装 Arduino IDE 或 PlatformIO。
2. 打开 `arduino/fishcar.ino`，检查串口波特率、引脚映射。
3. 根据 `arduino/README.md` 中的接线表完成布线。
4. 烧录固件，串口监视器确认能识别 `V 30 -10 0` 指令并打印 `STATUS ...`。

## 4. 系统联调

1. 启动 Arduino，确保电机驱动供电正常。
2. 在 Raspberry Pi 终端运行：
   ```bash
   source ~/fishcar-venv/bin/activate
   python /home/pi/fishcar/raspi/src/main.py
   ```
3. 观察 OpenCV 窗口中的检测框与小车同步动作。
4. 手动触发微动开关，确认小车停止并在鱼转向后恢复运动。

## 5. 常见问题

- **摄像头画面闪烁**：调整曝光、增益或添加补光。
- **YOLO 识别延迟高**：降低分辨率、启用模型量化或使用 `onnxruntime`。
- **串口无响应**：检查设备路径（`/dev/ttyACM0`）、波特率，确认用户在 `dialout` 组。
- **小车失控**：确认坐标系映射方向，必要时在 `raspi/config/default.yaml` 中调整符号和增益。

更多调试技巧请查看 `docs/system_overview.md` 和代码内注释。

