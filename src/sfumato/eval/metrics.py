"""
復調品質メトリクス（純粋関数）。

★ ここは「あなたが実装する」DSP の核。下記は契約(シグネチャ・単位・符号の向き)
   だけ定義したスタブ。中身を埋めて tests/test_metrics.py を green にしていく。
   契約を変えたくなったら、テスト側も合わせて更新すること。

単位・規約の約束:
- THD は「線形比」(無次元)。純音なら ~0、歪むほど大きい。
- dB 系メトリクス(SINAD・セパレーション)は大きいほど良い。
- 時間は秒。
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
    raise NotImplementedError("実装してください: THD")


def sinad_db(signal: np.ndarray, fs: float, f0: float) -> float:
    """SINAD [dB]。基本波電力 / (雑音+歪み)電力。大きいほど良い。"""
    raise NotImplementedError("実装してください: SINAD")


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
    raise NotImplementedError("実装してください: ステレオセパレーション")


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
    raise NotImplementedError("実装してください: PLL ロック時間")
