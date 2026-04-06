"""Seed the pilot building features CSV with candidate traditions.

Usage:
    python scripts/compilation/seed_pilot_buildings.py

Creates data/pilot/building_features.csv with vernacular building traditions
pre-filled with metadata and empty feature columns ready for manual coding
from architecture literature.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.buildings.schema import create_empty_dataframe, get_column_names
from src.utils.config import PILOT_DIR

# ── Pilot building traditions ────────────────────────────────────────────────

PILOT_BUILDINGS = [
    # Hot-dry (Riyadh, Saudi Arabia)
    {
        "building_id": "hot_dry_windcatcher",
        "tradition_name": "Iranian Windcatcher House (Yazd)",
        "region": "Central Iran",
        "climate_zone_id": "hot_dry_riyadh",
        "building_type": "vernacular",
        "era": "Traditional (pre-modern)",
        "design_notes": "Badgir (windcatcher) captures wind and channels it over water/wet surfaces for evaporative cooling; thick adobe walls provide thermal mass; courtyard with pool; night flushing of thermal mass",
    },
    {
        "building_id": "hot_dry_courtyard",
        "tradition_name": "Saharan Courtyard House (Ghardaia)",
        "region": "M'zab Valley, Algeria",
        "climate_zone_id": "hot_dry_riyadh",
        "building_type": "vernacular",
        "era": "Traditional (11th century+)",
        "design_notes": "Compact urban form with shared walls; deep courtyard creates shade and stack ventilation; thick stone/adobe walls; minimal openings; whitewashed exteriors; roof terraces for night sleeping",
    },
    {
        "building_id": "hot_dry_pueblo",
        "tradition_name": "Nubian Vault House (Upper Egypt)",
        "region": "Upper Egypt / Nubia",
        "climate_zone_id": "hot_dry_riyadh",
        "building_type": "vernacular",
        "era": "Traditional (centuries old)",
        "design_notes": "Self-supporting brick vault (barrel vault) construction; thick earthen walls (40-60cm); no timber required; high thermal mass; small high windows for indirect light; basement storage for coolness",
    },

    # Hot-humid (Malindi, Kenya — Swahili coast)
    {
        "building_id": "hot_humid_swahili_coral",
        "tradition_name": "Swahili Coral Stone House (Lamu/Malindi)",
        "region": "Kenyan Swahili Coast",
        "climate_zone_id": "hot_humid_malindi",
        "building_type": "vernacular",
        "era": "Traditional (12th-19th century)",
        "design_notes": "Coral rag stone walls (locally quarried limestone); thick walls provide thermal mass; deep verandas (baraza) for shade; raised ground floor for airflow; internal courtyards; carved wooden doors; mashrabiya screens for privacy and ventilation",
    },
    {
        "building_id": "hot_humid_lamu_wooden",
        "tradition_name": "Lamu Traditional Wooden House",
        "region": "Lamu Island, Kenya",
        "climate_zone_id": "hot_humid_malindi",
        "building_type": "vernacular",
        "era": "Traditional",
        "design_notes": "Timber frame with mangrove pole construction; palm-leaf thatch roofing; elevated on stone plinth; wide verandas for shade and ventilation; porous walls allow air exchange; lightweight structure handles humidity",
    },
    {
        "building_id": "hot_humid_giriama",
        "tradition_name": "Giriama Traditional House",
        "region": "Coastal Kenya",
        "climate_zone_id": "hot_humid_malindi",
        "building_type": "vernacular",
        "era": "Traditional",
        "design_notes": "Earthen walls (wattle-and-daub or mud brick); conical thatched roof (Makuti palm); raised floor on timber posts; excellent ventilation through walls and roof; thick walls moderate diurnal temperature swing; natural materials, fully breathable",
    },

    # Temperate (Fez, Morocco — Mediterranean)
    {
        "building_id": "temperate_riad",
        "tradition_name": "Moroccan Riad (Fez/Marrakech)",
        "region": "Morocco",
        "climate_zone_id": "temperate_fez",
        "building_type": "vernacular",
        "era": "Traditional (medieval+)",
        "design_notes": "Inward-facing courtyard with fountain/plants (evaporative cooling); thick earthen walls (rammed earth or mud brick); high thermal mass moderates temperature; small exterior windows; south-facing orientation; zellige tilework provides radiant cooling surface; rooftop terrace for sleeping",
    },
    {
        "building_id": "temperate_fassi",
        "tradition_name": "Fassi Townhouse (Fez el-Bali)",
        "region": "Fez, Morocco",
        "climate_zone_id": "temperate_fez",
        "building_type": "vernacular",
        "era": "Traditional (medieval medina)",
        "design_notes": "Dense urban fabric with shared walls; multiple floors minimize facade exposure; central lightwell/courtyard; thick pisé (rammed earth) walls; small windows on south facade; rooftop terrace for winter solar gain and summer sleeping; groundwater cistern",
    },
    {
        "building_id": "temperate_andalusian",
        "tradition_name": "Andalusian Courtyard House (Granada/Seville)",
        "region": "Southern Spain",
        "climate_zone_id": "temperate_fez",
        "building_type": "vernacular",
        "era": "Traditional (Islamic period+)",
        "design_notes": "Patio-centered plan with water feature (fuente); thick whitewashed walls reflect solar radiation; cool marble floors; rejar (carved lattice windows) for privacy and ventilation; shade pergolas; winter solar gain through high ceilings",
    },

    # Cold-dry (Ulaanbaatar, Mongolia)
    {
        "building_id": "cold_dry_ger",
        "tradition_name": "Mongolian Ger (Yurt)",
        "region": "Mongolia",
        "climate_zone_id": "cold_dry_ulaanbaatar",
        "building_type": "vernacular",
        "era": "Traditional (millennia)",
        "design_notes": "Circular form minimizes surface-to-volume ratio; thick felt insulation layers (kushak); adjustable roof opening (toono) for ventilation control and stove; central stove (livestock dung fuel); door faces south; portable; windbreak orientation; layers of reed mat, felt, and canvas",
    },
    {
        "building_id": "cold_dry_mud_brick",
        "tradition_name": "Central Asian Mud-Brick House",
        "region": "Central Asia",
        "climate_zone_id": "cold_dry_ulaanbaatar",
        "building_type": "vernacular",
        "era": "Traditional",
        "design_notes": "Thick mud-brick walls (high thermal mass); flat roof with earth layer; small windows; south-facing main rooms; interior courtyard protected from wind; semi-underground storage (sarowla); shared party walls reduce exposed surface area",
    },
    {
        "building_id": "cold_dry_tibetan",
        "tradition_name": "Tibetan Stone House",
        "region": "Tibet / High Plateau",
        "climate_zone_id": "cold_dry_ulaanbaatar",
        "building_type": "vernacular",
        "era": "Traditional",
        "design_notes": "Massive stone walls with battered profile; flat roof for solar exposure; south-facing glazed gallery (trombe wall effect); animal quarters below living spaces (heat rises from livestock); dark exterior absorbs solar radiation; interior timber frame",
    },

    # Cold-humid (Reykjavik, Iceland — subarctic maritime)
    {
        "building_id": "cold_humid_turf",
        "tradition_name": "Icelandic Turf House",
        "region": "Iceland",
        "climate_zone_id": "cold_humid_reykjavik",
        "building_type": "vernacular",
        "era": "Traditional (settlement era +)",
        "design_notes": "Earth-sheltered construction with thick turf walls and roof; stone foundation and wall base; minimal openings (small windows); shared longhouse form (bae) reduces exposed walls; sod roof provides insulation (R-40+); central long fire for heating; smoke ventilation through roof",
    },
    {
        "building_id": "cold_humid_torfajokull",
        "tradition_name": " Icelandic Stone/Turf Farmstead",
        "region": "Rural Iceland",
        "climate_zone_id": "cold_humid_reykjavik",
        "building_type": "vernacular",
        "era": "Traditional (18th-19th century)",
        "design_notes": "Stone walls with turf cladding on exterior; gable-end to prevailing wind; small window openings with fish-oil treated frames; peat fuel hearth; earth floor; animal byre attached to house for shared warmth; thick insulation value of turf (400-600mm)",
    },
    {
        "building_id": "cold_humid_norse",
        "tradition_name": "Norwegian Stave-Inspired Timber House",
        "region": "Western Norway (adapted for Iceland)",
        "climate_zone_id": "cold_humid_reykjavik",
        "building_type": "vernacular",
        "era": "Traditional",
        "design_notes": "Heavy timber frame with interlocking joints (no nails); vertical board cladding; steep pitched roof (snow shedding); small windows reduce heat loss; raised foundation; tar-coated exterior for moisture protection; double-layer wall construction",
    },
]


def main():
    PILOT_DIR.mkdir(parents=True, exist_ok=True)

    df = create_empty_dataframe()
    buildings_df = pd.DataFrame(PILOT_BUILDINGS)

    for col in buildings_df.columns:
        df[col] = buildings_df[col]

    for col in get_column_names():
        if col not in df.columns:
            df[col] = None

    outpath = PILOT_DIR / "building_features.csv"
    df.to_csv(outpath, index=False)
    print(f"Seeded {len(df)} pilot building traditions to {outpath}")
    print(f"Columns: {len(df.columns)}")
    print()
    for zone, grp in df.groupby("climate_zone_id"):
        print(f"  {zone}:")
        for _, row in grp.iterrows():
            print(f"    - {row['tradition_name']} ({row['region']})")
    print()
    print("Next step: Code building features from architecture literature.")
    print("Fields to fill: envelope, ventilation, moisture, solar, thermal storage, strategy tags")


if __name__ == "__main__":
    main()
