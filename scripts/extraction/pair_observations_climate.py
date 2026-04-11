"""
Pair iNaturalist observations with Open-Meteo daily climate data.

For each observation (lat, lon, date), looks up daily climate from the
Open-Meteo archive API and computes psychrometric features.

Strategy:
  1. Round lat/lon to 0.5° grid cells
  2. For each unique grid cell, query the full date range of observations
  3. Cache per-location daily climate CSVs for resume
  4. Join back to observations and compute psychrometric features

Usage:
    python3 scripts/extraction/pair_observations_climate.py [--taxon mammals|birds|both]
"""

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_VISION = PROJECT_ROOT / "data" / "vision"
CLIMATE_CACHE = DATA_VISION / "climate_cache"

API_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",
    "relative_humidity_2m_mean",
    "dew_point_2m_max",
    "dew_point_2m_min",
    "dew_point_2m_mean",
    "wind_speed_10m_max",
    "wind_speed_10m_mean",
    "shortwave_radiation_sum",
]
RATE_LIMIT_DELAY = 0.15  # ~400 req/min, well under any limit


def latlon_key(lat_r: float, lon_r: float) -> str:
    """Deterministic cache key from rounded lat/lon."""
    return f"{lat_r:+.1f}_{lon_r:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")


def wet_bulb_stull(t_c: np.ndarray, rh_pct: np.ndarray) -> np.ndarray:
    """Wet-bulb temperature (C) via Stull (2011)."""
    return (
        t_c * np.arctan(0.151977 * np.sqrt(rh_pct + 8.313659))
        + np.arctan(t_c + rh_pct)
        - np.arctan(rh_pct - 1.676331)
        + 0.00391838 * rh_pct**1.5 * np.arctan(0.023101 * rh_pct)
        - 4.686035
    )


def vpd_from_temps(t_c: np.ndarray, t_dew_c: np.ndarray) -> np.ndarray:
    """Vapor pressure deficit (kPa) from dry-bulb and dewpoint (C)."""
    e_s = 610.94 * np.exp(17.625 * t_c / (t_c + 243.04))
    e_a = 610.94 * np.exp(17.625 * t_dew_c / (t_dew_c + 243.04))
    return (e_s - e_a) / 1000.0


def fetch_daily_climate(
    lat: float, lon: float, start_date: str, end_date: str, retries: int = 3
) -> dict | None:
    """Fetch daily climate from Open-Meteo archive API."""
    params = {
        "latitude": round(lat, 1),
        "longitude": round(lon, 1),
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(DAILY_VARS),
        "timezone": "UTC",
    }

    for attempt in range(retries):
        try:
            resp = requests.get(API_URL, params=params, timeout=120)
            if resp.status_code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            if resp.status_code == 400:
                # Date range out of bounds (too old or future)
                return None
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, json.JSONDecodeError) as e:
            wait = 5 * (attempt + 1)
            print(f"    API error (attempt {attempt + 1}): {e}, retry in {wait}s")
            time.sleep(wait)

    return None


