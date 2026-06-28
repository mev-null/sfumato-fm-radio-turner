"""純遅延線(因果、roadmap 1.8)。群遅延整合用。

    y[n] = x[n − D]        (n < D では x = 0、つまりゼロ初期状態)

状態 = 直近 D 入力サンプルの FIFO(HW では D 段シフトレジスタ / BRAM)。

現行コードとの関係: ステレオ復調の main 経路で行っている
`np.concatenate([np.zeros(D), x])[:len(x)]`(zeros 前置)は本クラスの一括処理と
同値であり、bitwise 一致が要件(テストで検証)。
"""

import numpy as np


class DelayLine:
    """D サンプルの純遅延。1 適用箇所につき 1 インスタンス。"""

    def __init__(self, delay: int):
        self.delay = delay
        self.buf = np.zeros(delay)  # 状態: 直近 D 入力の FIFO

    def process(self, x: np.ndarray) -> np.ndarray:
        """ブロック x(任意長、0 も可)を D サンプル遅らせ、同じ長さの出力を返す。"""
        ext = np.concatenate([self.buf, x])
        L = len(x)
        self.buf = ext[L:]
        return ext[:L]

    def reset(self) -> None:
        """FIFO をゼロ初期化する。"""
        self.buf = np.zeros(self.delay)
