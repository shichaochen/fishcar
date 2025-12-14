# 串口连接故障排除指南

## 常见错误

### 错误1: `SerialException: could not open port /dev/ttyACM0: No such file or directory`

**原因**: 串口设备不存在或路径不正确

**解决方法**:

1. **查找串口设备**:
   ```bash
   # 方法1: 使用查找工具
   cd ~/fishcar/raspi
   source ~/fishcar-venv/bin/activate
   python -m raspi.src.find_serial
   
   # 方法2: 手动查找
   ls -l /dev/ttyACM* /dev/ttyUSB*
   ```

2. **检查 Arduino 连接**:
   ```bash
   # 查看 USB 设备
   lsusb
   
   # 查看串口设备详细信息
   dmesg | grep tty
   ```

3. **更新配置文件**:
   ```bash
   nano ~/fishcar/raspi/config/default.yaml
   ```
   
   找到 `serial.port` 并修改为实际设备路径，例如：
   ```yaml
   serial:
     port: "/dev/ttyACM0"  # 或 "/dev/ttyUSB0" 或其他
   ```

### 错误2: `Permission denied`

**原因**: 用户没有串口访问权限

**解决方法**:
```bash
# 将用户添加到 dialout 组
sudo usermod -a -G dialout $USER

# 重新登录或运行
newgrp dialout

# 验证权限
groups | grep dialout
```

### 错误3: `Device or resource busy`

**原因**: 串口被其他程序占用

**解决方法**:
```bash
# 查找占用串口的进程
lsof /dev/ttyACM0

# 或
fuser /dev/ttyACM0

# 结束占用进程
sudo kill -9 <PID>
```

## 串口设备查找

### 使用查找工具

```bash
cd ~/fishcar/raspi
source ~/fishcar-venv/bin/activate
python -m raspi.src.find_serial
```

### 手动查找

```bash
# 查看所有串口设备
ls -l /dev/tty*

# 查看 ACM 设备（Arduino UNO/Nano 通常使用）
ls -l /dev/ttyACM*

# 查看 USB 串口设备
ls -l /dev/ttyUSB*

# 查看 GPIO 串口（如果使用 GPIO 连接）
ls -l /dev/ttyAMA*
```

### 常见设备路径

- **Arduino UNO/Nano (USB)**: `/dev/ttyACM0` 或 `/dev/ttyACM1`
- **Arduino 通过 USB 转串口**: `/dev/ttyUSB0` 或 `/dev/ttyUSB1`
- **Raspberry Pi GPIO 串口**: `/dev/ttyAMA0` 或 `/dev/ttyS0`

## 连接检查步骤

### 1. 检查硬件连接

- [ ] Arduino 已通过 USB 连接到树莓派
- [ ] USB 线支持数据传输（不只是充电线）
- [ ] Arduino 已上电（LED 灯亮）
- [ ] 没有使用 USB Hub（直接连接到树莓派）

### 2. 检查设备识别

```bash
# 查看 USB 设备
lsusb

# 应该看到类似这样的输出：
# Bus 001 Device 004: ID 2341:0043 Arduino SA Uno R3 (CDC ACM)
```

### 3. 检查设备文件

```bash
# 插拔 Arduino，观察设备变化
ls -l /dev/ttyACM* /dev/ttyUSB*

# 拔掉 Arduino 后，设备应该消失
# 插上 Arduino 后，设备应该出现
```

### 4. 检查权限

```bash
# 检查当前用户组
groups

# 应该包含 dialout
# 如果没有，运行：
sudo usermod -a -G dialout $USER
newgrp dialout
```

### 5. 测试串口通信

```bash
# 使用 minicom 或 screen 测试
sudo apt install minicom
sudo minicom -D /dev/ttyACM0 -b 9600

# 或使用 screen
screen /dev/ttyACM0 9600

# 如果看到 Arduino 的输出（如 "READY"），说明连接正常
# 按 Ctrl+A 然后 K 退出 screen
```

## 配置串口

### 方法1: 修改配置文件

```bash
nano ~/fishcar/raspi/config/default.yaml
```

修改：
```yaml
serial:
  port: "/dev/ttyACM0"  # 替换为实际设备路径
  baudrate: 9600
  timeout: 0.1
```

### 方法2: 使用命令行参数（如果支持）

某些版本可能支持通过环境变量或命令行参数覆盖配置。

## 自动检测串口（未来功能）

可以修改代码自动检测串口设备：

```python
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
for port in ports:
    if 'Arduino' in port.description or 'ACM' in port.device:
        print(f"找到 Arduino: {port.device}")
```

## 常见问题

### Q: 为什么设备路径是 ttyACM0 而不是 ttyUSB0？

A: Arduino UNO/Nano 使用 USB CDC (Communication Device Class)，在 Linux 上显示为 `/dev/ttyACM*`。如果使用 USB 转串口芯片（如 CH340、FT232），则显示为 `/dev/ttyUSB*`。

### Q: 设备路径会变化吗？

A: 如果连接多个 USB 设备，设备编号可能会变化。建议：
- 使用 USB 设备 ID 固定设备（需要 udev 规则）
- 或使用符号链接
- 或每次连接后检查设备路径

### Q: 如何固定设备路径？

创建 udev 规则：

```bash
# 创建规则文件
sudo nano /etc/udev/rules.d/99-arduino.rules

# 添加内容（替换为你的 Arduino 的 ID）
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="0043", SYMLINK+="arduino"

# 重新加载规则
sudo udevadm control --reload-rules
sudo udevadm trigger

# 现在可以使用 /dev/arduino
```

### Q: 串口通信不稳定怎么办？

A: 
1. 检查 USB 线质量
2. 降低波特率
3. 增加超时时间
4. 检查电源供应（Arduino 需要稳定电源）

## 快速诊断命令

```bash
# 一键诊断
echo "=== USB 设备 ===" && lsusb | grep -i arduino && \
echo "=== 串口设备 ===" && ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null && \
echo "=== 用户组 ===" && groups | grep dialout && \
echo "=== 串口占用 ===" && (lsof /dev/ttyACM0 2>/dev/null || echo "未占用")
```

## 获取帮助

如果以上方法都无法解决问题：

1. 检查 Arduino IDE 串口监视器是否能连接
2. 尝试在另一台电脑上测试 Arduino
3. 检查 Arduino 固件是否正确烧录
4. 查看系统日志：`dmesg | tail -20`

