"""信号処理フィルタ部品 (Filter, EQ, Comp)。"""

import numpy as np
from scipy import signal

from algo import settings


def design_audio_decimation_fir() -> np.ndarray:
    """15kHz 帯域制限 + 192k→48k 間引きを兼ねる線形位相 FIR の係数 h を返す。

    仕様は settings: 通過端 AUDIO_BAND_HZ(15k)/ 阻止端 AUDIO_LPF_STOP_HZ(18k)/
    阻止量 AUDIO_LPF_STOP_ATTEN_DB(60dB)。等リプル設計(remez / Parks-McClellan)で
    阻止帯を 10 倍重みづけし、19kHz パイロットを沈める。
    係数は固定(HW では係数 ROM 相当)なので設計はここに閉じ、適用(ポリフェーズ間引き
    upfirdn(h, x, up=1, down=4))は受信機側で行う。
    """
    bands = [0, settings.AUDIO_BAND_HZ, settings.AUDIO_LPF_STOP_HZ, settings.MPX_FS / 2]
    desired = [1, 0]
    weights = [1, 10]

    # タップ数の目安: Kaiser 式 N ≈ (A − 8) / (2.285 · 2π · Δf/fs)
    # (Δf=4kHz, fs=192kHz, A=60dB → ≈175)を等リプル設計に流用。
    numtaps = 175
    return signal.remez(numtaps, bands, desired, weight=weights, fs=settings.MPX_FS)
