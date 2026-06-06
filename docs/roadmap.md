# Roadmap

進捗・フェーズ管理の**正本**。進捗を動かしたらこのファイルを直接更新する。
方式の決定理由は [adr/](adr/)、設計の現状は [architecture.md](architecture.md) を参照。

全体の流れ: **algo**(Python で FM 変復調方式を確立)→ **hdl**(Tang Nano 9K へ実装)。

到達ビジョンの全体図は [diagrams/system-architecture.mmd](diagrams/system-architecture.mmd)。
**MVP(v1.0 当面)= Phase 1–2**(FM をステレオで受信して鳴らす)。ビジョン上段の **適応オーディオ(Phase 3)・コンテキスト認識(Phase 4)は将来**で、方針は ADR が正本。MVP とビジョンの線引きは [architecture.md](architecture.md) を参照。

> **最優先は MVP(Phase 1–2)の完成**。FM をステレオで受信して鳴らすことを最初の達成点とする。Phase 3–4 は構想として記録し、MVP の成立まで着手しない。思想は [philosophy.md](philosophy.md) を参照。

## Phase 1: algo — モデリングとシミュレーション

Python/NumPy による FM ステレオ変復調モデル。成果の詳細は [README.md](../README.md) を参照。

- [x] 1.1 送信(音声 → FM 変調 → AWGN 付加)
- [x] 1.2 受信(選局 Mixing → 帯域制限 → デシメーション → ベースバンド IQ)
- [x] 1.3 復調(IQ → 位相 → 微分で音声復元)
- [x] 1.4 ステレオ MPX(MPX 生成 / 分離、DSB-SC によるサブキャリア検波)
- [x] 1.5.1 pre-emphasis / de-emphasis(高域のノイズ耐性向上)
- [x] 1.5.2 PLL(デジタル 2 次 Type-II)によるパイロット同期・搬送波再生
- [x] 1.5.3 PLL を含む受信系の最適化(README 1.5.2.2 続き)
  - ステレオ復調を線形位相 FIR 化(`stereo_main_lpf`/`stereo_sub_bpf`、同長=群遅延一致)し
    main を群遅延ぶん遅らせて sub と整合。IIR の非線形位相が壊していた「副搬送波=2×パイロット」関係を回復。
  - 38kHz 搬送波に位相補正(PLL の NCO 出力に定数オフセット、`STEREO_CARRIER_PHASE_RAD`)。
  - PLL 帯域を 50→200Hz に最適化(高 SNR では追従残差 ε が律速で広帯域が有利。低 SNR でも悪化しないことを SNR スイープで確認)。
  - 結果: セパレーション 0.84→**45.04dB**(Sony 42dB 超過 → ハードゲート昇格)。
- [x] 1.6 評価基盤の整備(品質を規律ではなく**仕組み**で守る。CI で lint と並ぶゲートにする)
  - [x] `add_awgn` の乱数シード固定(再現性。`radio/channel.py` は `rng` 注入式で固定可能)
  - [x] `pytest` 導入・`tests/` 雛形・`make eval` ターゲット・GitHub Actions(CI: fmt-check + lint + eval)
  - [x] メトリクス層 `algo/eval/metrics.py`(THD/SINAD・L-R セパレーション・PLL ロック時間)— 契約テスト 5 ケース green
        ※ HDL シミュ出力も同じ関数に通し、algo↔hdl のアクセプタンス・オラクルとして再利用する
