"""状態付きポリフェーズ間引き(因果、roadmap 1.8)。

M 分の 1 間引き = 「FIR で帯域制限してから M 個に 1 個拾う」:

    y[m] = Σ_k h[k] · x[mM − k]        (= lfilter(h, 1, x)[::M] と同値)

出力は通算入力番号 n ≡ 0 (mod M) のサンプルで発火する。状態は 2 つ:

- 入力レートの遅延線(len(taps) − 1)… FIR の状態
- 通算入力位相 p = n mod M … 次に来る入力サンプルの位相。HW の mod-M カウンタに相当

位相カウンタを持つことでブロック長は任意になる(M 未満のブロックなら出力 0 サンプル)。

等価性の要件(テストで検証):
- 任意のブロック分割で concat == 一括、かつゼロ初期状態の一括処理が
  `lfilter(taps, 1.0, x)[::M]` と一致(許容差 rtol=1e-12)。
  bitwise を要求しないのは FIR(dsp/fir.py)と同じ理由(scipy の FIR 経路は
  加算グルーピングが配列長依存)。「全レートで lfilter(+zi) → 位相が合う点だけ
  拾う」実装が素直。ポリフェーズ分解 h_p[k] = h[kM+p] で乗算を出力レート化する
  形(HW の実装形)も許容差内に収まるため、どちらを選んでもよい。

現行コードとの関係:
- RF→MPX(12×)の `signal.decimate(ftype="fir")` は既定 zero_phase=True で
  filtfilt 相当の非因果処理。本クラスへの置換が 1.8 の主目的の一つ
  (係数は同一、因果化により群遅延 +len(taps)//2 入力サンプルだけ全体が遅れる)。
- MPX→audio(4×)の `signal.upfirdn` は因果だが状態を持たない。置換で出力長が
  len(x)/M ちょうどに揃う(尻尾サンプルが出なくなる)。
"""

import numpy as np


class PolyphaseDecimator:
    """状態付き M 分の 1 間引き。1 適用箇所につき 1 インスタンス。"""

    def __init__(self, taps: np.ndarray, factor: int):
        self.taps = np.asarray(taps)  # 係数(HW では係数 ROM 相当)
        self.factor = factor  # 間引き比 M
        self.delay = np.zeros(len(self.taps) - 1)  # 状態: 入力レート遅延線
        self.phase = 0  # 状態: 通算入力位相 p = n mod M(p=0 のサンプルで出力発火)

    def process(self, x: np.ndarray) -> np.ndarray:
        """ブロック x(任意長、0 も可)を処理し、発火した出力(可変長、0 も可)を返す。

        呼び出しをまたいで遅延線と位相カウンタを引き継ぐこと。
        """
        raise NotImplementedError("TODO: ユーザ実装(発火条件はモジュール docstring)")

    def reset(self) -> None:
        """係数は保持し、遅延線と位相カウンタをゼロ初期化する。"""
        raise NotImplementedError("TODO: ユーザ実装")
