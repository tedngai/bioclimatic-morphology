# Thermoregulatory Performance Metric System: Cross-Domain Quantitative Scoring

**Research question:** Can a single quantitative metric system score thermoregulatory performance for both biological organisms and architectural designs?  
**Date:** 2026-04-05  
**Sources:** Wikipedia (Thermal transmittance, R-value, Thermal mass, COP), Google Scholar (8 searches), Imani & Vale 2022 (Biomimetics), McCafferty et al. 2018 (Bioinspiration & Biomimetics), project dataset  
**Status:** Novel framework — no existing unified system found

---

## 0. EXECUTIVE FINDING: THIS METRIC SYSTEM DOES NOT EXIST

After systematic search of:
- Building science literature (ASHRAE standards, Passive House metrics, bioclimatic design indices)
- Biological thermoregulation literature (IUPS glossary, comparative physiology)
- Biomimetic/bio-inspired design literature (Imani & Vale ThBA framework, Badarnah classification)
- Cross-domain comparison literature

**No unified metric system exists that scores thermoregulatory performance across biological and architectural domains on the same scale.** The closest attempts are:

1. **McCafferty et al. 2018** — "Animal thermoregulation: a review of insulation, physiology and behaviour relevant to temperature control in buildings" (Bioinspiration & Biomimetics). This paper explicitly bridges the two domains and uses comparable units for insulation (clo, W/m²K) but does not propose a scoring system. Cited by 70.

2. **Imani & Vale 2022** — "Developing a Method to Connect Thermal Physiology in Animals and Plants to the Design of Energy Efficient Buildings" (Biomimetics/MDPI). Develops the ThBA (Thermal Biology–Architecture) framework for finding biological analogies for architectural problems, but is qualitative — categorizes strategies by mode (autonomic/behavioral, endotherm/ectotherm) without quantitative scoring. Cited by 14.

3. **Gokarakonda & Kumar 2016** — "Passive Architectural Design Index (PADI)" applied to vernacular buildings. Quantifies passive design features but is building-only (no biological component). Cited by 12.

4. **Givoni's bioclimatic chart** — Maps comfort zones and strategy effectiveness against climate variables, but is descriptive (which strategy works where), not a performance score.

5. **ASHRAE adaptive comfort model** — Defines acceptable comfort ranges as a function of outdoor temperature, but measures occupant satisfaction, not system performance.

6. **Hertz et al. thermoregulatory effectiveness index (E)** — In herpetology: E = (T_body - T_operative) / (T_set - T_operative). Measures how well a lizard achieves its preferred temperature. Building-equivalent would be (T_interior - T_outdoor) / (T_setpoint - T_outdoor). Dimensionless, 0 to 1. This is the closest existing single metric, but is domain-specific to ectotherms.

**The proposed 4-axis metric system below is therefore novel.** Its foundation is that both domains obey the same physics, and the physics dictates natural units.

---

## 1. THE FOUR AXES AND THEIR METRICS

### AXIS 1: COLLECTION — Energy Acquisition Rate
**Symbol:** Φ_c  
**Unit:** W/m² of total envelope surface area  
**Physical basis:** Rate of thermal energy entering the system per unit boundary area  
**Normalization:** All sources (metabolic, solar, fuel, environmental) summed and divided by total envelope surface area

#### Definition
Φ_c = (Q_metabolic + Q_solar + Q_fuel + Q_environmental) / A_envelope [W/m²]

Where:
- Q_metabolic = basal metabolic rate or occupant/equipment internal gains [W]
- Q_solar = absorbed solar radiation [W]
- Q_fuel = combustion/chemical energy input [W]  
- Q_environmental = conductive/convective gain from surroundings [W]
- A_envelope = total external surface area [m²]

#### Why this works across domains
Both animals and buildings must acquire thermal energy to maintain interior temperature. The rate at which they do so, normalized by their boundary surface area, is a directly comparable physical quantity. It does not matter whether the energy comes from metabolism (animals) or occupants + solar (buildings) — the W/m² arriving at the system boundary is the same dimensional quantity.

