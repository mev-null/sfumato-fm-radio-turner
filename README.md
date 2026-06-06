# sfumato-fm-radio-turner

> FPGA で動かす FM ステレオラジオ受信機。Python/NumPy で変復調方式を確立し(**algo**)、Tang Nano 9K 向け SystemVerilog に落とし込む(**hdl**)2 トラック構成のプロジェクト。

<img width="2811" height="853" alt="sfumato-radio-v1-0" src="https://github.com/user-attachments/assets/dd557f31-7457-422a-b91d-ca37e6aa2c50" />

[![CI](https://github.com/mev-null/sfumato-fm-radio-turner/actions/workflows/ci.yml/badge.svg)](https://github.com/mev-null/sfumato-fm-radio-turner/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)

FM ステレオ放送の送信〜通信路〜受信を丸ごとソフトウェアでモデル化して方式を確立し(**algo** / Python)、その方式を Tang Nano 9K(Gowin GW1NR-9C)へ実装する(**hdl** / SystemVerilog)。

## デモ

実ステレオ音楽を**製品スペック水準**で復調できる。品質は決定論パイプライン + ゲート(`make eval`)で定量評価し、市販チューナ(Sony ST-5130)スペックを目標に置く:

| メトリクス | 現状 | 目標(Sony) | 状態 |
|---|---|---|---|
| THD(全高調波歪み) | 0.0072% | ≤ 0.3% | ✅ 達成 |
| セパレーション(L-R 分離) | 45.0 dB | ≥ 42 dB | ✅ 達成 |
| SINAD(信号対雑音+歪み) | 66.8 dB | ≥ 75 dB | ⏳ 追跡中 |

評価条件は 1kHz・SNR 40dB・シード固定。実ステレオ音楽でも Side(L−R)成分の入出力相関 **0.986**。
方式と数値の根拠は ADR([005](docs/adr/adr-005-demod-quality-gate.md) / [006](docs/adr/adr-006-receiver-filter-fir-iir.md) / [007](docs/adr/adr-007-stereo-separation.md))、アルゴリズムの解説は [docs/algorithm.md](docs/algorithm.md)。

https://github.com/user-attachments/assets/f829db6a-4b2d-4762-8efc-568c4f685ed2

**復調音声(ステレオ音楽)**: [原曲](https://github.com/user-attachments/files/25324970/first_ancem92.wav) → [復調後](https://github.com/user-attachments/files/28670715/first_ancem92.wav)

<img width="1400" height="1000" alt="first_ancem92_analysis" src="https://github.com/user-attachments/assets/a0f4a1f1-e2b0-4021-9e59-ff494015a0eb" />

## 仕組み

| トラック | 場所 | 役割 |
|---|---|---|
| algo | `src/algo/`(Python) | FM ステレオの変調・通信路・復調を NumPy/SciPy でモデル化 |
| hdl  | `src/hdl/`(SystemVerilog) | algo で確立した方式を Tang Nano 9K 向け RTL に実装 |

```
音声(48k) → MPX(192k) → RF(2.304M) → FM変調 → IQ
   → [AWGN] →
IQ → 直交復調 → MPX(192k) → PLLで38k再生 → マトリクス分離 → 音声(48k)
```

レート・帯域・物理定数の正本は `src/algo/settings.py`、構成の整理は [docs/architecture.md](docs/architecture.md)。

## Getting Started

### algo (Python)

前提: [uv](https://docs.astral.sh/uv/) / Python 3.12+。

```bash
make install   # uv sync で依存と本体を導入
make run       # FM 変復調シミュレーションを実行
make fmt       # ruff format + ruff check --fix
make lint      # ruff check
make eval      # 品質ゲート(pytest)
```

入力音源は `inputs/`(既定 `inputs/first_ancem92.wav`、`settings.INPUT_FILE`)に置く。`make run` で `outputs/` に復調音声(`*_restored.wav`)と解析グラフ(`*_analysis.png`:時間波形・残差・PSD)が出る。`/sim-algo` でも実行できる。

### hdl (FPGA, Tang Nano 9K)

ツールチェーンは [oss-cad-suite](https://github.com/YosysHQ/oss-cad-suite-build)。シェルで一度だけ有効化する。

```bash
source ./activate-cad.sh
make sim       # verilator でシミュレーション → build/fpga/<TOP>.vcd
make synth     # 合成(synth → pnr → bitstream は依存で連鎖)
make load      # 実機 SRAM に書き込み(揮発 / 確認用)
make fpga-help # FPGA ターゲット一覧
```

別モジュールは `make load TOP=fm_receiver` のように `TOP` を渡す。ビルド規約・ピン参照・デバイス値は [src/hdl/README.md](src/hdl/README.md) が正本。`/fpga` でも実行できる。

## リポジトリ構成

```
src/algo/   algo: Python DSP モデル(transmitter / channel / receiver, dsp/, eval/, settings.py)
src/hdl/    hdl: SystemVerilog(rtl/ tb/ constraints/)— 規約は src/hdl/README.md
docs/       roadmap / architecture / adr / algorithm
tests/      algo の品質評価(metrics gate)
inputs/     入力音源(wav。gitignore=ローカル資産)
outputs/    make run の生成物(復調音声・解析グラフ。gitignore)
```

## ドキュメント

| 内容 | 参照先 |
|---|---|
| アルゴリズム詳細解説(算譜の解説) | [docs/algorithm.md](docs/algorithm.md) |
| 進捗・フェーズ管理 | [docs/roadmap.md](docs/roadmap.md) |
| システム構成・信号設計 | [docs/architecture.md](docs/architecture.md) |
| 設計上の決定(ADR) | [docs/adr/](docs/adr/) |
| HDL ビルド規約・ピン参照 | [src/hdl/README.md](src/hdl/README.md) |
| 開発時の作業ガイド / 開発ルール | [CLAUDE.md](CLAUDE.md) / [.claude/rules.md](.claude/rules.md) |

## クレジット・ライセンス

- **"first_ancem92.wav"** — ステレオ FM 復調の忠実度を検証するために作曲したオリジナル曲。
  - 作曲・制作: mev-null © 2026
  - ライセンス: [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)(共有自由・クレジット必須・商用/二次創作は不可)
- **コード**: [MIT License](LICENSE)
