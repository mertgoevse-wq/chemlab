# ChemLab: Origins — Sandbox Mode Specification

**Version:** 1.0  
**Status:** Pre-Production (Phase B Specification)  
**Author:** Skills & Quests Design Lead  
**Source of Truth (Data-Driven Layer):** `design/gdd/data/sandbox_config.json`  
**Core Implementation References:**
- `src/chemlab/story/story_manager.py` (`unlock_all_for_sandbox`)
- `src/chemlab/sandbox/no_mans_sky_matrix.py` (`LaboratoryEnvironmentMatrix`, `PlanetaryPreset`, `HazardDifficulty`)
- `src/simulation/free_sim_engine.py` (`FreeSimulationEngine`)
- `src/simulation/experiment_book.py` (`ExperimentBook`, `Recipe`, `ReagentAddition`)
- `src/simulation/time_controller.py` (`TimeController`, `TimeScale`)
- `src/simulation/catalog.py` (`ReagentCatalog`, 100+ reagents with GHS classifications)
- `tests/test_free_sim.py`, `tests/test_no_mans_sky_sandbox.py`, `tests/test_storage_schemas.py`

---

## 1. Executive Summary & Mode Philosophy

Sandbox Mode (also referred to as **Free Simulation Mode** or **The Unlimited Lab**) removes all pedagogical rails, campaign objective gates, and reagent access restrictions. It transforms ChemLab into an unrestricted scientific playground and creative laboratory toolkit.

