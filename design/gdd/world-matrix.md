# ChemLab: Origins — World Matrix Hub & Procedural Systems Specification
**Document Version:** 1.0.0  
**Phase:** Phase B World Matrix Architecture & Persistence  
**Lead Discipline:** Open World & World Design  
**Target Engine:** Godot 4.7.2 (GDScript) / Python Headless Simulation Core  

---

## 1. Hub Architecture & World Graph Specification

### 1.1 Mathematical Graph Formulation
The ChemLab open world is modeled mathematically as a directed, weighted, attributed multigraph:

$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{W})$$

Where:
- $\mathcal{V}$ is the set of all laboratory facilities, regional hubs, outposts, and transit waypoints (Vertices).
- $\mathcal{E}$ is the set of transit links, supply corridors, and shipping lanes connecting facilities (Edges).
- $\mathcal{W}: \mathcal{E} \to \mathbb{R}^k$ assigns multi-dimensional weights to each edge:
  - $w_{cost}$: Financial fare in credits.
  - $w_{time}$: In-game traversal latency in minutes.
  - $w_{risk}$: Environmental hazard or cargo damage probability ($0.00$ to $1.00$).
  - $w_{scan}$: Contraband scanning and customs inspection rigor ($0.00$ to $1.00$).

```
                      [Academic Core: St. Jude]
                           ▲             │
               MagLev Link │             │ Chemical Waste Courier
             (w_scan=0.90) │             │ (w_risk=0.10)
                           ▼             ▼
  [Player Hub Lab] <===============> [Underground Bunker: Sector 7]
  (Anchor Facility)   Supply Route       ▲
                           ▲             │ HazMat Convoy
              Orbital Gate │             │ (w_scan=0.00)
             (w_cost=1500) │             ▼
                           ▼       [Rust Belt Industrial Ruin]
                      [Aeterna Station Alpha]
```

### 1.2 Facility Node States & Lifecycle
Every laboratory node $v \in \mathcal{V}$ transitions through a deterministic state machine:

```
  [ UNEXPLORED ] ──(Radar Ping / Story Trigger)──> [ DISCOVERED ]
                                                         │
                                               (Enter Facility / Transmit)
                                                         │
                                                         ▼
  [ RAIDED / QUARANTINED ] <──(Heat Exceeded)─── [ ACTIVE ]
            │                                            │
   (Cooldown / Fine)                             (Reagents Depleted)
            │                                            │
            ▼                                            ▼
  [ REACTIVATED ]                             [ DORMANT / ABANDONED ]
```

- **Unexplored:** Node exists in procedural seed database but is hidden from the player's world map terminal.
- **Discovered:** Coordinates and archetype are visible; transit routes are mapped; basic public communications open.
- **Active:** Full access to laboratory workstations, local NPC dialogues, trade inventories, and quest boards.
- **Raided / Quarantined:** Locked down by municipal police or OSHA regulators; access barred for 48–72 in-game hours unless player executes counter-forensic infiltration.
- **Dormant / Abandoned:** Power or reagent supply exhausted; functions as a salvage site for scrap glassware.

---

## 2. Player Starting Lab Customization & Hub Initialization

### 2.1 Initialization Lifecycle (`WorldMatrixHub`)
When a new game or simulation session begins, the `WorldMatrixHub` is instantiated with the player's profile:

```python
hub = WorldMatrixHub(player_name="Alchemist_One")
```

At initialization:
1. `player_lab` is initially `None`.
2. `discovered_labs` dictionary is empty (`len == 0`).
3. The deterministic procedural generator (`ProceduralLabGenerator`) is initialized with the master universe seed.
4. The player selects a starting archetype via `setup_player_starting_lab()`.

### 2.2 Starting Archetype Selection Matrix
Players choose their origin path, configuring initial equipment condition, starting reagents, financial balances, and faction standing:

