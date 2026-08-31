# CLAUDE.md — sfumato-fm-radio-tuner

FM ステレオ放送の送信〜通信路〜受信を Python/NumPy でモデル化し、復調品質(THD / SINAD / セパレーション)を CI の品質ゲートで測るプロジェクト。**成果物は DSP モデル(`src/algo/`)と評価基盤**。FPGA(Tang Nano 9K)への移植は将来の拡張として保留中(2026-08-31)で、資料は `docs/future/`、コードの足場は `src/hdl/` にある。本ファイルは開発時の作業ガイド(環境・コマンド・規約)を扱う。

各内容の正本は下記のとおり。本ファイルでは正本の内容を繰り返さず、リンクで参照する。

| 内容 | 正本 |
|---|---|
| 思想・哲学(sfumato / 身体性) | [docs/philosophy.md](docs/philosophy.md) |
| 進捗・次にやること | [docs/roadmap.md](docs/roadmap.md) |
| 設計上の決定(ADR) | [docs/adr/](docs/adr/) |
| システム構成・信号設計・評価基盤 | [docs/architecture.md](docs/architecture.md) |
| アルゴリズムの解説 | [docs/algorithm.md](docs/algorithm.md) |
| プロジェクト全体像・成果 | [README.md](README.md)(英語)/ [README.ja.md](README.ja.md) |
| 保留中のハードウェア・トラック | [docs/future/README.md](docs/future/README.md) |
| hdl 固有の規約・ビルド・ピン参照 | [src/hdl/README.md](src/hdl/README.md) |
| 開発時の遵守ルール | [.claude/rules.md](.claude/rules.md) |

方針に関わる決定は ADR が正本。本ファイルでは繰り返さない。

## 構成

- `src/algo/` … Python パッケージ。責務は `radio/`(送信・通信路・受信)、`dsp/`(フィルタ・エンファシス・PLL)、`eval/`(メトリクス・決定論ハーネス・characterize)、`utils/`。物理定数・レート・評価条件・しきい値は `settings.py` が単一の出どころ。
- `tests/` … メトリクスの契約テストと品質ゲート(`make eval`。CI と同じ)。
- `src/hdl/` … 保留中の FPGA スキャフォールド。独立した Makefile を持つ(`make -C src/hdl fpga-help`)。通常の開発では触らない。

## 開発環境

- パッケージ管理は **uv**、Python は **3.12 以上**(`pyproject.toml` で管理)。
- 主要依存: numpy / scipy / matplotlib / soundfile。テストは pytest、フォーマッタ/リンタは **ruff**。
- 入力音源は `inputs/`(gitignore)。無ければ `make run` が合成音を生成する。

### よく使うコマンド

タスクは Makefile でラップ済み(`make help` で一覧)。

```bash
make install       # uv sync で依存と本体を導入
make run           # 送信 → 通信路 → 受信のシミュレーション (src/algo/main.py → outputs/)
make eval          # 品質ゲート(pytest。CI と同じ)
make characterize  # 復調品質を再測定し baseline.json を書き換える(意図的操作。改善を確認したときだけ)
make fmt           # ruff format + ruff check --fix
make lint          # ruff check
```

### プロジェクト用スラッシュコマンド

- `/sim-algo` … モデルを実行し、出力(復調音声・解析グラフ)を確認する一連のフロー。
- `/fpga` … 保留中のハードウェア・トラック用。`src/hdl/` のビルドフロー(sim → synth → pnr → bitstream → load)を各段で確認しながら回す。

## 作業の進め方(規約)

- **作業を始める前に [.claude/rules.md](.claude/rules.md) を読み、記載の遵守事項(禁止/必須)に常に従う。** 不可逆な操作、Git 運用、コーディング、デバッグ方針などの正本は rules.md。本ファイルと矛盾する場合は rules.md を優先する。
- **進捗を動かしたら** [docs/roadmap.md](docs/roadmap.md) を直接更新する。進捗の状態は roadmap が正本。
- **方針に関わる判断**が出たら、コードや roadmap ではなく **新しい ADR を追加**して決める([docs/adr/README.md](docs/adr/README.md) の書き方に従う)。
- **信号設計(レート・帯域・方式)が確定したら** [docs/architecture.md](docs/architecture.md) に反映する。数値は `settings.py` を出どころとし、architecture.md からは参照して重複させない。
- **品質の変更は測定で示す。** アルゴリズムに手を入れたら `make eval` を通し、改善なら `make characterize` で baseline を上げ、その diff を PR に含める。
