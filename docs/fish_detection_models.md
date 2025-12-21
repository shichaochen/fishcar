# 鱼类识别模型资源

## 推荐的模型来源

### 1. GitHub 开源项目

#### Fish-identification-and-detection
- **项目地址**: https://github.com/qunshansj/Fish-identification-and-detection
- **特点**: 
  - 基于 YOLOv8
  - 包含训练好的模型
  - 提供完整源码和数据集
  - 支持图片、视频、摄像头输入

**使用方法**:
```bash
# 克隆项目
git clone https://github.com/qunshansj/Fish-identification-and-detection.git

# 复制模型文件到项目
cp Fish-identification-and-detection/runs/detect/train/weights/best.pt ~/fishcar/raspi/models/
```

### 2. Roboflow Universe

Roboflow Universe 提供了大量预训练的 YOLO 模型：

- **访问**: https://universe.roboflow.com
- **搜索**: "fish detection" 或 "aquarium fish"
- **特点**: 
  - 多种鱼类检测模型
  - 可直接下载 YOLOv5/YOLOv8 格式
  - 包含不同精度和速度的版本

### 3. 使用通用目标检测模型

如果找不到专门的鱼类模型，可以使用通用目标检测模型：

#### YOLOv8 预训练模型
```python
from ultralytics import YOLO

# 使用 COCO 预训练模型（包含多种动物类别）
model = YOLO('yolov8n.pt')  # nano 版本，适合树莓派
# 或
model = YOLO('yolov8s.pt')  # small 版本，精度更高
```

COCO 数据集包含 "fish" 类别，可以直接使用。

## 在项目中使用模型

### 方法1：使用现有的 best.pt

如果你已经有训练好的模型：

```bash
# 将模型文件放到指定目录
cp /path/to/your/best.pt ~/fishcar/raspi/models/best.pt

# 确保配置文件中的路径正确
# raspi/config/default.yaml:
# detector:
#   weights_path: "/home/pi/fishcar/raspi/models/best.pt"
```

### 方法2：使用 YOLOv8 预训练模型

修改代码以支持直接使用预训练模型：

```python
# 在 raspi/src/detector.py 中
from ultralytics import YOLO

class FishDetector:
    def __init__(self, config: DetectorConfig) -> None:
        self.config = config
        # 如果路径不存在，使用预训练模型
        if Path(config.weights_path).exists():
            self.model = YOLO(config.weights_path)
        else:
            # 使用 COCO 预训练模型（包含 fish 类别）
            self.model = YOLO('yolov8n.pt')
            logger.warning(f"模型文件不存在，使用预训练模型: {config.weights_path}")
```

### 方法3：训练自定义模型

如果需要针对特定鱼类训练：

1. **收集数据集**
   - 拍摄鱼缸中的鱼
   - 使用标注工具（如 LabelImg）标注边界框

2. **训练模型**
   ```python
   from ultralytics import YOLO
   
   # 加载预训练模型
   model = YOLO('yolov8n.pt')
   
   # 训练
   model.train(
       data='path/to/your/dataset.yaml',
       epochs=100,
       imgsz=640,
       device='cpu'  # 树莓派使用 CPU
   )
   ```

3. **导出模型**
   ```python
   # 训练完成后，best.pt 在 runs/detect/train/weights/ 目录
   # 复制到项目目录
   cp runs/detect/train/weights/best.pt ~/fishcar/raspi/models/
   ```

## 模型选择建议

### 树莓派 5 推荐配置

1. **YOLOv8n (nano)**
   - 速度最快
   - 精度较低
   - 适合实时性要求高的场景

2. **YOLOv8s (small)**
   - 速度和精度平衡
   - 推荐用于树莓派 5

3. **YOLOv8m (medium)**
   - 精度更高
   - 速度较慢
   - 如果性能允许可以使用

### 性能优化

1. **模型量化**
   ```python
   # 导出为 ONNX 格式（更快）
   model.export(format='onnx')
   ```

2. **降低输入分辨率**
   ```yaml
   # config/default.yaml
   camera:
     width: 640   # 降低分辨率
     height: 480
   ```

3. **降低检测频率**
   ```python
   # 每 N 帧检测一次
   if frame_count % 3 == 0:
       result = detector.detect(frame)
   ```

## 快速开始

### 使用 COCO 预训练模型（最简单）

1. **修改配置文件**，使用预训练模型：
   ```yaml
   detector:
     weights_path: "yolov8n.pt"  # 使用预训练模型
   ```

2. **修改 detector.py**，支持自动下载：
   ```python
   from ultralytics import YOLO
   
   # YOLO 会自动下载模型（如果不存在）
   self.model = YOLO(config.weights_path)
   ```

3. **运行程序**，模型会自动下载到 `~/.ultralytics/weights/`

### 使用专门的鱼类检测模型

1. **从 GitHub 下载模型**:
   ```bash
   cd ~/fishcar/raspi/models
   wget https://github.com/qunshansj/Fish-identification-and-detection/releases/download/v1.0/best.pt
   ```

2. **或从 Roboflow 下载**:
   - 访问 https://universe.roboflow.com
   - 搜索 "fish detection"
   - 下载 YOLOv8 格式的模型

## 测试模型

```python
from ultralytics import YOLO

# 加载模型
model = YOLO('yolov8n.pt')

# 测试图片
results = model('path/to/fish/image.jpg')

# 查看结果
results[0].show()
```

## 注意事项

1. **模型大小**: 确保树莓派有足够存储空间
2. **内存使用**: YOLOv8n 约需要 200-300MB 内存
3. **首次运行**: 预训练模型会自动下载，需要网络连接
4. **类别过滤**: COCO 模型的 "fish" 类别 ID 是 15，可以在配置中设置：
   ```yaml
   detector:
     classes: [15]  # 只检测 fish 类别
   ```

## 相关资源

- **Ultralytics 文档**: https://docs.ultralytics.com
- **YOLOv8 GitHub**: https://github.com/ultralytics/ultralytics
- **Roboflow Universe**: https://universe.roboflow.com
- **LabelImg 标注工具**: https://github.com/HumanSignal/labelImg



