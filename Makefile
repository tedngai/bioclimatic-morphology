.PHONY: help install extract-climate seed-animals seed-buildings analyze-pilot clean

PYTHON = uv run python

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Environment ─────────────────────────────────────────────────────────────

install: ## Install all dependencies with uv
	uv sync

install-dev: ## Install with dev dependencies
	uv sync --extra dev

# ── Phase 1: Climate backbone ──────────────────────────────────────────────

extract-climate: ## Extract ERA5 + AlphaEarth data for pilot locations
	$(PYTHON) scripts/extraction/extract_pilot_climate.py

# ── Phase 2-3: Seed pilot data ─────────────────────────────────────────────

seed-animals: ## Create pilot animal features CSV (needs manual coding)
	$(PYTHON) scripts/compilation/seed_pilot_animals.py

seed-buildings: ## Create pilot building features CSV (needs manual coding)
	$(PYTHON) scripts/compilation/seed_pilot_buildings.py

seed-all: seed-animals seed-buildings ## Seed both animal and building CSVs

# ── Phase 4: Analysis ──────────────────────────────────────────────────────

analyze-pilot: ## Run pilot analysis (requires coded data)
	$(PYTHON) scripts/analysis/run_pilot_analysis.py

# ── Full pilot pipeline ────────────────────────────────────────────────────

pilot: extract-climate seed-all ## Run full pilot data extraction + seeding
	@echo ""
	@echo "Pilot data seeded. Next steps:"
	@echo "  1. Code animal thermoregulatory features in data/pilot/animal_features.csv"
	@echo "  2. Code building design features in data/pilot/building_features.csv"
	@echo "  3. Run: make analyze-pilot"

# ── Notebooks ──────────────────────────────────────────────────────────────

lab: ## Launch JupyterLab
	uv run jupyter lab --no-browser

# ── Utilities ──────────────────────────────────────────────────────────────

lint: ## Run linter
	uv run ruff check src/ scripts/

format: ## Auto-format code
	uv run ruff format src/ scripts/

clean: ## Remove generated outputs (keeps raw data)
	rm -rf outputs/models/*.pt outputs/models/*.pkl
	rm -rf outputs/figures/*.png outputs/figures/*.pdf
	rm -f data/pilot/animals_merged.csv data/pilot/buildings_merged.csv
	rm -f outputs/pilot_strategy_correspondence.csv

clean-all: clean ## Remove all generated data including pilot CSVs
	rm -f data/pilot/*.csv
	rm -rf data/processed/*.csv
