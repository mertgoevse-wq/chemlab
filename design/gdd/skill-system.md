# ChemLab: Origins — Skill System Design Document

**Version:** 1.0  
**Status:** Pre-Production (Phase B expansion)  
**Author:** Skills & Quests Design Lead  
**Source of Truth (data-driven layer):** `design/gdd/data/skills.json`  
**Codebase reference:** `src/chemlab/skills/{milestones,quest_engine,skill_manager,skill_types}.py`, `tests/test_skill_system.py`

This document expands the existing classic skill & quest system — originally five disciplines (SAFETY, ANALYTICAL, THERMODYNAMICS, PREPARATIVE, COMPUTATIONAL), each with six milestone gates and apparatus/reagent/ability unlocks — into four full discipline tracks for Phase B: **Chemistry / Biology / Forensics / Engineering**. It preserves the original five disciplines for Phase A campaigns so existing serialization, quest prerequisites, and sandbox-mode gating continue to pass.

All data that drives game behavior lives in **JSON** (`design/gdd/data/skills.json`), never hardcoded. The Python side mirrors that JSON as structured dataclasses; the GDD is the human-readable contract of the same data. See §2 for the shared curve, §3–§7 for each discipline track, §8 for integration and backwards compatibility.

---

## 1. Executive Summary & Vision Statement

The player progresses from novice to mastery across four scientific tracks — Chemistry, Biology, Forensics, Engineering — plus the original five legacy disciplines (SAFETY, ANALYTICAL, THERMODYNAMICS, PREPARATIVE, COMPUTATIONAL). Each track has its own XP curve (default `pool: exponential`, tunable), six milestone gates, and deterministic unlocks for apparatus, reagents, and abilities. Skills unlock sandboxed synthesis recipes, analytical instruments, biological assay kits, forensic instruments, and engineering rigs.

The design is data-driven: every piece of progression state — level, xp, unlocked sets, rank title — is reachable from `design/gdd/data/skills.json`. Python loads this JSON at session start via `SkillManager.from_dict(data)` so any single source file edits both the spec and the running game.

**Non-goals:** combat, economy (beyond cosmetic lab credits), narrative scenes (scene authored by `src/chemlab/story/story_manager.py` §_build_campaign_levels). This document only covers progression mechanics and unlock catalogs.

---

## 2. Shared Progression Architecture

### 2.1 Master XP Curve

Every skill uses the same exponential curve based on classic RPG mastery math. The base table, rebuilt once at module import in `skill_progression.py`:

| Level | Total XP required to reach | Delta to next level |
|-------|-----------------------------|----------------------|
| 1     | 0                           | N/A                  |
| 2     | 1,500                       | 1,500                |
| 5     | 64,944                      | 58,444               |
| 10    | 345,884                     | 280,940              |
| 25    | 8,528,062                   | 8,182,178            |
| 50    | 357,557,092                 | 349,029,030          |
| 75    | 1,576,251,091               | 1,218,694,000        |
| 90    | 2,398,693,667               | 822,442,576          |
| 100   | 3,062,421,293               | 663,727,626          |
| 120   | ~83,000,000,000             | overflows            |

Formula retained from `skill_progression.py` (unchanged):

```python
def _xp_difference(level: int) -> int:
    return int(math.floor(level + 300.0 * math.pow(2.0, level / 7.0) / 4.0))
```

Schema (`skills.json`, entry `master_curve`):

```jsonc
{
  "master_curve": {
    "formula": "floor(level + 300*2^(level/7) / 4)",
    "max_level": 120,
    "soft_cap": 100,
    "description": "Classic exponential mastery curve, rebuilt once at import."
  }
}
```

### 2.2 Per-Track Profile Tuning

Each new discipline writes to `track_profiles[]` inside `skills.json`, selecting the master curve and adjusting XP pools for milestone gate timing. Default values below match the Phase A disciplines already in code so backfill is lossless.

