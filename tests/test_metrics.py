"""
メトリクス層の契約テスト(red → green の的)。

ここは「メトリクスの定義が正しいか」を、答えが分かっている合成信号で確かめる
ユニットテスト。sfumato/eval/metrics.py を実装すると green になる。
（後段 1.7 で、実際の復調パイプライン出力をこれらの関数に通してゲート化する。）

コヒーレントサンプリング(整数周期)になるよう fs/N/f0 を選んでいるので、
FFT のビンが基本波・高調波にちょうど乗る。
"""

import numpy as np
import pytest

from sfumato.eval import metrics

FS = 48_000
N = 48_000  # 1 秒 → 周波数分解能 1 Hz
F0 = 1_000.0  # 1 kHz, 48000/1000=48 周期 → コヒーレント


def _t():
    return np.arange(N) / FS


def test_thd_pure_sine_is_near_zero():
    x = np.sin(2 * np.pi * F0 * _t())
    assert metrics.thd(x, FS, F0) < 1e-3


def test_thd_with_known_second_harmonic():
    # 2 次高調波を基本波の 10% 加える → THD ≈ 0.1
    t = _t()
    x = np.sin(2 * np.pi * F0 * t) + 0.1 * np.sin(2 * np.pi * 2 * F0 * t)
    assert metrics.thd(x, FS, F0) == pytest.approx(0.1, abs=0.01)


def test_sinad_pure_sine_is_high():
    x = np.sin(2 * np.pi * F0 * _t())
    assert metrics.sinad_db(x, FS, F0) > 60.0


def test_channel_separation_db_matches_power_ratio():
    # 駆動側 振幅 1.0、漏れ側 振幅 0.01 → 電力比 1e4 → 40 dB
    t = _t()
    driven = 1.0 * np.sin(2 * np.pi * F0 * t)
    leak = 0.01 * np.sin(2 * np.pi * F0 * t)
    assert metrics.channel_separation_db(driven, leak) == pytest.approx(40.0, abs=0.5)


def test_pll_lock_time_detects_settling():
    # 前半 0.1 s は誤差大、以降ゼロ → ロック時刻 = 0.1 s
    fs = 1_000.0
    error = np.concatenate([np.ones(100), np.zeros(900)])
    t_lock = metrics.pll_lock_time(error, fs, tol=0.1, hold_samples=10)
    assert t_lock == pytest.approx(0.1, abs=1e-3)
