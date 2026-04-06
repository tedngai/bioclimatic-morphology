"""Extract climate data (Open-Meteo + AlphaEarth) for the 5 pilot locations.

Usage:
    python scripts/extraction/extract_pilot_climate.py

This script:
    1. Downloads hourly climate data from Open-Meteo (free, no API key needed)
    2. Computes psychrometric profiles (annual + monthly)
    3. Extracts AlphaEarth 64D embeddings via Google Earth Engine
    4. Saves the merged climate table to data/pilot/climate_zones.csv

Note: ERA5 via CDS API is also supported but requires API credentials and may
be rate-limited. Open-Meteo is used by default for reliability.
"""

import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.config import PILOT_LOCATIONS, PILOT_DIR
from src.climate.era5 import (
    download_openmeteo,
    load_openmeteo,
    compute_psychrometric_from_openmeteo,
    compute_monthly_profiles_openmeteo,
)
from src.climate.alphaearth import get_embeddings_batch, validate_embeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    PILOT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Download climate data from Open-Meteo ────────────────────
    logger.info("Step 1: Downloading climate data from Open-Meteo...")

    om_profiles = []
    monthly_profiles = []

    for loc in PILOT_LOCATIONS:
        loc_id = loc["location_id"]
        logger.info(f"  Processing {loc_id} ({loc['name']})")

        try:
            csv_path = download_openmeteo(
                lat=loc["lat"],
                lon=loc["lon"],
                location_id=loc_id,
            )
            hourly_df = load_openmeteo(csv_path)
            annual = compute_psychrometric_from_openmeteo(hourly_df)
            annual["location_id"] = loc_id
            om_profiles.append(annual)

            monthly = compute_monthly_profiles_openmeteo(hourly_df)
            monthly["location_id"] = loc_id
            monthly_profiles.append(monthly)
            logger.info(f"    Annual DBT: {annual['mean_dbt_c']:.1f}°C, RH: {annual['mean_rh_pct']:.0f}%")

        except Exception as e:
            logger.error(f"  Failed for {loc_id}: {e}")
            om_profiles.append({"location_id": loc_id})

    # ── Step 2: Extract AlphaEarth embeddings ─────────────────────────────
    logger.info("Step 2: Extracting AlphaEarth embeddings...")

    locations_df = pd.DataFrame(PILOT_LOCATIONS)[["location_id", "lat", "lon"]]
    ae_df = get_embeddings_batch(locations_df)
    validation = validate_embeddings(ae_df)
    logger.info(f"  Embedding validation: {validation}")

    # ── Step 3: Merge everything ──────────────────────────────────────────
    logger.info("Step 3: Merging climate data...")

    base_df = pd.DataFrame(PILOT_LOCATIONS)
    climate_df = pd.DataFrame(om_profiles)

    merged = base_df.merge(climate_df, on="location_id", how="left")

    # Expand monthly profiles into columns
    monthly_df = pd.DataFrame(monthly_profiles)
    for col in ["monthly_dbt", "monthly_rh", "monthly_vpd", "monthly_wbt"]:
        for i, month_num in enumerate(range(1, 13)):
            merged[f"{col}_{month_num:02d}"] = monthly_df[col].apply(
                lambda x: x[i] if isinstance(x, list) and len(x) == 12 else None
            )

    # AlphaEarth embeddings
    merged = merged.merge(ae_df, on="location_id", how="left")

    # Save
    outpath = PILOT_DIR / "climate_zones.csv"
    merged.to_csv(outpath, index=False)
    logger.info(f"Saved pilot climate data to {outpath}")
    logger.info(f"  Shape: {merged.shape}")
    logger.info(f"  Columns: {list(merged.columns[:10])}... ({merged.shape[1]} total)")


if __name__ == "__main__":
    main()