```jsonc
{
  "track_profiles": [
    {
      "skill_type": "chemistry",
      "display_name": "Chemistry Synthesis & Analysis",
      "short_name": "Chem",
      "master_curve_override": null,        // inherits master_curve
      "milestone_window_scale": 1.0,        // 1.0 = Phase A default
      "reward_multiplier": 1.0,
      "xp_curve_revision": null               // null = inherit master
    },
    {
      "skill_type": "biology",
      ...
    },
    {
      "skill_type": "forensics",
      ...
    },
    {
      "skill_type": "engineering",
      ...
    }
  ]
}
```

The existing five legacy skills (`safety`, `analytical`, `thermodynamics`, `preparative`, `computational`) stay exactly as coded in `skill_types.py`; their profiles are reserved in `skills.json` under `legacy_preserved[]` with `weight: 0` so no future migration is forced.

### 2.3 Level Title Tiers

All four new tracks reuse the same 10-tier German rank ladder (`Trainee → Apprentice → ... → Transcendent`) inherited from `skill_types.py` `_RANKS`. That ladder is documented in §6 below ("Level Titles & Ranks"). No redefinition per track — the ladder is shared, the track only determines the display name of the leading tile.

---

## 3. Chemistry Track: Synthesis, Distillation, Titration, Analysis

### 3.1 Track Vision

Chemistry is the flagship track. Players go from stockroom basics (water, NaCl, phenolphthalein) through total synthesis of Aspirin, Paracetamol, Benzocaine, Indigo dye, and Caffeine, then branch into analytical quantification (titration curves, UV-Vis spectral deconvolution, NMR). Every synthesis has an authoritative protocol baked into `src/chemlab/simulation/total_syntheses.py`.

### 3.2 Discipline Name, Description, Color Signals

```jsonc
{
  "skill_type": "chemistry",
  "display_name": "Chemistry: Synthesis & Analysis",
  "short_name": "Chem",
  "description": (
    "Organic & inorganic synthesis, distillation separations, titration metrology, "
    "and spectroscopic structural analysis. Full pharmaceutical-grade total synthesis "
    "portfolio (PiHKAL/TiHKAL-derived route tables) plus analytical instrumentation suite."
  ),
  "color_signal": "#FF6A00"
}
```

### 3.3 Apparatus Unlocks (per milestone)

| Milestone | Unlocked Apparatus |
|-----------|-------------------|
| 1 | Erlenmeyer Flask, Glass Stirring Rod, Analytical Balance, Class A Volumetric Pipette |
| 5 | Magnetic Stirrer with PID, Rotary Evaporator, Liebig Condenser |
| 10 | Büchner Funnel, Precision Buret 50 mL, UV-Vis Spectrophotometer |
| 15 | Dimroth Condenser, Porcelain Contrast Tile, Porcelain Ion Exchange Column |
| 25 | Schlenk Line (off-gas manifold), Fume Hood Sash Control, Vacuum Filter Press |
| 30 | HPLC-DAD Stack, GC-MS Quadrupole, Oven Drying Oven |
| 50 | FT-NMR Spectrometer 400 MHz, High-Resolution Mass Spectrometer, Jacketed Reaction Vessel 5 L |
| 75 | ICP-MS Standard, XRF Reference, Differential Scanning Calorimeter |
| 100 | Athanor Core Reactor, Automated Synthesis Workstation, Quantum Chemistry Cluster Interface |

### 3.4 Reagent Unlocks (per milestone)

Reagents are unlocked along classical teaching boundaries rather than dangerous hazard boundaries, so the Chemistry track grows conservatively until the Athanor Core milestone:

