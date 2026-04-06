"""Animal thermoregulatory feature schema and validation.

Defines the canonical column set for Table 2 (Animal Thermoregulatory Features)
and provides validation/loading utilities.
"""

from __future__ import annotations

import pandas as pd

# ── Column definitions ─────────────────────────────────────────────────────────

# Each tuple: (column_name, dtype, required, description)
ANIMAL_SCHEMA = [
    # Identity
    ("species_id", "str", True, "Taxonomic identifier (e.g., GBIF key)"),
    ("common_name", "str", True, "Common English name"),
    ("scientific_name", "str", True, "Binomial name"),
    ("clade", "str", True, "mammal / bird / reptile / amphibian / insect"),
    ("climate_zone_id", "str", True, "FK to climate zones table"),
    # Body metrics
    ("body_mass_kg", "float", True, "Body mass in kg"),
    ("sa_vol_ratio", "float", False, "Surface area to volume ratio"),
    # Respiratory exchange
    (
        "nasal_turbinate_complexity",
        "str",
        False,
        "none / simple / moderate / complex / highly_complex",
    ),
    ("respiratory_water_recovery_pct", "float", False, "Percent of exhaled moisture recovered"),
    ("panting_strategy", "str", False, "none / thermal_panting / lateral_nasal / gular_flutter"),
    # Cutaneous exchange
    ("sweating_capacity", "str", False, "none / eccrine_low / eccrine_high / apocrine"),
    ("cutaneous_ewl_mg_h_cm2", "float", False, "Cutaneous evaporative water loss rate"),
    ("skin_permeability_index", "float", False, "Relative skin water permeability"),
    ("fur_density_hairs_cm2", "float", False, "Hair density"),
    ("fur_depth_mm", "float", False, "Fur/feather insulation depth"),
    ("insulation_conductance_w_m2k", "float", False, "Thermal conductance of pelage/plumage"),
    # Vascular / radiative
    ("appendage_sa_ratio", "float", False, "Appendage SA relative to body SA"),
    ("vascular_appendage_type", "str", False, "ears / bill / horns / tail / fins / none"),
    ("countercurrent_system", "str", False, "none / limb / nasal / carotid_rete / multiple"),
    ("coloration_lightness", "float", False, "Reflectance/albedo proxy (0-1)"),
    # Behavioral
    ("burrowing", "bool", False, "Uses burrows for thermal refuge"),
    ("nocturnal_fraction", "float", False, "Fraction of activity at night (0-1)"),
    ("shade_seeking", "bool", False, "Actively seeks shade in heat"),
    ("huddling", "bool", False, "Social thermoregulation in cold"),
    ("posture_adjustment", "bool", False, "Changes posture for thermal control"),
    # Thermal performance
    ("tnz_lower_critical_c", "float", False, "Lower critical temperature (C)"),
    ("tnz_upper_critical_c", "float", False, "Upper critical temperature (C)"),
    ("bmr_w_kg", "float", False, "Basal metabolic rate (W/kg)"),
    ("max_evaporative_capacity", "float", False, "Maximum evaporative heat loss"),
    ("thermal_conductance_min", "float", False, "Minimum whole-body thermal conductance"),
    # Strategy tags (legacy single-axis)
    (
        "primary_cooling",
        "str",
        True,
        "evaporative / radiative / convective / conductive / shading / combined",
    ),
    ("primary_heating", "str", True, "metabolic / insulative / solar / conductive / combined"),
    (
        "water_conservation",
        "str",
        False,
        "recovery / reduction / buffering / ventilation / evaporation / combined / none",
    ),
    # Strategy tags (4-axis ontology)
    (
        "collection_strategy",
        "str",
        True,
        "solar / metabolic / communal / environmental / combined / none",
    ),
    (
        "transfer_strategy",
        "str",
        True,
        "evaporative / radiative / convective / conductive / combined",
    ),
    (
        "storage_strategy",
        "str",
        True,
        "sensible_mass / latent_pcm / chemical_fuel / diurnal_shift / seasonal_store / combined / none",
    ),
    (
        "regulation_strategy",
        "str",
        True,
        "insulation_mod / flow_mod / surface_mod / permeability_mod / geometry_mod / combined / none",
    ),
    # Metadata
    ("data_quality", "str", False, "measured / estimated / unknown per field"),
    ("thermoreg_notes", "str", False, "Free-text notes on unique adaptations"),
    ("key_references", "str", False, "Semicolon-separated citation keys"),
]


def get_column_names() -> list[str]:
    """Return ordered list of column names."""
    return [col[0] for col in ANIMAL_SCHEMA]


def get_required_columns() -> list[str]:
    """Return list of required column names."""
    return [col[0] for col in ANIMAL_SCHEMA if col[2]]


def create_empty_dataframe() -> pd.DataFrame:
    """Create an empty DataFrame with all schema columns."""
    return pd.DataFrame(columns=get_column_names())


def validate(df: pd.DataFrame) -> list[str]:
    """Validate a DataFrame against the animal schema.

    Returns list of validation error messages (empty = valid).
    """
    errors = []

    # Check required columns exist
    for col_name, _, required, _ in ANIMAL_SCHEMA:
        if required and col_name not in df.columns:
            errors.append(f"Missing required column: {col_name}")

    # Check required columns have no nulls
    for col_name, _, required, _ in ANIMAL_SCHEMA:
        if required and col_name in df.columns:
            n_null = df[col_name].isna().sum()
            if n_null > 0:
                errors.append(f"Required column '{col_name}' has {n_null} null values")

    # Check enum values
    enum_checks = {
        "clade": {"mammal", "bird"},
        "nasal_turbinate_complexity": {
            "none",
            "simple",
            "moderate",
            "complex",
            "highly_complex",
        },
        "panting_strategy": {
            "none",
            "thermal_panting",
            "lateral_nasal",
            "gular_flutter",
        },
        "sweating_capacity": {
            "none",
            "eccrine_low",
            "eccrine_high",
            "apocrine",
        },
        "countercurrent_system": {
            "none",
            "limb",
            "nasal",
            "carotid_rete",
            "multiple",
        },
        "collection_strategy": {"solar", "metabolic", "communal", "environmental", "combined", "none"},
        "transfer_strategy": {"evaporative", "radiative", "convective", "conductive", "combined"},
        "storage_strategy": {"sensible_mass", "latent_pcm", "chemical_fuel", "diurnal_shift", "seasonal_store", "combined", "none"},
        "regulation_strategy": {"insulation_mod", "flow_mod", "surface_mod", "permeability_mod", "geometry_mod", "combined", "none"},
    }

    for col, valid_vals in enum_checks.items():
        if col in df.columns:
            invalid = df[col].dropna()
            bad = set(invalid.unique()) - valid_vals
            if bad:
                errors.append(f"Column '{col}' has invalid values: {bad}")

    # Check numeric ranges
    if "coloration_lightness" in df.columns:
        vals = df["coloration_lightness"].dropna()
        if (vals < 0).any() or (vals > 1).any():
            errors.append("coloration_lightness must be in [0, 1]")

    if "nocturnal_fraction" in df.columns:
        vals = df["nocturnal_fraction"].dropna()
        if (vals < 0).any() or (vals > 1).any():
            errors.append("nocturnal_fraction must be in [0, 1]")

    return errors
