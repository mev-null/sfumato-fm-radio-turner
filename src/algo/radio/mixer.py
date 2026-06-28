"""複素 LO ミキサ(因果・ストリーミング逐次形、roadmap 1.8)。

選局: 実 RF 信号に複素 LO を掛け、搬送波 fc を 0 Hz 中心へ移す。

    z[n] = x[n] · e^{−j·2π·fc·n / fs}

ストリーミング化の要点は「n が配列の添字ではなく通算サンプル番号」になること。
状態 = 通算サンプル番号 n₀(整数)。ブロック内では n = n₀ + (0..L−1) を使い、
処理後に n₀ += L と進める。浮動小数点の位相を足し込んで持つとドリフトするため、
整数カウンタを正とする(float64 は 2^53 まで整数を厳密に表せる)。

等価性の要件(テストで検証): 一括処理が現行 `_mix_to_baseband` の

    t = np.arange(N) / fs;  lo = np.exp(-1j * 2 * np.pi * fc * t);  z = x * lo

と bitwise 一致すること。ブロック処理では t = (n₀ + np.arange(L)) / fs とすれば
同じ浮動小数点値・同じ演算順序になり bitwise が保たれる。

HDL 対応: fc/fs = 250k/2304k = 125/1152 は有理数なので、HW では mod-1152 の
位相アキュムレータ + sin/cos テーブル(または CORDIC)になる(Phase 2.3)。
"""

import numpy as np


class BasebandMixer:
    """複素 LO ミキサ。状態 = 通算サンプル番号(整数)。"""

    def __init__(self, fc: float, fs: float):
        self.fc = fc
        self.fs = fs
        self.n = 0  # 状態: 通算サンプルカウンタ(HW では位相アキュムレータ)

    def process(self, rf: np.ndarray) -> np.ndarray:
        """実 RF ブロック(任意長、0 も可)を複素ベースバンド IQ にして返す。

        呼び出しをまたいで self.n を進めること。
        """
        raise NotImplementedError("TODO: ユーザ実装(式はモジュール docstring)")

    def reset(self) -> None:
        """通算サンプルカウンタを 0 に戻す。"""
        raise NotImplementedError("TODO: ユーザ実装")
