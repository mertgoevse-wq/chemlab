# ChemLab: Origins — Quest System Design Document

**Version:** 1.0  
**Status:** Pre-Production (Phase B Expansion)  
**Author:** Skills & Quests Design Lead  
**Source of Truth (Data-Driven Layer):** `design/gdd/data/quests.json`  
**Engine & Systems Reference:** `src/chemlab/skills/quest_engine.py`, `src/chemlab/world/procedural_labs.py`, `src/chemlab/simulation/total_syntheses.py`, `src/chemlab/simulation/precursor_synthesis.py`

---

## 1. Executive Summary & Vision Statement

The ChemLab quest system translates authentic scientific methodology and high-stakes chemical drama into structured gameplay. Instead of abstract "fetch and deliver" objectives, every quest in ChemLab is an authentic laboratory operation evaluated by real-time thermodynamic, kinetic, and analytical criteria.

Players progress from introductory benchtop techniques through complex multi-step organic total syntheses (inspired by literature from LambdaSyn, TiHKAL, and PiHKAL), forensic crime-scene reconstructions, and clandestine laboratory contracts in the Badlands. The quest loop rewards procedural precision, safety awareness (OSHA/GHS compliance), and stoichiometric mastery while penalizing carelessness with yield degradation, impurity byproducts, or catastrophic containment failures.

### Core Gameplay Pillars for Quests

1. **Physical & Chemical Verifiability:** Objectives evaluate real physical states (pH, temperature, mass, optical density, retention time, NMR peaks) produced by the Cantera, RDKit, and ODE kinetic solver engines.
2. **Zero Arbitrary Gating:** Quest availability flows strictly from player skill levels, safety history, equipment ownership, and faction reputation.
3. **Branching Outcomes via Product Quality:** Quests do not merely succeed or fail; they evaluate a continuous spectrum of purity (0–100%) and isolated yield (grams). High-purity products grant bonus reputation and elite unlocks; contaminated batches trigger reprimands, chemical disposal fees, or investigation flags.
4. **Data-Driven Architecture:** All quest configurations, prerequisite graphs, objective tolerances, and failure thresholds live in external JSON (`design/gdd/data/quests.json`) consumed by `QuestEngine` without hardcoded Python logic.

---

## 2. Quest Taxonomy & Archetypes

