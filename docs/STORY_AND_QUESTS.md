# ChemLab: Origins — Narrative & Quest Design Specification

## Document Metadata
- **Project:** ChemLab: Immersive 3D Laboratory Simulation
- **Campaign Title:** ChemLab: Origins (Act I — The Vertical Slice)
- **Document Version:** 1.0.0
- **Authors:** Senior Narrative & Quest Designer
- **Target Engine:** Godot 4.x / Python Reaction Solver Bridge / Blender EEVEE Next Real-Time Engine

---

## 1. Setting & World Lore

### 1.1 The Kavli-Helmholtz Institute for Advanced Chemical Synthesis (KHI-ACS)
Located on an alpine plateau overlooking the Rhine-Danube watershed, the **Kavli-Helmholtz Institute for Advanced Chemical Synthesis (KHI-ACS)** is a premier international research facility dedicated to molecular discovery, non-equilibrium chemical physics, and sustainable chemical engineering. Established via a joint transnational treaty and private endowment, the Institute operates as an open-world campus housing both academic research groups and high-containment industrial pilot plants.

The architecture reflects functional brutalism blended with clean-room precision: exposed board-formed concrete, floor-to-ceiling anti-glare borosilicate glass facades, overhead stainless-steel utility trusses delivering dry nitrogen, argon, vacuum, and chilled glycol lines to every wet bench.

### 1.2 Facility Zones & Spatial Layout
The Institute campus is structured into five interconnected modular sectors:
1. **The Grand Atrium & Orientation Hall:** The public face of KHI-ACS. Features interactive periodic tables, safety credentialing kiosks, and the central lift bank leading to research wings.
2. **Analytical Metrology Core (Wing Alpha):** A climate-controlled, vibration-damped wing housing 400 MHz FT-NMR spectrometers, HPLC-DAD stacks, GC-MS quadrupoles, and high-precision analytical microbalances (0.1 µg sensitivity).
3. **Synthetic Chemistry Bays (Wing Beta):** Rows of dual-operator variable air volume (VAV) fume hoods, Schlenk line manifolds, inert-atmosphere gloveboxes, and modular organic synthesis workbenches.
4. **Physical & Dynamic Reaction Arena (Wing Gamma):** Specialized containment for high-rate kinetics, oscillating chemical reactions, photochemistry arrays, and laser spectroscopy stations.
5. **Hazard Mitigation & Environmental Abatement Hub (Lower Level Delta):** Negative-pressure chemical waste neutralization basins, ATEX-rated solvent storage vaults, emergency deluge showers, and HazMat incident response staging.

### 1.3 Key Dramatis Personae

#### Dr. Elena Vance — Senior Safety Director & Industrial Hygiene Officer
- **Background:** Former chief inspector for the Organisation for the Prohibition of Chemical Weapons (OPCW) with a Ph.D. in Chemical Engineering from ETH Zürich.
- **Personality:** Uncompromising, razor-sharp, protective, and possesses a dry, dark academic humor. She measures a chemist’s worth not by the purity of their crystals, but by whether all ten fingers remain intact at the end of the shift.
- **Narrative Role:** Dr. Vance serves as the player's mentor for regulatory adherence, laboratory safety, hazard containment, and emergency response. She operates the compliance scoring system and will shut down any experiment violating OSHA or ANSI standards without hesitation.
- **Voice Cue:** Authoritative, measured mid-European cadence; clicks her mechanical pencil when assessing infractions.

#### Prof. Aris Thorne — Lead Chemist & Chair of Dynamic Reaction Architecture
- **Background:** Celebrated pioneer in non-linear thermodynamics, dissipative structures, and autonomous molecular oscillation. Royal Society Fellow and former Kavli Laureate.
- **Personality:** Brilliant, mercurial, poetic, and perpetually impatient with institutional red tape. He views chemical reactions as living symphonies and considers equilibrium a tragic lack of imagination.
- **Narrative Role:** Prof. Thorne guides the protagonist through experimental methodology, reaction kinetics, total synthesis, and non-equilibrium systems. While he respects Vance's vigilance, he constantly encourages the player to peer beyond safe textbook boundaries.
- **Voice Cue:** Warm, slightly gravelly, rapid-fire intellectual delivery; taps glassware with his glass stirring rod for emphasis.

#### The Protagonist — Junior Lab Fellow
- **Background:** A gifted graduate chemist awarded the prestigious KHI-ACS International Junior Fellowship. Armed with top-tier theoretical knowledge but minimal experience in high-throughput industrial and advanced research laboratories.
- **Narrative Arc:** Begins on Day 1 as an untested novice wearing standard lab garb. Through methodical mastery of laboratory technique, analytical precision, thermal control, and emergency composure, the Fellow earns advanced clearance, laboratory autonomy, and the keys to the legendary *Athanor Core* research suite.

### 1.4 Narrative Tension: The Athanor Anomaly
The narrative background of "ChemLab: Origins" revolves around the sudden disappearance of Dr. Julian Voss, Prof. Thorne's previous star protégé. Six months prior to the player's arrival, an unscheduled non-equilibrium experiment in Wing Gamma suffered a kinetic runaway. Voss vanished from the institute overnight, leaving behind fragmented bench notes concerning an alleged "self-sustaining chemical clockwork" dubbed *Project Athanor*. As the player advances through standard research protocols, subtle anomalies in automated reagent dispensing, unexplained spectral peaks, and encrypted audio logs hidden in lab drawers hint that Voss's research is still active somewhere within the facility.

---

## 2. Skill Tree & Scientific Progression Architecture

The ChemLab progression system is organized around five core scientific disciplines. Progression is non-linear but gated by practical certification exams and quest completions.

```
                             [ CHEMIST RANK TIER ]
             T0: Fellow -> T1: Certified -> T2: Analyst -> T3: Synthesist -> T4: Operator -> T5: Master
                                       |
    +-----------------+----------------+----------------+-----------------+-----------------+
    |                 |                |                |                 |                 |
[SAFETY]         [ANALYTICAL]    [THERMODYNAMICS]  [PREPARATIVE]     [COMPUTATIONAL]   [INTEGRATED]
OSHA/ANSI        Metrology &     Kinetics &        Synthesis &       In-Silico         Autonomous
Mitigation       Spectroscopy    Phase Equilibria  Purification      Modeling          Mastery
```

### 2.1 The Five Disciplines

#### 1. Laboratory Safety (SAF)
- Focus: Personal protection, environmental containment, chemical hygiene, toxicity management, and crisis drills.
- Core Mechanic: Governs the Player Safety Multiplier, steady-hand tolerances during hazardous pouring, and unlocking higher hazard reagent classes (GHS Category 1 Corrosives, Pyrophorics, Toxics).
- Node Unlocks:
  - `SAF-101`: *PPE Protocol & Donning Discipline* — Unlocks nitrile, neoprene, and butyl gloves; splash goggles; lab coat certification.
  - `SAF-102`: *Aerodynamic Containment* — Unlocks manual sash adjustment, face velocity diagnostics, and turbulent airflow visualization.
  - `SAF-103`: *Stoichiometric Acid/Base Abatement* — Unlocks emergency spill kits, bicarbonate berm placement, and effervescence rate moderation.
  - `SAF-201`: *Cryogenic & Pyrophoric Containment* — Unlocks liquid nitrogen dewars, argon atmosphere glovebox, and pyrophoric syringe-transfer techniques.

#### 2. Analytical Chemistry (ANA)
- Focus: Quantitative metrology, volumetric precision, calibration curves, pH stat analysis, and spectroscopy.
- Core Mechanic: Reduces meniscus parallax error, sharpens visual color indicators, and unlocks high-resolution data readouts on digital balances and spectrometers.
- Node Unlocks:
  - `ANA-101`: *Tare & Gravimetric Precision* — Analytical balance 4-decimal stabilization, draft-shield auto-compensation.
  - `ANA-102`: *Volumetric Metrology (Class A)* — Calibrated burets, volumetric pipettes, bubble purge detection, and drop-wise stopcock control.
  - `ANA-103`: *Endpoint Chromatic Recognition* — Sub-visual indicator transition detection (phenolphthalein faint-pink threshold tracking).
  - `ANA-201`: *Optical Spectrophotometry* — UV-Vis absorption spectrum plotting, Beer-Lambert linearity calibration, and wavelength scans.

