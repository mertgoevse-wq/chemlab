# ChemLab Safety System — Game Design Document

**Document ID:** `GDD-CHEMLAB-SAFETY-SYSTEM-001`  
**Version:** 1.0.0  
**Status:** Production Specification  
**Target Engine:** Godot 4.7.2 + Embedded Python Safety Core  
**References:** `SCIENTIFIC_VALIDATION.md`, `game-concept.md`, Safety Simulation Unit Tests  

---

## 1. Overview & Design Intent

The ChemLab Safety System is a **central gameplay pillar**, not a peripheral overlay. Every synthesis quest, sandbox experiment, and open-world lab interaction is framed by authentic chemical hazard modeling. The system serves three unified goals:

| Goal | Implementation |
|------|----------------|
| **Educational Authenticity** | Real GHS Rev 10 hazard classes, OSHA 29 CFR 1910.1200 SDS sections, ANSI/AIHA Z9.5 fume hood aerodynamics, ANSI Z358.1 eyewash/shower standards. |
| **Gameplay Consequence** | Hazard ignorance triggers in-simulator consequences: vapor leaks, thermal runaway explosions, stopper projectiles, acid burns — all modeled with physics equations from `SCIENTIFIC_VALIDATION.md §6`. |
| **Narrative Integration** | The **Chemical Safety Officer Engine** (EHS Director persona) dispatches events, quests, and inspections. Players advance skills by demonstrating safe lab citizenship. |

**No real-world hazardous synthesis instructions appear outside the fictional simulator context.** Every procedure is presented as a *simulated quest* or *sandbox scenario* with mandatory safety warnings, GHS context, and PPE requirements.

---

## 2. GHS Hazard Classification Per Reagent

### 2.1 GHS Rev 10 Classes Implemented

| GHS Class | Enum Value | Pictogram | Signal Word | Example Reagents |
|-----------|------------|-----------|-------------|------------------|
| Explosive | `EXPLOSIVE` | GHS01 | DANGER | (Reserved for future advanced content) |
| Flammable | `FLAMMABLE` | GHS02 | DANGER | Acetone, Ethanol, Diethyl Ether |
| Oxidizing | `OXIDIZING` | GHS03 | DANGER | HNO₃, H₂O₂, KMnO₄, Cl₂ |
| Compressed Gas | `COMPRESSED_GAS` | GHS04 | DANGER | Chlorine |
| Corrosive | `CORROSIVE` | GHS05 | DANGER | HCl, H₂SO₄, NaOH |
| Toxic | `TOXIC` | GHS06 | DANGER | HCl, HNO₃, Cl₂ |
| Harmful/Irritant | `HARMFUL_IRRITANT` | GHS07 | WARNING | Ethanol, CuSO₄ |
| Health Hazard | `HEALTH_HAZARD` | GHS08 | DANGER | H₂SO₄ |
| Environmental | `ENVIRONMENTAL` | GHS09 | WARNING | KMnO₄, CuSO₄, Cl₂ |

### 2.2 ChemicalProfile Data Model (Per Reagent)

```python
@dataclass
class ChemicalProfile:
    id: str                           # "hydrochloric_acid"
    name: str                         # "Hydrochloric Acid 37%"
    formula: str                      # "HCl(aq)"
    cas_number: str                   # "7647-01-0"
    molar_mass: float                 # g/mol
    density: float                    # g/mL
    boiling_point_c: float
    flash_point_c: float | None
    autoignition_temp_c: float | None
    vapor_pressure_kpa_20c: float
    is_volatile: bool
    is_acid: bool
    is_base: bool
    acid_pka: float | None
    hazard_classes: set[GHSClass]
    signal_word: SignalWord
    pictograms: list[GHSPictogram]
    h_statements: list[str]           # H314, H335, H290...
    p_statements: list[str]           # P260, P280, P301+P330+P331...
    storage_group: StorageGroup
    incompatible_with: list[str]
    antoine_coefficients: tuple[float, float, float]  # (A, B, C)
```