def query_location_climate(
    lat_r: float, lon_r: float, dates: list[str], cache_dir: Path
) -> pd.DataFrame | None:
    """Query climate for a grid cell, using cache if available."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = latlon_key(lat_r, lon_r)
    cache_file = cache_dir / f"{key}.parquet"

    if cache_file.exists():
        try:
            return pd.read_parquet(cache_file)
        except Exception:
            pass  # corrupted cache, re-fetch

    # Determine date range
    sorted_dates = sorted(dates)
    start = sorted_dates[0]
    end = sorted_dates[-1]

    # Archive API starts at 1940-01-01
    if start < "1940-01-01":
        start = "1940-01-01"
    if end > "2023-12-31":
        end = "2023-12-31"

    if start > end:
        return None

    data = fetch_daily_climate(lat_r, lon_r, start, end)
    if data is None or "daily" not in data:
        return None

    daily = data["daily"]
    df = pd.DataFrame(daily)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")

    # Save cache
    try:
        df.to_parquet(cache_file)
    except Exception:
        pass  # parquet write failed, continue anyway

    return df


def process_taxon(taxon: str):
    """Pair observations with climate for one taxon."""
    obs_path = DATA_VISION / f"observations_{taxon}.csv"
    out_path = DATA_VISION / f"train_{taxon}.csv"
    cache_dir = CLIMATE_CACHE / taxon

    if not obs_path.exists():
        print(f"{obs_path} not found, skipping {taxon}")
        return

    # Load observations
    print(f"Loading {taxon} observations...")
    df = pd.read_csv(obs_path)
    print(f"  {len(df)} observations loaded")

    # Round to 0.5° grid
    df["lat_r"] = (df["lat"] * 2).round() / 2
    df["lon_r"] = (df["lon"] * 2).round() / 2

    # Filter to valid dates (archive API: 1940-01-01 to 2023-12-31)
    df["date"] = pd.to_datetime(df["date"])
    valid = (df["date"] >= "1940-01-01") & (df["date"] <= "2023-12-31")
    n_invalid = (~valid).sum()
    if n_invalid > 0:
        print(f"  Dropping {n_invalid} obs outside 1940-2023 date range")
        df = df[valid].copy()

    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    # Group by grid cell
    groups = df.groupby(["lat_r", "lon_r"])
    n_groups = len(groups)
    print(f"  {n_groups} unique 0.5° grid cells")

    # Check existing cache
    cached_keys = set()
    if cache_dir.exists():
        for f in cache_dir.glob("*.parquet"):
            cached_keys.add(f.stem)

    # Process each grid cell
    climate_records = {}
    processed = 0
    api_calls = 0
    t0 = time.time()

    for (lat_r, lon_r), group in groups:
        key = latlon_key(lat_r, lon_r)
        dates = group["date_str"].unique().tolist()

        # Query climate
        climate_df = query_location_climate(lat_r, lon_r, dates, cache_dir)

        if climate_df is None or climate_df.empty:
            processed += 1
            continue

        if key not in cached_keys:
            api_calls += 1

        # Index by date string for fast lookup
        climate_df.index = climate_df.index.strftime("%Y-%m-%d")

        for _, row in group.iterrows():
            date_s = row["date_str"]
            if date_s in climate_df.index:
                climate_records[row["observation_id"]] = climate_df.loc[date_s].to_dict()

        processed += 1

        # Progress
        if processed % 100 == 0:
            elapsed = time.time() - t0
            rate = processed / elapsed if elapsed > 0 else 0
            eta = (n_groups - processed) / rate if rate > 0 else 0
            print(
                f"  {processed}/{n_groups} cells | "
                f"{api_calls} API calls | "
                f"{len(climate_records)} obs paired | "
                f"{rate:.0f} cells/s | "
                f"ETA {eta / 60:.0f}min"
            )

        time.sleep(RATE_LIMIT_DELAY)

    # Build output dataframe
    print(f"\n  Building output CSV...")

    # Convert climate records to DataFrame
    climate_df_all = pd.DataFrame.from_dict(climate_records, orient="index")
    climate_df_all.index.name = "observation_id"
    climate_df_all = climate_df_all.reset_index()

    # Merge with observations
    result = df.merge(climate_df_all, on="observation_id", how="left")

    # Compute psychrometric features
    has_climate = result["temperature_2m_mean"].notna()
    print(f"  {has_climate.sum()} / {len(result)} obs have climate data")

    if has_climate.any():
        t_mean = result.loc[has_climate, "temperature_2m_mean"].values
        t_dew = result.loc[has_climate, "dew_point_2m_mean"].values
        rh_mean = result.loc[has_climate, "relative_humidity_2m_mean"].values
        t_max = result.loc[has_climate, "temperature_2m_max"].values
        t_min = result.loc[has_climate, "temperature_2m_min"].values
        solar = result.loc[has_climate, "shortwave_radiation_sum"].values
        wind = result.loc[has_climate, "wind_speed_10m_mean"].values

        wbt = wet_bulb_stull(t_mean, rh_mean)
        vpd = vpd_from_temps(t_mean, t_dew)
        diurnal = t_max - t_min
        solar_wm2 = solar / 24.0  # daily MJ/m² to mean hourly W/m²

        result.loc[has_climate, "wbt_c"] = wbt
        result.loc[has_climate, "vpd_kpa"] = vpd
        result.loc[has_climate, "diurnal_range_c"] = diurnal
        result.loc[has_climate, "solar_wm2"] = solar_wm2

    # Select output columns
    out_cols = [
        "observation_id",
        "species",
        "common_name",
        "family",
        "lat",
        "lon",
        "date_str",
        "photo_url",
        "photo_id",
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "relative_humidity_2m_mean",
        "relative_humidity_2m_max",
        "relative_humidity_2m_min",
        "dew_point_2m_mean",
        "wind_speed_10m_mean",
        "wind_speed_10m_max",
        "shortwave_radiation_sum",
        "wbt_c",
        "vpd_kpa",
        "diurnal_range_c",
        "solar_wm2",
    ]
    # Keep only columns that exist
    out_cols = [c for c in out_cols if c in result.columns]

    result[out_cols].to_csv(out_path, index=False)

    elapsed = time.time() - t0
    print(f"\n{taxon}: saved {len(result)} rows to {out_path}")
    print(f"  {api_calls} API calls in {elapsed / 60:.1f}min")
    print(f"  {has_climate.sum()} obs with climate ({100 * has_climate.sum() / len(result):.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Pair observations with climate")
    parser.add_argument(
        "--taxon",
        choices=["mammals", "birds", "both"],
        default="both",
    )
    args = parser.parse_args()

    taxa = ["mammals", "birds"] if args.taxon == "both" else [args.taxon]

    for taxon in taxa:
        process_taxon(taxon)


if __name__ == "__main__":
    main()
