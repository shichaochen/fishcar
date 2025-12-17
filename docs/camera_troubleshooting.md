# USB 摄像头故障排除指南

## 如何检查 USB 摄像头设备

### 方法1：使用查找工具（推荐）

```bash
cd ~/fishcar/raspi
source ~/fishcar-venv/bin/activate
python -m raspi.src.find_camera
```

### 方法2：手动检查设备文件

```bash
# 查看所有视频设备
ls -l /dev/video*

# 通常 USB 摄像头显示为：
# /dev/video0
# /dev/video1
# 等等
```

### 方法3：使用 v4l2-ctl 工具

```bash
# 安装工具（如果未安装）
sudo apt install v4l-utils

# 列出所有视频设备
v4l2-ctl --list-devices

# 查看设备详细信息
v4l2-ctl --device=/dev/video0 --all
```

### 方法4：查看 USB 设备

```bash
# 查看所有 USB 设备
lsusb

# 应该看到类似这样的输出：
# Bus 001 Device 003: ID 046d:0825 Logitech, Inc. Webcam C270
```

### 方法5：使用 Python 测试

```python
import cv2

# 测试不同的设备索引
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"摄像头 {i} 可用，分辨率: {frame.shape[1]}x{frame.shape[0]}")
        cap.release()
```

## 常见问题

### 问题1：找不到摄像头设备

**检查步骤**：

1. **检查 USB 连接**：
   ```bash
   lsusb
   # 应该能看到摄像头设备
   ```

2. **检查设备文件**：
   ```bash
   ls -l /dev/video*
   # 应该能看到 /dev/video0 或类似设备
   ```

3. **检查权限**：
   ```bash
   ls -l /dev/video0
   # 应该显示类似: crw-rw----+ 1 root video 81, 0 ...
   # 如果权限不对，运行：
   sudo usermod -a -G video $USER
   newgrp video
   ```

4. **查看系统日志**：
   ```bash
   dmesg | grep -i video
   dmesg | tail -20
   ```

### 问题2：摄像头被其他程序占用

**解决方法**：

```bash
# 查找占用摄像头的进程
lsof /dev/video0

# 或
fuser /dev/video0

# 结束占用进程
sudo kill -9 <PID>
```

### 问题3：设备索引不正确

**解决方法**：

1. **使用查找工具确定正确的索引**：
   ```bash
   python -m raspi.src.find_camera
   ```

2. **更新配置文件**：
   ```bash
   nano ~/fishcar/raspi/config/default.yaml
   ```
   
   修改：
   ```yaml
   camera:
     device_index: 0  # 改为实际设备索引
   ```

### 问题4：摄像头画面黑屏或无法读取

**可能原因**：

1. **摄像头需要初始化时间**：等待几秒后重试
2. **分辨率不支持**：尝试降低分辨率
3. **驱动问题**：检查是否需要安装驱动

**解决方法**：

```bash
# 测试摄像头
python3 << EOF
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"成功，分辨率: {frame.shape[1]}x{frame.shape[0]}")
        cv2.imwrite('/tmp/test.jpg', frame)
        print("测试图片已保存到 /tmp/test.jpg")
    else:
        print("无法读取画面")
    cap.release()
else:
    print("无法打开摄像头")
EOF
```

## 配置摄像头

### 在配置文件中设置

```yaml
camera:
  device_index: 0      # 设备索引（通常是 0）
  width: 1280          # 宽度
  height: 720          # 高度
  fps: 30              # 帧率
  flip_x: false        # 水平翻转
  flip_y: true         # 垂直翻转（根据安装方向）
```

### 常见设备索引

- **第一个摄像头**: `device_index: 0` (对应 `/dev/video0`)
- **第二个摄像头**: `device_index: 1` (对应 `/dev/video1`)
- 如果有多个摄像头，依次递增

## 测试摄像头

### 快速测试

```bash
# 使用 ffmpeg（如果已安装）
ffmpeg -f v4l2 -i /dev/video0 -frames 1 /tmp/test.jpg

# 或使用 Python
python3 -c "import cv2; cap = cv2.VideoCapture(0); ret, frame = cap.read(); cv2.imwrite('/tmp/test.jpg', frame) if ret else print('失败'); cap.release()"
```

### 查看测试图片

```bash
# 如果有图形界面
xdg-open /tmp/test.jpg

# 或传输到电脑查看
scp /tmp/test.jpg user@computer:/tmp/
```

## 多摄像头情况

如果有多个摄像头：

```bash
# 列出所有设备
v4l2-ctl --list-devices

# 测试每个设备
for i in 0 1 2; do
  echo "测试 /dev/video$i:"
  v4l2-ctl --device=/dev/video$i --all | head -5
done
```

## 性能优化

### 降低分辨率（提高帧率）

```yaml
camera:
  width: 640   # 从 1280 降低到 640
  height: 480  # 从 720 降低到 480
  fps: 30
```

### 降低帧率（减少 CPU 使用）

```yaml
camera:
  width: 1280
  height: 720
  fps: 15  # 从 30 降低到 15
```

## 快速诊断命令

```bash
# 一键诊断
echo "=== USB 设备 ===" && lsusb | grep -i -E "camera|video|webcam" && \
echo "=== 视频设备 ===" && ls -l /dev/video* 2>/dev/null && \
echo "=== 用户组 ===" && groups | grep video && \
echo "=== 设备占用 ===" && (lsof /dev/video0 2>/dev/null || echo "未占用") && \
echo "=== v4l2 设备 ===" && (v4l2-ctl --list-devices 2>/dev/null | head -10 || echo "v4l2-ctl 未安装")
```

## 获取帮助

如果以上方法都无法解决问题：

1. 检查摄像头在其他设备上是否正常工作
2. 尝试不同的 USB 端口
3. 检查 USB 线是否支持数据传输
4. 查看系统日志：`dmesg | tail -50`
5. 检查是否需要安装特定的摄像头驱动

