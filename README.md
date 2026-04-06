# Data-Driven Bioclimatic Morphology

Learning thermoregulatory design from millions of geotagged images of animals and buildings.

## What This Project Does

Trains a vision model to predict climate-appropriate thermal performance from photographs. Every geotagged photo of an animal or building is implicitly labeled with its climate. A model that learns to predict climate from images will discover thermoregulatory features — large ears, thick fur, windcatchers, stilt construction — without manual annotation.

The result is a design evaluation tool: **upload a photo of a building, get quantitative thermal performance metrics benchmarked against both biological and vernacular architectural solutions for that climate.**

## Approach

```
Self-supervised pre-training (1.5M+ geotagged images):
  iNaturalist animal photo → DINOv2 encoder → predict climate at geolocation
  Mapillary building photo → DINOv2 encoder → predict climate at geolocation

Fine-tuning (595 labeled samples from Phase 1-5):
  Pre-trained encoder → predict U_eff, C_th, D_reg, strategy fractions

Inference:
  Photo of building → thermal metrics → comparison with biological benchmark
```

## Current State

| Asset | Status |
|---|---|
| Labeled dataset | 425 animals + 170 buildings with thermal metrics (fine-tuning data) |
| 4-axis ontology | Collection, Transfer, Storage, Regulation (evaluation framework) |
| Physics metrics | U_eff (W/m²K), C_th (kJ/K/m²), D_reg (dimensionless) |
| Vision pipeline | Implementation planned (Phase 8) |
| Data sources identified | iNaturalist (190M), Mapillary (~2B), Open-Meteo, AlphaEarth |

## Key Finding (Phase 1-5)

Animal pelage and building envelopes occupy the same thermal conductance range (0.5-5 W/m²K). A reindeer's winter coat and an Icelandic turf wall are physically equivalent thermal envelopes. This finding provides the biological benchmark that the vision model's predictions are evaluated against.

## Project Structure

```
bioclimatic-morphology/
├── data/
│   ├── processed/                 # 425 animals + 170 buildings (fine-tuning labels)
│   ├── vision/                    # Image-climate paired datasets (Phase 8)
│   ├── pilot/                     # Original 5-zone pilot
│   └── raw/era5/                  # Climate CSVs
├── src/
│   ├── climate/                   # psychrometrics.py, era5.py, alphaearth.py
│   ├── animals/                   # schema.py, traits.py
│   ├── buildings/                 # schema.py
│   ├── ml/                        # baselines.py, strategy_alignment.py
│   └── utils/                     # config.py
├── scripts/                       # Data extraction and analysis pipelines
├── docs/
│   ├── phase7_restructure.md      # Continuous psychrometric plan (superseded)
│   └── phase8_vision.md           # Vision-based implementation plan (current)
├── backup/phase1-5/               # Archived: manuscript, figures, models, plans
├── outputs/                       # Current phase outputs
├── project_scope.md               # Status and task checklist
└── research-brief.md              # Original research design
```

## Key Documents

| Document | Purpose |
|---|---|
| `docs/phase8_vision.md` | Full implementation plan for vision approach |
| `project_scope.md` | Current status, task checklist, project evolution |
| `research-brief.md` | Original research design |
| `backup/phase1-5/reports/full_manuscript.md` | 32k-word draft from tabular phase |

## Getting Started

```bash
uv sync                    # Install dependencies
source .env                # Load API keys
cat docs/phase8_vision.md  # Read the implementation plan
```

## Dependencies

Core: pandas, numpy, scipy, matplotlib, scikit-learn, xgboost, torch, torchvision
Climate: earthengine-api, httpx, psychrolib, xarray
Vision: DINOv2 (via torch.hub), Pillow
Data: requests (iNaturalist API), httpx (Open-Meteo)