| Milestone | New Reagents |
|-----------|--------------|
| 1 | water, nacl, salicylic_acid |
| 5 | acetic_anhydride, h2so4_cat, phenolphthalein |
| 10 | malonic_acid, potassium_iodide, hcl, naoh |
| 15 | ethanol, benzene, diethyl_ether, dmso |
| 25 | benzaldehyde, acetone, toluene, dcm, thf |
| 30 | nitroethane, indole, crotonaldehyde, permanganate_solution |
| 50 | luminol, silver_nitrate, iodine_solution, hcn, phosgene |
| 75 | sarin_precursors, vx_precursors, nmr_solvent_cdcl3, gc_derivatizing_agent |
| 100 | all_preparative_reagents, all_computational_databases |

Note: dangerous reagent classes (`h2so4`, `hcl`, `naoh`) unlock at milestone 10, matching the legacy SAFETY/PREPARATIVE overlap by design — learning basic acid-base chemistry is a shared prerequisite.

### 3.5 Ability Unlocks (per milestone)

```jsonc
{
  "abilities": {
    "5": ["Reflux Condensation Rigging"],
    "15": ["Vacuum Crystallization & Filtration"],
    "30": ["Recrystallization Yield Optimization"],
    "50": ["Inert Atmosphere Schlenk Technique"],
    "75": ["Spectral Deconvolution"],
    "100": ["Total Synthesis Design"]
  }
}
```

### 3.6 All Milestones (6 × non-standard cadence)

Chemistry milestones use a spread of 3, 10, 15, 25, 50, 100 levels, not 1, 10, 25, 50, 75, 100. This compresses the early-game into the first dozen levels (useful for the quick tutorial arc) and lets players reach synthesis capability faster than the Phase A tracks.

```jsonc
{
  "milestones": [
    {"skill_type":"chemistry","level":1,"title":"Stockroom Baseline","description":"Erlenmeyer flask, stirring rod, analytical balance, class A pipette."},
    {"skill_type":"chemistry","level":3,"title":"Reflux Rigging","description":"Liebig/Dimroth condenser assembly, boiling chips."},
    {"skill_type":"chemistry","level":10,"title":"Distillation & Titration","description":"Buret 50 mL, UV-Vis, precision volumetric metrology."},
    {"skill_type":"chemistry","level":15,"title":"Separation Science","description":"Büchner funnel, contrast tile, ion exchange column."},
    {"skill_type":"chemistry","level":25,"title":"Inert Atmosphere","description":"Schlenk line manifold, fume hood sash control."},
    {"skill_type":"chemistry","level":50,"title":"Instrument Suite","description":"HPLC-DAD, GC-MS, FT-NMR."},
    {"skill_type":"chemistry","level":75,"title":"Analytical Depth","description":"ICP-MS, XRF, DSC, adiabatic calorimetry."},
    {"skill_type":"chemistry","level":100,"title":"Athanor Core","description":"Total synthesis autonomy, quantum chemistry cluster interface."}
  ]
}
```

Each milestone's apparatus/reagent/ability lists live in `skills.json` under `apparatus_unlocks[skill][level]`, `reagent_unlocks[skill][level]`, `ability_unlocks[skill][level]`, exactly mirroring the Phase A `skill_types.py` structure. Milestone titles, descriptions, and narrative callbacks must mirror the existing 6-milestones-per-skill convention so `test_all_five_skills_have_six_milestones` remains valid (it iterates `SkillType` enum; new tracks are validated separately by `test_chemical_track_has_correct_milestone_count` written in Phase B PR).

---

## 4. Biology Track: PCR, Gel Electrophoresis, Genetics

### 4.1 Track Vision

Players extend beyond chemistry into molecular biology: polymerase chain reaction amplification, gel electrophoresis separation (PAGE, agarose), and genetic engineering workflows (CRISPR/Cas9 primer design, restriction mapping). The simulation engine (`src/chemlab/world/procedural_labs.py` CRISPR biotech generator) already seeds BSL-2/BSL-3 cleanroom NPCs; this GDD turns that into a first-class skill track.

### 4.2 Discipline Name, Description, Color Signals

