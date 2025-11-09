from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass

import serial
from loguru import logger

from .config_loader import SerialConfig
from .motion_mapping import MotionVector


@dataclass
class ArduinoStatus:
    timestamp: float
    limits: dict[str, bool]


class SerialBridge:
    def __init__(self, config: SerialConfig) -> None:
        self.config = config
        self._serial: serial.Serial | None = None
        self._lock = threading.Lock()
        self._status = ArduinoStatus(time.monotonic(), {"front": False, "rear": False, "left": False, "right": False})
        self._reader_thread: threading.Thread | None = None
        self._running = False

    def open(self) -> None:
        logger.info("打开串口 {} @ {}", self.config.port, self.config.baudrate)
        self._serial = serial.Serial(
            self.config.port,
            self.config.baudrate,
            timeout=self.config.timeout,
        )
        self._running = True
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def stop(self) -> None:
        self._running = False
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=1.0)
        if self._serial:
            logger.info("关闭串口")
            self._serial.close()
            self._serial = None

    def send_vector(self, vector: MotionVector) -> None:
        payload = {
            "vx": round(vector.vx, 3),
            "vy": round(vector.vy, 3),
            "omega": round(vector.omega, 3),
            "active": vector.active,
        }
        self._write(payload)

    def send_heartbeat(self) -> None:
        self._write({"type": "heartbeat"})

    def read_status(self) -> ArduinoStatus:
        with self._lock:
            return self._status

    def _write(self, payload: dict) -> None:
        if self._serial is None or not self._serial.is_open:
            logger.debug("串口未就绪，跳过发送")
            return
        message = json.dumps(payload) + "\n"
        with self._lock:
            self._serial.write(message.encode("utf-8"))

    def _read_loop(self) -> None:
        assert self._serial is not None
        while self._running:
            try:
                raw = self._serial.readline()
                if not raw:
                    continue
                data = json.loads(raw.decode("utf-8").strip())
                if "limits" in data:
                    with self._lock:
                        self._status = ArduinoStatus(time.monotonic(), data["limits"])
            except json.JSONDecodeError:
                logger.warning("解析串口数据失败: {}", raw)
            except serial.SerialException as exc:
                logger.error("串口异常: {}", exc)
                break

