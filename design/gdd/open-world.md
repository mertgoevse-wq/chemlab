# ChemLab: Origins — Open-World Systems GDD
**Document Version:** 1.0.0  
**Phase:** Phase B Open-World & Macro-Progression  
**Lead Discipline:** Open World & World Design  
**Target Engine:** Godot 4.7.2 (GDScript) / Headless Simulation Core  

---

## 1. Vision & Conceptual Open-World Architecture

### 1.1 High-Level Fantasy
In ChemLab: Origins, the open world is framed as an expansive, interconnected scientific ecosystem inspired by macro-progression models found in classic MMORPGs (World of Warcraft) and procedural exploration sandboxes (No Man's Sky). The player begins as an uncredentialed amateur working out of makeshift basement installations and progresses toward operating multi-million-credit industrial pilot plants, high-containment biosafety suites, and microgravity orbital laboratories.

### 1.2 Conceptual Structural Scope (No Locomotion Mechanics)
This document specifies regional topology, facility node networks, quest gating, environmental scaling, and procedural lab structures. In accordance with ChemLab core tenets:
- Character movement, first-person WASD locomotion, and physics-based player avatar controllers are explicitly out of scope for this architecture.
- The world exists as a discrete node graph of laboratories, transit hubs, research institutions, and field outposts.
- Interaction occurs within room-scale laboratory workstations, spatial apparatus benches, analytical dashboards, and regional map matrix interfaces.
- Inter-region and inter-facility transitions are modeled as conceptual fast-travel links, dispatch manifests, security scans, and environmental handoffs.

### 1.3 Regional Triad
The simulated universe is partitioned into three macro-regions, each representing distinct regulatory, hazard, and chemical paradigms:
1. **Safehaven City:** The metropolitan center of legal commerce, academia, strict safety oversight, and hidden urban criminal underworlds.
2. **The Badlands:** An unregulated, hostile industrial frontier of abandoned chemical facilities, covert synthesis bunkers, and extreme environmental biomes.
3. **Orbital Research Station (Aeterna Station Alpha):** An orbital microgravity complex dedicated to zero-g fluidics, vacuum crystallization, and rare allotrope synthesis.

```
       [ Orbital Research Station ]
                   ^
                   |  (Sub-Orbital Shuttle / G-Force Envelope)
                   v
       [ Safehaven City ] <========> [ The Badlands ]
      (Regulated Metro Hub)  (MagLev /   (Unregulated Frontier)
                             Convoy)
```

---

## 2. Open-World Macro-Regions

### 2.1 Safehaven City
Safehaven City represents the apex of institutional chemical infrastructure, strict regulatory enforcement, and formal academic inquiry, counterbalanced by a clandestine urban counter-economy.

#### 2.1.1 District Nodes
- **University Quarter (St. Jude Academic Campus):**
  - *Facilities:* Teaching Laboratories, Central Spectroscopy Core, Department of Synthetic Organic Chemistry.
  - *Key Apparatus:* 400 MHz FT-NMR Spectrometer, Schlenk line inert-gas argon manifolds, fume hood rows, analytical balances.
  - *Gameplay Focus:* Foundational safety training, OSHA compliance certification, standard organic total syntheses (aspirin, paracetamol, indigo), grant funding.
- **Pharma Industrial Park (Synthetica & Aeterna Compounds):**
  - *Facilities:* GMP Pilot Plants, automated batch crystallization units, quality assurance cleanrooms.
  - *Key Apparatus:* Preparative and analytical HPLC-DAD arrays, LC-MS triple quadrupoles, automated 50L jacketed reactors.
  - *Gameplay Focus:* High-throughput validation, purity standards exceeding 99.5%, official pharmacological contract fulfillment.
- **Municipal Government & Police Precinct:**
  - *Facilities:* Forensic Toxicology & Crime Scene Investigation (CSI) Central Laboratory, Evidence Impound Vault, Regulatory Licensing Bureau.
  - *Key Apparatus:* Handheld Raman spectrometers, GC-MS fingerprint analyzers, fingerprint fuming chambers, spectrophotometers.
  - *Gameplay Focus:* Analysis of seized street samples, toxicological autopsies, forensic arson residue detection, chain-of-custody logging.
- **The Underbelly (Canal Alleyways & Sub-Cellars):**
  - *Facilities:* Camouflaged basement laboratories, illicit reagent drop points, speakeasy precursor distribution hubs.
  - *Key Apparatus:* Makeshift heating mantles, modified glass assemblies, charcoal exhaust scrubbers.
  - *Gameplay Focus:* Covert precursor acquisition, bypassing regulatory watchlists, handling high-heat illicit syntheses.

#### 2.1.2 Ambient Regulatory Profile
- *Police Patrol Frequency:* High (hourly surveillance sweeps, utility consumption audits).
- *Precursor Gating:* Mandatory end-user declaration certificates for Schedule I/II chemicals (acetic anhydride, nitroethane, sulfuric acid, toluene).
- *Atmospheric Baseline:* Earth standard (1.00 atm, 1.00g, 22.0°C).

---

### 2.2 The Badlands
The Badlands encompass hundreds of square kilometers of decommissioned chemical manufacturing sites, salt flats, strip mines, and rugged canyons outside municipal jurisdiction.

#### 2.2.1 District Nodes
- **Rust Belt Industrial Ruins:**
  - *Facilities:* Decommissioned petrochemical cracking plants, collapsed fertilizer silos, rusted railheads.
  - *Key Apparatus:* Abandoned 200L steel autoclaves, large-bore condensers, salvageable scrap valves and manifolds.
  - *Gameplay Focus:* Scrap scavenging, large-scale crude distillation, bulk reagent staging away from prying eyes.
- **Subterra Bunker Network (Bunker-7 & Echo Outposts):**
  - *Facilities:* Reinforced fallout shelters converted into covert multi-room synthesis bunkers.
  - *Key Apparatus:* Improvised fume ducting, sand-bath heating mantles, liquid-liquid extraction separatory funnels, gas-washing scrubbers.
  - *Gameplay Focus:* High-yield contraband synthesis, synthetic chemistry without municipal inspection risk, thermal runaway mitigation in enclosed spaces.
- **Toxic Slag Runoff & Alkaline Flats:**
  - *Facilities:* Open-air waste collection vats, mineral precipitation basins.
  - *Key Apparatus:* Settling tanks, industrial Buchner filter presses, solar evaporation pans.
  - *Gameplay Focus:* Environmental remediation contracts, extracting inorganic salts and heavy metals from contaminated runoff.
- **Planetary Weather Outpost (Extreme Surface Station):**
  - *Facilities:* Hyperbaric or low-pressure test domes simulating off-world atmospheric conditions.
  - *Key Apparatus:* Controlled-atmosphere gloveboxes, pressure-seal doors, external sampling probes.
  - *Gameplay Focus:* High-stress chemical reactions, testing volatile syntheses under Martian or cryogenic atmospheric conditions.

#### 2.2.2 Ambient Regulatory Profile
- *Police Patrol Frequency:* None to sporadic aerial reconnaissance drones.
- *Hazard Profile:* Severe uncontained chemical spills, ambient toxic gas pockets, ungrounded electrical systems triggering volatile spark ignition.
- *Logistics Gating:* No municipal utility supply; requires player-managed diesel generator fuel and pressurized water canisters.

---

### 2.3 Orbital Research Station (Aeterna Station Alpha)
Positioned in low-Earth orbit, Aeterna Station Alpha is an international cooperative research installation dedicated to zero-gravity physical chemistry, crystallography, and hazardous high-energy kinetics.

#### 2.3.1 District Nodes
- **Zero-G Fluidics Module (Deck 01):**
  - *Facilities:* Pressurized laboratory bay with acoustic levitation and capillary flow benches.
  - *Key Apparatus:* Acoustic 3D levitators, capillary fluid transfer injectors, contactless ultrasonic mixers, high-speed shadowgraph cameras.
  - *Gameplay Focus:* Manipulating free-floating spherical liquid droplets, diffusion-limited reaction kinetics without gravitational buoyancy convection.
- **Microgravity Protein & Salt Crystallization Deck (Deck 02):**
  - *Facilities:* Thermal-gradient crystal growth chambers, automated X-ray diffraction (XRD) analyzers.
  - *Key Apparatus:* Hanging-drop vapor diffusion plates, Peltier cold-finger incubators, motorized polarization microscopes.
  - *Gameplay Focus:* Synthesis of macroscopic, defect-free single crystals (lead iodide, insulin, lysozyme, complex coordination polymers).
- **External Vacuum Observation Platform:**
  - *Facilities:* Depressurized airlock-accessible research platform facing open space.
  - *Key Apparatus:* Solar-concentrator reaction tubes, ultra-high-vacuum reaction cells, cryo-sublimation traps.
  - *Gameplay Focus:* Flash vacuum pyrolysis, Clausius-Clapeyron vacuum boiling investigations, radiation-induced photochemistry.

#### 2.3.2 Ambient Regulatory Profile
- *Station Authority:* Aeterna Orbital Flight Safety Administration.
- *Containment Protocol:* Extreme. Open-flame apparatus (Bunsen burners) strictly prohibited; all liquids must be enclosed in sealed syringes or capillary cells.
- *Environmental Constants:* 0.00g gravity, 1.00 atm internal atmospheric pressure (0.0001 atm on exterior platform), 21.0°C controlled temperature.

---

## 3. World Matrix Hub & Neighboring Labs

### 3.1 Hub Topology & Procedural Connectivity
The open world is structured around the `WorldMatrixHub`, a persistent graph-management system that anchors the player's personal base of operations while procedurally populating surrounding regional nodes.

```
       [Neighbor 01: Academic]  <----+
                                     |
       [Neighbor 02: Industrial] <---+--- [Player Hub Lab] ---> [Neighbor 04: Orbital Module]
                                     |
       [Neighbor 03: Underground]<---+
```

### 3.2 Radial Distance Tiers
Facilities are mapped in concentric distance rings around the hub:
1. **Tier 0 (Anchor Hub):** The player's home laboratory. Customized archetype, personal equipment inventory, secure reagent storage safe, master terminal.
2. **Tier 1 (Local Neighbors, 1–5 km):** 3 to 6 procedurally generated laboratories representing complementary archetypes. Guaranteed diversity ensures accessible trading and collaborative quests.
3. **Tier 2 (Regional Nodes, 10–50 km):** Major institutional centers (St. Jude University, Synthetica Central Plant, Police Forensics HQ). Fixed narrative hubs.
4. **Tier 3 (Frontier & Orbital Nodes):** Distant Badlands bunkers, planetary test sites, and orbital station modules accessible only via dedicated transit routes.

### 3.3 Dynamic Laboratory Registry
Every facility in the matrix exposes standard interface properties queried by the client:
- `lab_id`: Unique persistent GUID (e.g. `lab_4812_clan`).
- `name`: Procedurally assembled title or registered institutional designation.
- `lab_type`: Enumeration (`clandestine_underground`, `industrial_pharma`, `crispr_biotech`, `academic_research`, `orbital_zero_g`, `extreme_planetary`).
- `security_level`: Access authorization tier governing player entry and inspection frequency.
- `reagent_cache`: Real-time stock quantities of feedstocks, solvents, catalysts, and products.
- `npcs`: Array of resident scientists, technicians, fixers, and auditors.
- `quests`: Array of locally originated research contracts and covert synthesis bounties.

---

## 4. Procedural Laboratory Generation Pipeline

### 4.1 Archetype Generation Pipeline
Facilities are generated deterministically using a seeded pseudo-random number generator (`ProceduralLabGenerator`). For any given seed and archetype, the generator constructs:
1. Architectural Layout (Room count, containment grade, airlock configuration).
2. Environmental Physics Matrix (Gravity, pressure, temperature, hazard tolerance).
3. Equipment Catalog Manifest (Condition ratings, cleanliness indices, specialized features).
4. Reagent Inventory (Volume balances, purity tiers, storage compatibility).
5. Resident NPCs (Dialogue tables, faction alignments, trade inventories).
6. Local Quest Board (Objectives, purity thresholds, safety penalties, credit rewards).

### 4.2 Architectural Parameters by Archetype

| Archetype | Room Count | Security Level | Biosafety Level | Primary Ventilation |
|---|---|---|---|---|
| Academic Research | 3–7 | Campus Card Access | BSL-1 / BSL-2 | Ducted Fume Hoods (DIN EN 14175) |
| Industrial Pharma | 6–14 | High-Security GMP | BSL-1 | Industrial Scrubbers + Positive Pressure |
| CRISPR Biotech | 4–8 | Biosafety Containment | BSL-2 / BSL-3 | Class II Laminar Flow + HEPA H14 |
| Clandestine Underground | 1–3 | Improvised / Covert | BSL-1 | Passive Vent / Improvised Carbon Blower |
| Orbital Zero-G | 2–5 | Airlock Sealed Station | BSL-1 / BSL-2 | Closed-Loop Environmental Life Support |
| Extreme Planetary | 3–6 | Hyperbaric Airlock | BSL-2 / BSL-3 | Dual Airlock + Scrubber Gas Recycle |

### 4.3 Procedural Equipment Ingress Rules
The generator populates equipment based on functional requirements:
- Every lab must possess at least one primary thermal control unit (hotplate, heating mantle, incubator, or cryostat).
- Analytical equipment is selected based on regulatory requirements: Industrial Pharma always receives HPLC and LC-MS; Academic receives NMR or FTIR; Clandestine receives portable Raman, melting point apparatus, or improvised TLC setups.
- Equipment conditions range from 0.40 (worn, prone to temperature drift) in clandestine labs to 1.00 (factory calibrated) in pharmaceutical plants.

---

## 5. Region Presets & Thermodynamic Environmental Scaling

### 5.1 Physical Scaling Parameters
ChemLab simulates ambient thermodynamic conditions via `LaboratoryEnvironmentMatrix`. Every reaction calculated in the backend solver is evaluated under active environmental variables that dictate physical phase, reaction rate, and fluid behavior:

```
  Variable                    Earth Baseline       Mars Outpost         Orbital Station
  --------------------------------------------------------------------------------------
  Gravity (g)                 1.00 g               0.38 g               0.00 g
  Ambient Pressure (atm)      1.00 atm             0.006 atm (6 mbar)   1.00 atm / 0.0001 (vac)
  Ambient Temperature (°C)    22.0 °C              -63.0 °C             21.0 °C / -150.0 (vac)
  Pour Velocity Scale         1.0000               0.6164               0.0000
  Boiling Point of Water      100.0 °C             ~ 0.0 °C             100.0 °C / Sublimation
```

### 5.2 Clausius-Clapeyron Thermodynamic Engine
Under low pressure (Badlands vacuum chambers, Martian surface, or orbital platforms), solvent boiling points drop precipitously according to the integrated Clausius-Clapeyron equation:

$$\frac{1}{T_{boil}} = \frac{1}{T_0} - \frac{R}{\Delta H_{vap}} \ln\left(\frac{P_{ambient}}{P_0}\right)$$

- **Practical Gameplay Consequence:** In a Martian surface outpost (0.006 atm), water boils at approximately 0.0°C. Refluxing a reaction in ethanol (normal boiling point 78.4°C) boils at approximately -15.0°C unless conducted in a pressurized autoclave. Players must calculate and maintain vessel pressure before initiating heat.

### 5.3 Gravity-Driven Fluid Kinematics
Efflux rate and pouring speed scale hydrostatically via Torricelli's theorem:

$$v_{pour} \propto \sqrt{2 \cdot g \cdot \Delta h} \implies \text{Multiplier} = \sqrt{g}$$

- **At 1.00g (Earth):** Standard gravity-fed pouring from buret and beaker.
- **At 0.38g (Mars):** Slower meniscus drainage; pouring streams travel farther horizontally; drop detachment frequency is halved.
- **At 0.00g (Orbital):** Downward pouring velocity is zero ($v = 0$). Liquid forms spherical beads adhering to glass surfaces by surface tension. Transferring reagents requires positive-displacement pipettes, sealed syringes, or acoustic levitation fields.

### 5.4 Consequence Severity Modes
The open world applies environmental hazard difficulty settings:
1. **Creative Godmode:** Glassware cannot shatter; runaway exotherms generate warning notices but do not rupture flasks; infinite personal safety tolerance. Used in sandbox exploration.
2. **Standard Student:** Safety warnings trigger HUD alerts; OSHA demerit points accumulate; minor thermal runaways crack glassware and ruin product yield.
3. **Hardcore Realistic:** Unchecked exotherms violently rupture glass vessels; toxic vapors (NOx, Cl2, SO2) contaminate the facility; severe spills require hazmat decontamination drills; unneutralized spills permanently damage equipment condition.

---

## 6. Fast Travel & Region Transitions (Conceptual)

### 6.1 Conceptual Transit Architecture
Because ChemLab does not feature real-time vehicle driving or avatar traversal, travel between regional nodes is resolved through modal transit operations:

```
[Select Destination Node] 
       │
       ▼
[Transit Mode Evaluation] 
       ├── Transit Permit Check
       ├── Contraband Cargo Scan
       └── Hazard Certification Validation
       │
       ▼
[Environmental Re-synchronization]
       ├── Unload Origin Environment Matrix
       ├── Load Target Environment Matrix
       └── Apply Thermal / Pressure Equalization
       │
       ▼
[Arrive at Destination Laboratory Interface]
```

### 6.2 Transit Routes & Requirements

#### 6.2.1 Safehaven Metropolitan MagLev
- *Connects:* Safehaven University <-> Pharma Park <-> Municipal Precinct.
- *Cost:* 15 Credits.
- *Security Screening:* High. Automated X-ray backscatter and mass spectrometry vapor sniffer scans. Carrying unsealed Schedule I precursors or contraband chemicals triggers immediate confiscation and municipal heat.
- *Transit Time:* Instantaneous fade-in with audio cue (`sfx_subway_chime`).

#### 6.2.2 Badlands Armored HazMat Convoy
- *Connects:* Safehaven Underbelly Border Gate <-> Rust Belt Ruins <-> Subterra Bunker Network.
- *Cost:* 120 Credits or Syndicate Vouching.
- *Security Screening:* Zero. Contraband friendly.
- *Risk Factor:* 15% probability of ambient chemical spill during transit if glassware is poorly packed; requires secure shipping containers.

#### 6.2.3 Aeterna Sub-Orbital Shuttle Launch
- *Connects:* Safehaven Spaceport <-> Orbital Research Station Alpha.
- *Cost:* 1,500 Credits + Orbital Clearance Pass.
- *Requirements:* Zero-G Chemical Safety Certification (Level 40 Physical Chemistry skill).
- *Cargo Restrictions:* Volatile solvents with vapor pressure > 50 kPa prohibited in unpressurized cargo; flammable gas cylinders must be certified DOT-3AL spec.

---

## 7. Open-World Sandbox vs. Quest Gating

### 7.1 Sandbox Mode ("Unrestricted Simulation")
- Accessible directly from the main menu or upon reaching Grandmaster in any primary skill.
- All 100+ chemical reagents in the authoritative database are unlocked with infinite stock.
- Real-time sliders for gravity (0.00g to 3.00g), pressure (0.001 atm to 50.0 atm), temperature (-200°C to +500°C), and time acceleration (0.0x to 100.0x).
- No OSHA penalties, no financial costs, no reputation tracking.

### 7.2 Origins Campaign Mode ("Progression Engine")
The narrative campaign utilizes a classic mastery progression system across five core skill disciplines:
1. **Analytical Chemistry:** Titration accuracy, balance precision, NMR/HPLC spectrum interpretation, purity quantification.
2. **Organic Synthesis:** Multi-step reaction assembly, reflux monitoring, recrystallization, yield optimization.
3. **Biotechnology & Genetics:** Sterile technique, PCR thermal cycling, gel electrophoresis, plasmid transformation.
4. **Physical Chemistry & Kinetics:** Reaction rate calculation, thermodynamics, Clausius-Clapeyron compensation, oscillator tuning.
5. **Chemical Engineering & Safety:** Fume hood management, scrubber operation, scale-up reactor management, emergency spill neutralization.

#### 7.2.1 Leveling & Milestone Unlocks
Skills scale from Level 1 to 99 using standard logarithmic XP thresholds:
- Level 1: Novice (Basic glass handling, water solutions, safety goggles).
- Level 20: Apprentice (Acid-base titrations, standard recrystallization, Safehaven University lab access).
- Level 40: Chemist (Organic reflux, vacuum distillation, Badlands outpost access).
- Level 60: Senior Scientist (Schlenk line inert-gas synthesis, HPLC validation, Aeterna orbital shuttle clearance).
- Level 80: Master Alchemist (Multi-step total syntheses, CRISPR gene-editing, automated 50L pilot reactors).
- Level 99: Grandmaster (Zero-G enantiomer separation, complex oscillating reaction stabilization, global patent holder).

### 7.3 Quest Gating Hierarchy
Quests act as gatekeepers for world access:
- **Campaign Quest 1 (Orientation & Safety Protocols):** Mandatory completion before leaving the starting workbench. Validates PPE donning, analytical balance taring, HCl dispensing, phenolphthalein addition, and NaOH titration.
- **Academic Accreditation Exams:** Required to requisition controlled reagents (nitric acid, lithium aluminum hydride) from university supply.
- **Syndicate Initiation Quests:** Required to unlock covert underground facilities and black market fixer inventories.

---

## 8. Reputation & Regional NPC Trading

### 8.1 Regional Factions
Player standing is tracked across four distinct political and economic factions:
1. **The Regulatory Board & OSHA:** Oversees municipal safety, laboratory licensing, and workplace hazard inspections. Rewards compliance and safe disposal.
2. **The Academic Guild (Universities & Research Councils):** Controls grant allocations, instrument time on NMR/LC-MS cores, and peer-reviewed publication bounties.
3. **The Underworld Syndicate:** Operates clandestine synthesis networks, smuggles regulated precursors, and issues high-paying contraband contracts.
4. **The Orbital Research Consortium:** Manages spaceflight manifests, patent licensing for space-grown crystals, and microgravity research subsidies.

### 8.2 Reputation Tiers & Dialogue States
Every NPC evaluates the player through a 5-tier reputation ladder:

```
  Tier Name       Reputation Range     Trading Perks & Dialogue Behaviors
  --------------------------------------------------------------------------------------
  Hostile         0.0 – 19.9           Refuses trade; reports player to authorities; hostile dialogue.
  Suspicious      20.0 – 39.9          Trade surcharge (+35%); requires upfront cash; guarded dialogue.
  Neutral         40.0 – 59.9          Standard catalog prices; standard professional dialogue.
  Friendly        60.0 – 79.9          Trade discount (-15%); offers specialty precursor batches.
  Trusted         80.0 – 100.0         Unrestricted access to restricted stores; offers VIP quest chains.
```

### 8.3 NPC Trading & Economic Mechanics
- **Stock Depletion & Replenishment:** NPC inventories diminish when the player purchases materials and restock on a 24-hour in-game cycle.
- **Purity Price Scaling:** Reagent sell prices scale quadratically with tested analytical purity:
  
$$\text{Payout} = \text{Base Price} \cdot \left(\frac{\text{Purity \%}}{100}\right)^2 \cdot \left(\frac{\text{Yield } g}{\text{Target } g}\right)$$

- Purity under 80% incurs severe buyer penalties or outright rejection for pharmaceutical contracts.

---

## 9. Data-Driven Configuration Specifications

All regional topologies, environmental presets, and transit parameters are defined in machine-readable JSON format to facilitate continuous balancing and headless test validation.

### 9.1 Open-World Region Configuration (`open_world_regions.json`)

```json
{
  "$schema": "https://chemlab.sim/schemas/regions.json",
  "version": "1.0.0",
  "regions": [
    {
      "region_id": "safehaven_city",
      "display_name": "Safehaven City",
      "regulatory_authority": "Safehaven Municipal Council & OSHA Board",
      "police_presence_index": 0.85,
      "base_environment": {
        "gravity_g": 1.0,
        "ambient_pressure_atm": 1.0,
        "ambient_temperature_c": 22.0,
        "hazard_difficulty": "standard_student"
      },
      "sub_districts": [
        {
          "district_id": "sh_university_quarter",
          "name": "St. Jude University Campus",
          "archetypes_present": ["academic_research", "analytical_spectroscopy"],
          "default_security_level": "campus_card_access"
        },
        {
          "district_id": "sh_pharma_park",
          "name": "Synthetica Industrial Zone",
          "archetypes_present": ["industrial_pharma"],
          "default_security_level": "high_security_gmp"
        },
        {
          "district_id": "sh_municipal_precinct",
          "name": "Central Police & Forensics Division",
          "archetypes_present": ["forensic_investigation"],
          "default_security_level": "police_secure_clearance"
        },
        {
          "district_id": "sh_underbelly",
          "name": "Canal Sub-Cellars",
          "archetypes_present": ["clandestine_underground", "clandestine_improvised"],
          "default_security_level": "clandestine_covert"
        }
      ]
    },
    {
      "region_id": "the_badlands",
      "display_name": "The Badlands Frontier",
      "regulatory_authority": "Unregulated Outlaw Territory",
      "police_presence_index": 0.05,
      "base_environment": {
        "gravity_g": 1.0,
        "ambient_pressure_atm": 0.98,
        "ambient_temperature_c": 34.0,
        "hazard_difficulty": "hardcore_realistic"
      },
      "sub_districts": [
        {
          "district_id": "bl_rust_belt",
          "name": "Petrochemical Ruins 09",
          "archetypes_present": ["industrial_pilot_plant", "clandestine_improvised"],
          "default_security_level": "abandoned_perimeter"
        },
        {
          "district_id": "bl_subterra_bunkers",
          "name": "Bunker Complex Sector-7",
          "archetypes_present": ["clandestine_underground"],
          "default_security_level": "reinforced_bunker"
        },
        {
          "district_id": "bl_planetary_dome",
          "name": "Elysium Extreme Planetary Dome",
          "archetypes_present": ["extreme_planetary"],
          "default_security_level": "hyperbaric_airlock"
        }
      ]
    },
    {
      "region_id": "orbital_station_aeterna",
      "display_name": "Aeterna Orbital Research Complex",
      "regulatory_authority": "Aeterna Aerospace Consortium",
      "police_presence_index": 0.95,
      "base_environment": {
        "gravity_g": 0.0,
        "ambient_pressure_atm": 1.0,
        "ambient_temperature_c": 21.0,
        "hazard_difficulty": "hardcore_realistic"
      },
      "sub_districts": [
        {
          "district_id": "orb_fluidics_deck",
          "name": "Microgravity Capillary Bay",
          "archetypes_present": ["orbital_zero_g"],
          "default_security_level": "airlock_sealed_station"
        },
        {
          "district_id": "orb_vacuum_platform",
          "name": "External Vacuum Exposure Rig",
          "archetypes_present": ["orbital_zero_g", "extreme_planetary"],
          "default_security_level": "extravehicular_airlock"
        }
      ]
    }
  ]
}
```

### 9.2 Fast Travel Network Specification (`transit_network.json`)

```json
{
  "$schema": "https://chemlab.sim/schemas/transit.json",
  "version": "1.0.0",
  "routes": [
    {
      "route_id": "maglev_metro_line",
      "name": "Safehaven Metro MagLev",
      "origin_region": "safehaven_city",
      "destination_region": "safehaven_city",
      "cost_credits": 15.0,
      "contraband_scan_rigor": 0.90,
      "allowed_hazard_classes": ["Class_1", "Class_2"],
      "transit_audio_event": "sfx_metro_pass"
    },
    {
      "route_id": "badlands_hazmat_convoy",
      "name": "Armored Overland Tanker Convoy",
      "origin_region": "safehaven_city",
      "destination_region": "the_badlands",
      "cost_credits": 120.0,
      "contraband_scan_rigor": 0.0,
      "allowed_hazard_classes": ["Class_1", "Class_2", "Class_3", "Class_4", "Explosive"],
      "cargo_damage_probability": 0.12,
      "transit_audio_event": "sfx_diesel_rumble"
    },
    {
      "route_id": "orbital_shuttle_launch",
      "name": "Aeterna Orbital Transfer Craft",
      "origin_region": "safehaven_city",
      "destination_region": "orbital_station_aeterna",
      "cost_credits": 1500.0,
      "contraband_scan_rigor": 0.99,
      "required_skill_discipline": "physical_chemistry",
      "required_skill_level": 40,
      "max_liquid_cargo_volume_ml": 2500.0,
      "transit_audio_event": "sfx_rocket_launch"
    }
  ]
}
```
