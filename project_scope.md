# Project Scope: Data-Driven Bioclimatic Morphology

**Companion to:** `research-brief.md`
**Date:** 2026-09-26 (remote state re-verified)
**Status:** Phase 8 — DINOv2 baseline complete (val mean R² ≈ 0.42); morphology test via SAM 3 segmentation in progress

---

## Overview

This project learns the relationship between visual morphology and thermoregulatory performance using self-supervised learning on millions of geotagged images. Every photo of an animal or building is implicitly labeled with its climate via geolocation. A vision encoder learns thermoregulatory features from pixels, using climate prediction as the training objective.

The core insight: **images of animals and buildings encode thermoregulatory information visually** — large ears, thick fur, windcatchers, stilt construction, whitewashed walls are all visible features that correlate with climate adaptation. A model trained to predict climate from images will learn these features without any manual coding.

---

## Project Evolution

### Phase 1-5: Tabular approach (completed, archived in `backup/phase1-5/`)

Built a hand-coded dataset of 425 animal species and 170 building traditions with ~44 features each. Developed the 4-axis thermoregulatory ontology (Collection, Transfer, Storage, Regulation) and physics-based metrics (U_eff, C_th, D_reg). Proved that animal and building thermal conductance occupies the same range (0.5-5 W/m²K).

**Limitation discovered:** Tabular ML on 595 hand-coded samples can't generalize. Categorical Koppen labels collapse continuous climate variation. The contrastive embedding model memorized zone assignments instead of learning thermal physics.

### Phase 7: Restructure (superseded by Phase 8)

Planned to switch from categorical Koppen labels to per-entity continuous psychrometric coordinates. Correctly diagnosed the problem but proposed the same tabular regression approach, which wouldn't scale.

### Phase 8: Vision-based self-supervised learning (current)

Reframes the entire approach: instead of hand-coding features, learn them from millions of geotagged images using climate prediction as the self-supervised objective.

| | Phase 1-5 (tabular) | Phase 8 (vision) |
|---|---|---|
| Data scale | 595 hand-coded samples | 1.5M+ geotagged photos |
| Feature extraction | Manual (fur density, wall thickness) | Learned from images |
| Climate pairing | Categorical Koppen labels | Automatic from geolocation |
| ML approach | Classification/regression on tabular data | Self-supervised visual pre-training + fine-tuning |
| Generalization | Only to coded species/buildings | To any photographed entity |
| Design tool | Code features by hand, run model | Upload a photo |

---

## Current Assets

### Data (retained from Phase 1-5)

| Asset | Count | Role in Phase 8 |
|---|---|---|
| Animal species (raw features) | 425 | Fine-tuning labels |
| Building traditions (raw features) | 170 | Fine-tuning labels |
| Quantitative metrics (U_eff, C_th, D_reg) | Computed for all 595 | Fine-tuning targets |
| Climate zones (location-based) | 20 | Reference |
| Psychrometric derivation engine | Production-ready | Climate extraction for new images |
| AlphaEarth extraction code | Production-ready | Satellite features for new images |

### Data (new for Phase 8)

| Source | Scale | Status |
|---|---|---|
| iNaturalist mammals | 500K obs, 499K images (56GB), 4173 species | **DONE** |
| iNaturalist birds | 500K obs, 488K images (46GB), 7892 species | **DONE** |
| NASA POWER daily climate pairing | 970,147 paired image-climate rows | **DONE** |
| Mapillary (building facades) | ~2B photos geotagged | Not yet accessed |
| AlphaEarth per-image | GEE API, unlimited | Pipeline ready (src/climate/alphaearth.py) |

**Data locations:**
- `data/vision/observations_mammals.csv` — 500K rows (82MB)
- `data/vision/observations_birds.csv` — 500K rows (77MB)
- `data/vision/images/mammals/` — 499K JPEGs (56GB)
- `data/vision/images/birds/` — 488K JPEGs (46GB)
- `data/vision/climate_cache/` — per-location cached climate used during pairing
- **Total disk used:** ~127GB of 1TB available (829GB free)
- **Also on the GPU server** (`spark-server:/mnt/wholemilk/bioclimatic-morphology`) with trained checkpoints — see `docs/infrastructure.md`

