"""AlphaEarth Foundations satellite embedding extraction via Google Earth Engine.

Extracts 64-dimensional learned embeddings from the AlphaEarth V1 Annual
collection for any given (lat, lon) or set of locations.

Reference:
    Brown, Kazmierski, Pasquarella et al. (2025). "AlphaEarth Foundations."
    arXiv:2507.22291.
    GEE asset: GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from src.utils.config import ALPHAEARTH_BANDS, ALPHAEARTH_COLLECTION, ALPHAEARTH_SCALE_M

logger = logging.getLogger(__name__)


def _init_ee() -> Any:
    """Initialize Earth Engine with service account credentials and return the ee module."""
    import json
    from pathlib import Path

    import ee

    credentials_path = Path.home() / ".config" / "earthengine" / "credentials"

    if credentials_path.exists():
        try:
            with open(credentials_path) as f:
                creds_data = json.load(f)
            email = creds_data["client_email"]
            credentials = ee.ServiceAccountCredentials(email, str(credentials_path))
            ee.Initialize(credentials=credentials)
        except Exception:
            try:
                ee.Initialize()
            except Exception:
                ee.Authenticate()
                ee.Initialize()
    else:
        try:
            ee.Initialize()
        except Exception:
            ee.Authenticate()
            ee.Initialize()

    return ee


def get_embedding(
    lat: float,
    lon: float,
    year: int = 2024,
    scale: int = ALPHAEARTH_SCALE_M,
) -> np.ndarray:
    """Extract a 64D AlphaEarth embedding for a single point.

    AlphaEarth is a tiled collection — each tile covers a regional UTM zone.
    This function filters by both date AND geometry to find the correct tile
    for the given coordinates.

    Args:
        lat: Latitude (WGS84).
        lon: Longitude (WGS84).
        year: Year of annual composite (2017-2024).
        scale: Sampling scale in meters (default: 10m native).

    Returns:
        64-element numpy array of embedding values.
    """
    ee = _init_ee()

    point = ee.Geometry.Point([lon, lat])
    collection = ee.ImageCollection(ALPHAEARTH_COLLECTION)
    img = (
        collection.filter(ee.Filter.date(f"{year}-01-01", f"{year + 1}-01-01"))
        .filter(ee.Filter.geometry(point))
        .first()
    )

    result = img.reduceRegion(ee.Reducer.mean(), point, scale).getInfo()
    embedding = np.array([result[band] for band in ALPHAEARTH_BANDS], dtype=np.float32)
    return embedding


def get_embeddings_batch(
    locations: pd.DataFrame,
    year: int = 2024,
    scale: int = ALPHAEARTH_SCALE_M,
    buffer_m: int = 0,
) -> pd.DataFrame:
    """Extract AlphaEarth embeddings for multiple locations.

    AlphaEarth is a tiled collection — filters by geometry to find the correct
    UTM-zone tile for each point before sampling.

    Args:
        locations: DataFrame with columns 'location_id', 'lat', 'lon'.
        year: Year of annual composite.
        scale: Sampling scale in meters.
        buffer_m: If > 0, average embeddings within this buffer radius (meters).

    Returns:
        DataFrame with location_id + 64 embedding columns (ae_00..ae_63).
    """
    ee = _init_ee()
    collection = ee.ImageCollection(ALPHAEARTH_COLLECTION)

    results = []
    for _, row in locations.iterrows():
        loc_id = row["location_id"]
        lat, lon = row["lat"], row["lon"]

        try:
            point = ee.Geometry.Point([lon, lat])
            img = (
                collection.filter(ee.Filter.date(f"{year}-01-01", f"{year + 1}-01-01"))
                .filter(ee.Filter.geometry(point))
                .first()
            )

            if buffer_m > 0:
                region = point.buffer(buffer_m)
                result = img.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=region,
                    scale=scale,
                    maxPixels=1e6,
                ).getInfo()
            else:
                result = img.reduceRegion(
                    ee.Reducer.mean(), point, scale
                ).getInfo()

            embedding = {f"ae_{i:02d}": result[ALPHAEARTH_BANDS[i]] for i in range(64)}
            embedding["location_id"] = loc_id
            results.append(embedding)
            logger.info(f"Extracted embedding for {loc_id} ({lat:.3f}, {lon:.3f})")

        except Exception as e:
            logger.warning(f"Failed to extract embedding for {loc_id}: {e}")
            embedding = {f"ae_{i:02d}": np.nan for i in range(64)}
            embedding["location_id"] = loc_id
            results.append(embedding)

    df = pd.DataFrame(results)
    col_order = ["location_id"] + [f"ae_{i:02d}" for i in range(64)]
    return df[col_order]


def validate_embeddings(df: pd.DataFrame) -> dict:
    """Run basic validation on extracted embeddings.

    Returns dict with validation results: completeness, norm check, etc.
    """
    ae_cols = [c for c in df.columns if c.startswith("ae_")]
    ae_data = df[ae_cols].values

    n_missing = np.isnan(ae_data).sum()
    norms = np.linalg.norm(ae_data, axis=1)  # should be ~1.0 (unit length)

    return {
        "n_locations": len(df),
        "n_missing_values": int(n_missing),
        "mean_norm": float(np.nanmean(norms)),
        "min_norm": float(np.nanmin(norms)),
        "max_norm": float(np.nanmax(norms)),
        "all_unit_length": bool(np.allclose(norms[~np.isnan(norms)], 1.0, atol=0.05)),
    }
