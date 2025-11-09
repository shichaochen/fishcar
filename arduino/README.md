# Arduino 模块

该目录包含麦克纳姆小车的 Arduino 固件及调试脚本。

## 主要功能

- 解析来自 Raspberry Pi 的文本指令 `V <vx> <vy> <omega>`（范围约 -127 ~ 127）。
- 通过 I2C 与电机驱动板通信，设置四个麦克纳姆轮速度。
- 处理四面微动开关，限制危险方向并输出碰撞提示。
- 以串口输出 `STATUS front=0 back=0 left=0 right=0` 供上位机解析；支持 `PING` 心跳。

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
3. 手动触发微动开关，串口监视器应输出 `STATUS front=1` 等提示。
4. PC 端发送示例指令：
   ```
   V 30 -10 0
   ```
5. 观察 `SPEED OK` 与 `STATUS` 反馈，电机动作正确后再与 Raspberry Pi 端联调。

