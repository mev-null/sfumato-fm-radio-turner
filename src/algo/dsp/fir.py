"""状態付き FIR フィルタ(因果・ストリーミング逐次形、roadmap 1.8)。

差分方程式:

    y[n] = Σ_{k=0}^{N-1} h[k] · x[n−k]

ブロック境界をまたぐ x[n−k] の参照が「状態」であり、HW ではタップ遅延線
(シフトレジスタ、N−1 段)に相当する。

等価性の要件(テストで検証):
- 任意のブロック分割で concat(process(x_1), ..., process(x_k)) が一括処理と
  一致する(許容差 rtol=1e-12)。bitwise を要求しないのは、scipy の FIR 経路
  (len(a)=1 の高速パス)が np.convolve による一括畳み込みで、積和の加算
  グルーピングが配列長に依存して変わるため。どんなストリーミング実装でも
  最終 bit までは揃わないことを実験で確認済み(IIR の逐次ループと違う点)。
- ゼロ初期状態で全体を 1 ブロックとして処理した場合は、現行の stateless 呼び出し
  `scipy.signal.lfilter(taps, 1.0, x)` と bitwise 一致する(同一経路を通るため)。
- 空ブロック(長さ 0)では状態を変えず空配列を返す。scipy の FIR 経路は空入力で
  例外を投げるため、実装側でガードが必要。
(実装に `lfilter(taps, 1.0, x, zi=self.zi)` を用いてよい。zi は転置直接 II 型の
内部状態で、FIR では遅延線と等価な情報を持つ。)
"""

import numpy as np
from scipy import signal

class StreamingFir:
    """状態付き FIR(タップ遅延線)。1 適用箇所につき 1 インスタンス(状態共有は不可)。"""

    def __init__(self, taps: np.ndarray):
        self.taps = np.asarray(taps)  # 係数(HW では係数 ROM 相当)
        self.zi = np.zeros(len(self.taps) - 1)  # 状態: 長さ N−1(HW のシフトレジスタ)

    def process(self, x: np.ndarray) -> np.ndarray:
        """ブロック x(任意長、0 も可)をフィルタし、同じ長さの出力を返す。

        呼び出しをまたいで self.zi を引き継ぐこと。
        """
        if len(x) <= 0:
          return np.zeros(0, dtype=self.zi.dtype)
        y, zf = signal.lfilter(self.taps, 1.0, x, zi=self.zi)
        self.zi = zf

        return y

    def reset(self) -> None:
        """係数は保持し、状態のみゼロ初期化する(受信開始直後と同一の状態)。"""
        self.zi = np.zeros(len(self.taps) - 1)
