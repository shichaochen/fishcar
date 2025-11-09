# Arduino 模块

该目录包含麦克纳姆小车的 Arduino 固件及调试脚本。

## 主要功能

- 解析来自 Raspberry Pi 的 JSON 指令（`vx`, `vy`, `omega`, `active`）。
- 将速度映射为四个麦克纳姆轮 PWM 与方向信号。
- 处理四面微动开关，限制对应方向的速度。
- 定期通过串口反馈限位状态及心跳。

## 引脚规划（示例）

| 组件 | 引脚 |
| --- | --- |
| 前左电机 PWM/Dir | D3 / D2 |
| 前右电机 PWM/Dir | D5 / D4 |
| 后左电机 PWM/Dir | D6 / D7 |
| 后右电机 PWM/Dir | D9 / D8 |
| 微动开关 Front/Rear/Left/Right | A0 / A1 / A2 / A3 |
| 串口 | D0 (RX), D1 (TX) |

请根据实际驱动板调整。

## 调试步骤

1. 将 Arduino 连接至电脑，打开串口监视器。
2. 烧录 `fishcar.ino`。
3. 手动触发微动开关，确认反馈 JSON 中 `limits` 状态变化。
4. PC 端发送示例指令：
   ```
   {"vx":0.2,"vy":0.0,"omega":0.0,"active":true}
   ```
5. 电机转向与预期一致后，再与 Raspberry Pi 端联调。

