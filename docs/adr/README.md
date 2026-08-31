# Architecture Decision Records (ADR)

このプロジェクトの**設計上の決定**を、連番・追記型で記録する。
一度 Accepted にした決定は原則書き換えず、覆す場合は**新しい ADR を追加**して旧 ADR を Superseded にする。

ここに置くのは **DSP モデル(`src/algo/`)と評価基盤に関する決定**。タイトルには `[algo]` を付ける。
ハードウェア(FPGA 移植)に関する ADR 001〜004 は 2026-08-31 に保留(Deferred)とし、[../future/adr/](../future/adr/) へ移した。番号は欠番のまま残し、再開時に同じ番号で `docs/adr/` へ復帰させる。

「やること/進捗」は [../roadmap.md](../roadmap.md)、「設計の現状」は [../architecture.md](../architecture.md) を参照。
ここは「なぜそう決めたか」の経緯が積み上がる場所。

## 一覧

| No. | タイトル | ステータス | 日付 |
|---|---|---|---|
| [000](adr-000-template.md) | テンプレート | Template | - |
| [005](adr-005-demod-quality-gate.md) | [algo] 復調品質ゲート(characterize / baseline / 回帰 / 絶対しきい値) | Accepted | 2026-06-05 |
| [006](adr-006-receiver-filter-fir-iir.md) | [algo] 復調純度(THD/SINAD)の改善 — モノ測定・パイロット除去・イメージ除去とフィルタ方式 | Accepted | 2026-06-07 |
| [007](adr-007-stereo-separation.md) | [algo] ステレオ・セパレーションの確立 — 遅延整合 + 搬送波位相補正 + PLL 帯域 | Accepted | 2026-06-07 |

保留中のハードウェア ADR(いずれも Deferred 2026-08-31、[../future/adr/](../future/adr/)):
[001](../future/adr/adr-001-rf-frontend-low-if-adc.md) RF フロントエンド(低IF + 高速ADC)/
[002](../future/adr/adr-002-audio-output-sigma-delta-dac.md) 音声出力(自作 ΣΔ DAC)/
[003](../future/adr/adr-003-brain-implementation-approach.md) コンテキスト認識(Brain)の実装方式 /
[004](../future/adr/adr-004-sfumato-core-substrate-spresense.md) Sfumato 核の実装基板(Spresense 候補)。経緯は [../future/README.md](../future/README.md)。

## 新しい ADR の書き方

- ファイル名: `adr-<3桁連番>-<短いkebab題>.md`(例 `adr-008-pll-lock-metric.md`。次の番号は 008)
- 雛形のセクション: **コンテキスト / 決定 / 影響(良い影響・トレードオフ・将来への含み)/ 備考**
- ステータス: `Proposed` → `Accepted` → 必要なら `Superseded by adr-NNN` / `Deprecated` / `Deferred`
- 決定したら、この索引表に1行追加する。
- 雛形は [adr-000-template.md](adr-000-template.md) をコピーして使う。
