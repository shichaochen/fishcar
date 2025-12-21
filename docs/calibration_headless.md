# 无图形界面环境下的标定方法

如果树莓派没有连接显示器或通过 SSH 连接（无图形界面），可以使用以下方法进行标定。

## 方法1：保存图片后手动标定（推荐）

### 步骤1：保存摄像头画面

```bash
cd ~/fishcar/raspi
source ~/fishcar-venv/bin/activate
python -m raspi.src.calibrate_aquarium --save-image /tmp/aquarium_frame.jpg
```

### 步骤2：在有图形界面的环境中标定

将图片传输到有图形界面的电脑（使用 scp、USB 或其他方式），然后：

```bash
# 在有图形界面的电脑上
python -m raspi.src.calibrate_aquarium --from-image /path/to/aquarium_frame.jpg
```

或者使用图片查看器查看图片，记录四个角点的像素坐标。

### 步骤3：将标定文件复制回树莓派

标定完成后，将生成的 `calibration.json` 文件复制回树莓派：

```bash
# 在树莓派上
scp user@computer:/path/to/calibration.json ~/fishcar/raspi/config/
```

## 方法2：手动输入坐标

如果你知道鱼缸四个角点的像素坐标，可以直接输入：

```bash
python -m raspi.src.calibrate_aquarium --manual TL_X TL_Y TR_X TR_Y BR_X BR_Y BL_X BL_Y
```

例如：
```bash
python -m raspi.src.calibrate_aquarium --manual 100 50 600 50 600 400 100 400
```

坐标说明：
- `TL_X, TL_Y`: 左上角 (Top-Left)
- `TR_X, TR_Y`: 右上角 (Top-Right)
- `BR_X, BR_Y`: 右下角 (Bottom-Right)
- `BL_X, BL_Y`: 左下角 (Bottom-Left)

## 方法3：直接编辑配置文件

你也可以直接编辑 JSON 配置文件：

```bash
nano ~/fishcar/raspi/config/calibration.json
```

格式：
```json
{
  "aquarium_bounds": {
    "top_left": [100, 50],
    "top_right": [600, 50],
    "bottom_right": [600, 400],
    "bottom_left": [100, 400]
  }
}
```

## 方法4：使用 VNC 或 X11 转发

### 使用 VNC

1. 在树莓派上安装 VNC 服务器：
   ```bash
   sudo apt install tightvncserver
   vncserver :1
   ```

2. 在电脑上使用 VNC 客户端连接

3. 运行标定工具：
   ```bash
   export DISPLAY=:1
   python -m raspi.src.calibrate_aquarium
   ```

### 使用 X11 转发（SSH）

1. SSH 连接时启用 X11 转发：
   ```bash
   ssh -X pi@raspberrypi
   ```

2. 运行标定工具：
   ```bash
   python -m raspi.src.calibrate_aquarium
   ```

## 获取坐标的方法

### 使用图片查看器

1. 保存图片：`--save-image /tmp/frame.jpg`
2. 在图片查看器中打开
3. 将鼠标悬停在四个角点上，查看坐标（大多数图片查看器会显示坐标）

### 使用 Python 脚本

创建一个简单的脚本查看坐标：

```python
import cv2

img = cv2.imread('/tmp/aquarium_frame.jpg')
cv2.namedWindow('image')

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"坐标: ({x}, {y})")

cv2.setMouseCallback('image', mouse_callback)
cv2.imshow('image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
```

### 使用在线工具

上传图片到在线图片编辑器，查看像素坐标。

## 验证标定结果

标定完成后，运行主程序查看效果：

```bash
cd ~/fishcar/raspi
bash run.sh
```

在 OpenCV 窗口中应该能看到黄色边界线。

## 故障排除

### 如果坐标输入错误

可以重新运行标定工具，或直接编辑 JSON 文件。

### 如果边界显示不正确

检查坐标顺序是否正确：
- 左上角：x+y 最小
- 右上角：x-y 最大
- 右下角：x+y 最大
- 左下角：x-y 最小

### 如果需要调整

直接编辑 `calibration.json` 文件，修改坐标值即可。