```
  Starting Archetype            Initial Name Preset     Key Apparatus               Starting Credits    Initial Reputation
  -------------------------------------------------------------------------------------------------------------------------
  Clandestine Underground       "Bunker-7"              Improvised Fume Vent,       250 Credits         Underworld: 35.0
                                                        Liebig Condenser Set                            OSHA / Police: 5.0
  Academic Research             "Campus Lab-4B"         EN 14175 Fume Hood,         500 Credits         Academic Guild: 50.0
                                                        Schlenk Inert Gas Line                          Underworld: 10.0
  Industrial Pharma             "Synthetica Unit 10"    Analytical HPLC-DAD,        1,200 Credits       Pharma Guild: 60.0
                                                        Jacketed 50L Reactor                            OSHA: 70.0
  CRISPR Biotech                "Cas9 GeneCore"         Mastercycler PCR,           800 Credits         Biotech Guild: 55.0
                                                        Laminar Flow Cabinet                            Academic: 45.0
  Orbital Zero-G                "Orbital Pod Alpha"     Acoustic Levitator,         2,000 Credits       Orbital Consortium: 65.0
                                                        Capillary Transfer Unit                         Earth Regulators: 40.0
```

### 2.3 Starting Anchor Registration
Upon selection, `setup_player_starting_lab()`:
- Deterministically generates the facility using `ProceduralLabGenerator.generate_lab()`.
- Assigns the generated facility as `hub.player_lab`.
- Adds the facility GUID into `hub.discovered_labs[lab.lab_id]`.
- Establishes the player's laboratory as the coordinate origin $(0, 0, 0)$ of the regional matrix graph.

---

## 3. Neighboring-Lab Generation & Procedural Spawning

### 3.1 Procedural Expansion Engine
Surrounding facilities are populated via `WorldMatrixHub.discover_nearby_labs(count)`. To ensure a rich sandbox experience, the engine enforces strict diversity guarantees.

### 3.2 Archetype Diversity Guarantee
When generating $N$ neighboring facilities:
- The generator iterates across the available `LabType` enumeration:
  - `CLANDESTINE_UNDERGROUND`
  - `INDUSTRIAL_PHARMA`
  - `CRISPR_BIOTECH`
  - `ACADEMIC_RESEARCH`
  - `ORBITAL_ZERO_G`
  - `EXTREME_PLANETARY`
- For a standard batch of $count = 5$, the generator ensures that at least 3 distinct laboratory archetypes are present within the immediate cluster (`len(types_present) >= 3`), preventing localized monocultures.

```python
def discover_nearby_labs(self, count: int = 4) -> list[ProceduralLab]:
    all_types = list(LabType)
    new_labs: list[ProceduralLab] = []
    for i in range(count):
        chosen_type = all_types[i % len(all_types)]
        lab = self.generator.generate_lab(chosen_type)
        self.discovered_labs[lab.lab_id] = lab
        new_labs.append(lab)
    return new_labs
```

### 3.3 Spatial Coordinate Assignment
To render the regional map terminal in Godot UI, each discovered node is assigned a procedural 3D spatial coordinate $(X, Y, Z)$ using Fibonacci lattice distribution:

$$r_i = R_{min} + (R_{max} - R_{min}) \cdot \sqrt{\frac{i + 0.5}{N}}$$

$$\theta_i = i \cdot 2.399963 \text{ rad (Golden Angle)}$$

$$X_i = r_i \cos(\theta_i), \quad Y_i = r_i \sin(\theta_i), \quad Z_i = \text{LayerHeight}(\text{Archetype})$$

- Ground facilities (Academic, Industrial, Clandestine) map to $Z = 0.0$ to $50.0$.
- Deep Underground bunkers map to $Z = -150.0$ to $-50.0$.
- Orbital facilities map to $Z = 1000.0$ to $1200.0$.

### 3.4 Economic Reagent Pairing
The generator pairs neighboring facilities with complementary supply and demand vectors:
- **Upstream Producer Node:** Synthesizes bulk precursors (e.g., Toluene oxidation to Benzaldehyde).
- **Downstream Consumer Node:** Issues quests requesting the synthesized precursor for secondary syntheses (e.g., Benzaldehyde condensation to Indigo or Schiff bases).

---

## 4. Seed Reproducibility & Deterministic Universe State

