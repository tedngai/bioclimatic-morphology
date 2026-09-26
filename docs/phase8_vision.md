# Phase 8: Vision-Based Self-Supervised Bioclimatic Morphology

> **Status (2026-09-26):** Original implementation plan, kept for reference. The actual
> implementation diverged (NASA POWER instead of Open-Meteo; no AlphaEarth head yet; a
> species-disjoint DINOv2 baseline is complete at val mean R² ≈ 0.42). Current state:
> `AGENTS.md`. Two-machine setup: `docs/infrastructure.md`.

## Paradigm Shift

Phases 1-7 treated this as a tabular ML problem: hand-code features for 595 entities, train regression/classification models. This hit a fundamental ceiling — not enough labeled data for any model to generalize.

Phase 8 reframes the problem as **self-supervised visual learning**. Every geotagged photo of an animal or building is implicitly labeled with its climate. A vision model trained on millions of such images learns thermoregulatory features directly from pixels, using climate prediction as the self-supervised objective.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    PRE-TRAINING (self-supervised)             │
│                                                              │
│  iNaturalist photo ──→ Vision Encoder ──→ Representation     │
│  (10M+ geotagged)       (DINOv2/ViT)      (768D vector)     │
│                              │                               │
│                              ├──→ Climate Head: predict       │
│                              │    (DBT, RH, WBT, VPD,        │
│                              │     solar, wind, diurnal)      │
│                              │    at the photo's geolocation  │
│                              │                               │
│                              └──→ AlphaEarth Head: predict    │
│                                   64D satellite embedding     │
│                                   at the photo's geolocation  │
│                                                              │
│  Loss = MSE(predicted_climate, actual_climate)               │
│        + MSE(predicted_AE, actual_AE)                        │
│                                                              │
│  What the encoder learns:                                    │
│    Large ears → hot-dry climate (radiative cooling)           │
│    Thick fur → cold climate (insulation)                      │
│    Windcatcher → hot-dry climate                              │
│    Stilt house → hot-humid climate                            │
│    Whitewash → high-solar climate                             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    FINE-TUNING (595 labeled samples)          │
│                                                              │
│  Pre-trained Encoder (frozen or light fine-tune)              │
│         │                                                    │
│         ▼                                                    │
│  Small MLP head ──→ U_eff, C_th, D_reg                       │
│                 ──→ evaporative_frac, radiative_frac, ...     │
│                                                              │
│  Training data: the 595 hand-coded samples from Phases 1-7   │
│  These become fine-tuning labels, not the whole training set  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    INFERENCE (design tool)                    │
│                                                              │
│  Architect uploads photo of building ──→ Encoder ──→ Head     │
│         │                                                    │
│         ▼                                                    │
│  Predicted: U_eff = 2.1 W/m²K (±0.3)                         │
│             C_th = 450 kJ/K/m²                                │
│             D_reg = 8.5                                       │
│             evaporative_frac = 0.15                            │
│         │                                                    │
│         ▼                                                    │
│  Compare against:                                             │
│    - Animal distribution at same climate (biological benchmark)│
│    - Vernacular buildings at same climate (traditional bench.) │
│         │                                                    │
│         ▼                                                    │
│  Design recommendation with quantitative targets               │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### Animals: iNaturalist

| Metric | Value |
|---|---|
| Total research-grade observations with photos | 190M |
| Mammals | 5.4M |
| Birds | 39M |
| API | Free, 100 req/min (unauth), 500/min (auth) |
| Bulk access | AWS S3 open data bucket (weekly export) |
| License | CC-BY-NC (most observations) |
| Geolocation | Lat/lon per observation, typically <100m accuracy |

### Buildings: Mapillary

| Metric | Value |
|---|---|
| Total street-level images | ~2B globally |
| Geotagged | Yes (GPS + compass heading + timestamp) |
| Labels | None natively (need building detection) |
| API | Free tier with Meta developer OAuth |
| License | CC-BY-SA (map data), ToS (images) |
| Resolution | 2048-4000px typical |

### Climate context: Open-Meteo + AlphaEarth

| Source | What it provides | Access |
|---|---|---|
| Open-Meteo Archive API | Hourly DBT, RH, dewpoint, wind, solar at any (lat, lon, date) | Free, no key |
| AlphaEarth (GEE) | 64D satellite embedding at any (lat, lon) at 10m resolution | Free with GEE project |

### Cross-reference: Google Open Buildings

| Metric | Value |
|---|---|
| Building footprints | 1.8B (Africa, S/SE Asia, Latin America) |
| Data | Polygon geometry + centroid lat/lon |
| Use | Filter Mapillary images that contain buildings |

---

## Implementation Plan

### Task 8.1 — Data Pipeline: iNaturalist Animals

**Goal:** Download and pair 1M+ mammal/bird photos with climate data.

**Steps:**

1. Download iNaturalist AWS bulk export (or use API for targeted species)
   - Filter: Mammalia + Aves, research_grade, has_photos, has_geo
   - Target: 500K mammals + 500K birds = 1M observations

