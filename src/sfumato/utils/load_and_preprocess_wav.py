import os
import soundfile as sf
import numpy as np
import math
from scipy import signal


def load_and_preprocess_wav(filename: str, target_fs: int) -> np.ndarray:
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    # 1. 読み込み
    data, fs = sf.read(filename)

    # 2. ステレオ -> モノラル変換
    if data.ndim > 1:
        data = data.mean(axis=1)

    # 3. リサンプリング
    if fs != target_fs:
        gcd = math.gcd(target_fs, fs)
        up = target_fs // gcd
        down = fs // gcd
        data = signal.resample_poly(data, up, down)

    # 4. 型変換と正規化
    data = data.astype(np.float32)
    max_val = np.abs(data).max()
    if max_val > 1.0:
        data = data / max_val

    return data
