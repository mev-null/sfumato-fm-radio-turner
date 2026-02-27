import numpy as np

from sfumato import settings


class PilotPLL:
    def __init__(
        self,
        fs: float = settings.MPX_FS,
        center_freq: float = settings.PILOT_FREQ,
        bandwidth: float = settings.PLL_BANDWIDTH,
    ):
        """
        Args:
            fs: サンプリング周波数 (192000)
            center_freq: ロックする目標周波数 (19000)
            bandwidth: ループ帯域幅 (Hz)。ここが「反応速度」を決める。
        """
        self.fs = fs
        self.center_freq = center_freq

        # --- 制御係数の計算 ---
        # アナログPLLの理論式からデジタル係数を導出
        zeta = settings.PLL_DAMPING

        # 自然角周波数 wn
        wn = 2 * np.pi * bandwidth

        # デジタル・ループフィルタ係数 (K1, K2)
        # alpha: 比例ゲイン
        # beta:  積分ゲイン
        self.alpha = (2 * zeta * wn) / fs
        self.beta = (wn * wn) / (fs * fs)

        # --- 内部状態の初期化 ---
        self.phase = 0.0  # 現在のNCOの位相
        self.freq_integrator = 0.0  # 積分器 (蓄積された周波数のズレ)

    def process(self, signal_in: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        n_samples = len(signal_in)

        # 出力用バッファ
        carrier_38k = np.zeros(n_samples)
        error_log = np.zeros(n_samples)  # デバッグ用

        # ループごとの基準ステップ (19kHz進む分)
        center_phase_step = 2 * np.pi * self.center_freq / self.fs

        # 高速化のためローカル変数に展開
        current_phase = self.phase
        integrator = self.freq_integrator

        for i in range(n_samples):
            sample = signal_in[i]

            # A. NCOの信号を作る (cos)
            # 現在の位相から cos を計算
            nco_cos = np.cos(current_phase)

            # B. 位相比較器 (Phase Detector)
            # 入力信号と NCO信号 を掛け算する
            error = sample * nco_cos

            # C. ループフィルタ (Loop Filter)
            # 1. 積分器を更新 (過去の蓄積 + 今回のズレ * beta)
            integrator += self.beta * error

            # 2. 制御量 u を計算 (積分器 + 今回のズレ * alpha)
            control = integrator + self.alpha * error

            # D. NCO更新 (Update Phase)
            # 次の位相 = 現在 + 基準ステップ + 制御量(u)
            current_phase += center_phase_step + control

            # ラップアラウンド処理
            if current_phase > 2 * np.pi:
                current_phase -= 2 * np.pi
            elif current_phase < 0:
                current_phase += 2 * np.pi

            # E. 出力生成 (38kHz)
            # 19kHzの位相(current_phase)を使って、2倍の周波数(38kHz)の sin を作る
            carrier_38k[i] = np.sin(2 * current_phase)

            # ログ記録
            error_log[i] = error

        self.phase = current_phase
        self.freq_integrator = integrator

        return carrier_38k, error_log
