# Analytical Instruments — Game Design Document

**Document ID:** `GDD-CHEMLAB-INSTR-001`  
**Version:** 1.0.0  
**Status:** Pre-Production  
**Date:** 2026-11-04  
**Author:** Chemistry & Synthesis Domain Lead

---

## 1. Overview

The Analytical Instruments system provides the physical, procedural, and quantitative basis for product verification, reaction monitoring, and purity auditing in ChemLab: Origins. In real organic and pharmaceutical synthesis, a product does not exist until it is verified by analytical instrumentation.

This document defines the 6 core analytical instruments:
1. **Nuclear Magnetic Resonance (NMR) Spectrometer** (400 MHz benchtop/high-field ¹H and ¹³C)
2. **Gas Chromatography–Mass Spectrometry (GC-MS)** (EI 70 eV, quadrupole analyzer)
3. **Automated & Manual Titration Apparatus** (Dropwise buret, potentiometric titrator)
4. **Analytical Balance** (4-decimal precision, 0.0001 g, draft shield)
5. **Digital pH Meter** (Combination glass electrode, 2/3-point buffer calibration)
6. **Melting Point Apparatus** (Digital capillary melting apparatus, ramp-rate control)

Every instrument models real physical constraints: sample preparation, calibration curves, baseline noise, instrumental artifacts, and user errors. Tuning knobs are stored in external JSON configuration files.

---

## 2. Player Fantasy

> **"I am an analytical chemist decoding the molecular fingerprint of matter. I prepare pristine NMR tubes, inject into GC-MS splitters, titrate to the drop of equivalence, and weigh down to the tenth of a milligram behind draft shields to prove purity."**

### 2.1 Core Gameplay Loop

```
Sample Preparation       →   Instrument Setup       →   Acquisition / Run    →   Data Interpretation   →   Quest Evaluation
(dissolve, filter, weigh)     (calibrate, blank, ramp)   (scan, spin, detect)     (peak pick, integrate)     (pass/fail check)
```

---

## 3. Detailed Rules

### 3.1 Nuclear Magnetic Resonance (NMR) Spectrometer

#### 3.1.1 Operation Flow
1. **Sample Prep:** Dissolve 5–15 mg purified solid (or 10–20 µL liquid) in 0.6 mL deuterated solvent (CDCl₃, DMSO-$d_6$, D₂O, CD₃OD).
2. **Tube Loading:** Transfer into 5 mm borosilicate NMR tube via glass pipette; verify height is 4.0–4.5 cm (vortex depth check).
3. **Insertion & Spinning:** Insert tube into spinner turbine; use depth gauge; lower into magnet bore via pneumatic cushion; engage 20 Hz sample spin.
4. **Acquisition Parameters:** Select nucleus (¹H @ 400 MHz, ¹³C @ 100 MHz); set number of scans ($NS = 16$ for ¹H, $NS = 512$ for ¹³C), spectral width ($SW = 15\text{ ppm}$ for ¹H, $220\text{ ppm}$ for ¹³C), pulse delay ($d_1 = 1.0\text{ s}$).
5. **Processing:** Fourier Transform (FID $\to$ Spectrum); phase correction (zero/first order); baseline flattening; chemical shift referencing (residual solvent peak: CDCl₃ @ 7.26 ppm ¹H, 77.16 ppm ¹³C; TMS @ 0.00 ppm).
6. **Interpretation:** Peak picking, multiplet integration ($\int I \, d\delta$), coupling constant calculation ($J\text{ in Hz}$).

#### 3.1.2 Data Output
- Interactive 1D Spectrum view: Zoom, pan, peak labeling, integral baseline integration.
- Peak Table: Chemical shift ($\delta$, ppm), multiplicity (s, d, t, q, m), integration (proton count), $J$-coupling (Hz).
- Purity Output: Area ratio of target peaks vs impurity peaks.

---

### 3.2 Gas Chromatography–Mass Spectrometry (GC-MS)