ChemLab classifies quests into five primary archetypes across the campaign and open-world procedural matrix:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CHEMLAB QUEST TAXONOMY                          │
├──────────────────┬─────────────────┬──────────────────┬────────────────┤
│ 1. Synthesis     │ 2. Clandestine  │ 3. Forensic      │ 4. Sandbox     │
│    Quests        │    Lab Quests   │    Investigation │    Challenges  │
├──────────────────┼─────────────────┼──────────────────┼────────────────┤
│ • API Total      │ • Precursor     │ • Crime Scene    │ • Extreme Env  │
│   Syntheses      │   Diversion     │   Processing     │   Physics      │
│ • LambdaSyn Org  │ • Improvisation │ • Chemical Spot  │ • Free Recipe  │
│ • Multi-Stage    │ • Badlands      │   Tests          │   Design       │
│   Recrystallize  │   Syndicate     │ • Instrumental   │ • Efficiency   │
│ • Titration/Assay│ • Low-Purity    │   Trace Matching │   Speedruns    │
│                  │   Contamination │ • Expert Witness │ • Zero-G       │
│                  │   Hazards       │   Certification  │   Fluidics     │
└──────────────────┴─────────────────┴──────────────────┴────────────────┘
```

### 2.1 Synthesis Quests (Preparative & Analytical)
Focused on pharmaceutical active ingredients (APIs), organic dyes, and analytical standards. Players execute authentic procedures: charging reagents, managing exotherms with cooling baths, refluxing under condensers, vacuum filtering on Büchner funnels, and recrystallizing to analytical purity.

### 2.2 Criminal-Lab Quests (Clandestine & Covert)
Operating in the unregulated Badlands and abandoned industrial zones. Players interact with covert operators and contraband chemists (`NPCRole.COVERT_OPERATOR`, `NPCRole.CONTRABAND_CHEMIST`), improvising apparatus with hardware store equipment, purifying diverted precursors, managing noxious off-gases without certified scrubbers, and balancing syndicate reputation against police detection.

### 2.3 Forensic Investigation Quests
Working with law enforcement, environmental agencies, and the Chief Medical Examiner. Players process simulated crime scenes, apply presumptive catalytic color tests (Luminol, Kastle-Meyer, Marquis), match ballistics striations, extract toxins from biological matrices via Solid-Phase Extraction (SPE), and analyze synthetic byproduct fingerprints to locate illicit production labs.

### 2.4 Sandbox-Mode Quests & Procedural Contracts
Freeform challenges generated dynamically by `ProceduralLabGenerator`. Tasks vary by regional archetype (Academic, Industrial Pharma, CRISPR Biotech, Orbital Zero-G, Extreme Planetary) with randomized target compounds, yield requirements, and environmental modifiers.

### 2.5 Narrative Campaign Quests (Story Acts I–V)
The pedagogical backbone following the player's journey at the Kavli-Helmholtz Institute for Advanced Chemical Synthesis (KHI-ACS), investigating Dr. Julian Voss's disappearance and uncovering *Project Athanor*.

---

## 3. Quantitative Prerequisites & Progression Gating

Quests use a multi-variable prerequisite validation system implemented in `Quest.is_unlocked()`:

```jsonc
{
  "prerequisites": {
    "completed_quests": ["q_synth_aspirin_01", "q_foren_scene_intro"],
    "required_skills": ["chemistry:25", "forensics:10", "engineering:15"],
    "min_safety_score": 85.0,
    "min_reputation": {
      "covert_syndicate": 40.0,
      "academic_faculty": 60.0
    },
    "required_apparatus": ["Büchner Funnel", "Liebig Condenser"],
    "required_lab_access": "Organic Synthesis Lab (North Bench)"
  }
}
```

### Prerequisite Evaluation Logic

1. **Dependency Graph (`completed_quests`):** Must be a strict subset of the player's completed quest history (`completed_quests.issubset(...)`).
2. **Multi-Skill Level Gating (`required_skills`):** Uses the `"skill_name:level"` format. Cross-track quests require balanced competency (e.g., clandestine synthesis requires both `chemistry:30` and `engineering:25`).
3. **Safety Score Multiplier (`min_safety_score`):** Evaluated against the player's rolling OSHA/ANSI safety index (0.0–100.0%). Reckless lab practice (fume hood violations, acid spills, runaway vessel pops) locks high-containment academic and industrial quests until safety remediation drills are completed.
4. **Faction Reputation Matrix (`min_reputation`):** Tracks trust thresholds across factions (Academic Faculty, Law Enforcement Forensics, Badlands Syndicate, Industrial Pharma Consortia). High academic standing locks out clandestine contracts, while syndicate trust unlocks black-market precursor routes.
5. **Hardware Readiness (`required_apparatus`):** Player must have unlocked and acquired the required glassware or analytical machinery.

---

## 4. Synthesis Quests Portfolio: PiHKAL / TiHKAL / LambdaSyn Style

Every synthesis quest in ChemLab reflects genuine organic reaction mechanisms, stoichiometry, and workup protocols documented in authoritative open literature (Vogel's Practical Organic Chemistry, LambdaSyn database, and Alexander Shulgin's synthetic methodology).

### 4.1 Master Synthesis Portfolio Table

| Quest ID | Target Molecule | Route Type / Mechanism | Literature Source | Required Chemistry Lvl | Target Purity | Min Yield | Exotherm Hazard |
|----------|-----------------|------------------------|-------------------|------------------------|---------------|-----------|-----------------|
| `q_synth_aspirin` | Acetylsalicylic Acid | O-Acylation of Salicylic Acid | LambdaSyn / Pharmacopeia | Level 5 | ≥ 95.0% | 12.0 g | Moderate (65°C water bath) |
| `q_synth_paracetamol` | 4-Acetamidophenol | Nucleophilic Acylation of 4-Aminophenol | LambdaSyn / Vogel | Level 15 | ≥ 98.0% | 8.5 g | Low (air oxidation tarring risk) |
| `q_synth_benzocaine` | Ethyl 4-aminobenzoate | Fischer Esterification of 4-Aminobenzoic Acid | Vogel / Organic Syntheses | Level 30 | ≥ 96.5% | 6.0 g | High (concentrated H2SO4 catalyst) |
| `q_synth_indigo` | Indigo Dye (Indigotin) | Baeyer-Drewson condensation | Classical Organic | Level 35 | ≥ 92.0% | 4.5 g | Rapid exothermic precipitation |
| `q_synth_caffeine` | 1,3,7-Trimethylxanthine | Liquid-Liquid Extraction & Sublimation | Natural Product Isolation | Level 45 | ≥ 99.0% | 1.8 g | Sublimation thermal control (178°C) |
| `q_synth_nitroethane` | Nitroethane | Victor Meyer nucleophilic substitution | Precursor Synthesis | Level 55 | ≥ 90.0% | 15.0 mL | High volatile organic vapor hazard |
| `q_synth_indole` | Indole Core | Fischer Indole Cyclization | TiHKAL / Heterocyclic Chem | Level 65 | ≥ 94.0% | 5.2 g | Extreme (Polyphosphoric acid, 180°C) |
| `q_synth_pihkal_step` | 2,5-Dimethoxy-β-nitrostyrene | Henry / Knoevenagel Condensation | PiHKAL Synthetic Route | Level 75 | ≥ 93.0% | 8.0 g | Severe (toxic amine catalyst reflux) |
| `q_synth_tihkal_step` | Tryptamine N-Methylation | Controlled Reductive Amination | TiHKAL Synthetic Route | Level 85 | ≥ 96.0% | 3.5 g | Extreme (Pyrophoric borohydride reductant) |

### 4.2 Detailed Quest Walkthrough: Quest `q_synth_aspirin`
- **Narrative Context:** Prof. Thorne assigns the Junior Fellow their first active pharmaceutical ingredient (API) synthesis to test reflux rigging and crystallization yield.
- **Stoichiometry:** $13.8\text{ g (0.100 mol) Salicylic Acid} + 14.2\text{ mL (0.150 mol) Acetic Anhydride} \xrightarrow{\text{5 drops } \text{H}_2\text{SO}_4} 18.02\text{ g Theoretical Aspirin}$.
- **Stage Objectives:**
  1. *Measurement:* Weigh $13.80\text{ g}\ (\pm 0.05\text{ g})$ salicylic acid on the analytical balance into a dry 125 mL Erlenmeyer flask.
  2. *Reagent Charging:* Dispense $14.2\text{ mL}\ (\pm 0.2\text{ mL})$ acetic anhydride and add 5 drops of concentrated sulfuric acid.
  3. *Thermal Reflux:* Heat in a $70\text{–}75^\circ\text{C}$ water bath for 15 minutes. Exceeding $85^\circ\text{C}$ triggers thermal decomposition.
  4. *Ice Bath Quenching:* Add $50\text{ mL}$ chilled distilled water to hydrolyze excess acetic anhydride. Rapidly chill to $0\text{–}5^\circ\text{C}$ to induce needle crystallization.
  5. *Vacuum Filtration & Washing:* Collect crystals on a Büchner funnel under aspirator vacuum. Wash cake with $15\text{ mL}$ ice-cold water.
  6. *Purity Assay:* Determine melting point ($135\text{–}136^\circ\text{C}$) and verify absence of purple color with $1\%\ \text{FeCl}_3$ phenol test.

---

## 5. Clandestine & Criminal-Lab Quests

Clandestine quests introduce moral ambiguity, legal tension, and improvised chemical engineering. They take place in covert cellars, abandoned container homes, or mobile trailers within the Badlands perimeter.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CLANDESTINE LAB HAZARD & RISK LOOP                   │
├────────────────────────────────────────────────────────────────────────┤
│  [Procure Precursor] ──► [Improvised Apparatus] ──► [Exothermic Run]   │
│          │                        │                         │          │
│   Diversion Flag           Glassware Stress           Vessel Rupture   │
│          ▼                        ▼                         ▼          │
│  [Police Detection]        [Toxic Vapor Leak]         [Explosion /     │
│  (+Suspicion Level)        (-Health / -Purity)         Syndicate Burn] │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.1 Faction Reputation Ladder
Player interactions with underworld NPCs (`NPCRole.COVERT_OPERATOR`, `CONTRABAND_CHEMIST`, `FACILITY_FIXER`) are governed by their numerical reputation index:

- **Hostile (0.0–19.9):** NPCs refuse trade, lock doors, and may tip off inspectors.
- **Suspicious (20.0–39.9):** Reagents sold at a 200% price surcharge; only primitive hardware store supplies accessible.
- **Neutral (40.0–59.9):** Standard clandestine missions available; access to basic diverted precursor batches.
- **Friendly (60.0–79.9):** Bulk reagent wholesale unlocked; customized glassware fabrication; safety raid early-warning tipoffs.
- **Trusted (80.0–100.0):** Master underground chemist status; access to secret high-yield synthesis routes, custom Schlenk manifolds, and syndicate laboratory automation skids.

### 5.2 Key Clandestine Quests

1. **`q_cland_precursor_01` — "The Hardware Store Synthesis"**
   - *Source NPC:* "Nails" Morau (`FACILITY_FIXER`), Rust Flat Garage.
   - *Task:* Synthesize benzaldehyde by oxidizing benzyl alcohol using pool chlorinating powder (calcium hypochlorite) and automotive vinegar under crude ice-bucket cooling.
   - *Improvised Gear:* Mason jar reaction vessel, aquarium tubing condenser, plastic funnel with coffee filter.
   - *Hazards:* Chlorine gas accumulation, runaway thermal boilover, sodium hypochlorite mist.

2. **`q_cland_byproduct_scrub` — "Odor Suppression Engineering"**
   - *Task:* Assemble a counter-flow activated charcoal scrubber with dry ice cold trap to neutralize volatile organic amines and mercaptan vapors before fumes escape into the surrounding settlement.
   - *Success Metric:* Ambient odor detection index $< 5\text{ ppm}$ at the exterior perimeter.

3. **`q_cland_purification_run` — "Acid-Base Partitioning"**
   - *Task:* Isolate crude freebase phenethylamine from an unrefined reaction sludge containing polymers and tar. Execute fractional liquid-liquid extraction between diethyl ether and dilute hydrochloric acid.
   - *Purity Hurdle:* Remove toxic organo-mercury or cyanoborohydride residues down to $< 10\text{ ppm}$.

---

## 6. Forensic Investigation Quests

Forensic quests reverse the synthesis process: players analyze degraded chemical traces, unknown powders, physiological samples, and ballistic impacts to reconstruct past events.

### 6.1 Investigation Workflow Pipeline

```
[Crime Scene Cordon] ──► [Latent Trace Detection] ──► [Presumptive Spot Test]
         │                          │                            │
  Spatial Mapping             UV Photomacrography        Marquis / Luminol
         ▼                          ▼                            ▼
