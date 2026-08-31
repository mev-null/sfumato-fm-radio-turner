# ハードウェア・ロードマップ(保留)

旧 `docs/roadmap.md` の Phase 2〜4・部品調達表・hdl セットアップ手順を 2026-08-31 に退避したもの。現在の正本は [../roadmap.md](../roadmap.md)(モデル)。保留の経緯は [README.md](README.md)、構成の構想は [architecture-hardware.md](architecture-hardware.md) を参照。再開時に `docs/roadmap.md` へ統合し直す。

> 旧 MVP 定義(参考): **MVP(v1.0)= Phase 1–2**(FM をステレオで受信して鳴らす)。到達ビジョンの全体図は [diagrams/system-architecture.mmd](diagrams/system-architecture.mmd)。ビジョン上段の適応オーディオ(Phase 3)・コンテキスト認識(Phase 4)は MVP 成立まで着手しない。思想は [../philosophy.md](../philosophy.md)。

## Phase 2: hdl — Tang Nano 9K 実装

ツールチェーン・ビルドフローは整備済み([../../src/hdl/README.md](../../src/hdl/README.md)、`src/hdl/Makefile`)。

進め方は **疎通 → 出力パス → DSP の RTL 化 → RF フロントエンド** の順。前段ほどハードが要らずブレッドボードで完結し、後段ほどアナログ・RF の作り込みが要る。RF 方式と固定小数点化は I/O 語長を決める設計判断なので、確定は ADR で行う(→ [adr/](adr/))。

### 2.1 疎通

- [x] 開発環境(oss-cad-suite / `src/hdl/Makefile` / `src/hdl/activate-cad.sh` / ディレクトリ規約)
- [ ] blink(`TOP=blink`)で合成 → 配置配線 → 実機点灯の疎通確認

### 2.2 出力パス(ΣΔ DAC を自作)

モデルの復調出力を実機で鳴らすための土台。コアは自作する(既製 I2S DAC に頼らず 1bit DAC の設計を学ぶ)。外付けは RC フィルタ + イヤホンジャックのみで、ブレッドボードで完結する。

- [ ] 1bit ΣΔ(または PWM)DAC を SystemVerilog で実装
- [ ] 正弦波テーブルを鳴らして `make -C src/hdl sim` で波形確認 → 実機でイヤホン出力確認
- [ ] ステレオ 2ch 化

### 2.3 DSP ブロックの RTL 化(ハード不要)

モデルで確立した各ブロックを RTL 化し、`make -C src/hdl sim` でモデルの数値と突き合わせる。対象・順序は ADR で決定。

- [ ] 直交復調 / de-emphasis など 1 ブロックを RTL 化 + テストベンチ検証
- [ ] 固定小数点モデルの作成(語長は ADC/DAC のビット幅で決まる ⇒ RF 方式確定後に着手)
- [ ] 受信チェーン全体の RTL 化

前提となるモデル側の作業: 因果・ストリーミング参照モデル化([../roadmap.md](../roadmap.md) 1.8)。現行復調は `np.unwrap` の全体処理でそのままでは HW に乗らない。

### 2.4 RF フロントエンド → 実局受信(到達目標: 81.3 MHz)

80 MHz 帯のアナログ部は **ブレッドボード(EIC-801)では安定しない**ため、基板化(or ベタアース実装)が前提。方式は **方式A(低IF + 高速 ADC 1個で実数標本化)** に確定していた([adr/adr-001-rf-frontend-low-if-adc.md](adr/adr-001-rf-frontend-low-if-adc.md)、現在は Deferred)。モデルの RF 段に 1 対 1 対応する。

- [x] RF 方式を ADR で確定(方式A / ADR-001)
- [ ] フロントエンド製作(アンテナ → BPF/LNA → ミキサ[LO: Si5351] → 低IF → 高速 ADC)
- [ ] 実機で 81.3 MHz の受信・ステレオ復調確認

