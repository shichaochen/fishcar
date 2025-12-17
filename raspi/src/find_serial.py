#!/usr/bin/env python3
"""
查找可用的串口设备
使用方法: 
  - python find_serial.py (从 raspi/src 目录)
  - python -m src.find_serial (从 raspi 目录)
  - python -m raspi.src.find_serial (从 fishcar 目录)
"""
import sys
from pathlib import Path

# 添加项目路径以便导入
_script_dir = Path(__file__).parent
_project_dir = _script_dir.parent.parent
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))

import serial.tools.list_ports
from pathlib import Path


def main():
    print("=" * 60)
    print("查找可用的串口设备")
    print("=" * 60)
    
    # 方法1: 使用 pyserial 的 list_ports
    print("\n方法1: 使用 pyserial 检测")
    ports = serial.tools.list_ports.comports()
    if ports:
        print("找到以下串口设备：")
        for port in ports:
            print(f"  设备: {port.device}")
            print(f"  描述: {port.description}")
            print(f"  硬件ID: {port.hwid}")
            print()
    else:
        print("  未找到串口设备")
    
    # 方法2: 检查常见的串口设备路径
    print("\n方法2: 检查常见串口设备路径")
    common_ports = [
        "/dev/ttyACM0",
        "/dev/ttyACM1",
        "/dev/ttyUSB0",
        "/dev/ttyUSB1",
        "/dev/ttyAMA0",  # Raspberry Pi GPIO 串口
    ]
    
    found_ports = []
    for port_path in common_ports:
        path = Path(port_path)
        if path.exists():
            found_ports.append(port_path)
            # 检查权限
            readable = path.is_char_device()
            print(f"  ✓ {port_path} (存在)")
            if not readable:
                print(f"    警告: 可能没有读取权限")
        else:
            print(f"  ✗ {port_path} (不存在)")
    
    # 总结
    print("\n" + "=" * 60)
    if found_ports:
        print("建议使用的串口设备：")
        for port in found_ports:
            print(f"  {port}")
        print("\n请在配置文件中设置：")
        print(f"  serial:")
        print(f"    port: \"{found_ports[0]}\"")
    else:
        print("未找到串口设备！")
        print("\n请检查：")
        print("1. Arduino 是否已通过 USB 连接到树莓派")
        print("2. 运行: ls -l /dev/ttyACM* /dev/ttyUSB*")
        print("3. 检查 USB 线是否支持数据传输（不只是充电）")
        print("4. 检查 Arduino 是否已上电")
    print("=" * 60)


if __name__ == "__main__":
    main()

