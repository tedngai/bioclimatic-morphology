"""Project-wide configuration: paths, constants, and pilot location definitions."""

from pathlib import Path

# ── Project paths ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PILOT_DIR = DATA_DIR / "pilot"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
MODELS_DIR = OUTPUTS_DIR / "models"

# ── AlphaEarth ─────────────────────────────────────────────────────────────────

ALPHAEARTH_COLLECTION = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
ALPHAEARTH_BANDS = [f"A{i:02d}" for i in range(64)]
ALPHAEARTH_YEAR = 2024
ALPHAEARTH_SCALE_M = 10  # native resolution

# ── ERA5 ───────────────────────────────────────────────────────────────────────

ERA5_VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "surface_pressure",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "surface_solar_radiation_downwards",
    "total_precipitation",
]
ERA5_YEARS = list(range(2014, 2025))  # 10-year window ending 2024

# ── Pilot locations ────────────────────────────────────────────────────────────

PILOT_LOCATIONS = [
    {
        "location_id": "hot_dry_riyadh",
        "name": "Riyadh, Saudi Arabia",
        "lat": 24.7136,
        "lon": 46.6753,
        "koppen": "BWh",
        "character": "High DBT, very low RH, huge diurnal range",
    },
    {
        "location_id": "hot_humid_malindi",
        "name": "Malindi, Kenya",
        "lat": -3.2138,
        "lon": 40.1169,
        "koppen": "Aw",
        "character": "Hot-humid tropical coast, monsoonal, Swahili vernacular architecture",
    },
    {
        "location_id": "temperate_fez",
        "name": "Fez, Morocco",
        "lat": 34.0181,
        "lon": -5.0078,
        "koppen": "Csa",
        "character": "Mediterranean, hot dry summers, mild wet winters, riad tradition",
    },
    {
        "location_id": "cold_dry_ulaanbaatar",
        "name": "Ulaanbaatar, Mongolia",
        "lat": 47.9184,
        "lon": 106.9177,
        "koppen": "Dwb",
        "character": "Very low winter DBT, extremely low RH, continental extreme",
    },
    {
        "location_id": "cold_humid_reykjavik",
        "name": "Reykjavik, Iceland",
        "lat": 64.1355,
        "lon": -21.8954,
        "koppen": "Cfc",
        "character": "Subarctic maritime, cool summers, mild winters, high RH, turf house tradition",
    },
]

# ── Core-scale locations (Stage A expansion) ───────────────────────────────────