### 4.1 Seed Architecture
Deterministic world generation guarantees that entering an identical seed produces an identical open-world state across platforms and headless test environments.

```
                    [ 64-bit Master Seed: 1337 ]
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
   [ Stream 0: Lab ]      [ Stream 1: NPCs ]      [ Stream 2: Quests ]
   ├── Name Prefix        ├── Names               ├── Objective Type
   ├── Room Count         ├── Roles               ├── Target Compound
   ├── Security Level     ├── Dialogue Lines      ├── Min Purity %
   └── Equipment Specs    └── Trade Stocks        └── Min Yield Grams
```

### 4.2 Seed Invariance Verification
As verified in `test_procedural_lab_generator_seed_reproducibility`:
```python
gen1 = ProceduralLabGenerator(seed=42)
gen2 = ProceduralLabGenerator(seed=42)

lab1 = gen1.generate_lab(LabType.CLANDESTINE_UNDERGROUND)
lab2 = gen2.generate_lab(LabType.CLANDESTINE_UNDERGROUND)

assert lab1.name == lab2.name
assert lab1.room_count == lab2.room_count
assert len(lab1.equipment) == len(lab2.equipment)
assert len(lab1.npcs) == len(lab2.npcs)
assert len(lab1.quests) == len(lab2.quests)
```
Every attribute—from equipment condition to resident NPC dialogue arrays—is fully reproducible.

---

## 5. Global Quest Aggregation & Quest Log Persistence

### 5.1 Dynamic World Quest Aggregation
The player does not need to visit every facility manually to review active research contracts. The `WorldMatrixHub` acts as a central communication terminal aggregating all pending contracts:

```python
def get_available_world_quests(self) -> list[LabQuest]:
    quests: list[LabQuest] = []
    for lab in self.discovered_labs.values():
        quests.extend([q for q in lab.quests if not q.completed])
    return quests
```

### 5.2 Quest Lifecycle State
Each quest advances through a formal state pipeline:
1. **Available:** Listed on regional hub terminals.
2. **Accepted:** Bound to player's active objective tracker HUD (`quest_overlay.tscn`).
3. **Evaluating:** Player submits completed reaction vessel to analytical inspection bench.
4. **Completed:** Validated against purity, yield, safety, and temperature constraints; rewards granted; marked `completed = True`.
5. **Failed:** Product rejected due to off-spec purity, insufficient mass, or safety breach; reputation penalty applied.

### 5.3 Persistence Architecture (`SaveManager`)
The world matrix state is serialized to JSON (`user://chemlab_save.json`) conforming to the schema verified in `tests/test_gameplay_systems.py`:

```json
{
  "save_version": "1.0.0",
  "player_profile": {
    "name": "Alchemist_One",
    "credits": 2450.0,
    "skills": {
      "analytical_chemistry": {"level": 24, "xp": 18500},
      "organic_synthesis": {"level": 32, "xp": 41200},
      "biotechnology": {"level": 12, "xp": 4200},
      "physical_chemistry": {"level": 18, "xp": 10500},
      "chemical_engineering": {"level": 28, "xp": 29800}
    },
    "reputation_matrix": {
      "academic_guild": 62.5,
      "regulatory_osha": 48.0,
      "underworld_syndicate": 74.0,
      "orbital_consortium": 50.0
    }
  },
  "world_matrix": {
    "master_seed": 1337,
    "player_anchor_lab_id": "lab_5120_clan",
    "discovered_lab_ids": [
      "lab_5120_clan",
      "lab_8814_indu",
      "lab_2301_cris",
      "lab_9104_acad",
      "lab_4412_orbi"
    ],
    "active_quest_ids": ["q_cov_712", "q_gmp_304"],
    "completed_quest_ids": ["quest_orientation_safety_01", "q_acad_119"],
    "osha_demerit_points": 0,
    "laboratory_overrides": {
      "lab_5120_clan": {
        "equipment_condition": {
          "eq_fume_imp": 0.65,
          "eq_flask_set": 0.80
        },
        "reagent_stock": {
          "toluene": 1200.0,
          "benzaldehyde": 350.0
        }
      }
    }
  }
}
```