#### 3.2.1 Operation Flow
1. **Sample Prep:** Dissolve 1 mg sample in 1.0 mL chromatography-grade solvent (DCM, MeOH, EtOAc). Filter through 0.22 µm PTFE syringe filter into auto-sampler vial with septa cap.
2. **Injection:** Load vial into carousel; select split ratio (splitless for trace impurities, 1:20 or 1:50 for concentrated APIs); set injection volume (1.0 µL).
3. **Oven Method:** Set column temperature ramp (e.g., 50°C hold 1 min, ramp 15°C/min to 280°C, hold 5 min; carrier gas He @ 1.0 mL/min).
4. **Mass Spec Ionization:** Electron Ionization (EI) @ standard 70 eV; scan range $m/z = 35 - 500\text{ Da}$; source temp 230°C.
5. **Data Analysis:** Total Ion Chromatogram (TIC) inspection; peak area integration for percentage purity; background subtraction of baseline; NIST library match factor ($0 - 999$).

#### 3.2.2 Data Output
- Total Ion Chromatogram (TIC): Abundance vs Retention Time ($t_R$, min).
- Mass Spectrum ($m/z$ vs relative abundance %): Molecular ion $[M]^{+\bullet}$, isotopic clusters ($M+1, M+2$), characteristic fragment ions (e.g., $m/z = 43$ for acetyl $[CH_3CO]^+$, $m/z = 91$ for tropylium $[C_7H_7]^+$).
- Library Match Report: Top 5 candidate structures with match similarity index.

---

### 3.3 Automated & Manual Titrator (Buret & Potentiometric)

#### 3.3.1 Operation Flow
1. **Buret Filling:** Flush 50.00 mL buret with titrant (e.g., standardized 0.1000 M NaOH); fill to above zero mark; purge air bubble from stopcock tip; adjust meniscus bottom to 0.00 mL line at eye level.
2. **Analyte Preparation:** Pipette 20.00 mL analyte into 250 mL Erlenmeyer flask or titration beaker; add 2–3 drops visual indicator (phenolphthalein, methyl orange) or immerse calibrated glass combination pH electrode.
3. **Dispensing Modes:**
   - `STREAM`: Fast preliminary titrant delivery ($> 2\text{ mL/s}$).
   - `DROPWISE`: Precision delivery (0.05 mL per drop every 0.8 s).
   - `POTENTIOMETRIC AUTO`: Titrator micro-doses with feedback stabilization ($dpH/dt < 0.01\text{ pH/s}$).
4. **Endpoint Detection:**
   - *Visual:* First persistent faint pink coloration (phenolphthalein, pH 8.2–10.0) lasting $\ge 30\text{ seconds}$.
   - *Potentiometric:* First derivative maximum $\frac{d(pH)}{dV}$ and second derivative zero-crossing $\frac{d^2(pH)}{dV^2} = 0$.

#### 3.3.2 Data Output
- Dispensed volume ($V_{titrant}$, mL, $\pm 0.02\text{ mL}$).
- Titration Curve: pH vs $V_{NaOH}$ (sigmoidal titration curve).
- Equivalence Point: $V_{eq}$, molarity calculation $C_{analyte} = \frac{C_{titrant} \times V_{eq}}{V_{analyte}}$.

---

### 3.4 Analytical Balance

#### 3.4.1 Operation Flow
1. **Leveling & Inspection:** Verify bubble level is centered; clean weighing pan with camel hair brush.
2. **Draft Shield:** Three sliding glass doors (left, right, top).
   - Doors open: Air turbulence causes readout flutter of $\pm 0.0003\text{ g}$.
   - Doors closed: Signal stabilizes within 1.5 seconds ($\pm 0.0001\text{ g}$).
3. **Tare Operation:** Place weigh boat or vessel on pan; press `TARE` button; display resets to `0.0000 g`.
4. **Addition:** Use micro-spatula; tap solid into weigh boat; avoid spilling on pan (spills create tare drift).
5. **Mass Calculation:** $m = \sum_i (n_i \times M_{w,i}) + V \times \rho$.

#### 3.4.2 Data Output
- VFD Digital Display: `X.XXXX g` (cyan/green fluorescent text).
- Stability Indicator: Circle icon illuminated when readout drift $< 0.0001\text{ g/s}$.

---

### 3.5 Digital pH Meter

#### 3.5.1 Operation Flow
1. **Electrode Hydration:** Inspect bulb; remove storage solution cap (3 M KCl).
2. **2-Point / 3-Point Calibration:**
   - Rinse electrode with deionized water; blot with lint-free wipe (no rubbing).
   - Submerge in pH 7.00 buffer $\to$ press `CAL 1` $\to$ wait for stability $\to$ accept.
   - Rinse $\to$ submerge in pH 4.01 buffer (for acids) or pH 10.01 buffer (for bases) $\to$ accept.
   - Instrument calculates Nernst slope: $S = \frac{\Delta E}{\Delta pH}$; pass if $95\% \le S \le 105\%$ (ideal $59.16\text{ mV/pH}$ at 25°C).
