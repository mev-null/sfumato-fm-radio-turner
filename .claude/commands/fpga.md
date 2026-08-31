# /fpga — Tang Nano 9K ビルドフロー(保留中のハードウェア・トラック)

FPGA 移植は保留中(2026-08-31、経緯は [docs/future/README.md](../../docs/future/README.md))。本コマンドは `src/hdl/` のスキャフォールドを動かすときだけ使う。通常の開発は `/sim-algo` と `make eval`。

hdl(`src/hdl/`)の SystemVerilog を、シミュレーション → 合成 → 配置配線 → ビットストリーム → 実機書き込みの順に、各段で確認しながら回す。ビルドは `src/hdl/Makefile` で、リポジトリルートから `make -C src/hdl <target>` を叩く。手早く回すだけなら個別のターゲットを直接叩いてよい。

対象モジュールは `TOP` 変数で指定する(既定 `TOP=blink`)。別モジュールなら各コマンドに `TOP=fm_receiver` のように渡す。

## 前提

- 一度だけツールチェーンを有効化する: `source src/hdl/activate-cad.sh`(このシェルで)。
- ピン制約 `src/hdl/constraints/tangnano9k.cst` のポート名がトップモジュールのポートと一致していること。
- 規約(ファイル名 = トップモジュール名 = `TOP`、テストベンチ名など)は [src/hdl/README.md](../../src/hdl/README.md) の「規約」を参照。

## 手順

1. **シミュレーション**: `make -C src/hdl sim TOP=<top>`
   - テストベンチ `<top>_tb.sv` が `src/hdl/build/<top>.vcd` を出力する。波形は `make -C src/hdl wave TOP=<top>`。
   - 期待波形と合わない場合はここで止め、RTL/TB を見直す(実機へ進まない)。
2. **合成**: `make -C src/hdl synth TOP=<top>`
   - yosys のエラー・致命的 warning が出たら止める。`synth → pnr → bitstream` は依存で連鎖する。
3. **配置配線 + ビットストリーム**: `make -C src/hdl bitstream TOP=<top>`
   - nextpnr のタイミング/配線エラー、ピン未割当が出たら止め、`.cst` を見直す。
4. **実機書き込み(要明示許可)**: `make -C src/hdl load TOP=<top>`(揮発、確認用)
   - 永続化が必要なときのみ `make -C src/hdl flash TOP=<top>`。**`flash` は内蔵フラッシュを書き換えるため、利用者の明示指示があるときだけ実行する。**

## 注意

- シミュレーションが期待どおりでない RTL を実機に書き込まない。
- モデル(`src/algo/`)で確立していない方式を RTL に実装しない。
- 実クロック 27 MHz のままだと点滅確認に時間がかかる。分周数を `parameter` 化し、TB では小さい値を渡す(詳細は [src/hdl/README.md](../../src/hdl/README.md))。
- 成果物は `src/hdl/build/`(gitignore 済み)。
