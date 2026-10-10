# AGENTS.md — Context for Continuation

## Two-Machine Setup (read first)

This project runs on two machines. Work from the management machine (this checkout); run GPU jobs on `spark-server`.

| | Management (this checkout) | GPU server (`spark-server`) |
|---|---|---|
| Host | `cio-tngai-m` (Ubuntu 22.04, RTX 2000 Ada 8 GB) | `promaxgb10-42ce` (NVIDIA GB10, aarch64, ~128 GB unified) |
| Repo | `/home/tngai/data/bioclimatic-morphology` | `/mnt/wholemilk/bioclimatic-morphology` |
| Role | source of truth: edit code/docs, commit, push, data prep | training, evaluation, segmentation |

- **Git is the sync channel.** Both machines use the `GITHUB_PAT` in `.env` via `~/.local/bin/github-token-helper`; remote URLs are tokenless. Flow: commit/push here → `make remote-pull` → run on server.
- **SSH:** `ssh spark-server` (password auth). Non-interactive helper exists for scripts — see `docs/infrastructure.md`.
- **Never commit `.env`.** It holds API keys + the git PAT.
- **GPU is shared** with a root-owned `sglang` LLM server (~99 GiB held). Check `nvidia-smi` before launching training; use `tmux` for long jobs.
- Full runbook: `docs/infrastructure.md` (SSH details, envs, disk, gotchas).

## Current Task: morphology test (task 8.3 follow-up)

Baseline DINOv2 climate training is **complete** (val mean R² ≈ 0.42, species-disjoint split) and per-target eval is **done**. **Decision taken: test whether the climate signal lives in animal morphology** — isolate the animal with SAM 3 and compare full-frame vs. bbox-crop vs. background-masked under the identical species-split/hparams.

**Segmentation complete (2026-10-01).** The grad-mode + mask-shape bugs and the stale `sam3` install are fixed, and the full run finished: **970,147 images → 744,528 detections (76.7%) in 55 h at 4.9 img/s** (mammals 73.6%, birds 80.0%; only 2 truncated images failed). Masks (~2.9 GB, 744,528 PNGs) are in `data/vision/segmented/masks/{taxon}/`.

**Variant runs + controls complete (2026-10-05).** `crop`, `masked`, and the `bg` background-only control each trained 10 epochs with the best-baseline hparams. Best val mean R²: full **0.4184** / bg **0.3921** / crop **0.3661** / masked **0.2749**; on the detected-only subset (no fallback, 64,848 rows): full **0.4241** / bg **0.3901** / crop **0.3583** / masked **0.2422**. Background alone keeps ~92–94% of the full-frame signal, animal alone ~57–66% → the photos' climate signal is dominated by habitat/background, with a genuine but secondary morphology component. **Scale-up running (2026-10-09):** ViT-L/14 @ 336, 5 epochs, tmux `dinov2-large336` (~18 h). Details in Training Status.

## What's Done

### Observation Metadata
- `data/vision/observations_mammals.csv` — 500K rows, 4173 species
- `data/vision/observations_birds.csv` — 500K rows, 7892 species

### Images
- `data/vision/images/mammals/` — 499,441 JPEGs (56 GB)
- `data/vision/images/birds/` — 488,102 JPEGs (46 GB)
- Named `{observation_id}.jpg`; copies exist on both machines

### Training Dataset (complete)
- `data/vision/train_all.csv` — **970,147 rows** (308 MB)
- Mammals: 489,465 | Birds: 480,682 | Species: 11,913
- 98%+ have daily climate from NASA POWER (1981–2019)
- Per-taxon files: `data/vision/train_mammals.csv`, `train_birds.csv`

### Climate features (columns in train_all.csv)
| Column | Description | Mean | Range |
|---|---|---|---|
| temperature_2m_mean | Daily mean temp (°C) | 15.89 | -42.32 to 41.66 |
| wbt_c | Wet-bulb temp (Stull 2011) | 12.34 | -42.75 to 29.81 |
| vpd_kpa | Vapor pressure deficit | 0.69 | -0.08 to 7.12 |
| diurnal_range_c | T_max - T_min | 10.22 | 0.02 to 29.35 |
| solar_wm2 | Mean hourly solar flux | 209.58 | 0 to 430.60 |

