#!/usr/bin/env python3
import sys
import time

import serial


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: send_test.py <serial_port>")
        sys.exit(1)

    port = sys.argv[1]
    ser = serial.Serial(port, 9600, timeout=1.0)
    try:
        while True:
            ser.write(b"V 40 0 0\n")
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                print("收到:", line)
            time.sleep(0.3)
            ser.write(b"PING\n")
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                print("收到:", line)
            time.sleep(0.7)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()


if __name__ == "__main__":
    main()