[Chain-of-Custody Log] ◄── [Instrumental Analysis] ◄── [SPE Sample Clean-Up]
                            (GC-MS / Raman / FTIR)
```

### 6.2 Key Forensic Quests

1. **`q_foren_scene_luminol` — "Echoes in the Darkroom"**
   - *Setting:* Abandoned research bay with suspected chemical spill and blood contamination.
   - *Objective 1:* Darken the room ($< 2\text{ lux}$ ambient illumination).
   - *Objective 2:* Prepare alkaline luminol reagent ($0.1\text{ g}$ luminol $+ 5.0\text{ g}\ \text{Na}_2\text{CO}_3 + 15\text{ mL}\ 3\%\ \text{H}_2\text{O}_2$ in $100\text{ mL}$ water).
   - *Objective 3:* Spray suspect vertical partition; photograph 430 nm chemiluminescent glow with 30-second camera exposure.
   - *Objective 4:* Discriminate false positive: apply potassium ferricyanide control vs bleach residue discrimination protocol.

2. **`q_foren_tox_overdose` — "The Poisoned Titration"**
   - *Setting:* Forensic Toxicology Core.
   - *Task:* Identify an unknown lethal adulterant in a beverage vial recovered from a deceased researcher's desk.
   - *Method:* Solid-Phase Extraction (SPE C18) followed by HPLC-DAD retention time and UV spectral library matching against cyanide, strychnine, and methanol.

3. **`q_foren_cland_fingerprint` — "The Signature Impurity"**
   - *Setting:* Seized Badlands clandestine lab apparatus.
   - *Task:* Analyze residual crust from a 5-liter three-neck round-bottom flask. Perform GC-MS quadrupole scan.
   - *Challenge:* Detect trace ketone condensation byproducts characteristic of the Leuckart route vs reductive amination, matching the exact synthetic signature to a suspect syndicate supplier.

---

## 7. Quest Evaluation Engine, Purity/Yield Thresholds & Failure Conditions

Objectives and failures evaluate dynamically every simulation tick through `QuestObjective.evaluate()` and `FailureCondition.check()`.

### 7.1 Quantitative Evaluation Modes

```python
class EvaluationMode(StrEnum):
    EQUIPMENT_STATE   = "EQUIPMENT_STATE"    # Switch positions, valve alignment, tare status
    METROLOGY_VALUE   = "METROLOGY_VALUE"    # pH, mass, volume, temperature within tolerance
    CHEMICAL_REACTION = "CHEMICAL_REACTION"  # Target product formed by kinetic solver
    SAFETY_COMPLIANCE = "SAFETY_COMPLIANCE"  # Rolling safety score >= target
    SPECTRAL_MATCH    = "SPECTRAL_MATCH"     # UV-Vis lambda_max, GC-MS fragmentation pattern
    SKILL_LEVEL       = "SKILL_LEVEL"        # Discipline level attainment