Full column list: `observation_id, image_path, taxon, species, common_name, family, lat, lon, date_str, photo_url, photo_id, temperature_2m_mean/max/min, relative_humidity_2m_mean/max/min, dew_point_2m_mean, wind_speed_10m_mean/max, shortwave_radiation_sum, wbt_c, vpd_kpa, diurnal_range_c, solar_wm2`

### Data-pipeline scripts (all complete)
- `scripts/extraction/download_inaturalist.py` — observation metadata
- `scripts/extraction/download_inaturalist_images.py` — image download
- `scripts/extraction/pair_observations_nasa.py` — NASA POWER daily climate
- `scripts/extraction/pair_observations_climate.py` — DEAD (Open-Meteo)
- `scripts/extraction/pair_observations_worldclim.py` — BACKUP (monthly normals)

## Training Status

### Code (implemented, on both machines)
- `scripts/training/climate_dataset.py` — PyTorch dataset, split helpers, target normalization, DINO-compatible transforms
- `scripts/training/train_dinov2.py` — training loop, checkpointing, TensorBoard logging, configurable dataloader knobs
- `scripts/training/evaluate.py` — checkpoint evaluation on train or validation split (per-target R²)
- `scripts/training/profile_dinov2.py` — dataloader-wait vs. GPU-compute profiler
- `scripts/training/update_progress.py` — regenerates `PROGRESS.xml` from runs/profiles

### Profiling (2026-05-17, ext4 drive)
Loader is not the bottleneck; GPU compute is (~100% active). Recommended config: `--batch-size 128 --num-workers 8` (~329 img/s end-to-end, ~5.35 GiB peak).

### Baseline results (2026-05-17/18)
Two runs, DINOv2 ViT-B/14, bs=128, nw=8, 10 epochs, species-disjoint split (10,719 train / 1,190 val species; 884,323 train / 85,595 val rows), image_size=224, last 4 blocks unfrozen.

| Run | backbone LR | head LR | Best val mean R² | Best epoch | Final val loss |
|---|---|---|---|---|---|
| `dinov2_climate_bs128w8_longrun` | 1e-6 | 1e-4 | 0.4120 | 9 | 0.6068 |
| `dinov2_climate_bs128w8_backbone2e6` | 2e-6 | 1e-4 | **0.4184** | 5 | 0.6003 |

- Best checkpoint: `outputs/models/dinov2_climate_bs128w8_backbone2e6/best.pt` (server).
- Both runs plateau by ~epoch 5; train loss keeps dropping while val stalls → **generalization ceiling**, not capacity/data-limited. Early stopping ~ep 5–6 is sensible.

### Per-target eval (2026-06-21, backbone2e6/best.pt, val split, 85,595 rows)
| Target | R² | Pearson r | MAE | Note |
|---|---|---|---|---|
| wbt_c (wet-bulb temp) | **0.552** | 0.743 | 4.01 °C | best — temp + moisture combined |
| temperature_2m_mean | **0.537** | 0.734 | 4.46 °C | strong — vegetation/lighting cues |
| solar_wm2 | 0.366 | 0.606 | 52.8 W/m² | moderate |
| vpd_kpa | 0.335 | 0.583 | 0.37 kPa | moderate (derived thermodynamic) |
| diurnal_range_c | 0.303 | 0.555 | 3.30 °C | weakest (within-day variability, not visible) |

- Mean R² = 0.4184; saved to `outputs/models/dinov2_climate_bs128w8_backbone2e6/eval_val.json`.
- All 5 targets are learned positively (R² > 0.30) on unseen species → genuine cross-species climate signal.
- Caveat: the full-frame model mostly reads the **environment** (habitat, vegetation, sky) — hence the morphology test.

### Variant results — morphology test (2026-10-02, controls 2026-10-05)

Same species-disjoint split and hparams as `dinov2_climate_bs128w8_backbone2e6`. `crop` = bbox around the animal (10% pad); `masked` = non-animal pixels to neutral gray 128 (animal-only); `bg` = animal pixels to neutral gray (background-only). Rows without a SAM 3 detection (23.3%) fall back to the full frame — `detection_coverage` is 0.768 train / 0.758 val — which dilutes variant differences; the detected-only re-eval (`evaluate.py --only-detected`, 64,848 val rows) removes that dilution.