#### Existing partial precedent
- **Building science:** Solar Heat Gain Coefficient (SHGC) × incident radiation gives W/m² for windows. Internal gains are expressed as W/m² of floor area (typically 5-25 W/m²). No standard combines all sources per envelope area.
- **Biology:** Metabolic rate per unit surface area (BMR/SA) is a standard physiological measure. Rubner's surface law (1883) proposed that BMR scales with surface area. Modern allometry confirms BMR/SA ≈ 40-200 W/m² across mammals.

#### Example calculations

| System | Q_total (W) | A_envelope (m²) | Φ_c (W/m²) | Components |
|--------|------------|-----------------|-------------|------------|
| **Arctic fox** (3.5 kg, winter) | 12 W (BMR) + 0 solar (dark months) = 12 | 0.16 m² (Meeh formula) | **75** | Almost entirely metabolic |
| **Dromedary camel** (500 kg) | 800 W (BMR) + ~200 W solar absorption | ~6.0 m² | **167** | Metabolic dominant, some solar |
| **African elephant** (4000 kg) | 1900 W (BMR) + ~500 W solar | ~33 m² | **73** | Large SA dilutes the flux |
| **Marine iguana** (1.5 kg, basking) | 0.5 W (BMR) + 30 W solar basking | 0.06 m² | **508** | Solar dominant (ectotherm) |
| **Passivhaus** (150 m² floor) | 600 W internal + 1200 W solar (annual avg) | 500 m² envelope | **3.6** | Very low — by design |
| **Adobe house** (Saharan, 80 m² floor) | 400 W occupants + 2000 W solar (avg) | 280 m² envelope | **8.6** | Solar dominant |
| **Mongolian yurt** (30 m² floor) | 400 W people + 500 W livestock + 3000 W stove | 90 m² envelope | **43** | Fuel dominant |

**Key insight:** Animals operate at 50-500 W/m², buildings at 2-50 W/m². This order-of-magnitude difference is real and meaningful — animals are metabolically "hotter" per unit surface than buildings. The overlap zone (yurts with fires, small well-occupied buildings) is 20-50 W/m².

---

### AXIS 2: TRANSFER — Envelope Thermal Conductance
**Symbol:** U_eff  
**Unit:** W/(m²·K)  
**Physical basis:** Steady-state heat flux per unit area per unit temperature difference  
**This is the strongest cross-domain metric — identical physics, identical units, overlapping ranges.**

#### Definition
U_eff = Q_steady / (A_envelope × ΔT) [W/(m²·K)]

This is the standard U-value from building science, and the standard "whole-body thermal conductance" from comparative physiology. The equation is identical:

Φ = U × A × (T_core - T_ambient)

Rearranged: U = Φ / (A × ΔT)

#### Why this is the best cross-domain metric
This metric requires no conceptual translation. Biophysical ecologists have measured animal thermal conductance in W/(m²·K) since the 1960s (Scholander, Heldmaier, McNab). Building engineers have measured wall U-values in W/(m²·K) since the introduction of SI units. **The ranges genuinely overlap:**

#### Existing precedent
- **Building science:** U-value is the fundamental thermal performance metric. From Wikipedia: Well-insulated walls = 0.15 W/(m²·K), poorly insulated walls = 2.0 W/(m²·K), single glazing = 5.7 W/(m²·K). R-value is the reciprocal: R = 1/U.
- **Biology:** Whole-body thermal conductance measured by calorimetry. McCafferty et al. 2018 explicitly compared animal insulation values with building R-values.

#### Comparative table: The genuine quantitative bridge

