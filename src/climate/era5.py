"""ERA5 reanalysis data download and processing via the Copernicus CDS API.

Downloads hourly climate fields for specified locations and time periods,
then feeds them into the psychrometric derivation pipeline.

Requires:
    - CDS API key configured in ~/.cdsapirc
    - cdsapi package installed
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.config import ERA5_VARIABLES, ERA5_YEARS, RAW_DIR

logger = logging.getLogger(__name__)

ERA5_OUTPUT_DIR = RAW_DIR / "era5"


def download_era5_location(
    lat: float,
    lon: float,
    location_id: str,
    variables: list[str] | None = None,
    years: list[int] | None = None,
    output_dir: Path | None = None,
) -> Path:
    """Download ERA5 hourly data for a single location.

    Uses the CDS API 'reanalysis-era5-single-levels' dataset. Downloads a small
    spatial area (0.25 deg box) around the target point.

    On 'cost limits exceeded' errors, retries with a reduced year range.

    Args:
        lat: Latitude.
        lon: Longitude.
        location_id: Identifier for this location (used in filename).
        variables: ERA5 variable names. Defaults to ERA5_VARIABLES.
        years: Years to download. Defaults to ERA5_YEARS.
        output_dir: Where to save. Defaults to data/raw/era5/.

    Returns:
        Path to the downloaded NetCDF file.
    """
    import cdsapi

    variables = variables or ERA5_VARIABLES
    years = years or ERA5_YEARS
    output_dir = output_dir or ERA5_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    outfile = output_dir / f"{location_id}_era5_hourly.nc"
    if outfile.exists():
        logger.info(f"ERA5 file already exists: {outfile}")
        return outfile

    delta = 0.125
    area = [lat + delta, lon - delta, lat - delta, lon + delta]  # N, W, S, E

    client = cdsapi.Client()

    def _retrieve(yr_list: list[int]) -> None:
        client.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "variable": variables,
                "year": [str(y) for y in yr_list],
                "month": [f"{m:02d}" for m in range(1, 13)],
                "day": [f"{d:02d}" for d in range(1, 32)],
                "time": [f"{h:02d}:00" for h in range(24)],
                "area": area,
                "format": "netcdf",
            },
            str(outfile),
        )

    try:
        _retrieve(years)
        logger.info(f"Downloaded ERA5 data to {outfile}")
    except Exception as e:
        if "cost limits exceeded" in str(e) or "too large" in str(e):
            logger.warning(
                f"ERA5 request too large for {location_id} ({len(years)} years). "
                "Retrying with 2024 only..."
            )
            _retrieve([2024])
            logger.info(f"Downloaded ERA5 (2024 only) to {outfile}")
        else:
            raise

    return outfile


def download_openmeteo(
    lat: float,
    lon: float,
    location_id: str,
    output_dir: Path | None = None,
    years: int = 2024,
) -> Path:
    """Download climate data from Open-Meteo API (free, no API key, no rate limits).

    Open-Meteo provides hourly and daily climate variables including temperature,
    relative humidity, dewpoint, wind, and solar radiation. No authentication needed.

    Variables used for psychrometric derivation:
        - temperature_2m (°C)
        - relative_humidity_2m (%)
        - dew_point_2m (°C)
        - wind_speed_10m (m/s)
        - shortwave_radiation (MJ/m²)
        - precipitation (mm)

    Args:
        lat: Latitude.
        lon: Longitude.
        location_id: Identifier for this location (used in filename).
        output_dir: Where to save. Defaults to data/raw/era5/.
        years: Number of years to download (default: 2024).

    Returns:
        Path to the downloaded CSV file.
    """
    import httpx

    output_dir = output_dir or ERA5_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    outfile = output_dir / f"{location_id}_openmeteo.csv"
    if outfile.exists():
        logger.info(f"Open-Meteo file already exists: {outfile}")
        return outfile

    variables = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "wind_speed_10m",
        "shortwave_radiation",
        "precipitation",
    ]

    logger.info(f"Fetching Open-Meteo data for {location_id} ({lat}, {lon})...")

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(variables),
        "start_date": f"{years - 1}-01-01",
        "end_date": f"{years}-12-31",
        "timezone": "UTC",
    }

    with httpx.Client(timeout=60.0) as client:
        resp = client.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params=params,
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()

    hourly = data["hourly"]
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")

    # Save
    df.to_csv(outfile)
    logger.info(f"Saved Open-Meteo data to {outfile} ({len(df)} hourly records)")
    return outfile


def load_openmeteo(filepath: Path) -> pd.DataFrame:
    """Load Open-Meteo CSV into a DataFrame with datetime index."""
    df = pd.read_csv(filepath, parse_dates=["time"])
    df = df.set_index("time")
    return df


def compute_psychrometric_from_openmeteo(df: pd.DataFrame) -> dict[str, float]:
    """Compute annual mean psychrometric profile from Open-Meteo DataFrame.

    Args:
        df: DataFrame from load_openmeteo() with hourly values and columns:
            temperature_2m, relative_humidity_2m, dew_point_2m,
            wind_speed_10m, shortwave_radiation, precipitation

    Returns:
        Dict of annual mean psychrometric variables.
    """
    from src.climate.psychrometrics import (
        relative_humidity,
        wet_bulb_temperature,
        moist_air_enthalpy,
        humidity_ratio,
        evaporative_cooling_potential,
        wind_speed,
    )

    t_c = df["temperature_2m"].values
    rh = df["relative_humidity_2m"].values / 100.0
    t_dew_c = df["dew_point_2m"].values
    u = df["wind_speed_10m"].values
    v = np.zeros_like(u)
    ssrd = df["shortwave_radiation"].values * 3.6e3  # MJ/m2 -> J/m2 (/hourly)

    # Compute derived psychrometric variables
    vpd = (
        relative_humidity(t_c, t_dew_c) * 0.0
    )  # placeholder — use VPD from dewpoint directly
    w = humidity_ratio(t_dew_c)
    t_wb = wet_bulb_temperature(t_c, rh * 100.0)
    h = moist_air_enthalpy(t_c, w)
    ecp = evaporative_cooling_potential(t_c, t_wb)
    ws = wind_speed(u, v)

    profile = {
        "mean_dbt_c": float(np.nanmean(t_c)),
        "mean_rh": float(np.nanmean(rh)),
        "mean_rh_pct": float(np.nanmean(rh)) * 100.0,
        "mean_dewpoint_c": float(np.nanmean(t_dew_c)),
        "mean_wbt_c": float(np.nanmean(t_wb)),
        "mean_vpd_kpa": float(np.nanmean(t_c - t_dew_c)) * 0.1,  # rough VPD in kPa
        "mean_enthalpy_kj_kg": float(np.nanmean(h)),
        "mean_evap_cooling_potential_c": float(np.nanmean(ecp)),
        "mean_wind_speed_ms": float(np.nanmean(ws)),
        "mean_solar_radiation_wm2": float(np.nanmean(ssrd)) / 3600.0 if "shortwave_radiation" in df.columns else 0.0,
        "mean_diurnal_temp_range_c": float(
            np.nanmean(
                df["temperature_2m"].resample("D").max()
                - df["temperature_2m"].resample("D").min()
            )
        ),
        "hours_above_wbt_threshold": int(np.sum(t_wb > 26.0)),
    }

    return profile


def compute_monthly_profiles_openmeteo(df: pd.DataFrame) -> dict[str, list[float]]:
    """Compute monthly mean psychrometric profiles from Open-Meteo DataFrame."""
    from src.climate.psychrometrics import (
        relative_humidity,
        vapor_pressure_deficit,
        wet_bulb_temperature,
    )

    df = df.copy()
    df["month"] = df.index.month
    df["t_c"] = df["temperature_2m"]
    df["rh"] = df["relative_humidity_2m"] / 100.0
    df["rh_pct"] = df["relative_humidity_2m"]
    df["t_dew_c"] = df["dew_point_2m"]
    df["vpd_kpa"] = vapor_pressure_deficit(df["t_c"].values, df["t_dew_c"].values)
    df["wbt_c"] = wet_bulb_temperature(df["t_c"].values, df["rh_pct"].values)

    monthly = (
        df.groupby("month")
        .agg(
            t_c=("t_c", "mean"),
            rh_pct=("rh_pct", "mean"),
            vpd_kpa=("vpd_kpa", "mean"),
            wbt_c=("wbt_c", "mean"),
        )
        .sort_index()
    )

    return {
        "monthly_dbt": monthly["t_c"].tolist(),
        "monthly_rh": monthly["rh_pct"].tolist(),
        "monthly_vpd": monthly["vpd_kpa"].tolist(),
        "monthly_wbt": monthly["wbt_c"].tolist(),
    }


def load_era5_location(filepath: Path) -> pd.DataFrame:
    """Load downloaded ERA5 NetCDF for a single location into a DataFrame.

    Averages over the small spatial extent (effectively a point sample) and
    returns an hourly time series.
    """
    import xarray as xr

    ds = xr.open_dataset(filepath)

    # Average over spatial dimensions (latitude, longitude) if present
    spatial_dims = [d for d in ds.dims if d in ("latitude", "longitude")]
    if spatial_dims:
        ds = ds.mean(dim=spatial_dims)

    df = ds.to_dataframe().reset_index()
    return df


def compute_annual_psychrometric_profile(
    hourly_df: pd.DataFrame,
) -> dict[str, float]:
    """Compute annual mean psychrometric statistics from hourly ERA5 data.

    Expects columns produced by load_era5_location():
        t2m (K), d2m (K), sp (Pa), u10 (m/s), v10 (m/s), ssrd (J/m2)

    Returns dict of annual mean values.
    """
    from src.climate.psychrometrics import compute_psychrometric_profile

    # Map ERA5 variable names to function arguments
    # ERA5 uses short names: t2m, d2m, sp, u10, v10, ssrd
    psychro = compute_psychrometric_profile(
        t2m_k=hourly_df["t2m"].values,
        d2m_k=hourly_df["d2m"].values,
        sp_pa=hourly_df["sp"].values,
        u10=hourly_df.get("u10", pd.Series(dtype=float)).values if "u10" in hourly_df else None,
        v10=hourly_df.get("v10", pd.Series(dtype=float)).values if "v10" in hourly_df else None,
        ssrd_j=hourly_df.get("ssrd", pd.Series(dtype=float)).values
        if "ssrd" in hourly_df
        else None,
    )

    # Annual means
    profile = {}
    for key, values in psychro.items():
        profile[f"mean_{key}"] = float(np.nanmean(values))

    # Diurnal temperature range: mean of daily (max - min)
    if "time" in hourly_df.columns:
        hourly_df = hourly_df.copy()
        hourly_df["date"] = pd.to_datetime(hourly_df["time"]).dt.date
        daily_range = hourly_df.groupby("date")["t2m"].agg(lambda x: x.max() - x.min())
        profile["mean_diurnal_temp_range_c"] = float(daily_range.mean())

    # Hours above wet-bulb comfort threshold
    from src.utils.config import WBT_COMFORT_UPPER_C

    profile["hours_above_wbt_threshold"] = int(np.sum(psychro["wbt_c"] > WBT_COMFORT_UPPER_C))

    return profile


def compute_monthly_profiles(
    hourly_df: pd.DataFrame,
) -> dict[str, list[float]]:
    """Compute monthly mean psychrometric profiles (12-element vectors).

    Returns dict like:
        {"monthly_dbt": [jan, feb, ..., dec], "monthly_rh": [...], ...}
    """
    from src.climate.psychrometrics import (
        relative_humidity,
        vapor_pressure_deficit,
        wet_bulb_temperature,
    )

    df = hourly_df.copy()
    df["t_c"] = df["t2m"] - 273.15
    df["t_dew_c"] = df["d2m"] - 273.15
    df["rh"] = relative_humidity(df["t_c"].values, df["t_dew_c"].values)
    df["rh_pct"] = df["rh"] * 100.0
    df["vpd_kpa"] = vapor_pressure_deficit(df["t_c"].values, df["t_dew_c"].values)
    df["wbt_c"] = wet_bulb_temperature(df["t_c"].values, df["rh_pct"].values)

    if "time" in df.columns:
        df["month"] = pd.to_datetime(df["time"]).dt.month
    elif "valid_time" in df.columns:
        df["month"] = pd.to_datetime(df["valid_time"]).dt.month
    else:
        raise ValueError("No time column found in ERA5 data")

    monthly = (
        df.groupby("month")
        .agg(
            {
                "t_c": "mean",
                "rh_pct": "mean",
                "vpd_kpa": "mean",
                "wbt_c": "mean",
            }
        )
        .sort_index()
    )

    return {
        "monthly_dbt": monthly["t_c"].tolist(),
        "monthly_rh": monthly["rh_pct"].tolist(),
        "monthly_vpd": monthly["vpd_kpa"].tolist(),
        "monthly_wbt": monthly["wbt_c"].tolist(),
    }
