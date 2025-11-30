# 树莓派安装指南

本文档详细说明如何将 FishCar 项目安装到 Raspberry Pi 5 上。

## 方法一：使用安装脚本（推荐）

### 1. 准备工作

- 确保 Raspberry Pi 5 已安装 **Raspberry Pi OS (64-bit)**
- 连接到网络（WiFi 或以太网）
- 通过 SSH 或直接连接显示器访问终端

### 2. 克隆项目

```bash
cd ~
git clone https://github.com/shichaochen/fishcar.git
cd fishcar
```

### 3. 运行安装脚本

```bash
chmod +x raspi/install.sh
bash raspi/install.sh
```

安装脚本会自动完成：
- 更新系统包
- 安装系统依赖（Python、OpenCV、Git 等）
- 配置串口权限
- 复制项目文件到 `~/fishcar`
- 创建 Python 虚拟环境
- 安装所有 Python 依赖

### 4. 安装后配置

#### 4.1 应用串口权限

安装脚本已将你的用户添加到 `dialout` 组，需要重新登录或运行：

```bash
newgrp dialout
```

#### 4.2 放置模型文件

将训练好的 YOLO 模型文件复制到指定位置：

```bash
cp /path/to/your/best.pt ~/fishcar/models/
```

#### 4.3 检查并修改配置

编辑配置文件：

```bash
nano ~/fishcar/config/default.yaml
```

主要需要检查的配置项：

- **串口设备**：`serial.port`（默认 `/dev/ttyACM0`，可通过 `ls /dev/ttyACM*` 查看）
- **摄像头参数**：`camera.device_index`、分辨率、FPS
- **模型路径**：`detector.weights_path`（应指向 `~/fishcar/models/best.pt`）
- **运动映射**：根据实际小车调整 `gain_x`、`gain_y` 等参数

#### 4.4 测试摄像头

```bash
# 查看可用摄像头
v4l2-ctl --list-devices

# 测试摄像头（如果支持）
ffplay /dev/video0
```

## 方法二：手动安装

如果安装脚本无法运行，可以按照以下步骤手动安装：

### 1. 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 安装系统依赖

```bash
sudo apt install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    libopencv-dev \
    libopencv-contrib-dev \
    git \
    screen \
    v4l-utils \
    usbutils
```

### 3. 配置串口权限

```bash
sudo usermod -a -G dialout $USER
# 重新登录或运行: newgrp dialout
```

### 4. 克隆项目

```bash
cd ~
git clone https://github.com/shichaochen/fishcar.git
cd fishcar
```

### 5. 创建虚拟环境

```bash
python3 -m venv ~/fishcar-venv
source ~/fishcar-venv/bin/activate
```

### 6. 安装 Python 依赖

```bash
# 升级 pip
pip install --upgrade pip setuptools wheel

# 安装 PyTorch (CPU 版本)
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu

# 安装其他依赖
cd ~/fishcar/raspi
pip install -r requirements.txt
```

### 7. 创建必要目录

```bash
mkdir -p ~/fishcar/models
mkdir -p ~/fishcar/logs
```

### 8. 放置模型文件

```bash
cp /path/to/your/best.pt ~/fishcar/models/
```

## 运行程序

### 基本运行

```bash
source ~/fishcar-venv/bin/activate
python ~/fishcar/src/main.py
```

### 后台运行（使用 screen）

```bash
screen -S fishcar
source ~/fishcar-venv/bin/activate
python ~/fishcar/src/main.py
# 按 Ctrl+A 然后 D 退出 screen
```

重新连接：

```bash
screen -r fishcar
```

### 后台运行（使用 systemd 服务，可选）

创建服务文件：

```bash
sudo nano /etc/systemd/system/fishcar.service
```

内容：

```ini
[Unit]
Description=FishCar Tracking System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/fishcar
Environment="PATH=/home/pi/fishcar-venv/bin"
ExecStart=/home/pi/fishcar-venv/bin/python /home/pi/fishcar/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable fishcar
sudo systemctl start fishcar
```

查看日志：

```bash
sudo journalctl -u fishcar -f
```

## 验证安装

### 1. 检查 Python 环境

```bash
source ~/fishcar-venv/bin/activate
python -c "import torch; import cv2; import ultralytics; print('所有依赖已安装')"
```

### 2. 检查串口设备

```bash
ls -l /dev/ttyACM*
# 应该能看到串口设备，且权限包含你的用户
```

### 3. 测试串口通信

```bash
source ~/fishcar-venv/bin/activate
python ~/fishcar/arduino/scripts/send_test.py /dev/ttyACM0
```

### 4. 运行主程序

```bash
source ~/fishcar-venv/bin/activate
python ~/fishcar/src/main.py
```

如果看到 OpenCV 窗口显示摄像头画面，说明安装成功！

## 常见问题

### 1. 串口权限不足

**错误**：`Permission denied: '/dev/ttyACM0'`

**解决**：
```bash
sudo usermod -a -G dialout $USER
newgrp dialout
# 或重新登录
```

### 2. 找不到摄像头

**错误**：`Cannot open camera`

**解决**：
```bash
# 检查摄像头设备
v4l2-ctl --list-devices
# 修改配置文件中的 device_index
```

### 3. PyTorch 安装失败

**解决**：使用 CPU 版本的 PyTorch：
```bash
pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu
```

### 4. 模型文件未找到

**错误**：`FileNotFoundError: best.pt`

**解决**：确保模型文件在正确位置：
```bash
ls -lh ~/fishcar/models/best.pt
```

### 5. 内存不足

如果 Raspberry Pi 内存较小，可以：
- 降低摄像头分辨率
- 使用量化后的模型
- 关闭可视化窗口

## 更新代码

如果项目代码有更新：

```bash
cd ~/fishcar
git pull origin main
# 如果有新的依赖，重新安装
source ~/fishcar-venv/bin/activate
pip install -r raspi/requirements.txt
```

## 卸载

如果需要完全卸载：

```bash
# 停止服务（如果使用了 systemd）
sudo systemctl stop fishcar
sudo systemctl disable fishcar
sudo rm /etc/systemd/system/fishcar.service

# 删除项目文件
rm -rf ~/fishcar
rm -rf ~/fishcar-venv
```

