.PHONY: help install extract-climate seed-animals seed-buildings analyze-pilot clean tensorboard progress
.PHONY: inat-obs inat-images inat-all
.PHONY: remote-shell remote-status remote-pull

PYTHON = uv run python
TENSORBOARD_LOGDIR ?= outputs/models
TENSORBOARD_HOST ?= 0.0.0.0
TENSORBOARD_PORT ?= 6006

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

tensorboard: ## Launch TensorBoard on 0.0.0.0:6006
	uv run tensorboard --logdir $(TENSORBOARD_LOGDIR) --host $(TENSORBOARD_HOST) --port $(TENSORBOARD_PORT)

progress: ## Refresh PROGRESS.xml from training outputs
	uv run python scripts/training/update_progress.py

# ── Phase 8: Vision pipeline ──────────────────────────────────────────────

inat-obs: ## Download iNaturalist observation metadata (mammals+birds)
	python3 scripts/extraction/download_inaturalist.py --taxon both --target 500000

inat-obs-mammals: ## Download mammal observations only
	python3 scripts/extraction/download_inaturalist.py --taxon mammals --target 500000

inat-obs-birds: ## Download bird observations only
	python3 scripts/extraction/download_inaturalist.py --taxon birds --target 500000

inat-images: ## Download iNaturalist images (mammals+birds)
	python3 scripts/extraction/download_inaturalist_images.py --taxon both --max-images 500000

inat-images-mammals: ## Download mammal images only
	python3 scripts/extraction/download_inaturalist_images.py --taxon mammals --max-images 500000

inat-images-birds: ## Download bird images only
	python3 scripts/extraction/download_inaturalist_images.py --taxon birds --max-images 500000

inat-all: inat-obs inat-images ## Run full iNaturalist pipeline (obs + images)

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

# ── GPU server (spark-server) ──────────────────────────────────────────────

REMOTE_HOST ?= spark-server
REMOTE_DIR ?= /mnt/wholemilk/bioclimatic-morphology

remote-shell: ## SSH into the GPU server
	ssh $(REMOTE_HOST)

remote-status: ## Show GPU server status (git, GPU, disk, tmux)
	ssh $(REMOTE_HOST) 'cd $(REMOTE_DIR) && echo "== git ==" && git status -sb && git log --oneline -3 && echo "== gpu ==" && nvidia-smi --query-gpu=name,memory.used,utilization.gpu --format=csv && echo "== disk ==" && df -h /mnt/wholemilk | tail -1 && echo "== tmux ==" && (tmux ls || true)'

remote-pull: ## Fast-forward the GPU server to origin/main
	ssh $(REMOTE_HOST) 'cd $(REMOTE_DIR) && git pull --ff-only'
