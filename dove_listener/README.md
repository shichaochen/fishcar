## DoveListener

**DoveListener** 是一个运行在 Raspberry Pi 上的简易斑鸠叫声监听与统计项目。

功能特点：
- 实时从麦克风采集音频
- 使用规则（非训练模型）判断是否为斑鸠叫声
- 将每次检测结果（时间、是否斑鸠、频率特征）记录到日志文件，便于后续统计分析

### 1. 环境准备

在 Raspberry Pi 上：

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip portaudio19-dev -y

cd /path/to/DoveListener  # 切换到本项目根目录
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

确认麦克风可用（如 USB 麦克风）：

```bash
arecord -l
```

### 2. 运行监听程序

在虚拟环境中：

```bash
source venv/bin/activate
python -m src.run_listener
```

程序会持续：
- 录音（默认每段 2 秒）
- 提取简单频谱特征
- 根据规则判断是否为斑鸠叫声
- 将结果写入 `logs/dove_calls.log`

按 `Ctrl + C` 可停止监听。

### 3. 日志与统计

日志默认位于项目根目录下：

- 日志目录：`logs/`
- 日志文件：`logs/dove_calls.log`

每一行类似：

```text
2025-11-16 08:30:00, dove=True, energy=1.234567e-03, f_dom=520.0, f_cent=850.0
```

可以使用简单命令统计斑鸠叫次数：

```bash
grep "dove=True" logs/dove_calls.log | wc -l
```

或查看最近若干次记录：

```bash
grep "dove=True" logs/dove_calls.log | tail -n 20
```

### 4. 未来扩展

本项目目前使用简单规则进行检测，你可以进一步：
- 录制并整理更多斑鸠与非斑鸠音频，训练轻量级 CNN 模型
- 将检测结果上传到云端或可视化前端
- 增加 LED / 蜂鸣器等硬件反馈








