"""
復調品質メトリクス（純粋関数）

単位・規約の約束:
- THD は「線形比」(無次元)。純音なら ~0、歪むほど大きい。
- dB 系メトリクス(SINAD・セパレーション)は大きいほど良い。
- 時間は秒。

np.fft.rfft        # 実数信号 → 片側スペクトル
np.fft.rfftfreq    # 各ビンの周波数 [Hz]
np.abs / **2       # 振幅 → 電力
np.sum, np.sqrt, np.log10
"""

from __future__ import annotations

import numpy as np


def thd(signal: np.ndarray, fs: float, f0: float, n_harmonics: int = 5) -> float:
    """全高調波歪み (Total Harmonic Distortion)。

    基本波 f0 に対する 2..n_harmonics 次高調波の RMS 比を線形値で返す。
        THD = sqrt(Σ P_k(k>=2)) / sqrt(P_1)

    Args:
        signal: 復調された実数音声(単一トーン入力に対する応答)
        fs: サンプリング周波数 [Hz]
        f0: 基本波周波数 [Hz]
        n_harmonics: 評価する最高次数

    Returns:
        THD(線形比、>= 0)。純音入力なら ~0。
    """
    X = np.fft.rfft(signal)
    delta_f = fs / len(signal)
    power = np.abs(X) ** 2

    def bin_at(freq: float) -> int:
        return int(np.round(freq / delta_f))

    p1 = power[bin_at(f0)]
    p_harm = sum(power[bin_at(k * f0)] for k in range(2, n_harmonics + 1))

    return np.sqrt(p_harm / p1)


def sinad_db(signal: np.ndarray, fs: float, f0: float) -> float:
    """SINAD [dB]。基本波電力 / (雑音+歪み)電力。大きいほど良い。"""
    X = np.fft.rfft(signal)
    power = np.abs(X) ** 2

    delta_f = fs / len(signal)
    bin_f0 = int(np.round(f0 / delta_f))

    p_signal = power[bin_f0]
    p_noise = power.sum() - p_signal

    return float(10 * np.log10(p_signal / p_noise))


def channel_separation_db(out_driven: np.ndarray, out_silent: np.ndarray) -> float:
    """ステレオ・セパレーション [dB]。

    片チャンネルだけにトーンを入れて受信したときの、
    駆動側 ch 出力電力 / 無音側 ch への漏れ電力 を dB で返す。
        separation = 10*log10( P(out_driven) / P(out_silent) )
    大きいほど分離が良い(漏れが少ない)。

    Args:
        out_driven: 駆動した側の出力 ch(例: L にトーン → L 出力)
        out_silent: 無音にした側の出力 ch(例: R 出力 = 漏れ)
    """
    p_driven = np.sum(out_driven**2)
    p_silent = np.sum(out_silent**2)
    return float(10 * np.log10(p_driven / p_silent))


def pll_lock_time(
    error_log: np.ndarray,
    fs: float,
    tol: float,
    hold_samples: int,
) -> float:
    """PLL ロック時間 [秒]。

    位相比較器の誤差 |error| が tol 未満になり、その後 hold_samples 連続で
    tol 未満を維持し続けた最初の時刻を返す。最後までロックしなければ inf。

    Args:
        error_log: PilotPLL.process が返す誤差系列
        fs: サンプリング周波数 [Hz]
        tol: ロック判定の閾値(|error| の上限)
        hold_samples: ロック継続とみなす連続サンプル数
    """
    is_ok = (np.abs(error_log) < tol).astype(int)

    idx_window = len(is_ok) - hold_samples + 1

    if idx_window < 0:
        return np.inf

    current_sum = np.sum(is_ok[0:hold_samples])
    for i in range(idx_window):
        if current_sum == hold_samples:
            return i / fs
        if i + hold_samples < len(is_ok):  # 次の窓があるときだけスライド
            current_sum += is_ok[i + hold_samples] - is_ok[i]
    return np.inf
