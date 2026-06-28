"""dsp ストリーミング・プリミティブの等価性テスト(roadmap 1.8、red → green の的)。

不変条件: 任意のブロック分割 {x_1, ..., x_k} に対し

    concat(f(x_1), ..., f(x_k)) == f(x)

一致の強さは経路で異なる(実験で確認済み):
- IIR(len(a) ≥ 2、scipy の C 逐次ループ): bitwise 一致。サンプル毎の漸化式が
  同一演算なので、ブロック分割しても 1 bit も変わらない。
- FIR / 間引き(len(a) = 1 の高速パス): 許容差 rtol=1e-12。scipy は np.convolve
  で一括畳み込みし、積和の加算グルーピングが配列長依存のため、どんな
  ストリーミング実装でも最終 bit は揃わない(最大相対誤差の実測 ~3e-13)。
- 純遅延(コピーのみ): bitwise 一致。

品質 baseline への影響は FIR の最終 bit の揺れのみで、回帰ゲートの許容 2% に
対して 10 桁以上小さく、再 characterize は不要。
"""

import numpy as np
import pytest
from scipy import signal

from algo import settings
from algo.dsp import filters
from algo.dsp.decimator import PolyphaseDecimator
from algo.dsp.delay import DelayLine
from algo.dsp.emphasis import EmphasisFilter
from algo.dsp.fir import StreamingFir
from algo.dsp.iir import StreamingIir

# 12 でも 4 でも割り切れない長さ(間引きの端数処理を必ず踏ませる)
N = 5003
SEED = 18

# ブロック分割パターン(サイクルして N を消費する)。空ブロック(長さ 0)も含む。
SPLIT_PATTERNS = {
    "len1": [1],
    "const7": [7],
    "prime997": [997],
    "mixed": [0, 1, 3, 997, 0, 64, 2048],
    "oneshot": [N],
}


def _split_sizes(n: int, pattern: list[int]) -> list[int]:
    """pattern をサイクルしながら合計 n になるブロック長リストを作る。"""
    sizes = []
    i = 0
    remaining = n
    while remaining > 0:
        s = min(pattern[i % len(pattern)], remaining)
        sizes.append(s)
        remaining -= s
        i += 1
    return sizes


def run_blocked(obj, x: np.ndarray, sizes: list[int]) -> np.ndarray:
    """x を sizes の長さで順に process へ渡し、出力を連結して返す。"""
    outs = []
    pos = 0
    for s in sizes:
        outs.append(np.asarray(obj.process(x[pos : pos + s])))
        pos += s
    assert pos == len(x)
    return np.concatenate(outs) if outs else np.zeros(0)


@pytest.fixture
def rng():
    return np.random.default_rng(SEED)


@pytest.fixture(params=SPLIT_PATTERNS.keys())
def sizes(request):
    return _split_sizes(N, SPLIT_PATTERNS[request.param])


# ---------------------------------------------------------------- FIR


def test_fir_block_vs_batch(rng, sizes):
    taps = filters.design_audio_decimation_fir()  # 実係数(175 タップ)で検証
    x = rng.standard_normal(N)
    ref = signal.lfilter(taps, 1.0, x)  # 現行の stateless 適用と同じ
    got = run_blocked(StreamingFir(taps), x, sizes)
    # FIR は加算グルーピングが配列長依存のため bitwise 不可(モジュール docstring)
    np.testing.assert_allclose(got, ref, rtol=1e-12, atol=1e-13)


def test_fir_reset_reproduces_fresh_state(rng):
    taps = rng.standard_normal(33)
    x = rng.standard_normal(512)
    f = StreamingFir(taps)
    first = f.process(x)
    f.reset()
    np.testing.assert_array_equal(f.process(x), first)


# ---------------------------------------------------------------- IIR


def test_iir_real_block_vs_batch_bitwise(rng, sizes):
    # de-emphasis(1 次 IIR)の実係数で検証
    em = EmphasisFilter()
    x = rng.standard_normal(N)
    ref = signal.lfilter(em.b_de, em.a_de, x)
    got = run_blocked(StreamingIir(em.b_de, em.a_de), x, sizes)
    np.testing.assert_array_equal(got, ref)