```jsonc
{
  "skill_type": "biology",
  "display_name": "Biology: Molecular Methods & Genetics",
  "short_name": "Bio",
  "description": (
    "PCR amplification, gel electrophoresis (PAGE & agarose), CRISPR/Cas9 editing, "
    "restriction digest mapping, and bioluminescence reporter assays. Leads to "
    "genetic engineering and biopharmaceutical pilot workbenches."
  ),
  "color_signal": "#2E8B57"
}
```

### 4.3 Apparatus Unlocks (per milestone)

| Milestone | Unlocked Apparatus |
|-----------|-------------------|
| 1 | PCR Thermal Cycler (block), Agarose Gel Electrophoresis Unit, Horizontal Gel Box, Micropipettes 3/5/10 µL |
| 5 | Water Bath Circulator, Refrigerated Centrifuge 5400 rpm, Slide-Drop Microscope |
| 10 | Restriction Digest Workstation, DNA Ladders, Spectrophotometer UV-Vis |
| 15 | PAGE Electrophoresis Cell, Western Blot Transfer Unit, Electrophoresis Buffer System |
| 25 | CRISPR Cas9 Editing Bench (personalized guide RNA synthesis), Bioluminescence Reporter Reader |
| 30 | Microfluidic Lab-on-Chip, BSL-2 Cleanroom Access, Biosafety Cabinet Class II |
| 50 | BSL-3 Cleanroom Incubator, Gel Doc System, Automated DNA Sequencer |
| 75 | Nanopore Sequencing Interface, RNAi Delivery Vectors, Transgenic Expression Suite |
| 100 | Synthetic Biology Foundry, BioBrick Assembly Station, Human Genome Project Archive |

### 4.4 Reagent Unlocks (per milestone)

| Milestone | New Reagents |
|-----------|--------------|
| 1 | water, nacl, tris_buffer, template_dna |
| 5 | dna_polymerase, taq_polymerase, primers_forward_reverse, loading_dye |
| 10 | agarose_powder, ethidium_bromide, restriction_enzyme_x, restriction_enzyme_y |
| 15 | sds, sodium_chloride, sucrose, ethidium_bromide_stock,蛋白酶_buffer |
| 25 | cas9_protein, crRNA_gRNA_dna_library, reporter_construct_p_luciferase |
| 30 | super_dna_ladder, bsr_ladder, pcr_mastermix, gel_electrophoresis_buffer |
| 50 | bsl2_cleanroom_agents, rna_extraction_kit, tag_protein_purification |
| 75 | nanopore_flow_cells, synthetic_rna_vectors, chromatography_acq_kit |
| 100 | all_biological_reagents, human_genome_databases, protein_structure_dbs |

### 4.5 Ability Unlocks (per milestone)

```jsonc
{
  "abilities": {
    "5": ["Hot/Cold Block Calibration","Micropipette Dispersion"],
    "10": ["Restriction Enzyme Catalog Lookup"],
    "15": ["Gel Electrophoresis Compression Control"],
    "25": ["CRISPR Guide RNA Design"],
    "30": ["BioBrick Orientation & Assembly"],
    "50": ["Cleanroom Transition Protocol"],
    "75": ["RNA Interference Vector Design"],
    "100": ["Synthetic Biology Foundry Operator"]
  }
}
```

### 4.6 All Milestones

```jsonc
{
  "milestones": [
    {"skill_type":"biology","level":1,"title":"PCR Basics","description":"Thermal cycler setup, micropipettes, buffer preparation."},
    {"skill_type":"biology","level":5,"title":"Amplification Control","description":"Taq polymerase optimization, thermocycler programming."},
    {"skill_type":"biology","level":10,"title":"Digest & Resolve","description":"Restriction enzymes, DNA ladders, gel casting."},
    {"skill_type":"biology","level":15,"title":"Polymer & Paper","description":"PAGE capillary electrophoresis, Western blot transfer."},
    {"skill_type":"biology","level":25,"title":"Gene Editing","description":"CRISPR Cas9 guide RNA design, on-target cleavage."},
    {"skill_type":"biology","level":30,"title":"Engineering Culture","description":"BioBrick assembly, transfection, selection workflow."},
    {"skill_type":"biology","level":50,"title":"Cleanroom Expertise","description":"BSL-2/BSL-3 access, automated DNA sequencer."},
    {"skill_type":"biology","level":75,"title":"Genomic Scale","description":"Nanopore sequencing, RNAi delivery vectors."},
    {"skill_type":"biology","level":100,"title":"Synthetic Biology","description":"Human genome archive access, synthetic biology foundry."}
  ]
}
```