### 2.3 Vapor Pressure Modeling (Antoine Equation)

For volatile solvents, vapor pressure drives fume hood containment calculations and thermal runaway pressure buildup:

$$\log_{10}(P_{\text{mmHg}}) = A - \frac{B}{T + C} \quad (T \text{ in } ^\circ\text{C})$$

$$P_{\text{kPa}} = P_{\text{mmHg}} \times 0.133322$$

**Validated coefficients** (from NIST Chemistry WebBook):
| Chemical | A | B | C | VP @ 20°C (kPa) |
|----------|---|---|---|----------------|
| Acetone | 7.02447 | 1161.0 | 224.0 | ~24.7 |
| Diethyl Ether | 6.92032 | 1064.07 | 228.8 | ~58.9 |
| Ethanol | 8.04494 | 1554.3 | 222.65 | ~5.95 |
| HCl (37%) | 7.33 | 1356.0 | 247.0 | ~16.0 |

---

## 3. Chemical Incompatibility Matrix

### 3.1 Reactivity Logic (EPA / NOAA CAMEO Standards)

The `check_chemical_compatibility(chem_a, chem_b)` engine evaluates:

| Priority | Check | Reaction Type | Risk Level | Example |
|----------|-------|---------------|------------|---------|
| 1 | Oxidizer + Flammable | `EXPLOSIVE_OXIDATION` | CRITICAL | HNO₃ + Acetone |
| 2 | Strong Acid + Strong Base (≠ NaHCO₃) | `VIOLENT_EXOTHERMIC_NEUTRALIZATION` | SEVERE | H₂SO₄ + NaOH |
| 3 | Acid + NaHCO₃ | `CONTROLLED_NEUTRALIZATION` | **LOW** (Compatible) | HCl + NaHCO₃ |
| 4 | KMnO₄ + Conc. Acid | `EXPLOSIVE_MANGANESE_HEPTAOXIDE_FORMATION` | CRITICAL | KMnO₄ + H₂SO₄ |
| 5 | Storage Group Violation | `STORAGE_SEGREGATION_VIOLATION` | MODERATE | Ether (Flammable) + H₂O₂ (Oxidizer) |
| 6 | Explicit Incompatible List | `INCOMPATIBLE_REAGENTS` | SEVERE | CuSO₄ + Strong Reducers |

### 3.2 IncompatibilityResult Output

```python
@dataclass
class IncompatibilityResult:
    compatible: bool
    risk_level: str           # "NONE" | "LOW" | "MODERATE" | "SEVERE" | "CRITICAL"
    reaction_type: str | None
    hazard_description: str | None
    byproducts: list[str]     # ["Thermal blast wave", "CO2(g)", "Mn2O7 (unstable explosive)"]
```

### 3.3 Storage Segregation Rules

| Storage Group | Cabinet Type | Incompatible Groups |
|---------------|--------------|---------------------|
| `FLAMMABLE_CABINET` | Flammables cabinet (vented) | ACID_CABINET, OXIDIZER_STORAGE |
| `ACID_CABINET` | Corrosive acid cabinet | BASE_CABINET, FLAMMABLE_CABINET |
| `BASE_CABINET` | Corrosive base cabinet | ACID_CABINET |
| `OXIDIZER_STORAGE` | Oxidizer cabinet (separate) | FLAMMABLE_CABINET, ACID_CABINET |
| `TOXIC_SECURE` | Locked poison cabinet | — |
| `GENERAL_STORAGE` | Open shelving | — |

---

## 4. Fume Hood Operation & Sash Rules

### 4.1 Physical Model (ANSI/AIHA Z9.5)

