from __future__ import annotations

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
        self._status = ArduinoStatus(
            time.monotonic(), {"front": False, "rear": False, "left": False, "right": False}
        )
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
        if not vector.active:
            command = "V 0 0 0"
        else:
            vx = self._scale_component(vector.vx)
            vy = self._scale_component(vector.vy)
            omega = self._scale_component(vector.omega)
            command = f"V {vx} {vy} {omega}"
        self._write_line(command)

    def send_heartbeat(self) -> None:
        if self.config.heartbeat_interval <= 0:
            return
        self._write_line("PING")

    def read_status(self) -> ArduinoStatus:
        with self._lock:
            return self._status

    def _write_line(self, payload: str) -> None:
        if self._serial is None or not self._serial.is_open:
            logger.debug("串口未就绪，跳过发送: {}", payload)
            return
        message = payload.strip() + "\n"
        with self._lock:
            self._serial.write(message.encode("utf-8"))

    def _read_loop(self) -> None:
        assert self._serial is not None
        while self._running:
            try:
                raw = self._serial.readline()
                if not raw:
                    continue
                line = raw.decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                logger.debug("串口收到: {}", line)
                if line.startswith("STATUS"):
                    limits = self._parse_status_line(line)
                    if limits:
                        with self._lock:
                            self._status = ArduinoStatus(time.monotonic(), limits)
                elif line == "PONG":
                    with self._lock:
                        self._status = ArduinoStatus(time.monotonic(), self._status.limits)
                else:
                    # 其他提示信息仅记录日志
                    continue
            except serial.SerialException as exc:
                logger.error("串口异常: {}", exc)
                break

    @staticmethod
    def _scale_component(value: float) -> int:
        scaled = int(round(value * 100))
        return max(-127, min(127, scaled))

    @staticmethod
    def _parse_status_line(line: str) -> dict[str, bool] | None:
        parts = line.split()
        if len(parts) < 5:
            return None
        result: dict[str, bool] = {}
        for token in parts[1:]:
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            result[key] = value == "1"
        if {"front", "back", "left", "right"} <= result.keys():
            # 将 back 映射为 rear，保证兼容性
            return {
                "front": result["front"],
                "rear": result["back"],
                "left": result["left"],
                "right": result["right"],
            }
        return None