#### 3. Thermodynamics & Kinetics (THM)
- Focus: Reaction rates, activation energy, Arrhenius relationships, heat exchange, and non-equilibrium oscillatory dynamics.
- Core Mechanic: Unlocks thermal prediction HUD overlays, hotplate PID tuning, jacketed reaction vessel control, and kinetic limit-cycle timers.
- Node Unlocks:
  - `THM-101`: *Calorimetry & Heat Transfer* — Thermocouple placement, water-bath PID stabilization (+/- 0.5°C), endo/exotherm anticipation.
  - `THM-102`: *Thermal Runaway Mitigation* — Heat dissipation calculation, ice-bath quenching speed, activation energy barrier visualization.
  - `THM-201`: *Non-Linear Chemical Oscillators* — Autocatalytic cycle synchronization, Briggs-Rauscher / BZ wave tracking, and redox potential logging.

#### 4. Preparative Synthesis (SYN)
- Focus: Organic and inorganic synthesis, esterification, reflux assemblies, vacuum filtration, and recrystallization yield maximization.
- Core Mechanic: Controls crystallization crystal habit, filtration flow rates, solvent evaporation efficiency, and molecular purity yields.
- Node Unlocks:
  - `SYN-101`: *Reflux & Condensation Rigging* — Liebig and Dimroth condenser assembly, silicone hose water routing, boiling chip addition.
  - `SYN-102`: *Vacuum Crystallization & Filtration* — Büchner funnel clamping, aspirator vacuum tuning, mother liquor washing.
  - `SYN-201`: *Esterification & Catalysis* — Acid-catalyzed condensation, limiting reagent optimization, side-product minimization.

#### 5. Computational Modeling (CMP)
- Focus: In-silico ODE reaction solving, stoichiometry calculations, RDKit 3D conformer minimization, and automated reagent computer bridging.
- Core Mechanic: Unlocks predictive yield displays, Cantera reaction rate integration, and live digital lab notebook auto-population.
- Node Unlocks:
  - `CMP-101`: *Stoichiometric Matrix Solver* — Live molar mass auto-calculation, limiting reagent highlights on benchtop.
  - `CMP-102`: *Kinetic Curve Fitting* — Real-time sigmoidal curve generation, reaction rate order calculation.

---

## 3. Data-Driven Quest Schema

The quest architecture is completely decoupled from UI presentation and graphics, utilizing a JSON/GDScript-compatible schema that interfaces with the physical reaction engine, the computer vision tracker, and the safety officer state machine.

### 3.1 JSON Schema Specification

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ChemLabQuestDefinition",
  "type": "object",
  "required": [
    "quest_id",
    "act",
    "title",
    "narrative_briefing",
    "instructor_id",
    "prerequisites",
    "objectives",
    "failure_conditions",
    "state_validation",
    "rewards"
  ],
  "properties": {
    "quest_id": {
      "type": "string",
      "pattern": "^quest_[0-9]{3}_[a-z0-9_]+$"
    },
    "act": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5
    },
    "title": { "type": "string" },
    "narrative_briefing": {
      "type": "object",
      "required": ["intro_text", "instructor_npc", "audio_log_id"],
      "properties": {
        "intro_text": { "type": "string" },
        "instructor_npc": { "type": "string", "enum": ["dr_elena_vance", "prof_aris_thorne", "dr_marcus_lin"] },
        "audio_log_id": { "type": ["string", "null"] }
      }
    },
    "prerequisites": {
      "type": "object",
      "required": ["completed_quests", "min_safety_score", "required_skills"],
      "properties": {
        "completed_quests": { "type": "array", "items": { "type": "string" } },
        "min_safety_score": { "type": "number", "minimum": 0.0, "maximum": 100.0 },
        "required_skills": { "type": "array", "items": { "type": "string" } }
      }
    },
    "objectives": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["objective_id", "description", "target_entity", "evaluation_mode", "target_value", "tolerance"],
        "properties": {
          "objective_id": { "type": "string" },
          "description": { "type": "string" },
          "target_entity": { "type": "string" },
          "evaluation_mode": { 
            "type": "string", 
            "enum": ["EQUIPMENT_STATE", "METROLOGY_VALUE", "CHEMICAL_REACTION", "SAFETY_COMPLIANCE", "SPECTRAL_MATCH"] 
          },
          "target_value": { "type": ["number", "string", "boolean", "object"] },
          "tolerance": { "type": ["number", "null"] },
          "hints": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "failure_conditions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["condition_id", "severity", "trigger_metric", "operator", "threshold", "narrative_reprimand"],
        "properties": {
          "condition_id": { "type": "string" },
          "severity": { "type": "string", "enum": ["WARNING", "SCORE_PENALTY", "INSTANT_FAIL_EXPLOSION", "CONTAINMENT_LOCKDOWN"] },
          "trigger_metric": { "type": "string" },
          "operator": { "type": "string", "enum": [">", "<", "==", "!=", ">=", "<="] },
          "threshold": { "type": ["number", "string", "boolean"] },
          "narrative_reprimand": { "type": "string" }
        }
      }
    },
    "state_validation": {
      "type": "object",
      "required": ["engine_checks", "required_products", "unwanted_byproducts"],
      "properties": {
        "engine_checks": { "type": "object" },
        "required_products": { "type": "array", "items": { "type": "string" } },
        "unwanted_byproducts": { "type": "array", "items": { "type": "string" } }
      }
    },
    "rewards": {
      "type": "object",
      "required": ["skill_points", "unlocked_nodes", "unlocked_apparatus", "unlocked_reagents", "academic_credential"],
      "properties": {
        "skill_points": { "type": "integer", "minimum": 0 },
        "unlocked_nodes": { "type": "array", "items": { "type": "string" } },
        "unlocked_apparatus": { "type": "array", "items": { "type": "string" } },
        "unlocked_reagents": { "type": "array", "items": { "type": "string" } },
        "academic_credential": { "type": ["string", "null"] }
      }
    }
  }
}
```

### 3.2 GDScript Native Implementation Architecture

```gdscript
# res://scripts/quests/quest_resource.gd
class_name QuestResource
extends Resource

enum EvaluationMode {
	EQUIPMENT_STATE,
	METROLOGY_VALUE,
	CHEMICAL_REACTION,
	SAFETY_COMPLIANCE,
	SPECTRAL_MATCH
}

enum FailureSeverity {
	WARNING,
	SCORE_PENALTY,
	INSTANT_FAIL_EXPLOSION,
	CONTAINMENT_LOCKDOWN
}

@export var quest_id: String = ""
@export var act: int = 1
@export var title: String = ""
@export_multiline var intro_dialogue: String = ""
@export var instructor: String = "dr_elena_vance"

@export var objectives: Array[Dictionary] = []
@export var failure_conditions: Array[Dictionary] = []
@export var state_validation_rules: Dictionary = {}
@export var rewards: Dictionary = {}

func evaluate_objective(objective_id: String, live_context: Dictionary) -> bool:
	for obj in objectives:
		if obj["objective_id"] == objective_id:
			var mode = obj["evaluation_mode"]
			var current_val = live_context.get(obj["target_entity"], null)
			if current_val == null:
				return false
			
			match mode:
				EvaluationMode.EQUIPMENT_STATE:
					return current_val == obj["target_value"]
				EvaluationMode.METROLOGY_VALUE:
					var target = float(obj["target_value"])
					var tol = float(obj["tolerance"])
					return abs(float(current_val) - target) <= tol
				EvaluationMode.CHEMICAL_REACTION:
					return live_context.get("reaction_type") == obj["target_value"]
				EvaluationMode.SAFETY_COMPLIANCE:
					return float(live_context.get("safety_score", 0.0)) >= float(obj["target_value"])
	return false

