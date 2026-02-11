# FM変調・送信機モデル
import numpy as np
import scipy

from sfumato import settings


class FmTransmitter:
    def __init__(
        self,
        carrier_freq: float = settings.CARRIER_FREQ,
        audio_fs: float = settings.AUDIO_FS,
        rf_fs: float = settings.RF_FS,
        max_deviation: float = settings.MAX_DEVIATION,
    ):
        """
        FM送信機を初期化

        Args:
            carrier_freq: 搬送波周波数 (Hz)
            audio_fs: 入力オーディオのサンプリングレート (Hz)
            rf_fs: シミュレーション上のRFサンプリングレート (Hz)
            max_deviation: 信号が最大振幅(1.0)の時の周波数変化量 (Hz)
        """
        self.fc = carrier_freq
        self.audio_fs = audio_fs
        self.rf_fs = rf_fs

        # kf = max_deviation / max_audio_amplitude
        # オーディオ入力を -1.0 ~ 1.0 に正規化を前提に実装
        self.kf = max_deviation  # 変調感度 kf

    def modulate(self, audio_data: np.ndarray) -> np.ndarray:
        """
        オーディオ信号を受け取り、FM変調されたRF信号を返す

        Args:
            audio_data: -1.0 〜 1.0 に正規化された音声データ配列

        Returns:
            rf_signal: FM変調された時系列データ
        """
        # 1.アップサンプリング
        upsampled_audio: np.ndarray = self._upsample(audio_data)

        # 2.時間軸の作成
        num_samples = len(upsampled_audio)
        t = np.arange(num_samples) / self.rf_fs

        # 3.位相項の計算
        phase_integral = np.cumsum(upsampled_audio) / self.rf_fs

        # 4. 変調 (変調信号の生成)
        # s(t) = cos(2πfc t + 2π kf ∫m(τ))
        theta = 2 * np.pi * self.fc * t + 2 * np.pi * self.kf * phase_integral
        rf_signal = np.cos(theta)

        return rf_signal

    def _upsample(self, data: np.ndarray) -> np.ndarray:
        """
        オーディオ信号をRFサンプリングレートに合わせて線形補間
        """
        ratio = int(self.rf_fs / self.audio_fs)

        original_len = len(data)
        target_len = int(original_len * ratio)

        return scipy.signal.resample(data, target_len)
