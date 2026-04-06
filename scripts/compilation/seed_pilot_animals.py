"""Seed the pilot animal features CSV with candidate species.

Usage:
    python scripts/compilation/seed_pilot_animals.py

Creates data/pilot/animal_features.csv with the 22-25 pilot species pre-filled
with metadata (name, clade, climate zone) and empty thermoregulatory feature
columns ready for manual literature coding.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.animals.schema import create_empty_dataframe, get_column_names
from src.utils.config import PILOT_DIR

# ── Pilot species definitions ────────────────────────────────────────────────

PILOT_SPECIES = [
    # Hot-dry (Riyadh, Saudi Arabia)
    {
        "species_id": "gbif:7044903",
        "common_name": "Dromedary Camel",
        "scientific_name": "Camelus dromedarius",
        "clade": "mammal",
        "climate_zone_id": "hot_dry_riyadh",
        "thermoreg_notes": "Nasal countercurrent heat/moisture recovery; heterothermy (allows body temp to rise ~6C); low sweating threshold; thick dorsal fur as solar shield",
    },
    {
        "species_id": "gbif:5219426",
        "common_name": "Fennec Fox",
        "scientific_name": "Vulpes zerda",
        "clade": "mammal",
        "climate_zone_id": "hot_dry_riyadh",
        "thermoreg_notes": "Extremely large ears (radiative heat loss); nocturnal/burrowing; thick foot fur for hot sand; metabolic water production",
    },
    {
        "species_id": "gbif:2440940",
        "common_name": "Arabian Oryx",
        "scientific_name": "Oryx leucoryx",
        "clade": "mammal",
        "climate_zone_id": "hot_dry_riyadh",
        "thermoreg_notes": "Light coloration (high albedo); carotid rete; heterothermy; shade seeking under sparse trees",
    },
    {
        "species_id": "gbif:2456795",
        "common_name": "Desert Horned Viper",
        "scientific_name": "Cerastes cerastes",
        "clade": "reptile",
        "climate_zone_id": "hot_dry_riyadh",
        "thermoreg_notes": "Nocturnal; burrowing/sand swimming; sidewinding minimizes ground contact; behavioral thermoregulation",
    },
    {
        "species_id": "gbif:2474428",
        "common_name": "Houbara Bustard",
        "scientific_name": "Chlamydotis undulata",
        "clade": "bird",
        "climate_zone_id": "hot_dry_riyadh",
        "thermoreg_notes": "Gular flutter for evaporative cooling; shade seeking; reduced activity in heat",
    },

    # Hot-humid (Malindi, Kenya)
    {
        "species_id": "gbif:141432",
        "common_name": "African Savanna Elephant",
        "scientific_name": "Loxodonta africana",
        "clade": "mammal",
        "climate_zone_id": "hot_humid_malindi",
        "thermoreg_notes": "Very large ears with dense vasculature (radiative/convective cooling); skin wetting/bathing; wallowing; low SA:V ratio compensated by ear radiators and skin surface area",
    },
    {
        "species_id": "gbif:2441025",
        "common_name": "Nile Crocodile",
        "scientific_name": "Crocodylus niloticus",
        "clade": "reptile",
        "climate_zone_id": "hot_humid_malindi",
        "thermoreg_notes": "Gigantothermy (large body mass = thermal inertia); bask with mouth open for thermoregulation; move between sun and water to behaviorally regulate; estivation during dry season",
    },
    {
        "species_id": "gbif:5218824",
        "common_name": "African Leopard",
        "scientific_name": "Panthera pardus",
        "clade": "mammal",
        "climate_zone_id": "hot_humid_malindi",
        "thermoreg_notes": "Nocturnal hunting; shade seeking during day; arboreal rest; panting; licking fur to cool via evaporation; generalized to many climates but coastal Kenya populations are heat-stressed",
    },
    {
        "species_id": "gbif:4850313",
        "common_name": "Greater Flamingo",
        "scientific_name": "Phoenicopterus roseus",
        "clade": "bird",
        "climate_zone_id": "hot_humid_malindi",
        "thermoreg_notes": "Stand on one leg to reduce heat load (unipedal thermoregulation); gular flutter; urohidrosis (defecate on legs for evaporative cooling); nocturnal foraging",
    },
    {
        "species_id": "gbif:5404679",
        "common_name": "African Rock Python",
        "scientific_name": "Python sebae",
        "clade": "reptile",
        "climate_zone_id": "hot_humid_malindi",
        "thermoreg_notes": "Gigantothermy (large body mass); basking behavior; nocturnal; coiled posture reduces exposed surface area; cutaneous water loss modulation",
    },

    # Temperate (Fez, Morocco — Atlas Mountains / Mediterranean)
    {
        "species_id": "gbif:5849301",
        "common_name": "Barbary Macaque",
        "scientific_name": "Macaca sylvanus",
        "clade": "mammal",
        "climate_zone_id": "temperate_fez",
        "thermoreg_notes": "Non-seasonal coat (mediterranean climate); huddling in cold; seeking shade in heat; rock shelters for thermoregulation;唯一的非人类灵长类动物在摩洛哥",
    },
    {
        "species_id": "gbif:2441023",
        "common_name": "Cairo Spiny Mouse",
        "scientific_name": "Acomys cahirinus",
        "clade": "mammal",
        "climate_zone_id": "temperate_fez",
        "thermoreg_notes": "Rock crevice inhabitant; nocturnal; cutaneous evaporative cooling; can tolerate high temperatures; burrowing behavior",
    },
    {
        "species_id": "gbif:4418059",
        "common_name": "Barbary Partridge",
        "scientific_name": "Alectoris barbara",
        "clade": "bird",
        "climate_zone_id": "temperate_fez",
        "thermoreg_notes": "Dust bathing for thermoregulation; panting; seek shade in rocky habitat; seasonal movement between elevations; compact body form",
    },
    {
        "species_id": "gbif:6173564",
        "common_name": "Maghreb Lizard",
        "scientific_name": "Scelarcis perspicillata",
        "clade": "reptile",
        "climate_zone_id": "temperate_fez",
        "thermoreg_notes": "Mediterranean lacertid; heliothermic basking; seek shade at high temps; crevice use for microclimate selection; seasonal activity patterns",
    },

    # Cold-dry (Ulaanbaatar, Mongolia)
    {
        "species_id": "gbif:7044904",
        "common_name": "Bactrian Camel",
        "scientific_name": "Camelus bactrianus",
        "clade": "mammal",
        "climate_zone_id": "cold_dry_ulaanbaatar",
        "thermoreg_notes": "Extremely dense winter coat (shed in summer); nasal countercurrent recovery; heterothermy; adapted to -30C winters and +40C summers; metabolic water production",
    },
    {
        "species_id": "gbif:2440860",
        "common_name": "Mongolian Gazelle",
        "scientific_name": "Procapra gutturosa",
        "clade": "mammal",
        "climate_zone_id": "cold_dry_ulaanbaatar",
        "thermoreg_notes": "Dense pelage; compact body; long-distance movement to favorable microclimates; nasal heat recovery; seasonal fur change",
    },
    {
        "species_id": "gbif:5219368",
        "common_name": "Pallas's Cat",
        "scientific_name": "Otocolobus manul",
        "clade": "mammal",
        "climate_zone_id": "cold_dry_ulaanbaatar",
        "thermoreg_notes": "Densest fur of any cat; small flat ears (reduced heat loss); stocky body; long belly fur for ground insulation; uses burrows/rock crevices",
    },
    {
        "species_id": "gbif:2498604",
        "common_name": "Saker Falcon",
        "scientific_name": "Falco cherrug",
        "clade": "bird",
        "climate_zone_id": "cold_dry_ulaanbaatar",
        "thermoreg_notes": "Feathered tarsi (reduced heat loss); compact body; panting in heat; soaring in thermals; nesting in cliffs; excellent continental flier",
    },

    # Cold-humid (Reykjavik, Iceland — subarctic maritime)
    {
        "species_id": "gbif:5220042",
        "common_name": "Reindeer",
        "scientific_name": "Rangifer tarandus",
        "clade": "mammal",
        "climate_zone_id": "cold_humid_reykjavik",
        "thermoreg_notes": "Nasal countercurrent heat exchange (Langman 1985); countercurrent limb vasculature; hollow hair insulation; can reduce leg temperature to near 0C",
    },
    {
        "species_id": "gbif:2481168",
        "common_name": "Atlantic Puffin",
        "scientific_name": "Fratercula arctica",
        "clade": "bird",
        "climate_zone_id": "cold_humid_reykjavik",
        "thermoreg_notes": "Bill thermoregulation (heat dump via bill vasculature); dense waterproof plumage; burrow nesting; countercurrent in feet; excellent swimmers",
    },
    {
        "species_id": "gbif:2433676",
        "common_name": "European Otter",
        "scientific_name": "Lutra lutra",
        "clade": "mammal",
        "climate_zone_id": "cold_humid_reykjavik",
        "thermoreg_notes": "Extremely dense underfur (70,000 hairs/cm2); guard hairs trap air layer; high metabolic rate; countercurrent in tail/feet; behavioral: grooming maintains air layer",
    },
    {
        "species_id": "gbif:4415147",
        "common_name": "Rock Ptarmigan",
        "scientific_name": "Lagopus muta",
        "clade": "bird",
        "climate_zone_id": "cold_humid_reykjavik",
        "thermoreg_notes": "Seasonal plumage color change (white winter = insulation + camouflage); feathered feet and legs (reduces heat loss); snow burrowing; compact body; willow ptarmigan diet in winter",
    },
]


def main():
    PILOT_DIR.mkdir(parents=True, exist_ok=True)

    df = create_empty_dataframe()
    species_df = pd.DataFrame(PILOT_SPECIES)
    for col in species_df.columns:
        df[col] = species_df[col]

    for col in get_column_names():
        if col not in df.columns:
            df[col] = None

    outpath = PILOT_DIR / "animal_features.csv"
    df.to_csv(outpath, index=False)
    print(f"Seeded {len(df)} pilot species to {outpath}")
    print(f"Columns: {len(df.columns)}")
    print()
    for zone, grp in df.groupby("climate_zone_id"):
        print(f"  {zone}: {', '.join(grp['common_name'].tolist())}")
    print()
    print("Next step: Code thermoregulatory features from literature for each species.")
    print("Fields to fill: respiratory, cutaneous, vascular, behavioral, thermal performance, strategy tags")


if __name__ == "__main__":
    main()