func check_failures(live_context: Dictionary) -> Dictionary:
	for fail in failure_conditions:
		var val = live_context.get(fail["trigger_metric"], null)
		if val == null:
			continue
		var threshold = fail["threshold"]
		var triggered = false
		match fail["operator"]:
			">": triggered = float(val) > float(threshold)
			"<": triggered = float(val) < float(threshold)
			">=": triggered = float(val) >= float(threshold)
			"<=": triggered = float(val) <= float(threshold)
			"==": triggered = val == threshold
			"!=": triggered = val != threshold
		
		if triggered:
			return {
				"failed": true,
				"severity": fail["severity"],
				"reprimand": fail["narrative_reprimand"]
			}
	return {"failed": false}
```

---

## 4. Playable Vertical Slice Campaign (Quests 1 – 5)

The Vertical Slice covers the complete "Origins: Initiation" arc, progressing from basic personal safety through quantitative analysis, organic synthesis, active hazard response, and culminating in non-linear oscillatory chemistry.

```
+----------------------------------------------------------------------------------------------------+
|                                    VERTICAL SLICE CAMPAIGN FLOW                                    |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [QUEST 1: Orientation & Safety Protocols]                                                         |
|  (Instructor: Dr. Vance | Room: Sector Delta Safety & Antechamber)                                 |
|  * Donning PPE -> Eyewash 15s Test -> Sash 0.35m Calibration -> Balance Tare 2.5000g              |
|                                |                                                                   |
|                                v                                                                   |
|  [QUEST 2: Acid-Base Equilibrium & Titration]                                                      |
|  (Instructor: Prof. Thorne | Room: Wing Alpha Metrology Core)                                      |
|  * Buret Rinse & Bubble Purge -> Pipette 25.00mL HOAc -> Phenolphthalein -> 0.1M NaOH Titration    |
|  * Endpoint Capture (pH 8.2-8.4, faint pink) -> Sigmoidal Inflection Verification                  |
|                                |                                                                   |
|                                v                                                                   |
|  [QUEST 3: Thermodynamic Synthesis of Aspirin]                                                     |
|  (Instructors: Dr. Vance & Prof. Thorne | Room: Wing Beta Synthetic Bay)                           |
|  * Fume Hood Prep -> Salicylic Acid + Acetic Anhydride + H2SO4 -> PID Bath 65°C (+/- 3°C)         |
|  * Thermal Runaway Mitigation (< 85°C) -> Ice Bath Quench -> Büchner Filtration -> 82%+ Yield      |
|                                |                                                                   |
|                                v                                                                   |
|  [QUEST 4: Hazard Mitigation & Chemical Spill Drill]                                               |
|  (Instructor: Dr. Vance | Room: Wing Beta Main Aisle)                                              |
|  * 250mL 3.0M HCl Bench Rupture -> Evacuation Alarm -> Absorbent Berm Dike Perimeter              |
|  * Step-wise NaHCO3 Inward Neutralization -> CO2 Monitoring -> pH Paper Verification (6.5 - 8.0)   |
|                                |                                                                   |
|                                v                                                                   |
|  [QUEST 5: The Oscillating Heart (Briggs-Rauscher Reaction)]                                       |
|  (Instructor: Prof. Thorne | Room: Wing Gamma Dynamic Reaction Arena)                              |
|  * Prepare Solutions A (H2O2), B (KIO3+H2SO4), C (Malonic+MnSO4+Starch) -> 600 RPM Vortex          |
|  * Tri-liquid Co-Infusion -> 8 Cyclic Transitions (Amber -> Blue -> Clear) -> Damping Analysis   |
|                                                                                                    |
+----------------------------------------------------------------------------------------------------+
```

---

### Quest 1: "Orientation & Safety Protocols"
- **Quest ID:** `quest_001_orientation_safety`
- **Act:** I (The Junior Fellow)
- **Primary Instructor:** Dr. Elena Vance
- **Location:** Sector Delta / Preparation & Safety Antechamber
- **Narrative Framing:** Day One at the Institute. Dr. Elena Vance meets the newly arrived fellow at the containment airlock. She makes it unequivocally clear that academic pedigrees do not prevent chemical burns, blindness, or toxic inhalation. Before the player touches a single reagent bottle, they must prove their competence with life-saving equipment.

#### Equipment & Apparatus
- Personal Protective Equipment Locker (Goggles ANSI Z87.1, Nitrile Gloves, Lab Coat)
- ANSI Z358.1 Certified Dual-Stream Eyewash Station with foot-treadle and push-plate
- Variable Air Volume (VAV) Chemical Fume Hood with vertical sliding tempered sash
- Mettler-Toledo 4-Decimal Analytical Balance (Model XPR204)
- Glass weigh boat, micro-spatula, camel-hair balance brush
- Primary standard Sodium Chloride (NaCl, crystalline analytical grade)

#### Step-by-Step Objectives & Quantitative Tolerances
1. **Don Personal Protective Equipment (PPE):**
   - Interact with PPE locker in correct regulatory sequence: Lab Coat -> Eye Splash Goggles -> Nitrile Gloves.
   - *Tolerance:* Sequence strictly checked; attempting to put on gloves before lab coat triggers reprimand for sleeve contamination.
2. **Inspect & Operate Emergency Eyewash Station:**
   - Approach eyewash station, inspect dust covers, actuate push-plate valve.
   - Run continuous flow for a minimum of 15.0 seconds.
   - Verify water temperature (target: tepid 16.0°C to 38.0°C; default simulation 21.5°C) and dual aeration stream height (80 to 120 mm).
3. **Calibrate Chemical Fume Hood Sash:**
   - Grasp sash handle via hand tracking / mouse grip.
   - Adjust vertical sash height from wide-open (0.85 m) down to the OSHA/ANSI working position benchmark of 0.35 m (accepted range: 0.20 m to 0.45 m).
   - Observe face velocity gauge stabilizing between 0.45 m/s and 0.55 m/s (nominal 0.50 m/s).
   - Raise sash past 0.55 m to test audible velocity failure alarm, then restore to 0.35 m and silence alarm.
4. **Precision Analytical Balance Taring & Mass Transfer:**
   - Inspect balance spirit level (bubble must be centered within target reticle).
   - Open right draft-shield door, place glass weigh boat on center pan, close door completely.
   - Press TARE key; confirm digital readout displays `0.0000 g` (+/- 0.0001 g).
   - Open draft shield, transfer solid NaCl standard with micro-spatula until mass reaches `2.5000 g`.
   - Close draft shield; allow convection currents to settle for 3.0 seconds.
   - *Target Mass:* 2.5000 g | *Acceptable Tolerance:* +/- 0.0005 g (2.4995 g to 2.5005 g).

#### State Validation Dictionary
```json
{
  "quest_id": "quest_001_orientation_safety",
  "engine_checks": {
    "player_ppe_flags": ["lab_coat_fastened", "goggles_sealed", "nitrile_gloves_intact"],
    "eyewash_flush_duration_seconds": { "min": 15.0 },
    "eyewash_water_temp_c": { "min": 16.0, "max": 38.0 },
    "fume_hood_sash_height_m": { "target": 0.35, "min": 0.20, "max": 0.45 },
    "fume_hood_face_velocity_mps": { "min": 0.40, "max": 0.60 },
    "fume_hood_alarm_tested": true,
    "balance_level_bubble_offset_mm": { "max": 0.5 },
    "balance_tare_recorded": true,
    "balance_final_mass_grams": { "target": 2.5000, "tolerance": 0.0005 },
    "balance_draft_shield_closed_at_readout": true
  }
}
```

#### Failure Conditions & Reprimands
- **Sash Open Operation:** Leaving sash above 0.50 m while volatile reagents are inside hood -> *Score Penalty (-15) & Vance warning.*
- **Draft Shield Open Reading:** Recording mass while balance doors are open -> *Metrology rejection; air currents cause fluctuating mass.*
- **Eyewash Under-Flush:** Releasing eyewash push-plate before 15 seconds -> *Safety violation; chemical flushes require sustained rinsing.*

#### Dialogue Tree
```
[ELENA VANCE]: "Welcome to Kavli-Helmholtz, Fellow. Before you start dreaming of Nobel banquets, let's understand one thing: chemistry is indifferent to enthusiasm. It respects only discipline. Put on your coat, your goggles, and your gloves. In that exact order."
   ├── [Player]: "Understood, Dr. Vance. Safety first."
   │     └── [VANCE]: "Actions, not slogans. Inspect that eyewash. If you splash concentrated phenol in your eyes, you have ten seconds before permanent corneal scarring. Prove to me the station works."
   └── [Player]: "I've handled wet labs for five years. Is this really necessary?"
         └── [VANCE]: "The last fellow who said that tried to weigh fine powder with the balance draft shield wide open while the ventilation fan was pulsing. Don't be that statistic. Don the PPE."
