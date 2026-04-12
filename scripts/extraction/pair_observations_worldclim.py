"""
Pair iNaturalist observations with WorldClim monthly climate normals.

Uses WorldClim v2.1 monthly rasters (10-min resolution) to extract climate
at each observation's (lat, lon, month). No API calls — everything is local
raster extraction after a one-time download.

Variables extracted per month:
  - tavg, tmin, tmax (°C)
  - vapr (water vapor pressure, kPa)
  - wind (wind speed at 10m, m/s)
  - srad (solar radiation, kJ/m²/day)

Derived features:
  - rh_mean (relative humidity %, from vapr + tavg)
  - wbt_c (wet-bulb temp, Stull 2011)
  - vpd_kpa (vapor pressure deficit)
  - diurnal_range_c (tmax - tmin)
  - solar_wm2 (mean hourly solar flux)

Usage:
    python3 scripts/extraction/pair_observations_worldclim.py [--taxon mammals|birds|both]
"""

import argparse
import io
import os
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

# Check rasterio is available
try:
    import rasterio
    from rasterio.transform import rowcol
except ImportError:
    print("ERROR: rasterio not installed. Run: pip install rasterio")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_VISION = PROJECT_ROOT / "data" / "vision"
WORLDCLIM_DIR = DATA_VISION / "worldclim"

WORLDCLIM_BASE = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/base"

# Variables to download (monthly, 10-min resolution)
VARIABLES = {
    "tavg": "Average temperature (°C)",
    "tmin": "Minimum temperature (°C)",
    "tmax": "Maximum temperature (°C)",
    "vapr": "Water vapor pressure (kPa)",
    "wind": "Wind speed (m/s)",
    "srad": "Solar radiation (kJ/m²/day)",
}


def download_worldclim_rasters():
    """Download WorldClim monthly rasters if not already present."""
    WORLDCLIM_DIR.mkdir(parents=True, exist_ok=True)

    for var, desc in VARIABLES.items():
        # Check if already downloaded (any month file)
        existing = list(WORLDCLIM_DIR.glob(f"wc2.1_10m_{var}_*.tif"))
        if len(existing) == 12:
            print(f"  {var}: already downloaded")
            continue

        url = f"{WORLDCLIM_BASE}/wc2.1_10m_{var}.zip"
        print(f"  Downloading {var} ({desc})...")

        try:
            resp = requests.get(url, timeout=300, stream=True)
            resp.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                for member in zf.namelist():
                    if member.endswith(".tif"):
                        # Extract to worldclim dir
                        target = WORLDCLIM_DIR / Path(member).name
                        if not target.exists():
                            with zf.open(member) as src, open(target, "wb") as dst:
                                dst.write(src.read())
            print(f"  {var}: done")

        except Exception as e:
            print(f"  {var}: FAILED - {e}")
            print(f"  URL: {url}")
            print("  Download manually and place .tif files in data/vision/worldclim/")
            raise


def load_rasters():
    """Load all 12 months for each variable into memory.

    Returns dict: var_name -> list of (array, transform, nodata) for months 1-12.
    """
    rasters = {}
    for var in VARIABLES:
        monthly = []
        for month in range(1, 13):
            path = WORLDCLIM_DIR / f"wc2.1_10m_{var}_{month:02d}.tif"
            if not path.exists():
                print(f"WARNING: {path} not found")
                monthly.append(None)
                continue
            with rasterio.open(path) as src:
                data = src.read(1)
                monthly.append((data, src.transform, src.nodata))
        rasters[var] = monthly
    return rasters


def extract_values(rasters, lats, lons, months):
    """Extract raster values at (lat, lon, month) positions.

    Args:
        rasters: dict from load_rasters()
        lats, lons: arrays of coordinates
        months: array of month numbers (1-12)

    Returns: dict of var_name -> array of values
    """
    from rasterio.transform import rowcol

    results = {var: np.full(len(lats), np.nan) for var in VARIABLES}

    for var, monthly in rasters.items():
        # Group by month for efficiency
        for m in range(1, 13):
            if monthly[m - 1] is None:
                continue
            data, transform, nodata = monthly[m - 1]
            mask = months == m
            if not mask.any():
                continue

            # Convert lat/lon to pixel coordinates
            rows, cols = rowcol(transform, lons[mask], lats[mask])
            rows = np.array(rows, dtype=int)
            cols = np.array(cols, dtype=int)

            # Bounds check
            valid = (rows >= 0) & (rows < data.shape[0]) & (cols >= 0) & (cols < data.shape[1])

            if valid.any():
                vals = data[rows[valid], cols[valid]]
                # Handle nodata
                if nodata is not None:
                    vals = np.where(np.isclose(vals, nodata), np.nan, vals)
                results[var][np.where(mask)[0][valid]] = vals

    return results


def wet_bulb_stull(t_c, rh_pct):
    """Wet-bulb temperature (C) via Stull (2011)."""
    return (
        t_c * np.arctan(0.151977 * np.sqrt(rh_pct + 8.313659))
        + np.arctan(t_c + rh_pct)
        - np.arctan(rh_pct - 1.676331)
        + 0.00391838 * rh_pct**1.5 * np.arctan(0.023101 * rh_pct)
        - 4.686035
    )


def vpd_from_temps_and_vapr(t_c, vapr_kpa):
    """Vapor pressure deficit (kPa) from temperature and actual vapor pressure."""
    e_s = 610.94 * np.exp(17.625 * t_c / (t_c + 243.04)) / 1000.0  # kPa
    return e_s - vapr_kpa