```python
# Standard Lab Digestorium Dimensions
WIDTH: float = 1.90       # m
DEPTH: float = 0.95       # m
HEIGHT: float = 1.50      # m (internal working height)
BENCH_Z: float = 0.90     # m (floor to bench)
MAX_SASH_HEIGHT: float = 0.85  # m
SAFE_SASH_LIMIT: float = 0.45  # m (~18 inches)
BYPASS_AREA: float = 0.04      # m² (top aerodynamic bypass)
```

### 4.2 Face Velocity Calculation

$$v_{\text{face}} = \frac{Q_{\text{exhaust}}}{W \cdot h_{\text{sash}}}$$

- **CAV Mode:** Constant $Q = 0.38 \text{ m}^3/\text{s}$ — face velocity drops as sash rises
- **VAV Mode:** Blower throttles to maintain $v_{\text{face}} \approx 0.50 \text{ m/s}$ ($100 \text{ fpm}$)

**Acceptable Range:** $0.40 \le v_{\text{face}} \le 0.60 \text{ m/s}$ ($80\text{--}120 \text{ fpm}$)

### 4.3 Sash Position Alarm States

| Sash Height | Volatiles Present? | Alarm State | Containment Efficiency | Gameplay Effect |
|-------------|-------------------|-------------|------------------------|-----------------|
| ≤ 0.45 m | Any | `SAFE` | > 99% | Normal operation |
| > 0.45 m | None | `WARNING_SASH_ELEVATED` | 95–99% | Visual/audio warning; skill XP penalty |
| > 0.45 m | Yes (VP > 2 kPa) | `ALARM_SASH_TOO_HIGH_VOLATILE` | < 90% | Vapor leak (g/s); toxicity exposure event |
| Any | Blower failure | `ALARM_LOW_AIRFLOW` | < 50% | Emergency purge required |
| Turbulence detected | — | `ALARM_TURBULENT_LEAKAGE` | < 80% | Immediate evacuation prompt |

### 4.4 3D Aerodynamic Streamlines (for Blender/Godot Animation)

`generate_draft_streamlines(num_streamlines=10, steps=30)` produces particle trails:
- **Origin:** Points in front of sash plane ($y < 0$)
- **Trajectory:** Inward (+Y), upward along baffles (+Z), toward exhaust duct
- **Escaped particles:** Flag `escaped_into_room=True` when containment fails
- **Output:** List of `[(x,y,z), ...]` coordinate tuples per streamline

---

## 5. Emergency Purge System

### 5.1 Activation

- **Manual:** Player presses purge button (physical red mushroom switch on hood)
- **Automatic:** Triggered by `ALARM_SASH_TOO_HIGH_VOLATILE` or `ALARM_TURBULENT_LEAKAGE`
- **API:** `hood.toggle_purge(True)` / `engine.trigger_fume_hood_purge(hood_id)`

### 5.2 Purge Parameters

| Parameter | Value |
|-----------|-------|
| Purge Flow Rate | $0.85 \text{ m}^3/\text{s}$ (max blower capacity) |
| Face Velocity @ 0.45m sash | ~$0.99 \text{ m/s}$ ($195 \text{ fpm}$) |
| Containment Efficiency | 1.0 (100%) during purge |
| Purge Duration | Player-controlled; auto-timeout after 120s |

### 5.3 Gameplay Integration

- **Energy Cost:** Purge consumes lab power budget (Iris Xe thermal budget)
- **Noise:** Audible high-flow roar; visual particle density increase
- **Event:** `FUME_HOOD_PURGE_ACTIVATED` dispatched to Safety Officer Engine
- **Quest:** "Emergency Containment" — player must recognize leak, hit purge, evacuate

---

## 6. Neutralization Drills (Acid Spill, Eyewash, Shower)

### 6.1 Acid Spill Neutralization (NaHCO₃)

**Stoichiometry:** $\text{H}^+ + \text{HCO}_3^- \rightarrow \text{H}_2\text{O} + \text{CO}_2 \uparrow$

| Acid | Equivalence Factor | Moles H⁺ per mole |
|------|-------------------|-------------------|
| HCl, HNO₃ | 1 | 1 |
| H₂SO₄ | 2 | 2 |

