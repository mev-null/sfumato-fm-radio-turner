"""
ヘッドレス・決定論パイプライン(characterize 用ドライバ)。

main.py の TX→通信路→RX を、UI・実音源・グローバル乱数を排して
「同じ入力 → 同じ出力」になるよう回す層。ここは数値判断(しきい値)を
持たず、メトリクスに渡す生信号を取り出すことだけに責務を絞る。
判定は characterize.py / tests 側で行う。

決定論の担保:
- AWGN は `np.random.default_rng(seed)` を注入してノイズ列を固定する。
- 評価トーンは settings の EVAL_* 条件から生成する。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from algo import settings
from algo.radio.channel import add_awgn
from algo.radio.receiver import FmReceiver
from algo.radio.transmitter import FmTransmitter
from algo.utils.audio_source import AudioSource


@dataclass
class PipelineResult:
    """パイプライン 1 回分の出力。メトリクス関数への入力をまとめる。"""

    mono: np.ndarray  # モノラル復調 main=L+R [audio_fs]（THD/SINAD 用）
    left: np.ndarray  # ステレオ復調 L チャンネル [audio_fs]
    right: np.ndarray  # ステレオ復調 R チャンネル [audio_fs]
    pll_error: np.ndarray  # PLL 位相比較器の誤差系列 [mpx_fs]
    audio_fs: float  # L/R のサンプリング周波数 [Hz]
    mpx_fs: float  # pll_error のサンプリング周波数 [Hz]


def _steady_state(
    x: np.ndarray, n_coherent: int, fir_taps: int, decim: int
) -> np.ndarray:
    """upfirdn 出力から定常区間 n_coherent サンプルを切り出す(mono / L / R 共通)。

    線形位相 FIR の群遅延 (fir_taps-1)/2(入力レート)を出力レートに換算した分だけ
    先頭の立ち上がり過渡を捨て、そこからコヒーレント長を取る。
    """
    group_delay = (fir_taps - 1) // 2 // decim
    return x[group_delay : group_delay + n_coherent]


def run_pipeline(audio: np.ndarray, snr_db: float, seed: int) -> PipelineResult:
    """audio を TX→AWGN(seed固定)→RX に通し、L/R と PLL 誤差を返す。

    main.py の受信手順をヘッドレスに再現する。PilotPLL.process は内部状態を
    進めるため 1 回だけ呼び、その搬送波を _stereo_decode に渡す
    (_recover_carrier は併用しない。代わりに同等の正規化をここで行う)。

    Args:
        audio: 入力音声 (N,) モノラル または (N, 2) ステレオ
        snr_db: 通信路の SN比 [dB]
        seed: AWGN の乱数シード(再現性のため固定)

    Returns:
        PipelineResult: 復調 L/R と PLL 誤差系列
    """
    rng = np.random.default_rng(seed)

    tx = FmTransmitter()
    rx = FmReceiver()

    rf_signal = tx.modulate(audio)
    noisy_rf = add_awgn(rf_signal, snr_db, rng=rng)

    mpx_signal = rx.process(noisy_rf)

    # モノラル復調(main=L+R のみ)。THD/SINAD はステレオ・マトリクスを通さない
    # この経路で測り、FM 復調チェーン単体の品質を見る。
    mono = rx._mono_decode(mpx_signal)

    # 搬送波再生と誤差ログの回収(誤差は _recover_carrier では捨てられている)
    carrier_38k, pll_error = rx.pll.process(mpx_signal)

    # _recover_carrier と同じ正規化(振幅を 1.0 に揃える)
    peak = np.max(np.abs(carrier_38k))
    if peak > 0:
        carrier_38k = carrier_38k / peak

    lr = rx._stereo_decode(mpx_signal, carrier_38k)

    # 測定窓の切り出し(受信機は素のストリーミング出力を返すので、定常区間の抽出は
    # 測定側の責務)。mono / L / R とも FIR の立ち上がり過渡を群遅延ぶん捨て、入力と同じ
    # 長さ=コヒーレント長(評価トーンが整数周期に乗る長さ)の定常区間だけをメトリクスに渡す。
    n = len(audio)
    taps, dec = len(rx.audio_fir), rx.audio_dec
    return PipelineResult(
        mono=_steady_state(mono, n, taps, dec),
        left=_steady_state(lr[:, 0], n, taps, dec),
        right=_steady_state(lr[:, 1], n, taps, dec),
        pll_error=pll_error,
        audio_fs=rx.audio_fs,
        mpx_fs=rx.mpx_fs,
    )


def single_tone(
    freq: float = settings.EVAL_TONE_FREQ,
    duration: float = settings.EVAL_DURATION_S,
) -> np.ndarray:
    """THD/SINAD 用の単一トーン (N,) を生成する。"""
    return AudioSource(sample_rate=settings.AUDIO_FS).sine_tone(freq, duration)


def one_channel_driven(
    freq: float = settings.EVAL_TONE_FREQ,
    duration: float = settings.EVAL_DURATION_S,
) -> np.ndarray:
    """セパレーション用に L だけ駆動・R 無音のステレオ (N, 2) を生成する。"""
    return AudioSource(sample_rate=settings.AUDIO_FS).stereo_sine_tone(
        freq_l=freq, freq_r=0.0, duration=duration
    )
