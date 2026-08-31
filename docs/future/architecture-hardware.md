# ハードウェア構成の構想(保留)

旧 `docs/architecture.md` の North Star(Brain / Muscle 二層構想)・hdl の構成・RF 入力 / 音声出力の方式を 2026-08-31 に退避したもの。現在の正本は [../architecture.md](../architecture.md)(モデル)。保留の経緯は [README.md](README.md)、進捗は [roadmap-hardware.md](roadmap-hardware.md)、決定理由は [adr/](adr/) を参照。

## 旧・全体像(二本立て)

保留前は、FM ステレオ放送の受信機を 2 つのトラックで構成していた。

- **algo**(`src/algo/`): Python/NumPy で送信〜通信路〜受信を丸ごとモデル化し、方式と数値を確立する場。
- **hdl**(`src/hdl/`): algo で確立した方式を Tang Nano 9K(Gowin GW1NR-9C)向け SystemVerilog に実装する場。

設計の原則: **algo で検証していない方式を hdl に実装しない。** この原則は再開時もそのまま適用する。

## 全体ビジョン(North Star)と MVP の線引き

到達ビジョンの全体図は [diagrams/system-architecture.mmd](diagrams/system-architecture.mmd)。FPGA を 2 層に分けて構想している。

- **Muscle(Adaptive Audio Path)**: RF 受信 → DDC/復調 → 適応オーディオ(Sfumato DSP Core)→ 出力。音を通す本線。
- **Brain(Context Awareness Engine)**: マイク入力 → 特徴量 → コンテキスト認識 → パラメータ制御。環境に応じて Muscle のエフェクトを動的に書き換える(Register Bus 経由の "Morphing")。

実装射程を MVP とビジョンに線引きしていた。MVP はビジョンの Muscle 最小経路に対応する。

| 区分 | 範囲 | 正本 |
|---|---|---|
| **MVP** | Muscle の最小経路: RF 受信 → 復調 → 出力(自作 ΣΔ DAC)。FM をステレオで鳴らす | [roadmap-hardware.md](roadmap-hardware.md) Phase 2(Phase 1 = モデル) |
| **ビジョン: 適応オーディオ** | Sfumato DSP Core(Adaptive EQ / Compressor / Ambience) | roadmap-hardware Phase 3 / [../philosophy.md](../philosophy.md) |
| **ビジョン: コンテキスト認識** | Brain(特徴量 + 推論 + パラメータ制御) | roadmap-hardware Phase 4 / [adr-003](adr/adr-003-brain-implementation-approach.md) |

Brain / Muscle の二層は思想(思考する身体・境界を溶かす)を構成へ写したものである。**思想の正本は [../philosophy.md](../philosophy.md)**。用語と責務構成は次のとおり:

- **基盤(substrate)= FM 放送リンク**: 変調・通信路・復調。sfumato の核ではなく土台。責務名 **radio**(= `src/algo/radio/`)。
- **sfumato の核 = 境界を溶かす層**: 適応オーディオ(morph)+ コンテキスト認識(context)。図の "Sfumato DSP Core" + "Brain"。将来(Phase 3 / 4)。パッケージ `src/algo/morph/` `src/algo/context/` は構想のみで未作成。

## hdl の構成

`src/hdl/`。ディレクトリ規約・ビルドフロー・ピン参照・デバイス値は [../../src/hdl/README.md](../../src/hdl/README.md) が正本。

- `rtl/` … 合成対象 SystemVerilog(トップは `<TOP>.sv`、既定 `TOP=blink`)。
- `tb/` … テストベンチ(`<TOP>_tb.sv`)。
- `constraints/tangnano9k.cst` … ピン制約。
- ビルドは `src/hdl/Makefile`(yosys → nextpnr-himbaechel → gowin_pack → openFPGALoader)。ルートから `make -C src/hdl <target>`。

RF 入力方式は **低IF + 高速 ADC 1個で実数標本化**(方式A、[adr/adr-001-rf-frontend-low-if-adc.md](adr/adr-001-rf-frontend-low-if-adc.md))。アンテナ → BPF/LNA → ミキサ(LO: Si5351)→ 低IF(`CARRIER_FREQ` = 250 kHz に整合)→ 高速 ADC(`RF_FS` = 2.304 MSPS 相当を狙う)→ FPGA。これによりモデルの受信器(digital mix で選局する RF 段)をそのまま RTL 化の基準にできる。音声出力は FPGA 内製の ΣΔ DAC → RC フィルタ → イヤホンジャック(方式は [adr-002](adr/adr-002-audio-output-sigma-delta-dac.md)、I2S 外部 DAC は任意上位)。

モデルの各ブロックを RTL へどの順序・粒度で落とすかは未確定。再開時に ADR を追加し、algo ↔ hdl の対応表(方式 / 定数 → モジュール / ステータス / 関連 ADR)を本ファイルに設ける。