```

#### Rewards
- Skill Points: 100 SP
- Unlocked Skill Nodes: `SAF-101` (PPE Discipline), `ANA-101` (Gravimetric Tare)
- Unlocked Apparatus: Personal Lab Coat, Safety Splash Goggles, Micro-Spatula, Weigh Boats
- Academic Credential: *KHI-ACS Level 0 General Lab Entry Clearance*

---

### Quest 2: "Acid-Base Equilibrium & Titration"
- **Quest ID:** `quest_002_acid_base_titration`
- **Act:** I (The Junior Fellow)
- **Primary Instructor:** Prof. Aris Thorne (with Dr. Marcus Lin on analytical verification)
- **Location:** Wing Alpha / Analytical Metrology Core
- **Narrative Framing:** Prof. Thorne welcomes the player to the Metrology Core. An analytical sample of acetic acid from a newly synthesized bio-fermentation batch requires exact concentration verification. Thorne emphasizes that volumetric analysis is the classical foundation of quantitative chemistry: a test of patience, dexterity, and visual acuity.

#### Equipment & Reagents
- 50.00 mL Class A Precision Glass Buret with PTFE stopcock (0.05 mL graduations)
- Heavy cast-iron ring stand with dual buret clamp
- White porcelain contrast tile
- 25.00 mL Class A volumetric bulb pipette with three-valve rubber pipette filler (A, S, E valves)
- 250 mL Pyrex Erlenmeyer titration flasks (x3)
- 0.1000 M standardized Sodium Hydroxide solution (NaOH, titrant)
- Unstandardized Acetic Acid stock solution (~0.10 M CH3COOH, analyte)
- Phenolphthalein indicator solution (0.1% in ethanol/water)
- Deionized water wash bottle

#### Chemical Equations & Thermodynamics
$$\text{CH}_3\text{COOH}_{(aq)} + \text{OH}^-_{(aq)} \rightleftharpoons \text{CH}_3\text{COO}^-_{(aq)} + \text{H}_2\text{O}_{(l)}$$
- Acid Dissociation Constant ($K_a$): $1.75 \times 10^{-5}$ ($pK_a = 4.76$ at 25°C)
- Equivalence Point: Hydrolysis of acetate ion yields a basic solution:
$$\text{CH}_3\text{COO}^- + \text{H}_2\text{O} \rightleftharpoons \text{CH}_3\text{COOH} + \text{OH}^- \quad (\text{pH}_{\text{equiv}} \approx 8.72)$$
- Indicator Transition Range: Phenolphthalein colorless ($\text{pH} < 8.2$) to faint pink ($\text{pH } 8.2 - 8.4$) to vibrant magenta ($\text{pH} > 10.0$). Target is the earliest permanent faint pink lasting $>30\text{ seconds}$.

#### Step-by-Step Objectives & Quantitative Tolerances
1. **Buret Preparation & Conditioning:**
   - Rinse 50 mL buret with 5 mL deionized water, drain, then condition with two successive 5 mL rinses of 0.1000 M NaOH titrant to coat inner walls.
   - Clamp buret perfectly plumb on the ring stand.
   - Fill buret with 0.1000 M NaOH using a small funnel until fluid is above the 0.00 mL line; remove funnel.
2. **Purging Stopcock Tip Air Pocket:**
   - Rapidly twist PTFE stopcock 360° into a waste beaker to dislodge trapped air bubbles from the delivery tip.
   - *Failure check:* An air bubble left in tip results in volumetric delivery errors of 0.15 to 0.40 mL.
3. **Volumetric Aliquot Transfer:**
   - Use rubber suction bulb to draw acetic acid into 25.00 mL volumetric pipette.
   - Adjust bottom of meniscus precisely to calibration line at eye level (avoiding parallax).
   - Drain gravity-wise into 250 mL Erlenmeyer flask; touch tip to flask wall for 3 seconds (do not blow out remaining droplet).
   - Add 3 drops of phenolphthalein indicator; place flask on white porcelain contrast tile.
4. **Execution of Titration:**
   - Record initial buret volume $V_{\text{initial}}$ (e.g. 0.00 mL +/- 0.02 mL).
   - Swirl flask continuously with dominant hand while controlling stopcock with non-dominant hand wrapped around the barrel.
   - Rapidly dispense down to estimated 22.0 mL, then transition to drop-by-drop and half-drop additions as pink flashes linger longer.
   - Rinse flask inner walls with DI wash bottle to wash down splashed titrant droplets.
5. **Endpoint Detection & Sigmoidal Curve Logging:**
   - Stop addition when one single half-drop imparts a faint, uniform pale pink hue that persists across the flask for $>30$ seconds.
   - Read final volume $V_{\text{final}}$ at bottom of meniscus.
   - *Theoretical equivalence volume:* 25.00 mL for 0.1000 M.
   - *Acceptable endpoint range:* 24.85 mL to 25.15 mL (relative error $< 0.6\%$).
   - Confirm sigmoidal titration curve generated on digital bench recorder.

#### State Validation Dictionary
```json
{
  "quest_id": "quest_002_acid_base_titration",
  "engine_checks": {
    "buret_conditioned_with_titrant": true,
    "buret_tip_air_bubble_purged": true,
    "pipette_aliquot_volume_ml": { "target": 25.00, "tolerance": 0.03 },
    "indicator_added_drops": { "min": 2, "max": 4 },
    "titration_swirl_rpm_average": { "min": 80.0, "max": 220.0 },
    "endpoint_color_hex": ["#FCE4EC", "#F8BBD0", "#F48FB1"],
    "endpoint_color_overtitrated_fail": ["#E91E63", "#C2185B", "#880E4F"],
    "endpoint_ph_at_completion": { "min": 8.1, "max": 8.9 },
    "titrant_consumed_ml": { "target": 25.00, "tolerance": 0.15 },
    "calculated_molarity_hoac": { "target": 0.1000, "tolerance": 0.0015 }
  }
}
```

#### Failure Conditions & Reprimands
- **Over-titration (Magenta Blowout):** Adding excess NaOH yielding dark magenta/fuchsia solution ($\text{pH} > 9.5$) -> *Must dump flask, record over-titration error, and re-run with fresh aliquot.*
- **Unpurged Air Bubble:** Dispensing titrant with bubble in buret tip -> *Bubble expels mid-run; recorded volume inaccurate by $> 0.2\text{ mL}$.*
- **Parallax Error:** Viewing buret meniscus from above or below horizontal line -> *Visual alignment penalty; buret reading offset by +/- 0.08 mL.*

#### Dialogue Tree
```
[PROF. ARIS THORNE]: "Look at that clear meniscus, Fellow. Two opposing forces: cohesion pulling water inward, adhesion climbing the glass walls. In volumetric analysis, we honor the curve. Read the bottom of the meniscus, not the horns."
   ├── [Player]: "I've brought the titrant right to the point where the pink hue flashes and vanishes in one swirl."
   │     └── [THORNE]: "Splendid! You are in the steep buffer cliff. Now: half-drops only. Split the drop on the glass tip, wash it down with deionized water. That faint blush of pink is equilibrium yielding its secret."
   └── [Player]: "I added two milliliters in a burst and the whole flask went vibrant magenta."
         └── [THORNE]: "A magnificent shade of fuchsia, Fellow, worthy of a Venetian textile, but utterly useless to analytical science. You’ve overshot the equivalence point by three miles. Rinse the Erlenmeyer; start again."
