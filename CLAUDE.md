# CLAUDE.md — sfumato-fm-radio-turner

FPGA で動かす FM ラジオ受信機。**algo**(Python/NumPy による FM 変復調アルゴリズムのモデリング・シミュレーション)で方式を確立し、確立した方式を **hdl**(SystemVerilog / Tang Nano 9K)へ落とし込む二本立てのプロジェクト。本ファイルは開発時の作業ガイド(環境・コマンド・規約)を扱う。

各内容の正本は下記のとおり。本ファイルでは正本の内容を繰り返さず、リンクで参照する。

| 内容 | 正本 |
|---|---|
| 思想・哲学(sfumato / 身体性 / 思考する身体) | [docs/philosophy.md](docs/philosophy.md) |
| 進捗・フェーズ管理 | [docs/roadmap.md](docs/roadmap.md) |
| 設計上の決定(ADR) | [docs/adr/](docs/adr/) |
| システム構成・信号設計(algo / hdl) | [docs/architecture.md](docs/architecture.md) |
| HDL 固有のビルド規約・ピン参照 | [src/hdl/README.md](src/hdl/README.md) |
| プロジェクト全体像・成果(算譜の解説) | [README.md](README.md) |
| 開発時の遵守ルール | [.claude/rules.md](.claude/rules.md) |

方針に関わる決定は ADR が正本。本ファイルでは繰り返さない。

## 二本立ての構成

- **algo**: `src/algo/`(Python パッケージ)。FM ステレオの変調・通信路・復調を NumPy/SciPy でモデル化する。物理定数・レートは `src/algo/settings.py` が単一の出どころ。
- **hdl**: `src/hdl/`(SystemVerilog)。algo で確立した方式を Tang Nano 9K(Gowin GW1NR-9C)向け RTL に実装する。ビルド規約・ピン参照は [src/hdl/README.md](src/hdl/README.md) が正本。
- 両者は独立にビルド・テストできる。algo を「先に正しい方式を見つける場」、hdl を「それをハードに落とす場」として扱い、algo で確定した数値・方式を hdl 実装の根拠にする。

## 開発環境

### algo(Python)

- パッケージ管理は **uv**、Python は **3.12 以上**(`pyproject.toml` で管理)。
- 主要依存: numpy / scipy / matplotlib / soundfile。
- フォーマッタ/リンタは **ruff**。
- セットアップ手順のチェックリストは [docs/roadmap.md](docs/roadmap.md) を参照。

### hdl(FPGA / Tang Nano 9K)

- ツールチェーンは **oss-cad-suite**(yosys / nextpnr-himbaechel / gowin_pack(apicula) / openFPGALoader)。既定の場所は `~/tools/oss-cad-suite`。
- このシェルで一度だけ有効化する: `source ./activate-cad.sh`。
- デバイス値・ピン参照は [src/hdl/README.md](src/hdl/README.md) に記載(Makefile に設定済み)。

### よく使うコマンド

タスクは Makefile でラップ済み。

```bash
# --- algo (Python) ---
make install   # uv sync で依存と本体を導入
make run       # FM 変復調シミュレーションを実行 (src/algo/main.py)
make fmt       # ruff format + ruff check --fix
make lint      # ruff check

# --- hdl (FPGA, 先に source ./activate-cad.sh) ---
make sim       # verilator でシミュレーション → build/fpga/<TOP>.vcd
make wave      # surfer で波形を開く
make synth     # 合成 (synth→pnr→bitstream は依存で連鎖)
make load      # 実機 SRAM に書き込み(揮発 / 確認用)
make flash     # 内蔵フラッシュに書き込み(永続)
make fpga-help # FPGA ターゲット一覧
```

別モジュールを対象にするには `make load TOP=fm_receiver` のように `TOP` を渡す。

### プロジェクト用スラッシュコマンド

- `/sim-algo` … algo(Python DSP)モデルを実行し、出力(復調音声・解析グラフ)を確認する一連のフロー。
- `/fpga` … hdl のビルドフロー(sim → synth → pnr → bitstream → load)を各段で確認しながら回す。

## 作業の進め方(規約)

- **進捗を動かしたら** [docs/roadmap.md](docs/roadmap.md) を直接更新する。進捗の状態は roadmap が正本。
- **方針に関わる判断**が出たら、コードや roadmap ではなく **新しい ADR を追加**して決める([docs/adr/README.md](docs/adr/README.md) の書き方に従う)。
- **信号設計(レート・帯域・方式)や algo↔hdl の対応が確定したら** architecture.md に反映する。algo の数値は `settings.py`、hdl の規約は `src/hdl/README.md` を出どころとし、architecture.md からはそれらを参照して重複させない。
