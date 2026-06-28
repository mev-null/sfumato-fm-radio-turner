"""I/Q 差分形 FM 判別器(因果・ストリーミング逐次形、roadmap 1.8)。

FM 復調 = 瞬時周波数の抽出 = 位相増分 Δφ[n] = φ[n] − φ[n−1] の抽出。
複素共役積を取ると絶対位相が消え、位相増分だけが偏角に残る:

    d[n] = z[n] · conj(z[n−1]) = |z[n]||z[n−1]| · e^{jΔφ[n]}
    y[n] = arg(d[n])
         = atan2( Q[n]·I[n−1] − I[n]·Q[n−1],  I[n]·I[n−1] + Q[n]·Q[n−1] )

atan2 の値域 (−π, π] がそのまま Δφ の主値であり、|Δφ| < π である限り
unwrap+diff(現行 `_demodulate`)と数学的に同値。本系では瞬時周波数の上限
(±75 kHz 偏移 ≪ fs/2 = 1.152 MHz)から Δφ_max = 2π·f/fs ≪ π が保証される
ため、系列全体の累積補正(np.unwrap)が不要になる。累積位相を持たないので
値が無限成長せず、固定小数点(Phase 2.3)に乗る。

状態と初期化:
- 状態 = z_prev 1 サンプルのみ(HW ではレジスタ 2 語: I, Q)。
- 初回呼び出しでは z_prev を入力の先頭サンプルで種付けする。これで
  y[0] = arg(z[0]·conj(z[0])) = 0 となり、現行の
  `np.diff(unwrapped, prepend=unwrapped[0])`(先頭出力 0)と一致する。

等価性(テストで検証):
- ブロック分割 vs 一括は bitwise 一致。
- unwrap 形との一致は経路が違うため浮動小数点許容差(atol ≈ 1e-9)。

HDL 対応: atan2 は Phase 2.3 で CORDIC(vectoring mode)に落とす。近似形
y ≈ Im(d)/|z|²(クロスプロダクト判別器)は atan 不要だが振幅依存が残るため、
参照モデルは厳密 atan2 を正とする。
"""

import numpy as np


class IqDiscriminator:
    """I/Q 差分形 FM 判別器。状態 = 直前の複素サンプル 1 語。"""

    def __init__(self):
        self.z_prev: complex | None = (
            None  # None = 未初期化(初回に先頭サンプルで種付け)
        )

    def process(self, iq: np.ndarray) -> np.ndarray:
        """複素 IQ ブロック(任意長、0 も可)から周波数偏移(実数、同じ長さ)を返す。

        呼び出しをまたいで self.z_prev を引き継ぐこと。
        """
        raise NotImplementedError("TODO: ユーザ実装(式はモジュール docstring)")

    def reset(self) -> None:
        """状態を未初期化(None)に戻す。"""
        raise NotImplementedError("TODO: ユーザ実装")
