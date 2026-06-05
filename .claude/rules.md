# 開発ルール

本リポジトリで作業する際に常に従うルール。CLAUDE.md から参照される。
各項目は「禁止/必須」を明示する遵守事項であり、背景や設計判断は ADR・architecture.md を正本とする。

このプロジェクトは **algo**(Python DSP モデル: `src/algo/`)と **hdl**(SystemVerilog / Tang Nano 9K: `src/hdl/`)の 2 トラック構成。両者に共通するルールに加え、章ごとに固有の注意を記す。

## 1. 危険・不可逆な操作(プロジェクト固有)

- **実機書き込み**(`make load` / `make flash`)を無許可で実行しない。`flash` は内蔵フラッシュを永続的に書き換えるため特に注意する。
- 合成・配置配線・ビットストリーム生成(`make synth` / `pnr` / `bitstream`)はファイル生成のみだが、実機反映を伴う操作は利用者の明示指示があるときのみ実行する。

## 2. Git 運用

- 無許可でコミットしない。
- `main` に直接 push しない。必ずブランチを切り、PR を作成する。
- author は `mev-null <190558379+mev-null@users.noreply.github.com>`。**`Co-Authored-By` 行は付けない**。

### コミットメッセージ

`<type>: <要約>` の形式で書く(Conventional Commits)。type は以下を使う。

- `feat:` 機能追加
- `fix:` バグ修正
- `docs:` ドキュメント変更
- `test:` テストの追加・修正
- `refac:` 挙動を変えないコード整理
- `chore:` ビルド・依存・設定など雑務

## 3. コーディング

- コメント・ドキュメントは**日本語**で書く(リポジトリ全体の既存方針に合わせる)。
- **algo (Python)**: ruff に従う。コミット前に `make fmt`(整形 + 自動修正)と `make lint` を通す。物理定数・サンプリングレートは `src/algo/settings.py` に集約し、各モジュールへハードコードしない。
- **hdl (SystemVerilog)**: ファイル名 = トップモジュール名 = `TOP` 変数 を一致させる(Makefile の規約)。テストベンチは `<TOP>_tb.sv`、モジュール名も `<TOP>_tb`。ピン制約は `src/hdl/constraints/tangnano9k.cst`。詳細は [src/hdl/README.md](../src/hdl/README.md)。

## 4. デバッグ

- ソースコード単体で原因を結論づけない。必ず実際の動作データを根拠に推論する。
  - **algo**: 出力波形・PSD・復調音声(`outputs/`)、中間信号の可視化を根拠にする。
  - **hdl**: シミュレーション波形(`make sim` → `make wave`、`build/fpga/<TOP>.vcd`)を根拠にする。RTL を読むだけで断定しない。

## 5. 方針と実装

- 方針を決定してから実装する。勝手に plan mode を抜けない。
- テストカバレッジ(algo: シミュレーションでの検証、hdl: テストベンチでの検証)までを「方針完了」の範囲に含める。
- **algo で確立していない方式を hdl に実装しない。** ハードへ落とす前に、algo モデルで数値・挙動を確認することを原則とする。

## 6. 不明点の扱い

- 仕様・優先度などで曖昧さが残る場合、勝手に仮定して進めず利用者に確認する。

## 7. 破壊的操作の事前確認

- ファイル削除・上書き、`git reset --hard`、force push、実機 `flash` など取り消し困難な操作は、実行前に必ず確認する。

## 8. ドキュメント更新の徹底

- 進捗を動かしたら [docs/roadmap.md](../docs/roadmap.md) を更新する。
- 方針に関わる判断が出たら [docs/adr/](../docs/adr/) に新しい ADR を追加する。
- 信号設計(レート・帯域・方式)や algo↔hdl の対応が確定したら [docs/architecture.md](../docs/architecture.md) に反映する。

## 9. 文章・ドキュメントの語調

- 業務技術文書のトーンで書く。簡潔・断定・常体。
- 問いかけ調(「〜は?」「どこを見ればいい?」)を見出しや項目名に使わない。体言止めの名詞句にする。
- 口語語彙(「楽」「いちばん」「やさしい」「OK」など)を避け、技術文書の語彙に置換する。

## 10. 開発スタイル

- 1ファイル=1責務。重複は単一の出どころに集約する(algo の定数は `settings.py`、hdl の規約は `src/hdl/README.md`)。

## 11. 事実の根拠(記憶で断定しない)

- 仕様・型番・API・バージョンなどを**記憶で断定しない**。
- まず [docs/architecture.md](../docs/architecture.md) / `settings.py` / [src/hdl/README.md](../src/hdl/README.md) など一次情報を参照する。記載がない/疑義があるときは、公式ドキュメント(`.claude/settings.json` の allowlist 参照)を確認し、必要なら architecture.md を更新する。

## 12. 学習者主体(コードは本人が書く)

- 利用者は本プロジェクトのコア、特に **HDL を自分で書いて学ぶ**ことを目的としている。RTL やアルゴリズムのコア実装を先回りして書かない。求められたときに方針・観点・参考情報を提供し、実装は本人に委ねる。