```

### 7.2 Failure Condition Severity Matrix

| Severity Level | Game Consequence | Trigger Example | Narrative Outcome |
|----------------|------------------|-----------------|-------------------|
| `WARNING` | Audio cue, safety score deduction (-5 to -10%), HUD banner | Sash raised above aerodynamic limit while boiling volatiles | Dr. Vance delivers verbal reprimand via intercom. |
| `SCORE_PENALTY` | Permanent safety index deduction (-20%), forfeit bonus XP | Incompatible waste disposal (acid into cyanide sink) | Safety violation filed on player record; disposal fees assessed. |
| `INSTANT_FAIL_EXPLOSION` | Lab glassware shatters, toxic cloud disperses, quest immediately resets | Exothermic runaway overpressure in a sealed vessel without pressure relief | Blast shield cracks, emergency sirens blare, immediate emergency room revival. |
| `CONTAINMENT_LOCKDOWN` | Airlocks seal, decontamination halon/purge triggers, laboratory quarantined | Toxic gas generation outside fume hood ($\text{HCN}, \text{CO}, \text{Cl}_2 > \text{IDLH}$) | Full hazmat response team clears bay; player locked out for 5 in-game minutes. |

### 7.3 Continuous Purity & Yield Scoring Formula

Final quest grade is calculated continuously upon product submission:

$$\text{Final Score} = \left(0.6 \times \frac{\text{Actual Purity}}{\text{Target Purity}}\right) + \left(0.4 \times \frac{\text{Actual Yield}}{\text{Theoretical Yield}}\right) \times \left(\frac{\text{Safety Score}}{100}\right)$$

- $\text{Purity} < \text{Objective Threshold}$: Quest fails with product rejection.
- $\text{Score} \ge 1.0$: *Exemplary Distinction* (granting 1.5× bonus skill XP and rare reagent drops).

---

## 8. Reward Economics, Reputation Gains & Cross-System Dispatch

Upon successful quest completion, `QuestEngine._complete_quest()` coordinates cross-system state updates:

```
[Quest Completed]
       │
       ├──► Dispatch Skill XP ────► [SkillManager.add_xp()] ──► Check Level-Up / Milestones
       ├──► Unlock Reagents/Gear ─► [PlayerInventory / Node Unlocks]
       ├──► Adjust Factions ──────► [NPC.adjust_reputation() across regional hubs]
       └──► Persist Save State ───► [SaveManager.save_to_disk()]
