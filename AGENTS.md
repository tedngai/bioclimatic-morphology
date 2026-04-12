# AGENTS.md — Context for Continuation

## Current Task: DINOv2 fine-tuning (task 8.3)

Climate pairing is **complete**. The training dataset is ready. Next step is building a vision encoder that predicts climate features from animal photos using DINOv2.

## What's Done

### Observation Metadata
- `data/vision/observations_mammals.csv` — 500K rows, 4173 species
- `data/vision/observations_birds.csv` — 500K rows, 7892 species

### Images
- `data/vision/images/mammals/` — 499,441 JPEGs (56GB)
- `data/vision/images/birds/` — 488,102 JPEGs (46GB)
- Named `{observation_id}.jpg`

### Training Dataset (COMPLETE)
- `data/vision/train_all.csv` — **970,147 rows** (308 MB)
- Mammals: 489,465 | Birds: 480,682 | Species: 11,913
- 98%+ have daily climate from NASA POWER (1981-2019)
- Per-taxon files: `data/vision/train_mammals.csv`, `data/vision/train_birds.csv`

### Climate features (columns in train_all.csv)
| Column | Description | Mean | Range |
|---|---|---|---|
| temperature_2m_mean | Daily mean temp (°C) | 15.89 | -42.32 to 41.66 |
| wbt_c | Wet-bulb temp (Stull 2011) | 12.34 | -42.75 to 29.81 |
| vpd_kpa | Vapor pressure deficit | 0.69 | -0.08 to 7.12 |
| diurnal_range_c | T_max - T_min | 10.22 | 0.02 to 29.35 |
| solar_wm2 | Mean hourly solar flux | 209.58 | 0 to 430.60 |

Full column list: `observation_id, image_path, taxon, species, common_name, family, lat, lon, date_str, photo_url, photo_id, temperature_2m_mean/max/min, relative_humidity_2m_mean/max/min, dew_point_2m_mean, wind_speed_10m_mean/max, shortwave_radiation_sum, wbt_c, vpd_kpa, diurnal_range_c, solar_wm2`

### Scripts (data pipeline — all complete)
- `scripts/extraction/download_inaturalist.py` — observation metadata
- `scripts/extraction/download_inaturalist_images.py` — image download
- `scripts/extraction/pair_observations_nasa.py` — NASA POWER daily climate
- `scripts/extraction/pair_observations_climate.py` — DEAD (Open-Meteo)
- `scripts/extraction/pair_observations_worldclim.py` — BACKUP (monthly normals)

## What's Next: DINOv2 Fine-Tuning

### Goal
Train a vision encoder (DINOv2) to predict climate features from animal photos. The hypothesis: animals photographed in different climates will teach the model to recognize bioclimatic signals in images.

### Approach
1. Load pretrained DINOv2 ViT-B/14 (or ViT-L/14 if GPU memory allows)
2. Freeze or partially fine-tune the backbone
3. Add a regression head: embedding → 5 climate targets (wbt_c, vpd_kpa, diurnal_range_c, solar_wm2, temperature_2m_mean)
4. Train with MSE loss (or multi-task weighted loss)
5. Evaluate: per-target R², correlation with true climate

### Setup on GPU machine
```bash
git clone https://github.com/tedngai/bioclimatic-morphology.git
cd bioclimatic-morphology
pip install torch torchvision transformers pandas pillow tqdm
# or: uv sync  (if pyproject.toml has deps)
```

### Training script skeleton (to be written)
- PyTorch Dataset: reads `train_all.csv`, loads JPEG from `data/vision/images/{taxon}/{id}.jpg`
- Apply DINOv2 standard preprocessing (Resize 256, CenterCrop 224, normalize)
- Train/val split: 90/10 by species (stratified, no species leakage)
- Batch size: as large as GPU allows (start 64 for ViT-B)
- LR: 1e-4 for head, 1e-6 for backbone (if fine-tuning)
- Log to wandb or tensorboard

### Key files to write
- `scripts/training/climate_dataset.py` — PyTorch Dataset class
- `scripts/training/train_dinov2.py` — training loop
- `scripts/training/evaluate.py` — metrics and visualization

## Environment
- **Data scripts:** python3 (3.13), pandas, numpy, requests, pyarrow, rasterio
- **Training:** PyTorch + transformers (needs GPU machine)
- **Git:** https://github.com/tedngai/bioclimatic-morphology
- **Disk:** ~829GB free of 1TB (images are ~102GB total)

## Grid / Caching Details
- Observations rounded to 0.5° grid cells
- Mammals: 15,271 grid cells | Birds: 9,292 cells
- Climate cache in `data/vision/climate_cache/{taxon}/` (parquet per cell)
- NASA POWER API: free, no key, daily 1981-present