In Sandbox Mode, players can freely mix any of the 100+ verified chemical reagents, build custom modular apparatus rigs, manipulate fundamental thermodynamic and planetary variables (gravity, ambient pressure, temperature), warp simulation time up to 100×, record bespoke synthesis protocols, and export validated recipes as shareable JSON artifacts.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SANDBOX MODE ARCHITECTURE                       │
├──────────────────┬─────────────────┬──────────────────┬────────────────┤
│ 1. Unlocked      │ 2. Environmental│ 3. Consequence   │ 4. Protocol    │
│    Chemistry     │    Matrix       │    Engines       │    Studio      │
├──────────────────┼─────────────────┼──────────────────┼────────────────┤
│ • 100+ Reagents  │ • Gravity: 0-3g │ • Exotherm/Endo  │ • Experiment   │
│ • All Glassware  │ • Pressure:     │ • Precipitates   │   Book         │
│ • All Analytics  │   0.001-50 atm  │ • Gas Evolution  │ • Recipe JSON  │
│   (NMR/GC/HPLC)  │ • Temp:         │ • Runaway & Pops │   Export/Import│
│ • No Quest Gates │   -200 to +500°C│ • Oscillators    │ • In-Game Photo│
│ • Level Bypass   │ • Time Warp     │ • Containment    │   Snapshots    │
└──────────────────┴─────────────────┴──────────────────┴────────────────┘
```

---

## 2. Unlocked Chemistry & Zero-Gate Access

### 2.1 Complete Reagent Catalog Access
Sandbox Mode bypasses the milestone unlock tables defined in `skill_types.py` and `skills.json`. All chemical species across every classification are unlocked simultaneously with infinite bench stock:

- **Acids & Bases:** Concentrated $\text{HCl}, \text{H}_2\text{SO}_4, \text{HNO}_3, \text{CH}_3\text{COOH}, \text{HF}$, solid $\text{NaOH}, \text{KOH}, \text{Ca(OH)}_2, \text{NaHCO}_3, \text{Na}_2\text{CO}_3$.
- **Organic Solvents:** Ethanol, Methanol, Acetone, Diethyl Ether, Dichloromethane (DCM), Tetrahydrofuran (THF), Dimethyl Sulfoxide (DMSO), Toluene, Benzene, Acetonitrile.
- **Precursor Library (LambdaSyn / PiHKAL / TiHKAL):** Salicylic acid, acetic anhydride, 4-aminophenol, benzaldehyde, nitroethane, indole, phenylhydrazine, methylamine, ethyl cyanoacetate.
- **Oxidizers & Catalysts:** $\text{KMnO}_4, \text{K}_2\text{Cr}_2\text{O}_7, \text{H}_2\text{O}_2\ (30\%\text{ and }50\%), \text{KIO}_3, \text{MnO}_2, \text{FeCl}_3$, palladium on carbon ($\text{Pd/C}$), Raney nickel.
- **Transition Metal Salts:** $\text{CuSO}_4, \text{CoCl}_2, \text{NiSO}_4, \text{FeSO}_4, \text{AgNO}_3, \text{Pb(NO}_3)_2, \text{KI}$.
- **Indicators & Biochemical Agents:** Phenolphthalein, Bromothymol Blue, Universal Indicator, Starch, Methyl Orange, Ferroin, Luminol, Taq Polymerase, DNA Ladders, Cas9 Protein.

### 2.2 Unlocked Apparatus & Analytical Instruments
Every piece of hardware is immediately selectable from the spatial workbench inventory without currency costs or clearance prerequisites:

1. **Synthetic Glassware:** Standard ground-joint ($24/40$) round-bottom flasks (50 mL to 5000 mL), Claisen adapters, Dean-Stark traps, Vigreux fractional columns, Dimroth condensers, addition funnels, sublimation cold fingers.
2. **Thermal & Separation Rigging:** Jacketed reaction vessels, magnetic hotplate stirrers with PID controllers, heating mantles, cryogenic dewars, rotary evaporators, Büchner vacuum filter presses, centrifuges.
3. **Advanced Metrology & Spectroscopy:** 4-decimal analytical microbalances, Hot-wire anemometers, UV-Vis spectrophotometers, HPLC-DAD automated stacks, GC-MS quadrupoles, and 400 MHz FT-NMR spectrometers.
4. **Extreme Containment:** Class II Biosafety cabinets, double-manifold Schlenk lines, argon atmosphere gloveboxes, and high-pressure Parr hydrogenation bombs.

### 2.3 Instant Sandbox Activation Mechanism
As implemented in `StoryProgressionManager.unlock_all_for_sandbox()`, entering Sandbox Mode sets all campaign levels to `COMPLETED`, elevates the player rank to `PlayerRank.MASTER_ALCHEMIST`, and populates the feedback status:
```python
mgr.unlock_all_for_sandbox()
# Result: all 10 story levels unlocked, 100+ reagents accessible, full apparatus access.
```

---

## 3. Planetary Physics & The "No Man's Sky" Environmental Matrix

Laboratory physics in ChemLab Sandbox Mode are not static. Through `LaboratoryEnvironmentMatrix` (`src/chemlab/sandbox/no_mans_sky_matrix.py`), players can dynamically adjust the ambient physics constants of the simulation room:

### 3.1 Environmental Variables

| Variable | Range | Earth Baseline | Physical Impact on Chemistry |
|----------|-------|----------------|------------------------------|
| **Gravity ($g$)** | $0.0\text{ g}\ \text{to}\ 3.0\text{ g}$ | $1.0\text{ g}$ | Scales hydrostatic pouring rate ($v \propto \sqrt{g}$). At $0.0\text{ g}$, fluids do not drain; capillary action and surface tension dominate meniscus formation. |
| **Ambient Pressure ($P$)** | $0.001\text{ atm}\ \text{to}\ 50.0\text{ atm}$ | $1.0\text{ atm}$ | Modulates boiling points via the Clausius-Clapeyron equation. Vacuum induces boiling at room temperature; hyperbaric pressures prevent boiling. |
| **Ambient Temperature ($T$)** | $-200^\circ\text{C}\ \text{to}\ +500^\circ\text{C}$ | $+22.0^\circ\text{C}$ | Ambient thermal conduction boundary. Sub-zero temperatures freeze aqueous solutions; extreme heat boils volatile solvents without heaters. |
| **Time Warp ($\Delta t$)** | $0.0\times\ (\text{pause})\ \text{to}\ 100.0\times$ | $1.0\times$ | Scales numerical Arrhenius integration step rates for multi-hour reactions (esterification, slow crystal growth). |

### 3.2 Clausius-Clapeyron Thermodynamic Scaling
Boiling point of solvents under varying ambient pressure is evaluated continuously in real time:

$$\frac{1}{T_{\text{boil}}} = \frac{1}{T_0} - \frac{R}{\Delta H_{\text{vap}}} \ln\left(\frac{P}{P_0}\right)$$

Under orbital vacuum ($P = 0.001\text{ atm}$), water boils vigorously at $-20^\circ\text{C}$. Under hyperbaric conditions ($P = 10\text{ atm}$), water remains liquid past $180^\circ\text{C}$.

### 3.3 Planetary Environment Presets

```jsonc
{
  "planetary_presets": {
    "earth_standard": {
      "gravity_g": 1.0,
      "ambient_pressure_atm": 1.0,
      "ambient_temperature_c": 22.0,
      "description": "Standard Earth sea-level conditions."
    },
    "orbital_zero_g": {
      "gravity_g": 0.0,
      "ambient_pressure_atm": 1.0,
      "ambient_temperature_c": 21.0,
      "description": "Pressurized orbital space station. Fluids form spherical droplets; capillary fluidics enabled."
    },
    "martian_surface": {
      "gravity_g": 0.38,
      "ambient_pressure_atm": 0.006,
      "ambient_temperature_c": -63.0,
      "description": "Martian thin CO2 atmosphere (6 mbar). Pure water sublimates/boils at ~0°C."
    },
    "venusian_hyperbaric": {
      "gravity_g": 0.91,
      "ambient_pressure_atm": 92.0,
      "ambient_temperature_c": 462.0,
      "description": "Supercritical surface conditions. Volatiles remain compressed liquids at extreme temperatures."
    },
    "titan_cryogenic": {
      "gravity_g": 0.14,
      "ambient_pressure_atm": 1.45,
      "ambient_temperature_c": -179.0,
      "description": "Dense cryogenic atmosphere. Methane/ethane liquid lakes; rapid reaction freezing."
    }
  }
}
```

---

## 4. Consequence Engines & Hazard Difficulty Scaling

Sandbox mode permits catastrophic reactions without terminating the play session. The consequence system (`src/simulation/consequence.py`) evaluates real-time physical effects:

1. **Exothermic & Endothermic Thermal Spikes:** Acid-base neutralization creates instantaneous thermal spikes ($\Delta T \propto \Delta H_{\text{rxn}}$); dissolving ammonium nitrate drops vessel temperatures down to freezing.
2. **Precipitation Dynamics:** Supersaturation triggers crystal precipitation (e.g. golden needles of lead iodide, indigo microcrystals).
3. **Gas Release & Pressure Buildup:** Rapid gas evolution ($\text{CO}_2, \text{NO}_x, \text{Cl}_2$) in closed vessels stresses stoppers and glass joints.
4. **Thermal Runaways & Stopper Pops:** Sealed vessels without pressure relief valves trigger audio-visual stopper popping or vessel burst when internal pressure exceeds ratings.
5. **Chemical Oscillators:** Non-equilibrium autocatalysis runs uninterrupted (Briggs-Rauscher, Belousov-Zhabotinsky periodic color cycling).

### Hazard Difficulty Tiers (`HazardDifficulty`)

```python
class HazardDifficulty(StrEnum):
    CREATIVE_GODMODE   = "creative_godmode"    # Indestructible glassware, infinite spill immunity, zero toxic damage.
    STANDARD_STUDENT   = "standard_student"    # Safety warnings, localized smoke, soft cleanup resets.
    HARDCORE_REALISTIC = "hardcore_realistic"  # Glassware shatters, toxic vapors cause health damage, room evacuations.