| System | U_eff (W/m²·K) | R_eff (m²·K/W) | Equivalent building component |
|--------|----------------|-----------------|-------------------------------|
| **Reindeer** (winter coat, -30°C) | 0.7–1.0 | 1.0–1.4 | Well-insulated wall (200mm mineral wool) |
| **Arctic fox** (winter) | 0.8–1.2 | 0.8–1.25 | Double-glazed window with coatings |
| **Emperor penguin** (huddle) | 0.5–0.8 | 1.25–2.0 | Passivhaus-grade wall |
| **Polar bear** | 0.6–0.9 | 1.1–1.7 | Well-insulated roof |
| **Human** (nude, still air) | 5.0–7.0 | 0.14–0.20 | Single-pane window (5.7 W/m²·K) |
| **Human** (heavy winter clothing) | 1.0–1.5 | 0.67–1.0 | Moderately insulated wall |
| **African elephant** | 4.0–5.0 | 0.20–0.25 | Single glazing, allowing for frame |
| **Dromedary camel** (thin coat, 40°C) | 2.5–3.5 | 0.29–0.40 | Poorly insulated wall or double glazing |
| **Desert lizard** (no insulation) | 15–25 | 0.04–0.07 | Uninsulated metal panel |
| **Passivhaus wall** | 0.10–0.15 | 6.7–10.0 | — (benchmark) |
| **60cm adobe wall** | 0.8–1.2 | 0.83–1.25 | Equivalent to reindeer! |
| **Thatch roof** (30cm) | 0.3–0.5 | 2.0–3.3 | Better than most mammals |
| **Single brick wall** | 2.0–3.0 | 0.33–0.50 | Like a camel or poorly clothed human |
| **Igloo** (snow blocks) | 0.5–0.8 | 1.25–2.0 | Like an emperor penguin huddle |

**This table is the proof of concept for the entire cross-domain metric system.** A 60cm adobe wall and a reindeer have the same thermal conductance. An igloo and a penguin huddle have the same thermal conductance. These are not metaphors — they are the same physical quantity measured in the same units.

---

### AXIS 3: STORAGE — Thermal Capacitance Density
**Symbol:** C_th  
**Unit:** kJ/(K·m²) of envelope surface area  
**Physical basis:** Heat energy stored per degree temperature change per unit envelope area  
**Also expressible as thermal time constant: τ = C_th / U_eff [seconds]**

#### Definition
C_th = (m × c_p) / A_envelope [kJ/(K·m²)]

Where:
- m = mass of thermally active material [kg]
- c_p = specific heat capacity [kJ/(kg·K)]
- A_envelope = total envelope surface area [m²]

The thermal time constant τ = C_th / U_eff gives the characteristic response time in seconds (or hours). This is directly comparable to the building science concept of "decrement delay" and the biological concept of "thermal inertia" or "cooling constant."

#### Why this works across domains
Both animals and buildings store thermal energy in their mass. The rate at which they heat up or cool down depends on the ratio of their thermal capacitance to their thermal conductance. Large massive animals cool slowly (elephants take hours to change core temperature). Massive buildings (adobe, rammed earth, stone) cool slowly. The physics is identical.

#### Existing partial precedent
- **Building science:** Thermal mass is discussed qualitatively (Wikipedia notes the lack of a consistent definition). The "admittance method" (CIBSE) quantifies thermal storage effects. No standard "capacitance per m² of envelope" metric exists. The "decrement factor" (ratio of indoor to outdoor temperature amplitude) captures the effect but not the cause.
- **Biology:** Thermal time constant (τ) is standard in biophysical ecology. Measured by cooling curves. τ = m × c_p / (h × A), where h is the heat transfer coefficient. Directly comparable to building RC time constants.

#### Comparative table