**Required NaHCO₃:** $m = n_{\text{H}^+} \times 84.007 \text{ g/mol}$

#### Drill Flow (Quest/Sandbox)

1. **Spill Event:** `engine.create_acid_spill(spill_id, acid_id, volume_L, molarity, location)`
   - Dispatches `CHEMICAL_SPILL_OCCURRED` (CRITICAL)
   - Computes `grams_needed`, initial pH (≤ 0.5 for strong acids)

2. **Player Action:** `engine.neutralize_spill(spill_id, bicarbonate_grams)`
   - Each application updates pH, CO₂ evolution, effervescence state
   - **Correct technique:** Ring perimeter → inward (prevents boiling splatter)
   - **Penalty:** Single dump → -10% score, splatter risk

3. **Completion:** pH 6.5–8.5, effervescence ceased → `safe_for_cleanup=True`
   - Dispatches `SPILL_NEUTRALIZATION_COMPLETE` (INFO)
   - Performance report: score ≥ 80% = pass

### 6.2 Emergency Eyewash & Deluge Shower (ANSI Z358.1)

| Parameter | Requirement |
|-----------|-------------|
| Max Travel Time | ≤ 10 seconds (≈ 12 m @ 1.2 m/s walk) |
| Eyewash Flow | 2.0 L/min (0.5 gpm) |
| Shower Flow | 76 L/min (20 gpm) |
| Flush Duration | 900 seconds (15 minutes) continuous |
| Water Temperature | Tepid: 16–38 °C (60–100 °F) |

#### Drill Flow

1. **Exposure Event:** `engine.start_eyewash_shower_drill(drill_id, exposure_type, chemical_id, distance_m)`
   - Dispatches `PERSONNEL_CONTAMINATION_EMERGENCY` (CRITICAL)

2. **Travel Phase:** `drill.travel_to_station(walking_speed_mps)` 
   - Tracks `time_to_reach_station_s`; >10s = non-compliant

3. **Activation:** `drill.activate_eyewash()` or `drill.activate_shower()`
   - Wrong fixture (eyewash for body splash) = critical error

4. **Flush Phase:** `drill.run_flush(duration_seconds)`
   - Clothing removal required for body exposure
   - < 900s = non-compliant

5. **Evaluation:** `drill.evaluate_drill()`
   - 100% = perfect ANSI compliance
   - Penalties: delayed arrival, wrong fixture, short flush, hot/cold water
   - Injury severity score: 0 (perfect) → 100 (irreversible damage)

---

## 7. Thermal Runaway & Pressure Relief

### 7.1 Vessel Types & Relief Mechanisms

| Vessel Type | Relief Type | Burst Pressure | Relief Behavior |
|-------------|-------------|----------------|-----------------|
| `ERLENMEYER_FLASK_STOPPERED` | `GROUND_GLASS_STOPPER` | ~140 kPa (pop) | Stopper launches as projectile |
| `SCREW_CAP_BOROSILICATE_VIAL` | `GROUND_GLASS_STOPPER` | ~200 kPa | Cap ejects |
| `ROUND_BOTTOM_FLASK_STOPPERED` | `GROUND_GLASS_STOPPER` | ~140 kPa | Stopper launches |
| `AUTOCLAVE_PRESSURE_REACTOR` | `SPRING_RELIEF_VALVE` | 800 kPa (burst) / 220 kPa (valve) | Valve vents, re-seats |
| `SEALED_TEST_TUBE` | `SEALED_NO_RELIEF` | 220 kPa (thin glass) | **Catastrophic BLEVE** |

### 7.2 Physics Model

**Vapor Pressure (Antoine):** $P_{\text{vap}}(T)$ drives headspace pressurization

**Ideal Gas Law:** $P V = n R T$ → $P_{\text{total}} = P_{\text{vap}} + P_{\text{air}} + P_{\text{rxn gas}}$

