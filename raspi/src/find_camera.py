#!/usr/bin/env python3
"""
查找可用的 USB 摄像头设备
使用方法: 
  - python find_camera.py (从 raspi/src 目录)
  - python -m src.find_camera (从 raspi 目录)
  - python -m raspi.src.find_camera (从 fishcar 目录)
"""
import sys
from pathlib import Path

# 添加项目路径以便导入
_script_dir = Path(__file__).parent
_project_dir = _script_dir.parent.parent
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))

import cv2
import subprocess


def main():
    print("=" * 60)
    print("查找可用的 USB 摄像头设备")
    print("=" * 60)
    
    # 方法1: 检查 /dev/video* 设备
    print("\n方法1: 检查 /dev/video* 设备文件")
    video_devices = []
    for i in range(40):  # 检查 video0 到 video39
        device_path = f"/dev/video{i}"
        path = Path(device_path)
        if path.exists():
            video_devices.append((i, device_path))
    
    print(f"找到 {len(video_devices)} 个视频设备")
    
    # 方法2: 使用 OpenCV 测试摄像头
    print("\n方法2: 使用 OpenCV 测试摄像头（通常 USB 摄像头是 video0 或 video1）")
    working_cameras = []
    
    # 优先测试常见的设备索引
    test_indices = [0, 1] + [i for i in range(2, min(10, len(video_devices)))]
    
    for index in test_indices:
        device_path = f"/dev/video{index}"
        if not Path(device_path).exists():
            continue
            
        print(f"\n测试设备 {device_path} (index={index}):")
        try:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # 尝试读取几帧（有些设备需要初始化时间）
                ret = False
                for _ in range(5):
                    ret, frame = cap.read()
                    if ret:
                        break
                    import time
                    time.sleep(0.1)
                
                if ret:
                    height, width = frame.shape[:2]
                    print(f"  ✓ 摄像头可用！")
                    print(f"    分辨率: {width}x{height}")
                    print(f"    设备路径: {device_path}")
                    print(f"    在配置中使用: device_index: {index}")
                    working_cameras.append((index, device_path, width, height))
                else:
                    print(f"  ✗ 无法读取画面（可能是元数据设备，不是实际摄像头）")
                cap.release()
            else:
                print(f"  ✗ 无法打开摄像头")
        except Exception as e:
            print(f"  ✗ 错误: {e}")
    
    # 方法3: 使用 v4l2-ctl 工具（如果可用）
    print("\n方法3: 使用 v4l2-ctl 工具查看设备信息")
    try:
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("  v4l2-ctl 未安装，运行: sudo apt install v4l-utils")
    except FileNotFoundError:
        print("  v4l2-ctl 未安装，运行: sudo apt install v4l-utils")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 方法4: 查看 USB 设备
    print("\n方法4: 查看 USB 设备")
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            camera_lines = [line for line in lines if any(keyword in line.lower() 
                          for keyword in ['camera', 'video', 'webcam', 'usb'])]
            if camera_lines:
                print("  找到可能的摄像头设备：")
                for line in camera_lines:
                    print(f"    {line}")
            else:
                print("  所有 USB 设备：")
                for line in lines[:15]:  # 显示前15个
                    print(f"    {line}")
        else:
            print("  无法运行 lsusb")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    if working_cameras:
        print("✓ 找到可用的摄像头设备：")
        for index, device_path, width, height in working_cameras:
            print(f"\n  设备索引: {index}")
            print(f"  设备路径: {device_path}")
            print(f"  分辨率: {width}x{height}")
        
        print("\n建议配置（使用第一个可用的摄像头）：")
        print("  在 ~/fishcar/raspi/config/default.yaml 中设置：")
        print("  camera:")
        print(f"    device_index: {working_cameras[0][0]}")
        print(f"    width: {working_cameras[0][2]}")
        print(f"    height: {working_cameras[0][3]}")
    else:
        print("✗ 未找到可用的摄像头设备！")
        print("\n请检查：")
        print("1. USB 摄像头是否已连接到树莓派")
        print("2. USB 线是否支持数据传输")
        print("3. 运行: v4l2-ctl --list-devices")
        print("4. 检查系统日志: dmesg | grep -i video")
        print("5. 检查权限: groups | grep video")
    print("=" * 60)


if __name__ == "__main__":
    main()