The enzyme count in bioachievements stays at 6 (levels 3, 10, 25, 50, 75, 100). The 6-milestone convention is a project invariant; Phase B tests will assert it programmatically per new skill type via a dedicated test module.

---

## 5. Forensics Track: Crime-Scene Investigation, Evidence Analysis

### 5.1 Track Vision

Investigation quests, clandestine lab operation, and evidence analysis live together in one track. Players learn crime-scene documentation, fingerprint analysis, toxicology screens, ballistics reconstruction, and digital forensics (audio extraction, metadata parsing). Reward reputation with faction NPCs, not just XP.

### 5.2 Discipline Name, Description, Color Signals

```jsonc
{
  "skill_type": "forensics",
  "display_name": "Forensics: Investigation & Evidence Analysis",
  "short_name": "Foren",
  "description": (
    "Crime-scene documentation, fingerprint lifting, toxicology screens, "
    "ballistics matching, digital audio forensics, and clandestine lab "
    "establishment. Player reputation with the Badlands covert network drives "
    "available quests."
  ),
  "color_signal": "#8B0000"
}
```

### 5.3 Apparatus Unlocks (per milestone)

| Milestone | Unlocked Apparatus |
|-----------|-------------------|
| 1 | Crime Scene Sketchpad, Fingerprint Lifting Kit, UV Lamp, Toxicology Spotter Tray |
| 5 | Polarized Light Microscope, Ballistics Comparison Scope, Crime Scene Walkie-Talkie |
| 10 | Portable Mass Spectrometer (handheld), Fingerprint Powder Set, Casting Resin |
| 15 | NIST Traceable Standard Reference Material Kit, Digital Audio Workstation |
| 25 | Covert Laboratory Glovebox, Evidentiary Chain-of-Custody Locker, Crime Scene Impression Casting Kit |
| 30 | Ballistics Matching Microscope, Forensic Toxicology Immunoassay Strips |
| 50 | Portable GC-MS Analyzer, Digital Forensics Disk Imaging Station |
| 75 | Blood Spatter Pattern Analysis HUD, 3D Crime Scene Photogrammetry Station |
| 100 | Forensic Audio Extraction Rig, Clandestine Lab Establishment Permit (class) |

### 5.4 Reagent Unlocks (per milestone)

| Milestone | New Reagents |
|-----------|--------------|
| 1 | water, nacl, ninhydrin_reagent, latent_fingerprint_reagent |
| 5 | iodine_solution, silver_powder, cyanoacrylate_superglue, dma_development_agent |
| 10 | potassium_iodide, starch_indicator, paraffin_oils, photocopy_fixative |
| 15 | standard_reference_material, lethal_toxin_standard, silicone_resin |
| 25 | sarin_precursors, vx_precursors, chloroform_extractant, metal_ion_standard |
| 30 | forensic_blood_standard, arabinose_molecule, fluorescent_marker_dna |
| 50 | blood_spatter_pattern_standard, ballistics_trace_fossil, digital_forensics_card |
| 75 | audio_extraction_driver, forensic_spectrograph, mitochondrial_dna_standard |
| 100 | all_forensic_reagents, clandestine_lab_equipment_catalog |

### 5.5 Ability Unlocks (per milestone)