CORE_LOCATIONS = [
    # Existing pilot zones (already have data)
    {"location_id": "hot_dry_riyadh", "name": "Riyadh, Saudi Arabia", "lat": 24.7136, "lon": 46.6753, "koppen": "BWh", "character": "High DBT, very low RH, huge diurnal range"},
    {"location_id": "hot_humid_malindi", "name": "Malindi, Kenya", "lat": -3.2138, "lon": 40.1169, "koppen": "Aw", "character": "Hot-humid tropical coast, monsoonal"},
    {"location_id": "temperate_fez", "name": "Fez, Morocco", "lat": 34.0181, "lon": -5.0078, "koppen": "Csa", "character": "Mediterranean, hot dry summers, mild wet winters"},
    {"location_id": "cold_dry_ulaanbaatar", "name": "Ulaanbaatar, Mongolia", "lat": 47.9184, "lon": 106.9177, "koppen": "Dwb", "character": "Continental extreme, very low winter DBT"},
    {"location_id": "cold_humid_reykjavik", "name": "Reykjavik, Iceland", "lat": 64.1355, "lon": -21.8954, "koppen": "Cfc", "character": "Subarctic maritime, turf house tradition"},
    # New zones
    {"location_id": "hot_arid_jaisalmer", "name": "Jaisalmer, India", "lat": 26.9157, "lon": 70.9083, "koppen": "BWh", "character": "Thar Desert, stone haveli tradition, extreme heat"},
    {"location_id": "hot_arid_timbuktu", "name": "Timbuktu, Mali", "lat": 16.7735, "lon": -3.0074, "koppen": "BWh", "character": "Sahelian, mud-brick vernacular, extreme dry heat"},
    {"location_id": "hot_humid_bangkok", "name": "Bangkok, Thailand", "lat": 13.7563, "lon": 100.5018, "koppen": "Aw", "character": "Hot-humid monsoonal, Thai stilt house tradition"},
    {"location_id": "hot_humid_manaus", "name": "Manaus, Brazil", "lat": -3.1190, "lon": -60.0217, "koppen": "Af", "character": "Equatorial rainforest, indigenous raised platform architecture"},
    {"location_id": "hot_humid_abidjan", "name": "Abidjan, Côte d'Ivoire", "lat": 5.3600, "lon": -4.0083, "koppen": "Am", "character": "Tropical savanna, West African vernacular"},
    {"location_id": "med_isfahan", "name": "Isfahan, Iran", "lat": 32.6546, "lon": 51.6680, "koppen": "BSk", "character": "Cold semi-arid, Persian courtyard house tradition"},
    {"location_id": "med_aleppo", "name": "Aleppo, Syria", "lat": 36.2021, "lon": 37.1343, "koppen": "Csa", "character": "Mediterranean, limestone houses, courtyard tradition"},
    {"location_id": "med_kunming", "name": "Kunming, China", "lat": 25.0389, "lon": 102.7183, "koppen": "Cwb", "character": "Subtropical highland, mild year-round, Yunnan vernacular"},
    {"location_id": "highland_lhasa", "name": "Lhasa, Tibet", "lat": 29.6500, "lon": 91.1000, "koppen": "BSk", "character": "Cold highland plateau (3650m), Tibetan stone house tradition"},
    {"location_id": "highland_cusco", "name": "Cusco, Peru", "lat": -13.5320, "lon": -71.9675, "koppen": "Cwb", "character": "Highland (3400m), Inca stone masonry tradition"},
    {"location_id": "cold_cont_yakutsk", "name": "Yakutsk, Russia", "lat": 62.0355, "lon": 129.6755, "koppen": "Dfd", "character": "Coldest city on earth (-50C winters), log house tradition"},
    {"location_id": "cold_cont_harbin", "name": "Harbin, China", "lat": 45.7500, "lon": 126.6500, "koppen": "Dwa", "character": "Harsh continental, Manchurian keng-style dwelling"},
    {"location_id": "cold_mar_tromso", "name": "Tromsø, Norway", "lat": 69.6492, "lon": 18.9553, "koppen": "Cfc", "character": "Arctic maritime, traditional Nordic timber construction"},
    {"location_id": "cold_mar_ushuaia", "name": "Ushuaia, Argentina", "lat": -54.8019, "lon": -68.3030, "koppen": "Cfc", "character": "Subantarctic maritime, indigenous Yamana shelter + European timber"},
    {"location_id": "hot_humid_zanzibar", "name": "Zanzibar, Tanzania", "lat": -6.1659, "lon": 39.1970, "koppen": "Am", "character": "Tropical maritime, Swahili coral stone house tradition"},
]

# ── Psychrometric constants ────────────────────────────────────────────────────

# Standard atmospheric pressure at sea level (Pa)
P_ATM = 101325.0

# Comfort thresholds
WBT_COMFORT_UPPER_C = 26.0  # wet-bulb temperature above which comfort is unlikely
DBT_COMFORT_LOWER_C = 18.0
DBT_COMFORT_UPPER_C = 26.0
RH_COMFORT_LOWER = 0.30
RH_COMFORT_UPPER = 0.60