3. **Sample Measurement:** Submerge in stirred reaction mixture; activate automatic temperature compensation (ATC); read stabilized pH and mV.
4. **Maintenance:** Return to 3 M KCl storage solution; warning logged if left dry $> 10\text{ minutes}$.

---

### 3.6 Melting Point Apparatus

#### 3.6.1 Operation Flow
1. **Capillary Packing:** Pulverize dry crystals with agate mortar and pestle; push open end of capillary tube into powder; drop tube down 1-meter glass tube to pack bottom (bed height 2–3 mm).
2. **Loading:** Insert capillary into optical observation chamber (up to 3 simultaneous tubes: analyte, reference standard, 1:1 mixture).
3. **Heating Profiles:**
   - *Ramp 1 (Fast scan):* $10^\circ\text{C/min}$ to locate rough melting zone.
   - *Ramp 2 (Precision scan):* $1.0 - 2.0^\circ\text{C/min}$ starting $10^\circ\text{C}$ below estimated melting point.
4. **Visual Phase Transition Observation:**
   - $T_{onset}$: First sign of droplet formation / meniscus collapse.
   - $T_{clear}$: Complete liquefaction and optical clarity.
5. **Mixed Melting Point Test:** 1:1 blend with authentic standard. If identical compound $\to$ sharp MP identical to reference. If different $\to$ depressed MP range ($> 5^\circ\text{C}$ lower, broad range).

---

## 4. Formulas & Mathematical Models

### 4.1 NMR Chemical Shift and Shielding
$$\delta = \frac{\nu_{sample} - \nu_{ref}}{\nu_0} \times 10^6 \, (\text{ppm})$$

Coupling split multiplet intensity follows Pascal's triangle (spin $I = 1/2$):
$$(n+1)\text{-rule: multiplicity } M = n + 1$$

Peak broadening due to impurities / relaxation:
$$\Delta \nu_{1/2} = \frac{1}{\pi T_2^*}$$

### 4.2 GC Retention and Peak Resolution
Capacity factor:
$$k' = \frac{t_R - t_0}{t_0}$$

Chromatographic resolution between two peaks:
$$R_s = \frac{2(t_{R2} - t_{R1})}{w_1 + w_2}$$
$R_s \ge 1.5$ defines baseline separation.

Peak area percentage purity:
$$Purity_{GC}\% = \frac{A_{target}}{\sum_{i} A_i} \times 100$$

### 4.3 Potentiometric Nernst Equation (pH Meter)
$$E_{cell} = E^\circ - \frac{2.303 R T}{F} \cdot pH = E^\circ - 0.05916 \cdot \left(\frac{T}{298.15}\right) \cdot pH \, (\text{V})$$

Electrode slope efficiency:
$$\text{Slope}\% = \frac{|\Delta E_{meas}|}{0.05916 \times |\Delta pH_{buffer}|} \times 100$$

### 4.4 Analytical Balance Draft Flutter
When doors are open:
$$m_{read} = m_{true} + \delta_{flutter}(t) + \delta_{electrostatic}$$
$$\delta_{flutter}(t) = A_{draft} \cdot \sin(2\pi f_1 t) \cdot \cos(2\pi f_2 t) + \mathcal{N}(0, \sigma^2)$$
Where $A_{draft} = 0.0003\text{ g}$, $\sigma = 0.0001\text{ g}$. When closed: $A_{draft} = 0$, $\sigma = 0.00002\text{ g}$.

### 4.5 Melting Point Depression (Freezing Point Depression)
$$\Delta T_m = T_{m,pure} - T_{m,obs} \approx \frac{R \cdot (T_{m,pure})^2}{\Delta H_{fusion}} \cdot x_{impurity}$$

---

## 5. Edge Cases & Player Errors