| Run | image content | Best val mean R² | Best epoch | Final epoch | Detected-only mean R² |
|---|---|---|---|---|---|
| `dinov2_climate_bs128w8_backbone2e6` | animal + background | 0.4184 | 5 | 0.4155 | **0.4241** |
| `dinov2_climate_bg` | background only | 0.3921 | 5 | 0.3890 | **0.3901** |
| `dinov2_climate_crop` | cropped context | 0.3661 | 4 | 0.3573 | **0.3583** |
| `dinov2_climate_masked` | animal only | 0.2749 | 6 | 0.2705 | **0.2422** |

Per-target val R² at each run's best epoch (all rows):

| Target | full | bg | crop | masked |
|---|---|---|---|---|
| wbt_c | 0.552 | 0.517 | 0.488 | 0.384 |
| temperature_2m_mean | 0.537 | 0.501 | 0.471 | 0.362 |
| solar_wm2 | 0.366 | 0.329 | 0.324 | 0.242 |
| vpd_kpa | 0.335 | 0.314 | 0.287 | 0.197 |
| diurnal_range_c | 0.303 | 0.300 | 0.260 | 0.189 |
| **mean** | **0.4184** | **0.3921** | **0.3661** | **0.2749** |

- **Background dominance:** background-only retains 94% of the full-frame mean R² (all rows) / 92% (detected-only); animal-only retains 66% / 57%. The climate signal in wildlife photos is carried mostly by habitat/background; animal morphology contributes a genuine but secondary component.
- All five targets remain clearly positive with the animal isolated (detected-only masked: wbt 0.339, temp 0.318, solar 0.225, vpd 0.172, diurnal 0.158) → the morphology claim survives, at reduced strength.
- The 23.3% no-detection fallback rows inflate the masked headline (0.2749 → 0.2422 on matched rows) and slightly deflate full-frame (0.4184 → 0.4241).
- History: `outputs/models/dinov2_climate_{bg,crop,masked}/history.csv` (tracked). Checkpoints `best.pt` (~550 MB) live only on the server. Eval JSONs via `evaluate.py` (see image-variants section).

## Assessment & Plan

### The scientific fork
1. **Environment-from-photos** (current full-frame setup): "climate is readable from wildlife photos." Strong, publishable; R²≈0.42 is a floor.
2. **Morphology** (project namesake, tested 2026-10-01/05): "the climate signal lives in the animal body." Animal-only retains ~57–66% of the full-frame signal on matched rows — real but secondary; background dominates.

### Order of operations
1. ~~Per-target eval~~ — done 2026-06-21.
2. ~~Decide claim~~ — decided: run the morphology test.
3. ~~Segmentation~~ — **done 2026-10-01**: 970,147 images, 76.7% detections, 55 h. Manifest deduplicated to one row per observation (resumability fixed via `astype(str)` on ids).
4. ~~Retrain on variants~~ — **done 2026-10-02**: crop **0.3661** / masked **0.2749** vs. full-frame **0.4184**. Neither collapsed → morphology signal is real, but the background/habitat carries a large share (caveat: 23.3% no-detection rows fall back to full frame). See variant results table.
5. ~~Controls~~ — **done 2026-10-04/05**: detected-only re-eval (masked 0.2422 vs full 0.4241 on matched rows) + `bg` background-only run (0.3921; ~94% of full-frame). Verdict: environment/habitat dominates the signal; morphology is real but secondary.
6. **Scale-up running (launched 2026-10-09):** ViT-L/14 @ 336, bs 128, 5 epochs (early-stopping budget, ~18 h), tmux `dinov2-large336`, based on the 2026-10-09 benchmark. Evals are chained after training. The silhouette (shape-only) control remains available if we want the morphology story airtight first.

### Ceiling-raising levers (claim-independent)
Resolution (224 → 518), capacity (ViT-B → ViT-L/14), regularization (dropout/weight decay), early stopping ~ep 5.

**Scale-up benchmark (2026-10-09, with the LLM server holding ~34 GiB).** `profile_dinov2.py --mode train` (bs 128 unless noted, 8 workers, 5 warmup + 10 profile steps; GPU 100% active, loader wait 0%). Epoch = 884,323 train images.