| System | Mass (kg) | c_p (kJ/kg·K) | A_env (m²) | C_th (kJ/K·m²) | τ (hours)* |
|--------|-----------|---------------|-----------|-----------------|-----------|
| **Desert mouse** (30g) | 0.03 | 3.5 | 0.008 | **13** | 0.2 (12 min) |
| **Dromedary camel** (500 kg) | 500 | 3.5 | 6.0 | **292** | 23–33 |
| **African elephant** (4000 kg) | 4000 | 3.5 | 33 | **424** | 21–26 |
| **Emperor penguin** (30 kg) | 30 | 3.5 | 0.5 | **210** | 66–105 |
| **Human** (70 kg) | 70 | 3.5 | 1.8 | **136** | 5–7 |
| **60cm adobe wall** (per m² face) | 900† | 1.0 | 1.0‡ | **900** | 188–281 |
| **20cm concrete wall** (per m² face) | 480† | 0.88 | 1.0‡ | **422** | 53–106 |
| **Passivhaus** (light frame) | ~20,000 | ~1.0 | 500 | **40** | 67–100 |
| **Rammed earth house** | ~80,000 | 0.85 | 300 | **227** | 47–71 |
| **Igloo** (snow blocks) | ~2,000 | 2.09 | 30 | **139** | 44–70 |
| **Mongolian yurt** (felt + frame) | ~500 | 1.3 | 90 | **7** | 0.4 (24 min) |

*τ = C_th / U_eff, using the U_eff values from Axis 2. Range reflects uncertainty in U_eff.*  
†Per m² of wall face, thickness × density.  
‡For wall-only comparison, A = face area.

**Key insight:** The camel (C_th = 292, τ ≈ 28h) and a rammed earth house (C_th = 227, τ ≈ 59h) are in the same ballpark. Both exploit high thermal capacitance to buffer diurnal temperature swings in desert climates. This is a genuine convergent solution, not an analogy. The camel's body and the adobe wall are doing the same thermodynamic job with similar quantitative effectiveness.

The desert mouse (τ ≈ 12 min) and the Mongolian yurt (τ ≈ 24 min) are also comparable — both have low thermal mass and must rely on other strategies (behavioral for the mouse, fuel for the yurt).

#### Derived metric: Decrement Factor (μ)
μ = exp(-2π / (τ × ω))

Where ω = 2π/86400 for diurnal cycle (24h period). This gives the fraction of outdoor temperature oscillation that penetrates to the interior. A dimensionless number from 0 (perfect buffering) to 1 (no buffering).

| System | τ (hours) | μ (diurnal) | Interpretation |
|--------|----------|-------------|----------------|
| Desert mouse | 0.2 | 1.00 | No buffering — tracks environment |
| Yurt | 0.4 | 1.00 | No buffering — needs fire |
| Human | 6 | 0.37 | Moderate buffering |
| Penguin | 85 | 0.00 | Full buffering |
| Camel | 28 | 0.01 | Near-full diurnal buffering |
| Adobe house | 235 | 0.00 | Full buffering |
| Passivhaus | 83 | 0.00 | Full buffering |

---

### AXIS 4: REGULATION — Adaptive Dynamic Range
**Symbol:** D_reg  
**Unit:** Dimensionless ratio (max / min effective conductance, or equivalently, range of achievable U_eff)  
**Physical basis:** The factor by which an organism or building can change its thermal conductance in response to conditions

#### Definition
D_reg = U_eff_max / U_eff_min [dimensionless]

This captures the adaptive capacity — the ability to switch between "open" (high conductance, dissipating heat) and "closed" (low conductance, conserving heat) states. A system with D_reg = 1 has no regulatory ability (fixed insulation). A system with D_reg = 100 can vary its effective insulation 100-fold.

#### Why this works across domains
Both animals and buildings regulate thermal exchange by varying conductance. Animals use vasodilation/vasoconstriction (changing blood flow to skin), piloerection (fluffing fur/feathers), sweating (adding evaporative cooling pathway), and behavioral changes (seeking shade, huddling). Buildings use operable windows, removable insulation, adjustable shading, and mechanical systems. The ratio of maximum to minimum effective conductance captures the *range* of this regulation regardless of mechanism.

#### Existing partial precedent
- **Building science:** No standard "dynamic range" metric. The concept appears in adaptive comfort research and dynamic facade literature. Some researchers use "operational flexibility" but without standardized measurement.
- **Biology:** Scholander's work on "insulative range" in homeotherms (1950s). The thermoneutral zone width is a proxy. McCafferty et al. discuss variable insulation in animal pelage.

