"""BasebandMixer の等価性テスト(roadmap 1.8、red → green の的)。

要件: ブロック処理(通算サンプル番号を状態に持つ)が、現行 `_mix_to_baseband` の
一括処理(t = arange(N)/fs)と bitwise 一致すること。
"""

import numpy as np
import pytest

from algo import settings
from algo.radio.mixer import BasebandMixer

N = 5003
SEED = 18

SPLIT_PATTERNS = {
    "len1": [1],
    "const7": [7],
    "prime997": [997],
    "mixed": [0, 1, 3, 997, 0, 64, 2048],
    "oneshot": [N],
}


def _split_sizes(n: int, pattern: list[int]) -> list[int]:
    sizes = []
    i = 0
    remaining = n
    while remaining > 0:
        s = min(pattern[i % len(pattern)], remaining)
        sizes.append(s)
        remaining -= s
        i += 1
    return sizes


def _reference(rf: np.ndarray, fc: float, fs: float) -> np.ndarray:
    """現行 FmReceiver._mix_to_baseband と同一の式・演算順序。"""
    t = np.arange(len(rf)) / fs
    lo = np.exp(-1j * 2 * np.pi * fc * t)
    return rf * lo


@pytest.fixture
def rf():
    return np.random.default_rng(SEED).standard_normal(N)


@pytest.mark.parametrize("pattern", SPLIT_PATTERNS.keys())
def test_mixer_block_vs_batch_bitwise(rf, pattern):
    fc, fs = settings.CARRIER_FREQ, settings.RF_FS
    ref = _reference(rf, fc, fs)
    mixer = BasebandMixer(fc, fs)
    outs = []
    pos = 0
    for s in _split_sizes(N, SPLIT_PATTERNS[pattern]):
        outs.append(np.asarray(mixer.process(rf[pos : pos + s])))
        pos += s
    np.testing.assert_array_equal(np.concatenate(outs), ref)


def test_mixer_counter_advances_across_calls(rf):
    fc, fs = settings.CARRIER_FREQ, settings.RF_FS
    mixer = BasebandMixer(fc, fs)
    mixer.process(rf[:1000])
    # 2 回目の呼び出しは通算番号 1000 から始まる(配列先頭からやり直さない)
    got = np.asarray(mixer.process(rf[1000:2000]))
    ref = _reference(rf, fc, fs)[1000:2000]
    np.testing.assert_array_equal(got, ref)


def test_mixer_reset_reproduces_fresh_output(rf):
    fc, fs = settings.CARRIER_FREQ, settings.RF_FS
    mixer = BasebandMixer(fc, fs)
    first = np.asarray(mixer.process(rf))
    mixer.reset()
    np.testing.assert_array_equal(np.asarray(mixer.process(rf)), first)
