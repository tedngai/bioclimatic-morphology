# Data-Driven Bioclimatic Morphology: Mapping Animal Thermoregulatory Features and Vernacular Building Strategies in Psychrometric Space

**Principal Investigator:** Ted Ngai  
**Date:** 2026-04-04  
**Last Revised:** 2026-04-06  
**Status:** Phase 8 — Vision-Based Self-Supervised Learning

> **Note (2026-04-06):** This document is the original research design. The methodology has evolved significantly through implementation. Phases 1-5 built a tabular dataset (425 animals, 170 buildings) and proved that animal/building thermal conductance occupies the same physical range. Phase 8 reframes the approach as self-supervised visual learning on millions of geotagged images, using climate prediction as the training objective. See `docs/phase8_vision.md` for the current implementation plan and `project_scope.md` for the full project evolution.

---

## 1. Executive Summary

This research proposes a data-driven framework that links **animal thermoregulatory anatomy**, **psychrometric climate descriptions**, and **vernacular/passive building design strategies** into a unified training dataset. The end goal is to create an AI-usable dataset that can recommend climate-responsive building design strategies by learning from how animals solve the same heat and moisture management problems under the same climatic constraints.

The key innovation is using **psychrometric space** — the coordinate system architects and mechanical engineers use to reason about air, heat, and moisture — as the shared framework for describing climate, rather than coarse labels like "tropical" or "arid." This allows precise alignment between animal features and building features based on the actual thermodynamic and hygric constraints each must negotiate.

The computational approach uses a **hybrid climate representation** combining explicit psychrometric variables (derived from ERA5 reanalysis) with Google DeepMind's **AlphaEarth Foundations** satellite embedding vectors — 64-dimensional learned representations of surface conditions at 10m resolution, available globally from 2017–2024 via Google Earth Engine. This dual representation preserves the interpretability of psychrometric reasoning (essential for the architectural audience) while leveraging the richness of a foundation model trained on petabytes of multi-modal Earth observation data. The target ML architecture is **embedding-based alignment**, where animal thermoregulatory features and building design features are projected into a shared climate-environment space for cross-domain retrieval and recommendation.

---

## 2. Research Context

### 2.1 The Architectural Starting Point

Psychrometric charts are a foundational tool in mechanical engineering and architectural environmental design. They map the relationships between:

- dry-bulb temperature
- wet-bulb temperature
- relative humidity
- humidity ratio
- dew point
- enthalpy (total heat content of moist air)
- specific volume

Architects and engineers use these charts to determine:

- thermal comfort zones
- when passive strategies (natural ventilation, evaporative cooling, thermal mass, etc.) are effective
- heating and cooling loads
- dehumidification requirements

A critical observation: **psychrometric values are derived from physical observations and empirically fitted relationships**, not purely from first-principles theory. The charts encode a hybrid of thermodynamic law and measured behavior of real moist air. This empirical, observation-grounded character connects them to how biology works — evolution also produces solutions grounded in real environmental constraints, not abstract optimization.

### 2.2 The Biological Parallel

Animals face the same fundamental problems as buildings:

- managing heat gain and loss
- controlling moisture exchange
- maintaining internal conditions within a viable range
- doing so using locally available materials and energy

Over evolutionary time, animals have developed specific **thermoregulatory and water-conserving anatomical features** — not just general body shape, but purpose-built exchange structures:

- **Nasal turbinates and nasal passages** — countercurrent heat and moisture exchangers (Schmidt-Nielsen's camel nose work is the classic example)
- **Vascular appendages** — ears, bills, horns, tails used as radiators or heat dumps
- **Fur, feathers, and skin** — variable insulation and evaporative surfaces
- **Countercurrent vascular systems** — in limbs, nasal passages, and brain cooling circuits
- **Sweating and panting systems** — evaporative cooling devices
- **Behavioral adaptations** — burrowing, nocturnality, shade-seeking, huddling

These features are analogous to building elements:

- windcatchers and heat recovery ventilators
- shading devices and radiative cooling surfaces
- insulated envelopes and breathable walls
- evaporative cooling towers and water features
- thermal mass and night flushing
- earth-sheltered construction

### 2.3 The Gap

The connection between animal thermoregulation and building design has been explored qualitatively in the **biomimetic architecture** literature. However:

1. **No structured dataset exists** that maps animal thermoregulatory features to psychrometric climate descriptions
2. **No parallel dataset exists** that maps vernacular building strategies to the same psychrometric descriptions
3. **No unified training dataset exists** that enables machine learning to discover or predict cross-domain correspondences
4. **Psychrometric space has not been used** as the organizing framework for comparative animal morphology

This research fills all four gaps.

---

## 3. Research Questions

### Primary Question
Can animal thermoregulatory features and vernacular passive building strategies be systematically mapped into shared psychrometric climate space, and can this mapping produce a training dataset that enables AI to recommend climate-responsive building design strategies informed by biological solutions?

### Secondary Questions
1. Which psychrometric variables (beyond simple temperature and precipitation) best predict the thermoregulatory strategies observed in animals?
2. Do animals and vernacular buildings in the same psychrometric regime converge on analogous heat and moisture management strategies?
3. Can a model trained on this dataset generate novel building design recommendations by identifying animal strategies that have no current architectural analogue?

---

## 4. Hypotheses

**H1:** Animal thermoregulatory features cluster meaningfully in psychrometric space — species from similar hygrothermal regimes will share thermoregulatory strategies regardless of phylogenetic relatedness.

**H2:** Psychrometric variables (wet-bulb temperature, vapor pressure deficit, dew point, enthalpy, evaporative potential) will explain thermoregulatory strategy variation better than standard bioclimatic variables (mean annual temperature, annual precipitation) alone.

**H3:** Vernacular building strategies and animal thermoregulatory strategies will show statistically significant correspondence when mapped to the same psychrometric climate zones — i.e., buildings and animals under the same hygrothermal constraints independently converge on analogous solutions.

**H4:** A machine learning model trained on the unified dataset can predict appropriate passive building strategies for a given psychrometric profile with accuracy comparable to or exceeding expert heuristic judgment.

---

## 5. Literature Review

### 5.1 Foundational: Schmidt-Nielsen and Respiratory Heat/Water Exchange

Knut Schmidt-Nielsen's work on desert animal physiology established the paradigm of treating animal anatomy as heat and moisture exchange infrastructure.

- **Schmidt-Nielsen, K. (1965).** *Desert Animals: Physiological Problems of Heat and Water.* — The foundational monograph. 1,426 citations. Establishes the framework for understanding animal thermoregulation as an engineering problem.
- **Schmidt-Nielsen, K., Hainsworth, F.R., Murrish, D.E. (1970).** "Counter-current heat exchange in the respiratory passages: effect on water and heat balance." *Respiration Physiology.* 316 citations. — The key mechanistic paper on nasal countercurrent exchange.
- **Schmidt-Nielsen, K. & Schroter, R.C. (1981).** "Desaturation of exhaled air in camels." *Proceedings of the Royal Society B.* 71 citations. — Demonstrates the camel nose as a sophisticated moisture recovery device.
- **Schmidt-Nielsen, K. & Crawford, E.C. (1981).** "Respiratory water loss in camels." *Proceedings of the Royal Society B.* 28 citations. — Quantifies the water-saving function of nasal heat exchange.
- **Schmidt-Nielsen, K. (1981).** "Countercurrent systems in animals." *Scientific American.* 67 citations. — Accessible overview of countercurrent exchange principles across species.

### 5.2 Nasal Heat Exchange Across Species

The Schmidt-Nielsen framework has been extended to many species and climates:

- **Langman, V.A. (1985).** "Nasal heat exchange in a northern ungulate, the reindeer (*Rangifer tarandus*)." *Respiration Physiology.* — Shows nasal heat exchange matters in cold climates too, not just deserts.
- **Huntley, A.C. & Costa, D.P. (1984).** "The contribution of nasal countercurrent heat exchange to water balance in the northern elephant seal." *Journal of Experimental Biology.* 80 citations. — Marine mammals using the same principle.
- **Folkow, L.P. & Blix, A.S. (1987).** "Nasal heat and water exchange in gray seals." *American Journal of Physiology.* 77 citations.
- **Hillenius, W.J. (1992).** "The evolution of nasal turbinates and mammalian endothermy." *Paleobiology.* 206 citations. — Connects internal nasal anatomy to the evolutionary origin of warm-bloodedness itself.
- **Rigaut, C. et al. (2024).** "The air conditioning in the nose of mammals depends on their mass and on their maximal running speed." *Scientific Reports.* — Very recent; treats the nose explicitly as an "air conditioning" system scaled by body parameters.
- **Robertshaw, D. (2006).** "Mechanisms for the control of respiratory evaporative heat loss in panting animals." *Journal of Applied Physiology.* 295 citations.

### 5.3 Biophysical Ecology and Mechanistic Modeling

This literature provides the physics framework for animal–environment heat and mass exchange:

- **Gates, D.M. (1980/2012).** *Biophysical Ecology.* 2,686 citations. — The foundational textbook.
- **Bakken, G.S. & Gates, D.M. (1975).** "Heat-transfer analysis of animals: some implications for field ecology, physiology, and evolution." *Perspectives of Biophysical Ecology.* 423 citations.
- **Helmuth, B. (2002).** "How do we measure the environment? Linking intertidal thermal physiology and ecology through biophysics." *Integrative and Comparative Biology.* 224 citations.
- **Helmuth, B., Kingsolver, J.G., Carrington, E. (2005).** "Biophysics, physiological ecology, and climate change: does mechanism matter?" *Annual Review of Physiology.* 585 citations. — Argues that mechanistic understanding of heat exchange is essential for predicting climate responses.
- **Mitchell, D. et al. (2018).** "Revisiting concepts of thermal physiology: predicting responses of mammals to climate change." *Journal of Animal Ecology.* 330 citations.
- **Briscoe, N.J. et al. (2023).** "Mechanistic forecasts of species responses to climate change: the promise of biophysical ecology." *Global Change Biology.* 207 citations.
- **Porter, W.P. & Kearney, M. (2009).** "Size, shape, and the thermal niche of endotherms." *PNAS.* 330 citations. — Mechanistic modeling of how size and shape determine thermal niches.

### 5.4 Evaporative Water Loss, Humidity, and Thermoregulation

This cluster addresses the hygric (moisture) side — critical for psychrometric framing:

- **Cooper, C.E. & Withers, P.C. (2008).** "Allometry of evaporative water loss in marsupials: implications of the effect of ambient relative humidity." *Journal of Experimental Biology.* 33 citations.
- **Weaver, S.J. et al. (2022).** "Cutaneous evaporative water loss in lizards is variable across body regions and plastic in response to humidity." *Herpetologica.* 27 citations.
- **Weaver, S.J. et al. (2023).** "Hydration and evaporative water loss of lizards change in response to temperature and humidity acclimation." *Journal of Experimental Biology.* 27 citations.
- **Bulova, S.J. (2002).** "How temperature, humidity, and burrow selection affect evaporative water loss in desert tortoises." *Journal of Thermal Biology.* 120 citations.
- **Cain, J.W. et al. (2006).** "Mechanisms of thermoregulation and water balance in desert ungulates." *Wildlife Society Bulletin.* 378 citations.
- **Van Sant, M.J. et al. (2012).** "A phylogenetic approach to total evaporative water loss in mammals." *Physiological and Biochemical Zoology.* 38 citations.
- **Fuller, A. et al. (2016).** "Towards a mechanistic understanding of the responses of large terrestrial mammals to heat and aridity associated with climate change." *Climate Change Responses.* 217 citations.

### 5.5 Climate-Driven Morphological Variation

The broader ecogeographical and shape-shifting literature:

- **Ryding, S. et al. (2021).** "Shape-shifting: changing animal morphologies as a response to climatic warming." *Trends in Ecology & Evolution.* 173 citations. — Modern synthesis of Allen's rule and climate-driven morphological change.
- **Koehl, M.A.R. (1996).** "When does morphology matter?" *Annual Review of Ecology and Systematics.* 474 citations.
- **Chabaud, C. et al. (2022).** "Climate aridity and habitat drive geographical variation in morphology and thermo-hydroregulation strategies of a widespread lizard species." *Biological Journal of the Linnean Society.* — Directly links climate aridity to thermoregulatory morphology.

### 5.6 Biomimetic Architecture and Thermoregulation

The existing architecture-side literature that connects biology to building design:

- **McCafferty, D.J. et al. (2018).** "Animal thermoregulation: a review of insulation, physiology and behaviour relevant to temperature control in buildings." *Bioinspiration & Biomimetics.* 70 citations. — Closest direct precursor to this project on the building science side.
- **Badarnah, L. (2015).** "A biophysical framework of heat regulation strategies for the design of biomimetic building envelopes." *Procedia Engineering.* 57 citations.
- **Imani, N. & Vale, B. (2020).** "A framework for finding inspiration in nature: Biomimetic energy efficient building design." *Energy and Buildings.* 45 citations.
- **Imani, N. & Vale, B. (2022).** "Developing a method to connect thermal physiology in animals and plants to the design of energy efficient buildings." *Biomimetics.* 14 citations.
- **Webb, M. (2022).** "Biomimetic building facades demonstrate potential to reduce energy consumption for different building typologies in different climate zones." *Clean Technologies and Environmental Policy.* 62 citations.
- **Hays, N., Badarnah, L., Jain, A. (2024).** "Biomimetic design of building facades… inspired by elephant skin for cooling in hot and humid climates." *Frontiers in Built Environment.* 24 citations.
- **Onuike, C.B. & Aderibigbe, M.O. (2025).** "Biomimetic passive cooling architectures for hot-humid climates using ML-driven computational design." *Berkeley Journal of Engineering Research and Design.*

### 5.7 Bioclimatic / Psychrometric Building Design

The architectural climate analysis tradition:

- **Olgyay, V. (1963).** *Design with Climate: Bioclimatic Approach to Architectural Regionalism.* — Foundational text linking climate analysis to building form.
- **Givoni, B. (1969/1998).** *Man, Climate and Architecture* / *Climate Considerations in Building and Urban Design.* — Established the building bioclimatic chart (psychrometric overlay for passive strategies).
- **Kishore, K.N. & Rekha, J. (2018).** "A bioclimatic approach to develop spatial zoning maps for comfort, passive heating and cooling strategies within a composite zone of India." *Building and Environment.* 54 citations.
- **Bhamare, D.K. et al. (2020).** "Evaluation of cooling potential of passive strategies using bioclimatic approach for different Indian climatic zones." *Journal of Building Engineering.* 61 citations.
- **Tamaskani Esfehankalateh, A. et al. (2022).** "Bioclimatic passive design strategies of traditional houses in cold climate regions." *Environment, Development and Sustainability.* 23 citations.

### 5.8 Psychrometric Use in Animal Science (Adjacent)

A small but relevant cluster using psychrometric reasoning for animal thermal comfort (primarily livestock):

- **de Castro Júnior, S.L. et al. (2024).** "Psychrometry in the thermal comfort diagnosis of production animals: a combination of the systematic review and methodological proposal." *International Journal of Biometeorology.* 10 citations. — Uses psychrometric air relations to assess animal thermal comfort.

### 5.9 Animal Trait Databases

Existing structured data sources for animal traits:

- **PanTHERIA** — mammalian ecological traits (body mass, diet, habitat, litter size, etc.)
- **AVONET** — bird morphological traits (beak dimensions, wing length, body mass, etc.)
- **AmphiBIO** — amphibian life-history traits
- **AnimalTraits** (animaltraits.org) — comparative animal physiology database
- **NicheMapR / endoR** — R packages for mechanistic biophysical modeling of animal–environment exchange (by Kearney & Porter)
- **GBIF** — species occurrence records with geolocation
- **iNaturalist** — citizen science observations with images and geolocation

---

## 6. Approach: Building the Dataset

### 6.1 Overview

The dataset consists of three linked tables sharing a common climate representation in psychrometric space:

```
┌─────────────────────────┐
│  Table 1: Climate Zones │
│  (Psychrometric Space)  │
└────────────┬────────────┘
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
┌─────────────┐ ┌──────────────────┐
│  Table 2:   │ │  Table 3:        │
│  Animal     │ │  Building /      │
│  Thermo-    │ │  Vernacular      │
│  regulatory │ │  Design          │
│  Features   │ │  Features        │
└─────────────┘ └──────────────────┘
```

### 6.2 Table 1: Climate Zones in Psychrometric Space

**Purpose:** Define climate not by labels but by measured psychrometric state.

**Fields:**

| Field | Type | Description | Source |
|---|---|---|---|
| `location_id` | string | Geographic point or zone identifier | — |
| `name` | string | Location or zone name | — |
| `lat` | float | Latitude | — |
| `lon` | float | Longitude | — |
| `koppen_class` | string | Köppen-Geiger classification | WorldClim / Beck et al. |
| `mean_dbt` | float (°C) | Mean annual dry-bulb temperature | ERA5 / CHELSA |
| `mean_wbt` | float (°C) | Mean annual wet-bulb temperature | Derived |
| `mean_rh` | float (%) | Mean annual relative humidity | ERA5 |
| `mean_vpd` | float (kPa) | Mean annual vapor pressure deficit | Derived |
| `mean_dew_point` | float (°C) | Mean annual dew point | ERA5 |
| `mean_enthalpy` | float (kJ/kg) | Mean moist air enthalpy | Derived |
| `diurnal_temp_range` | float (°C) | Mean daily temperature swing | ERA5 |
| `annual_precip` | float (mm) | Total annual precipitation | WorldClim |
| `solar_radiation` | float (W/m²) | Mean surface solar irradiance | ERA5 / MODIS |
| `wind_speed` | float (m/s) | Mean wind speed | ERA5 |
| `aridity_index` | float | PET / precipitation ratio | CGIAR-CSI |
| `evap_cooling_potential` | float | Wet-bulb depression × hours available | Derived |
| `hours_above_wbt_threshold` | int | Annual hours where WBT exceeds comfort | Derived |
| `seasonal_profile` | JSON | Monthly vectors of [DBT, RH, VPD, WBT] | Derived |

**Derivation notes:**
- Wet-bulb temperature: from DBT + RH using standard psychrometric equations
- VPD: saturation vapor pressure (from DBT) minus actual vapor pressure (from RH)
- Enthalpy: 1.006·DBT + W·(2501 + 1.86·DBT), where W = humidity ratio
- Evaporative cooling potential: proxy for how much cooling evaporation can provide = f(DBT − WBT, hours)

**Target:** 50–100 representative locations spanning all major psychrometric regimes.

### 6.3 Table 2: Animal Thermoregulatory Features

**Purpose:** Catalog the specific anatomical, physiological, and behavioral features animals use to manage heat and moisture, tagged to climate zones.

**Fields:**

| Field | Type | Description | Source |
|---|---|---|---|
| `species_id` | string | Taxonomic identifier | GBIF / ITIS |
| `common_name` | string | — | — |
| `scientific_name` | string | — | — |
| `clade` | enum | mammal / bird / reptile / amphibian / insect | — |
| `climate_zone_id` | FK | Links to Table 1 | Occurrence data |
| `body_mass_kg` | float | Body mass | PanTHERIA / AVONET / literature |
| `sa_vol_ratio` | float | Surface area to volume ratio | Derived / literature |
| | | **Respiratory Exchange** | |
| `nasal_turbinate_complexity` | enum | none / simple / moderate / complex / highly complex | Literature |
| `nasal_passage_rel_length` | float | Passage length relative to skull length | Literature |
| `respiratory_water_recovery_pct` | float | % of exhaled moisture recovered | Literature |
| `panting_strategy` | enum | none / thermal_panting / lateral_nasal / gular_flutter | Literature |
| | | **Cutaneous Exchange** | |
| `sweating_capacity` | enum | none / eccrine_low / eccrine_high / apocrine | Literature |
| `cutaneous_ewl_mg_h_cm2` | float | Cutaneous evaporative water loss rate | Literature |
| `skin_permeability_index` | float | Relative skin water permeability | Literature |
| `fur_density_hairs_cm2` | float | Hair density | Literature |
| `fur_depth_mm` | float | Fur/feather depth | Literature |
| `insulation_conductance_w_m2k` | float | Thermal conductance of pelage/plumage | Literature |
| | | **Vascular / Radiative** | |
| `appendage_sa_ratio` | float | Appendage surface area relative to body SA | Literature / measurement |
| `vascular_appendage_type` | string | ears / bill / horns / tail / fins / none | Literature |
| `countercurrent_system` | enum | none / limb / nasal / carotid_rete / multiple | Literature |
| `coloration_lightness` | float (0–1) | Reflectance / albedo proxy | Image analysis / literature |
| | | **Behavioral** | |
| `burrowing` | bool | Uses burrows for thermal refuge | Literature |
| `nocturnal_fraction` | float (0–1) | Fraction of activity at night | Literature |
| `shade_seeking` | bool | Actively seeks shade in heat | Literature |
| `huddling` | bool | Social thermoregulation in cold | Literature |
| `posture_adjustment` | bool | Changes posture for thermal control | Literature |
| | | **Thermal Performance** | |
| `tnz_lower_critical_c` | float | Lower critical temperature | Literature |
| `tnz_upper_critical_c` | float | Upper critical temperature | Literature |
| `bmr_w_kg` | float | Basal metabolic rate | Literature |
| `max_evaporative_capacity` | float | Maximum evaporative heat loss | Literature |
| `thermal_conductance_min` | float | Minimum whole-body thermal conductance | Literature |
| | | **Strategy Tags** | |
| `primary_cooling` | enum | evaporative / radiative / conductive / behavioral / combined | Derived |
| `primary_heating` | enum | metabolic / insulative / behavioral / solar / combined | Derived |
| `water_conservation` | enum | nasal_recovery / reduced_ewl / metabolic_water / behavioral / renal / combined | Derived |
| `thermoreg_notes` | text | Free-text notes on unique adaptations | — |

**Target:** 100–200 well-documented species across major clades and climate zones.

### 6.4 Table 3: Building / Vernacular Design Features

**Purpose:** Catalog the passive and vernacular building strategies used in each climate zone, structured to enable comparison with animal strategies.

**Fields:**

| Field | Type | Description | Source |
|---|---|---|---|
| `building_id` | string | — | — |
| `tradition_name` | string | e.g., "Iranian windcatcher house", "Inuit igloo" | — |
| `region` | string | Geographic region | — |
| `climate_zone_id` | FK | Links to Table 1 | — |
| `building_type` | enum | vernacular / modern_passive / biomimetic | — |
| `era` | string | Historical period or "contemporary" | — |
| | | **Envelope** | |
| `wall_thickness_cm` | float | — | — |
| `wall_material` | string | adobe / stone / timber / brick / reed / ice / etc. | — |
| `thermal_mass_level` | enum | low / medium / high / very_high | — |
| `insulation_r_value` | float (m²·K/W) | — | — |
| `envelope_porosity` | enum | sealed / semi_porous / porous / open | — |
| `surface_albedo` | float (0–1) | Exterior surface reflectance | — |
| `roof_material` | string | — | — |
| `roof_form` | enum | flat / pitched / domed / vaulted / green | — |
| | | **Ventilation / Airflow** | |
| `natural_ventilation_type` | enum | none / cross / stack / wind_driven / combined | — |
| `has_windcatcher` | bool | — | — |
| `has_courtyard` | bool | — | — |
| `chimney_stack_effect` | bool | — | — |
| `ventilation_control` | enum | fixed / operable / automated | — |
| | | **Moisture Management** | |
| `evaporative_cooling_type` | enum | none / direct / indirect / combined | — |
| `water_feature_type` | enum | none / fountain / channel / pool / misting | — |
| `breathable_walls` | bool | Walls permit vapor diffusion | — |
| `humidity_control_type` | enum | none / natural / desiccant / mechanical | — |
| | | **Solar / Radiation** | |
| `shading_strategy` | enum | none / overhang / screen / mashrabiya / vegetation / combined | — |
| `glazing_ratio` | float (0–1) | Window-to-wall ratio | — |
| `orientation_strategy` | string | e.g., "long axis E-W", "minimized west exposure" | — |
| `radiative_cooling` | bool | Uses sky radiative cooling | — |
| | | **Thermal Storage / Earth** | |
| `night_flushing` | bool | Night ventilation to discharge thermal mass | — |
| `earth_sheltering` | bool | Partially or fully underground | — |
| `earth_tubes` | bool | Uses earth-air heat exchangers | — |
| `phase_change_materials` | bool | — | — |
| | | **Heat Recovery** | |
| `heat_recovery_type` | enum | none / air_to_air / earth_coupled / water_based | — |
| | | **Strategy Tags** | |
| `primary_cooling` | enum | evaporative / radiative / ventilative / massive / shading / earth / combined | — |
| `primary_heating` | enum | solar_gain / insulative / massive / internal_gain / earth / combined | — |
| `moisture_strategy` | enum | ventilation / absorption / evaporation / sealing / combined / none | — |
| `design_notes` | text | Free-text description of notable features | — |

**Target:** 50–100 well-documented vernacular and passive building traditions.

### 6.5 Linking Logic: Strategy Alignment

The three tables are joined on `climate_zone_id`. For any psychrometric zone, the dataset enables:

1. **Within-domain queries:**
   - What thermoregulatory strategies do animals use in hot-humid zones?
   - What passive building strategies appear in cold-dry zones?

2. **Cross-domain queries:**
   - For a given psychrometric profile, do animal and building strategies converge?
   - Which animal strategies have no current architectural analogue?

3. **Prediction tasks:**
   - Given a psychrometric profile → predict appropriate building strategies
   - Given a psychrometric profile + animal strategies → recommend building features
   - Given a novel climate (e.g., future climate projection) → suggest strategies from both domains

### 6.6 Strategy Tag Ontology

To enable cross-domain comparison, both animal and building features use a shared **strategy tag vocabulary** organized by function:

**Cooling strategies:**
- evaporative (sweating / panting / misting / direct evaporative cooling)
- radiative (vascular appendages / light coloration / radiative roof cooling / sky exposure)
- conductive (burrowing / earth contact / earth-sheltered construction)
- convective/ventilative (gular flutter / wing spreading / cross ventilation / windcatcher)
- massive (body thermal inertia / thermal mass walls / night flushing)
- shading (posture / nocturnal activity / overhangs / screens)

**Heating strategies:**
- metabolic (BMR elevation / shivering / internal gains)
- insulative (fur / feathers / fat / wall insulation / double envelope)
- solar (basking / dark coloration / solar gain / greenhouse)
- massive (body mass thermal buffering / thermal mass + solar gain)
- behavioral (huddling / orientation / shelter)

**Moisture strategies:**
- recovery (nasal countercurrent / heat recovery ventilator / enthalpy wheel)
- reduction (low skin permeability / sealed envelope / vapor barriers)
- tolerance (metabolic water production / vapor-permeable construction)
- active removal (panting / dehumidification / ventilation)

---

## 7. Implementation Plan

*Detailed step-by-step implementation with timelines, dependencies, and deliverables is provided in the companion document `project_scope.md`. Below is the summary.*

### Phase 1: Climate Backbone — Hybrid Representation (Weeks 1–3)

Build a dual climate representation combining explicit psychrometric variables with AlphaEarth Foundations embeddings.

**Psychrometric layer (ERA5):**
1. Select 50–100 representative locations spanning all major psychrometric regimes
2. Download hourly climate data from ERA5 reanalysis (minimum 10-year period)
3. Derive psychrometric variables: WBT, VPD, dew point, enthalpy, evaporative cooling potential
4. Generate seasonal psychrometric profiles (monthly averages)
5. Cluster locations into psychrometric zones

**AlphaEarth layer (Google Earth Engine):**
6. Extract 64D AlphaEarth Foundations satellite embeddings for each location
7. Aggregate embeddings spatially (region-average for species ranges, point-sample for building sites)
8. Validate that AlphaEarth embedding structure correlates with psychrometric clustering

**Output:** Each location has a hybrid climate vector = [~12 psychrometric variables] + [64D AlphaEarth embedding]

### Phase 2: Animal Feature Compilation (Weeks 2–8)

1. Identify 100–200 target species with documented thermoregulatory physiology
2. Pull baseline traits from PanTHERIA, AVONET, AnimalTraits, GBIF
3. Code thermoregulatory features from literature
4. Extract AlphaEarth embeddings at GBIF occurrence centroids for each species
5. Derive psychrometric profiles at occurrence locations from ERA5
6. Tag strategy labels
7. Quality check against review papers

### Phase 3: Building Feature Compilation (Weeks 2–8, parallel)

1. Identify 50–100 vernacular/passive building traditions
2. Code building features from published descriptions and surveys
3. Geolocate each tradition (representative lat/lon)
4. Extract AlphaEarth embeddings and ERA5 psychrometric profiles at building locations
5. Tag strategy labels using shared ontology

### Phase 4: Baseline Analysis and Hypothesis Testing (Weeks 8–10)

1. Join all three tables on location/climate
2. Train gradient boosted tree models (XGBoost) for strategy prediction
3. Run three ablation conditions:
   - **Psychrometric-only:** climate → strategy (tests H2)
   - **AlphaEarth-only:** embedding → strategy
   - **Combined:** psychrometric + embedding → strategy
4. SHAP analysis for feature importance
5. Test H1–H3 statistically
6. UMAP/PCA visualization of combined strategy space

### Phase 5: Embedding Alignment (Weeks 10–14)

1. Train projection networks:
   - `f_animal(thermoreg_features) → climate embedding space`
   - `f_building(design_features) → climate embedding space`
2. Use contrastive loss: same-climate pairs should align, different-climate pairs should separate
3. Evaluate cross-domain retrieval: given a climate, retrieve similar animals → retrieve analogous buildings
4. Test H4
5. Generate novel recommendations: identify animal strategies without building analogues

### Phase 6: Scale and Publish (Weeks 14–20)

1. Expand dataset to 200+ animals, 100+ buildings
2. Retrain models at scale
3. Build RAG pipeline for practical design recommendations
4. Write paper
5. Release dataset

---

## 8. Computational Approach: Hybrid Climate Representation and Embedding Alignment

### 8.1 Why a Hybrid Representation

This project uses a dual climate representation:

**Layer A — Explicit psychrometric variables (from ERA5 reanalysis)**
- Dry-bulb temperature, wet-bulb temperature, relative humidity, vapor pressure deficit, dew point, enthalpy, evaporative cooling potential, diurnal range, solar radiation, wind speed, aridity index
- ~12 interpretable, physically meaningful variables
- Directly maps onto the psychrometric chart framework architects already use
- Essential for testing H2 and for architectural interpretability

**Layer B — AlphaEarth Foundations satellite embeddings (from Google Earth Engine)**
- 64-dimensional learned embedding per 10m pixel, annually from 2017–2024
- Trained on optical imagery, radar, LiDAR, climate simulations, and other sources
- Encodes land cover, vegetation, surface moisture, terrain, seasonal dynamics
- Not directly interpretable but extremely rich
- Captures environmental context that psychrometric variables alone miss (habitat structure, vegetation, land use)

**Rationale for combining both:**
- AlphaEarth encodes **surface conditions** (what satellites see) but not **atmospheric state** (temperature, humidity, wind as experienced by organisms and buildings)
- Psychrometric variables capture **atmospheric state** precisely but miss **surface/habitat context**
- The combination gives both: the thermodynamic environment (psychrometric) and the ecological/physical context (AlphaEarth)
- The ablation study (psychrometric-only vs. AlphaEarth-only vs. combined) is itself a contribution

### 8.2 AlphaEarth Foundations: What It Is and What It Provides

AlphaEarth Foundations (Brown, Kazmierski, Pasquarella et al., 2025; arXiv:2507.22291) is a geospatial foundation model by Google DeepMind that:

- Integrates petabytes of multi-source Earth observation data
- Produces a 64D unit-length embedding vector for every 10m×10m terrestrial pixel globally
- Annual embeddings available 2017–2024 via Google Earth Engine
- Outperforms other featurization approaches by 24% lower error rate on diverse mapping tasks
- Embeddings are linearly composable (can be averaged over regions) and consistent across years

**For this project, AlphaEarth provides:**
- A pre-trained, globally consistent environmental fingerprint for any location
- Eliminates the need to build a custom land-cover / habitat classification
- Enables linking animal occurrence locations and building locations through a shared, learned environmental space
- Available at no training cost — only extraction and aggregation needed

**Limitations for this project:**
- Encodes surface reflectance/structure, not atmospheric psychrometric state
- 64 dimensions are not individually interpretable
- 10m resolution is finer than needed; spatial aggregation required
- Does not encode animal traits, building features, or thermoregulatory strategies

### 8.3 ML Architecture: Tiered Approach

**Tier 1 — Baseline (Gradient Boosted Trees + SHAP)**
- XGBoost multi-label classifiers: climate → strategy tags
- Three ablation conditions: psychrometric-only / AlphaEarth-only / combined
- SHAP for interpretable feature importance
- Tests H1–H3, establishes baselines
- Data requirement: 50+ animals, 30+ buildings

**Tier 2 — Embedding Alignment (Learned Projections)**
- Train projection networks mapping animal features and building features into the hybrid climate space
- Contrastive learning: same-climate pairs align, different-climate pairs separate
- Cross-domain retrieval: climate → animal strategies → analogous building strategies
- Multi-task MLP with shared climate encoder, separate animal/building prediction heads
- Tests H4
- Data requirement: 200+ animals, 100+ buildings

**Tier 3 — Future (Generative + Retrieval)**
- RAG pipeline: embed all records, retrieve by climate similarity, generate recommendations via LLM
- VAE for generative strategy proposals
- GNN for relational reasoning across the climate–animal–building graph
- Transfer to future climate projections (2050/2100)
- Data requirement: 500+ animals, 200+ buildings

### 8.4 Data Formats for ML Consumption

The dataset is structured to support all three tiers:

**Format 1: Flat CSV** (for tree models, MLPs)
- One row per (location, entity) pair
- All features as columns, strategy tags as binary indicators

**Format 2: Paired JSON** (for embedding/metric learning)
- Climate vector + associated animal and building records
- Used for contrastive pair construction

**Format 3: Graph edges** (for GNN, future work)
- Nodes: climate zones, species, building traditions
- Edges: occurs_in, built_in, shares_strategy

**Format 4: Text + structured** (for RAG/LLM)
- Each record includes structured fields AND a natural language description
- Enables LLM-based reasoning and recommendation generation

---

## 9. Expected Contributions

1. **A novel dataset** linking animal thermoregulatory features and building passive strategies through psychrometric climate space — the first of its kind.

2. **Validation of psychrometric framing** for biological thermoregulation — testing whether psychrometric variables outperform standard bioclimatic predictors for animal strategy prediction.

3. **Quantitative evidence for convergence** (or divergence) between biological and architectural climate-response strategies.

4. **An AI-ready training dataset** for recommending passive building design strategies, grounded in both evolutionary biology and architectural tradition.

5. **Ablation study** comparing psychrometric variables, AlphaEarth satellite embeddings, and their combination for predicting thermoregulatory and design strategies — a methodological contribution to both geospatial AI and bioclimatic design research.

6. **A bridge between disciplines** — connecting biophysical ecology, comparative physiology, architectural science, and machine learning in a way that has not been done before.

---

## 10. Risks and Limitations

- **Data scarcity for animal thermoregulatory traits:** Many species lack quantitative measurements. The dataset will necessarily be sparse for some fields, requiring imputation or hierarchical modeling.
- **Subjectivity in strategy tagging:** Mapping "nasal countercurrent heat recovery" to "air-to-air heat recovery" requires expert judgment. Inter-rater reliability should be tested.
- **Phylogenetic confounding:** Animal strategies are shaped by evolutionary history, not just climate. Phylogenetic controls are essential for H1.
- **Vernacular architecture documentation is uneven:** Some traditions are well-studied; others are poorly documented. Coverage will be biased toward regions with strong architectural history research.
- **Psychrometric variables are correlated:** VPD, WBT, RH, and enthalpy are not independent. Dimensionality reduction or careful variable selection will be needed.
- **Climate is not static:** Both animal populations and building traditions respond to climate change. The dataset captures current/recent states, not historical trajectories.

---

## 11. Tools and Data Sources

### Climate / Environment Data
- **AlphaEarth Foundations Satellite Embedding V1** — 64D learned geospatial embeddings at 10m resolution, annual, 2017–2024. Access via Google Earth Engine (`GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`). See Brown, Kazmierski, Pasquarella et al. (2025), arXiv:2507.22291.
- **ERA5** (ECMWF reanalysis) — hourly global climate fields (temperature, humidity, wind, radiation, precipitation)
- **CHELSA** — high-resolution bioclimatic variables
- **WorldClim** — standard bioclimatic surfaces
- **CGIAR-CSI** — aridity index and PET data
- **MODIS** — land surface temperature, albedo, vegetation

### Animal Data
- **PanTHERIA** — mammalian ecological traits
- **AVONET** — bird morphological traits
- **AmphiBIO** — amphibian traits
- **AnimalTraits** (animaltraits.org) — comparative physiology
- **GBIF** — species occurrence
- **iNaturalist** — geolocated images
- **NicheMapR / endoR** — mechanistic modeling packages (R)

### Building Data
- Published surveys of vernacular architecture
- Olgyay, Givoni, and regional architecture textbooks
- ASHRAE climate zone standards
- Climate Consultant / CBE Thermal Comfort Tool
- AskNature database (biomimetic strategies)

### Computing
- **Google Earth Engine** (Python API) — AlphaEarth embedding extraction, spatial aggregation
- **Python** (pandas, scikit-learn, xgboost, SHAP, PyTorch, UMAP)
- **R** (NicheMapR for biophysical modeling)
- **ERA5 via CDS API** — climate data download
- **PsychroLib** — psychrometric calculations

---

## 12. Pilot Study Design

To validate the framework before full-scale compilation:

### 5 Psychrometric Zones
1. **Hot-dry** (e.g., Riyadh, Saudi Arabia)
2. **Hot-humid** (e.g., Singapore)
3. **Temperate** (e.g., San Francisco, USA)
4. **Cold-dry** (e.g., Ulaanbaatar, Mongolia)
5. **Cold-humid** (e.g., Bergen, Norway)

### Per Zone
- Full psychrometric profile
- 3–5 animal species with coded thermoregulatory features
- 2–3 vernacular building traditions with coded design features
- Strategy correspondence analysis

### Pilot Output
- Populated tables for 5 zones (~20 animals, ~12 buildings)
- Cross-domain strategy correspondence matrix
- Preliminary psychrometric clustering
- Visual: strategy distributions on psychrometric chart overlays

---

## 13. References

See Section 5 for full citations organized by topic. Key foundational works:

- Schmidt-Nielsen, K. (1965). *Desert Animals.*
- Schmidt-Nielsen, K. et al. (1970). Counter-current heat exchange in respiratory passages.
- Gates, D.M. (1980). *Biophysical Ecology.*
- Olgyay, V. (1963). *Design with Climate.*
- Givoni, B. (1969). *Man, Climate and Architecture.*
- Helmuth, B. et al. (2005). Biophysics, physiological ecology, and climate change.
- McCafferty, D.J. et al. (2018). Animal thermoregulation: a review relevant to temperature control in buildings.
- Porter, W.P. & Kearney, M. (2009). Size, shape, and the thermal niche of endotherms.
- Badarnah, L. (2015). A biophysical framework of heat regulation strategies for biomimetic building envelopes.
- Imani, N. & Vale, B. (2020). A framework for finding inspiration in nature.

---

*Document generated 2026-04-04. This is a living research document — update as the project evolves.*