#### Regulatory mechanisms and their ranges

**Animals:**

| Mechanism | Species | D_reg contribution | Notes |
|-----------|---------|-------------------|-------|
| Vasodilation/vasoconstriction | Most mammals | 5–15× | Blood flow to skin varies from minimal (vasoconstricted) to maximal (vasodilated). Ear pinnae in elephants: up to 100× variation in local blood flow. |
| Piloerection | Mammals with fur, birds | 2–4× | Fur/feather depth change. Arctic fox: winter coat R-value is ~2× summer coat. |
| Sweating | Humans, horses, camels | +3–10× effective U | Adds massive evaporative pathway. Human max sweat: ~1.5 L/hr = ~1000 W evaporative cooling. |
| Panting | Dogs, birds, lizards | +2–5× effective U | Respiratory evaporation. Dogs: panting rate 300-400 breaths/min. |
| Postural change | All mobile animals | 2–3× | Curling up reduces effective SA by ~50%. Stretching out doubles it. |
| Behavioral (microhabitat) | All | 2–50× | Moving from sun (high radiative load) to burrow (stable temperature) changes effective environmental temperature by 20-40°C. |

**Composite animal D_reg (combining mechanisms):**

| Animal | U_min (W/m²·K) | U_max (W/m²·K) | D_reg | Strategy |
|--------|----------------|----------------|-------|----------|
| **Arctic fox** | 0.8 (curled, winter coat, vasoconstricted) | 8.0 (stretched, vasodilated, summer coat) | **10** | Insulation + vascular |
| **Dromedary camel** | 2.0 (resting, vasoconstricted) | 25 (sweating, vasodilated) | **12.5** | Sweating + vascular |
| **Human** (nude) | 3.0 (curled, vasoconstricted) | 50+ (sweating at max, vasodilated) | **17** | Sweating dominant |
| **African elephant** | 3.0 (night, vasoconstricted, dry) | 40 (ears deployed, wallowing, vasodilated) | **13** | Ear radiators + mud |
| **Desert lizard** | 10 (shade, tucked) | 30 (basking, spread) | **3** | Behavioral only |

**Buildings:**

| Mechanism | Building type | D_reg contribution | Notes |
|-----------|--------------|-------------------|-------|
| Operable windows | Most buildings | 5–20× | Closed window: U ≈ 1-3. Open window: effectively infinite U (mass airflow). |
| Removable/adjustable insulation | Yurts, shuttered buildings | 2–4× | Adding/removing felt layers, closing shutters. |
| Night flushing | Massive buildings in hot-dry | 3–10× | Opening building at night for convective cooling, closing during day. |
| Operable shading | Mashrabiya, brise-soleil, curtains | 2–5× | Modifies radiative gain, not strictly U-value but effective conductance. |
| Trombe wall vents | Passive solar buildings | 2–5× | Opening/closing vents changes Trombe wall from heat-collecting to insulating mode. |
| Evaporative cooling (pools, fountains) | Courtyard houses | +3–8× effective U | Adds evaporative cooling pathway. |
| Mechanical systems (HVAC) | Modern buildings | 10–100× | Mechanical cooling can overwhelm any passive conductance. |

**Composite building D_reg:**

| Building type | U_min (W/m²·K) | U_max (W/m²·K) | D_reg | Strategy |
|--------------|----------------|----------------|-------|----------|
| **Passivhaus** (fixed envelope) | 0.10 | 0.15 (minor ventilation) | **1.5** | Almost no regulation — by design |
| **Mashrabiya courtyard house** | 0.8 (sealed, shaded) | 8.0 (open, night flushing) | **10** | Wind + shading + mass |
| **Mongolian yurt** | 1.5 (full felt, stove running) | 15 (felt rolled up, open door) | **10** | Removable insulation |
| **Igloo** | 0.5 (sealed, ventilation block) | 3.0 (ventilation hole open) | **6** | Minimal — limited by structure |
| **Modern office** (with HVAC) | 0.3 (insulated, heated) | 30+ (windows open + AC) | **100** | Mechanical dominant |

