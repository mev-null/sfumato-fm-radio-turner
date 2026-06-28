"""状態付き IIR フィルタ(転置直接 II 型、因果・ストリーミング逐次形、roadmap 1.8)。

差分方程式(転置直接 II 型、a[0]=1 に正規化済みとする):

    y[n]   = b₀·x[n] + d₁[n−1]
    d_k[n] = b_k·x[n] − a_k·y[n] + d_{k+1}[n−1]   (k = 1..N−1, d_N ≡ 0)

状態 = ベクトル d(長さ max(len(a), len(b)) − 1)。HW では各 d_k が 1 本の
レジスタに相当する。この d は scipy.signal.lfilter の `zi` と同一定義なので、
実装に `lfilter(b, a, x, zi=self.zi)` を用いてよい(= 差分方程式そのもの)。

等価性の要件(テストで検証):
- 任意のブロック分割で concat == 一括(bitwise)。
- ゼロ初期状態の一括処理が stateless な `lfilter(b, a, x)` と bitwise 一致。

適用先と注意:
- de-emphasis(1 次)、チャネル選択(6 次 Butterworth)。後者は複素 IQ を通すため
  状態 zi も複素で確保する必要がある(dtype 引数)。float の zi に複素を流すと
  例外または黙ったキャストになる。
- 6 次を単段の直接形で回す構成は固定小数点では数値的に脆い。
  固定小数点化(Phase 2.3)では SOS(2 次節カスケード)化を検討する。
"""

import numpy as np

class StreamingIir:
    """状態付き IIR(転置直接 II 型)。1 適用箇所につき 1 インスタンス。"""
    def __init__(self, b: np.ndarray, a: np.ndarray, dtype=np.float64):
        self.b = np.asarray(b)
        self.a = np.asarray(a)
        # 状態: 転置直接 II 型のレジスタ列(scipy lfilter の zi と同一定義)
        self.zi = np.zeros(max(len(self.a), len(self.b)) - 1, dtype=dtype)

    def process(self, x: np.ndarray) -> np.ndarray:
        """ブロック x(任意長、0 も可)をフィルタし、同じ長さの出力を返す。

        呼び出しをまたいで self.zi を引き継ぐこと。
        """
        raise NotImplementedError("TODO: ユーザ実装(差分方程式はモジュール docstring)")

    def reset(self) -> None:
        """係数は保持し、状態のみゼロ初期化する。"""
        raise NotImplementedError("TODO: ユーザ実装")
