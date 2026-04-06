"""Psychrometric derivation functions.

Converts raw ERA5 fields (dry-bulb temperature, dewpoint, pressure) into the
full set of psychrometric variables used throughout the project.

References:
    - ASHRAE Fundamentals (2021), Chapter 1: Psychrometrics
    - Stull, R. (2011). Wet-bulb temperature from relative humidity and air
      temperature. J. Appl. Meteor. Climatol., 50, 2267-2269.
    - PsychroLib: https://github.com/psychrometrics/psychrolib
"""

from __future__ import annotations

import math

import numpy as np


# ── Saturation vapor pressure (Magnus formula) ────────────────────────────────


def saturation_vapor_pressure(t_c: float | np.ndarray) -> float | np.ndarray:
    """Saturation vapor pressure over water (Pa) from dry-bulb temperature (C).

    Uses the Magnus-Tetens approximation:
        e_s = 610.94 * exp(17.625 * T / (T + 243.04))
    """
    return 610.94 * np.exp(17.625 * t_c / (t_c + 243.04))


def actual_vapor_pressure(t_dewpoint_c: float | np.ndarray) -> float | np.ndarray:
    """Actual vapor pressure (Pa) from dewpoint temperature (C)."""
    return saturation_vapor_pressure(t_dewpoint_c)


# ── Relative humidity ──────────────────────────────────────────────────────────


def relative_humidity(t_c: float | np.ndarray, t_dew_c: float | np.ndarray) -> float | np.ndarray:
    """Relative humidity (0-1) from dry-bulb and dewpoint temperatures (C)."""
    return actual_vapor_pressure(t_dew_c) / saturation_vapor_pressure(t_c)


# ── Humidity ratio ─────────────────────────────────────────────────────────────


def humidity_ratio(t_dew_c: float | np.ndarray, p_pa: float = 101325.0) -> float | np.ndarray:
    """Humidity ratio W (kg water / kg dry air) from dewpoint and pressure.

    W = 0.621945 * e_a / (p - e_a)
    """
    e_a = actual_vapor_pressure(t_dew_c)
    return 0.621945 * e_a / (p_pa - e_a)


# ── Vapor pressure deficit ────────────────────────────────────────────────────


def vapor_pressure_deficit(
    t_c: float | np.ndarray, t_dew_c: float | np.ndarray
) -> float | np.ndarray:
    """Vapor pressure deficit (Pa) = e_s(T) - e_a(T_d).

    Returns in kPa for consistency with ecological convention.
    """
    vpd_pa = saturation_vapor_pressure(t_c) - actual_vapor_pressure(t_dew_c)
    return vpd_pa / 1000.0  # kPa


# ── Wet-bulb temperature (Stull 2011 approximation) ──────────────────────────


def wet_bulb_temperature(t_c: float | np.ndarray, rh_pct: float | np.ndarray) -> float | np.ndarray:
    """Wet-bulb temperature (C) from dry-bulb (C) and relative humidity (%).

    Uses the Stull (2011) empirical regression, valid for:
        RH: 5-99%, T: -20 to 50 C
        Accuracy: +/- 0.3 C for most conditions

    Reference:
        Stull, R. (2011). J. Appl. Meteor. Climatol., 50, 2267-2269.
    """
    t = t_c
    rh = rh_pct
    tw = (
        t * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
        + np.arctan(t + rh)
        - np.arctan(rh - 1.676331)
        + 0.00391838 * rh**1.5 * np.arctan(0.023101 * rh)
        - 4.686035
    )
    return tw


# ── Enthalpy of moist air ────────────────────────────────────────────────────


def moist_air_enthalpy(t_c: float | np.ndarray, w: float | np.ndarray) -> float | np.ndarray:
    """Enthalpy of moist air (kJ/kg dry air).

    h = 1.006 * T + W * (2501 + 1.86 * T)

    Args:
        t_c: Dry-bulb temperature (C)
        w: Humidity ratio (kg/kg)
    """
    return 1.006 * t_c + w * (2501.0 + 1.86 * t_c)


# ── Evaporative cooling potential ─────────────────────────────────────────────


def evaporative_cooling_potential(
    t_c: float | np.ndarray, t_wb_c: float | np.ndarray
) -> float | np.ndarray:
    """Wet-bulb depression (C) = T_db - T_wb.

    A proxy for how much cooling evaporation can provide.
    Higher values = more evaporative cooling available.
    """
    return t_c - t_wb_c


# ── Wind speed from u/v components ────────────────────────────────────────────


def wind_speed(u: float | np.ndarray, v: float | np.ndarray) -> float | np.ndarray:
    """Wind speed (m/s) from u and v components."""
    return np.sqrt(u**2 + v**2)


# ── Full psychrometric profile from ERA5 fields ──────────────────────────────


def compute_psychrometric_profile(
    t2m_k: np.ndarray,
    d2m_k: np.ndarray,
    sp_pa: np.ndarray,
    u10: np.ndarray | None = None,
    v10: np.ndarray | None = None,
    ssrd_j: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Compute all psychrometric variables from ERA5 hourly fields.

    Args:
        t2m_k: 2m temperature (K)
        d2m_k: 2m dewpoint temperature (K)
        sp_pa: Surface pressure (Pa)
        u10: 10m u-wind component (m/s), optional
        v10: 10m v-wind component (m/s), optional
        ssrd_j: Surface solar radiation downwards (J/m2), optional

    Returns:
        Dictionary of derived psychrometric variables.
    """
    # Convert Kelvin to Celsius
    t_c = t2m_k - 273.15
    t_dew_c = d2m_k - 273.15

    rh = relative_humidity(t_c, t_dew_c)
    rh_pct = rh * 100.0
    w = humidity_ratio(t_dew_c, sp_pa)
    vpd = vapor_pressure_deficit(t_c, t_dew_c)
    t_wb = wet_bulb_temperature(t_c, rh_pct)
    h = moist_air_enthalpy(t_c, w)
    ecp = evaporative_cooling_potential(t_c, t_wb)

    result = {
        "dbt_c": t_c,
        "dewpoint_c": t_dew_c,
        "rh": rh,
        "rh_pct": rh_pct,
        "humidity_ratio": w,
        "vpd_kpa": vpd,
        "wbt_c": t_wb,
        "enthalpy_kj_kg": h,
        "evap_cooling_potential_c": ecp,
        "pressure_pa": sp_pa,
    }

    if u10 is not None and v10 is not None:
        result["wind_speed_ms"] = wind_speed(u10, v10)

    if ssrd_j is not None:
        # Convert accumulated J/m2 to mean W/m2 (assuming hourly accumulation)
        result["solar_radiation_wm2"] = ssrd_j / 3600.0

    return result