### Code (retained)

| Module | Purpose | Status |
|---|---|---|
| `src/climate/psychrometrics.py` | Psychrometric derivation | Production-ready |
| `src/climate/era5.py` | Open-Meteo download + psychrometric pipeline | Production-ready |
| `src/climate/alphaearth.py` | GEE AlphaEarth extraction | Production-ready |
| `src/animals/schema.py` | Feature schema + validation | Reference for fine-tuning labels |
| `src/buildings/schema.py` | Feature schema + validation | Reference for fine-tuning labels |
| `scripts/training/climate_dataset.py` | Dataset, splits, transforms | Ready |
| `scripts/training/train_dinov2.py` | DINOv2 climate training loop | Ready |
| `scripts/training/evaluate.py` | Checkpoint evaluation | Ready |
| `scripts/training/profile_dinov2.py` | Dataloader/GPU bottleneck profiling | Ready |

### Key Findings (preserved)

- U_eff overlap: animal pelage and building envelopes share 0.5-5 W/m²K range
- Collection axis (p=0.001) and storage axis (p=0.034) converge across domains
- Temperate convergence gap reflects ecosystem-level distributed thermoregulation
- Night flushing = building vasodilation; fat = PCM; panting = permeable stilt-house ventilation
- Termite mound (decrement factor 0.90) outperforms most vernacular buildings

---

## Phase 8 Task List

See `docs/phase8_vision.md` for the full implementation plan.

- [x] 8.1a: Download iNaturalist observations (500K mammals + 500K birds) ✅
- [x] 8.1b: Download iNaturalist images (~987K images, 101GB) ✅
- [x] 8.1c: Pair observations with daily climate and build `train_all.csv` ✅
- [ ] 8.2: Data pipeline — Mapillary buildings (500K photos paired with climate)
- [x] 8.3a: DINOv2 climate pre-training baseline (ViT-B/14, val mean R² ≈ 0.42; per-target eval complete) ✅
- [ ] 8.3b: Morphology test — SAM 3 segmentation blocked on a grad-mode bug in `segment_sam3.py`; then retrain on crop/masked variants
- [ ] 8.4: Fine-tuning on 595 labeled samples (encoder → thermal metrics)
- [ ] 8.5: Evaluation, ablation, figures
- [ ] 8.6: Manuscript revision

### Current 8.3 status (2026-09-26)

- Baseline DINOv2 ViT-B/14 complete: best val mean R² **0.4184** (species-disjoint split, 10 epochs).
  Per-target R²: wbt 0.552, temp 0.537, solar 0.366, vpd 0.335, diurnal 0.303.
- GPU compute (not image I/O) is the bottleneck; recommended config `batch_size=128`, `num_workers=8`.
- `make tensorboard` launches TensorBoard on `0.0.0.0:6006`; `make remote-status` / `make remote-pull` manage the GPU server.
- Scientific decision: test the morphology claim — segment the animal (SAM 3), retrain on crop/masked variants, compare to the full-frame baseline. Segmentation pilot currently blocked on a torch inference-mode bug (see `AGENTS.md`, `docs/infrastructure.md`).

---

## Architecture

```
Pre-training (self-supervised, 1.5M images):
  Photo → DINOv2 encoder → 768D representation
                              ├→ Climate head: predict (DBT, RH, WBT, VPD, solar)
                              └→ AlphaEarth head: predict 64D satellite embedding
  
Fine-tuning (595 labeled samples):
  Pre-trained encoder (frozen) → 768D → Small MLP → U_eff, C_th, D_reg, strategy fractions

Inference (design tool):
  Photo of building → encoder → head → predicted thermal metrics
                                      → compare against biological benchmark
                                      → design recommendation
```

---

## Compute Budget

| Task | Hardware | Time | Cost |
|---|---|---|---|
| Data pipeline | CPU, 200GB disk | 2 weeks | ~$100 |
| Pre-training | 1× A100 GPU | 3-5 days | ~$300-500 |
| Fine-tuning | Any GPU | 1 hour | ~$5 |
| Evaluation | CPU | 1 day | negligible |
| **Total** | | **3-4 weeks** | **~$500** |
