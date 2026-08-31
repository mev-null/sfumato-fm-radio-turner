# ============================================================================
#  FPGA flow — Tang Nano 9K (Gowin GW1NR-9C) / oss-cad-suite
#  保留中の移植スキャフォールド(経緯は docs/future/README.md)
# ============================================================================
#  使い方(リポジトリルートから):  make -C src/hdl <target>     例) make -C src/hdl sim
#  ディレクトリ構成(このファイルからの相対パス):
#    rtl/          … 合成対象の SystemVerilog (<TOP>.sv を含む)
#    tb/           … テストベンチ (<TOP>_tb.sv)
#    constraints/  … ピン制約 (tangnano9k.cst)
#    build/        … 生成物(.gitignore の build/ で除外済み)
#  別モジュールを対象にするには:  make -C src/hdl synth TOP=fm_receiver
#  ツールチェーンは事前に有効化しておく:  source src/hdl/activate-cad.sh
# ----------------------------------------------------------------------------
SHELL := /bin/bash

.DEFAULT_GOAL := fpga-help

# oss-cad-suite の場所(別の場所なら: make -C src/hdl synth OSS_CAD_SUITE=/path/to/oss-cad-suite)
OSS_CAD_SUITE ?= $(HOME)/tools/oss-cad-suite
CAD_ENV       := source $(OSS_CAD_SUITE)/environment

# プロジェクト規約
TOP       ?= blink
RTL_DIR   := rtl
TB_DIR    := tb
BUILD     := build
CST       := constraints/tangnano9k.cst

# 合成対象 = rtl/*.sv、シミュレーションは rtl + tb
SYN_SRCS  := $(wildcard $(RTL_DIR)/*.sv)
SIM_SRCS  := $(wildcard $(RTL_DIR)/*.sv) $(wildcard $(TB_DIR)/*.sv)

# Tang Nano 9K 固有値(値の末尾に空白が混入しないよう、コメントは行頭に置く)
# nextpnr-himbaechel 用デバイス文字列
DEVICE    := GW1NR-LV9QN88PC6/I5
# gowin_pack(apicula)用デバイス名
PACK_DEV  := GW1N-9C
# nextpnr-himbaechel 用ファミリ(GW1N-9 系は必須)
FAMILY    := GW1N-9C
# openFPGALoader 用ボード名
BOARD     := tangnano9k

JSON      := $(BUILD)/$(TOP).json
PNR       := $(BUILD)/$(TOP)_pnr.json
BITSTREAM := $(BUILD)/$(TOP).fs
VCD       := $(BUILD)/$(TOP).vcd
# verilator の生成物置き場
OBJ_DIR   := $(BUILD)/obj_dir

# 波形ビューア(gtkwave は macOS で不安定なため surfer を既定。上書き可: make -C src/hdl wave WAVE=gtkwave)
WAVE      ?= surfer

$(BUILD):
	@mkdir -p $(BUILD)

.PHONY: synth
synth: $(JSON)                ## 合成 (SystemVerilog → ネットリスト JSON)
$(JSON): $(SYN_SRCS) | $(BUILD)
	@echo "Synthesis (yosys)..."
	$(CAD_ENV) && yosys -p "read_verilog -sv $(SYN_SRCS); synth_gowin -top $(TOP) -json $@"

.PHONY: pnr
pnr: $(PNR)                   ## 配置配線 (ネットリスト + 制約 → 配線済み JSON)
$(PNR): $(JSON) $(CST)
	@echo "Place & Route (nextpnr-himbaechel)..."
	$(CAD_ENV) && nextpnr-himbaechel \
		--json $(JSON) --write $@ \
		--device "$(DEVICE)" --vopt family=$(FAMILY) --vopt cst=$(CST)

.PHONY: bitstream
bitstream: $(BITSTREAM)       ## ビットストリーム生成 (.fs)
$(BITSTREAM): $(PNR)
	@echo "Pack bitstream (gowin_pack)..."
	$(CAD_ENV) && gowin_pack -d $(PACK_DEV) -o $@ $(PNR)

.PHONY: load
load: $(BITSTREAM)            ## SRAM へ書き込み(電源OFFで消える / 開発中の確認用)
	@echo "Load to SRAM (volatile)..."
	$(CAD_ENV) && openFPGALoader -b $(BOARD) $(BITSTREAM)

.PHONY: flash
flash: $(BITSTREAM)           ## 内蔵フラッシュへ書き込み(電源OFFでも残る)
	@echo "Write to flash (persistent)..."
	$(CAD_ENV) && openFPGALoader -b $(BOARD) -f $(BITSTREAM)

.PHONY: sim
sim: $(SIM_SRCS) | $(BUILD)   ## シミュレーション (verilator --binary、VCD 出力)
	@echo "Simulate: TB=$(TOP)_tb  → VCD=$(VCD)"
	$(CAD_ENV) && verilator --binary --timing --trace -j 0 \
		--top-module $(TOP)_tb --Mdir $(OBJ_DIR) -o $(TOP)_tb \
		$(SIM_SRCS)
	./$(OBJ_DIR)/$(TOP)_tb

.PHONY: wave
wave:                         ## 波形ビューア(surfer)で VCD を開く
	@test -f $(VCD) || { echo "VCD が無い。先に make -C src/hdl sim を実行: src/hdl/$(VCD)"; exit 1; }
	$(WAVE) $(VCD) &

.PHONY: clean-fpga
clean-fpga:                   ## FPGA ビルド成果物を削除
	@echo "Cleaning FPGA build..."
	rm -rf $(BUILD)

.PHONY: fpga-help
fpga-help:                    ## FPGA ターゲット一覧
	@echo "FPGA flow (Tang Nano 9K) — 保留中の移植スキャフォールド。リポジトリルートから:"
	@echo "  source src/hdl/activate-cad.sh   ツールチェーン有効化(このシェルで一度)"
	@echo "  make -C src/hdl synth            合成"
	@echo "  make -C src/hdl pnr              配置配線"
	@echo "  make -C src/hdl bitstream        ビットストリーム生成 (.fs)"
	@echo "  make -C src/hdl load             SRAM へ書き込み(揮発)"
	@echo "  make -C src/hdl flash            フラッシュへ書き込み(永続)"
	@echo "  make -C src/hdl sim              シミュレーション → src/hdl/build/<TOP>.vcd"
	@echo "  make -C src/hdl wave             波形表示"
	@echo "  make -C src/hdl clean-fpga       成果物削除"
	@echo "  例) 別モジュール:  make -C src/hdl load TOP=fm_receiver"