```

#### Rewards
- Skill Points: 150 SP
- Unlocked Skill Nodes: `ANA-102` (Class A Volumetric Metrology), `CMP-102` (Sigmoidal Curve Fitting)
- Unlocked Apparatus: 50 mL Precision Buret, Buret Clamp Stand, 25 mL Volumetric Bulb Pipette, Porcelain Contrast Plate
- Unlocked Reagents: 0.100 M NaOH Standard Solution, 0.100 M Acetic Acid, Phenolphthalein Indicator Solution

---

### Quest 3: "Thermodynamic Synthesis of Aspirin"
- **Quest ID:** `quest_003_aspirin_synthesis`
- **Act:** I (The Junior Fellow)
- **Primary Instructors:** Dr. Elena Vance (Containment/Thermal Oversight) & Prof. Aris Thorne (Synthetic Guidance)
- **Location:** Wing Beta / Synthetic Chemistry Bay
- **Narrative Framing:** The Fellow is entrusted with their first real organic transformation: the classic Fischer-type esterification of salicylic acid to acetylsalicylic acid (Aspirin). Dr. Vance warns that acetic anhydride is a corrosive lachrymator that demands strict fume hood operation, while concentrated sulfuric acid reacts violently with moisture. Prof. Thorne stresses that temperature control is paramount: 65°C drives the reaction to completion, but exceeding 85°C triggers thermal degradation into sticky polymeric tars.

#### Equipment & Reagents
- VAV Fume Hood (operational at 0.50 m/s face velocity)
- 125 mL Pyrex Erlenmeyer synthesis flask
- Constant-temperature circulating water bath with digital PID controller
- Calibrated digital immersion thermocouple (PT100 probe)
- Magnetic stirring hotplate with PTFE stir bar
- Büchner funnel (ceramic 70 mm), heavy-wall vacuum filtering flask (500 mL), water aspirator vacuum pump, Whatman No. 1 filter paper
- Ice-water crystallization bath (-2°C to 4°C)
- Reagents:
  - Salicylic acid powder ($\text{C}_7\text{H}_6\text{O}_3$, MW 138.12 g/mol) — 2.00 g
  - Acetic anhydride liquid ($\text{C}_4\text{H}_6\text{O}_3$, MW 102.09 g/mol, $d = 1.08\text{ g/mL}$) — 5.00 mL
  - Concentrated Sulfuric Acid catalyst ($\text{H}_2\text{SO}_4$, 18.0 M / 98% purity)
  - Chilled deionized water (ice cold, for precipitation and hydrolysis)

#### Chemical Reaction & Thermodynamics
$$\text{C}_7\text{H}_6\text{O}_3\text{ (s)} + \text{C}_4\text{H}_6\text{O}_3\text{ (l)} \xrightarrow{\text{H}_2\text{SO}_4\text{ (cat)}} \text{C}_9\text{H}_8\text{O}_4\text{ (s)} + \text{CH}_3\text{COOH}\text{ (l)}$$
- Enthalpy of Reaction: Exothermic ($\Delta H \approx -32.4\text{ kJ/mol}$).
- Target Reaction Temperature: $65.0^\circ\text{C}$ (optimum kinetic range $60.0^\circ\text{C} - 70.0^\circ\text{C}$).
- Thermal Decomposition Threshold: $> 85.0^\circ\text{C}$.
  - At elevated temperatures, salicylic acid undergoes decarboxylation and self-condensation into yellow/brown polyester tars, destroying product purity.

#### Step-by-Step Objectives & Quantitative Tolerances
1. **Fume Hood Setup & Reagent Charging:**
   - Ensure fume hood sash is at 0.35 m; verify negative pressure airflow indicator is GREEN.
   - Weigh $2.000\text{ g}$ of salicylic acid (+/- 0.010 g) and transfer to 125 mL Erlenmeyer flask.
   - In the fume hood, measure $5.00\text{ mL}$ of acetic anhydride via graduated cylinder and pour into the flask, washing down any salicylic acid sticking to the neck.
2. **Catalyst Addition & Thermal Safety:**
   - Using a glass Pasteur pipette, add exactly 5 drops of concentrated $\text{H}_2\text{SO}_4$ down the inner wall of the flask.
   - Swirl gently; observe immediate mild exotherm as solid starts dissolving.
3. **Controlled Isothermal Heating:**
   - Lower flask into pre-equilibrated $65.0^\circ\text{C}$ water bath.
   - Insert digital PT100 thermocouple into reaction mixture.
   - Maintain temperature between $62.0^\circ\text{C}$ and $68.0^\circ\text{C}$ for 12.0 simulated minutes.
   - *Thermal Runaway Guard:* If hotplate thermal output causes temperature to approach $78^\circ\text{C}$, player must dial down PID heater or temporarily elevate flask from bath. Exceeding $85.0^\circ\text{C}$ results in thermal decomposition.
4. **Quenching Excess Reagent & Induced Crystallization:**
   - Remove flask from bath; allow to cool on bench for 60 seconds to $\sim 45^\circ\text{C}$.
   - Add $20.0\text{ mL}$ of ice-cold deionized water in small portions.
   - Observe exothermic decomposition of unreacted acetic anhydride releasing pungent acetic acid vapors safely up the fume hood exhaust:
   $$\text{C}_4\text{H}_6\text{O}_3 + \text{H}_2\text{O} \rightarrow 2\text{ CH}_3\text{COOH}$$
   - Plunge flask into the crushed ice-water bath.
   - Scratch the bottom inside glass wall with a glass stirring rod to generate micro-scratches that provide nucleation sites for crystal growth.
   - Watch long, brilliant white needle-like crystals of acetylsalicylic acid precipitate rapidly.
5. **Vacuum Filtration & Yield Calculation:**
   - Seat Whatman filter paper in Büchner funnel; moisten with cold DI water; activate water aspirator vacuum.
   - Slurry crystal suspension into funnel; wash crystal bed with two 5 mL portions of ice-cold DI water.
   - Pull air through crystal cake for 3.0 minutes to desolvate.
   - Transfer dry crystals to tared watch glass; determine mass on analytical balance.
   - *Theoretical Yield:* $\frac{2.00\text{ g}}{138.12\text{ g/mol}} \times 180.16\text{ g/mol} = 2.609\text{ g}$.
   - *Target Yield:* $\ge 2.14\text{ g}$ ($\ge 82.0\%$ theoretical yield) with pure white needle morphology.

#### State Validation Dictionary
```json
{
  "quest_id": "quest_003_aspirin_synthesis",
  "engine_checks": {
    "fume_hood_active_during_transfer": true,
    "salicylic_acid_mass_grams": { "target": 2.000, "tolerance": 0.020 },
    "acetic_anhydride_volume_ml": { "target": 5.00, "tolerance": 0.20 },
    "sulfuric_acid_drops": { "min": 4, "max": 6 },
    "reaction_bath_temp_c": { "min": 60.0, "max": 72.0 },
    "max_recorded_internal_temp_c": { "max": 84.9 },
    "ice_water_hydrolysis_volume_ml": { "min": 18.0, "max": 25.0 },
    "stirring_rod_nucleation_scratch_performed": true,
    "vacuum_filtration_pressure_kpa": { "min": -85.0, "max": -60.0 },
    "final_aspirin_dry_mass_grams": { "min": 2.14, "max": 2.61 },
    "yield_percentage": { "min": 82.0 },
    "crystal_purity_score": { "min": 0.95 }
  }
}
```

#### Failure Conditions & Reprimands
- **Thermal Runaway / Tarring:** Internal temperature exceeding $85.0^\circ\text{C}$ -> *Product turns brown/yellow tar; yield collapses below 30%; Vance issues thermal safety violation.*
- **Corrosive Vapor Inhalation:** Adding water to acetic anhydride outside the fume hood -> *Toxic vapor alert; room evacuated; health penalty.*
- **Dissolving Crystals in Hot Wash:** Washing crystals on the filter with room-temperature or warm water instead of ice water -> *Crystals re-dissolve through filter into waste flask; yield penalty.*

#### Dialogue Tree
```
[DR. ELENA VANCE]: "Acetic anhydride is an aggressive lachrymator. If you pop that bottle open outside the sash, you will have twenty people coughing their lungs out in the hallway. Keep your hands inside the hood, Fellow."
   ├── [Player]: "Understood. The hood velocity is at 0.50 m/s and the sash is at 0.35 m."
   │     └── [VANCE]: "Good. And remember: water bath, not direct hotplate heating. Water acts as a thermal buffer. Direct glass-to-plate heating will spike your temperature past the limit before your hands can react."
   └── [PROF. ARIS THORNE]: "Watch the crystallization after the ice bath, Fellow. The moment you scratch the glass with the rod, watch the symmetry break. Homogeneous solution collapsing into thousands of ordered lattices. Chemistry is architecture in miniature."
