#!/usr/bin/env python3
"""
查找可用的 USB 摄像头设备
使用方法: python find_camera.py
"""
import cv2
from pathlib import Path


def main():
    print("=" * 60)
    print("查找可用的 USB 摄像头设备")
    print("=" * 60)
    
    # 方法1: 检查 /dev/video* 设备
    print("\n方法1: 检查 /dev/video* 设备文件")
    video_devices = []
    for i in range(10):  # 检查 video0 到 video9
        device_path = f"/dev/video{i}"
        path = Path(device_path)
        if path.exists():
            video_devices.append((i, device_path))
            print(f"  ✓ {device_path} (存在)")
        else:
            print(f"  ✗ {device_path} (不存在)")
    
    # 方法2: 使用 OpenCV 测试摄像头
    print("\n方法2: 使用 OpenCV 测试摄像头")
    if video_devices:
        for index, device_path in video_devices:
            print(f"\n测试设备 {device_path} (index={index}):")
            try:
                cap = cv2.VideoCapture(index)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        height, width = frame.shape[:2]
                        print(f"  ✓ 摄像头可用")
                        print(f"    分辨率: {width}x{height}")
                        print(f"    设备路径: {device_path}")
                        print(f"    在配置中使用: device_index: {index}")
                    else:
                        print(f"  ✗ 无法读取画面")
                    cap.release()
                else:
                    print(f"  ✗ 无法打开摄像头")
            except Exception as e:
                print(f"  ✗ 错误: {e}")
    else:
        print("  未找到 /dev/video* 设备")
    
    # 方法3: 使用 v4l2-ctl 工具（如果可用）
    print("\n方法3: 使用 v4l2-ctl 工具（如果已安装）")
    import subprocess
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
            camera_lines = [line for line in lines if 'camera' in line.lower() or 
                          'video' in line.lower() or 'webcam' in line.lower() or
                          'usb' in line.lower()]
            if camera_lines:
                print("  找到可能的摄像头设备：")
                for line in camera_lines:
                    print(f"    {line}")
            else:
                print("  未找到明显的摄像头设备（可能需要查看所有 USB 设备）")
                print("  所有 USB 设备：")
                for line in lines[:10]:  # 只显示前10个
                    print(f"    {line}")
        else:
            print("  无法运行 lsusb")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    if video_devices:
        print("建议使用的摄像头设备：")
        for index, device_path in video_devices:
            print(f"  设备索引: {index}")
            print(f"  设备路径: {device_path}")
            print(f"  在配置文件中设置: device_index: {index}")
        print("\n配置文件位置: ~/fishcar/raspi/config/default.yaml")
        print("配置项:")
        print("  camera:")
        print(f"    device_index: {video_devices[0][0]}")
    else:
        print("未找到摄像头设备！")
        print("\n请检查：")
        print("1. USB 摄像头是否已连接到树莓派")
        print("2. USB 线是否支持数据传输")
        print("3. 运行: ls -l /dev/video*")
        print("4. 运行: lsusb 查看 USB 设备")
        print("5. 检查系统日志: dmesg | grep -i video")
    print("=" * 60)


if __name__ == "__main__":
    main()