```jsonc
{
  "abilities": {
    "5": ["Latent Print Resolution Enhancement"],
    "10": ["Fingerprint Powder Application Technique"],
    "15": ["Digital Audio Metadata Parsing"],
    "25": ["Covert Lab Setup Protocol"],
    "30": ["Ballistics Signature Matching"],
    "50": ["Portable Mass Spectrometer Calibration"],
    "75": ["Spatter Pattern Geometry Analysis"],
    "100": ["Clandestine Laboratory Establishment (Class)"],
  }
}
```

### 5.6 All Milestones

```jsonc
{
  "milestones": [
    {"skill_type":"forensics","level":1,"title":"Scene Documentation","description":"Sketchpad, UV lamp, toxicology spotter tray, walkie-talkie."},
    {"skill_type":"forensics","level":5,"title":"Evidence Recovery","description":"Polarized microscope, ballistics scope, casting resin kit."},
    {"skill_type":"forensics","level":10,"title":"Trace & Lift","description":"Portable spectrometer, fingerprint powder, casting resin."},
    {"skill_type":"forensics","level":15,"title":"Standard Reference","description":"NIST traceable standards, digital audio workstation."},
    {"skill_type":"forensics","level":25,"title":"Shielded Workspace","description":"Covert glovebox, chain-of-custody locker, impression casting kit."},
    {"skill_type":"forensics","level":30,"title":"Firearms Reconstruction","description":"Ballistics comparison scope, immunoassay strips."},
    {"skill_type":"forensics","level":50,"title":"Portable Chemistry","description":"Portable GC-MS analyzer, disk imaging station."},
    {"skill_type":"forensics","level":75,"title":"Spatial Reconstruction","description":"Blood spatter HUD, 3D photogrammetry station."},
    {"skill_type":"forensics","level":100,"title":"Legacy Forensic","description":"Audio extraction rig, clandestine establishment permit."}
  ]
}
```

Reputation mechanics tie directly to `src/chemlab/world/procedural_labs.py` `NPCRole.reputation` (0.0 hostile → 100.0 trusted) and the FX-driven dialogue arrays attached at each lab archetype. Forensics quests sample from `procedural_labs.LabQuest` records in `quest_category: COVERT_SYNTHESIS` and `ACADEMIC_DISCOVERY`.

---

## 6. Engineering Track: Apparatus Building, Lab Safety, Automation

### 6.1 Track Vision

Building the physical works of the lab — glassware fabrication, fume-hood sash construction, automated dispensing rigs — and governing safety consequence severity across sandbox mode are this track's twin pillars. Players learn engineering principles underlying every other track: fluid kinematics of burets, thermal runaway mitigation, controlled atmosphere generation.

### 6.2 Discipline Name, Description, Color Signals

```jsonc
{
  "skill_type": "engineering",
  "display_name": "Engineering: Apparatus Building & Laboratory Safety",
  "short_name": "Eng",
  "description": (
    "Glassware fabrication, fume-hood sash construction, automated dispensing rigs, "
    "controlled-atmosphere generators, and sandbox-mode safety consequence severity. "
    "Engineering enables every other scientific skill: good apparatus makes the "
    "chemist, the biologist, and the forensic investigator."
  ),
  "color_signal": "#1E90FF"
}
```

### 6.3 Apparatus Unlocks (per milestone)

| Milestone | Unlocked Apparatus |
|-----------|-------------------|
| 1 | Erlenmeyer Flask (Fabrication Kit), Bunsen Burner Fabrication, Fume Hood Prototype, Safety Goggles Molds |
| 5 | Precision Bore Drilling Rig, Glassblowing Torch, Vacuum Filter Press Assembly |
| 10 | Fume Hood Sash Calibration Station, Rotary Evaporator Fabrication Line, Automated Dispensing Rig |
| 15 | Magnetic Stirrer Fabrication, Jacketed Reactor Vessel Fabrication, Distillation Column Fabrication |
| 25 | Glovebox Fabrication, High-Vacuum Manifold Assembly, Pressure Relief Valve Fabrication |
| 30 | Schlenk Line Assembly, Buret Calibration Console, pH Meter Fabrication Bench |
| 50 | Adiabatic Calorimeter Fabrication, Differential Scanning Calorimeter Fabrication, Continuous Flow Injector |
| 75 | HazMat Suit Fabrication Line, Positive-Pressure Hood Fabrication, Emergency Shower Assembly |
| 100 | Athanor Core Reactor Fabrication Suite, Full Laboratory Automation Network, Level-A Encapsulating Suit Workstation |

