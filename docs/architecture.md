# Architecture

システム構成・信号設計の現状(設計の「現在地」)。
「なぜそう決めたか」は [adr/](adr/)、「やること/進捗」は [roadmap.md](roadmap.md) を参照。

数値の出どころは重複させない。algo の物理定数・レートは `src/algo/settings.py`、hdl の規約・デバイス値は [../src/hdl/README.md](../src/hdl/README.md) を正本とし、ここからは参照する。

## 全体像

FM ステレオ放送の受信機。2 つのトラックで構成する。

- **algo**(`src/algo/`): Python/NumPy で送信〜通信路〜受信を丸ごとモデル化し、方式と数値を確立する場。
- **hdl**(`src/hdl/`): algo で確立した方式を Tang Nano 9K(Gowin GW1NR-9C)向け SystemVerilog に実装する場。

設計の原則: **algo で検証していない方式を hdl に実装しない。**

## 全体ビジョン(North Star)と MVP の線引き

到達ビジョンの全体図は [diagrams/system-architecture.mmd](diagrams/system-architecture.mmd)。FPGA を 2 層に分けて構想している。

- **Muscle(Adaptive Audio Path)**: RF 受信 → DDC/復調 → 適応オーディオ(Sfumato DSP Core)→ 出力。音を通す本線。
- **Brain(Context Awareness Engine)**: マイク入力 → 特徴量 → コンテキスト認識 → パラメータ制御。環境に応じて Muscle のエフェクトを動的に書き換える(Register Bus 経由の "Morphing")。

本プロジェクトの実装射程を MVP とビジョンに線引きする。MVP はビジョンの Muscle 最小経路に対応する。

| 区分 | 範囲 | 正本 |
|---|---|---|
| **MVP** | Muscle の最小経路: RF 受信 → 復調 → 出力(自作 ΣΔ DAC)。FM をステレオで鳴らす | roadmap Phase 1–2 |
| **ビジョン: 適応オーディオ** | Sfumato DSP Core(Adaptive EQ / Compressor / Ambience) | roadmap Phase 3 / [philosophy.md](philosophy.md) |
| **ビジョン: コンテキスト認識** | Brain(特徴量 + 推論 + パラメータ制御) | roadmap Phase 4 / [adr-003](adr/adr-003-brain-implementation-approach.md) |

Brain / Muscle の二層は思想(思考する身体・境界を溶かす)を構成へ写したものである。**思想の正本は [philosophy.md](philosophy.md)**。用語と責務構成は次のとおり(本節を正本とする):

- **基盤(substrate)= FM 放送リンク**: 変調・通信路・復調。sfumato の核ではなく土台。責務名 **radio**(= `src/algo/radio/`)。
- **sfumato の核 = 境界を溶かす層**: 適応オーディオ(morph)+ コンテキスト認識(context)。図の "Sfumato DSP Core" + "Brain"。将来(Phase 3 / 4)。

## 信号設計(レート / 帯域)

レートは多段で、音声 ⇄ MPX ⇄ RF の 3 層。値は `src/algo/settings.py` が正本(下表は参照用サマリ)。

| 層 | レート | 定数 | 備考 |
|---|---|---|---|
| 音声 (Audio) | 48 kHz | `AUDIO_FS` | ベースバンド音声 |
| MPX(中間) | 192 kHz | `MPX_FS` | ステレオ MPX 生成・分離用(= 48k × 4) |
| RF | 2.304 MHz | `RF_FS` | 無線帯域(= 192k × 12) |

- デシメーション: RF → MPX が ×1/12(`RF_TO_MPX_FACTOR`)、MPX → 音声が ×1/4(`MPX_TO_AUDIO_FACTOR`)。
- ステレオ規格: パイロット 19 kHz(`PILOT_FREQ`)、サブキャリア 38 kHz(`SUB_FREQ`)。
- FM 規格: 搬送波はシミュレーション用に 250 kHz(`CARRIER_FREQ`、本番は 81.3 MHz 想定)、最大周波数偏移 ±75 kHz(`MAX_DEVIATION`)、時定数 50 µs(`TIME_CONSTANT`)。
- PLL: ループ帯域幅 50 Hz(`PLL_BANDWIDTH`)、ダンピング 1.2(`PLL_DAMPING`)。

