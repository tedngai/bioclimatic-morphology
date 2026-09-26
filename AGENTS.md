# AGENTS.md — Context for Continuation

## Current Task: Baseline assessment + per-target eval

Baseline DINOv2 climate training is **complete** (two 10-epoch runs). Val mean R² plateaued at ~0.42. The immediate next step is per-target evaluation (which of the 5 climate vars the model actually learns), then deciding the scientific direction (environment-from-photos vs. morphology). See "Assessment & Plan" below.

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

## Current Training Status

### Training code (implemented)
- `scripts/training/climate_dataset.py` — PyTorch dataset, split helpers, target normalization, DINO-compatible transforms
- `scripts/training/train_dinov2.py` — end-to-end training loop, checkpointing, TensorBoard logging, configurable dataloader knobs
- `scripts/training/evaluate.py` — checkpoint evaluation on train or validation split
- `scripts/training/profile_dinov2.py` — pipeline profiler for dataloader wait vs GPU compute timing

### Profiling results (2026-05-17)
- The project was moved from a FAT32 external drive to an ext4 external drive before profiling.
- On the ext4 drive, the dataloader is no longer the dominant bottleneck.
- Loader-only profile at `batch_size=64`, `num_workers=12`: ~6552 images/sec, mean wait ~9.8 ms.
- Train-step profile at `batch_size=64`, `num_workers=12`: ~241 images/sec end-to-end, loader wait ~0.0%, GPU active ~100%.
- Batch-size sweep showed higher throughput at larger batches:
  - `batch_size=96`, `num_workers=8`: ~319 images/sec
  - `batch_size=128`, `num_workers=8`: ~329 images/sec, peak CUDA allocated ~5.35 GiB
  - `batch_size=160`, `num_workers=8`: ~333 images/sec, peak CUDA allocated ~6.52 GiB
- Recommended starting point for the first real run: `--batch-size 128 --num-workers 8`.

### TensorBoard status
- Training loss and learning rate now log during the epoch via `--tensorboard-log-every-batches`.
- Default intra-epoch logging interval is 100 batches.
- Repo-level launch command is available via `make tensorboard`.
- TensorBoard is bound to `0.0.0.0` by default through the Makefile target.

### Baseline training results (2026-05-17/18)
Two production runs, both DINOv2 ViT-B/14, bs=128, nw=8, 10 epochs, species-disjoint split (10,719 train species / 1,190 val species), 884,323 train rows / 85,595 val rows, image_size=224, last 4 blocks unfrozen.

| Run | backbone LR | head LR | Best val mean R² | Best epoch | Final val loss |
|---|---|---|---|---|---|
| `dinov2_climate_bs128w8_longrun` | 1e-6 | 1e-4 | 0.4120 | 9 | 0.6068 |
| `dinov2_climate_bs128w8_backbone2e6` | 2e-6 | 1e-4 | **0.4184** | 5 | 0.6003 |

- Best checkpoint: `outputs/models/dinov2_climate_bs128w8_backbone2e6/best.pt` (val mean R² ≈ 0.4184).
- Both runs plateau by ~epoch 5; train loss keeps dropping (0.66 → 0.45) while val stalls → mild overfitting, generalization ceiling.
- Higher backbone LR (2e-6) reached a slightly higher peak earlier; longer training did not help.
- Run configs: `outputs/models/<run>/run_config.json`. Per-epoch logs: `outputs/logs/<run>.log`.
- `eval_val_best.json` was empty until the per-target eval was run (see below).

### Per-target eval (2026-06-21, backbone2e6/best.pt, val split, 85,595 rows)
All 5 climate targets are learned positively (R² > 0.30, Pearson > 0.55). Thermodynamic variables learned best; atmospheric/radiative structure weaker.