# ── FOUR-AXIS THERMOREGULATORY ONTOLOGY ────────────────────────────────────────
#
# The ontology describes thermoregulation across four independent axes:
#
#   1. COLLECTION  — how energy enters the system
#   2. TRANSFER    — how energy moves through/away from the system
#   3. STORAGE     — how energy is buffered over time
#   4. REGULATION  — how the envelope adapts to modulate flow
#
# Each axis uses the same vocabulary for both animals and buildings.
# Tags describe the physical mechanism, not the domain-specific implementation.
#
# ── Axis 1: COLLECTION ────────────────────────────────────────────────────────
#
#   solar          = shortwave radiation absorbed by surfaces
#                    Animal: basking, dark coloration, orientation to sun
#                    Building: south-facing glazing, trombe wall, dark absorptive roof
#   metabolic      = internal chemical heat production
#                    Animal: BMR, shivering, nonshivering thermogenesis (BAT)
#                    Building: occupant body heat, cooking fires, livestock (400-500W/cow)
#   communal       = heat pooling from aggregated bodies
#                    Animal: penguin huddling, bat roost, herding
#                    Building: shared-wall medina fabric, co-housed livestock (byre-dwelling)
#   environmental  = passive absorption from warm surroundings (air, ground, water)
#                    Animal: lying on sun-heated rock, warm-water immersion
#                    Building: earth coupling when ground is warmer than air
#
# ── Axis 2: TRANSFER ─────────────────────────────────────────────────────────
#
#   evaporative    = phase change of water removes latent heat (2,260 kJ/kg)
#                    Animal: sweating, panting, gular flutter, saliva spreading
#                    Building: qanat, fountain, misting, wetted pads, PDEC tower
#   radiative      = net longwave/shortwave radiation exchange
#                    Animal: large ears/bill dump heat; white pelage reflects solar
#                    Building: high-albedo whitewash, sky radiative cooling, shading
#   convective     = moving air carries sensible heat
#                    Animal: panting airflow, ear flapping, wing fanning
#                    Building: cross ventilation, stack effect, windcatcher
#   conductive     = direct contact transfers heat to/from mass
#                    Animal: burrowing, wallowing, aquatic immersion, huddling
#                    Building: earth sheltering, earth tubes, ground-coupled slab
#
# ── Axis 3: STORAGE ──────────────────────────────────────────────────────────
#
#   sensible_mass  = high thermal capacity dampens temperature swings
#                    Animal: body mass as thermal capacitor (heterothermy: camel stores
#                            10,500 kJ with 6C rise in 500kg body)
#                    Building: thick adobe/stone walls, water tanks (c_p 4.18 kJ/kgK)
#   latent_pcm     = phase change absorbs/releases energy at constant temperature
#                    Animal: subcutaneous fat/blubber (latent heat ~160-200 kJ/kg)
#                    Building: paraffin wax PCM (150-250 kJ/kg), ice storage (334 kJ/kg),
#                              turf wall freeze/thaw buffering
#   chemical_fuel  = energy stored in molecular bonds, released on demand
#                    Animal: fat oxidation (39 kJ/g + metabolic water), camel hump
#                    Building: fuel stockpile (wood 16 MJ/kg, dung 12 MJ/kg, peat 15 MJ/kg)
#   diurnal_shift  = exploit day/night temperature swing via mass
#                    Animal: heterothermy (absorb heat by day, radiate at night)
#                    Building: night flushing (cool mass at night, absorb heat by day)
#   seasonal_store = bridge temporal mismatch between energy supply and demand
#                    Animal: hibernation fat, seasonal fat accumulation
#                    Building: earth coupling (ground lags air by 2-3 months),
#                              seasonal ice harvesting, interseasonal water TES
#
# ── Axis 4: REGULATION ───────────────────────────────────────────────────────
#
#   insulation_mod = variable thermal resistance of the envelope
#                    Animal: piloerection (2-4x R-value change in seconds),
#                            seasonal molt (3-6x R-value change over weeks)
#                    Building: removable ger felt layers (3x), operable shutters
#   flow_mod       = variable conductance of heat/air pathways
#                    Animal: vasodilation/constriction (10-100x skin blood flow),
#                            countercurrent bypass
#                    Building: night flushing (0-30 ACH), adjustable windcatcher dampers,
#                              ger toono opening
#   surface_mod    = variable absorptivity/emissivity of surfaces
#                    Animal: seasonal color change (ptarmigan α 0.20→0.70),
#                            mud coating
#                    Building: seasonal whitewashing (α 0.60→0.20),
#                              deciduous vine pergola
#   permeability_mod = variable air/vapor transmission through envelope
#                    Animal: sweat gland activation, nostril flaring, panting rate
#                    Building: mashrabiya adjustable panels, operable windows/louvers
#   geometry_mod   = variable exposed surface area or orientation
#                    Animal: curling (reduce SA 40-60%), ear/wing spreading (+20-25%)
#                    Building: courtyard self-shading by time of day, retractable awning

# ── Tag enums ──────────────────────────────────────────────────────────────────

COLLECTION_STRATEGIES = [
    "solar",
    "metabolic",
    "communal",
    "environmental",
    "combined",
    "none",
]

TRANSFER_STRATEGIES = [
    "evaporative",
    "radiative",
    "convective",
    "conductive",
    "combined",
]

STORAGE_STRATEGIES = [
    "sensible_mass",
    "latent_pcm",
    "chemical_fuel",
    "diurnal_shift",
    "seasonal_store",
    "combined",
    "none",
]

REGULATION_STRATEGIES = [
    "insulation_mod",
    "flow_mod",
    "surface_mod",
    "permeability_mod",
    "geometry_mod",
    "combined",
    "none",
]

# ── Moisture strategies (shared vocabulary) ────────────────────────────────────

MOISTURE_STRATEGIES = [
    "recovery",
    "reduction",
    "buffering",
    "ventilation",
    "evaporation",
    "combined",
    "none",
]

# ── Legacy aliases (for backward compatibility) ────────────────────────────────

COOLING_STRATEGIES = TRANSFER_STRATEGIES  # cooling = primary transfer out
HEATING_STRATEGIES = COLLECTION_STRATEGIES  # heating = primary collection in
