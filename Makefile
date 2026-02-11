UV := uv

.PHONY: all
all: install

.PHONY: install
install:
	@echo "📦 Installing dependencies and project..."
	$(UV) sync

.PHONY: clean-env
clean-env:
	@echo "🗑️ Removing virtual environment..."
	rm -rf .venv uv.lock

.PHONY: run
run:
	@echo "🚀 Running simulation..."
	$(UV) run src/sfumato/main.py

.PHONY: jupyter
jupyter:
	@echo "📓 Starting Jupyter Lab..."
	$(UV) run jupyter lab

.PHONE: kernel
kernel:
	@echo "activating notebook kernel..."
	$(UV) run python -m ipykernel install --user --name=sfumato --display-name "Python (Sfumato)"

.PHONY: fmt
fmt:
	@echo "🎨 Formatting code..."
	$(UV) run ruff format src notebooks
	$(UV) run ruff check --fix src notebooks

.PHONY: lint
lint:
	@echo "🔍 Linting code..."
	$(UV) run ruff check src notebooks

.PHONY: clean
clean:
	@echo "🧹 Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
