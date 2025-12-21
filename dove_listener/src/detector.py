import datetime
from pathlib import Path

import librosa
import numpy as np
import sounddevice as sd


SAMPLE_RATE = 16000  # Hz
CHUNK_DURATION = 2.0  # seconds
CHANNELS = 1

# Project root: .../dove_listener
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "dove_calls.log"

LOG_DIR.mkdir(exist_ok=True)


def record_chunk() -> np.ndarray:
    """Record a short audio chunk and return as 1D float32 numpy array."""
    frames = int(CHUNK_DURATION * SAMPLE_RATE)
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32")
    sd.wait()
    return np.squeeze(audio)


def extract_features(y: np.ndarray, sr: int):
    """
    Extract simple features for rule-based detection:
    - energy
    - dominant frequency
    - spectral centroid
    """
    if y.size == 0:
        return 0.0, 0.0, 0.0

    energy = float(np.mean(y**2))

    S, _ = librosa.magphase(librosa.stft(y, n_fft=1024, hop_length=512))
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
    Heuristic rule for dove call detection.

    These ranges are initial guesses and should be adjusted with real recordings:
    - energy in a moderate range (filter out very low or very loud noise)
    - dominant frequency between 300–900 Hz
    - spectral centroid between 400–1200 Hz
    """
    if energy < 1e-4 or energy > 0.1:
        return False

    if not (300.0 <= dominant_freq <= 900.0):
        return False

    if not (400.0 <= spectral_centroid <= 1200.0):
        return False

    return True


def append_log(
    event_time: datetime.datetime,
    is_dove: bool,
    energy: float,
    dominant_freq: float,
    spectral_centroid: float,
):
    """Append one detection result to the log file."""
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
    Main loop: continuously record → extract features → rule-based decision → log.
    """
    print("DoveListener: rule-based dove call detector started. Press Ctrl+C to stop.")
    print(f"Log file: {LOG_FILE}")

    try:
        while True:
            now = datetime.datetime.now()
            try:
                audio = record_chunk()
            except Exception as e:
                print(f"[Recording error] {e}")
                continue

            energy, f_dom, f_cent = extract_features(audio, SAMPLE_RATE)
            dove = is_dove_call(energy, f_dom, f_cent)

            append_log(now, dove, energy, f_dom, f_cent)

            if dove:
                print(
                    f"[{now}] Dove-like call detected! "
                    f"f_dom={f_dom:.1f} Hz, f_cent={f_cent:.1f} Hz"
                )
            else:
                print(
                    f"[{now}] Non-dove / noise. "
                    f"f_dom={f_dom:.1f} Hz, f_cent={f_cent:.1f} Hz"
                )
    except KeyboardInterrupt:
        print("DoveListener stopped.")


__all__ = [
    "record_chunk",
    "extract_features",
    "is_dove_call",
    "append_log",
    "run_detector",
]