```

#### Rewards
- Skill Points: 200 SP
- Unlocked Skill Nodes: `THM-101` (Calorimetry & Heat Transfer), `SYN-101` (Reflux & Condensation), `SYN-201` (Esterification Catalysis)
- Unlocked Apparatus: Circulating PID Water Bath, Büchner Vacuum Filtration Rig, Ice Bath Basin, PT100 Thermocouple
- Unlocked Reagents: Salicylic Acid, Acetic Anhydride, Concentrated Sulfuric Acid, Ice Matrix

---

### Quest 4: "Hazard Mitigation & Chemical Spill Drill"
- **Quest ID:** `quest_004_spill_neutralization`
- **Act:** I (The Junior Fellow)
- **Primary Instructor:** Dr. Elena Vance
- **Location:** Wing Beta / Main Laboratory Aisle & Workbench
- **Narrative Framing:** An unannounced emergency containment drill triggered by Dr. Vance. A simulated accident occurs: a shelf support shears, causing a glass reagent bottle containing $250\text{ mL}$ of $3.0\text{ M}$ Hydrochloric Acid ($\text{HCl}$) to shatter across the epoxy resin lab bench and cascade toward the floor. Fuming acidic vapors rise immediately. Dr. Vance initiates the emergency timer: the player must maintain situational awareness, isolate the zone, arrest the spreading liquid, and neutralize the spill stoichiometrically without splashing or creating an uncontrolled exothermic boil.

#### Equipment & Reagents
- Emergency Chemical Spill Response Kit (Yellow High-Density Polyethylene Drum)
- Absorbent polypropylene containment berm dikes (snake booms)
- Granular Sodium Bicarbonate neutralization shaker ($\text{NaHCO}_3$, technical grade)
- Wide chemical scoop and natural polypropylene dustpan
- Colorimetric broad-range pH indicator paper (pH 1.0 to 14.0) with reference swatch
- Neutralizing absorbent cleanup pads
- Heavy neoprene HazMat gloves, full-face splash shield, chemical apron
- Heavy-duty hazardous waste disposal pail with gasket lid

#### Physics, Stoichiometry & Gas Kinetics
$$\text{HCl}_{(aq)} + \text{NaHCO}_{3\text{ (s)}} \rightarrow \text{NaCl}_{(aq)} + \text{H}_2\text{O}_{(l)} + \text{CO}_{2\text{ (g)}}\uparrow$$
- Initial Hazard Profile:
  - Volume: $250\text{ mL}$ ($0.250\text{ L}$) of $3.0\text{ M HCl}$.
  - Total Moles of $\text{H}^+$: $0.250\text{ L} \times 3.0\text{ mol/L} = 0.750\text{ mol H}^+$.
  - Molar mass of $\text{NaHCO}_3$: $84.007\text{ g/mol}$.
  - Stoichiometric Mass of Bicarbonate Required:
  $$m_{\text{NaHCO}_3} = 0.750\text{ mol} \times 84.007\text{ g/mol} = 63.005\text{ g}$$
  - $\text{CO}_2$ Gas Generated: $0.750\text{ mol} \times 24.45\text{ L/mol} \approx 18.34\text{ L}$ of gaseous carbon dioxide.
- Physical Phenomena Modeled:
  - Puddle spreading radius across smooth resin workbench ($r(t) \propto \sqrt{t}$).
  - Viscous fluid dripping from bench lip to floor.
  - Vigorous effervescence (bubbling rate proportional to remaining $[\text{H}^+]$ and local $\text{NaHCO}_3$ addition flux).
  - Risk of acid aerosol spattering if neutralizer is dumped violently into the puddle center.
  - Exothermic heating: $\Delta H_{\text{neutralization}} \approx -12.5\text{ kJ/mol}$; localized puddle temp must remain below $60^\circ\text{C}$ to prevent boiling splatter.

#### Step-by-Step Objectives & Quantitative Tolerances
1. **Immediate Threat Assessment & Warning Call:**
   - Step back immediately from splash zone.
   - Hit the Bench Emergency Alert beacon within 8.0 seconds to sound localized evacuation buzzer.
   - Don Full-Face Shield and Heavy Neoprene HazMat Over-Gloves from the wall-mounted spill station.
2. **Perimeter Containment (Diking):**
   - Retrieve flexible polypropylene absorbent berm dikes from spill kit.
   - Lay down containment berms surrounding the spreading puddle perimeter, forming a horseshoe dam before the acid reaches the front edge of the bench.
   - *Failure check:* Allowing acid to spill over the edge onto the floor increases contaminated surface area threefold and incurs severe score penalty.
3. **Step-Wise Inward Neutralization:**
   - Take granular $\text{NaHCO}_3$ shaker bottle.
   - Apply powder methodically from the outer perimeter inward toward the center in a gentle circular motion.
   - *Spatter Prevention:* Do not dump large clumps into the center of the liquid. Add powder in controlled passes ($10 - 15\text{ g}$ per pass), monitoring the hiss and foam of $\text{CO}_2$ gas release.
4. **Effervescence & Temperature Monitoring:**
   - Continue addition until a total of $65 - 75\text{ g}$ of $\text{NaHCO}_3$ has been integrated.
   - Observe the slurry until active foaming and effervescence completely ceases (indicating no free $\text{H}^+$ ions remain).
5. **Colorimetric pH Verification:**
   - Take a strip of pH indicator paper using plastic forceps.
   - Dip paper into the wet neutralized slurry; compare color to reference card.
   - Target color: Light green to yellow-green (pH $6.5 - 8.0$).
   - If paper shows red/orange (pH $< 5$), add additional $5\text{ g}$ bicarbonate. If paper shows dark blue/violet (pH $> 10$), player over-salted with base.
6. **Slurry Cleanup & Hazardous Disposal:**
   - Use polypropylene scoop and squeegee to collect neutralized slurry and spent berms.
   - Transfer waste into yellow HazMat container; seal gasket lid.
   - Wipe bench surface with neutralizing wet sponge; log incident clearance on safety terminal.

#### State Validation Dictionary
```json
{
  "quest_id": "quest_004_spill_neutralization",
  "engine_checks": {
    "alarm_tripped_within_seconds": { "max": 10.0 },
    "face_shield_donned": true,
    "neoprene_gloves_donned": true,
    "spill_contained_on_bench": true,
    "acid_reached_floor": false,
    "berm_deployment_time_seconds": { "max": 25.0 },
    "neutralizer_application_pattern": "PERIMETER_TO_CENTER",
    "bicarbonate_total_grams_added": { "min": 63.0, "max": 80.0 },
    "effervescence_fully_ceased": true,
    "slurry_final_ph": { "min": 6.5, "max": 8.0 },
    "splatter_droplets_generated": { "max": 0 },
    "waste_sealed_in_hazard_drum": true,
    "overall_drill_score_percent": { "min": 85.0 }
  }
}
```

#### Failure Conditions & Reprimands
- **Center Dump / Acid Boiling Splatter:** Dumping bulk bicarbonate straight into the center of uncontained acid -> *Instant violent foaming eruption; acid droplets splash player face/arms; drill failed.*
- **Uncontained Bench Overflow:** Failing to place berms before acid spills onto floor -> *Contamination expands to Floor Zone; clean-up complexity doubled; 30-point deduction.*
- **Premature Cleanup:** Scooping slurry while it is still effervescing (pH $< 4.0$) -> *Acid off-gassing into scoop; corrosion warning; drill marked incomplete.*

#### Dialogue Tree
```
[ALARM KLAXON PULSING]
[DR. ELENA VANCE over intercom]: "Drill condition active! Hydrochloric acid bottle failure on Bench 4! 250 milliliters, 3 molar! You have toxic fuming and rapid fluid dispersion! Move, Fellow!"
   ├── [Player]: "Alert beacon activated! Deploying absorbent berms at the bench perimeter!"
   │     └── [VANCE]: "Good instinct! Cut off the front edge! If that acid hits the subfloor conduits, we're looking at a half-million in cable corrosion! Now: neutralize from the outside in! Do not dump it all at once!"
   └── [Player]: "Grabbing the bicarbonate and dumping the whole container on it!"
         └── [VANCE]: "Stop! Are you trying to launch an acid volcano?! The carbon dioxide evolution will throw aerosolized hydrochloric mist right into your eyes! Work the edges! Control the rate of effervescence!"
