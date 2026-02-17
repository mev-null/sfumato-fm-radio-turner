import numpy as np
from scipy import signal
from sfumato import settings


class EmphasisFilter:
    """
    FM放送用のプリエンファシス・ディエンファシスフィルタ (IIR)
    アナログの時定数(tau)を、双一次変換でデジタルフィルタ係数に変換して適用する。
    """

    def __init__(
        self,
        fs: float = settings.AUDIO_FS,
        time_constant: float = settings.TIME_CONSTANT,
    ):
        """
        Args:
            fs (float): サンプリング周波数 (Hz)
            time_constant (float): 時定数 (秒). Default: 50e-6
        """
        self.fs = fs
        self.tau = time_constant

        self.b_pre, self.a_pre = self._calc_coeffs(mode="pre")
        self.b_de, self.a_de = self._calc_coeffs(mode="de")

    def _calc_coeffs(self, mode: str):
        """
        デジタル・プリエンファシス/ディエンファシスの係数計算
        """
        fc = 1.0 / (2.0 * np.pi * self.tau)
        
        if mode == 'pre':
            # --- Pre-emphasis (High-Shelf Filter) ---
            
            # y[n] = x[n] + alpha * (x[n] - x[n-1])
            # alpha = tau / T = tau * fs
            # 1次微分 (High-pass) 成分を足し合わせる処理
            
            alpha = self.tau * self.fs # 例: 50e-6 * 48000 = 2.4
            
            # 係数: b0 = 1 + alpha, b1 = -alpha
            # H(z) = (1+alpha) - alpha*z^-1
            b = [1.0 + alpha, -alpha]
            a = [1.0]

            return b, a

        else:
            # --- De-emphasis (Low-Pass Filter) ---
            # 標準的な IIR LPF
            # y[n] = (1-p)*x[n] + p*y[n-1]  (p = exp(-1/(fs*tau)))
            
            dt = 1.0 / self.fs
            p = np.exp(-dt / self.tau) # 減衰係数
            
            # IIRフィルタ係数
            # H(z) = (1-p) / (1 - p*z^-1)
            b = [1.0 - p]
            a = [1.0, -p]
            
            return b, a

    def pre_emphasis(self, data: np.ndarray) -> np.ndarray:
        """
        [送信] 高域をブーストする (High-shelf)
        """
        return signal.lfilter(self.b_pre, self.a_pre, data)

    def de_emphasis(self, data: np.ndarray) -> np.ndarray:
        """
        [受信] 高域をカットしてノイズを除去する (Low-pass)
        """
        return signal.lfilter(self.b_de, self.a_de, data)
