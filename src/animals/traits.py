"""Animal trait compilation from external databases.

Pulls baseline traits from PanTHERIA, AVONET, GBIF, and AnimalTraits,
then merges them into the project schema.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.utils.config import RAW_DIR

logger = logging.getLogger(__name__)

TRAITS_DIR = RAW_DIR / "traits"


# ── GBIF occurrence data ──────────────────────────────────────────────────────


def get_gbif_occurrences(
    scientific_name: str,
    limit: int = 300,
) -> pd.DataFrame:
    """Fetch occurrence records from GBIF for a species.

    Returns DataFrame with columns: lat, lon, year, country.
    """
    try:
        from pygbif import occurrences
    except ImportError:
        raise ImportError("Install pygbif: pip install pygbif")

    results = occurrences.search(
        scientificName=scientific_name,
        hasCoordinate=True,
        limit=limit,
    )

    records = []
    for r in results.get("results", []):
        if "decimalLatitude" in r and "decimalLongitude" in r:
            records.append(
                {
                    "lat": r["decimalLatitude"],
                    "lon": r["decimalLongitude"],
                    "year": r.get("year"),
                    "country": r.get("country"),
                }
            )

    return pd.DataFrame(records)


def get_occurrence_centroid(scientific_name: str, limit: int = 300) -> tuple[float, float]:
    """Get the median occurrence location for a species from GBIF.

    Returns (lat, lon) tuple.
    """
    df = get_gbif_occurrences(scientific_name, limit=limit)
    if df.empty:
        raise ValueError(f"No GBIF occurrences found for {scientific_name}")
    return float(df["lat"].median()), float(df["lon"].median())


# ── PanTHERIA mammal traits ──────────────────────────────────────────────────


def load_pantheria(filepath: Path | None = None) -> pd.DataFrame:
    """Load the PanTHERIA mammalian trait database.

    PanTHERIA uses -999 as a missing value sentinel.

    Download from:
        https://esapubs.org/archive/ecol/E090/184/PanTHERIA_1-0_WR05_Aug2008.txt
    """
    filepath = filepath or TRAITS_DIR / "PanTHERIA_1-0_WR05_Aug2008.txt"
    if not filepath.exists():
        logger.warning(
            f"PanTHERIA file not found at {filepath}. "
            "Download from https://esapubs.org/archive/ecol/E090/184/"
        )
        return pd.DataFrame()

    df = pd.read_csv(filepath, sep="\t", encoding="latin-1")
    # Replace -999 with NaN
    df = df.replace(-999, pd.NA).replace(-999.0, pd.NA)
    return df


def extract_pantheria_traits(
    pantheria_df: pd.DataFrame,
    scientific_name: str,
) -> dict:
    """Extract relevant traits for a species from PanTHERIA.

    Returns dict with: body_mass_kg, bmr_w_kg (if available).
    """
    match = pantheria_df[pantheria_df["MSW05_Binomial"].str.lower() == scientific_name.lower()]
    if match.empty:
        return {}

    row = match.iloc[0]
    traits = {}

    # Body mass (PanTHERIA stores in grams)
    mass_g = row.get("5-1_AdultBodyMass_g")
    if pd.notna(mass_g):
        traits["body_mass_kg"] = float(mass_g) / 1000.0

    # BMR (PanTHERIA stores in mL O2/hr)
    bmr = row.get("5-2_BasalMetRateMass_g")
    if pd.notna(bmr):
        # Approximate conversion: 1 mL O2/hr ~ 0.0056 W
        # BMR per kg = (bmr_mL_O2_hr * 0.0056) / mass_kg
        if "body_mass_kg" in traits and traits["body_mass_kg"] > 0:
            traits["bmr_w_kg"] = float(bmr) * 0.0056 / traits["body_mass_kg"]

    return traits


# ── AVONET bird traits ────────────────────────────────────────────────────────


def load_avonet(filepath: Path | None = None) -> pd.DataFrame:
    """Load the AVONET bird morphological trait database.

    Download from:
        https://figshare.com/s/b990722d72a26b5bfead (AVONET Supplementary dataset 1)
    """
    filepath = filepath or TRAITS_DIR / "AVONET_BirdLife.csv"
    if not filepath.exists():
        logger.warning(
            f"AVONET file not found at {filepath}. "
            "Download from https://figshare.com/s/b990722d72a26b5bfead"
        )
        return pd.DataFrame()

    return pd.read_csv(filepath)


def extract_avonet_traits(
    avonet_df: pd.DataFrame,
    scientific_name: str,
) -> dict:
    """Extract relevant traits for a bird species from AVONET.

    Returns dict with: body_mass_kg, beak_length_mm, wing_length_mm.
    """
    match = avonet_df[avonet_df["Species1"].str.lower() == scientific_name.lower()]
    if match.empty:
        return {}

    row = match.iloc[0]
    traits = {}

    mass = row.get("Mass")
    if pd.notna(mass):
        traits["body_mass_kg"] = float(mass) / 1000.0

    beak = row.get("Beak.Length_Culmen")
    if pd.notna(beak):
        traits["beak_length_mm"] = float(beak)

    wing = row.get("Wing.Length")
    if pd.notna(wing):
        traits["wing_length_mm"] = float(wing)

    return traits
