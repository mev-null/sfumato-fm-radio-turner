# Roadmap

進捗・フェーズ管理の**正本**。進捗を動かしたらこのファイルを直接更新する。
方式の決定理由は [adr/](adr/)、設計の現状は [architecture.md](architecture.md) を参照。

全体の流れ: **algo**(Python で FM 変復調方式を確立)→ **hdl**(Tang Nano 9K へ実装)。

## Phase 1: algo — モデリングとシミュレーション

Python/NumPy による FM ステレオ変復調モデル。成果の詳細は [README.md](../README.md) を参照。

- [x] 1.1 送信(音声 → FM 変調 → AWGN 付加)
- [x] 1.2 受信(選局 Mixing → 帯域制限 → デシメーション → ベースバンド IQ)
- [x] 1.3 復調(IQ → 位相 → 微分で音声復元)
- [x] 1.4 ステレオ MPX(MPX 生成 / 分離、DSB-SC によるサブキャリア検波)
- [x] 1.5.1 pre-emphasis / de-emphasis(高域のノイズ耐性向上)
- [x] 1.5.2 PLL(デジタル 2 次 Type-II)によるパイロット同期・搬送波再生
- [ ] 1.5.3 PLL を含む受信系の最適化(README 1.5.2.2 続き)
- [ ] 2 段デシメーションの整理 / 最大周波数偏移の本来値での検証(README 1.2 c.f. 参照)

## Phase 2: hdl — Tang Nano 9K 実装

ツールチェーン・ビルドフローは整備済み([src/hdl/README.md](../src/hdl/README.md)、ルートの Makefile FPGA セクション)。

- [x] 開発環境(oss-cad-suite / Makefile / `activate-cad.sh` / ディレクトリ規約)
- [ ] blink(`TOP=blink`)で合成 → 配置配線 → 実機点灯のフロー疎通確認
- [ ] algo で確立した各ブロックの RTL 化(対象・順序は今後 ADR で決定)
- [ ] テストベンチによる各モジュール検証(`make sim` / `make wave`)
- [ ] 実機での FM 受信動作確認

> Phase 2 の具体的な実装対象・順序は未確定。確定したら ADR を追加し、ここを更新する。

## セットアップ・チェックリスト

### algo

1. `make install`(uv sync で `.venv` 構築)
2. `make run`(シミュレーション実行、`outputs/` に結果)

### hdl

1. oss-cad-suite を `~/tools/oss-cad-suite` に配置(別の場所なら `OSS_CAD_SUITE` で上書き)
2. `source ./activate-cad.sh`(このシェルで有効化)
3. `make sim` でシミュレーション疎通確認 → `make load` で実機確認
