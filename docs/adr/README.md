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

## 新しい ADR の書き方

- ファイル名: `adr-<3桁連番>-<短いkebab題>.md`(例 `adr-001-pll-type2.md`)
- 雛形のセクション: **コンテキスト / 決定 / 影響(良い影響・トレードオフ・将来への含み)/ 備考**
- ステータス: `Proposed` → `Accepted` → 必要なら `Superseded by adr-NNN` / `Deprecated`
- 決定したら、この索引表に1行追加する。
- 雛形は [adr-000-template.md](adr-000-template.md) をコピーして使う。
