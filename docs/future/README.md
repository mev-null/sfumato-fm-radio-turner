# ハードウェア・トラック(保留)

2026-08-31 時点の方針: **本プロジェクトの成果物は Python/NumPy の DSP モデル**(`src/algo/`)と、その復調品質を測る評価基盤である。FPGA(Tang Nano 9K)への移植は将来の拡張候補であり、着手時期は未定。
モデル側では移植を妨げない設計(位相律速段の線形位相 FIR・整数比のレート・逐次形の PLL)を保つに留め、それ以上のハードウェア資料は本ディレクトリに退避して、正本ドキュメント(`docs/` 直下)からは切り離した。

## 保留の理由

- モデル単体で測定可能な成果(THD 0.0072 % / セパレーション 45.04 dB / SINAD 66.8 dB)が出ており、公開・評価の単位として完結している。
- ハードウェア側は疎通用の `blink` 止まりで、RF フロントエンドは基板化が前提のため着手コストが大きい。
- モデルと実装の二本立てを正本に残すと、README・roadmap・architecture が二重に膨らみ、モデルの説明が薄まる。

## ここにあるもの

| ファイル | 内容 |
|---|---|
| [roadmap-hardware.md](roadmap-hardware.md) | 旧 roadmap の Phase 2〜4(FPGA 実装 / 適応オーディオ / コンテキスト認識)、部品調達表、hdl セットアップ手順 |
| [architecture-hardware.md](architecture-hardware.md) | 旧 architecture の North Star(Brain / Muscle 二層構想)、hdl の構成、RF 入力・音声出力の方式 |
| [adr/](adr/) | ハードウェア ADR 001〜004(RF フロントエンド / ΣΔ DAC / Brain 実装方式 / Spresense)。ステータスは Deferred |
| [diagrams/system-architecture.mmd](diagrams/system-architecture.mmd) | FPGA ボード全体のビジョン図(Brain / Muscle) |

コードの足場は [../../src/hdl/](../../src/hdl/README.md)(`blink` の RTL / テストベンチ / ピン制約と、独立した Makefile)。ビルドはリポジトリルートから `make -C src/hdl <target>`(一覧は `make -C src/hdl fpga-help`)。

## 再開するとき

- 移植の合格基準はモデルと同じメトリクス(`src/algo/eval/metrics.py`)を HDL シミュレーション出力に適用すること([ADR-005](../adr/adr-005-demod-quality-gate.md) の将来メモ)。
- ADR のステータスを Deferred → Proposed / Accepted に戻し、番号(001〜004)はそのまま `docs/adr/` へ復帰させる。
- [roadmap-hardware.md](roadmap-hardware.md) を [../roadmap.md](../roadmap.md) に再統合し、architecture も同様に戻す。