```

### 8.1 Reward Structure Schema
Each quest entry specifies discrete and composite rewards:

```jsonc
{
  "rewards": {
    "skill_xp": {
      "chemistry": 2500,
      "engineering": 1000,
      "forensics": 500
    },
    "reputation_deltas": {
      "academic_faculty": +15.0,
      "badlands_syndicate": -5.0
    },
    "unlocked_apparatus": ["HPLC-DAD System", "Porcelain Contrast Tile"],
    "unlocked_reagents": ["aniline", "o_nitrobenzaldehyde"],
    "academic_credential": "KHI-ACS Advanced Preparative Synthesis Certification",
    "credits": 750.0
  }
}
```

### 8.2 Save Game & Runtime Serialization
Runtime quest states are serialized into `user://chemlab_save.json` via `QuestEngine.to_dict()` and `from_dict()`:

```jsonc
{
  "completed_quests": ["q_titration_01", "q_synth_aspirin"],
  "quests": [
    {
      "quest_id": "q_synth_aspirin",
      "act": 1,
      "title": "Synthesis of Acetylsalicylic Acid",
      "status": "completed",
      "completed_objectives": ["obj_weigh", "obj_heat", "obj_crystallize", "obj_filter"],
      "current_objective_idx": 4
    }
  ]
}
```

This guarantees 100% roundtrip persistence across desktop sessions, headless CI runs, and Godot 4 save/load cycles without state loss.