## algo の構成

`src/algo/` パッケージ。処理の流れと解説は [algorithm.md](algorithm.md)、エントリは `main.py`。責務別に構成する(基盤 = `radio/`、将来の sfumato 核 = `morph/` `context/` を予約)。

- `radio/` … 【基盤】FM 放送リンク。
  - `transmitter.py` … 音声 → MPX 生成 → アップサンプリング → FM 変調 → IQ 信号(`FmTransmitter.modulate`)。
  - `channel.py` … 通信路。AWGN 付加(`add_awgn`)。
  - `receiver.py` … RF → ベースバンド IQ → MPX 復調(`FmReceiver.process`)、搬送波再生(`_recover_carrier`)、ステレオ分離(`_stereo_decode`)。
- `dsp/` … 信号処理部品(共通)。`filters.py`(各種フィルタ)、`emphasis.py`(pre/de-emphasis)、`pll.py`(デジタル 2 次 Type-II PLL、ブロック図 [diagrams/pll-block.mmd](diagrams/pll-block.mmd))。
- `settings.py` … 物理定数・レートの単一の出どころ。
- `eval/` … メトリクス層(品質オラクル)。`utils/` … WAV 入出力・音源生成・可視化。`component/radio_ui.py` … 実行時の UI/ログ。
- `morph/` `context/` … sfumato 核(ビジョン)。適応オーディオ / 環境センシング。Phase 3 / 4 で設ける責務として予約する。

主要処理パイプライン(送信 → 通信路 → 受信):

```
音声(48k) → MPX(192k) → RF(2.304M) → FM変調 → IQ
   → [AWGN] →
IQ → 直交復調 → MPX(192k) → PLLで38k再生 → マトリクス分離 → 音声(48k)
```

## hdl の構成

`src/hdl/`。ディレクトリ規約・ビルドフロー・ピン参照・デバイス値は [../src/hdl/README.md](../src/hdl/README.md) が正本。

- `rtl/` … 合成対象 SystemVerilog(トップは `<TOP>.sv`、既定 `TOP=blink`)。
- `tb/` … テストベンチ(`<TOP>_tb.sv`)。
- `constraints/tangnano9k.cst` … ピン制約。
- ビルドはルートの Makefile FPGA セクション(yosys → nextpnr-himbaechel → gowin_pack → openFPGALoader)。

RF 入力方式は **低IF + 高速 ADC 1個で実数標本化**(方式A、[adr/adr-001-rf-frontend-low-if-adc.md](adr/adr-001-rf-frontend-low-if-adc.md))。アンテナ → BPF/LNA → ミキサ(LO: Si5351)→ 低IF(`CARRIER_FREQ` = 250 kHz に整合)→ 高速 ADC(`RF_FS` = 2.304 MSPS 相当を狙う)→ FPGA。これにより algo の受信器(digital mix で選局する RF 段)をそのまま RTL 化の基準にできる。音声出力は FPGA 内製の ΣΔ DAC → RC フィルタ → イヤホンジャック(方式は [adr-002](adr/adr-002-audio-output-sigma-delta-dac.md)、I2S 外部 DAC は任意上位)。

algo の各ブロックを RTL へどの順序・粒度で落とすかは未確定。確定次第 ADR を追加し、対応表をここに追記する。

## algo ↔ hdl 対応表

algo の方式を hdl に落とした対応を、確定したものから記録する。

| algo(方式 / 定数) | hdl(モジュール) | ステータス | 関連 ADR |
|---|---|---|---|
| (未) | (未) | - | - |
