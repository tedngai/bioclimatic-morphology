# Energy Collection / Acquisition: Animal Thermoregulation vs. Building Passive Design

**Research focus:** How thermal energy *enters* the system  
**Sources:** Wikipedia — Thermoregulation, Passive Solar Building Design, Basal Metabolic Rate, Trombe Wall  
**Date:** 2026-04-05

---

## 1. SOLAR COLLECTION

### 1A. Direct Solar Radiation Absorption

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Basking / heliothermy — orienting body to maximize intercepted solar radiation | Direct-gain passive solar — south-facing glazing admits shortwave radiation to interior surfaces |
| **Species examples** | Desert lizards (*Microlophus occipitalis*, *Ctenophorus decresii*) bask by raising head from burrow, then exposing entire body. Angle of body relative to sun is actively controlled. Snakes and turtles bask on rocks. | South-facing glass in Northern Hemisphere (north-facing in Southern). Direct-gain systems utilize 65-70% of solar radiation striking the aperture. |
| **Orientation control** | Lizards orient perpendicular to sun rays for maximum gain, parallel for minimum. Behavioral: morning emergence sequence (head first, then body). | Building long axis oriented E-W; equator-facing facade maximized. A few degrees east of true south captures morning sun. |
| **Surface area management** | Ectotherms flatten body, spread ribs (horned lizards), expose wing surfaces (butterflies). Folding skin or concealing wings reduces exposure. | Window-to-wall ratio on equator face: 5-7% of floor area for sun-tempered buildings; higher with added thermal mass. Minimize glazing on other facades, especially west. |
| **Shared physical principle** | **Radiative heat transfer**: Q = alpha * A * I * cos(theta), where alpha = absorptivity, A = exposed area, I = solar irradiance, theta = angle of incidence. Lambert's cosine law governs both. |
| **Quantitative values** | Solar irradiance at ground: ~1000 W/m^2 peak. Lizard basking can raise body temp 1-2 C/min in favorable conditions. | Direct-gain systems convert 65-70% of incident solar to useful heat. Passive solar fraction (PSF): 5-75% depending on optimization level. |
| **Proposed tag** | `solar_direct_gain` |

### 1B. Dark Surface Absorption (Selective Absorptivity)

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Dark coloration increases solar absorptivity of skin/fur/scales | Dark-painted thermal mass surfaces absorb shortwave radiation; selective coatings maximize absorption while minimizing IR re-emission |
| **Species examples** | Dark-colored lizards and snakes heat faster. Marine iguanas are black to maximize solar gain after cold ocean foraging. Many desert beetles are dark for morning warm-up. | Trombe wall: "painted a dark color in order to absorb thermal energy from incident sunlight." Kelbaugh House (1974): concrete wall painted with selective black paint over masonry sealer. |
| **Selective surfaces** | Not documented in animals — animal surfaces are non-selective (high absorptivity = high emissivity generally). Some evidence of spectral tuning in butterfly wing scales. | Selective surface: metal foil glued to wall exterior. "Absorbs almost all radiation in the visible portion of the solar spectrum and emits very little in the infrared range." High absorptance (~0.95) + low emittance (~0.1). |
| **Absorptivity values** | Dark reptile skin: alpha ~ 0.90-0.95. Light-colored desert mammals (e.g., fennec fox, addax): alpha ~ 0.3-0.5. Dark fur (black bear): alpha ~ 0.90-0.95. Light fur (Arctic fox winter): alpha ~ 0.2-0.3. | Dark painted surface: alpha ~ 0.90-0.95. Adobe (natural): alpha ~ 0.55-0.75. Whitewash/lime: alpha ~ 0.20-0.30. Dark stone (basalt): alpha ~ 0.85-0.95. Red brick: alpha ~ 0.65-0.80. Selective coating: alpha_solar ~ 0.95, epsilon_IR ~ 0.10. |
| **Shared physical principle** | **Kirchhoff's law of thermal radiation**: at thermal equilibrium, absorptivity = emissivity at each wavelength. Both domains exploit the difference between shortwave solar spectrum (where absorption is desired) and longwave thermal IR (where emission may or may not be desired). |
| **Proposed tag** | `absorptive_surface` |