| Target | R² | Pearson r | MAE | Note |
|---|---|---|---|---|
| wbt_c (wet-bulb temp) | **0.552** | 0.743 | 4.01 °C | best — temp + moisture combined |
| temperature_2m_mean | **0.537** | 0.734 | 4.46 °C | strong — vegetation/lighting cues |
| solar_wm2 | 0.366 | 0.606 | 52.8 W/m² | moderate |
| vpd_kpa | 0.335 | 0.583 | 0.37 kPa | moderate (derived thermodynamic) |
| diurnal_range_c | 0.303 | 0.555 | 3.30 °C | weakest (within-day variability, not visible) |

- Mean R² = 0.4184 (matches training log). Saved to `outputs/models/dinov2_climate_bs128w8_backbone2e6/eval_val.json`.
- Interpretation: temp & wbt (R²≈0.54) are visually encoded in habitat; diurnal range (R²≈0.30) is a daily-statistic not readable from a single photo, so its floor is lower. None are at zero → genuine cross-species climate signal across all targets.

## Assessment & Plan

### What the result means
- Val mean R² ≈ 0.42 on a **species-disjoint split** is a real positive signal: the model cannot use "species → climate" shortcuts and must learn environmental cues (vegetation, sky, terrain, lighting) that generalize across unseen species. ~42% of climate variance explained from photos of unfamiliar species is non-trivial.
- The plateau + train/val gap is a **generalization** ceiling, not a capacity or data-quantity problem. More epochs/data at the current config will not move R² much.

### Scientific fork (must be decided before scaling)
The project is named *bioclimatic morphology* (thesis: animal morphology encodes climate), but the current full-frame setup learns the **environment** around the animal, not the animal's body plan. Two distinct claims:
1. **Environment-from-photos** (current setup): "climate is readable from wildlife photos." Strong, publishable, R²≈0.42 is a floor.
2. **Morphology** (namesake): "climate signal lives in the animal body." Untested. Requires removing background cues via segmentation/cropping and comparing full-frame vs. segmented under the same split.

