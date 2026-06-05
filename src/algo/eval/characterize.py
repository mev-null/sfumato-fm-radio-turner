"""
復調品質の characterize(測定 → レポート → baseline.json 書き出し)。

harness で回した復調出力を metrics 関数に通し、品質メトリクスの辞書を作る。
これが baseline.json の schema であり、回帰ゲートの比較対象になる。

使い方:
    python -m algo.eval.characterize           # 測定してレポートを表示
    python -m algo.eval.characterize --update   # baseline.json を再生成(意図的更新)

baseline の更新は「改善を確認したとき」だけ手動で行う(回帰ゲートが黙って
基準値ごと動く事故を避ける)。方針は docs/adr/adr-005-demod-quality-gate.md。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from algo import settings
from algo.eval import metrics
from algo.eval.harness import one_channel_driven, run_pipeline, single_tone

# baseline.json の所在(このモジュールと同じディレクトリ)
BASELINE_PATH = Path(__file__).parent / "baseline.json"

# schema のバージョン。条件・項目の構造を変えたら上げる。
SCHEMA_VERSION = 1


def current_conditions() -> dict:
    """現在の settings から測定条件を取り出す(baseline との一致判定にも使う)。"""
    return {
        "tone_hz": settings.EVAL_TONE_FREQ,
        "duration_s": settings.EVAL_DURATION_S,
        "snr_db": settings.EVAL_SNR_DB,
        "seed": settings.EVAL_SEED,
    }


def build_report() -> dict:
    """各シナリオを回しメトリクス値を集計する。baseline schema と同形を返す。

    THD/SINAD は単一トーン、セパレーションは L 駆動・R 無音で測る。
    PLL ロック時間は tol/hold が未設定(None)の間は計測せず None を記録する。
    """
    f0 = settings.EVAL_TONE_FREQ
    snr = settings.EVAL_SNR_DB
    seed = settings.EVAL_SEED

    r_tone = run_pipeline(single_tone(), snr, seed)
    r_sep = run_pipeline(one_channel_driven(), snr, seed)

    pll_lock = None
    if settings.PLL_LOCK_TOL is not None and settings.PLL_LOCK_HOLD_SAMPLES is not None:
        pll_lock = metrics.pll_lock_time(
            r_tone.pll_error,
            r_tone.mpx_fs,
            tol=settings.PLL_LOCK_TOL,
            hold_samples=settings.PLL_LOCK_HOLD_SAMPLES,
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "conditions": current_conditions(),
        "metrics": {
            "thd": metrics.thd(r_tone.left, r_tone.audio_fs, f0),
            "sinad_db": metrics.sinad_db(r_tone.left, r_tone.audio_fs, f0),
            "separation_db": metrics.channel_separation_db(r_sep.left, r_sep.right),
            "pll_lock_time_s": pll_lock,
        },
    }


def load_baseline() -> dict | None:
    """baseline.json を読む。未生成なら None。"""
    if not BASELINE_PATH.exists():
        return None
    return json.loads(BASELINE_PATH.read_text())


def write_baseline(report: dict) -> None:
    """レポートを baseline.json に書き出す。"""
    BASELINE_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    report = build_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if "--update" in sys.argv:
        write_baseline(report)
        print(f"\nbaseline written → {BASELINE_PATH}")


if __name__ == "__main__":
    main()