def rh_from_vapr(t_c, vapr_kpa):
    """Relative humidity (%) from temperature and vapor pressure."""
    e_s = 610.94 * np.exp(17.625 * t_c / (t_c + 243.04)) / 1000.0  # kPa
    return np.clip((vapr_kpa / e_s) * 100.0, 0, 100)


def process_taxon(taxon, rasters):
    """Pair observations with WorldClim climate for one taxon."""
    obs_path = DATA_VISION / f"observations_{taxon}.csv"
    out_path = DATA_VISION / f"train_{taxon}.csv"

    if not obs_path.exists():
        print(f"{obs_path} not found, skipping {taxon}")
        return

    # Load observations
    print(f"\nLoading {taxon} observations...")
    df = pd.read_csv(obs_path)
    print(f"  {len(df)} observations loaded")

    # Parse dates
    df["date"] = pd.to_datetime(df["date"])
    df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
    df["month"] = df["date"].dt.month

    # Extract climate values
    print(f"  Extracting climate values from rasters...")
    t0 = time.time()

    lats = df["lat"].values.astype(float)
    lons = df["lon"].values.astype(float)
    months = df["month"].values.astype(int)

    values = extract_values(rasters, lats, lons, months)

    elapsed = time.time() - t0
    print(f"  Extraction done in {elapsed:.1f}s")

    # Add climate columns to dataframe
    for var in VARIABLES:
        df[var] = values[var]

    # Rename to match expected output names
    df = df.rename(
        columns={
            "tavg": "temperature_2m_mean",
            "tmax": "temperature_2m_max",
            "tmin": "temperature_2m_min",
            "wind": "wind_speed_10m_mean",
            "vapr": "vapor_pressure_kpa",
        }
    )

    # WorldClim wind is at 10m; use same value for max (monthly avg)
    df["wind_speed_10m_max"] = df["wind_speed_10m_mean"]

    # Solar radiation: kJ/m²/day → daily MJ/m² (for consistency with Open-Meteo format)
    df["shortwave_radiation_sum"] = values["srad"] / 1000.0  # kJ → MJ

    # Compute relative humidity from vapr and tavg
    has_climate = df["temperature_2m_mean"].notna() & df["vapor_pressure_kpa"].notna()

    if has_climate.any():
        t_mean = df.loc[has_climate, "temperature_2m_mean"].values
        vapr = df.loc[has_climate, "vapor_pressure_kpa"].values
        t_max = df.loc[has_climate, "temperature_2m_max"].values
        t_min = df.loc[has_climate, "temperature_2m_min"].values
        solar = df.loc[has_climate, "shortwave_radiation_sum"].values

        # Relative humidity
        rh = rh_from_vapr(t_mean, vapr)
        df.loc[has_climate, "relative_humidity_2m_mean"] = rh
        # Approximate max/min RH (WorldClim only gives mean)
        df.loc[has_climate, "relative_humidity_2m_max"] = np.clip(rh * 1.15, 0, 100)
        df.loc[has_climate, "relative_humidity_2m_min"] = np.clip(rh * 0.85, 0, 100)

        # Dew point (back-calculate from vapr)
        # vapr = 610.94 * exp(17.625 * Td / (Td + 243.04)) / 1000
        # Td = 243.04 * ln(vapr * 1000 / 610.94) / (17.625 - ln(vapr * 1000 / 610.94))
        vapr_pa = vapr * 1000.0
        ln_ratio = np.log(np.clip(vapr_pa / 610.94, 1e-10, None))
        dew_point = 243.04 * ln_ratio / (17.625 - ln_ratio)
        df.loc[has_climate, "dew_point_2m_mean"] = dew_point

        # Derived psychrometric features
        wbt = wet_bulb_stull(t_mean, rh)
        vpd = vpd_from_temps_and_vapr(t_mean, vapr)
        diurnal = t_max - t_min
        solar_wm2 = solar * 1e6 / 86400  # MJ/m²/day → W/m²

        df.loc[has_climate, "wbt_c"] = wbt
        df.loc[has_climate, "vpd_kpa"] = vpd
        df.loc[has_climate, "diurnal_range_c"] = diurnal
        df.loc[has_climate, "solar_wm2"] = solar_wm2

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
    out_cols = [c for c in out_cols if c in df.columns]

    df[out_cols].to_csv(out_path, index=False)

    n_paired = has_climate.sum()
    print(f"\n{taxon}: saved {len(df)} rows to {out_path}")
    print(f"  {n_paired} obs with climate ({100 * n_paired / len(df):.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="Pair observations with WorldClim climate")
    parser.add_argument(
        "--taxon",
        choices=["mammals", "birds", "both"],
        default="both",
    )
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download rasters, don't process observations",
    )
    args = parser.parse_args()

    # Step 1: Download rasters
    print("Downloading WorldClim rasters...")
    download_worldclim_rasters()

    if args.download_only:
        print("Download complete. Run again without --download-only to process observations.")
        return

    # Step 2: Load rasters into memory
    print("\nLoading rasters into memory...")
    t0 = time.time()
    rasters = load_rasters()
    elapsed = time.time() - t0
    print(f"  Loaded in {elapsed:.1f}s")

    # Step 3: Process taxa
    taxa = ["mammals", "birds"] if args.taxon == "both" else [args.taxon]
    for taxon in taxa:
        process_taxon(taxon, rasters)


if __name__ == "__main__":
    main()
