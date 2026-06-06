# Architecture Decision Records (ADR)

このプロジェクトの**設計上の決定**を、連番・追記型で記録する。
一度 Accepted にした決定は原則書き換えず、覆す場合は**新しい ADR を追加**して旧 ADR を Superseded にする。

algo(信号処理方式)・hdl(回路実装方式)のどちらの決定もここに記録する。タイトルに `[algo]` / `[hdl]` を付けて区別してよい。

「やること/進捗」は [../roadmap.md](../roadmap.md)、「設計の現状」は [../architecture.md](../architecture.md) を参照。
ここは「なぜそう決めたか」の経緯が積み上がる場所。

## 一覧

| No. | タイトル | ステータス | 日付 |
|---|---|---|---|
| [000](adr-000-template.md) | テンプレート | Template | - |
| [001](adr-001-rf-frontend-low-if-adc.md) | [hdl] FM RF フロントエンド = 低IF + 高速ADC(方式A) | Accepted | 2026-06-03 |
| [002](adr-002-audio-output-sigma-delta-dac.md) | [hdl] 音声出力 = 自作 ΣΔ DAC(MVP)、I2S 外部 DAC は任意上位 | Proposed | 2026-06-04 |
| [003](adr-003-brain-implementation-approach.md) | [hdl] コンテキスト認識(Brain)の実装方式 | Proposed | 2026-06-04 |
| [004](adr-004-sfumato-core-substrate-spresense.md) | [hdl] Sfumato 核の実装基板 = 外部 DSP(Spresense)候補 / 物理 ANC ではなく環境調和 | Proposed | 2026-06-04 |
| [005](adr-005-demod-quality-gate.md) | [algo] 復調品質ゲート(characterize / baseline / 回帰 / 絶対しきい値) | Accepted | 2026-06-05 |
| [006](adr-006-receiver-filter-fir-iir.md) | [algo] 復調純度(THD/SINAD)の改善 — モノ測定・パイロット除去・イメージ除去とフィルタ方式 | Accepted | 2026-06-07 |
| [007](adr-007-stereo-separation.md) | [algo] ステレオ・セパレーションの確立 — 遅延整合 + 搬送波位相補正 + PLL 帯域 | Accepted | 2026-06-07 |

## 新しい ADR の書き方

- ファイル名: `adr-<3桁連番>-<短いkebab題>.md`(例 `adr-001-pll-type2.md`)
- 雛形のセクション: **コンテキスト / 決定 / 影響(良い影響・トレードオフ・将来への含み)/ 備考**
- ステータス: `Proposed` → `Accepted` → 必要なら `Superseded by adr-NNN` / `Deprecated`
- 決定したら、この索引表に1行追加する。
- 雛形は [adr-000-template.md](adr-000-template.md) をコピーして使う。