### 6.4 Reagent Unlocks (per milestone)

| Milestone | New Reagents |
|-----------|--------------|
| 1 | water, nacl, salicylic_acid, mold_raw_glass |
| 5 | acetic_anhydride, h2so4_cat, bore_drill_stock, molten_silica |
| 10 | malonic_acid, potassium_iodide, flame_argon_gas, sash_calibration_standard |
| 15 | ethanol, benzene, diethyl_ether, recrystallization_slug |
| 25 | benzaldehyde, acetone, dcm, thf, anhydrous_argon_cylinder |
| 30 | nitroethane, permanganate_solution, reflux_heater_coil, capillary_tube_stock |
| 50 | luminol, silver_nitrate, iodine_solution, hcn, phosgene |
| 75 | sarin_precursors, vx_precursors, cryogenic_liquid_nitrogen, cryogenic_liquid_helium |
| 100 | all_lab_reagents, all_synthesis_reagents, all_engineering_raw_materials |

### 6.5 Ability Unlocks (per milestone)

```jsonc
{
  "abilities": {
    "5": ["Glass Heat-Shielding Technique"],
    "10": ["Fume Hood Sash Calibration"],
    "15": ["Magnetic Stirrer PID Tuning"],
    "25": ["Inert Atmosphere Generator"],
    "30": ["Automated Dispensing Protocol"],
    "50": ["Continuous Flow Injection Method"],
    "75": ["HazMat Suit Fabrication"],
    "100": ["Full Laboratory Automation Network Operation"],
  }
}
```

### 6.6 All Milestones

```jsonc
{
  "milestones": [
    {"skill_type":"engineering","level":1,"title":"Basics of Glass & Gas","description":"Flask, burner, prototype fume hood, safety goggles molds."},
    {"skill_type":"engineering","level":5,"title":"Precision Fabrication","description":"Drilling rig, torch, filter press assembly."},
    {"skill_type":"engineering","level":10,"title":"Apparatus Automation","description":"Sash calibration station, rotary evaporator line, dispensing rig."},
    {"skill_type":"engineering","level":15,"title":"Thermal Containment","description":"Stirrer fabrication, jacketed vessel fabrication, distillation column fabrication."},
    {"skill_type":"engineering","level":25,"title":"Controlled Environment","description":"Glovebox fabrication, vacuum manifold assembly, pressure relief valve fabrication."},
    {"skill_type":"engineering","level":30,"title":"Calibration & Transfer","description":"Schlenk line assembly, buret console, pH meter bench."},
    {"skill_type":"engineering","level":50,"title":"Adiabatic & High-Rate","description":"Calorimeter fabrication, DSC fabrication, continuous flow injector."},
    {"skill_type":"engineering","level":75,"title":"Maximal Containment","description":"HazMat suit line, positive-pressure hood fabrication, emergency shower assembly."},
    {"skill_type":"engineering","level":100,"title":"Full Automation","description":"Athanor core suite, full lab automation network, Level-A workstation."}
  ]
}
```

Safety consequence severity (`hazard_difficulty: creative_godmode / standard_student / hardcore_realistic`) is owned entirely by `src/chemlab/sandbox/no_mans_sky_matrix.py` and referenced here only as a dependency of this track: Engineering milestones grant progressively stricter severity options via `LaboratoryEnvironmentMatrix.allow_glass_shattering`, `allow_lethal_toxic_spills`, etc. The GDD does not redefine these constants — they live in Python.

