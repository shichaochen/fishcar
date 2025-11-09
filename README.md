# FishCar 项目

该仓库用于部署“鱼驱动麦克纳姆小车”项目，包含 Raspberry Pi 5 端实时识别与控制代码，以及 Arduino 端电机与防撞输入固件。

## 目录结构

- `docs/`：设计说明与调试手册。
- `raspi/`：Raspberry Pi 端代码、配置与模型文件。
- `arduino/`：Arduino 固件与辅助脚本。

## 快速开始

1. 按 `docs/setup_guide.md` 准备硬件与环境。
2. 在 Raspberry Pi 端安装依赖并运行 `raspi/src/main.py`。
3. 将 `arduino/fishcar.ino` 烧录至 Arduino，按章节布线、调试。

更多细节请参考各子目录内的说明文件。

