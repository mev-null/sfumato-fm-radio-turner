# /fpga — Tang Nano 9K ビルドフロー

hdl(`src/hdl/`)の SystemVerilog を、シミュレーション → 合成 → 配置配線 → ビットストリーム → 実機書き込みの順に、各段で確認しながら回す。手早く回すだけなら個別の `make` ターゲットを直接叩いてよい。

対象モジュールは `TOP` 変数で指定する(既定 `TOP=blink`)。別モジュールなら各コマンドに `TOP=fm_receiver` のように渡す。

## 前提

- 一度だけツールチェーンを有効化する: `source ./activate-cad.sh`(このシェルで)。
- ピン制約 `src/hdl/constraints/tangnano9k.cst` のポート名がトップモジュールのポートと一致していること。

## 手順

1. **シミュレーション**: `make sim TOP=<top>`
   - テストベンチ `<top>_tb.sv` が `build/fpga/<top>.vcd` を出力する。波形は `make wave TOP=<top>`。
   - 期待波形と合わない場合はここで止め、RTL/TB を見直す(実機へ進まない)。
2. **合成**: `make synth TOP=<top>`
   - yosys のエラー・致命的 warning が出たら止める。`synth → pnr → bitstream` は依存で連鎖する。
3. **配置配線 + ビットストリーム**: `make bitstream TOP=<top>`
   - nextpnr のタイミング/配線エラー、ピン未割当が出たら止め、`.cst` を見直す。
4. **実機書き込み(要明示許可)**: `make load TOP=<top>`(揮発、確認用)
   - 永続化が必要なときのみ `make flash TOP=<top>`。**`flash` は内蔵フラッシュを書き換えるため、利用者の明示指示があるときだけ実行する。**

## 注意

- シミュレーションが期待どおりでない RTL を実機に書き込まない。
- 実クロック 27 MHz のままだと点滅確認に時間がかかる。分周数を `parameter` 化し、TB では小さい値を渡す(詳細は [src/hdl/README.md](../../src/hdl/README.md))。
- 成果物は `build/fpga/`(gitignore 済み)。