### 1C. Indirect Solar Gain (Thermal Storage Wall / Heated Substrate)

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Conductive heat gain from sun-heated substrates (rocks, sand, soil) that have absorbed and stored solar energy | Trombe wall / thermal storage wall: massive wall behind glazing absorbs solar energy, conducts it inward over time (time-lagged gain) |
| **Species examples** | Lizards lie on hot rocks heated by sun, absorbing heat by conduction. "An example of behavioral adaptation is that of a lizard lying in the sun on a hot rock in order to heat through radiation and conduction." Sand temperatures in ergs reach 57.7 C. | Trombe wall at Odeillo, France (1967): 2-ft thick concrete wall, dark-painted, double-glazed. 70% of annual heating from solar. Kelbaugh House: 76-84% heating cost reduction. Montmedy house: 77% reduction in heating load. |
| **Time lag** | Rock/soil stores daytime heat, available for evening/night use. Snakes coil on warm rocks at dusk. Burrowing animals benefit from soil thermal lag. | "The delayed heat-flow phenomenon is known as time lag and it causes the heat gained during the day to reach the interior surface of the thermal mass later." Optimum wall thickness varies by material. Concrete: 8-16 inches. Adobe: 8-12 inches. |
| **Greenhouse trapping** | Not applicable in animals (no transparent covering). | "Heat from the sun, in the form of shorter-wavelength radiation, passes through the glazing largely unimpeded. When this radiation strikes the dark colored surface... the energy is absorbed and then re-emitted in the form of longer-wavelength radiation that cannot pass through the glazing as readily." Greenhouse effect traps heat between glazing and mass. |
| **Quantitative values** | Rock surface temperatures: 50-70 C in desert conditions. Lizard gains ~0.5-1 C/min from hot rock contact. | Trombe wall air space temperatures can exceed 66 C (150 F). Wall surface temperatures reach similar levels. Water walls store more heat per volume than masonry (higher specific heat capacity of water: 4.18 kJ/kg-K vs. ~0.84 for concrete). |
| **Shared physical principle** | **Conduction through thermal mass with time lag**: both exploit materials with high heat capacity that absorb solar energy and release it later. Q = k * A * dT/dx (Fourier's law of conduction). |
| **Proposed tag** | `solar_indirect_gain` |

---

## 2. METABOLIC / INTERNAL HEAT PRODUCTION

### 2A. Basal Metabolic Heat (Continuous Internal Generation)

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Basal metabolic rate (BMR): continuous heat production from cellular respiration in endotherms. ~70% of total daily energy expenditure. | Internal gains: continuous heat production from occupants, lighting, equipment, and cooking |
| **Scaling law** | Kleiber's law: BMR = 70 * M^0.75 kcal/day (where M = body mass in kg). Alternatively: BMR proportional to lean body mass. | Roughly linear with occupancy. ~100 W per sedentary adult human. Cooking: 500-2000 W depending on appliance. Equipment: variable. |
| **Range by body size** | Mouse (0.02 kg): BMR ~ 70 * 0.02^0.75 = ~2.3 kcal/day = ~0.11 W. Rat (0.3 kg): ~12 kcal/day = ~0.58 W. Human (70 kg): ~1500-1700 kcal/day = ~75-80 W. Elephant (4000 kg): ~70 * 4000^0.75 = ~39,500 kcal/day = ~1900 W. | Single occupant: ~100 W (75 W sensible + 25 W latent at rest). Family of 4: ~400 W. Traditional yurt with livestock: 400 W (people) + 300-500 W (animals) = 700-900 W. Dense traditional dwelling: 200-600 W total internal gains. |
| **Organ contribution** | Liver: 27%, Brain: 19%, Skeletal muscle: 18%, Kidneys: 10%, Heart: 7%, Other: 19%. At rest ~70% ATP from fat oxidation, ~30% from carbohydrates. | In buildings: occupants dominate in traditional construction. In modern buildings, equipment and lighting can exceed occupant heat. |
| **Phenotypic flexibility** | BMR is adjustable: lower temperatures -> higher BMR in birds and rodents. Red knot increases BMR ~40% before migration. Seasonal adjustment is well-documented. | Adjustable by occupancy scheduling, equipment use patterns. Traditional cultures adjust cooking and fire timing seasonally. |
| **Shared physical principle** | **Steady-state internal heat generation**: both require continuous energy conversion (chemical -> thermal) to maintain internal temperatures above ambient. The "furnace" must balance envelope losses. |
| **Proposed tag** | `internal_heat_generation` |

### 2B. Shivering Thermogenesis (Acute Muscular Heat Production)

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Involuntary rapid muscle contraction that converts chemical energy to heat. Can increase heat production 2-5x above BMR. | No direct building analogue. Closest: emergency/supplemental heating systems activated on demand (wood stove startup, electric space heater). |
| **Species examples** | All endotherms (mammals and birds) can shiver. Humans can sustain shivering for hours. Cold-exposed mice and rats increase metabolic rate 3-5x. | Traditional: lighting a fire in a cold house is the behavioral analogue — an acute, high-output heat source activated when passive gains are insufficient. |
| **Energy cost** | Very expensive metabolically. Unsustainable long-term. Requires large food/fat reserves. | Wood/dung fires are fuel-expensive. Traditional Mongolian yurt: cow dung fuel consumption rises sharply in extreme cold. |
| **Shared physical principle** | **Emergency heat production exceeding baseline**: both systems have a "burst mode" that trades efficiency for survival when passive/baseline gains fail. |
| **Proposed tag** | `emergency_heat_boost` |

### 2C. Non-Shivering Thermogenesis (Brown Adipose Tissue)

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Brown adipose tissue (BAT) generates heat by uncoupling oxidative phosphorylation from ATP synthesis via UCP1 protein. Mitochondria-rich cells convert fat directly to heat. | No direct analogue. Conceptually similar: catalytic or phase-change heat sources that release stored chemical energy without mechanical work (e.g., exothermic salts, calcium oxide + water in traditional heating). |
| **Species examples** | Hibernating bats use "rapid, non-shivering thermogenesis of their brown fat deposit to bring them out of hibernation." Newborn mammals and cold-adapted rodents have significant BAT deposits. Human infants have BAT; adults retain some. | Partial analogue: traditional Korean ondol floor heating uses slow combustion of fuel beneath a thermal mass floor — continuous low-grade heat without mechanical work. |
| **Efficiency** | Less metabolically costly than shivering. Can be sustained longer. Activated by sympathetic nervous system. | Ondol and kang (Chinese heated bed) systems achieve efficient fuel-to-heat conversion through slow combustion and conductive mass distribution. |
| **Shared physical principle** | **Chemical-to-thermal energy conversion in a dedicated subsystem**, decoupled from the primary function (muscle contraction / living space). The "heater" is architecturally separated from the "workspace." |
| **Proposed tag** | `dedicated_heat_subsystem` |

---

## 3. FOOD / FUEL ENERGY

### 3A. Fat Reserves as Metabolic Fuel (+ Metabolic Water)

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Stored body fat serves as both energy reserve and metabolic water source. Fat oxidation: C16H32O2 + 23O2 -> 16CO2 + 16H2O. Each 100g fat yields ~107g metabolic water. | Stored fuel (wood, dung, peat, coal, charcoal) provides chemical energy for heating. Traditional buildings stockpile fuel seasonally. |
| **Species examples** | Camel hump: concentrated fat deposit (~36 kg in a well-fed dromedary). "Storing fat reserves in one place (e.g., camel's hump) to avoid its insulating effect" — localized storage prevents unwanted insulation elsewhere. Fat oxidation provides both energy (9.4 kcal/g) and water. | Mongolian yurt: dried dung stockpiled for winter. Scandinavian traditions: peat and wood stored in summer. Irish bothans: turf/peat stacked against exterior walls (serving as both fuel reserve and insulation). |
| **Dual function** | Fat serves as: (1) energy reserve, (2) metabolic water source, (3) insulation (when distributed) or NOT insulation (when concentrated in hump). Respiratory quotient for fat = 0.696 (more O2 needed per CO2 produced than carbohydrates). | Fuel stockpiles serve as: (1) heating energy, (2) cooking energy, (3) sometimes insulation (peat walls, straw bales). Dung fuel from co-housed livestock creates a closed-loop energy system. |
| **Quantitative values** | Fat: 9.4 kcal/g (39.3 kJ/g). Metabolic water from fat: 107 g H2O per 100 g fat. A 36 kg camel hump = ~338,000 kcal energy + ~38.5 L metabolic water. Palmitic acid yields 106 ATP per molecule. | Wood: ~4.5 kWh/kg. Dried dung: ~3.5 kWh/kg. Peat: ~3.8 kWh/kg. Charcoal: ~8 kWh/kg. A family winter fuel stockpile: 2000-5000 kg depending on climate. |
| **Shared physical principle** | **Chemical energy storage for deferred thermal use**: both systems stockpile reduced carbon compounds (lipids / biomass) during resource-abundant periods for oxidation during energy-deficit periods. The thermochemistry is literally the same reaction: C-H bonds + O2 -> CO2 + H2O + heat. |
| **Proposed tag** | `chemical_energy_reserve` |

### 3B. Food Energy as Ongoing Fuel Input

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Continuous food intake provides substrates for metabolic heat production. Postprandial thermogenesis (heat from digestion) contributes ~10% of daily energy expenditure. | Continuous fuel input for hearth/stove. In traditional buildings, fire is maintained continuously or re-lit daily. |
| **Substrate types** | Carbohydrates: RQ = 1.0, 4 kcal/g. Fats: RQ = 0.696, 9.4 kcal/g. Proteins: RQ = 0.818, 4 kcal/g. At rest: ~70% energy from fat, ~30% from carbohydrates. | Biomass fuels: wood (cellulose), dung (mixed), peat (partially decomposed plant matter), animal fat/tallow (for lamps providing both light and heat). |
| **Shared physical principle** | **Sustained exothermic oxidation of organic compounds** maintaining thermal homeostasis. Both require continuous supply chain (foraging/farming for animals; fuel gathering for buildings). |
| **Proposed tag** | `sustained_fuel_input` |

---

## 4. ENVIRONMENTAL HEAT ABSORPTION

### 4A. Conductive Heat Gain from Ground

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Animals absorb heat by lying on warm ground, warm rocks, or warm sand heated by solar radiation | Buildings absorb heat from warm ground through foundation/floor contact (often unwanted in summer; beneficial in winter via earth coupling) |
| **Species examples** | Lizards lie on hot rocks and sand. Ground squirrels press against sun-warmed burrow walls. Snakes coil on warm asphalt/rocks at dusk. Sand temperature in desert ergs: up to 57.7 C. | Earth-sheltered buildings gain heat from ground in winter (ground temp > air temp). Adobe and rammed earth floors absorb stored ground heat. However: "in summer the earth temperature will be lower than the surface air temperature" — earth coupling provides cooling, not heating. |
| **Bidirectional** | Animals also dump heat to cool ground (lizards on cool burrow floors). Koalas wrap around cool tree trunks. The same conductive pathway works in both directions. | Earth tubes and earth-sheltered buildings exploit the same bidirectionality: warming in winter, cooling in summer. Ground temperature at depth stabilizes near annual mean air temperature. |
| **Quantitative values** | Desert rock surface: 50-70 C. Soil at 2m depth: approximately annual mean air temp (~15-20 C in temperate zones). | Soil at 2-3m depth: stable year-round, approximately annual mean air temperature. "Approximately 50% of the heat from the Sun is absorbed at the surface." Thermal lag at depth: weeks to months. |
| **Shared physical principle** | **Conductive heat transfer at the organism/building-ground interface**: Q = k * A * (T_surface - T_body) / d. Both exploit the thermal mass and solar charging of the ground as a heat source (or sink). |
| **Proposed tag** | `ground_conductive_gain` |

### 4B. Convective Heat Gain from Warm Air

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | When ambient air temperature exceeds body/interior temperature, convective heat transfer moves energy INTO the organism/building. This is typically unwanted. | When outdoor air is warmer than indoor air, infiltration and ventilation carry heat into the building — usually an unwanted gain in hot climates. |
| **Species examples** | Desert animals face convective heat gain when air temp > body temp (~37 C for mammals). At air temp > skin temp, "the body gains heat by convection and conduction." The only cooling path remaining is evaporation. | In hot climates, buildings gain heat through air infiltration. "Uncontrolled air infiltration from poor weatherization can contribute up to 40% of heat loss during winter" — the same pathway delivers unwanted heat gain in summer. |
| **Management** | Animals seek burrows, shade, microhabitats where air is cooler. Burrowing creates a sealed envelope. Fur can paradoxically insulate against convective heat gain ("Dense coats found in desert endotherms also aid in preventing heat gain such as in the case of the camels"). | Buildings in hot climates minimize openings during peak heat, use thermal mass to buffer daytime heat, and ventilate at night when air is cool. Sealed envelope + insulation resists convective gain. |
| **Shared physical principle** | **Newton's law of cooling in reverse**: when T_environment > T_system, the same convective transfer that normally cools becomes a heat gain pathway. Both domains respond by increasing resistance to convective exchange (insulation, sealing, reducing exposed surface). |
| **Proposed tag** | `convective_environmental_gain` |

### 4C. Kleptothermy / Social/Communal Heat Sharing

| Attribute | Animal Implementation | Building Implementation |
|---|---|---|
| **Mechanism** | Kleptothermy: sharing or stealing body warmth between individuals. Huddling increases effective thermal inertia and reduces per-capita surface area. | Communal heating from co-habiting humans and livestock. Traditional buildings that house animals on ground floor benefit from livestock body heat rising to living spaces above. |
| **Species examples** | Emperor penguins huddle in Antarctic winter — rotating positions to share thermal burden. Bats huddle in roosts. Mousebirds cluster. "Animals engage in kleptothermy in which they share or steal each other's body warmth." | Scandinavian longhouses: livestock on ground floor, humans above. Mongolian yurt: goats/sheep brought inside during extreme cold. Alpine Bauernhaus: stable integrated with dwelling. Each cow produces ~400-500 W of heat. |
| **Quantitative values** | Huddling reduces heat loss 20-50% per individual compared to isolation (varies by species and group size). Effective SA:V ratio decreases with group size. | A cow produces ~400-500 W. 10 cows in a ground-floor stable = 4-5 kW of "free" heating for the dwelling above. Human occupant: ~100 W each. |
| **Shared physical principle** | **Aggregation of internal heat sources to increase thermal inertia and reduce per-unit heat loss**: both exploit the fact that grouping heat-producing bodies reduces the ratio of total surface area to total volume (cf. Bergmann's rule at group scale). |
| **Proposed tag** | `communal_heat_pooling` |

---

## 5. SUMMARY: HARMONIZED ONTOLOGY TAGS FOR ENERGY COLLECTION

| Tag | Category | Animal Expression | Building Expression | Physical Principle |
|---|---|---|---|---|
| `solar_direct_gain` | Solar | Basking, heliothermy, body orientation to sun | South-facing glazing, direct-gain systems | Radiative absorption: Q = alpha * A * I * cos(theta) |
| `absorptive_surface` | Solar | Dark coloration (melanin), dark scales/skin | Dark-painted Trombe wall, selective coatings | Kirchhoff's law; spectral absorptivity tuning |
| `solar_indirect_gain` | Solar | Lying on sun-heated rocks/sand (conductive) | Trombe wall, thermal storage wall + glazing | Conduction through solar-charged thermal mass with time lag |
| `internal_heat_generation` | Metabolic/Internal | BMR: Kleiber's law, 70*M^0.75 kcal/day | Occupant heat (~100 W/person), equipment, cooking | Steady-state chemical-to-thermal energy conversion |
| `emergency_heat_boost` | Metabolic/Internal | Shivering thermogenesis (2-5x BMR increase) | Emergency fire/supplemental heating activation | Acute burst heat production trading efficiency for survival |
| `dedicated_heat_subsystem` | Metabolic/Internal | Brown adipose tissue (non-shivering thermogenesis) | Ondol/kang heated floor systems, hypocaust | Chemical-to-thermal conversion in isolated subsystem |
| `chemical_energy_reserve` | Fuel | Body fat (9.4 kcal/g, +107g H2O per 100g) | Fuel stockpiles (wood, dung, peat, charcoal) | Deferred oxidation of reduced carbon compounds |
| `sustained_fuel_input` | Fuel | Continuous food intake, postprandial thermogenesis | Continuous fire/stove fuel feeding | Ongoing exothermic oxidation of organic substrates |
| `ground_conductive_gain` | Environmental | Lying on warm rocks/sand/soil | Earth-coupled floors, earth sheltering | Fourier's conduction at ground interface |
| `convective_environmental_gain` | Environmental | Passive convective gain when T_air > T_body | Infiltration gain when T_outdoor > T_indoor | Newton's law of cooling in reverse |
| `communal_heat_pooling` | Environmental | Kleptothermy, huddling (penguins, bats) | Co-housed livestock, dense occupancy | Aggregation reduces SA:V ratio per heat source |

---

## 6. KEY QUANTITATIVE REFERENCE TABLE

| Parameter | Value | Context |
|---|---|---|
| Peak solar irradiance at ground | ~1000 W/m^2 | Both domains |
| Direct-gain solar utilization efficiency | 65-70% | Passive solar buildings |
| Trombe wall annual heating fraction | 70% (Odeillo), 77% (Montmedy) | Verified by monitoring |
| Passive solar fraction range | 5-75% depending on optimization | Buildings general |
| Trombe wall air space peak temp | 66 C (150 F) | Behind glazing |
| Absorptivity: dark-painted surface | 0.90-0.95 | Both domains |
| Absorptivity: whitewash/lime | 0.20-0.30 | Buildings |
| Absorptivity: adobe (natural) | 0.55-0.75 | Buildings |
| Absorptivity: dark reptile skin | 0.90-0.95 | Animals |
| Absorptivity: light desert mammal fur | 0.30-0.50 | Animals |
| Selective coating: alpha_solar / epsilon_IR | 0.95 / 0.10 | Trombe wall technology |
| Kleiber's law | BMR = 70 * M^0.75 kcal/day | Mammals |
| BMR: mouse (20g) | ~0.11 W | Endotherm |
| BMR: human (70 kg) | ~75-80 W | Endotherm |
| BMR: elephant (4000 kg) | ~1900 W | Endotherm |
| Human occupant heat output | ~100 W (75 sensible + 25 latent) | Building internal gain |
| Human BMR range (measured) | 1027-2499 kcal/day (mean ~1500) | Scottish population study |
| Energy from fat oxidation | 9.4 kcal/g (39.3 kJ/g) | Both domains (body fat / tallow) |
| Metabolic water from fat | 107 g H2O per 100 g fat | Animal physiology |
| RQ carbohydrates | 1.0 | Substrate utilization |
| RQ fats (palmitic acid) | 0.696 | Substrate utilization |
| RQ proteins (albumin) | 0.818 | Substrate utilization |
| Desert sand surface temperature | up to 57.7 C | Environmental heating source |
| Ground temperature at 2-3m depth | Approximately annual mean air temp | Both domains |
| Wood fuel energy content | ~4.5 kWh/kg | Building fuel |
| Dried dung fuel energy content | ~3.5 kWh/kg | Building fuel |
| Cow body heat output | ~400-500 W | Building internal gain (co-housed livestock) |
| Trombe wall energy savings | 16-30% of building heating demand | Literature range |

---

## 7. GAPS AND NOTES

### Evidence quality
- **Strong**: Trombe wall performance data (monitored buildings with multi-year data). BMR scaling laws (Kleiber's law extensively validated). Direct-gain efficiency figures (well-established).
- **Moderate**: Absorptivity values for animal surfaces (published in biophysical ecology literature but not in the Wikipedia sources reviewed; values above drawn from Gates 1980 and standard references). Fat oxidation metabolic water yield (standard biochemistry).
- **Weak/Inferred**: Specific W output for livestock in traditional buildings (engineering estimates, not from reviewed sources). Absorptivity values for specific building materials (standard solar engineering tables, not in Wikipedia sources).

### Missing from Wikipedia sources (needs separate research)
1. Quantitative shivering thermogenesis output (W or W/kg) for specific species
2. Non-shivering thermogenesis capacity in BAT (W/g tissue)
3. Specific absorptivity measurements for named animal species across solar spectrum
4. Solar heat gain coefficients for traditional building materials (adobe, rammed earth, thatch)
5. Postprandial thermogenesis as fraction of total metabolic heat in different species
6. Traditional building internal gains from cooking fires (measured, not estimated)

### Connection to project ontology
The tags proposed above extend the existing strategy tag vocabulary in `research-brief.md` (Section 6.6). Current ontology has:
- **Heating strategies**: metabolic, insulative, solar, massive, behavioral
- **Proposed additions for energy collection**: `solar_direct_gain`, `solar_indirect_gain`, `absorptive_surface`, `internal_heat_generation`, `emergency_heat_boost`, `dedicated_heat_subsystem`, `chemical_energy_reserve`, `sustained_fuel_input`, `ground_conductive_gain`, `convective_environmental_gain`, `communal_heat_pooling`

These are finer-grained sub-tags within the existing `solar` and `metabolic` categories, providing the mechanistic resolution needed for cross-domain mapping.
