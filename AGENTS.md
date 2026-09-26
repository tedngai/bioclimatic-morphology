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

Immediate blocker: the SAM 3 pilot (2026-06-28, 1000 mammals) failed for every image with `forward:Expected grad to be disabled`. Root cause verified: `segment_sam3.py` calls `torch.inference_mode().__enter__()` on a temporary object that is garbage-collected immediately, so grad stays enabled. Fix by wrapping model build + inference loop in a proper `with torch.inference_mode():` block, then rerun with `--checkpoint /mnt/wholemilk/sam3/sam3.pt` (bypasses HF gating).

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

## Assessment & Plan

### The scientific fork
1. **Environment-from-photos** (current full-frame setup): "climate is readable from wildlife photos." Strong, publishable; R²≈0.42 is a floor.
2. **Morphology** (project namesake, being tested now): "the climate signal lives in the animal body." Requires background removal via segmentation/cropping and a same-split comparison.

### Order of operations
1. ~~Per-target eval~~ — done 2026-06-21.
2. ~~Decide claim~~ — decided: run the morphology test.
3. **Segmentation (in progress, blocked):** fix the grad-mode bug in `scripts/segmentation/segment_sam3.py`, rerun the 1000-image pilot, verify masks, then launch the full ~970K run.
4. **Retrain on variants:** same DINOv2 init, same species split, same hparams; train on (a) bbox-crop and (b) background-masked; compare per-target val R² to the 0.42 full-frame baseline. Masked ≈ 0.42 → morphology carries signal; collapse → habitat.
5. **If environment claim instead:** scale up — image_size 224 → 518, ViT-B → ViT-L/14, stronger regularization, early stopping.

### Ceiling-raising levers (claim-independent)
Resolution (224 vs. DINOv2 native 518), capacity (ViT-L/14), regularization (dropout/weight decay), early stopping ~ep 5.

## SAM 3 Segmentation Pipeline

### Goal
Isolate the animal subject so the dataset can produce full-frame / bbox-crop / background-masked variants for the make-or-break comparison.

### Code & env
- Script: `scripts/segmentation/segment_sam3.py` — batched SAM 3 inference, text-prompted by `common_name` (fallback `taxon`), saves binary mask PNGs + `data/vision/segmented/manifest.csv` (bbox, score, mask-area fraction). Resumable (skips obs_ids already in the manifest), `--limit` for pilots.
- SAM 3 repo/checkpoint: `/mnt/wholemilk/sam3` with local `sam3.pt` (3.3 GB).
- Env: `/home/tngai/miniconda3/envs/sam3/bin/python` (Python 3.11, torch 2.12.0+cu130, `numpy<2`). Separate from `bm-venv` because SAM 3 needs numpy 1.26.
- HF gating: `facebook/sam3` is gated and the cached token is unauthorized (401). **Use `--checkpoint /mnt/wholemilk/sam3/sam3.pt`** — no HF access needed.

### Status (2026-06-28)
- Pilot of 1000 mammals ran; **all rows failed**: `forward:Expected grad to be disabled` (raised by `sam3/perflib/fused.py:addmm_act`).
- Verified root cause on torch 2.12: `torch.inference_mode().__enter__()` on a temporary object does not hold (object GC'd; `is_inference_mode_enabled()==False`, grad remains enabled). A kept reference or proper `with` block works.
- Fix: wrap model build + batch loop in `with torch.inference_mode():` (or call `torch.set_grad_enabled(False)` once). Smoke-test with `--limit 2`, then rerun the pilot.

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
Masks (~15 GB) land in `data/vision/segmented/masks/{taxon}/{obs_id}.png`.

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