```

- **In `CREATIVE_GODMODE`:** Overpressure vents harmlessly; toxic gases emit glowing particle indicators without player damage.
- **In `HARDCORE_REALISTIC`:** Rupturing an Erlenmeyer flask under pressure sprays glass shards and hot acid, triggering decontamination showers and laboratory quarantine.

---

## 5. Simulation Time Controller

The time warp system (`src/simulation/time_controller.py`) gives players cinematic and analytical control over reaction kinetics:

| Scale Name | Multiplier | Primary Use Case |
|------------|------------|------------------|
| **PAUSED** | $0.0\times$ | Freeze simulation state for precise measurement inspection, balance reading, and photo capture. |
| **HALF_SPEED**| $0.5\times$ | Inspect violent reactions, explosive foam eruptions, and droplet splashing dynamics. |
| **REAL_TIME** | $1.0\times$ | Authentic 1:1 laboratory pacing for titrations and manual mixing. |
| **FAST_2X** | $2.0\times$ | Moderate acceleration for steady reflux heating and dissolution. |
| **FAST_5X** | $5.0\times$ | Accelerate evaporative concentration and cooling curves. |
| **FAST_10X**| $10.0\times$| Rapid progress through standard 30-minute organic condensations. |
| **TIME_LAPSE_50X** | $50.0\times$ | Multi-hour recrystallization crystal growth and bio-incubations. |
| **MAX_WARP_100X** | $100.0\times$ | Long-term precipitation equilibrium and environmental diffusion. |

Step-frame execution (`time_controller.step_frame()`) allows researchers to advance the kinetic solver by a discrete $\Delta t = 0.016\text{ s}$ while paused.

---

## 6. Synthesis Recording & Experiment Book Export

Players can document and export their synthetic discoveries using the **Experiment Book** system (`src/simulation/experiment_book.py`).

### 6.1 Recording Architecture
1. **Action Journaling:** As the player dispenses liquids, weighs powders, sets hotplates, and stirs mixtures, the `FreeSimulationEngine` records each action with timestamps, reagent IDs, masses/volumes, and vessel IDs.
2. **Snapshot Photos:** Players can trigger the virtual camera to capture in-game viewport snapshots (`Snapshot`), embedding real-time optical attributes (color hex, precipitate density, liquid meniscus level).
3. **Recipe Formulation:** Upon concluding an experiment, the player names and saves the procedure as a `Recipe`.

### 6.2 Recipe Data Schema (`Recipe`)
Serialized as standard JSON compatible with `storage_schemas.py`:

```jsonc
{
  "recipe_id": "rec_custom_briggs_rauscher_001",
  "title": "Optimized Briggs-Rauscher Oscillating Solution",
  "author": "Player Scientist",
  "created_timestamp": "2026-11-04T12:00:00Z",
  "environment": {
    "gravity_g": 1.0,
    "ambient_pressure_atm": 1.0,
    "ambient_temperature_c": 22.0
  },
  "reagents_used": [
    {
      "reagent_id": "malonic_acid",
      "amount_g": 3.12,
      "step_number": 1
    },
    {
      "reagent_id": "potassium_iodate",
      "amount_g": 4.28,
      "step_number": 2
    },
    {
      "reagent_id": "hydrogen_peroxide",
      "amount_ml": 25.0,
      "concentration_percent": 30.0,
      "step_number": 3
    },
    {
      "reagent_id": "manganese_sulfate",
      "amount_g": 0.45,
      "step_number": 4
    },
    {
      "reagent_id": "starch",
      "amount_g": 0.10,
      "step_number": 5
    }
  ],
  "procedure_steps": [
    "Dissolve potassium iodate in 100 mL warm distilled water in Beaker A.",
    "Dissolve malonic acid and manganese sulfate in 100 mL water with starch in Beaker B.",
    "Pour 30% hydrogen peroxide into Beaker C.",
    "Simultaneously mix Beakers A, B, and C in a 500 mL Erlenmeyer flask on magnetic stirrer (300 RPM).",
    "Observe periodic amber-blue-clear oscillation cycle with 15-second frequency."
  ],
  "product_metrics": {
    "final_volume_ml": 225.0,
    "peak_temperature_c": 28.5,
    "oscillation_period_s": 14.8,
    "photograph_token": "snap_br_oscillation_peak_blue.png"
  }
}
```

---

## 7. Player-Created Recipes & Community Import/Export

Custom recipes are first-class assets in ChemLab:

1. **Local Storage:** Saved in `user://recipes/` or SQLite `custom_reaction_recipe_storage` (`storage_schemas.py`).
2. **Direct Export:** Exportable as standalone `.json` files to the player's desktop or documents directory.
3. **Recipe Validation:** When a recipe is imported, the `FreeSimulationEngine` validates reagent IDs against the authoritative `ReagentCatalog`. Unrecognized chemicals or impossible stoichiometry values produce non-blocking warnings.
4. **Automated Replay:** Players can load a saved recipe into the **Synthesis Guided Wizard** (`src/chemlab/synthesis/guided_wizard.py`) to replay step-by-step instructions with visual target confirmation rings.

---

## 8. Data-Driven Configuration Schema

All sandbox tuning constants live in `design/gdd/data/sandbox_config.json`:

```jsonc
{
  "sandbox_configuration": {
    "default_environment": "earth_standard",
    "allow_godmode": true,
    "allow_time_warp": true,
    "max_time_warp": 100.0,
    "min_ambient_pressure": 0.001,
    "max_ambient_pressure": 50.0,
    "min_gravity": 0.0,
    "max_gravity": 3.0,
    "reagent_catalog_override": "ALL_UNRESTRICTED",
    "equipment_catalog_override": "ALL_UNRESTRICTED"
  }
}
```
