import numpy as np
from scipy import signal

from algo import settings
from algo.dsp import filters
from algo.dsp.emphasis import EmphasisFilter
from algo.dsp.pll import PilotPLL


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
        # 38kHz 搬送波は位相補正を入れて再生(ステレオ検波の位相整合)。
        self.pll = PilotPLL(out_phase_offset=settings.STEREO_CARRIER_PHASE_RAD)

        # decimatoin ratio
        self.dec_factor = int(self.rf_fs / self.mpx_fs)

        self.emphasis = EmphasisFilter(
            fs=self.audio_fs, time_constant=settings.TIME_CONSTANT
        )

        # 音声再生用 15kHz 間引き FIR(192k→48k)。係数は固定(HW では係数 ROM 相当)。
        self.audio_dec = int(self.mpx_fs // self.audio_fs)  # 4
        self.audio_fir = filters.design_audio_decimation_fir()

        # ステレオ復調用の線形位相 FIR(main LPF / sub BPF、同長=群遅延一致)。
        self.stereo_main_lpf, self.stereo_sub_bpf = filters.design_stereo_fir()
        self.stereo_group_delay = (len(self.stereo_main_lpf) - 1) // 2  # D

    def process(self, rf_signal: np.ndarray) -> np.ndarray:
        """
        RF信号 -> ベースバンドIQ -> FM復調(MPX) -> 間引き
        Returns:
            np.ndarray: MPX信号 [192 kHz sample rate]
        """
        # 1. Mixing (2.4MHz) -> 0Hz中心のIQ信号へ
        baseband_iq = self._mix_to_baseband(rf_signal)

        # 1.5 チャネル選択 (2*fc=500kHz の像を除去してから位相を取る)
        baseband_iq = self._channel_select(baseband_iq)

        # 2. Demodulate (2.4MHz IQ -> 2.4MHz MPX)
        demodulated_mpx_high_rate = self._demodulate(baseband_iq)

        # 3. Decimation (2.4MHz MPX -> 192kHz MPX)
        mpx_signal = self._decimate(demodulated_mpx_high_rate)

        return mpx_signal

    def _mix_to_baseband(self, rf_signal: np.ndarray) -> np.ndarray:
        t = np.arange(len(rf_signal)) / self.rf_fs
        lo = np.exp(-1j * 2 * np.pi * self.fc * t)
        return rf_signal * lo

    def _channel_select(self, iq: np.ndarray) -> np.ndarray:
        """複素ミキシング後・判別器前のチャネル選択 LPF。

        実信号を複素 LO で混ぜると 2*fc(=500kHz)に像が出る。位相 (np.angle) を
        取る前にこれを除去する Butterworth LPF(settings.IF_LPF_CUTOFF_HZ /
        IF_LPF_ORDER)。側波帯(Carson ≈ 256kHz)は残し像だけ落とす。
        HW では DDC のチャネル選択フィルタに相当。
        """
        b, a = signal.butter(
            settings.IF_LPF_ORDER,
            settings.IF_LPF_CUTOFF_HZ / (self.rf_fs / 2),
            btype="low",
        )
        return signal.lfilter(b, a, iq)

    def _demodulate(self, iq_signal: np.ndarray) -> np.ndarray:
        # 1. 角度 (-π ~ +π)
        phase = np.angle(iq_signal)
        # 2. 連続化 (Unwrap)
        unwrapped_phase = np.unwrap(phase)
        # 3. 微分 (周波数 = dφ/dt)
        freq_dev = np.diff(unwrapped_phase, prepend=unwrapped_phase[0])
        return freq_dev

    def _decimate(self, signal_data: np.ndarray) -> np.ndarray:
        down_factor = int(self.rf_fs // self.mpx_fs)
        return signal.decimate(signal_data, down_factor, ftype="fir")

    def _mono_decode(self, mpx_signal: np.ndarray) -> np.ndarray:
        """MPX から main(L+R)だけを取り出すモノラル復調経路。

        ステレオ・マトリクス(サブキャリア検波)を通さず、FM 復調チェーン単体の
        THD/SINAD を測るために使う。15kHz 間引き FIR(192k→48k のポリフェーズ間引き、
        upfirdn = 出力点だけ計算する HW 忠実な構造)で帯域制限と間引きを同時に行い、
        19kHz パイロット漏れを断ってから de-emphasis する。返り値はモノラル (N,)。
        立ち上がり過渡を含む素のストリーミング出力で、定常区間の切り出しは測定側で行う。
        """
        mono = signal.upfirdn(self.audio_fir, mpx_signal, up=1, down=self.audio_dec)
        return self.emphasis.de_emphasis(mono)

    def _recover_carrier(self, mpx_signal: np.ndarray) -> np.ndarray:
        """
        MPX信号から19kHzパイロットを抽出し、38kHz搬送波を再生する
        """
        carrier_38k, _ = self.pll.process(mpx_signal)

        # 正規化 (振幅を1.0に揃える)
        if np.max(np.abs(carrier_38k)) > 0:
            carrier_38k = carrier_38k / np.max(np.abs(carrier_38k))

        return carrier_38k

    def _stereo_decode(self, mpx_signal: np.ndarray, carrier_38k: np.ndarray):
        """
        MPX信号と再生キャリア(38k)を使って、L/Rを分離する。

        位相が命なので帯域分割は線形位相 FIR(`stereo_main_lpf` / `stereo_sub_bpf`、同長)。
        main は LPF 1 段(群遅延 D)、sub は BPF→検波→LPF の 2 段(2D)なので、
        main を D 遅らせて両者の群遅延を 2D に揃える(これで L=main+sub / R=main-sub の
        打ち消しが成立)。搬送波は PLL 側で位相補正済み。
        """
        d = self.stereo_group_delay

        # --- 1. Main (L+R): 線形位相 LPF → sub と総遅延を揃えるため D 遅延 ---
        main = signal.lfilter(self.stereo_main_lpf, 1.0, mpx_signal)
        main_signal = np.concatenate([np.zeros(d), main])[: len(main)]

        # --- 2. Sub (L-R): 23k〜53k BPF → 検波(振幅補償 2.0)→ 15kHz LPF (合計 2D) ---
        sub_modulated = signal.lfilter(self.stereo_sub_bpf, 1.0, mpx_signal)
        demodulated_raw = sub_modulated * carrier_38k * 2.0
        sub_signal = signal.lfilter(self.stereo_main_lpf, 1.0, demodulated_raw)

        # --- 3. マトリックス回路 (分離) ---
        left_ch = main_signal + sub_signal
        right_ch = main_signal - sub_signal

        # --- 4. ダウンサンプリング (192k -> 48k) ---
        # 15kHz ポリフェーズ間引き
        left_out = signal.upfirdn(self.audio_fir, left_ch, up=1, down=self.audio_dec)
        right_out = signal.upfirdn(self.audio_fir, right_ch, up=1, down=self.audio_dec)

        # --- 5. De Emphasis ---
        left_final = self.emphasis.de_emphasis(left_out)
        right_final = self.emphasis.de_emphasis(right_out)

        return np.stack([left_final, right_final], axis=1)