**Semenov Thermal Explosion Criterion:**
$$\psi = \frac{V (-\Delta H) E_a A \exp(-E_a / R T_a)}{U S R T_a^2}$$
If $\psi > 1/e \approx 0.368$ → **Thermal Runaway**

**Stopper Pop Ballistics:**
$$v_0 = \sqrt{\frac{2 \Delta P V_{\text{headspace}}}{m_{\text{stopper}}}}$$
Trajectory: parabolic with drag; reports `launch_velocity_mps`, `peak_height_m`, `trajectory[]`

**BLEVE Fragmentation:**
- Explosion energy: $E = \int P dV$
- Blast radius: $R \propto E^{1/3}$
- Shrapnel count: Poisson from glass mass; each fragment gets velocity, angle, distance

### 7.3 State Machine & Events

| State | Trigger | Event Dispatched |
|-------|---------|------------------|
| `NORMAL` → `HEATING` | `set_heat_source(W)` | — |
| `HEATING` → `OVERPRESSURE_WARNING` | P > 80% burst | `VESSEL_OVERPRESSURE_WARNING` |
| → `THERMAL_RUNAWAY` | Semenov ψ > 0.368 | `EXOTHERMIC_RUNAWAY_INITIATED` |
| → `STOPPER_POPPED` | P > pop pressure | `STOPPER_POPPED_PRESSURE_RELIEF` |
| → `VALVE_VENTING` | P > valve setpoint | `RELIEF_VALVE_ACTIVATED` |
| → `CATASTROPHIC_EXPLOSION` | P > burst (no relief) | `VESSEL_CATASTROPHIC_EXPLOSION` + `EVACUATION_ORDER` |

### 7.4 Gameplay Integration

- **Quest:** "Pressure Reactor Calibration" — tune valve setpoint, monitor runaway
- **Skill:** *Chemical Engineering* milestone "Pressure Vessel Safety"
- **Sandbox:** Deliberate runaway → observe stopper ballistics, shrapnel patterns
- **Narrative:** Catastrophic explosion triggers lab evacuation, reputation loss, investigation quest

---

## 8. PPE Requirements & Safety-Officer Events

### 8.1 PPE Matrix (Per Hazard Class)

| Hazard Class | Eye Protection | Gloves | Lab Coat | Respirator | Face Shield | Apron |
|--------------|----------------|--------|----------|------------|-------------|-------|
| `FLAMMABLE` | Safety goggles | Nitrile | Flame-resistant | — | — | — |
| `CORROSIVE` | Goggles + Face shield | Neoprene/Butyl | Acid-resistant | — | Required | Acid-proof |
| `TOXIC` | Goggles | Double nitrile | Tyvek® | N95 / PAPR | — | Chemical-resistant |
| `OXIDIZING` | Goggles | Nitrile | Flame-resistant | — | — | — |
| `COMPRESSED_GAS` | Goggles | Leather (cylinder) | Standard | — | — | — |
| `HARMFUL_IRRITANT` | Safety glasses | Nitrile | Standard | — | — | — |

**PPE Enforcement in Simulator:**
- Quest start: Auto-check PPE vs. reagents → warning if insufficient
- Sandbox: Player equips via radial menu; missing PPE = injury risk multiplier
- Eyewash/Shower drill: PPE removal simulated (contaminated clothing doff time)

### 8.2 ChemicalSafetyOfficerEngine — Event Bus Architecture

```python
@dataclass
class SafetyIncidentEvent:
    timestamp: float
    event_type: str
    severity: str         # "INFO" | "WARNING" | "CRITICAL" | "CATASTROPHIC"
    message: str
    details: dict[str, Any]

# Subscription
engine.subscribe_events(lambda ev: ui.show_toast(ev.severity, ev.message))
```

### 8.3 Core Event Types