| Instrument | User Error / Edge Case | In-Game Consequence | Resolution |
|------------|------------------------|---------------------|------------|
| **NMR** | Forgetting deuterated solvent (used regular acetone/water) | Gigantic solvent peak dwarfs analyte; receiver overflow error; quest rejected | Re-prepare sample with CDCl₃ / DMSO-$d_6$ |
| **NMR** | Tube underfilled ($< 3\text{ cm}$) | Inhomogeneous field; severe peak broadening ($J$-couplings unresolvable) | Dilute to 4.5 cm height |
| **GC-MS** | Injecting non-volatile salts / high-boiling acids | Column fouling; baseline rise; inlet degradation warning | Perform aqueous-organic extraction first |
| **GC-MS** | Concentration too high ($> 5\text{ mg/mL}$) | Detector saturation; flat-topped peak; inaccurate purity integration | Dilute 1:10 with DCM |
| **Buret** | Air bubble trapped below stopcock | Bubble dislodges during titration $\to$ false volume jump $\to$ inaccurate stoichiometry | Flick stopcock in STREAM mode to purge air bubble |
| **Buret** | Reading meniscus from top instead of bottom | Systematic parallax error of $+0.15\text{ mL}$ | Align camera with crosshair to meniscus bottom |
| **Balance** | Weighing hot vessel ($> 30^\circ\text{C}$) | Convection air currents create buoyant lift $\to$ mass drifts downward continuously | Cool in desiccator to 22°C before weighing |
| **pH Meter** | Uncalibrated electrode used | Systematic pH offset ($> 0.8\text{ pH}$ error) $\to$ false endpoint declaration | Perform 2-point buffer calibration |
| **Melting Point**| Heating ramp too fast ($> 5^\circ\text{C/min}$) | Thermal lag in glass wall $\to$ observed MP is $4-8^\circ\text{C}$ higher than true value | Repeat with $1^\circ\text{C/min}$ ramp |

---

## 6. Dependencies & Architectural Wiring

```
[Godot 3D Client]  <--- IPC TCP/Pipe --->  [Scientific Core (Python)]
  - Apparatus 3D Meshes                     - cantera_engine.py (Thermodynamics)
  - Interactive Knobs/Buttons               - reagents.py (Reagent Database)
  - VFD / LCD Displays                      - side_reactions.py (Impurity Models)
  - RayCast3D Interaction                   - quest_evaluator.py (Purity Assessment)
                                            - analytical_engine.py (Spectra Generation)
```

1. **Reagent Database (`reagents.py`):** Provides theoretical MW, melting points, pKa, SMILES, and CAS numbers.
2. **Side-Reaction Analyzer (`side_reactions.py`):** Supplies impurity species and mass fractions to analytical generators.
3. **Godot UI / Shader Stack:** Renders interactive 1D spectra (NMR), 2D chromatograms (GC-MS), and live digital displays.
4. **Quest Evaluator (`quest_evaluator.py`):** Compares measured instrument parameters against quest criteria.

---

## 7. Tuning Knobs (Externally Configurable — JSON)

**Configuration File:** `design/gdd/tuning/analytical_instruments.json`

```json
{
  "instruments": {
    "nmr": {
      "spectrometer_frequency_mhz": 400.13,
      "default_scans_1h": 16,
      "default_scans_13c": 512,
      "chemical_shift_tolerance_ppm": 0.05,
      "integral_tolerance_percent": 10.0,
      "minimum_sample_height_cm": 4.0,
      "spinning_rate_hz": 20.0,
      "residual_solvent_shifts_1h": {
        "cdcl3": 7.26,
        "dmso_d6": 2.50,
        "d2o": 4.79,
        "cd3od": 3.31
      }
    },
    "gc_ms": {
      "carrier_gas": "Helium",
      "flow_rate_ml_min": 1.0,
      "injector_temp_c": 250.0,
      "ionization_energy_ev": 70.0,
      "retention_time_tolerance_min": 0.10,
      "purity_pass_area_percent": 85.0,
      "library_match_threshold": 800,
      "maximum_injection_concentration_mg_ml": 2.0
    },
    "titrator": {
      "buret_capacity_ml": 50.00,
      "drop_volume_ml": 0.05,
      "drop_interval_s": 0.80,
      "stream_flow_rate_ml_s": 2.5,
      "meniscus_parallax_tolerance_ml": 0.05,
      "equivalence_point_tolerance_ml": 0.15,
      "phenolphthalein_ph_start": 8.2,
      "phenolphthalein_ph_full": 10.0
    },
    "analytical_balance": {
      "readout_precision_decimals": 4,
      "air_draft_flutter_amplitude_g": 0.0003,
      "flutter_frequency_hz": [1.2, 3.7],
      "stabilization_time_s": 1.5,
      "tare_drift_per_spill_g": 0.0015,
      "thermal_buoyancy_coefficient_g_per_c": 0.00008
    },
    "ph_meter": {
      "ideal_nernst_slope_mv_per_ph_25c": 59.16,
      "minimum_acceptable_slope_percent": 95.0,
      "maximum_acceptable_slope_percent": 105.0,
      "buffer_standards": [4.01, 7.00, 10.01],
      "electrode_response_time_s": 4.0,
      "dry_bulb_damage_timeout_s": 600.0
    },
    "melting_point": {
      "fast_ramp_rate_c_min": 10.0,
      "precision_ramp_rate_c_min": 1.0,
      "max_acceptable_mp_depression_c": 2.5,
      "pure_substance_range_max_c": 2.0,
      "thermal_lag_fast_ramp_error_c": 5.0,
      "capillary_bed_height_optimal_mm": 2.5
    }
  }
}
```

