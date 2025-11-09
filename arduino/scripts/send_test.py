#!/usr/bin/env python3
import json
import sys
import time

import serial


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: send_test.py <serial_port>")
        sys.exit(1)

    port = sys.argv[1]
    ser = serial.Serial(port, 115200, timeout=1.0)
    try:
        while True:
            payload = {"vx": 0.3, "vy": 0.0, "omega": 0.0, "active": True}
            ser.write((json.dumps(payload) + "\n").encode("utf-8"))
            line = ser.readline().decode("utf-8").strip()
            if line:
                print("收到:", line)
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()


if __name__ == "__main__":
    main()

