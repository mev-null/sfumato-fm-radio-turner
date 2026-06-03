# HDL (Tang Nano 9K / Gowin GW1NR-9C)

SystemVerilog で書く RTL とテストベンチ、ピン制約を置く場所。
ビルドはリポジトリルートの `Makefile`（FPGA セクション)から行う。

## ディレクトリ構成

```
src/hdl/
├── rtl/          # 合成対象の SystemVerilog。トップは <TOP>.sv（既定 TOP=blink）
├── tb/           # テストベンチ。<TOP>_tb.sv（モジュール名も <TOP>_tb）
└── constraints/  # ピン制約 tangnano9k.cst
```

- `make` が拾うファイル名の規約：トップモジュール名 = ファイル名 = `TOP` 変数。
- `rtl/` は合成・シミュレーション両方、`tb/` はシミュレーションのみで使われる。

## 開発フロー

最初に1度だけツールチェーンを有効化（このシェルで)：

```bash
source ./activate-cad.sh
```

以降はルートで：

```bash
make sim      # verilator でシミュレーション → build/fpga/<TOP>.vcd
make wave     # surfer で波形を開く
make load     # 実機 SRAM に書き込み(電源OFFで消える / 確認用)
make flash    # 内蔵フラッシュに書き込み(永続)
make fpga-help # ターゲット一覧
```

`synth → pnr → bitstream` は依存関係で自動連鎖する。
別モジュールを対象にするには `make load TOP=fm_receiver` のように `TOP` を渡す。
成果物は `build/fpga/`（gitignore 済み)。

## Tang Nano 9K ピン参照（`constraints/tangnano9k.cst` 記述用)

| 信号 | ピン | 備考 |
|------|------|------|
| クロック | 52 | 27 MHz オンボード水晶 |
| リセットボタン S1 | 4 | 押すと L（負論理) |
| ボタン S2 | 3 | |
| LED0〜LED5 | 10, 11, 13, 14, 15, 16 | **アクティブLow**（0 で点灯) |

`.cst` の書式（apicula/Gowin 形式。`"..."` 内はトップモジュールのポート名と一致させる)：

```
IO_LOC "clk" 52;
IO_PORT "clk" PULL_MODE=UP;
IO_LOC "led[0]" 10;
IO_PORT "led[0]" PULL_MODE=NONE DRIVE=8;
```

## テストベンチの波形出力

`make wave` は `build/fpga/<TOP>.vcd` を開くので、TB で次を指定すると噛み合う：

```systemverilog
initial begin
  $dumpfile("build/fpga/blink.vcd");
  $dumpvars(0, blink_tb);
end
```

実クロック 27 MHz のままだとシミュレーションで点滅が見えるまで時間がかかる。
分周数を `parameter` にしておき、TB では小さい値を渡すのが定石。

シミュレータは **verilator**(`--binary --timing --trace`)。`#delay` は `--timing`、
`$dumpfile`/`$dumpvars` による VCD 出力は `--trace` で有効になる(いずれも Makefile で指定済み)。
verilator は lint が厳格なため、未接続信号・幅不一致などの warning は TB/RTL 側で解消しておく。

## デバイス値（参考。Makefile に設定済み)

| 用途 | 値 |
|------|-----|
| nextpnr-himbaechel `--device` | `GW1NR-LV9QN88PC6/I5` |
| gowin_pack `-d` (apicula) | `GW1N-9C` |
| openFPGALoader `-b` | `tangnano9k` |
