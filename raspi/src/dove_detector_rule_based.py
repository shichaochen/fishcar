import datetime
import os
from pathlib import Path

import numpy as np
import sounddevice as sd
import librosa


SAMPLE_RATE = 16000  # 采样率
CHUNK_DURATION = 2.0  # 每次录音时长（秒）
CHANNELS = 1

# 简单日志文件路径（在项目根目录下的 logs 文件夹）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "dove_calls.log"


def record_chunk() -> np.ndarray:
    """录制一段音频并返回为 float32 numpy 数组。"""
    frames = int(CHUNK_DURATION * SAMPLE_RATE)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32")
    sd.wait()
    return np.squeeze(audio)


def extract_features(y: np.ndarray, sr: int):
    """
    提取用于规则判断的简单特征：
    - 总能量
    - 主频（能量最大的频率）
    - 频谱重心（spectral centroid）
    """
    if y.size == 0:
        return 0.0, 0.0, 0.0

    # 总能量
    energy = float(np.mean(y**2))

    # 计算功率谱
    S, phase = librosa.magphase(librosa.stft(y, n_fft=1024, hop_length=512))
    power_spectrum = np.mean(S**2, axis=1)

    freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
    if power_spectrum.sum() > 0:
        dominant_freq = float(freqs[np.argmax(power_spectrum)])
    else:
        dominant_freq = 0.0

    spectral_centroid = float(
        librosa.feature.spectral_centroid(S=S, sr=sr).mean()
    )

    return energy, dominant_freq, spectral_centroid


def is_dove_call(energy: float, dominant_freq: float, spectral_centroid: float) -> bool:
    """
    非精确的“斑鸠叫”规则：
    - 能量在一个正常范围内（过滤掉太小/太大的噪声）
    - 主频和谱重心落在一个典型区间（你可以根据实际录音不断调整）
    这里的数值是经验初始值，需要你根据录到的斑鸠叫声微调。
    """
    # 能量阈值（根据环境噪音调整）
    if energy < 1e-4 or energy > 0.1:
        return False

    # 经验频率范围（单位 Hz，需按实际斑鸠叫声微调）
    # 例如：主频在 300~900Hz 之间，谱重心在 400~1200Hz 之间
    if not (300.0 <= dominant_freq <= 900.0):
        return False

    if not (400.0 <= spectral_centroid <= 1200.0):
        return False

    return True


def append_log(event_time: datetime.datetime, is_dove: bool, energy: float, dominant_freq: float, spectral_centroid: float):
    """
    将每次检测结果写入日志文件。
    若检测到斑鸠叫，则在同一行标记，并方便后续统计。
    日志格式示例：
    2025-11-16 08:30:00, dove=True, energy=..., f_dom=..., f_cent=...
    """
    line = (
        f"{event_time.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"dove={'True' if is_dove else 'False'}, "
        f"energy={energy:.6e}, "
        f"f_dom={dominant_freq:.1f}, "
        f"f_cent={spectral_centroid:.1f}\n"
    )
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def run_detector():
    """
    主循环：持续录音 → 提取特征 → 规则判断 → 写日志。
    可用 Ctrl+C 停止。
    """
    print("斑鸠规则检测器启动，按 Ctrl+C 停止。")
    print(f"日志文件: {LOG_FILE}")

    try:
        while True:
            now = datetime.datetime.now()

            try:
                audio = record_chunk()
            except Exception as e:
                print(f"[录音错误] {e}")
                continue

            energy, f_dom, f_cent = extract_features(audio, SAMPLE_RATE)
            dove = is_dove_call(energy, f_dom, f_cent)

            append_log(now, dove, energy, f_dom, f_cent)

            if dove:
                print(f"[{now}] 检测到疑似斑鸠叫！f_dom={f_dom:.1f}Hz, f_cent={f_cent:.1f}Hz")
            else:
                print(f"[{now}] 非斑鸠 / 噪声，f_dom={f_dom:.1f}Hz, f_cent={f_cent:.1f}Hz")

    except KeyboardInterrupt:
        print("检测停止。")


if __name__ == "__main__":
    run_detector()







