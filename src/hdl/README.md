# HDL (Tang Nano 9K / Gowin GW1NR-9C)

> **保留中のスキャフォールド(2026-08-31)**: 本プロジェクトの成果物は Python/NumPy の DSP モデル(`src/algo/`)であり、FPGA 移植は将来の拡張。経緯・計画・ハードウェア ADR は [docs/future/](../../docs/future/README.md)。
> ビルドは本ディレクトリの `Makefile` で行い、リポジトリルートから `make -C src/hdl <target>` を叩く(一覧: `make -C src/hdl fpga-help`)。

SystemVerilog で書く RTL とテストベンチ、ピン制約を置く場所。現状は疎通用の `blink`(ランニングライト)のみ。

## ディレクトリ構成

```
src/hdl/
├── Makefile         # FPGA フロー(yosys → nextpnr-himbaechel → gowin_pack → openFPGALoader / verilator)
├── activate-cad.sh  # oss-cad-suite をシェルで有効化(source して使う)
├── rtl/             # 合成対象の SystemVerilog。トップは <TOP>.sv(既定 TOP=blink)
├── tb/              # テストベンチ。<TOP>_tb.sv(モジュール名も <TOP>_tb)
├── constraints/     # ピン制約 tangnano9k.cst
└── build/           # 生成物(gitignore 済み。make -C src/hdl clean-fpga で削除)
```

- `make` が拾うファイル名の規約: トップモジュール名 = ファイル名 = `TOP` 変数。
- `rtl/` は合成・シミュレーション両方、`tb/` はシミュレーションのみで使われる。

## 開発フロー

ツールチェーンは [oss-cad-suite](https://github.com/YosysHQ/oss-cad-suite-build)(既定 `~/tools/oss-cad-suite`、別の場所なら `OSS_CAD_SUITE` で上書き)。最初に 1 度だけ有効化する(このシェルで):

```bash
source src/hdl/activate-cad.sh
```

以降はリポジトリルートから:

```bash
make -C src/hdl sim        # verilator でシミュレーション → src/hdl/build/<TOP>.vcd
make -C src/hdl wave       # surfer で波形を開く
make -C src/hdl synth      # 合成(synth → pnr → bitstream は依存で連鎖)
make -C src/hdl load       # 実機 SRAM に書き込み(電源OFFで消える / 確認用)
make -C src/hdl flash      # 内蔵フラッシュに書き込み(永続)
make -C src/hdl fpga-help  # ターゲット一覧(ツールチェーン不要)
```

別モジュールを対象にするには `make -C src/hdl load TOP=fm_receiver` のように `TOP` を渡す。
`/fpga` スラッシュコマンドは上記を各段で確認しながら回す手順。

## 規約(hdl 固有)

- ファイル名 = トップモジュール名 = `TOP` 変数(Makefile の規約)。テストベンチは `<TOP>_tb.sv`、モジュール名も `<TOP>_tb`。ピン制約は `constraints/tangnano9k.cst`。
- **実機書き込み**(`load` / `flash`)は利用者の明示指示があるときのみ実行する。`flash` は内蔵フラッシュを永続的に書き換えるため特に注意する。合成・配置配線・ビットストリーム生成はファイル生成のみ。
- デバッグはシミュレーション波形(`sim` → `wave`)を根拠にする。RTL を読むだけで断定しない。
- **モデル(`src/algo/`)で確立していない方式を RTL に実装しない。** 数値・挙動はモデルで確認してから移す。合格基準はモデルと同じメトリクス(`src/algo/eval/metrics.py`)。
- テストベンチでの検証までを「実装完了」の範囲に含める。
- RTL のコア実装は利用者本人が書く(学習目的)。支援側は方針・観点・参考情報の提供に留める。
- コメント・ドキュメントは日本語。

## Tang Nano 9K ピン参照(`constraints/tangnano9k.cst` 記述用)

| 信号 | ピン | 備考 |
|------|------|------|
| クロック | 52 | 27 MHz オンボード水晶 |
| リセットボタン S1 | 4 | 押すと L(負論理) |
| ボタン S2 | 3 | |
| LED0〜LED5 | 10, 11, 13, 14, 15, 16 | **アクティブLow**(0 で点灯) |

`.cst` の書式(apicula/Gowin 形式。`"..."` 内はトップモジュールのポート名と一致させる):

```
IO_LOC "clk" 52;
IO_PORT "clk" PULL_MODE=UP;
IO_LOC "led[0]" 10;
IO_PORT "led[0]" PULL_MODE=NONE DRIVE=8;
```

## テストベンチの波形出力

`make -C src/hdl wave` は `src/hdl/build/<TOP>.vcd` を開く。シミュレーションのバイナリは `src/hdl` をカレントとして実行されるので、TB では `build/` 相対で指定すると噛み合う:

```systemverilog
initial begin
  $dumpfile("build/blink.vcd");
  $dumpvars(0, blink_tb);
end
```

実クロック 27 MHz のままだとシミュレーションで点滅が見えるまで時間がかかる。
分周数を `parameter` にしておき、TB では小さい値を渡すのが定石。

シミュレータは **verilator**(`--binary --timing --trace`)。`#delay` は `--timing`、
`$dumpfile`/`$dumpvars` による VCD 出力は `--trace` で有効になる(いずれも Makefile で指定済み)。
verilator は lint が厳格なため、未接続信号・幅不一致などの warning は TB/RTL 側で解消しておく。

## デバイス値(参考。Makefile に設定済み)

| 用途 | 値 |
|------|-----|
| nextpnr-himbaechel `--device` | `GW1NR-LV9QN88PC6/I5` |
| gowin_pack `-d` (apicula) | `GW1N-9C` |
| openFPGALoader `-b` | `tangnano9k` |
