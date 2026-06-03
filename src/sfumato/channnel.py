import numpy as np


def add_awgn(
    signal: np.ndarray,
    snr_db: float,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    信号に白色ガウス雑音(AWGN)を加える

    Args:
        signal: 入力信号（複素数または実数）
        snr_db: 信号対雑音比 (dB)
        rng: 乱数生成器。再現性が必要な場面(品質メトリクスのゲート等)では
            `np.random.default_rng(seed)` を渡してノイズを固定する。
            None の場合は毎回新しい乱数列(本番シミュレーション用)。

    Returns:
        noisy_signal: ノイズが付加された信号
    """
    if rng is None:
        rng = np.random.default_rng()

    sig_power = np.mean(np.abs(signal) ** 2)

    # dBをリニアな倍率に変換: SNR = Ps / Pn
    # 10^(SNR/10) = Ps / Pn  =>  Pn = Ps / 10^(SNR/10)
    noise_power = sig_power / (10 ** (snr_db / 10))

    # ノイズ生成（実数信号）
    noise_std = np.sqrt(noise_power)
    noise = rng.normal(0, noise_std, len(signal))

    return signal + noise