```

#### Rewards
- Skill Points: 250 SP
- Unlocked Skill Nodes: `SAF-103` (Stoichiometric Spill Abatement), `SAF-201` (Hazardous Spill Mitigation)
- Unlocked Apparatus: Chemical Spill Response Kit, Polypropylene Spill Berms, Face Shield, Colorimetric pH Strips
- Unlocked Reagents: Technical Grade Sodium Bicarbonate, Absorbent Neutralizing Pads
- Academic Credential: *OSHA/ANSI Laboratory HazMat First-Responder Certification*

---

### Quest 5: "The Oscillating Heart (Briggs-Rauscher Reaction)"
- **Quest ID:** `quest_005_oscillating_heart`
- **Act:** I Finale (The Gateway to Non-Equilibrium Dynamics)
- **Primary Instructor:** Prof. Aris Thorne
- **Location:** Wing Gamma / Dynamic Reaction Arena (The Dark-Bench Spectrophotometry Suite)
- **Narrative Framing:** The capstone challenge of the Vertical Slice. Prof. Thorne invites the Fellow to the darkened, temperature-stabilized core of Wing Gamma. Having proven their mettle in safety, precision, synthesis, and crisis mitigation, the Fellow is granted access to the frontier of Thorne's life work: non-equilibrium dissipative structures. The Briggs-Rauscher reaction—a coupled oscillating chemical clock—defies intuitive thermodynamics by cycling repeatedly through vivid color states. Thorne watches eagerly: if the Fellow can master this complex three-part mixture and tune its chemical resonance, they will be initiated into the search for *Project Athanor*.

#### Equipment & Reagents
- 500 mL Heavy-Duty Borosilicate Reaction Beaker with calibrated volume markings
- Digital laboratory overhead magnetic stirrer with tachometer readout (set to 600 RPM)
- White PTFE elliptical stirring egg (ensuring vortex stability without cavitation)
- Multi-wavelength optical spectrophotometer probe (fiber-optic dip immersion probe, logging at 460 nm and 620 nm)
- Dark-bench contrast lighting with matte black backdrop
- Constant temperature peltier plate set to $22.0^\circ\text{C}$
- Three precisely prepared stock solutions:
  - **Solution A (Oxidizer):** Hydrogen Peroxide ($\text{H}_2\text{O}_2$, $4.00\text{ M}$, freshly diluted from 30% unstabilized stock).
  - **Solution B (Iodine Source & Acid Matrix):** Potassium Iodate ($\text{KIO}_3$, $0.200\text{ M}$) acidified with Sulfuric Acid ($\text{H}_2\text{SO}_4$, $0.080\text{ M}$).
  - **Solution C (Substrate, Catalyst & Indicator):** Malonic Acid ($\text{CH}_2(\text{COOH})_2$, $0.150\text{ M}$), Manganese(II) Sulfate monohydrate ($\text{MnSO}_4\cdot\text{H}_2\text{O}$, $0.020\text{ M}$), and soluble Potato Starch indicator ($0.10\%\text{ w/v}$).

#### The Non-Linear Chemical Mechanics
The Briggs-Rauscher reaction is governed by two competing thermodynamic and kinetic pathways:
1. **The Non-Radical Pathway:**
   $$\text{IO}_3^- + 2\text{ H}_2\text{O}_2 + \text{CH}_2(\text{COOH})_2 + \text{H}^+ \rightarrow \text{ICH}(\text{COOH})_2 + 2\text{ O}_2 + 3\text{ H}_2\text{O}$$
   - Produces iodomalonic acid while consuming iodine intermediates slowly.
2. **The Radical Autocatalytic Pathway:**
   - Involves $\text{IO}_2^\bullet$ radicals and $\text{Mn}^{2+}/\text{Mn}^{3+}$ catalyst redox transitions:
   $$\text{HIO}_2 + \text{IO}_3^- + \text{H}^+ \rightarrow 2\text{ IO}_2^\bullet + \text{H}_2\text{O}$$
   - When iodide ion $[\text{I}^-]$ concentration drops below a critical threshold, the radical pathway ignites explosively, rapidly converting $\text{H}_2\text{O}_2$ and $\text{HIO}$ into elemental iodine ($\text{I}_2$).
3. **The Cyclic Visual Transitions:**
   - **Phase 1: Colorless to Golden Amber:** Elemental iodine ($\text{I}_2$) accumulates as the radical reaction surges:
   $$\text{Amber Appearance: } [\text{I}_2] > 10^{-4}\text{ M}$$
   - **Phase 2: Golden Amber to Deep Midnight Blue / Black:** When free $\text{I}^-$ and $\text{I}_2$ combine, they form the triiodide ($\text{I}_3^-$) and pentaiodide ($\text{I}_5^-$) polyiodide chains that insert into the helical cavities of amylose starch, creating the intense charge-transfer midnight blue complex:
   $$\text{I}_2 + \text{I}^- + \text{Starch} \rightleftharpoons [\text{Starch}\cdot\text{I}_3^-]\text{ (Deep Blue)}$$
   - **Phase 3: Midnight Blue to Crystal Clear:** As iodomalonic acid is formed and $\text{I}_2$ is stripped away, the starch complex dissociates rapidly, clearing the solution back to crystal clarity within 0.5 seconds.
   - **Periodicity:** At $22.0^\circ\text{C}$ with proper concentrations, each oscillation cycle lasts between $12.0$ and $16.0$ seconds, repeating for $15 - 25$ cycles before reactant depletion causes terminal damping.

#### Step-by-Step Objectives & Quantitative Tolerances
1. **Precision Aliquot Preparation:**
   - Measure $100.0\text{ mL}$ of Solution A, $100.0\text{ mL}$ of Solution B, and $100.0\text{ mL}$ of Solution C into separate clean graduated cylinders (+/- 0.5 mL).
2. **Vortex & Stirrer Hydrodynamics:**
   - Pour Solution B and Solution C into the 500 mL beaker on the magnetic stirrer.
   - Adjust magnetic stirrer speed to exactly $600\text{ RPM}$ (+/- 30 RPM).
   - Ensure a clean, smooth central vortex without bubbles or turbulent splashing.
   - Insert spectrophotometer fiber-optic immersion probe into the beaker periphery.
3. **Triggering the Oscillator (Co-Infusion):**
   - In a single smooth, decisive pour, introduce the $100.0\text{ mL}$ of Solution A into the swirling mixture.
   - Start the optical data logger instantly upon mixing.
4. **Spectroscopic Oscillation Verification:**
   - Observe and record at least 8 continuous, uninterrupted oscillation cycles.
   - Optical absorbance at $460\text{ nm}$ (amber) and $620\text{ nm}$ (starch-iodine blue) must register distinct, periodic square-wave / relaxation peaks.
   - *Period Consistency:* Cycle periods must remain within $14.0 \pm 2.0\text{ seconds}$ across the first 5 cycles.
5. **Kinetic Damping & Substrate Consumption Analysis:**
   - Allow reaction to run through cycle 10; observe the gradual lengthening of the clear phase as malonic acid is converted to diiodomalonic acid and carbon dioxide micro-bubbles slowly evolve.
   - Export limit-cycle phase space plot ($[\text{I}_2]$ vs $[\text{I}^-]$) on the bench computer terminal.

#### State Validation Dictionary
```json
{
  "quest_id": "quest_005_oscillating_heart",
  "engine_checks": {
    "solution_a_volume_ml": { "target": 100.0, "tolerance": 1.0 },
    "solution_b_volume_ml": { "target": 100.0, "tolerance": 1.0 },
    "solution_c_volume_ml": { "target": 100.0, "tolerance": 1.0 },
    "stirrer_speed_rpm": { "target": 600.0, "min": 550.0, "max": 650.0 },
    "reaction_temperature_c": { "target": 22.0, "min": 20.0, "max": 24.0 },
    "spectrophotometer_probe_immersed": true,
    "completed_oscillation_cycles": { "min": 8 },
    "average_cycle_period_seconds": { "min": 12.0, "max": 16.5 },
    "color_sequence_validated": [
      "COLORLESS", "AMBER", "DEEP_BLUE", "COLORLESS",
      "AMBER", "DEEP_BLUE", "COLORLESS",
      "AMBER", "DEEP_BLUE", "COLORLESS"
    ],
    "phase_portrait_limit_cycle_generated": true
  }
}
```

#### Failure Conditions & Reprimands
- **Stirrer Stall or Turbulent Cavitation:** Stirrer below 300 RPM causes spatial heterogeneity (color clumps rather than uniform solution); stirrer above 850 RPM introduces cavitation bubbles that disrupt spectrophotometer beam -> *Oscillation coherence lost; run invalidated.*
- **Temperature Deviation:** Reaction running $> 32^\circ\text{C}$ accelerates radical branch into non-oscillatory permanent iodine brown; running $< 15^\circ\text{C}$ freezes oscillation kinetics -> *Thorne critiques lack of thermal stability.*
- **Incorrect Order of Addition:** Adding Solution A without manganese catalyst or starch -> *Reaction stalls or goes irreversibly dark without cycling.*

#### Dialogue Tree
```
[PROF. ARIS THORNE, lights dimmed in Wing Gamma]: "Turn the room lights down, Fellow. Let the glow of the data screen and the liquid speak for themselves. You have spent your life being told that reactions move from reactants to products in a straight, boring line toward equilibrium. Tonight, you see chemistry breathe."
   ├── [Player]: "All three solutions are at 22°C. Stirrer locked at 600 RPM. Introducing Solution A now."
   │     └── [THORNE]: "Watch! There! Clear... amber... and BAM! Midnight blue! Look at that spectrophotometer curve jump! It's a non-linear limit cycle, Fellow. The iodine concentration isn't dying down; it's hunting between radical and non-radical attractors! Keep that vortex steady!"
   └── [Player]: "Why does the blue color snap back to clear so fast? It looks instantaneous."
         └── [THORNE]: "Because the moment the iodide threshold triggers the iodomalonic sink, the starch complex is starved of iodine in less than three hundred milliseconds. It’s not just a reaction—it’s a molecular flip-flop circuit. You are watching chemical computation in a glass beaker."