| Event Type | Severity | Trigger | Details Payload |
|------------|----------|---------|-----------------|
| `GHS_INCOMPATIBILITY_ALERT` | WARNING/CATASTROPHIC | `audit_chemical_interaction()` | risk_level, reaction_type, byproducts |
| `FUME_HOOD_SASH_WARNING` | WARNING | Sash > 0.45m, no volatiles | sash_height_m |
| `FUME_HOOD_SASH_DANGER` | CRITICAL | Sash > 0.45m + volatiles | leakage_g_s |
| `FUME_HOOD_PURGE_ACTIVATED` | WARNING | Purge button / auto | exhaust_flow_m3s |
| `EXOTHERMIC_RUNAWAY_INITIATED` | CRITICAL | `trigger_runaway_reaction()` | delta_h_kJ_mol |
| `STOPPER_POPPED_PRESSURE_RELIEF` | WARNING | Stopper pop | pop_pressure_kPa, launch_velocity_mps |
| `RELIEF_VALVE_ACTIVATED` | INFO | Spring valve opens | valve_pressure_kPa |
| `VESSEL_CATASTROPHIC_EXPLOSION` | CATASTROPHIC | BLEVE | blast_radius_m, shrapnel_count, energy_J |
| `CHEMICAL_SPILL_OCCURRED` | CRITICAL | `create_acid_spill()` | ph, nahco3_needed_g, spread_area_m2 |
| `NEUTRALIZATION_IN_PROGRESS` | WARNING/INFO | `neutralize_spill()` | ph, effervescing |
| `SPILL_NEUTRALIZATION_COMPLETE` | INFO | pH 6.5–8.5 reached | score_percentage |
| `PERSONNEL_CONTAMINATION_EMERGENCY` | CRITICAL | `start_eyewash_shower_drill()` | exposure_type, distance_m |
| `EVACUATION_ORDER` | CATASTROPHIC | BLEVE or major release | evacuation_zone |

### 8.4 Telemetry Export (Per Tick)

```python
telemetry = engine.get_telemetry()
# {
#   "fume_hoods": { "hood_primary": { "sash_height_m": 0.35, "face_velocity_mps": 0.5, "alarm_state": "SAFE", "vapor_leakage_g_s": 0.0, "containment_efficiency": 1.0 }},
#   "pressure_vessels": { "test_flask_1": { "pressure_kpa": 120, "temp_c": 56, "state": "HEATING", "stopper_popped": False }},
#   "active_spills": { "spill_bench_01": { "is_neutralized": True, "safe_for_cleanup": True }},
#   "active_drills": { "drill_01": { "flush_duration_s": 450, "ansi_compliant": True }},
#   "emergency_alarm_active": False,
#   "evacuation_order": False
# }
```

---

## 9. Integration Points

| System | Integration |
|--------|-------------|
| **Quest Engine** | Safety events spawn quests: "Contain the Leak", "Investigate the Explosion", "Pass Safety Audit" |
| **Skill System** | *Lab Safety* skill: XP from successful drills, PPE compliance, zero-incident shifts |
| **Reputation** | Criminal labs: poor safety → NPC distrust, inspection raids; Legal labs: high safety → promotions |
| **Narrative** | Safety Officer (EHS Director) as recurring NPC — inspections, mentorship, incident debriefs |
| **Analytics** | Telemetry exported to companion app for post-lab review, instructor dashboards |

---

## 10. Compliance & Validation

- All calculations trace to `SCIENTIFIC_VALIDATION.md §6` (Semenov, Antoine, ANSI Z9.5, Z358.1)
- Unit tests: `test_ghs.py`, `test_fume_hood.py`, `test_neutralization_drill.py`, `test_thermal_runaway.py`, `test_safety_officer_engine.py` — **294 tests passing**
- No chemical weapon agents, illicit drug synthesis, or high-order explosives in accessible database (`SCIENTIFIC_VALIDATION.md §8.3`)
- Educational framing: every hazard presented in **simulator quest/sandbox context only** with disclaimers (see `safety-framework.md`)