---

## 8. Acceptance Criteria

| ID | Criterion | Test Method |
|----|-----------|-------------|
| **INST-001** | Analytical Balance doors open produces $\pm 0.0003\text{ g}$ flutter | `pytest tests/test_apparatus_systems.py::test_air_draft_flutter_model` |
| **INST-002** | Closing Balance doors settles readout to stable within 1.5s | `pytest tests/test_apparatus_systems.py::test_analytical_balance_gdscript_structure` |
| **INST-003** | Titration buret dispenses exactly 0.05 mL per drop at 0.8 s interval | `pytest tests/test_apparatus_systems.py::test_dropwise_drainage_math` |
| **INST-004** | Acid-Base titration generates sigmoidal curve with equivalence derivative peak | `pytest tests/test_apparatus_systems.py::test_titration_equivalence_curve_and_endpoint` |
| **INST-005** | Phenolphthalein endpoint triggers visual color transition between pH 8.2 and 10.0 | `pytest tests/test_godot_simulation_bridge.py::test_phenolphthalein_equilibrium_colors` |
| **INST-006** | pH meter returns uncalibrated error if buffers not measured prior to quest | Integration test / quest evaluator assertion |
| **INST-007** | Melting point fast ramp ($10^\circ\text{C/min}$) triggers thermal lag warning | Unit test in `tests/test_apparatus_systems.py` |
| **INST-008** | NMR spectrum generates correct integration ratios matching molecular formula | Validation test in `tests/test_rdkit_engine.py` |
| **INST-009** | GC-MS peak area integrates impurities generated by `SideReactionAnalyzer` | Integration test between `side_reactions.py` and GC-MS engine |
| **INST-010** | All tuning constants load from `analytical_instruments.json` without fallback | Grep check for hardcoded instrument limits |

---

## 9. Concrete Verification Workflows (3 Examples)

### 9.1 Verification Workflow 1: Aspirin API Quality Control

| Parameter | Specification |
|-----------|---------------|
| **Target Molecule** | Acetylsalicylic acid (Aspirin), MW 180.16 g/mol, CAS 50-78-2 |
| **Sample Prep** | Recrystallized product washed with cold water, vacuum-dried at 60°C for 30 min. |
| **Instrument 1: Melting Point** | Target: $135 - 136^\circ\text{C}$ (literature: 135°C). Fast ramp to 120°C, then 1.0°C/min. Fail if onset $< 132^\circ\text{C}$ or range $> 3^\circ\text{C}$ (indicates residual salicylic acid). |
| **Instrument 2: ¹H-NMR (400 MHz, CDCl₃)** | - $\delta = 2.35\text{ ppm}$ (s, 3H, $-COCH_3$ acetyl)\n- $\delta = 7.14\text{ ppm}$ (d, $J = 8.1\text{ Hz}$, 1H, Ar-H)\n- $\delta = 7.35\text{ ppm}$ (t, $J = 7.6\text{ Hz}$, 1H, Ar-H)\n- $\delta = 7.62\text{ ppm}$ (t, $J = 7.8\text{ Hz}$, 1H, Ar-H)\n- $\delta = 8.13\text{ ppm}$ (dd, $J = 7.9, 1.6\text{ Hz}$, 1H, Ar-H)\n- $\delta = 11.2\text{ ppm}$ (br s, 1H, $-COOH$). Impurity check: No phenol $-OH$ singlet at $\delta \approx 10.5\text{ ppm}$ (unreacted salicylic acid). |
| **Instrument 3: Analytical Balance** | Weigh $100.0\text{ mg}$ into volumetric flask for spectrophotometric assay. Tare stability confirmed with closed draft shield. |
| **Quest Outcome** | PASS if MP is $134.5 - 136.0^\circ\text{C}$ and unreacted salicylic acid on NMR $< 1.5\%$. |

