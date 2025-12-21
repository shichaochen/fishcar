# FishCar 项目

该仓库用于部署“鱼驱动麦克纳姆小车”项目，包含 Raspberry Pi 5 端实时识别与控制代码，以及 Arduino 端电机与防撞输入固件。

## 目录结构

- `docs/`：设计说明与调试手册。
- `raspi/`：Raspberry Pi 端代码、配置与模型文件。
- `arduino/`：Arduino 固件与辅助脚本。

## 快速开始

### Raspberry Pi 安装

**推荐方式（使用安装脚本）**：
```bash
cd ~
git clone https://github.com/shichaochen/fishcar.git
cd fishcar
chmod +x raspi/install.sh
bash raspi/install.sh
```

详细安装步骤请参考：[安装指南](docs/installation_guide.md)

### Arduino 固件

1. 打开 `arduino/fishcar.ino` 并烧录到 Arduino
2. **硬件连接**：详细连接方法请参考 [硬件连接指南](docs/hardware_connection.md)
3. 按照 `arduino/README.md` 完成硬件接线
4. 使用串口监视器测试指令格式：`V <vx> <vy> <omega>`

### 运行程序

**推荐方式（使用启动脚本）**：
```bash
cd ~/fishcar/raspi
source ~/fishcar-venv/bin/activate
bash run.sh
```

**或者使用模块方式**：
```bash
cd ~/fishcar/raspi
source ~/fishcar-venv/bin/activate
python -m src.main
```

**或者直接运行**：
```bash
cd ~/fishcar
source ~/fishcar-venv/bin/activate
python ~/fishcar/raspi/src/main.py
```

更多细节请参考：
- [系统概览](docs/system_overview.md)
- [搭建指南](docs/setup_guide.md)
- [安装指南](docs/installation_guide.md)
- [硬件连接指南](docs/hardware_connection.md) - **Arduino 与树莓派连接方法**
- [鱼缸标定指南](docs/aquarium_calibration.md)