[DR. ELENA VANCE enters]: "Peltier temperature steady, exhaust scrubbers nominal, zero vapor leakage. I admit it, Thorne... your pulsating monster is behaving itself. Well done, Fellow. You've earned your stripes."
```

#### Rewards
- Skill Points: 500 SP
- Unlocked Skill Nodes: `THM-201` (Non-Linear Chemical Oscillators), `CMP-101` (Stoichiometric Matrix Solver)
- Unlocked Apparatus: Digital Overhead Stirrer, Multi-Wavelength Fiber-Optic Spectrophotometer, Peltier Temperature Control Bench
- Unlocked Reagents: Malonic Acid, Potassium Iodate, Manganese(II) Sulfate, Soluble Potato Starch Indicator, Hydrogen Peroxide 30%
- Academic Credential: *Fellowship Research Track Promotion: Specialist in Non-Equilibrium Chemical Dynamics*
- Narrative Unlock: *The Keycard to Sub-Level Delta & The Voss Laboratory Archive (Act II Hook)*

---

## 5. Dialogue Scripts, Environmental Storytelling & Audio Logs

### 5.1 Environmental Storytelling Assets
To ground the player in a living, breathing research facility, the following environmental assets and interactive terminals are scattered throughout the vertical slice:
1. **The Fume Hood Whiteboards:** Hand-scribbled chemical structures in dry-erase marker. In Wing Beta, a faded equation depicts an anomalous rate law with a circled question mark: `k_obs = A * exp(-Ea / RT) * [Athanor]?`
2. **Safety Notice Board (Wing Delta):** OSHA 300 incident summary logs with Dr. Vance’s sarcastic red pen annotations ("Reminder: Pipetting with the mouth was banned in 1974. Do not test my patience again.").
3. **The Glovebox Sticky Note:** Attached to Glovebox 03 in Prof. Thorne's bay: *"Julian — check the iodine clock period at 4°C. The damping ratio isn't fitting the Lindemann-Hinshelwood model. There's a second autocatalyst. — A.T."*

### 5.2 Audio Log: Julian Voss — Log 047 (Found in Wing Gamma Desk)
- **Audio Log ID:** `log_voss_047_resonance`
- **Transcript:**
> *(Sound of high-frequency glass resonance and an oscillating liquid vortex in the background)*
>
> "Julian Voss recording. 02:40 AM. Aris thinks I'm chasing ghosts. He keeps calling the Briggs-Rauscher an educational curiosity—a party trick for undergraduates. He doesn't see it.
>
> When you couple the iodate oscillator to an immobilized enzymatic matrix under constant microfluidic feed... the oscillations don't damp out after twenty cycles. They synchronize. Last night, at 01:15, Beaker 4 and Beaker 7 locked phase across two meters of separation through the shared electrolyte drain. It's not just a clock. It's a chemical neural network.
>
> Elena is getting suspicious about the peroxide shipments. If she flags my requisition, I'll have to move the secondary manifold down to Sub-Level Delta. The old fermentation vaults... nobody goes down there except the wastewater technicians. If anyone finds this... look at the third derivative of the absorbance curve. The answer is in the inflection."

---

## 6. Verification & Automated Test Matrix

The quest state machine interfaces directly with `chemlab_core` and the headless pytest test suite (`tests/test_story_mode.py`). The following test scenarios ensure end-to-end reliability of the quest engine:

| Test Identifier | Quest Target | Injected Failure State | Expected Engine Response |
| :--- | :--- | :--- | :--- |
| `test_quest_001_sash_high` | Quest 1 | Sash set to 0.75 m with volatile present | `FumeHoodAlarmState.ALARM_SASH_TOO_HIGH` triggered, score deducted by 15. |
| `test_quest_001_balance_tare` | Quest 1 | Mass recorded before tare | Metric validation rejects, balance tare prompt re-asserted. |
| `test_quest_002_overtitration` | Quest 2 | pH forced to 10.5 (fuchsia endpoint) | `endpoint_color_overtitrated_fail` triggered, objective marked failed, aliquot reset. |
| `test_quest_003_thermal_runaway`| Quest 3 | Hotplate temp allowed to climb to 92°C | Reaction kinetics branch to `AspirinDecompositionTar`, yield $< 20\%$. |
| `test_quest_004_acid_floor` | Quest 4 | Berms deployed after puddle radius $> 0.8\text{ m}$ | `acid_reached_floor: true`, incident score $< 70\%$, HazMat re-test mandatory. |
| `test_quest_005_rpm_cavitation` | Quest 5 | Stirrer set to 950 RPM | Spectrophotometer beam disrupted by air vortex, oscillation count invalidated. |
| `test_quest_chain_progression` | Quests 1-5 | Sequential completion with passing metrics | Player promoted from `TRAINEE` through `APPRENTICE`, `JOURNEYMAN`, to `SENIOR_SYNTHESIST`. |

---
*(End of Document — ChemLab: Origins Narrative & Quest Design Specification)*