- [ ] 1.7 復調品質の定量評価とゲート化(characterize → `baseline.json` → 回帰ゲート → 絶対しきい値)
  - [x] characterize ハーネス(決定論パイプライン `eval/harness.py` / 集計 `eval/characterize.py`)
  - [x] `baseline.json` 機構(`make characterize` で生成、`schema_version`/`conditions` 付き)
  - [x] 回帰ゲート(ハード)・絶対しきい値ゲート(`tests/test_quality_gate.py`、`make eval` に同梱)
  - [x] 方針を ADR-005 で確定([adr/adr-005-demod-quality-gate.md](adr/adr-005-demod-quality-gate.md))
  - [x] 絶対しきい値の目標を市販製品スペック(Sony ST-5130)に設定 — THD ≤0.3% / セパレーション ≥42dB / S/N ≥75dB
  - [ ] **ギャップを詰める**(現状 THD 0.007% / SINAD 66.8dB / セパレーション 0.84dB)。
        ステレオ分離の前にモノラル復調経路で THD/SINAD を測る方針へ切替(`_mono_decode`、baseline schema v2)。
        THD はモノラルで Sony 絶対ゲート(≤0.3%)に到達しハードゲートへ昇格済み。
        SINAD は2段で改善: (1) 19kHz パイロット漏れを 15kHz 間引き FIR(`dsp/filters.py`、ポリフェーズ)で除去 40.9→49.8dB、
        (2) 複素ミキサ後のチャネル選択 LPF(`_channel_select`、2*fc 像除去)で 49.8→66.8dB。
        ※ (2) は受信共通段のため、未達のセパレーションが 1.67→0.84dB に微変動(共に分離ゼロ域、baseline 追従)。
        ステレオ L/R の最終間引きも mono と同じ 15kHz ポリフェーズ FIR に統一(パイロット除去を反映)。
        セパレーションは 1.5.3 で 0.84→45.04dB に改善し Sony 絶対ゲート(≥42dB)へ昇格(下記 1.5.3)。
        **残るギャップは SINAD のみ(目標 75dB・現状 66.8dB・あと 8.2dB)**。THD・セパレーションは昇格済み。
  - [ ] PLL ロック tol/hold の確定(観測ログから `settings.py` を埋める)

  > 運用(ラチェット): 回帰ゲートが床を守り、Sony 絶対ゲートは strict xfail で目標を追跡する。
  > アルゴが各メトリクスで Sony 仕様に到達すると xpass(strict→fail)で「ハードゲートへ昇格」を通知。
  > **1.7 合格 = Sony 絶対ゲートが全て昇格しきった状態**(= 方式確立 = Phase 2/HDL 合格基準)。
  > 改善したら `make characterize` で baseline の床を上げ直す。
- [ ] 1.8 因果・ストリーミング参照モデル化(判別器を I/Q 差分形へ / フィルタを状態付き逐次形へ)
- [ ] デシメーション多段化の整理(現状: 係数 12 単段 FIR、`radio/receiver.py`)
- [ ] 最大周波数偏移 75kHz での品質検証(settings は復帰済み・定量未確認、README 1.2 c.f. 参照)

> **「完了(x)」は実装済みを表す。方式の確立は 1.7 の定量評価に合格して初めて成立**する(これが Phase 2/HDL の合格基準)。
> 1.8 は固定小数点化([../docs/adr/](adr/) 経由で Phase 2.3)の前段。現行復調は `np.unwrap` の全体処理でそのままでは HW に乗らない。

## Phase 2: hdl — Tang Nano 9K 実装

ツールチェーン・ビルドフローは整備済み([src/hdl/README.md](../src/hdl/README.md)、ルートの Makefile FPGA セクション)。

進め方は **疎通 → 出力パス → DSP の RTL 化 → RF フロントエンド** の順。前段ほどハードが要らずブレッドボードで完結し、後段ほどアナログ・RF の作り込みが要る。RF 方式と固定小数点化は I/O 語長を決める設計判断なので、確定は ADR で行う(→ [adr/](adr/))。

### 2.1 疎通

- [x] 開発環境(oss-cad-suite / Makefile / `activate-cad.sh` / ディレクトリ規約)
- [ ] blink(`TOP=blink`)で合成 → 配置配線 → 実機点灯の疎通確認

### 2.2 出力パス(ΣΔ DAC を自作)

algo の復調出力を実機で鳴らすための土台。コアは自作する(既製 I2S DAC に頼らず 1bit DAC の設計を学ぶ)。外付けは RC フィルタ + イヤホンジャックのみで、ブレッドボードで完結する。

- [ ] 1bit ΣΔ(または PWM)DAC を SystemVerilog で実装
- [ ] 正弦波テーブルを鳴らして `make sim` で波形確認 → 実機でイヤホン出力確認
- [ ] ステレオ 2ch 化

### 2.3 DSP ブロックの RTL 化(ハード不要)

algo で確立した各ブロックを RTL 化し、`make sim` で algo の数値と突き合わせる。対象・順序は ADR で決定。

- [ ] 直交復調 / de-emphasis など 1 ブロックを RTL 化 + テストベンチ検証
- [ ] 固定小数点モデルの作成(語長は ADC/DAC のビット幅で決まる ⇒ RF 方式確定後に着手)
- [ ] 受信チェーン全体の RTL 化

### 2.4 RF フロントエンド → 実局受信(到達目標: 81.3 MHz)