---

### 9.2 Verification Workflow 2: Paracetamol (Acetaminophen) Batch Analysis

| Parameter | Specification |
|-----------|---------------|
| **Target Molecule** | 4-Acetamidophenol (Paracetamol), MW 151.16 g/mol, CAS 103-90-2 |
| **Sample Prep** | Recrystallized from hot water, dried on Hirsch funnel under aspirator vacuum. |
| **Instrument 1: Melting Point** | Target: $169 - 171^\circ\text{C}$. Measured onset: $169.5^\circ\text{C}$, clear: $170.8^\circ\text{C}$ (sharp $\Delta T = 1.3^\circ\text{C}$). |
| **Instrument 2: GC-MS (EI 70 eV)** | - Retention time $t_R = 7.42\text{ min}$ (DB-5MS column, ramp 80°C to 280°C @ 15°C/min).\n- Mass spectrum base peak $m/z = 109$ ($[M - COCH_3]^+$, 4-aminophenol fragment), molecular ion $[M]^{+\bullet} m/z = 151$ (45% abundance), acetyl fragment $m/z = 43$ (30%).\n- Impurity scan: Check for $N,O$-diacetylated byproduct at $t_R = 8.85\text{ min}$ ($m/z = 193$). Must be $< 2.0\%$ peak area. |
| **Instrument 3: Potentiometric Titrator** | Back-titration of sample in aqueous base to verify purity assay percentage $\ge 98.5\%$. |
| **Quest Outcome** | PASS if GC-MS purity $\ge 98.0\%$ and MP within $169 - 172^\circ\text{C}$. |

---

### 9.3 Verification Workflow 3: Benzaldehyde Precursor Purity & Oxidation Assay

| Parameter | Specification |
|-----------|---------------|
| **Target Molecule** | Benzaldehyde, MW 106.12 g/mol, CAS 100-52-7 (Liquid API precursor) |
| **Sample Prep** | Fractional distillation cut at $178 - 179^\circ\text{C}$. Protected under nitrogen flush. |
| **Instrument 1: GC-MS** | - Injection: 1.0 µL in DCM (1:50 split).\n- $t_R = 4.15\text{ min}$.\n- Mass spectrum: Molecular ion $m/z = 106$ (85%), base peak $m/z = 105$ ($[M-H]^+$, benzoyl cation, 100%), phenyl cation $m/z = 77$ (75%), $m/z = 51$ (35%).\n- Impurity check: Benzoic acid ($t_R = 6.80\text{ min}$, $m/z = 122$) from autoxidation must be $< 3.0\%$. |
| **Instrument 2: pH Meter & Titrator** | Measure acidity of 5% ethanolic solution; titrate trace benzoic acid with 0.050 M NaOH. Acid value must be $< 5.0\text{ mg KOH/g}$. |
| **Instrument 3: Analytical Balance** | Density determination via 5.000 mL pycnometer. Target density: $1.044\text{ g/mL}$ at 20°C. |
| **Quest Outcome** | PASS if GC-MS purity $\ge 97.0\%$ and benzoic acid content $< 2.5\%$. |

---

## 10. Open Questions for User

1. **2D NMR Gameplay:** Should COSY (Correlation Spectroscopy) or HSQC be modeled for advanced late-game natural product identification quests?
2. **Interactive Spectral Processing:** Should the player manually adjust NMR phase correction (PH0/PH1 knobs) and baseline polynomial fit, or have an "Auto-Process" button?
3. **Chromatography Consumables:** Should GC septa, syringe needles, and columns have wear/bleed mechanics requiring replacement after $N$ injections?
4. **Instrument Breakdowns:** Should uncalibrated or improperly maintained instruments incur breakdown events (e.g., detector saturation, blown filament, blocked buret tip)?

---