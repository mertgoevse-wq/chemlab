# Synthesis Protocols — Game Design Document

**Document ID:** `GDD-CHEMLAB-SYNTH-001`  
**Version:** 1.0.0  
**Status:** Pre-Production  
**Date:** 2026-11-04  
**Author:** Chemistry & Synthesis Domain Lead

---

## 1. Overview

The Synthesis Protocols system provides the structural backbone for all chemical synthesis gameplay in ChemLab: Origins. Inspired by **lambdaSyn.org** (open-source synthetic procedure database), **PiHKAL/TiHKAL** (Alexander Shulgin's detailed phenethylamine/tryptamine syntheses with stoichiometry, conditions, and analytical verification), and industrial process chemistry, this system transforms real synthetic procedures into playable, verifiable, and educationally sound quest content.

**Core Philosophy:** Every synthesis recipe in-game mirrors a real procedure with authentic stoichiometry, safety constraints (GHS pictograms, fume hood requirements, neutralization drills), and analytical verification checkpoints (NMR, TLC, MP, GC-MS). The simulator is a teaching aid first, entertainment second.

### 1.1 Scope

| Category | Examples | Count (Launch) |
|----------|----------|----------------|
| **Pharmaceutical APIs** | Aspirin, Paracetamol, Caffeine, Benzocaine | 4 |
| **Organic Pigments/Dyes** | Indigo | 1 |
| **Precursor Syntheses** | Benzaldehyde (from toluene), Salicylic acid (Kolbe-Schmitt), Nitroethane, 4-Aminophenol, Indole (Fischer) | 5 |
| **Total Syntheses (Multi-stage)** | Aspirin → Salicylic acid → Phenol, Paracetamol → 4-Aminophenol → Phenol | 2+ |

### 1.2 Key Design Pillars

1. **Stoichiometric Authenticity** — Molar ratios, limiting reagent calculations, theoretical yields derived from NIST thermochemistry.
2. **Condition Sensitivity** — Temperature, time, catalyst presence/absence, addition order, and stirring rate all affect yield/purity.
3. **Side-Reaction Fidelity** — Overheating → tarring/polymerization; wrong addition order → violent exotherm; missing catalyst → unreacted starting material.
4. **Analytical Gates** — Quests require passing TLC, NMR, melting point, and/or GC-MS verification before completion.
5. **Safety Integration** — GHS hazard pictograms, fume hood face-velocity checks, neutralization drills, and PPE requirements are enforced.

---

## 2. Player Fantasy

> **"I am a synthetic chemist who plans, executes, and verifies multi-step organic syntheses — from simple acetylations to complex total syntheses — using authentic laboratory techniques, real safety protocols, and industry-standard analytical verification."**

### 2.1 Core Loops

| Loop | Duration | Description |
|------|----------|-------------|
| **Plan** | 30-60s | Select target molecule → Review retrosynthetic tree → Choose precursor pathway → Calculate stoichiometry → Check GHS hazards → Prepare reagent list |
| **Execute** | 2-10 min | Set up apparatus → Add reagents in correct order → Control temperature/time/stirring → Monitor visual cues (color, precipitation, gas evolution) → Quench/workup |
| **Verify** | 30-90s | Run TLC → Measure melting point → Acquire NMR/GC-MS → Compare to reference spectra → Pass/fail quest gate |
| **Iterate** | Variable | If purity < threshold: diagnose impurity (side-reaction report) → Adjust conditions → Re-run |

### 2.2 Progression Arc

```
Trainee (Quest 1-2)       →   Junior Chemist (Quest 3-5)   →   Senior Chemist (Quest 6-8)    →   Master Alchemist (Quest 9-10)
Single-stage, guided      →   Multi-stage, precursor synth   →   Total synthesis, optimization →   Custom route design, sandbox
Aspirin, Paracetamol      →   Indigo, Caffeine, Benzaldehyde →   Salicylic acid (Kolbe), Indole →   Player-defined targets
```

---

## 3. Detailed Rules

### 3.1 Synthesis Protocol Data Structure

All protocols are defined in `src/chemlab/simulation/total_syntheses.py` (`SynthesisProtocol`) and `src/chemlab/simulation/precursor_synthesis.py` (`PrecursorPathway`). Each is a frozen dataclass loaded from a central registry — **no hardcoded values in gameplay code**.

```python
# total_syntheses.py
@dataclass(frozen=True)
class SynthesisStage:
    stage_number: int
    name: str
    description: str
    technique: TechniqueType  # REFLUX_HEATING, ICE_BATH_QUENCHING, VACUUM_FILTRATION, RECRYSTALLIZATION, LIQUID_EXTRACTION, SUBLIMATION, PRECIPITATION
    required_inputs: tuple[str, ...]  # reagent IDs from reagent registry
    temperature_target_c: float
    duration_s: float
    safety_notes: str = ""

@dataclass(frozen=True)
class SynthesisProtocol:
    id: str
    target_molecule: str
    cas_number: str
    molar_mass_g_mol: float
    description: str
    initial_reagents: tuple[str, ...]
    catalysts: tuple[str, ...]
    stages: tuple[SynthesisStage, ...]
    final_color_rgb: tuple[float, float, float]
    produces_colored_precipitate: bool
    sublimation_point_c: float | None
```

```python
# precursor_synthesis.py
@dataclass(frozen=True)
class ReactionStep:
    step_number: int
    name: str
    equation: str  # Human-readable balanced equation
    reagents: tuple[str, ...]
    catalysts: tuple[str, ...] = ()
    temperature_c: float = 22.0
    pressure_bar: float = 1.0
    acid_catalyst: str | None = None
    yield_fraction: float = 0.85  # Literature yield per step
    hazard_notes: str = ""

@dataclass(frozen=True)
class PrecursorPathway:
    id: str
    target_compound: str
    primary_feedstock: str
    cas_number: str
    description: str
    steps: tuple[ReactionStep, ...>
```

### 3.2 Yield & Purity Calculation

**Theoretical Yield** (100% conversion, no losses):
```python
def theoretical_yield_g(self, moles_limiting: float) -> float:
    return round(moles_limiting * self.molar_mass_g_mol, 4)
```

**Actual Yield** accounts for:
1. **Per-stage literature yield** (`yield_fraction` from `ReactionStep`)
2. **Side-reaction penalties** from `SideReactionAnalyzer.evaluate_conditions()`
3. **Workup losses** (fixed 5% per isolation step: filtration, extraction, recrystallization)
4. **Player technique modifiers** (stirring rate, temperature control accuracy, addition rate)

**Purity Calculation:**
```
purity% = 100 * (1 - total_impurity_mass_fraction)
total_impurity_mass_fraction = sum(side_product.mass_fraction) + unreacted_fraction + tarring_extent
```
- `SideReactionReport.purity_percentage` is the authoritative value used for quest evaluation.
- Quest pass threshold: **≥ 80% purity** (configurable via `tuning.synthesis.purity_pass_threshold`).

### 3.3 Stoichiometry Engine

The reaction solver (`src/chemlab/simulation/reaction_solver.py`) computes:
- **Limiting reagent detection** from `reagent_moles` dict
- **Molar equivalence** for each reagent relative to limiting
- **Excess reagent tracking** (carried forward to workup)
- **Gas evolution stoichiometry** (CO₂, H₂, N₂, HCl, etc.) for visual bubbles/pressure
- **Heat release** via `CanteraEngine` → `adiabatic_temperature_rise_c`

```python
# Example: Aspirin synthesis
# Salicylic acid (138.12 g/mol) + Acetic anhydride (102.09 g/mol) → Aspirin (180.16 g/mol) + Acetic acid
# 1:1 molar ratio. Limiting = salicylic_acid if equimolar.
# Theoretical: 0.1 mol salicylic → 18.016 g aspirin
```

### 3.4 Time / Temperature / Catalyst Variables

All variables are **externally configurable** via `design/gdd/tuning/synthesis.json` (see Section 7). Never hardcoded.

| Variable | Source | Effect on Simulation |
|----------|--------|---------------------|
| `temperature_target_c` | `SynthesisStage.temperature_target_c` | Arrhenius rate; > optimal → side reactions (tarring, oxidation); < optimal → incomplete conversion |
| `duration_s` | `SynthesisStage.duration_s` | Reaction progress integration; too short → high unreacted fraction |
| `has_catalyst` | `SynthesisStage.required_inputs` contains catalyst ID | Missing catalyst → rate multiplier = 0.01; yield drops to ~30% |
| `addition_order_correct` | Player gesture sequence (water into acid vs acid into water) | Wrong order → violent exotherm, aerosol, 10% purity (see `SideReactionAnalyzer`) |
| `stirring_rpm` | Player input (magnetic stirrer control) | < 200 RPM → mass transfer limit; > 1000 RPM → vortex cavitation |
| `in_fume_hood` | Vessel position check | Volatile reagents (acetic anhydride, DCM, ether) → safety penalty if false |

### 3.5 Side Reactions & Impurities

Implemented in `src/chemlab/simulation/side_reactions.py` → `SideReactionAnalyzer`. Each protocol has a dedicated evaluator (`_evaluate_aspirin`, `_evaluate_paracetamol`, `_evaluate_acetanilide`) plus a generic fallback.

**Impurity Severity Tiers:**
| Tier | Mass Fraction | Gameplay Effect |
|------|---------------|-----------------|
| NEGLIGIBLE | < 1% | Auto-removed on standard workup |
| MINOR | 1-5% | Lowers MP by 2-5°C; single recrystallization suffices |
| MODERATE | 5-20% | Requires 2x recrystallization or column chromatography (unlocked later) |
| CRITICAL | > 20% | Quest fails; product toxic/unstable; requires full re-run |

**Key Side-Reaction Triggers (Configurable):**
```json
{
  "aspirin": {
    "overheating_threshold_c": 85.0,
    "tarring_rate_per_degree": 0.015,
    "polymerization_threshold_c": 100.0,
    "missing_catalyst_unreacted_fraction": 0.72
  },
  "paracetamol": {
    "oxidation_threshold_c": 80.0,
    "oxidation_rate_per_degree": 0.015,
    "diacylation_rate_per_degree": 0.008,
    "tarring_rate_per_degree": 0.01
  },
  "acetanilide": {
    "low_temp_threshold_c": 45.0,
    "unreacted_rate_per_degree_below": 0.015,
    "oxidation_threshold_c": 105.0,
    "azobenzene_rate_per_degree": 0.01,
    "tarring_rate_per_degree": 0.018
  }
}
```

### 3.6 Analytical Verification Gates

Each synthesis quest requires **at least two** orthogonal analytical checks:

| Instrument | Measured Property | Pass Criterion | Quest Tier |
|------------|-------------------|----------------|------------|
| **TLC** | Rf value vs reference | Rf ± 0.05 of literature | All |
| **Melting Point Apparatus** | MP range (°C) | Within ± 2°C of literature; narrow range (< 3°C) = pure | All |
| **NMR** (¹H/¹³C) | Chemical shifts, integrals, multiplicity | Major peaks match reference; no impurity peaks > 5% | Junior+ |
| **GC-MS** | Retention time, mass fragments | RT ± 0.1 min; base peak match; no unknown > 3% | Senior+ |
| **pH Meter** | Reaction mixture pH | Quench pH within target window | Trainee+ |

**Quest Evaluation Logic** (`src/chemlab/gameplay/quest_evaluator.py`):
```python
def evaluate_synthesis_quest(protocol_id: str, analytical_results: dict) -> QuestResult:
    protocol = SynthesisRegistry().get_protocol(protocol_id)
    purity = analytical_results.get("purity_percentage", 0)
    mp_measured = analytical_results.get("melting_point_c")
    mp_lit = protocol.melting_point_c  # from tuning JSON
    tlc_match = analytical_results.get("tlc_rf_match", False)
    
    passed = (
        purity >= TUNING.purity_pass_threshold and
        (mp_measured is None or abs(mp_measured - mp_lit) <= TUNING.mp_tolerance_c) and
        tlc_match
    )
    return QuestResult(passed, purity, mp_measured, ...)
```

### 3.7 Safety System Integration

Safety is **not optional** — it is a hard gate on quest progression.

| Safety Requirement | Enforcement | Penalty for Violation |
|--------------------|-------------|----------------------|
| **Fume hood face velocity ≥ 0.5 m/s** | Real-time `FumeHoodEngine` check | Quest auto-fail; safety points -50 |
| **Sash height ≤ 45 cm with volatiles** | `SashPositionMonitor` | Warning → alarm → auto-fail |
| **Acid into water (never water into acid)** | `SideReactionAnalyzer.addition_order_correct` | Violent exotherm simulation; purity 10% |
| **GHS PPE check** | Reagent `ghs_pictograms` → required PPE icons | Cannot start quest without PPE |
| **Neutralization drill** | Spill scenario quest | Must complete before unlocking corrosive reagents |
| **Waste segregation** | End-of-quest waste disposal minigame | Incorrect → reputation penalty |

---

## 4. Formulas

### 4.1 Theoretical Yield
$$Y_{theor} = n_{limiting} \times M_{product}$$

### 4.2 Actual Yield (Multi-Stage)
$$Y_{actual} = n_{limiting} \times M_{product} \times \prod_{i=1}^{N} (y_{stage,i} \times (1 - w_{workup,i})) \times (1 - f_{side})$$

Where:
- $y_{stage,i}$ = literature yield fraction for stage i
- $w_{workup,i}$ = workup loss fraction (default 0.05 per isolation)
- $f_{side}$ = side-reaction mass loss fraction from `SideReactionReport`

### 4.3 Purity Percentage
$$Purity\% = 100 \times \left(1 - \sum_{j} m_{impurity,j} - m_{unreacted} - m_{tarring}\right)$$

### 4.4 Arrhenius Rate Constant
$$k(T) = A \times \exp\left(-\frac{E_a}{R \times T}\right)$$

- $A$, $E_a$ from `CanteraEngine` reaction database (configurable per reaction)
- Temperature acceleration: $k(T_2)/k(T_1) = \exp\left(\frac{E_a}{R} \left(\frac{1}{T_1} - \frac{1}{T_2}\right)\right)$

### 4.5 Adiabatic Temperature Rise
$$\Delta T_{ad} = \frac{-\Delta H_{rxn} \times n_{limiting} \times X_{conv}}{\sum n_i C_{p,i} + m_{solvent} C_{p,solvent}}$$

### 4.6 Melting Point Depression (Impurity Check)
$$\Delta T_f = K_f \times m_{solute} \approx \frac{R \times T_f^2}{\Delta H_{fus}} \times x_{impurity}$$

Used to validate MP narrowing as purity proof.

---

## 5. Edge Cases

| Edge Case | Handling |
|-----------|----------|
| **Reagent not in registry** | `KeyError` at protocol load; fail-fast at registry build |
| **Impossible stoichiometry** (e.g., 0 limiting moles) | Return 0 yield; quest cannot start |
| **Temperature runaway > 200°C** | `ThermalRunawayEngine` triggers vessel rupture simulation; safety event logged |
| **Pressure > vessel rating** | `SemenovBLEVE` model → stopper pop / catastrophic rupture |
| **Catalyst consumed** (not true catalyst) | Tracked as reagent; stoichiometric consumption in `ReactionStep` |
| **Hygroscopic reagent mass drift** | `Reagent.moisture_content_fraction` applied at weigh-in |
| **Chiral impurity** (e.g., ibuprofen enantiomer) | NMR distinguishes; separate tuning knob `chiral_purity_required` |
| **Polymorph formation** | MP shows multiple plateaus; DSC required (late-game instrument) |
| **Solvent carryover in sublimation** | GC-MS detects residual solvent; vacuum bake step required |

---

## 6. Dependencies

| Module | Role | Interface |
|--------|------|-----------|
| `src/chemlab/simulation/reagents.py` | Reagent registry (CAS, MW, density, GHS, color, particle type) | `get_reagent(id)`, `search_by_category()` |
| `src/chemlab/simulation/cantera_engine.py` | Thermodynamics (ΔH, ΔS, ΔG, K_eq, Arrhenius) | `compute_reaction_thermodynamics()` |
| `src/chemlab/simulation/side_reactions.py` | Impurity/yield/safety evaluation | `SideReactionAnalyzer.evaluate_conditions()` |
| `src/chemlab/simulation/rdkit_engine.py` | 3D conformers, SMILES→properties, PDB export | `smiles_to_3d_molecule()` |
| `src/chemlab/gameplay/quest_evaluator.py` | Quest pass/fail logic | `evaluate_synthesis_quest()` |
| `src/chemlab/safety/fume_hood.py` | Face velocity, sash monitoring | `FumeHoodEngine.tick()` |
| `src/chemlab/safety/thermal_runaway.py` | Pressure buildup, Semenov explosion | `ThermalRunawayEngine.step()` |
| `design/gdd/tuning/synthesis.json` | **ALL numeric constants** | Loaded at startup via `TuningManager` |

---

## 7. Tuning Knobs (Externally Configurable — JSON)

**File:** `design/gdd/tuning/synthesis.json` (to be created)

```json
{
  "synthesis": {
    "purity_pass_threshold": 80.0,
    "mp_tolerance_c": 2.0,
    "tlc_rf_tolerance": 0.05,
    "workup_loss_per_stage": 0.05,
    "default_stirring_rpm": 400,
    "min_stirring_rpm": 200,
    "max_stirring_rpm": 1000,
    "fume_hood_min_face_velocity_ms": 0.5,
    "fume_hood_max_sash_cm_volatile": 45,
    "side_reactions": {
      "aspirin": {
        "optimal_temperature_c": 65.0,
        "overheating_threshold_c": 85.0,
        "tarring_rate_per_degree": 0.015,
        "polymerization_threshold_c": 100.0,
        "missing_catalyst_unreacted_fraction": 0.72
      },
      "paracetamol": {
        "optimal_temperature_c": 60.0,
        "oxidation_threshold_c": 80.0,
        "oxidation_rate_per_degree": 0.015,
        "diacylation_rate_per_degree": 0.008,
        "tarring_rate_per_degree": 0.01
      },
      "acetanilide": {
        "optimal_temperature_c": 70.0,
        "low_temp_threshold_c": 45.0,
        "unreacted_rate_per_degree_below": 0.015,
        "oxidation_threshold_c": 105.0,
        "azobenzene_rate_per_degree": 0.01,
        "tarring_rate_per_degree": 0.018
      },
      "indigo": {
        "optimal_temperature_c": 25.0,
        "overheating_decomposition_c": 50.0
      },
      "caffeine": {
        "sublimation_temperature_c": 178.0,
        "sublimation_tolerance_c": 5.0,
        "decomposition_threshold_c": 200.0
      }
    },
    "precursor_yields": {
      "benzaldehyde_from_toluene": 0.65,
      "salicylic_acid_kolbe_schmitt": 0.70,
      "nitroethane_victor_meyer": 0.55,
      "aminophenol_from_phenol": 0.60,
      "indole_fischer": 0.75
    },
    "analytical": {
      "nmr_chemical_shift_tolerance_ppm": 0.05,
      "gc_ms_rt_tolerance_min": 0.1,
      "gc_ms_purity_threshold": 95.0,
      "tlc_visualization_uv254": true,
      "tlc_visualization_iodine": true
    },
    "safety": {
      "acid_into_water_enforced": true,
      "neutralization_drill_required_before": ["h2so4_conc", "hno3_conc", "hcl_conc"],
      "ppe_requirements": {
        "GHS05": ["face_shield", "acid_resistant_gloves", "lab_coat"],
        "GHS06": ["nitrile_gloves", "lab_coat", "fume_hood"],
        "GHS08": ["fume_hood", "nitrile_gloves", "respirator_if_no_hood"]
      }
    }
  }
}
```

**Loading Code Pattern:**
```python
# src/chemlab/config/tuning.py
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SynthesisTuning:
    purity_pass_threshold: float
    mp_tolerance_c: float
    # ... all fields ...

def load_synthesis_tuning() -> SynthesisTuning:
    path = Path("design/gdd/tuning/synthesis.json")
    with path.open() as f:
        data = json.load(f)["synthesis"]
    return SynthesisTuning(**data)  # type: ignore[arg-type]
```

---

## 8. Acceptance Criteria

| ID | Criterion | Test Method |
|----|-----------|-------------|
| **SYN-001** | All 5 pharmaceutical protocols load without error | `pytest tests/test_total_syntheses.py::test_synthesis_registry_contains_pharmaceuticals` |
| **SYN-002** | Aspirin theoretical yield matches 180.16 g/mol × moles | `pytest tests/test_total_syntheses.py::test_paracetamol_stoichiometry_and_yield` (adapted) |
| **SYN-003** | Precursor registry contains all 5 feedstock pathways | `pytest tests/test_precursor_synthesis.py::test_precursor_registry_contains_fundamental_feedstocks` |
| **SYN-004** | Kolbe-Schmitt step requires CO₂ at ≥ 6 bar | `pytest tests/test_precursor_synthesis.py::test_salicylic_acid_kolbe_schmitt_carboxylation` |
| **SYN-005** | Fischer indole synthesis uses phenylhydrazine + ZnCl₂ | `pytest tests/test_precursor_synthesis.py::test_indole_fischer_synthesis` |
| **SYN-006** | Side-reaction analyzer returns CRITICAL purity for water-into-acid | `pytest tests/test_side_reactions.py::test_water_onto_concentrated_acid_triggers_violent_splash` |
| **SYN-007** | Overheating aspirin → tarring + brown discoloration | `pytest tests/test_side_reactions.py::test_overheating_causes_thermal_degradation_and_tarring` |
| **SYN-008** | Missing catalyst → high unreacted fraction | `pytest tests/test_side_reactions.py::test_missing_catalyst_leads_to_unreacted_starting_materials` |
| **SYN-009** | Yield/purity calculation uses tuning JSON (not hardcoded) | Grep for hardcoded literals in yield/purity code → zero hits |
| **SYN-010** | Quest evaluator requires ≥ 2 analytical checks | `pytest tests/test_procedural_labs.py::test_quest_evaluation_fails_when_unmet_purity` |
| **SYN-011** | Fume hood violation auto-fails quest | `pytest tests/test_fume_hood.py::test_sash_too_high_with_volatile_solvents_alarm` |
| **SYN-012** | All 3 GDD files pass ruff check | `.venv/Scripts/ruff check design/gdd` |

---

## 9. Concrete Example Recipes

### 9.1 Aspirin (Acetylsalicylic Acid) — Full Protocol

| Property | Value |
|----------|-------|
| **Target** | Acetylsalicylsäure (Aspirin) |
| **CAS** | 50-78-2 |
| **Molar Mass** | 180.16 g/mol |
| **Route** | Salicylic acid + Acetic anhydride → Aspirin + Acetic acid (H₂SO₄ cat.) |
| **Limiting Reagent** | Salicylic acid (1.0 eq) |
| **Reagents** | Salicylic acid (138.12 g/mol), Acetic anhydride (102.09 g/mol), Conc. H₂SO₄ (3 drops), Ethanol (recryst.), Water (quench) |
| **Stages** | 1. Reflux 65°C, 60s (acylation) 2. Ice bath quench, 30s (hydrolyze excess anhydride) 3. Recrystallization EtOH/H₂O, 78°C, 45s |
| **Theoretical Yield** (0.1 mol) | 18.016 g |
| **Literature Yield** | 75-85% (multi-stage) |
| **Melting Point** | 135-136°C (pure) |
| **TLC** | Rf 0.45 (EtOAc/hexane 1:1, UV254) |
| **NMR (¹H, CDCl₃)** | δ 2.35 (s, 3H, COCH₃), 7.0-8.1 (m, 4H, Ar-H), 11.5 (br s, 1H, COOH) |
| **GHS Hazards** | Acetic anhydride: GHS05 (Corrosive), GHS07 (Harmful); H₂SO₄: GHS05; Salicylic acid: GHS07 |
| **Safety Notes** | Acetic anhydride: lachrymator, use fume hood. H₂SO₄: add to water NEVER water to acid. Ethanol: flammable, no open flame. |

### 9.2 Salicylic Acid via Kolbe-Schmitt Carboxylation — Precursor Pathway

| Property | Value |
|----------|-------|
| **Target** | Salicylsäure (Salicylic Acid) |
| **CAS** | 69-72-7 |
| **Molar Mass** | 138.12 g/mol |
| **Primary Feedstock** | Phenol (94.11 g/mol) |
| **Route** | Phenol → Sodium phenolate (NaOH) → Kolbe-Schmitt (CO₂, 6 bar, 125°C) → Acidification (HCl) |
| **Steps** | 1. Deprotonation: Phenol + NaOH → Sodium phenolate + H₂O (25°C) 2. Carboxylation: Sodium phenolate + CO₂ → Sodium salicylate (125°C, 6 bar) 3. Acidification: Sodium salicylate + HCl → Salicylic acid + NaCl (15°C) |
| **Overall Yield** | ~70% (literature) |
| **Key Equipment** | Pressure reactor (autoclave), burst disk, pressure gauge |
| **GHS Hazards** | Phenol: GHS06 (Toxic), GHS05; NaOH: GHS05; HCl: GHS05; CO₂: asphyxiation at high conc. |
| **Safety Notes** | **Autoclave required** — verify burst disk. Phenol causes severe burns; immediate water wash. CO₂ pressure vessel inspection mandatory. |

### 9.3 Indole via Fischer Indole Synthesis — Precursor Pathway

| Property | Value |
|----------|-------|
| **Target** | Indol (Indole) |
| **CAS** | 120-72-9 |
| **Molar Mass** | 117.15 g/mol |
| **Primary Feedstock** | Phenylhydrazine (108.14 g/mol) + Acetaldehyde (44.05 g/mol) |
| **Route** | Phenylhydrazine + Acetaldehyde → Phenylhydrazone → [3,3]-Sigmatropic rearrangement → Indole + NH₃ (ZnCl₂ cat., 140°C) |
| **Catalyst** | ZnCl₂ (Lewis acid) or conc. H₂SO₄ (Brønsted) |
| **Yield** | ~75% (literature) |
| **GHS Hazards** | **Phenylhydrazine: GHS06 (Toxic), GHS08 (Carcinogen)** — closed system only. Acetaldehyde: GHS02 (Flammable), GHS07. ZnCl₂: GHS05. |
| **Safety Notes** | **Phenylhydrazine is a potent contact toxin and carcinogen.** Use sealed tube/autoclave. No open flask. Waste must be quenched with bleach (oxidative destruction) before disposal. |

---

## 10. Open Questions for User

1. **Precursor depth:** Should *all* starting materials (e.g., toluene, phenol, bromoethane) be synthesizable from even simpler feedstocks (methane, benzene, ethylene), or stop at commodity chemical level?
2. **Chiral synthesis:** Include enantioselective routes (e.g., ibuprofen, naproxen) with chiral HPLC/GC analysis?
3. **Process chemistry mode:** Add continuous-flow reactor simulations (tube reactor, CSTR) for industrial context?
4. **Deuterated solvents:** NMR solvent peaks (CDCl₃, DMSO-d₆, D₂O) as selectable options?
5. **Spectral library:** Bundle simulated NMR/GC-MS reference spectra for all targets, or generate on-the-fly via RDKit/ML?
6. **Regulatory compliance:** Simulate FDA/EMA impurity qualification (ICH Q3A/Q3B) for pharmaceutical syntheses?

---