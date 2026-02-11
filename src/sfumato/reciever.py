# src/sfumato/receiver.py

import numpy as np
from scipy import signal
from sfumato import settings


class FmReceiver:
    def __init__(
        self,
        fc: float = settings.CARRIER_FREQ,
        rf_fs: float = settings.RF_FS,
        audio_fs: float = settings.AUDIO_FS,
    ):
        self.fc = fc
        self.rf_fs = rf_fs
        self.audio_fs = audio_fs

        # --- フィルタ設計 ---
        # 20kHz以上の高周波ノイズをカットするLPF
        cutoff = 20_000
        self.fir_taps = signal.firwin(numtaps=101, cutoff=cutoff, fs=self.rf_fs)

        # デシメーション比
        self.dec_factor = int(self.rf_fs / self.audio_fs)

    def process(self, rf_signal: np.ndarray) -> np.ndarray:
        """
        受信したRF信号(高周波・実数)を、ベースバンドIQ信号(低周波・複素数)に変換

        DDC(Digital Down Converter)処理：
        1. 選局 (Mixing): 目的の周波数を0Hz中心に移動
        2. 帯域制限 (Filtering): 信号以外の余計なノイズを除去
        3. 間引き (Decimation): サンプリングレートをRF帯域(2.4MHz)から音声帯域(48kHz)へ変換

        Args:
            rf_signal (np.ndarray): アンテナからの入力信号 [2.4 MHz sample rate]

        Returns:
            np.ndarray: 復調(偏角計算)準備が整ったIQ信号 [48 kHz sample rate]
        """
        # 1. Mixing (2.4MHz) -> 0Hz中心へ
        baseband_iq = self._mix_to_baseband(rf_signal)

        # 2. Decimation (2.4MHz -> 48kHz) -> データ量を1/50に
        decimated_iq = self._decimate(baseband_iq)

        return decimated_iq

    def _mix_to_baseband(self, rf_signal: np.ndarray) -> np.ndarray:
        # 時間軸
        t = np.arange(len(rf_signal)) / self.rf_fs
        # LO (回転)
        lo = np.exp(-1j * 2 * np.pi * self.fc * t)
        return rf_signal * lo

    def _decimate(self, iq_signal: np.ndarray) -> np.ndarray:
        # 1. フィルタリング (LPF)
        # 畳み込み演算を行い、帯域外ノイズを除去
        filtered_iq = signal.lfilter(self.fir_taps, 1.0, iq_signal)

        # 2. 間引き (Downsampling)
        return filtered_iq[:: self.dec_factor]
