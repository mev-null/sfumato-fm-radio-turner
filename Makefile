UV := uv

.PHONY: all
all: install

.PHONY: install
install:
	@echo "Installing dependencies and project..."
	$(UV) sync

.PHONY: clean-env
clean-env:
	@echo "Removing virtual environment..."
	rm -rf .venv uv.lock

.PHONY: run
run:
	@echo "Running simulation..."
	PYTHONPATH=src $(UV) run python -m algo.main

.PHONY: fmt
fmt:
	@echo "Formatting code..."
	$(UV) run ruff format src
	$(UV) run ruff check --fix src

.PHONY: fmt-check
fmt-check:
	@echo "Checking formatting (non-destructive)..."
	$(UV) run ruff format --check src

.PHONY: lint
lint:
	@echo "Linting code..."
	$(UV) run ruff check src

.PHONY: eval
eval:
	@echo "Evaluating algo quality (metrics gate)..."
	$(UV) run pytest -q

.PHONY: characterize
characterize:
	@echo "Characterizing demod quality -> baseline.json ..."
	PYTHONPATH=src $(UV) run python -m algo.eval.characterize --update

.PHONY: clean
clean:
	@echo "Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.PHONY: help
help:
	@echo "algo(Python DSP モデル):"
	@echo "  make install       uv sync で依存と本体を導入"
	@echo "  make run           送信 → 通信路 → 受信のシミュレーション(outputs/ に結果)"
	@echo "  make eval          品質ゲート(pytest。CI と同じ)"
	@echo "  make characterize  復調品質を再測定し baseline.json を書き換える(意図的操作)"
	@echo "  make fmt           ruff format + ruff check --fix"
	@echo "  make lint          ruff check"
	@echo "  make clean         __pycache__ 等を削除"
	@echo "FPGA スキャフォールド(保留中): make -C src/hdl fpga-help"

# ----------------------------------------------------------------------------
# FPGA(Tang Nano 9K)向けターゲットは src/hdl/Makefile に分離した(保留中の移植スキャフォールド)。
#   make -C src/hdl fpga-help
# ----------------------------------------------------------------------------