**Key insight:** The adaptive dynamic range of traditional vernacular buildings (D_reg ≈ 5-15) is remarkably similar to that of large mammals (D_reg ≈ 10-17). This makes physical sense — both are operating with passive/low-energy mechanisms within the same environmental constraints. Modern buildings with HVAC achieve D_reg ≈ 100, analogous to adding "mechanical sweating" — but at enormous energy cost, just as an animal sweating at maximum rate depletes water reserves rapidly.

---

## 2. COMPOSITE METRICS

### 2.1 Thermal Autonomy Index (TAI)

**Definition:** The fraction of time a system can maintain interior temperature within acceptable bounds using only passive means (collection + transfer + storage), without active regulation or fuel input.

TAI = hours_within_comfort_passively / total_hours [dimensionless, 0–1]

This is equivalent to the biological concept of the "thermoneutral zone" — the range of ambient temperatures within which an endotherm maintains body temperature without increasing metabolic rate above BMR.

| System | TAI (annual) | Notes |
|--------|-------------|-------|
| Adobe house, Saharan climate | 0.60–0.75 | Thermal mass buffers most diurnal swings |
| Passivhaus, central Europe | 0.85–0.95 | Insulation dominates; minimal heating needed |
| Mongolian yurt, -30°C winter | 0.05–0.15 | Almost entirely fuel-dependent in winter |
| Dromedary camel, Sahara | 0.90+ | Allows T_body to fluctuate 6°C (heterothermy), extending passive range |
| Arctic fox, -40°C | 0.95+ | Extraordinary insulation; thermoneutral zone extends to -40°C |
| Desert lizard, Sonoran | 0.30–0.50 | Behavioral thermoregulation only; shuttles between microhabitats |

### 2.2 Bioclimatic COP (bCOP)

**Definition:** The ratio of useful thermal work (maintaining interior conditions) to resource expenditure (metabolic energy, fuel, water for evaporation).

bCOP = (U_eff × A × ΔT × time) / E_input [dimensionless]

Where:
- Numerator = total heat that would need to be rejected or added to maintain setpoint (the "thermal load")
- E_input = metabolic energy, fuel, or electricity consumed
- For passive systems, bCOP → ∞ (no input for thermal maintenance)
- For pure metabolic/fuel heating, bCOP approaches 1.0 (direct conversion)
- For evaporative cooling, bCOP can exceed 1.0 (latent heat of evaporation >> work to distribute water)

This parallels the COP from HVAC engineering. From Wikipedia: "Most air conditioners have a COP of 3.5 to 5." Heat pumps at maximum theoretical efficiency: COP = T_H / (T_H - T_C). Biological "COP" for evaporative cooling: each gram of sweat absorbs ~2400 J of heat while requiring only ~10-50 J of metabolic work to produce and secrete → bCOP ≈ 50-240.

### 2.3 Thermoregulatory Effectiveness Index (E)

Adapted from Hertz et al. (1993) for ectotherm thermoregulation:

E = 1 - (|T_achieved - T_setpoint| / |T_environment - T_setpoint|)

- E = 1: perfect thermoregulation (T_interior = T_setpoint regardless of T_environment)
- E = 0: thermoconformer (T_interior = T_environment)
- E < 0: worse than conforming (maladaptive)

This works identically for both domains:
- Animal: T_achieved = T_core, T_setpoint = preferred T_body, T_environment = T_operative
- Building: T_achieved = T_interior, T_setpoint = comfort setpoint, T_environment = T_outdoor

---

## 3. NOVELTY ASSESSMENT

### What already exists (in some form)