80 MHz 帯のアナログ部は **ブレッドボード(EIC-801)では安定しない**ため、基板化(or ベタアース実装)が前提。方式は **方式A(低IF + 高速 ADC 1個で実数標本化)** に確定([adr/adr-001-rf-frontend-low-if-adc.md](adr/adr-001-rf-frontend-low-if-adc.md))。algo の RF 段に 1 対 1 対応する。

- [x] RF 方式を ADR で確定(方式A / ADR-001)
- [ ] フロントエンド製作(アンテナ → BPF/LNA → ミキサ[LO: Si5351] → 低IF → 高速 ADC)
- [ ] 実機で 81.3 MHz の受信・ステレオ復調確認

> 各ブロックの RTL 化対象・順序、および RF 方式は ADR が正本。確定したらここを更新する。

## Phase 3: 適応オーディオ(Sfumato DSP Core)— 将来

MVP(Phase 1–2)成立後の拡張。ビジョン図 Muscle 段の Sfumato DSP Core(Adaptive EQ / Compressor / Ambience)を algo で確立してから hdl へ落とす(二本立ての原則は不変)。エフェクトは固定または手動パラメータで駆動し、AI は用いない。用語・責務構成は [architecture.md](architecture.md)、思想は [philosophy.md](philosophy.md) を参照。

- [ ] 適応エフェクト(EQ / Compressor / Ambience)を algo でモデル化・評価
- [ ] パラメータ制御 I/F(Register Bus / レジスタ書き換え方式)を定義 ⇒ Brain と疎結合にする前提([adr/adr-003-brain-implementation-approach.md](adr/adr-003-brain-implementation-approach.md))
- [ ] 確立したエフェクトを RTL 化し、Muscle 経路に挿入

## Phase 4: コンテキスト認識(Brain)— 将来

ビジョン図上段の Brain(マイク → 特徴量 → 推論 → パラメータ制御)。環境に応じて Phase 3 のエフェクトを動的に "Morphing" する。**実装方式は未決**([adr/adr-003-brain-implementation-approach.md](adr/adr-003-brain-implementation-approach.md))で、MVP では着手しない。

- [ ] マイク入力(I2S Rx)+ 特徴量(FFT / 帯域パワー等)を algo で試作
- [ ] コンテキスト判定をまず軽量ヒューリスティクス / 小規模分類器で実装(大規模 NN は範囲外候補)
- [ ] 実装方式(専用 RTL / ソフトコア / HLS)を ADR-003 で確定し、Register Bus 経由で Phase 3 を制御

> Phase 3 / 4 はビジョン段階。着手前に該当 ADR(003 / 004)を Proposed → Accepted へ更新し、方式を確定してから進める。

## ハードウェア調達(調達タイミングと候補)

**手元にあるもの**: Tang Nano 9K / ジャンパワイヤ / ブレッドボード EIC-801。
調達は急がない。各段階に入る直前にまとめる方針(特に RF 部品は方式未確定のうちは買わない)。

| 段階 | 買うべき時 | 候補 | 備考 |
|---|---|---|---|
| 2.2 出力パス | ΣΔ DAC を実機で鳴らす直前 | 3.5mm ステレオジャック / 抵抗(1kΩ前後 数種)/ コンデンサ(数nF〜0.1µF 数種)/ ピンヘッダ | RC フィルタ定数は実験で詰める。秋月で一括で揃う |
| 音質改善(任意) | ΣΔ で音質に不満が出たら | PCM5102A DIP化キット(I2S・MCLK 不要) | 秋月 AE 品。ΣΔ から載せ替え |
| 2.4 RF(方式確定後) | RF 方式 ADR を決めてから | LO: Si5351A モジュール / ADC: AD9226 系(12bit・65MSPS、秋月では弱く通販)/ ミキサ・アナログスイッチ(FST3253 等)/ RF フィルタ・オペアンプ / アンテナ用ワイヤ(約 75cm) | 方式 A/B で構成が変わるため ADR 後に確定。基板化前提 |

> イヤホンの「アンテナ兼用」(RF 入力と音声出力を 1 本で共存)は上級技。まずは RF 入力(別ワイヤ)と音声出力(イヤホンジャック)を分けて進める。

## セットアップ・チェックリスト

### algo

1. `make install`(uv sync で `.venv` 構築)
2. `make run`(シミュレーション実行、`outputs/` に結果)

### hdl

1. oss-cad-suite を `~/tools/oss-cad-suite` に配置(別の場所なら `OSS_CAD_SUITE` で上書き)
2. `source ./activate-cad.sh`(このシェルで有効化)
3. `make sim` でシミュレーション疎通確認 → `make load` で実機確認
