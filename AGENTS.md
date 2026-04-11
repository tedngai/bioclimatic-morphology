# AGENTS.md — Context for Continuation

## Current Task: Pair iNaturalist observations with climate data

The iNaturalist download is complete (987K images, 101GB). The next step is pairing each observation with its climate at the observation date, to create training labels for the vision encoder.

## What's Done

### Observation Metadata
- `data/vision/observations_mammals.csv` — 500K rows, 4173 species, lat/lon/date/photo_url
- `data/vision/observations_birds.csv` — 500K rows, 7892 species, lat/lon/date/photo_url

### Images
- `data/vision/images/mammals/` — 499,441 JPEGs (56GB), 99.9% success rate
- `data/vision/images/birds/` — 488,102 JPEGs (46GB), 97.6% success rate
- Images are named `{observation_id}.jpg`
- Photo URLs are medium resolution from iNaturalist (static.inaturalist.org or inaturalist-open-data.s3.amazonaws.com)

### Scripts Created
- `scripts/extraction/download_inaturalist.py` — observation metadata download (cursor-based pagination)
- `scripts/extraction/download_inaturalist_images.py` — concurrent image download with resume
- `scripts/extraction/pair_observations_climate.py` — **PARTIALLY BUILT**, needs completion

### Makefile Targets
- `make inat-obs` — download observation metadata
- `make inat-images` — download images
- `make inat-all` — both

## What's Blocked

### Climate Pairing (task 8.1c)
The script `scripts/extraction/pair_observations_climate.py` queries the Open-Meteo archive API for daily climate at each observation's (lat, lon, date). It hit the **hourly API rate limit** (429 error: "Hourly API request limit exceeded").

**The script works** — tested successfully with 5 grid cells before rate limiting.

**Rate limit details:**
- Open-Meteo free tier: 10,000 requests per day, hourly limit also enforced
- After many test calls during development, the hourly limit was exceeded
- Need to wait ~1 hour for reset, then run with conservative rate limiting

**Grid strategy:**
- Observations rounded to 0.5° grid cells
- Mammals: 15,268 unique grid cells
- Birds: 9,298 unique grid cells  
- Total: ~24.5K API calls needed
- At 3s delay (20 req/min): ~20 hours for all cells
- Each response cached as parquet for resume

**Required daily variables from Open-Meteo:**
- temperature_2m_max, temperature_2m_min, temperature_2m_mean
- relative_humidity_2m_max, relative_humidity_2m_min, relative_humidity_2m_mean
- dew_point_2m_max, dew_point_2m_min, dew_point_2m_mean
- wind_speed_10m_max, wind_speed_10m_mean
- shortwave_radiation_sum

**Derived psychrometric features (computed in script):**
- `wbt_c` — wet-bulb temperature via Stull (2011)
- `vpd_kpa` — vapor pressure deficit
- `diurnal_range_c` — daily temperature range
- `solar_wm2` — mean hourly solar radiation

**Output format (train_mammals.csv / train_birds.csv):**
```
observation_id, species, common_name, family, lat, lon, date_str, photo_url, photo_id,
temperature_2m_mean, temperature_2m_max, temperature_2m_min,
relative_humidity_2m_mean, relative_humidity_2m_max, relative_humidity_2m_min,
dew_point_2m_mean, wind_speed_10m_mean, wind_speed_10m_max,
shortwave_radiation_sum, wbt_c, vpd_kpa, diurnal_range_c, solar_wm2
```

## How to Resume

1. **Wait for rate limit to reset** (check: `curl -s "https://archive-api.open-meteo.com/v1/archive?latitude=0&longitude=0&start_date=2020-01-01&end_date=2020-01-02&daily=temperature_2m_mean&timezone=UTC"` — should return data, not 429)

2. **Run climate pairing:**
   ```bash
   cd /home/tngai/data/bioclimatic-morphology
   python3 scripts/extraction/pair_observations_climate.py --taxon mammals
   python3 scripts/extraction/pair_observations_climate.py --taxon birds
   ```

3. **The script is resume-safe** — caches per-grid-cell climate as parquet files in `data/vision/climate_cache/{taxon}/`. If interrupted, re-run and it skips cached cells.

4. **After climate pairing completes**, the next step is:
   - Merge train_mammals.csv + train_birds.csv into one training dataset
   - Add image_path column (relative path to images/)
   - Validate climate coverage and distribution
   - Move to task 8.3 (DINOv2 fine-tuning)

## Alternative Approach (if API rate limit is persistent)

If the Open-Meteo API rate limit is too restrictive for 24K calls:

1. **Use WorldClim monthly normals** — downloadable rasters at 1km resolution
   - Requires `rasterio` (not currently installed: `pip install rasterio`)
   - Gives monthly averages, not daily — still usable for self-supervised objective
   - No API limits
   
2. **Coarsen grid to 2°** — reduces to ~5K cells (well under 10K/day limit)
   - Climate labels less precise but still captures regional patterns
   
3. **Use ERA5 reanalysis via CDS API** — requires `.cdsapirc` credentials
   - More complex but no rate limit concerns
   - Script already exists in `src/climate/era5.py`

## Environment

- **Python:** system python3 (3.13) for data scripts; uv-managed .venv for project code
- **Key packages:** pandas, numpy, requests, pyarrow (for parquet caching)
- **pip install:** `python3 -m pip install pandas requests pyarrow` (system python)
- **uv run:** `uv run python` for project modules (uses .venv)
- **Git:** pushed to https://github.com/tedngai/bioclimatic-morphology
- **Disk:** ~829GB free of 1TB

## Key Design Decisions

1. **0.5° grid cells** for climate lookup — balances precision vs API calls
2. **Daily aggregates** not hourly — 24x fewer data points, sufficient for training
3. **Per-cell parquet cache** — enables resume after interruption
4. **Stull (2011) for wet-bulb** — fast empirical approximation, ±0.3°C accuracy
5. **Observations outside 1940-2023** dropped (archive API range) — only 5 mammals affected