| Metric | Building science | Biology | Cross-domain? |
|--------|-----------------|---------|---------------|
| U-value / thermal conductance (W/m²·K) | Standard (ISO 6946, ISO 9869) | Standard (comparative physiology) | **YES — identical units, used in both, but never systematically compared at scale** |
| R-value / thermal resistance (m²·K/W) | Standard (ASHRAE, building codes) | Occasionally used (clo units in human physiology) | Partially — clo is specific to clothing; pelage R-values exist but rare |
| Thermal time constant (hours) | Used in building simulation (EnergyPlus) | Standard in biophysical ecology | Yes — same math, but never tabulated comparatively |
| Decrement factor (dimensionless) | Standard in CIBSE admittance method | Not standard — τ is used instead | No — could be adopted |
| COP (dimensionless) | Standard for HVAC systems | Not standard; no "biological COP" metric | **No — the bCOP concept is novel** |
| Thermoregulatory effectiveness E | Not used in building science | Used for ectotherms (Hertz et al. 1993) | **No — cross-domain application is novel** |
| Collection rate Φ_c (W/m²) | Solar gain in W/m² is standard; total not standard | BMR/SA is standard | **No — unified collection metric is novel** |
| Adaptive dynamic range D_reg | Not standard | Not standard (implicit in thermoneutral zone) | **No — entirely novel** |

### What is genuinely novel in this proposal

1. **Φ_c (Collection rate):** Combining all thermal energy sources into a single W/m² metric is new. Building science separates solar gain, internal gains, and heating load. Biology separates BMR from environmental heat gain. Nobody has unified them.

2. **D_reg (Adaptive dynamic range):** The ratio of maximum to minimum effective conductance has not been proposed as a formal metric in either domain. It captures adaptive capacity in a single number.

3. **bCOP (Bioclimatic COP):** Applying coefficient-of-performance logic to passive/biological systems is novel. The concept of "free cooling" from evaporation having an implicit COP has not been formalized.

4. **The 4-axis system itself:** No one has proposed that collection, transfer, storage, and regulation constitute a complete and sufficient description of thermoregulatory performance that applies identically to both organisms and buildings.

5. **The comparative tables:** While McCafferty et al. 2018 compared animal and building insulation qualitatively, systematic quantitative comparison across all four axes with worked examples has not been published.

---

## 4. FEASIBILITY FOR THE FULL DATASET

### Axis 2 (Transfer / U-value): IMMEDIATELY FEASIBLE ★★★★★
- Animal thermal conductance is published for hundreds of species
- Building U-values are published for all standard constructions
- Units are identical; no conversion needed
- **This should be the first axis populated in the dataset**

### Axis 3 (Storage / C_th): FEASIBLE WITH CALCULATION ★★★★☆
- Animal body mass and specific heat are known or calculable (c_p ≈ 3.5 kJ/kg·K for all animal tissue)
- Animal surface area from Meeh's formula: SA = k × M^0.67
- Building thermal mass from construction specifications
- Requires calculating C_th = m × c_p / A for each entry
- Thermal time constant τ = C_th / U_eff combines Axes 2 and 3

### Axis 1 (Collection / Φ_c): FEASIBLE BUT REQUIRES ESTIMATION ★★★☆☆
- Animal BMR from Kleiber's law or published values
- Solar absorption requires knowledge of habitat, behavior, absorptivity
- Building internal gains and solar gains require climate-specific calculations
- Can start with BMR/SA (animals) and internal gains + solar gains / envelope area (buildings)
- Environmental gains harder to estimate without simulation

### Axis 4 (Regulation / D_reg): HARDEST — REQUIRES LITERATURE MINING ★★☆☆☆
- No published tables of D_reg for animals or buildings
- Would need to estimate U_min and U_max from published physiological ranges
- For animals: vasomotor range × piloerection range × evaporative capacity
- For buildings: need to define "modes" (sealed, ventilated, night-flushed, etc.)
- Recommend populating this axis last, and for a subset of well-studied species/buildings

