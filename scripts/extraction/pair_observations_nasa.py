"""
Pair iNaturalist observations with daily climate data from NASA POWER.

Uses NASA POWER daily API (free, no key, no stated rate limit) to get:
  - T2M, T2M_MAX, T2M_MIN (temperature °C)
  - RH2M (relative humidity %)
  - T2MDEW (dew point °C)
  - WS10M, WS10M_MAX (wind speed m/s)
  - ALLSKY_SFC_SW_DWN (solar radiation W/m²)

Strategy:
  1. Round lat/lon to 0.5° grid cells
  2. Parallel fetch all grid cells (ThreadPoolExecutor, 10 workers)
  3. Cache per-cell parquet files for resume
  4. Join back to observations, compute psychrometric features

Usage:
    python3 scripts/extraction/pair_observations_nasa.py [--taxon mammals|birds|both]
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import numpy as np
import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_VISION = PROJECT_ROOT / "data" / "vision"
CLIMATE_CACHE = DATA_VISION / "climate_cache"

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

PARAMS = [
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "T2MDEW",
    "WS10M",
    "WS10M_MAX",
    "ALLSKY_SFC_SW_DWN",
]

MAX_WORKERS = 10


def latlon_key(lat_r: float, lon_r: float) -> str:
    return f"{lat_r:+.1f}_{lon_r:+.1f}".replace("+", "p").replace("-", "m").replace(".", "d")


def wet_bulb_stull(t_c, rh_pct):
    return (
        t_c * np.arctan(0.151977 * np.sqrt(rh_pct + 8.313659))
        + np.arctan(t_c + rh_pct)
        - np.arctan(rh_pct - 1.676331)
        + 0.00391838 * rh_pct**1.5 * np.arctan(0.023101 * rh_pct)
        - 4.686035
    )


def vpd_from_temps(t_c, t_dew_c):
    e_s = 610.94 * np.exp(17.625 * t_c / (t_c + 243.04))
    e_a = 610.94 * np.exp(17.625 * t_dew_c / (t_dew_c + 243.04))
    return (e_s - e_a) / 1000.0


def fetch_daily_climate(lat, lon, start_date, end_date, retries=3):
    start = start_date.replace("-", "")
    end = end_date.replace("-", "")

    params = {
        "parameters": ",".join(PARAMS),
        "community": "SB",
        "longitude": round(lon, 1),
        "latitude": round(lat, 1),
        "start": start,
        "end": end,
        "format": "JSON",
    }

    for attempt in range(retries):
        try:
            resp = requests.get(API_URL, params=params, timeout=300)
            if resp.status_code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            if resp.status_code >= 400:
                return None
            resp.raise_for_status()
            data = resp.json()
            if "properties" not in data or "parameter" not in data["properties"]:
                return None
            return data["properties"]["parameter"]
        except (requests.RequestException, json.JSONDecodeError):
            time.sleep(5 * (attempt + 1))

    return None


def parse_raw_to_df(raw):
    first_param = list(raw.values())[0]
    dates_list = sorted(first_param.keys())

    rows = []
    for d in dates_list:
        row = {"date": f"{d[:4]}-{d[4:6]}-{d[6:]}"}
        for param in PARAMS:
            val = raw.get(param, {}).get(d, np.nan)
            if val == -999:
                val = np.nan
            row[param] = val
        rows.append(row)

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    return df


def fetch_and_cache_cell(args):
    """Worker function: fetch one grid cell, return (key, climate_df or None)."""
    lat_r, lon_r, min_date, max_date, cache_dir, cache_file, key = args

    # Already cached?
    if cache_file.exists():
        try:
            return key, pd.read_parquet(cache_file)
        except Exception:
            pass

    # Clip dates to NASA POWER range
    start = max(min_date, "1981-01-01")
    end = min(max_date, "2025-12-31")
    if start > end:
        return key, None

    raw = fetch_daily_climate(lat_r, lon_r, start, end)
    if raw is None:
        return key, None

    df = parse_raw_to_df(raw)

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_file)
    except Exception:
        pass

    return key, df


def process_taxon(taxon):
    obs_path = DATA_VISION / f"observations_{taxon}.csv"
    out_path = DATA_VISION / f"train_{taxon}.csv"
    cache_dir = CLIMATE_CACHE / taxon

    if not obs_path.exists():
        print(f"{obs_path} not found, skipping {taxon}")
        return

    print(f"Loading {taxon} observations...")
    df = pd.read_csv(obs_path)
    print(f"  {len(df)} observations loaded")

    # Round to 0.5° grid
    df["lat_r"] = (df["lat"] * 2).round() / 2
    df["lon_r"] = (df["lon"] * 2).round() / 2

    # Filter to NASA POWER date range
    df["date"] = pd.to_datetime(df["date"])
    valid = (df["date"] >= "1981-01-01") & (df["date"] <= "2025-12-31")
    n_invalid = (~valid).sum()
    if n_invalid > 0:
        print(f"  Dropping {n_invalid} obs outside 1981-2025 date range")
        df = df[valid].copy()

    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")

    # Build work items: one per unique grid cell
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_keys = {f.stem for f in cache_dir.glob("*.parquet")} if cache_dir.exists() else set()

    cell_info = df.groupby(["lat_r", "lon_r"]).agg(
        min_date=("date_str", "min"),
        max_date=("date_str", "max"),
    )

    work_items = []
    for (lat_r, lon_r), info in cell_info.iterrows():
        key = latlon_key(lat_r, lon_r)
        cache_file = cache_dir / f"{key}.parquet"
        work_items.append(
            (lat_r, lon_r, info["min_date"], info["max_date"], cache_dir, cache_file, key)
        )

    n_total = len(work_items)
    n_cached = sum(1 for w in work_items if w[5].exists())
    n_to_fetch = n_total - n_cached
    print(f"  {n_total} grid cells ({n_cached} cached, {n_to_fetch} to fetch)")
    print(f"  Fetching with {MAX_WORKERS} parallel workers...")

    # Parallel fetch
    climate_dfs = {}
    fetched = 0
    failed = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_and_cache_cell, item): item[6] for item in work_items}

        for future in as_completed(futures):
            key = futures[future]
            try:
                k, cdf = future.result()
                if cdf is not None:
                    climate_dfs[k] = cdf
                    fetched += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                if failed <= 10:
                    print(f"  Error fetching {key}: {e}")

            done = fetched + failed + n_cached
            if done % 200 == 0 or done == n_total:
                elapsed = time.time() - t0
                rate = (fetched + failed) / elapsed if elapsed > 0 else 0
                remaining = n_to_fetch - (fetched + failed)
                eta = remaining / rate if rate > 0 else 0
                print(
                    f"  {done}/{n_total} cells done | "
                    f"{fetched} fetched, {failed} failed, {n_cached} cached | "
                    f"{rate:.1f} cells/s | ETA {eta / 60:.0f}min"
                )

    # Also load cached cells we skipped
    for item in work_items:
        key = item[6]
        cache_file = item[5]
        if key not in climate_dfs and cache_file.exists():
            try:
                climate_dfs[key] = pd.read_parquet(cache_file)
            except Exception:
                pass

    # Join climate to observations
    print(f"\n  Joining {len(climate_dfs)} climate grids to observations...")
    climate_records = {}
    for _, row in df.iterrows():
        key = latlon_key(row["lat_r"], row["lon_r"])
        cdf = climate_dfs.get(key)
        if cdf is None or cdf.empty:
            continue
        date_s = row["date_str"]
        try:
            match = cdf.loc[cdf.index.strftime("%Y-%m-%d") == date_s]
            if not match.empty:
                climate_records[row["observation_id"]] = match.iloc[0].to_dict()
        except Exception:
            pass

    # Build output
    print(f"  Building output CSV...")
    climate_df_all = pd.DataFrame.from_dict(climate_records, orient="index")
    climate_df_all.index.name = "observation_id"
    climate_df_all = climate_df_all.reset_index()

    result = df.merge(climate_df_all, on="observation_id", how="left")

    rename_map = {
        "T2M": "temperature_2m_mean",
        "T2M_MAX": "temperature_2m_max",
        "T2M_MIN": "temperature_2m_min",
        "RH2M": "relative_humidity_2m_mean",
        "T2MDEW": "dew_point_2m_mean",
        "WS10M": "wind_speed_10m_mean",
        "WS10M_MAX": "wind_speed_10m_max",
        "ALLSKY_SFC_SW_DWN": "shortwave_radiation_sum",
    }
    result = result.rename(columns=rename_map)

    has_climate = result["temperature_2m_mean"].notna()
    print(f"  {has_climate.sum()} / {len(result)} obs have climate data")

    if has_climate.any():
        t_mean = result.loc[has_climate, "temperature_2m_mean"].values
        t_dew = result.loc[has_climate, "dew_point_2m_mean"].values
        rh_mean = result.loc[has_climate, "relative_humidity_2m_mean"].values
        t_max = result.loc[has_climate, "temperature_2m_max"].values
        t_min = result.loc[has_climate, "temperature_2m_min"].values
        solar = result.loc[has_climate, "shortwave_radiation_sum"].values

        result.loc[has_climate, "wbt_c"] = wet_bulb_stull(t_mean, rh_mean)
        result.loc[has_climate, "vpd_kpa"] = vpd_from_temps(t_mean, t_dew)
        result.loc[has_climate, "diurnal_range_c"] = t_max - t_min
        result.loc[has_climate, "solar_wm2"] = solar

    if "relative_humidity_2m_mean" in result.columns:
        rh = result["relative_humidity_2m_mean"]
        result["relative_humidity_2m_max"] = np.clip(rh * 1.15, 0, 100)
        result["relative_humidity_2m_min"] = np.clip(rh * 0.85, 0, 100)

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
    out_cols = [c for c in out_cols if c in result.columns]

    result[out_cols].to_csv(out_path, index=False)

    elapsed = time.time() - t0
    print(f"\n{taxon}: saved {len(result)} rows to {out_path}")
    print(f"  {elapsed / 60:.1f}min total")
    print(f"  {has_climate.sum()} obs with climate ({100 * has_climate.sum() / len(result):.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Pair observations with NASA POWER climate")
    parser.add_argument("--taxon", choices=["mammals", "birds", "both"], default="both")
    args = parser.parse_args()

    taxa = ["mammals", "birds"] if args.taxon == "both" else [args.taxon]
    for taxon in taxa:
        process_taxon(taxon)


if __name__ == "__main__":
    main()