| Model | image_size | batch | img/s | peak CUDA alloc | epoch ETA | 5-epoch ETA |
|---|---|---|---|---|---|---|
| ViT-B/14 (baseline config) | 224 | 128 | ~329 | 5.4 GiB | ~0.75 h | ~3.7 h |
| ViT-B/14 | 518 | 128 | 60.7 | 25.7 GiB | ~4.0 h | ~20 h |
| ViT-L/14 | 224 | 128 | 145.8 | 7.9 GiB | ~1.7 h | ~8.4 h |
| ViT-L/14 | 336 | 128 | 66.9 | 15.7 GiB | ~3.7 h | ~18 h |
| ViT-L/14 | 518 | 128 | 26.9 | 34.9 GiB | ~9.1 h | ~46 h |
| ViT-L/14 | 518 | 64 | 27.4 | 18.3 GiB | ~9.0 h | ~45 h |

- Memory is not the constraint: the heaviest config peaked at 34.9 GiB alongside the LLM's ~34 GiB; the system stayed ≥38 GiB available throughout. No OOM; the LLM does **not** need stopping for memory (only if it starts serving heavy traffic and bandwidth contention shows up, or for the unmeasured throughput headroom).
- Throughput is the constraint: ViT-L/14 @ 518 is ~9 h/epoch (~2 days for a 5-epoch run); ViT-L/14 @ 336 ~3.7 h/epoch; ViT-B/14 @ 518 ~4 h/epoch.
- All existing runs plateaued by epoch 4–6, so early stopping ≈5 epochs is sensible.

## SAM 3 Segmentation Pipeline

### Goal
Isolate the animal subject so the dataset can produce full-frame / bbox-crop / background-masked variants for the make-or-break comparison.

### Code & env
- Script: `scripts/segmentation/segment_sam3.py` — batched SAM 3 inference, text-prompted by `common_name` (fallback `taxon`), saves binary mask PNGs + `data/vision/segmented/manifest.csv` (bbox, score, mask-area fraction). Resumable (skips obs_ids already in the manifest), `--limit` for pilots.
- SAM 3 repo/checkpoint: `/mnt/wholemilk/sam3` with local `sam3.pt` (3.3 GB).
- Env: `/home/tngai/miniconda3/envs/sam3/bin/python` (Python 3.11, torch 2.12.0+cu130, `numpy<2`). Separate from `bm-venv` because SAM 3 needs numpy 1.26.
- HF gating: `facebook/sam3` is gated and the cached token is unauthorized (401). **Use `--checkpoint /mnt/wholemilk/sam3/sam3.pt`** — no HF access needed.

### Status (2026-09-26) — pilot validated
- **Fixed:** grad-mode bug (keep the `inference_mode` context object alive; `e5d2d2e`) and mask-shape bug (squeeze singleton/channel dims to H×W; `706e94c`). Also repointed the stale `sam3` editable install from `/mnt/usb/sam3` to `/mnt/wholemilk/sam3`.
- **Smoke test:** 2/2 detections (scores 0.95 / 0.84), valid masks.
- **Pilot (1000 mammals):** 765 detections (76.5%), 0 errors, 4.9 img/s → 3.4 min. Score mean 0.889 / median 0.926 (min 0.504). Mask area median 7.6%, none degenerate (>0.9); masks saved at original image resolution (~4 KB each, ~4 GB for the full run).
- **Batch sweep (256 imgs each):** bs 16/32/64 all ~5.0 img/s with identical 208/256 detections, 0 errors → throughput is GPU-bound at res 1008 and insensitive to batch size; keep the batch-8 default.
- Previous failed run's manifest kept as `data/vision/segmented/manifest.failed-20260628.csv`.
- **Full run complete (2026-10-01):** 970,147 images in 54 h 59 m at 4.9 img/s → **744,528 detections (76.7%)**. Mammals 360,174/489,465 (73.6%); birds 384,354/480,682 (80.0%). 2 rows failed on truncated images; masks total 2.9 GB (744,528 PNGs). Manifest: one row per observation (970,147).
- **Resumability bug found & fixed:** `observation_id` is int64 in the source CSVs while manifest ids are strings, so `load_done()` never matched and the full run reprocessed the pilot (1,000 duplicate manifest rows). Fixed with `astype(str)`; manifest deduplicated (backup on server: `/mnt/wholemilk/manifest.pre-dedupe-20261001.csv.gz`).