2. For each observation, extract:
   - Photo URL (medium resolution, ~800px)
   - Species taxonomy (family, genus, species)
   - Latitude, longitude
   - Observation date

3. For each (lat, lon, date), query Open-Meteo archive API:
   - Hourly temperature, humidity, dewpoint, wind, solar for that date
   - Compute psychrometric profile: DBT, RH, WBT, VPD, enthalpy

4. For each (lat, lon), extract AlphaEarth 64D embedding via GEE
   - Batch extraction (groups of 100 points)

5. Save as a paired dataset:
   ```
   image_path, species, lat, lon, date, 
   dbt_c, rh_pct, wbt_c, vpd_kpa, solar_wm2, wind_ms,
   ae_00, ae_01, ..., ae_63
   ```

**Output:** `data/vision/animals_paired.parquet` (~1M rows)

**Estimated compute:** 
- iNaturalist download: ~100GB images (medium res)
- Open-Meteo API: ~1M calls (at 100/min = ~7 days, or batch via daily aggregates)
- AlphaEarth: ~10K unique locations (most species cluster) = 1 hour via GEE

### Task 8.2 — Data Pipeline: Building Images

**Goal:** Collect and pair 500K+ building photos with climate data.

**Steps:**

1. Query Mapillary API for images in regions with known vernacular architecture:
   - Bounding boxes for: Morocco, Iran, India, Japan, China, W Africa, E Africa, Mongolia, Iceland, Norway, Peru, Thailand, etc.
   - Filter by: has_building_in_frame (use Mapillary's object detection or a pre-trained building detector)
   - Target: 500K building images across diverse climates

2. Alternative/supplement: use Google Open Buildings footprints to identify building locations, then find nearest Mapillary image.

3. For each image (lat, lon, date):
   - Query Open-Meteo for climate
   - Extract AlphaEarth embedding

4. Save as paired dataset:
   ```
   image_path, lat, lon, date,
   dbt_c, rh_pct, wbt_c, vpd_kpa, solar_wm2, wind_ms,
   ae_00, ae_01, ..., ae_63
   ```

**Output:** `data/vision/buildings_paired.parquet` (~500K rows)

**Estimated compute:** Similar to animal pipeline.

### Task 8.3 — Self-Supervised Pre-Training

**Goal:** Train a vision encoder that predicts climate from images.

**Architecture:**

```python
# Option A: Fine-tune DINOv2 (recommended — pre-trained on 142M images)
encoder = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14')
# Freeze early layers, fine-tune last 4 blocks
for param in encoder.parameters():
    param.requires_grad = False
for block in encoder.blocks[-4:]:
    for param in block.parameters():
        param.requires_grad = True

# Climate prediction head
climate_head = nn.Sequential(
    nn.Linear(768, 256),
    nn.ReLU(),
    nn.Linear(256, 7),  # DBT, RH, WBT, VPD, solar, wind, diurnal_range
)

# AlphaEarth prediction head
ae_head = nn.Sequential(
    nn.Linear(768, 256),
    nn.ReLU(),
    nn.Linear(256, 64),  # 64D AlphaEarth embedding
)

# Loss
loss = MSE(climate_head(encoder(image)), actual_climate) 
     + 0.5 * MSE(ae_head(encoder(image)), actual_ae)
```

**Option B: Train from scratch with I-JEPA objective**
- Mask random patches of the image
- Predict their representations from context patches
- Add climate prediction as auxiliary task
- More compute-intensive, potentially better representations
- Only worth it if DINOv2 fine-tuning underperforms

**Training details:**
- Batch size: 256 (or 128 with gradient accumulation)
- Learning rate: 1e-4 for encoder, 1e-3 for heads
- Epochs: 10-20 over the 1.5M image dataset
- Hardware: 1× A100 GPU (~3-5 days) or 4× A100 (~1 day)
- Optimizer: AdamW with cosine schedule
- Data augmentation: minimal (random crop, horizontal flip only — we want the model to learn from natural variation, not augmentation invariance)

**Validation:** Hold out 10% of images. Measure:
- Climate prediction R² (should be >0.5 for DBT, >0.3 for RH)
- AlphaEarth prediction R² (should be >0.3)
- Representation quality via linear probe on Koppen classification (should beat chance significantly)

**Output:** Pre-trained encoder weights at `outputs/models/bioclimate_encoder.pt`

### Task 8.4 — Fine-Tuning on Labeled Data

**Goal:** Predict thermal metrics from the pre-trained representation.

**Approach:**

1. For each of the 595 labeled samples (425 animals, 170 buildings):
   - Find the best matching iNaturalist/Mapillary photo
   - Or: use a representative photo for the species/tradition
   - Extract the 768D representation from the pre-trained encoder

2. Train a small MLP head:
   ```python
   head = nn.Sequential(
       nn.Linear(768, 128),
       nn.ReLU(),
       nn.Dropout(0.3),
       nn.Linear(128, 64),
       nn.ReLU(),
       nn.Linear(64, 7),  # U_eff, C_th, D_reg, 4 strategy fractions
   )
   ```

3. Training: 595 samples, leave-one-out CV by entity
   - With pre-trained encoder, 595 is plenty for a 768→7 mapping
   - Compare against: raw climate features → XGBoost (the tabular baseline)

**Validation metrics:**
- R² per output (U_eff, C_th, D_reg, strategy fractions)
- Compare: encoder representation vs. raw psychrometric features
- Compare: encoder representation vs. AlphaEarth embeddings alone
- Compare: encoder + psychrometric vs. psychrometric alone

**Output:** Fine-tuned head at `outputs/models/bioclimate_head.pt`

### Task 8.5 — Evaluation and Figures

**Goal:** Demonstrate that the vision-based approach outperforms tabular ML.

**Analyses:**

1. **Ablation study** (like Phase 1-5 but now with vision features):
   | Condition | Features | Expected R² |
   |---|---|---|
   | Psychrometric only | 7 climate vars | 0.3-0.5 |
   | AlphaEarth only | 64D satellite | 0.2-0.4 |
   | Vision encoder only | 768D from photo | 0.5-0.7 |
   | Vision + psychrometric | 768D + 7 | 0.6-0.8 |
   | Vision + AlphaEarth + psychrometric | 768D + 64D + 7 | 0.6-0.8 |

2. **Representation space visualization:**
   - UMAP of encoder representations colored by:
     - Koppen type (do climate zones cluster?)
     - U_eff (does conductance form a gradient?)
     - Domain (animals vs buildings — do they mix or separate?)

3. **Cross-domain retrieval** (the original goal, now achievable):
   - Given a climate, retrieve nearest animals and buildings in encoder space
   - Measure whether retrieved entities have similar thermal metrics

4. **Design evaluation demo:**
   - Take photos of known buildings
   - Predict thermal metrics from the encoder
   - Compare against measured/calculated metrics
   - Show that the model gives useful feedback

**Output:** Publication figures + evaluation report

### Task 8.6 — Manuscript Revision

**Goal:** Rewrite the manuscript to center the vision-based approach.

The vision approach reframes the contributions:

1. **The ontology and metric system** (from Phase 1-5) become the fine-tuning labels and evaluation framework — they're still valuable, just not the ML backbone
2. **The self-supervised pre-training** is the new core ML contribution
3. **The design evaluation tool** is now feasible (upload a photo, get thermal metrics)
4. **The cross-domain alignment** is learned from millions of images, not forced by 17 Koppen labels

---

## Dependencies and Sequencing

```
8.1 (Animal data) ────┐
                       ├──→ 8.3 (Pre-training) ──→ 8.4 (Fine-tune) ──→ 8.5 (Eval) ──→ 8.6 (Paper)
8.2 (Building data) ───┘
```

8.1 and 8.2 can run in parallel. Everything else is sequential.

---

## Compute Budget

| Task | Hardware | Time | Cost (cloud) |
|---|---|---|---|
| 8.1 Data pipeline (animals) | CPU, 100GB disk | 1-2 weeks | ~$50 (API + storage) |
| 8.2 Data pipeline (buildings) | CPU, 100GB disk | 1-2 weeks | ~$50 |
| 8.3 Pre-training | 1× A100 GPU | 3-5 days | ~$300-500 |
| 8.4 Fine-tuning | Any GPU | 1 hour | ~$5 |
| 8.5 Evaluation | CPU | 1 day | negligible |
| 8.6 Manuscript | — | 1-2 weeks | — |
| **Total** | | **4-6 weeks** | **~$500-1000** |

---

## Pilot Validation (before full pipeline)

Before committing to the full 1.5M image pipeline, validate the approach with a small pilot:

1. Download 5K iNaturalist photos (500 per Koppen type, 10 types)
2. Pair with Open-Meteo climate
3. Fine-tune DINOv2 for 5 epochs on climate prediction
4. Measure: can the encoder predict DBT from animal photos?
5. If R² > 0.3 on held-out images, proceed to full pipeline
6. If R² < 0.1, the approach may not work and we should reconsider

**Estimated time for pilot:** 2-3 days, no GPU needed (use frozen DINOv2 + linear probe)

---

## What Stays From Phase 1-7

| Asset | Role in Phase 8 |
|---|---|
| 425 animal species (raw features) | Fine-tuning labels |
| 170 building traditions (raw features) | Fine-tuning labels |
| Quantitative metrics (U_eff, C_th, D_reg) | Fine-tuning targets |
| 4-axis ontology | Evaluation framework |
| Psychrometric derivation engine | Climate extraction for new images |
| AlphaEarth extraction code | Satellite feature extraction |
| Ecosystem case studies | Conceptual findings (manuscript discussion) |

## What's New in Phase 8

| Component | Description |
|---|---|
| Data pipeline | iNaturalist + Mapillary + Open-Meteo + AlphaEarth pairing |
| Vision encoder | DINOv2 fine-tuned on climate prediction |
| Self-supervised objective | Image → climate + AlphaEarth prediction |
| Fine-tuning head | 768D → thermal metrics (U_eff, C_th, D_reg) |
| Design evaluation tool | Upload photo → get thermal performance assessment |