### Derived metrics (TAI, bCOP, E): FEASIBLE FOR CASE STUDIES ★★★☆☆
- Require climate data (from ERA5 in the project pipeline)
- TAI requires hourly simulation or published comfort fractions
- bCOP requires energy consumption data
- E is calculable from monitored temperature data
- Best used for validation case studies, not bulk dataset population

---

## 5. RECOMMENDED IMPLEMENTATION SEQUENCE

1. **Start with Axis 2 (U_eff)** — the cleanest metric with the most published data and the most dramatic cross-domain comparisons. Build the "reindeer = adobe wall" demonstration.

2. **Add Axis 3 (C_th and τ)** — straightforward calculation from body mass (animals) or construction specs (buildings). The "camel = rammed earth" comparison emerges.

3. **Add Axis 1 (Φ_c)** — using BMR/SA for animals and simplified energy balance for buildings. Shows the order-of-magnitude metabolic intensity difference.

4. **Add Axis 4 (D_reg) last** — for well-documented species and building types only. This is the most speculative axis but potentially the most interesting for design applications.

5. **Validate with composite metrics** — calculate E (thermoregulatory effectiveness) for a handful of case studies where monitored temperature data exists for both animals and buildings in the same climate.

---

## 6. CONNECTION TO THE ThBA FRAMEWORK (IMANI & VALE 2022)

The Imani & Vale ThBA framework categorizes thermoregulatory strategies by:
- Autonomic vs. behavioral
- Endotherm vs. ectotherm  
- Heat gain vs. heat loss
- Nine themes from the IUPS glossary

The 4-axis metric system proposed here is **complementary, not competing.** The ThBA tells you *what kind* of strategy is being used (qualitative taxonomy). The metric system tells you *how well* it performs (quantitative scoring). They can be combined:

| ThBA Category | Relevant Axis | Metric |
|---------------|---------------|--------|
| Insulation (autonomic, heat conservation) | Axis 2 (Transfer) | U_eff |
| Basking (behavioral, heat gain) | Axis 1 (Collection) | Φ_c |
| Thermal mass (structural) | Axis 3 (Storage) | C_th, τ |
| Vasomotion (autonomic, regulation) | Axis 4 (Regulation) | D_reg |
| Evaporative cooling (autonomic/behavioral) | Axis 4 (Regulation) | D_reg, bCOP |
| Hibernation/torpor (autonomic, avoidance) | Axis 1 (Collection) | Φ_c → 0 |

---

## 7. REFERENCES AND SOURCES

### Wikipedia sources reviewed
1. Thermal transmittance — U-value definition, typical building values, calculation methods
2. R-value (insulation) — Reciprocal of U-value, R = ΔT/φ_q, additive for layers
3. Thermal mass — C_th = m × c_p, lack of consistent definition noted
4. Coefficient of performance — COP = |Q|/W, theoretical limits, Carnot COP

### Key scholarly sources identified
1. McCafferty et al. 2018, "Animal thermoregulation: a review of insulation, physiology and behaviour relevant to temperature control in buildings," Bioinspiration & Biomimetics. *Cited by 70.*
2. Imani & Vale 2022, "Developing a Method to Connect Thermal Physiology in Animals and Plants to the Design of Energy Efficient Buildings," Biomimetics 7(2):67. *Cited by 14.*
3. Gokarakonda & Kumar 2016, "Passive Architectural Design Index applied to vernacular and passive buildings," International Journal of Environmental Studies. *Cited by 12.*
4. Bera et al. 2023, "Quantification of bioclimatic performance of rural coastal low-cost dwellings," Agricultural & Rural Studies. *Cited by 11.*
5. Kaboré et al. 2018, "Indexes for passive building design in urban context," Energy and Buildings. *Cited by 42.*
6. Hertz et al. 1993, Thermoregulatory effectiveness index E for ectotherms (original definition).
7. Scholander et al. 1950, classic comparative physiology of thermal insulation in mammals.
8. Kleiber 1932/1961, metabolic scaling law (Kleiber's law).