---

## 6. Dynamic World Simulation & Background State Changes

### 6.1 World Tick Engine
The simulation runs background state updates whenever the player completes a synthesis, uses fast travel, or rests:
- **Reagent Restocking:** NPC inventories replenish depleted stock at a rate of 10% per in-game day.
- **Equipment Wear:** Repeated use degrades heating elements and vacuums; unattended scrubbers clog.
- **Police Heat Dissipation:** Inactive clandestine labs cool off by 5.0 heat points per 24 hours.
- **Market Scarcity Shifts:** Sourcing large volumes of acetic anhydride or nitric acid triggers temporary regional price spikes (+15% to +40%) due to supply-chain constraints.

---

## 7. Environmental Matrix Synchronization

### 7.1 Environmental Parameter Inheritance
When the player transitions to any facility in the world matrix, the global simulation bridge (`simulation_bridge.gd`) synchronizes with the facility's `LaboratoryEnvironmentMatrix`:

```
               [ WorldMatrixHub Node ]
                         │
        (Extract LaboratoryEnvironmentMatrix)
                         │
                         ▼
        ┌─────────────────────────────────┐
        │ Gravity:               gravity_g│
        │ Pressure:   ambient_pressure_atm│
        │ Temperature:ambient_temp_c      │
        │ Time Warp:             time_warp│
        │ Hazard Mode:   hazard_difficulty│
        └────────────────┬────────────────┘
                         │
                         ▼
           [ Global Simulation Engine ]
       ├── Clausius-Clapeyron Boiling Points
       ├── Torricelli Fluid Pour Multiplier
       └── Glass Rupture / Toxic Gas Evaluator
```

### 7.2 Clausius-Clapeyron Formula Execution
Under low-pressure planetary or vacuum station nodes, the boiling point of pure water and solvents shifts in real time:

$$T_{boil} = \left[ \frac{1}{T_0} - \frac{R}{\Delta H_{vap}} \ln\left( \frac{P_{ambient}}{P_0} \right) \right]^{-1}$$

- For pure water ($T_0 = 373.15\text{ K}$, $\Delta H_{vap} = 40,660\text{ J/mol}$, $R = 8.314\text{ J/(mol}\cdot\text{K)}$):
  - At $1.00\text{ atm}$: $T_{boil} = 100.0^\circ\text{C}$.
  - At $0.10\text{ atm}$ (High altitude/Vacuum chamber): $T_{boil} \approx 45.8^\circ\text{C}$.
  - At $0.006\text{ atm}$ (Martian surface): $T_{boil} \approx 0.0^\circ\text{C}$ (liquid water flash-boils unless pressurized).

### 7.3 Efflux Pour Scaling Execution
Pouring speed calculated across Godot pouring animations and shader liquid surface levels scales directly with local gravity:

$$v_{multiplier} = \begin{cases} 0.0 & \text{if } g \le 0.0 \\ \sqrt{g} & \text{if } g > 0.0 \end{cases}$$

- In an Orbital Zero-G lab ($g = 0.0$), tilting a beaker produces zero downward pour stream. Reagent transfers require positive-displacement syringes or capillary transfer units.

---

## 8. Complete Data-Driven JSON Configuration Schemas

