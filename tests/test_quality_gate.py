"""
復調品質の回帰ゲート(roadmap 1.7)。

実際の TX→通信路→RX パイプライン出力をメトリクスに通し、
(A) 絶対しきい値ゲート と (B) baseline 回帰ゲート で品質を守る。

運用方針(ラチェット):
- 絶対しきい値ゲート(A)は市販製品(Sony)スペックを目標に置く。現行アルゴが
  未達の間は strict xfail として CI を緑に保ちつつギャップを毎回計測する。
  アルゴが仕様に到達すると xpass(strict→fail)で「ハードゲートへ昇格しろ」と
  通知される。昇格は該当テストの xfail マークを外して行う。
- 回帰ゲート(B)はハード。baseline からの劣化を毎 PR でブロックする(床を守る)。
- しきい値・許容幅・PLL tol が None の間、baseline 未生成の間は skip する。

数値は利用者が確定する(rule 12 / docs/adr/adr-005-demod-quality-gate.md)。
"""

import pytest

from algo import settings
from algo.eval.characterize import build_report, current_conditions, load_baseline


@pytest.fixture(scope="module")
def report():
    """TX/RX は重いので 1 セッションで 1 回だけ measure し、テスト間で共有する。"""
    return build_report()


# --- (A) 絶対しきい値ゲート(Sony スペック目標 / strict xfail で追跡) --------
# dB 系(SINAD・セパレーション)は「大きいほど良い」→ 下限。
# THD・ロック時間は「小さいほど良い」→ 上限。
# 未達の間は xfail(緑)、到達すると xpass(strict→赤)でハードゲート昇格を促す。

_SONY_TARGET = "Sony 製品スペック目標。到達したら xfail を外しハードゲートへ昇格する"


# THD はモノラル復調経路で Sony 絶対しきい値(0.3%)に到達したためハードゲートへ昇格。
# (roadmap 1.7 ラチェット運用。SINAD・セパレーションは未達のため strict xfail のまま追跡)
def test_thd_below_absolute_ceiling(report):
    if settings.THD_MAX is None:
        pytest.skip("settings.THD_MAX 未設定(利用者が観測値から確定する)")
    assert report["metrics"]["thd"] <= settings.THD_MAX


@pytest.mark.xfail(reason=_SONY_TARGET, strict=True)
def test_sinad_above_absolute_floor(report):
    if settings.SINAD_MIN_DB is None:
        pytest.skip("settings.SINAD_MIN_DB 未設定(利用者が観測値から確定する)")
    assert report["metrics"]["sinad_db"] >= settings.SINAD_MIN_DB


@pytest.mark.xfail(reason=_SONY_TARGET, strict=True)
def test_separation_above_absolute_floor(report):
    if settings.SEPARATION_MIN_DB is None:
        pytest.skip("settings.SEPARATION_MIN_DB 未設定(利用者が観測値から確定する)")
    assert report["metrics"]["separation_db"] >= settings.SEPARATION_MIN_DB


def test_pll_lock_within_budget(report):
    if settings.PLL_LOCK_MAX_S is None:
        pytest.skip("settings.PLL_LOCK_MAX_S 未設定(利用者が観測値から確定する)")
    lock = report["metrics"]["pll_lock_time_s"]
    if lock is None:
        pytest.skip("PLL_LOCK_TOL/HOLD_SAMPLES 未設定でロック時間が未計測")
    assert lock <= settings.PLL_LOCK_MAX_S


# --- (B) baseline 回帰ゲート ---------------------------------------------------
# baseline.json の good 値から「良い向きと逆」に許容幅を超えて劣化したら fail。


def test_no_regression_against_baseline(report):
    if settings.REGRESSION_TOL is None:
        pytest.skip("settings.REGRESSION_TOL 未設定(利用者が許容幅を確定する)")

    base = load_baseline()
    if base is None:
        pytest.skip("baseline.json 未生成(先に make characterize を実行する)")

    # 条件が変わっていたら基準は無効。比較しない。
    assert base["conditions"] == current_conditions(), (
        "測定条件が baseline と異なる。make characterize で baseline を取り直す"
    )

    tol = settings.REGRESSION_TOL
    cur = report["metrics"]
    base_m = base["metrics"]

    # 大きいほど良い: 下振れを検出
    assert cur["sinad_db"] >= base_m["sinad_db"] * (1 - tol)
    assert cur["separation_db"] >= base_m["separation_db"] * (1 - tol)

    # 小さいほど良い: 上振れを検出
    assert cur["thd"] <= base_m["thd"] * (1 + tol)

    # PLL ロック時間は両側が None でないときだけ比較
    if cur["pll_lock_time_s"] is not None and base_m["pll_lock_time_s"] is not None:
        assert cur["pll_lock_time_s"] <= base_m["pll_lock_time_s"] * (1 + tol)
