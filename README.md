# sfumato-fm-radio-turner

> FPGA で動かす FM ステレオラジオ受信機。Python/NumPy で変復調方式を確立し(**algo**)、Tang Nano 9K 向け SystemVerilog に落とし込む(**hdl**)2 トラック構成のプロジェクト。

<img width="2811" height="853" alt="sfumato-radio-v1-0" src="https://github.com/user-attachments/assets/dd557f31-7457-422a-b91d-ca37e6aa2c50" />

[![CI](https://github.com/mev-null/sfumato-fm-radio-turner/actions/workflows/ci.yml/badge.svg)](https://github.com/mev-null/sfumato-fm-radio-turner/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)

## 概要

FM ステレオ放送を受信するデジタルラジオ受信機を作る。送信〜通信路〜受信を丸ごとソフトウェアでモデル化して正しい変復調方式を確立し、その方式をそのまま FPGA(Tang Nano 9K / Gowin GW1NR-9C)へ実装する。

開発は 2 つのトラックで進める。

- **algo** … 先に正しい方式を見つける場(Python/NumPy/SciPy)。
- **hdl** … 確立した方式をハードに落とす場(SystemVerilog)。

原則として、**algo で検証していない方式は hdl に実装しない**。

## デモ・成果

algo では、FM ステレオの変調・通信路(AWGN)・復調を通したモデルが完成し、音楽信号をそれなりの音質で復調できる。pre/de-emphasis と PLL による搬送波再生まで実装済み。hdl は RTL 実装に着手した段階(進捗は [docs/roadmap.md](docs/roadmap.md))。

### モデル全体のシミュレーション動画

https://github.com/user-attachments/assets/f829db6a-4b2d-4762-8efc-568c4f685ed2

### 復調音声(ステレオ音楽)

- 変調前: [first_ancem92.wav](https://github.com/user-attachments/files/25324970/first_ancem92.wav)
- 復調後: [first_ancem92_restored.wav](https://github.com/user-attachments/files/25324963/first_ancem92_restored.wav)

### 復調結果の解析(pre/de-emphasis 適用後)

<img width="1400" height="1000" alt="ancem92_emphasised_10db_analysis" src="https://github.com/user-attachments/assets/9137d37b-cdd3-4cf1-9c2f-9e06f2ef189a" />

変復調アルゴリズムの詳しい解説は [docs/algorithm.md](docs/algorithm.md) を参照。

## 構成(2 トラック)

| トラック | 場所 | 役割 |
|---|---|---|
| algo | `src/algo/`(Python) | FM ステレオの変調・通信路・復調を NumPy/SciPy でモデル化 |
| hdl  | `src/hdl/`(SystemVerilog) | algo で確立した方式を Tang Nano 9K 向け RTL に実装 |

主要処理パイプライン(送信 → 通信路 → 受信):

```
音声(48k) → MPX(192k) → RF(2.304M) → FM変調 → IQ
   → [AWGN] →
IQ → 直交復調 → MPX(192k) → PLLで38k再生 → マトリクス分離 → 音声(48k)
```

信号設計(レート・帯域)と物理定数の正本は `src/algo/settings.py`、現状の整理は [docs/architecture.md](docs/architecture.md)。

## リポジトリ構成

```
src/algo/   algo: Python DSP モデル(transmitter / channnel / receiver, dsp/, settings.py)
src/hdl/       hdl: SystemVerilog(rtl/ tb/ constraints/)— 規約は src/hdl/README.md
docs/          roadmap / architecture / adr / algorithm
tests/         algo の品質評価(metrics gate)
Makefile       algo・hdl のタスクをラップ
```

## Getting Started

### algo (Python)

前提: [uv](https://docs.astral.sh/uv/) / Python 3.12+。

```bash
make install   # uv sync で依存と本体を導入
make run       # FM 変復調シミュレーションを実行(src/algo/main.py)
make fmt       # ruff format + ruff check --fix
make lint      # ruff check
```

実行すると `outputs/<name>_restored.wav`(復調音声)と `outputs/<name>_analysis.png`(L/R の時間波形・PSD)が生成される。一連のフローは `/sim-algo` スラッシュコマンドでも実行できる。

### hdl (FPGA, Tang Nano 9K)

ツールチェーンは [oss-cad-suite](https://github.com/YosysHQ/oss-cad-suite-build)。シェルで一度だけ有効化する。

```bash
source ./activate-cad.sh
make sim       # verilator でシミュレーション → build/fpga/<TOP>.vcd
make synth     # 合成(synth → pnr → bitstream は依存で連鎖)
make load      # 実機 SRAM に書き込み(揮発 / 確認用)
make fpga-help # FPGA ターゲット一覧
```

別モジュールを対象にするには `make load TOP=fm_receiver` のように `TOP` を渡す。ビルド規約・ピン参照・デバイス値は [src/hdl/README.md](src/hdl/README.md) が正本。一連のフローは `/fpga` スラッシュコマンドでも実行できる。

## ドキュメント

| 内容 | 参照先 |
|---|---|
| アルゴリズム詳細解説(算譜の解説) | [docs/algorithm.md](docs/algorithm.md) |
| 進捗・フェーズ管理 | [docs/roadmap.md](docs/roadmap.md) |
| システム構成・信号設計 | [docs/architecture.md](docs/architecture.md) |
| 設計上の決定(ADR) | [docs/adr/](docs/adr/) |
| HDL ビルド規約・ピン参照 | [src/hdl/README.md](src/hdl/README.md) |
| 開発時の作業ガイド | [CLAUDE.md](CLAUDE.md) |
| 開発ルール | [.claude/rules.md](.claude/rules.md) |

## クレジット・ライセンス

本プロジェクトで使用する音声ファイルには 2 つの由来がある。

### オリジナル楽曲

- **"first_ancem92.wav"**
  - 作曲・制作: mev-null
  - 著作権: © 2026 mev-null. All rights reserved.
  - 概要: ステレオ FM 復調の忠実度を検証するために作曲したオリジナル曲。

### ライセンス

- **コード**: [MIT License](LICENSE)
- **音楽 (first_ancem92.wav)**: [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)
  - (共有は自由だが、クレジット表記が必要であり、商用利用および二次創作は不可。)
