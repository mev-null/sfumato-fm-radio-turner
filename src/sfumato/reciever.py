import numpy as np
from scipy import signal
from sfumato import settings


class FmReceiver:
    def __init__(
        self,
        fc: float = settings.CARRIER_FREQ,
        rf_fs: float = settings.RF_FS,
        mpx_fs: float = settings.MPX_FS,
        audio_fs: float = settings.AUDIO_FS,
    ):
        self.fc = fc
        self.rf_fs = rf_fs
        self.mpx_fs = mpx_fs
        self.audio_fs = audio_fs

    def process(self, rf_signal: np.ndarray) -> np.ndarray:
        """
        RF信号 -> ベースバンドIQ -> FM復調(MPX) -> 間引き
        Returns:
            np.ndarray: MPX信号 [192 kHz sample rate]
        """
        # 1. Mixing (2.4MHz) -> 0Hz中心のIQ信号へ
        baseband_iq = self._mix_to_baseband(rf_signal)

        # 2. Demodulate (2.4MHz IQ -> 2.4MHz MPX)
        demodulated_mpx_high_rate = self._demodulate(baseband_iq)

        # 3. Decimation (2.4MHz MPX -> 192kHz MPX)
        mpx_signal = self._decimate(demodulated_mpx_high_rate)

        return mpx_signal

    def _mix_to_baseband(self, rf_signal: np.ndarray) -> np.ndarray:
        # 時間軸
        t = np.arange(len(rf_signal)) / self.rf_fs
        # LO (回転)
        lo = np.exp(-1j * 2 * np.pi * self.fc * t)
        return rf_signal * lo

    def _demodulate(self, iq_signal: np.ndarray) -> np.ndarray:
        """
        IQ信号の「角度の変化速度(周波数)」を計算する
        """
        # 1. 角度 (-π ~ +π)
        phase = np.angle(iq_signal)

        # 2. 連続化 (Unwrap)
        unwrapped_phase = np.unwrap(phase)

        # 3. 微分 (周波数 = dφ/dt)
        # diffを取ると長さが1減るので、最後に0埋めして長さを合わせる
        freq_dev = np.diff(unwrapped_phase, prepend=unwrapped_phase[0])

        return freq_dev

    def _decimate(self, signal_data: np.ndarray) -> np.ndarray:
        """
        2.4MHz -> 192kHz へのダウンサンプリング (フィルタ処理込み)
        """
        down_factor = int(self.rf_fs // self.mpx_fs)

        return signal.decimate(signal_data, down_factor, ftype="fir")

    def _recover_carrier(self, mpx_signal: np.ndarray) -> np.ndarray:
        """
        MPX信号から19kHzパイロットを抽出し、38kHz搬送波を再生する
        """
        # 1. 19kHz パイロット信号の抽出
        # Q = 中心周波数 / 帯域幅 (-3dB)
        target_freq = 19000
        quality_factor = 30.0

        # IIRピークフィルタの設計
        b, a = signal.iirpeak(target_freq, quality_factor, fs=self.mpx_fs)

        # フィルタ適用 (抽出された19kHz正弦波)
        pilot_tone = signal.lfilter(b, a, mpx_signal)

        # 2. 38kHz への逓倍 (Teigen-Doubling)
        # 2乗して2倍波を作る: sin^2(x) = (1 - cos(2x))/2
        doubled = pilot_tone**2

        # 直流成分(DC)と、元の成分などを除去するために再度フィルタを通す
        target_freq_38 = 38000
        b2, a2 = signal.iirpeak(target_freq_38, quality_factor, fs=self.mpx_fs)

        carrier_38k = signal.lfilter(b2, a2, doubled)

        if np.max(np.abs(carrier_38k)) > 0:
            carrier_38k = carrier_38k / np.max(np.abs(carrier_38k))

        return carrier_38k

    def _stereo_decode(self, mpx_signal: np.ndarray, carrier_38k: np.ndarray):
        """
        MPX信号と再生キャリア(38k)を使って、L/Rを分離する
        """
        # --- 1. Main (L+R) の抽出 ---
        # 0Hz 〜 15kHz を通すローパスフィルタ(LPF)
        # fs に対して 15k は余裕があるので、次数は5次くらいで十分綺麗に切れます
        nyquist = self.mpx_fs / 2
        cutoff_main = 15000  # 15kHz
        
        b_main, a_main = signal.butter(N=5, Wn=cutoff_main/nyquist, btype='low')
        main_signal = signal.lfilter(b_main, a_main, mpx_signal)


        # --- 2. Sub (L-R) の抽出と復調 ---
        
        # step A: 23k〜53k を取り出すバンドパスフィルタ(BPF)
        low_edge = 23000
        high_edge = 53000
        
        b_sub, a_sub = signal.butter(N=5, Wn=[low_edge/nyquist, high_edge/nyquist], btype='band')
        
        sub_modulated = signal.lfilter(b_sub, a_sub, mpx_signal)
        
        # step B: 復調 (検波)
        demodulated_raw = sub_modulated * carrier_38k * 2.0 
        # ※ "2.0" は変調で半減した振幅を戻すための係数（AM復調の定石）

        # step C: 不要な成分をカット (LPF)
        # 掛け算すると 76kHz 付近にもイメージができるので、もう一度 LPF で 15kHz 以下だけ残します
        sub_signal = signal.lfilter(b_main, a_main, demodulated_raw)


        # --- 3. マトリックス回路 (分離) ---
        left_ch = main_signal + sub_signal
        right_ch = main_signal - sub_signal


        # --- 4. ダウンサンプリング ---
        # 192kHz -> 48kHz (1/4)
        q = int(self.mpx_fs // self.audio_fs) # 4
        
        left_out = signal.decimate(left_ch, q, ftype='fir')
        right_out = signal.decimate(right_ch, q, ftype='fir')

        # (オプション) ディエンファシスをかけるならここ！
        # left_out = self.deemphasis(left_out)
        # right_out = self.deemphasis(right_out)

        return np.stack([left_out, right_out], axis=1)