### Run commands (from the server repo root)
```bash
# Smoke test (2 images)
/home/tngai/miniconda3/envs/sam3/bin/python scripts/segmentation/segment_sam3.py \
  --taxon mammals --batch-size 2 --limit 2 --checkpoint /mnt/wholemilk/sam3/sam3.pt

# Pilot (1000 mammals)
/home/tngai/miniconda3/envs/sam3/bin/python scripts/segmentation/segment_sam3.py \
  --taxon mammals --batch-size 8 --limit 1000 --checkpoint /mnt/wholemilk/sam3/sam3.pt

# Full run (~970K images; ~5–13 h at 10–50 img/s)
/home/tngai/miniconda3/envs/sam3/bin/python scripts/segmentation/segment_sam3.py \
  --taxon both --batch-size 8 --checkpoint /mnt/wholemilk/sam3/sam3.pt
```
Masks (~3 GB) land in `data/vision/segmented/masks/{taxon}/{obs_id}.png`.

### Image variants for the morphology test (2026-10-01, extended 2026-10-04)

- `scripts/training/climate_dataset.py` supports `--image-mode full|crop|masked|bg`:
  - `crop` — bbox around the animal from the SAM 3 manifest, 10% padding, min side 32 px.
  - `masked` — non-animal pixels set to neutral gray (128) using the SAM 3 mask (animal-only).
  - `bg` — animal pixels set to neutral gray (128), background kept (background-only control).
  - Rows without a detection (23.3% of the dataset) or with a missing mask fall back to the full frame; `detection_coverage` is recorded in each run's `run_config.json`. `evaluate.py --only-detected` filters to rows with usable detections (no fallback) for dilution-free comparisons.
- Variant runs complete (2026-10-01/02, tmux `dinov2-variants`): `outputs/models/dinov2_climate_crop` (best ep 4, 0.3661), then `outputs/models/dinov2_climate_masked` (best ep 6, 0.2749); ~8 h each.
- Background-only control complete (2026-10-04/05, tmux `dinov2-controls`): `outputs/models/dinov2_climate_bg` (best ep 5, 0.3921; detected-only 0.3901). Followed by `evaluate.py` on both splits → `eval_val.json` + `eval_val_detected.json`.
- Train command:
  ```bash
  bm-venv/bin/python scripts/training/train_dinov2.py --image-mode bg \
    --output-dir outputs/models/dinov2_climate_bg \
    --batch-size 128 --num-workers 8 --backbone-lr 2e-6 --head-lr 1e-4 --epochs 10
  ```
- Eval command (picks up `image_mode` from the checkpoint config automatically; writes `eval_val.json` next to the checkpoint). Add `--only-detected` for the no-fallback subset:
  ```bash
  bm-venv/bin/python scripts/training/evaluate.py outputs/models/dinov2_climate_masked/best.pt \
    --split val --csv-path data/vision/train_all.csv --num-workers 8
  ```

## Server Environments

- **Training/eval:** `/home/tngai/miniconda3/envs/bm-venv/bin/python` — torch 2.12.0+cu130 (CUDA works on GB10), transformers 5.8.1. Do NOT use the repo `.venv` (no GPU torch) or system python3.
- **Segmentation:** `/home/tngai/miniconda3/envs/sam3/bin/python` (numpy<2).
- **GPU sharing:** root-owned sglang LLM server holds ~99 GiB; check `nvidia-smi` before launching. Use `tmux`.
- **Checkpoint paths:** checkpoints store absolute paths from the writing machine; `evaluate.py` needs `--csv-path data/vision/train_all.csv` to override stale mounts.

## Useful Commands

```bash
# Management machine
ssh spark-server                 # interactive shell on GPU server
make remote-status               # git + GPU + disk + tmux on the server
make remote-pull                 # fast-forward server repo to origin/main

# Server: training / eval
bm-venv/bin/python scripts/training/train_dinov2.py --batch-size 128 --num-workers 8
bm-venv/bin/python scripts/training/evaluate.py \
  outputs/models/dinov2_climate_bs128w8_backbone2e6/best.pt \
  --split val --csv-path data/vision/train_all.csv --num-workers 8
make tensorboard                 # 0.0.0.0:6006; tunnel with ssh -L 6006:localhost:6006 spark-server
```

## Grid / Caching Details
- Observations rounded to 0.5° grid cells
- Mammals: 15,271 grid cells | Birds: 9,292 cells
- Climate cache in `data/vision/climate_cache/{taxon}/` (parquet per cell)
- NASA POWER API: free, no key, daily 1981–present
