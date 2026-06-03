# Architecture

システム構成・信号設計の現状(設計の「現在地」)。
「なぜそう決めたか」は [adr/](adr/)、「やること/進捗」は [roadmap.md](roadmap.md) を参照。

数値の出どころは重複させない。algo の物理定数・レートは `src/sfumato/settings.py`、hdl の規約・デバイス値は [../src/hdl/README.md](../src/hdl/README.md) を正本とし、ここからは参照する。

## 全体像

FM ステレオ放送の受信機。2 つのトラックで構成する。

- **algo**(`src/sfumato/`): Python/NumPy で送信〜通信路〜受信を丸ごとモデル化し、方式と数値を確立する場。
- **hdl**(`src/hdl/`): algo で確立した方式を Tang Nano 9K(Gowin GW1NR-9C)向け SystemVerilog に実装する場。

設計の原則: **algo で検証していない方式を hdl に実装しない。**

## 信号設計(レート / 帯域)

レートは多段で、音声 ⇄ MPX ⇄ RF の 3 層。値は `src/sfumato/settings.py` が正本(下表は参照用サマリ)。

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

`src/sfumato/` パッケージ。処理の流れと解説は [algorithm.md](algorithm.md)、エントリは `main.py`。

- `transmitter.py` … 音声 → MPX 生成 → アップサンプリング → FM 変調 → IQ 信号(`FmTransmitter.modulate`)。
- `channnel.py` … 通信路。AWGN 付加(`add_awgn`)。
- `receiver.py` … RF → ベースバンド IQ → MPX 復調(`FmReceiver.process`)、搬送波再生(`_recover_carrier`)、ステレオ分離(`_stereo_decode`)。
- `dsp/` … 信号処理部品。`filters.py`(各種フィルタ)、`emphasis.py`(pre/de-emphasis)、`pll.py`(デジタル 2 次 Type-II PLL)。
- `settings.py` … 物理定数・レートの単一の出どころ。
- `utils/` … WAV 入出力・音源生成・可視化。`component/radio_ui.py` … 実行時の UI/ログ。

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

algo の各ブロックを RTL へどの順序・粒度で落とすかは未確定。確定次第 ADR を追加し、対応表をここに追記する。

## algo ↔ hdl 対応表

algo の方式を hdl に落とした対応を、確定したものから記録する。

| algo(方式 / 定数) | hdl(モジュール) | ステータス | 関連 ADR |
|---|---|---|---|
| (未) | (未) | - | - |