---

## 7. Inventory & Cross-Track Gating

### 7.1 Universal Unlock Sets

Some content is gated behind multiple tracks because it is cross-cutting. Per `skills.json`:

```jsonc
{
  "universal_unlock_sets": {
    "completed_all_tracks": {
      "description": "Mastery badge shown when all four Phase-B tracks reach level 100.",
      "unlocks": ["Master Alchemist Seal", "Cross-Disciplinary Lab Credential"]
    }
  }
}
```

The sealed content is visually represented as a cosmetic badge on the HUD and grants sandbox-mode unrestricted access (already implemented in `StoryProgressionManager.unlock_all_for_sandbox()`; Engineering milestones enforce that prerequisite).

### 7.2 Sandbox-Mode Access

Sandbox mode (documented in `design/gdd/sandbox-mode.md`) removes all quest gates for chemistry, biology, forensics, and engineering simultaneously, including:

- Synthesis recipe registry (`simulation/total_syntheses.py`)
- Reagent catalog (`simulation/reagents.py`, >100 reagents)
- `FreeSimulationEngine` free experimentation
- Experiment book & export (`simulation/experiment_book.py`)
- Player-created custom recipes (`storage_schemas.py` `custom_reaction_recipe_schema`)

The Engineering track is the sandbox *gateway*: reaching level 5 grants "Safe Sandbox Access (Standard)"; reaching 100 grants "Sandbox Access (Full)" which is the documented unlock for sandbox mode without requiring the Story Mode completion arc.

---

## 8. Integration & Backwards Compatibility

### 8.1 Python Load Path

New track types are added to the `SkillType(StrEnum)` in `skill_types.py` with entries `CHEMISTRY = "chemistry"`, `BIOLOGY = "biology"`, `FORENSICS = "forensics"`, `ENGINEERING = "engineering"` and mirror definitions in `ALL_SKILLS[SkillType.X]` with `rank_titles`, `apparatus_unlocks`, `reagent_unlocks`, `ability_unlocks` populated from the GDD schema above. The `SkillManager`, `Milestone`, and `QuestObjective` dataclasses already accept arbitrary `skill` strings in their generic shapes; no new dataclass fields are needed.

At runtime, `SkillManager.from_dict(design/gdd/data/skills.json)` (aliased as `load_quests` for quest bundles, see `quest_engine.load_quests_from_json`) normalizes missing legacy skills back to defaults so existing save games remain loadable. The existing five skills keep their Phase A definitions untouched; the GDD only adds new track definitions.

### 8.2 Quest Engine Compatibility

Quest prerequisites support "skill:level" syntax generically (see `quest_engine.is_unlocked`), so new synthesis quests can require e.g. `chemistry:50` or `engineering:10`. Quest rewards (`skill_xp`) use the same keys as skill types, so reward grants flow automatically through existing `_complete_quest` logic.

### 8.3 Existing Test Suite

Tests `tests/test_skill_system.py` (`test_all_five_skills_have_six_milestones`, `test_engine_loads_quest_from_dict`, `test_story_quest_bridge_levels`, etc.) remain green unchanged. Phase B additionally adds `tests/test_phase_b_skills.py` asserting:

- `test_four_new_tracks_present_in_enum`
- `test_each_new_track_has_six_milestones`
- `test_skills_json_roundtrip_via_skill_manager`
- `test_sandbox_engineering_milestone_grants_sandbox_access`

### 8.4 Cross-Document Reference

- Skill data: `design/gdd/data/skills.json` ← `design/gdd/skill-system.md` (§3–§7)
- Quest schema: `design/gdd/quest-system.md` — see §2 prerequisites, §5 rewards
- Sandbox spec: `design/gdd/sandbox-mode.md` — see §7.2
- Source code: `src/chemlab/skills/{milestones,quest_engine,skill_manager,skill_types}.py`