### 8.1 World Matrix Hub Schema (`world_matrix_hub_schema.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WorldMatrixHubConfig",
  "type": "object",
  "required": ["version", "default_master_seed", "archetype_registry", "transit_rules"],
  "properties": {
    "version": {"type": "string"},
    "default_master_seed": {"type": "integer"},
    "archetype_registry": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type_id", "display_name", "base_room_count_range", "base_security_tier"],
        "properties": {
          "type_id": {"type": "string"},
          "display_name": {"type": "string"},
          "base_room_count_range": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2
          },
          "base_security_tier": {"type": "string"},
          "gmp_certified": {"type": "boolean"},
          "biosafety_level": {"type": "integer", "minimum": 1, "maximum": 4}
        }
      }
    },
    "transit_rules": {
      "type": "object",
      "required": ["base_fare_per_km", "interplanetary_multiplier"],
      "properties": {
        "base_fare_per_km": {"type": "number"},
        "interplanetary_multiplier": {"type": "number"}
      }
    }
  }
}
```

### 8.2 Procedural Lab Templates (`procedural_lab_templates.json`)

```json
{
  "$schema": "https://chemlab.sim/schemas/lab_templates.json",
  "version": "1.0.0",
  "templates": [
    {
      "lab_type": "clandestine_underground",
      "name_prefixes": ["Bunker-", "Keller-Sektor ", "Subterra-", "Verlassene Werkstatt "],
      "room_count_bounds": [1, 3],
      "security_levels": ["clandestine_covert", "improvised", "reinforced_bunker"],
      "gmp_certified": false,
      "biosafety_level": 1,
      "environment_preset": "earth_hardcore",
      "mandatory_equipment_tags": ["suction_exhaust", "distillation", "magnetic_stir"],
      "starter_reagents": {
        "toluene": 1500.0,
        "benzaldehyde": 400.0,
        "nitroethane": 250.0,
        "acetic_acid": 800.0,
        "h2so4": 300.0
      }
    },
    {
      "lab_type": "industrial_pharma",
      "name_prefixes": ["Synthetica GMP-Werk ", "Aeterna Pharmazeutik ", "BioPharma Batch-Unit ", "Helix Pharma "],
      "room_count_bounds": [6, 14],
      "security_levels": ["high_security_gmp"],
      "gmp_certified": true,
      "biosafety_level": 1,
      "environment_preset": "earth_standard",
      "mandatory_equipment_tags": ["purity_analysis", "jacket_cooling", "molecular_weight"],
      "starter_reagents": {
        "salicylic_acid": 5000.0,
        "acetic_anhydride": 5000.0,
        "aminophenol": 3500.0,
        "ethanol": 10000.0,
        "water": 50000.0
      }
    },
    {
      "lab_type": "orbital_zero_g",
      "name_prefixes": ["Orbital-Labor Alpha-", "Zero-G Fluid-Modul ", "Mir-Station Experiment-Deck ", "ISS-Kompensationsmodul "],
      "room_count_bounds": [2, 5],
      "security_levels": ["airlock_sealed_station"],
      "gmp_certified": false,
      "biosafety_level": 2,
      "environment_preset": "orbital_zero_g",
      "mandatory_equipment_tags": ["contactless_mixing", "zero_g_pour"],
      "starter_reagents": {
        "water": 5000.0,
        "lead_nitrate": 500.0,
        "potassium_iodide": 500.0,
        "ethanol": 2000.0
      }
    }
  ]
}
```

### 8.3 Quest Objective & Evaluation Rules (`quest_generation_rules.json`)

```json
{
  "$schema": "https://chemlab.sim/schemas/quest_rules.json",
  "version": "1.0.0",
  "rules": [
    {
      "category": "covert_synthesis",
      "allowed_target_compounds": ["benzaldehyde", "nitroethane", "phenylacetone"],
      "min_purity_percent_range": [80.0, 90.0],
      "min_yield_grams_range": [10.0, 30.0],
      "requires_fume_hood_probability": 0.85,
      "base_reward_credits": 450.0,
      "base_reward_reputation": 15.0
    },
    {
      "category": "gmp_validation",
      "allowed_target_compounds": ["aspirin", "paracetamol", "acetanilide"],
      "min_purity_percent_range": [95.0, 99.5],
      "min_yield_grams_range": [25.0, 100.0],
      "requires_fume_hood_probability": 1.0,
      "enforce_max_temperature_c": 85.0,
      "base_reward_credits": 1200.0,
      "base_reward_reputation": 25.0
    },
    {
      "category": "zero_g_physics",
      "allowed_target_compounds": ["lead_iodide", "copper_sulfate_crystal", "protein_crystal"],
      "min_purity_percent_range": [92.0, 98.0],
      "min_yield_grams_range": [2.0, 10.0],
      "requires_fume_hood_probability": 0.0,
      "base_reward_credits": 800.0,
      "base_reward_reputation": 20.0
    }
  ]
}
```
