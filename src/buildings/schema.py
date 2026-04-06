"""Building / vernacular design feature schema and validation.

Defines the canonical column set for Table 3 (Building Design Features)
and provides validation/loading utilities.
"""

from __future__ import annotations

import pandas as pd

# ── Column definitions ─────────────────────────────────────────────────────────

BUILDING_SCHEMA = [
    # Identity
    ("building_id", "str", True, "Unique identifier"),
    ("tradition_name", "str", True, "e.g. 'Iranian windcatcher house', 'Inuit igloo'"),
    ("region", "str", True, "Geographic region"),
    ("climate_zone_id", "str", True, "FK to climate zones table"),
    ("building_type", "str", True, "vernacular / modern_passive / biomimetic"),
    ("era", "str", False, "Historical period or 'contemporary'"),
    # Envelope
    ("wall_thickness_cm", "float", False, "Wall thickness"),
    ("wall_material", "str", False, "adobe / stone / timber / brick / reed / ice / etc."),
    ("thermal_mass_level", "str", False, "low / medium / high / very_high"),
    ("insulation_r_value", "float", False, "R-value (m2 K/W)"),
    ("envelope_porosity", "str", False, "sealed / semi_porous / porous / open"),
    ("surface_albedo", "float", False, "Exterior reflectance (0-1)"),
    ("roof_material", "str", False, "Roof material"),
    ("roof_form", "str", False, "flat / pitched / domed / vaulted / green"),
    # Ventilation / Airflow
    ("natural_ventilation_type", "str", False, "none / cross / stack / wind_driven / combined"),
    ("has_windcatcher", "bool", False, "Has windcatcher"),
    ("has_courtyard", "bool", False, "Has courtyard"),
    ("chimney_stack_effect", "bool", False, "Uses chimney/stack effect"),
    ("ventilation_control", "str", False, "fixed / operable / automated"),
    # Moisture management
    ("evaporative_cooling_type", "str", False, "none / direct / indirect / combined"),
    ("water_feature_type", "str", False, "none / fountain / channel / pool / misting"),
    ("breathable_walls", "bool", False, "Walls permit vapor diffusion"),
    ("humidity_control_type", "str", False, "none / natural / desiccant / mechanical"),
    # Solar / radiation
    (
        "shading_strategy",
        "str",
        False,
        "none / overhang / screen / mashrabiya / vegetation / combined",
    ),
    ("glazing_ratio", "float", False, "Window-to-wall ratio (0-1)"),
    ("orientation_strategy", "str", False, "e.g. 'long axis E-W', 'minimized west exposure'"),
    ("radiative_cooling", "bool", False, "Uses sky radiative cooling"),
    # Thermal storage / earth
    ("night_flushing", "bool", False, "Night ventilation to cool thermal mass"),
    ("earth_sheltering", "bool", False, "Partially/fully underground"),
    ("earth_tubes", "bool", False, "Uses earth-air heat exchangers"),
    ("phase_change_materials", "bool", False, "Uses PCMs"),
    # Heat recovery
    ("heat_recovery_type", "str", False, "none / air_to_air / earth_coupled / water_based"),
    # Strategy tags (legacy single-axis)
    (
        "primary_cooling",
        "str",
        True,
        "evaporative / radiative / convective / conductive / massive / combined",
    ),
    (
        "primary_heating",
        "str",
        True,
        "metabolic / insulative / solar / massive / conductive / combined / none",
    ),
    (
        "moisture_strategy",
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
    ("design_notes", "str", False, "Free-text description of notable features"),
    ("key_references", "str", False, "Semicolon-separated citation keys"),
]


def get_column_names() -> list[str]:
    return [col[0] for col in BUILDING_SCHEMA]


def get_required_columns() -> list[str]:
    return [col[0] for col in BUILDING_SCHEMA if col[2]]


def create_empty_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=get_column_names())


def validate(df: pd.DataFrame) -> list[str]:
    """Validate a DataFrame against the building schema."""
    errors = []

    for col_name, _, required, _ in BUILDING_SCHEMA:
        if required and col_name not in df.columns:
            errors.append(f"Missing required column: {col_name}")
        if required and col_name in df.columns:
            n_null = df[col_name].isna().sum()
            if n_null > 0:
                errors.append(f"Required column '{col_name}' has {n_null} null values")

    enum_checks = {
        "building_type": {"vernacular", "modern_passive", "biomimetic"},
        "thermal_mass_level": {"low", "medium", "high", "very_high"},
        "envelope_porosity": {"sealed", "semi_porous", "porous", "open"},
        "roof_form": {"flat", "pitched", "domed", "vaulted", "green"},
        "natural_ventilation_type": {
            "none",
            "cross",
            "stack",
            "wind_driven",
            "combined",
        },
        "evaporative_cooling_type": {"none", "direct", "indirect", "combined"},
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

    # Range checks
    for col in ("surface_albedo", "glazing_ratio"):
        if col in df.columns:
            vals = df[col].dropna()
            if (vals < 0).any() or (vals > 1).any():
                errors.append(f"{col} must be in [0, 1]")

    return errors
