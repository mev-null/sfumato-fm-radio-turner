"""IqDiscriminator の等価性テスト(roadmap 1.8、red → green の的)。

要件:
- ブロック分割 vs 一括は bitwise 一致(状態 = z_prev 1 サンプル)。
- 現行 unwrap+diff 形(`_demodulate`)とは |Δφ| < π の範囲で数学的同値。
  経路が違うため一致は浮動小数点許容差(atol=1e-9)で確認する。
- 初回出力 y[0] = 0(現行の prepend 挙動と一致)。
"""

import numpy as np
import pytest

from algo.radio.discriminator import IqDiscriminator

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


def _synthetic_iq() -> np.ndarray:
    """Δφ を ±0.95π まで振り、振幅変動も乗せた合成 FM IQ。

    位相増分が ±π 近くまで暴れても(= 生の角度は頻繁に ±π をまたぐ)、
    |Δφ| < π なら差分形は unwrap 不要で復調できることを踏ませる。
    振幅変動は「偏角だけ見ている(振幅非依存)」ことの確認。
    """
    n = np.arange(N)
    dphi = 0.95 * np.pi * np.sin(2 * np.pi * 3 * n / N)
    amp = 1.0 + 0.5 * np.sin(2 * np.pi * 7 * n / N)
    return amp * np.exp(1j * np.cumsum(dphi))


def _unwrap_reference(z: np.ndarray) -> np.ndarray:
    """現行 FmReceiver._demodulate と同一の式。"""
    phase = np.angle(z)
    unwrapped = np.unwrap(phase)
    return np.diff(unwrapped, prepend=unwrapped[0])


@pytest.mark.parametrize("pattern", SPLIT_PATTERNS.keys())
def test_discriminator_block_vs_batch_bitwise(pattern):
    z = _synthetic_iq()
    ref = IqDiscriminator().process(z)
    disc = IqDiscriminator()
    outs = []
    pos = 0
    for s in _split_sizes(N, SPLIT_PATTERNS[pattern]):
        outs.append(np.asarray(disc.process(z[pos : pos + s])))
        pos += s
    np.testing.assert_array_equal(np.concatenate(outs), np.asarray(ref))


def test_discriminator_matches_unwrap_form():
    z = _synthetic_iq()
    got = np.asarray(IqDiscriminator().process(z))
    np.testing.assert_allclose(got, _unwrap_reference(z), atol=1e-9)


def test_first_output_is_zero():
    z = _synthetic_iq()
    got = np.asarray(IqDiscriminator().process(z))
    assert got[0] == 0.0


def test_constant_deviation_near_pi():
    # 一定の Δφ = 0.95π。生の角度は約 2 サンプル毎に ±π をまたぐが、
    # 差分形は各サンプルで主値 0.95π を直接返す
    dphi = 0.95 * np.pi
    z = np.exp(1j * np.cumsum(np.full(N, dphi)))
    got = np.asarray(IqDiscriminator().process(z))
    assert got[0] == 0.0
    np.testing.assert_allclose(got[1:], dphi, atol=1e-9)


def test_reset_reproduces_fresh_state():
    z = _synthetic_iq()
    disc = IqDiscriminator()
    first = np.asarray(disc.process(z))
    disc.reset()
    np.testing.assert_array_equal(np.asarray(disc.process(z)), first)