def test_iir_complex_block_vs_batch_bitwise(rng, sizes):
    # チャネル選択(6 次 Butterworth)を複素 IQ に適用するケース。zi も複素が必要
    b, a = signal.butter(
        settings.IF_LPF_ORDER,
        settings.IF_LPF_CUTOFF_HZ / (settings.RF_FS / 2),
        btype="low",
    )
    x = rng.standard_normal(N) + 1j * rng.standard_normal(N)
    ref = signal.lfilter(b, a, x)
    got = run_blocked(StreamingIir(b, a, dtype=complex), x, sizes)
    np.testing.assert_array_equal(got, ref)


def test_iir_reset_reproduces_fresh_state(rng):
    em = EmphasisFilter()
    x = rng.standard_normal(512)
    f = StreamingIir(em.b_de, em.a_de)
    first = f.process(x)
    f.reset()
    np.testing.assert_array_equal(f.process(x), first)


# ---------------------------------------------------------------- 間引き


@pytest.mark.parametrize(
    "factor,taps_fn",
    [
        # RF→MPX 12×: scipy.signal.decimate(ftype="fir") の内部設計と同一係数
        (12, lambda: signal.firwin(20 * 12 + 1, 1.0 / 12, window="hamming")),
        # MPX→audio 4×: 既存の 15kHz 間引き FIR
        (4, filters.design_audio_decimation_fir),
    ],
    ids=["rf12", "audio4"],
)
def test_decimator_block_vs_batch(rng, sizes, factor, taps_fn):
    taps = taps_fn()
    x = rng.standard_normal(N)
    # 因果な間引きの定義: 全レートで畳み込み → 通算番号 ≡ 0 (mod M) を拾う
    ref = signal.lfilter(taps, 1.0, x)[::factor]
    got = run_blocked(PolyphaseDecimator(taps, factor), x, sizes)
    # FIR 経路のため bitwise 不可(モジュール docstring)
    np.testing.assert_allclose(got, ref, rtol=1e-12, atol=1e-13)


def test_decimator_short_block_emits_nothing(rng):
    # M 未満のブロックでも状態は進み、後続と合わせて一括と一致する
    taps = filters.design_audio_decimation_fir()
    x = rng.standard_normal(11)
    d = PolyphaseDecimator(taps, 4)
    out1 = d.process(x[:2])  # 通算 0..1 → 出力は番号 0 の 1 点
    out2 = d.process(x[2:3])  # 通算 2 → 出力なし
    out3 = d.process(x[3:])  # 通算 3..10 → 番号 4, 8 の 2 点
    got = np.concatenate([np.asarray(o) for o in (out1, out2, out3)])
    ref = signal.lfilter(taps, 1.0, x)[::4]
    np.testing.assert_allclose(got, ref, rtol=1e-12, atol=1e-13)


def test_decimator_reset_reproduces_fresh_state(rng):
    taps = filters.design_audio_decimation_fir()
    x = rng.standard_normal(512)
    d = PolyphaseDecimator(taps, 4)
    first = d.process(x)
    d.reset()
    np.testing.assert_array_equal(d.process(x), first)


# ---------------------------------------------------------------- 純遅延


def test_delay_block_vs_batch_bitwise(rng, sizes):
    d_len = 127  # ステレオ群遅延整合の実値 (STEREO_FIR_TAPS-1)//2
    x = rng.standard_normal(N)
    # 現行 receiver の zeros 前置と同値
    ref = np.concatenate([np.zeros(d_len), x])[: len(x)]
    got = run_blocked(DelayLine(d_len), x, sizes)
    np.testing.assert_array_equal(got, ref)


def test_delay_reset_reproduces_fresh_state(rng):
    x = rng.standard_normal(512)
    d = DelayLine(127)
    first = d.process(x)
    d.reset()
    np.testing.assert_array_equal(d.process(x), first)