> 各ブロックの RTL 化対象・順序、および RF 方式は ADR が正本。確定したらここを更新する。

## Phase 3: 適応オーディオ(Sfumato DSP Core)— 将来

MVP(Phase 1–2)成立後の拡張。ビジョン図 Muscle 段の Sfumato DSP Core(Adaptive EQ / Compressor / Ambience)をモデルで確立してから hdl へ落とす(モデル先行の原則は不変)。エフェクトは固定または手動パラメータで駆動し、AI は用いない。用語・責務構成は [architecture-hardware.md](architecture-hardware.md)、思想は [../philosophy.md](../philosophy.md) を参照。

- [ ] 適応エフェクト(EQ / Compressor / Ambience)をモデルで設計・評価
- [ ] パラメータ制御 I/F(Register Bus / レジスタ書き換え方式)を定義 ⇒ Brain と疎結合にする前提([adr/adr-003-brain-implementation-approach.md](adr/adr-003-brain-implementation-approach.md))
- [ ] 確立したエフェクトを RTL 化し、Muscle 経路に挿入

## Phase 4: コンテキスト認識(Brain)— 将来

ビジョン図上段の Brain(マイク → 特徴量 → 推論 → パラメータ制御)。環境に応じて Phase 3 のエフェクトを動的に "Morphing" する。**実装方式は未決**([adr/adr-003-brain-implementation-approach.md](adr/adr-003-brain-implementation-approach.md))で、MVP では着手しない。

- [ ] マイク入力(I2S Rx)+ 特徴量(FFT / 帯域パワー等)をモデルで試作
- [ ] コンテキスト判定をまず軽量ヒューリスティクス / 小規模分類器で実装(大規模 NN は範囲外候補)
- [ ] 実装方式(専用 RTL / ソフトコア / HLS)を ADR-003 で確定し、Register Bus 経由で Phase 3 を制御

> Phase 3 / 4 はビジョン段階。着手前に該当 ADR(003 / 004)を Deferred → Proposed → Accepted へ更新し、方式を確定してから進める。

## ハードウェア調達(調達タイミングと候補)

**手元にあるもの**: Tang Nano 9K / ジャンパワイヤ / ブレッドボード EIC-801。
調達は急がない。各段階に入る直前にまとめる方針(特に RF 部品は方式未確定のうちは買わない)。

| 段階 | 買うべき時 | 候補 | 備考 |
|---|---|---|---|
| 2.2 出力パス | ΣΔ DAC を実機で鳴らす直前 | 3.5mm ステレオジャック / 抵抗(1kΩ前後 数種)/ コンデンサ(数nF〜0.1µF 数種)/ ピンヘッダ | RC フィルタ定数は実験で詰める。秋月で一括で揃う |
| 音質改善(任意) | ΣΔ で音質に不満が出たら | PCM5102A DIP化キット(I2S・MCLK 不要) | 秋月 AE 品。ΣΔ から載せ替え |
| 2.4 RF(方式確定後) | RF 方式 ADR を決めてから | LO: Si5351A モジュール / ADC: AD9226 系(12bit・65MSPS、秋月では弱く通販)/ ミキサ・アナログスイッチ(FST3253 等)/ RF フィルタ・オペアンプ / アンテナ用ワイヤ(約 75cm) | 方式 A/B で構成が変わるため ADR 後に確定。基板化前提 |

> イヤホンの「アンテナ兼用」(RF 入力と音声出力を 1 本で共存)は上級技。まずは RF 入力(別ワイヤ)と音声出力(イヤホンジャック)を分けて進める。

## セットアップ・チェックリスト(hdl)

1. oss-cad-suite を `~/tools/oss-cad-suite` に配置(別の場所なら `OSS_CAD_SUITE` で上書き)
2. `source src/hdl/activate-cad.sh`(このシェルで有効化)
3. `make -C src/hdl sim` でシミュレーション疎通確認 → `make -C src/hdl load` で実機確認(実機書き込みは利用者の明示指示があるときのみ)