### Recommended order of operations
1. **Per-target eval** (DONE, 2026-06-21): see per-target table above. All 5 targets learned; temp & wbt strongest (R²≈0.54).
2. **Decide claim**: environment-from-photos vs. morphology. → **Pursuing the morphology test** (the project's namesake). Decision: build a SAM 3 segmentation pipeline to isolate the animal subject, then compare full-frame vs. masked under the same split.
3. **Segmentation pipeline (IN PROGRESS)**: SAM 3 (`facebookresearch/sam3`, cloned to `/mnt/usb/sam3`), open-vocabulary text prompting with each photo's `common_name`. Produces binary masks + bbox + score manifest. Training dataset will derive full/crop/masked variants on the fly. See "SAM 3 segmentation pipeline" below.
4. **Retrain on variants**: from the same DINOv2 init, same species split, same hparams, train on (a) bbox-crop and (b) background-masked images; compare per-target val R² to the full-frame baseline. If masked R² ≈ 0.42 → morphology carries the signal; if it collapses → current result is habitat.
5. **If environment claim instead**: scale up — image_size 224 → 518 (DINOv2 native), ViT-B → ViT-L/14, stronger regularization, early stopping ~ep 5–6.

### Ceiling-raising levers (independent of claim)
- Resolution: 224 is well below DINOv2's native 518; information is being left on the table.
- Capacity: ViT-L/14 (~3× ViT-B params).
- Regularization: higher dropout / weight decay to combat the overfitting gap.
- Early stopping: best val is at epoch 5; runs beyond that overfit.

## SAM 3 segmentation pipeline

### Goal
Isolate the animal subject in each photo so the training dataset can produce full-frame / bbox-crop / background-masked variants. The make-or-break experiment: retrain on masked images under the same species-disjoint split and compare per-target val R² to the full-frame baseline (R²≈0.42). If masked R² holds → morphology carries the signal; if it collapses → the current result is habitat.

### Code & env
- Script: `scripts/segmentation/segment_sam3.py` — batched SAM 3 inference, text-prompted by `common_name` (fallback `taxon`), saves binary mask PNGs + `data/vision/segmented/manifest.csv` (bbox, score, mask-area fraction). Resumable (skips obs_ids in manifest), `--limit` for pilots.
- SAM 3 repo: cloned to `/mnt/usb/sam3` (installed editable).
- Env: `sam3` conda env (Python 3.11, torch 2.12.0+cu130, sam3 + deps, numpy 1.26.4). Use `/home/tngai/miniconda3/envs/sam3/bin/python`. Kept separate from `bm-venv` because SAM 3 requires `numpy<2`.

### Status (2026-06-21)
- Env built and all SAM 3 imports verified on the GB10.
- Segmentation script written and syntax-checked.
- **BLOCKER — HuggingFace access**: `facebook/sam3` is a gated repo. The cached HF token does not yet have access. `build_sam3_image_model()` fails with `GatedRepoError` until access is granted. Action required: request access at https://huggingface.co/facebook/sam3 and accept the SAM license. Once granted, the auto-download works; or pass `--checkpoint /path/to/sam3.pt` for a local file.

### Run commands
```bash
# Pilot (1000 mammals) — once HF access is granted:
/home/tngai/miniconda3/envs/sam3/bin/python scripts/segmentation/segment_sam3.py \
  --taxon mammals --batch-size 8 --limit 1000

# Full run (~970K images):
/home/tngai/miniconda3/envs/sam3/bin/python scripts/segmentation/segment_sam3.py \
  --taxon both --batch-size 8
```
First forward pass is slow (torch compilation); expect ~10–50 img/s on the GB10 → ~5–13 h one-time for the full dataset. Masks (~15 GB total) saved to `data/vision/segmented/masks/{taxon}/{obs_id}.png`.

## Environment
- **Machine:** NVIDIA GB10 (Grace Blackwell, aarch64), CUDA 13.0 driver. This is the GPU machine (was previously separate from the data-prep machine; the repo now lives on it at `/mnt/usb/bioclimatic-morphology`).
- **Python env for training/eval:** `/home/tngai/miniconda3/envs/bm-venv` (torch 2.12.0+cu130, CUDA-enabled). Use `bm-venv/bin/python` to run training/eval. Do NOT use the repo `.venv` (CPU-only torch) or system python3 (no torch).
- **Python env for SAM 3 segmentation:** `/home/tngai/miniconda3/envs/sam3` (python 3.11, torch 2.12.0+cu130, sam3 package, numpy 1.26.4). Use `sam3/bin/python` for `scripts/segmentation/segment_sam3.py`. Separate from `bm-venv` because SAM 3 requires `numpy<2`.
- **Data scripts:** python3 (3.13), pandas, numpy, requests, pyarrow, rasterio
- **Git:** https://github.com/tedngai/bioclimatic-morphology
- **Disk:** ~829GB free of 1TB (images are ~102GB total)

## Useful Commands

### Profile the pipeline
```bash
python scripts/training/profile_dinov2.py --mode all --batch-size 128 --num-workers 8
```

### Start training
```bash
python scripts/training/train_dinov2.py --batch-size 128 --num-workers 8
```

### Evaluate a checkpoint (per-target R²)
```bash
# NOTE: use bm-venv (CUDA torch); override --csv-path since checkpoints store a stale mount path.
bm-venv/bin/python scripts/training/evaluate.py \
  outputs/models/dinov2_climate_bs128w8_backbone2e6/best.pt \
  --split val --csv-path data/vision/train_all.csv --num-workers 8
```

### Launch TensorBoard
```bash
make tensorboard TENSORBOARD_LOGDIR=outputs/models/dinov2_climate/tensorboard
```

## Grid / Caching Details
- Observations rounded to 0.5° grid cells
- Mammals: 15,271 grid cells | Birds: 9,292 cells
- Climate cache in `data/vision/climate_cache/{taxon}/` (parquet per cell)
- NASA POWER API: free, no key, daily 1981-present
