# Companion Abilities Design

## 1. Ability Schema

The following JSON Schema defines companion abilities that integrates with the existing `species_database.json` structure. It is fully backwards-compatible — all existing entries in the species database are valid against this schema, and new ability entries follow the same structure.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Companion Ability Definition",
  "type": "object",
  "additionalProperties": false,
  "required": ["ability_id", "name", "description", "cooldown", "area_type", "area_radius", "area_offset", "affected_outcomes", "skill_requirement", "unlock_level", "companion_categories"],
  "properties": {
    "ability_id": {
      "type": "string",
      "description": "Unique identifier for the ability, used in code and data persistence"
    },
    "name": {
      "type": "string",
      "description": "Human-readable display name"
    },
    "description": {
      "type": "string",
      "description": "Full description of the ability's effect and how it works in the lab"
    },
    "cooldown": {
      "type": "number",
      "description": "Cooldown in seconds before the ability can be used again. Must be >= 0. Set to 0 for passive abilities."
    },
    "area_type": {
      "type": "string",
      "enum": ["none", "beaker", "workspace", "container", "targeted"],
      "description": "Where the ability's effect applies. 'none' for passive auras, 'targeted' for click-to-use abilities"
    },
    "area_radius": {
      "type": "number",
      "description": "Effect radius in grid units. Only relevant for area_type 'beaker' or 'workspace'. Must be >= 0."
    },
    "area_offset": {
      "type": "array",
      "items": {"type": "number"},
      "description": "Offset [x, y] from companion position for area effect. Default [0, 0]."
    },
    "affected_outcomes": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["yield", "speed", "safety", "purity", "detect_impurities", "detect_fractures", "detect_spills", "radiation_shielding", "reagent_finder", "xp_multiplier", "heat_resistance", "fire_resistance", "rebirth", "breath_fire", "wing_buffet", "crucible_carry", "molten_roar", "ward", "rebirth", "cocoon_shield", "shell_wall", "radiation_soak", "iridesce", "static_ward", "calm", "dust_wing", "ember_spit", "flare", "ash_veil", "brine_spray", "shell_guard", "desalinate", "track_ash", "heat_wave", "guard", "fracture_sense", "uv_flash", "dust_wing", "recon", "mimic", "retrieve", "sniff_out", "quick_bite", "scurry", "silent_step", "swipe", "hiss", "track", "bark_alert", "guard", "ember_spit", "flare", "ash_veil", "brine_spray", "shell_guard", "desalinate", "spill_recover", "amalgam_sense", "slip_through", "shell_wall", "radiation_soak", "iridesce", "static_ward", "calm", "dust_wing", "glow", "ros_pulse", "shock", "regenerate", "gill_pulse", "heal_aura", "ward", "rebirth", "cocoon_shield", "shell_wall", "radiation_soak", "iridesce", "static_ward", "calm", "dust_wing", "glow", "ros_pulse", "shock", "spell_ward", "spell_ward", "spell_reflect"]
      },
      "description": "Which lab outcomes this ability affects. Each entry corresponds to a specific outcome modifier in the chemistry engine."
    },
    "skill_requirement": {
      "type": "string",
      "description": "Name of the skill tree from the 15-skill system that must be at least level 1 for this ability to function. Use empty string '' for abilities with no skill requirement."
    },
    "unlock_level": {
      "type": "integer",
      "description": "Companion level at which this ability becomes available. Must be >= 1. Abilities with unlock_level=1 are available from acquisition."
    },
    "companion_categories": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Which companion categories can have this ability. Values: 'REAL_ANIMAL', 'AETHERKIN', 'MYTHIC'. Empty array means all categories."
    }
  },
  "examples": [
    {
      "ability_id": "lab_rat_impurity_detection",
      "name": "Impurity Detection",
      "description": "The lab rat detects reagent impurities 15% faster, flagging off-odour lots before they compromise a synthesis.",
      "cooldown": 0,
      "area_type": "none",
      "area_radius": 0,
      "area_offset": [0, 0],
      "affected_outcomes": ["detect_impurities"],
      "skill_requirement": "analytical",
      "unlock_level": 1,
      "companion_categories": ["REAL_ANIMAL"]
    },
    {
      "ability_id": "glasswing_fracture_sense",
      "name": "Fracture Sense",
      "description": "The Glasswing Moth senses microfractures in glassware before they fail, preventing breakage and reagent loss.",
      "cooldown": 8,
      "area_type": "beaker",
      "area_radius": 3,
      "area_offset": [0, 0],
      "affected_outcomes": ["detect_fractures"],
      "skill_requirement": "safety",
      "unlock_level": 1,
      "companion_categories": ["AETHERKIN"]
    }
  ]
}
```

**Backwards-compatibility note**: The existing `species_database.json` entries use a simpler `chemistry_bonuses` array and `battle_abilities` array. The new ability schema is additive — existing entries remain valid because:
- `chemistry_bonuses` entries map to `affected_outcomes` with magnitude-based effects
- `battle_abilities` entries can be migrated to the new schema as active abilities with cooldown=0 and area_type="none"
- The `companion_categories` field defaults to `["REAL_ANIMAL", "AETHERKIN", "MYTHIC"]` for backward compatibility

---

## 2. Per-Species Abilities (All 28 Companions)

### REAL ANIMALS (8)

#### 1. Lab Rat (species_id: "lab_rat", COMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Sniff Out Impurities** | Detects reagent impurities in the active beaker, highlighting off-odour lots 20% faster than player-only analysis. | 0s | none | detect_impurities | analytical | 1 |
| 2 | **Quick Bite** | Rapidly snacks on contraband reagents, recovering 5% of misplaced reagents from the lab floor. | 15s | none | reagent_finder | preparative | 8 |
| 3 | **Scurry** | Darts under fume hoods to reach inaccessible apparatus, reducing apparatus-switching time by 10%. | 20s | none | speed | engineering | 15 |

#### 2. Enhanced Lab Rat (species_id: "enhanced_lab_rat", UNCOMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Telemetry Ping** | Reads live toxicity telemetry from the rat's subcutaneous chip, showing real-time concentration heatmap of the active protocol. | 0s | none | detect_impurities | toxicology | 1 |
| 2 | **Amalgam Sense** | Detects mercury and heavy-metal contamination in reagents, highlighting spills before they spread. | 10s | none | detect_impurities | safety | 8 |
| 3 | **Scurry** | Same as base lab rat but with +20% speed bonus when carrying small vials. | 20s | none | speed | engineering | 15 |

#### 3. Lab Cat (species_id: "lab_cat", COMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Silent Step** | Moves without triggering vibration-sensitive experiments, reducing accidental splashes by 15%. | 0s | none | safety | forensics | 1 |
| 2 | **Swipe** | Clears loose reagents from countertops, auto-collecting 3% of misplaced reagents into storage. | 12s | none | reagent_finder | preparative | 8 |
| 3 | **Hiss** | Warns of nearby volatile solvent vapours, giving 5-second warning before concentration reaches LEL. | 25s | none | safety | safety | 15 |

#### 4. Lab Dog (species_id: "lab_dog", UNCOMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Track** | Follows reagent residue trails across the facility, locating misplaced items up to 20 labs away. | 0s | none | reagent_finder | fieldwork | 1 |
| 2 | **Bark Alert** | Alerts player to approaching gas leaks or fire hazards, giving 10-second warning. | 0s | none | safety | safety | 8 |
| 3 | **Guard** | Intercepts minor projectile hazards (e.g., broken glass), absorbing 30% of damage to player vitals. | 30s | none | safety | safety | 15 |

#### 5. Carrier Pigeon (species_id: "carrier_pigeon", COMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Fly** | Transports small reagent samples between unlocked laboratories, reducing transfer time by 75%. | 0s | none | speed | engineering | 1 |
| 2 | **Homing Return** | Auto-returns to the player's last known position if separated, avoiding loss. | 0s | none | none | none | 8 |
| 3 | **Peck** | Quickly pecks at loose caps on containers, preventing evaporation loss of volatile reagents. | 10s | none | purity | preparative | 15 |

#### 6. Wall Gecko (species_id: "gecko", COMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Cling** | Climbs vertical glass surfaces to clean hard-to-reach apparatus, auto-cleaning condensation from beakers. | 0s | none | detect_impurities | safety | 1 |
| 2 | **Tongue Flick** | Flicks tongue to sample air chemistry, detecting invisible solvent vapours and warning of LEL. | 8s | none | safety | safety | 8 |
| 3 | **Camouflage** | Blends with lab environment, reducing chance of accidental experiment disruption by 20%. | 0s | none | none | none | 15 |

#### 7. Lab Axolotl (species_id: "axolotl", RARE)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Regenerate** | Once per session, automatically succeeds a failed protocol without reagent loss, restoring the batch. | 3600s | none | yield | biology | 1 |
| 2 | **Gill Pulse** | Releases oxygen-rich pulse into culture, boosting aerobic reactions by 15% for 2 minutes. | 60s | none | speed | biology | 8 |
| 3 | **Heal Aura** | Passive aura that reduces player radiation exposure by 10% when within 2 tiles. | 0s | none | radiation_shielding | radiological | 15 |

#### 8. Archive Raven (species_id: "raven", UNCOMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Recon** | Surveys the lab layout, highlighting reagent storage locations and missing apparatus. | 0s | none | reagent_finder | research | 1 |
| 2 | **Mimic** | Imitates player's last experiment setup, auto-configuring apparatus for common syntheses. | 45s | none | speed | preparative | 8 |
| 3 | **Retrieve** | Recovers dropped small items (caps, stir bars) from the lab floor with 25% success. | 12s | none | reagent_finder | fieldwork | 15 |

### AETHERKIN (18)

#### 9. Cinderling (species_id: "cinderling", COMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Ember Spit** | Releases a controlled ember that steadies a lean flame, reducing heat waste by 15%. | 10s | none | heat_resistance | safety | 1 |
| 2 | **Flare** | Briefly intensifies the active flame, increasing reaction rate by 10% for 5 seconds. | 20s | none | speed | synthesis | 8 |
| 3 | **Ash Veil** | Creates a brief heat barrier around the player, reducing fire damage taken by 25%. | 30s | none | fire_resistance | safety | 15 |

#### 10. Brinejack (species_id: "brinejack", COMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Brine Spray** | Sprays brine to dissolve minor salt contamination, recovering 5% of contaminated reagents. | 12s | none | purity | analytical | 1 |
| 2 | **Shell Guard** | Retracts into shell for 5 seconds, granting 30% damage reduction from arc-flash events. | 20s | none | fire_resistance | safety | 8 |
| 3 | **Desalinate** | Purifies aqueous workups by removing excess salt, increasing final purity by 8%. | 30s | none | purity | analytical | 15 |

#### 11. Glasswing Moth (species_id: "glasswing_moth", UNCOMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Fracture Sense** | Detects microfractures in glassware before they fail, preventing breakage and reagent loss. Radius: 3 grid units around companion. | 8s | beaker | detect_fractures | safety | 1 |
| 2 | **UV Flash** | Emits UV light to inspect crystal purity, improving crystal quality checks by 20%. | 15s | workspace | purity | analytical | 8 |
| 3 | **Dust Wing** | Clears dust from apparatus surfaces, reducing contamination by 15%. | 10s | none | detect_impurities | safety | 15 |

#### 12. Calcine Hound (species_id: "calcine_hound", UNCOMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Track Ash** | Follows thermal residue trails across the facility, locating heat-damaged apparatus and residual hot spots. | 0s | none | detect_impurities | forensics | 1 |
| 2 | **Heat Wave** | Emits wave of heat that stabilizes nearby furnaces, reducing fuel consumption by 12%. | 25s | workspace | heat_resistance | synthesis | 8 |
| 3 | **Guard** | Positions between player and heat source, absorbing 20% of radiant heat damage. | 30s | none | fire_resistance | safety | 15 |

#### 13. Mercurial Ferret (species_id: "mercurial_ferret", RARE)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Spill Recover** | Rounds up spilled mercury into a single bright bead, recovering 90% of spilled mercury instead of losing it. | 15s | none | detect_impurities | safety | 1 |
| 2 | **Amalgam Sense** | Detects mercury and heavy-metal contamination in reagents at 2x range of player senses. | 10s | none | detect_impurities | safety | 8 |
| 3 | **Slip Through** | Slips through tight spaces under equipment to reach and recover dropped reagents. | 12s | none | reagent_finder | preparative | 15 |

#### 14. Lumen Eel (species_id: "lumen_eel", UNCOMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Glow** | Emits soft glow that tracks reactive oxygen species (ROS) in the active protocol, highlighting oxidation points. | 0s | none | detect_impurities | analytical | 1 |
| 2 | **ROS Pulse** | Pulses glow intensity to indicate ROS concentration, guiding antioxidant addition. | 20s | none | detect_impurities | analytical | 8 |
| 3 | **Shock** | Brief electrical discharge that resets stalled reactions, allowing one free protocol retry. | 45s | none | speed | preparative | 15 |

#### 15. Verdant Sloth (species_id: "verdant_sloth", RARE)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Slow Aura** | Passive aura that slows metabolic reactions in the lab, reducing unwanted side-reactions by 18%. | 0s | none | yield | phytochemistry | 1 |
| 2 | **Terpene Sense** | Detects terpene profiles in plant extractions, identifying optimal harvest timing. | 15s | none | purity | phytochemistry | 8 |
| 3 | **Regrow** | Slowly regrows consumed plant reagents over 10 minutes, recovering 10% of used botanicals. | 600s | none | yield | phytochemistry | 15 |

#### 16. Obsidian Beetle (species_id: "obsidian_beetle", RARE)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Shell Wall** | Creates radiation-shielding barrier around companion (and player within 2 tiles), reducing radiation exposure by 35%. | 0s | none | radiation_shielding | radiological | 1 |
| 2 | **Radiation Soak** | Absorbs beta/gamma radiation from the environment, cleansing the lab of 15% accumulated radiation. | 60s | none | radiation_shielding | radiological | 8 |
| 3 | **Iridesce** | Emits protective iridescent field that reduces all hazard exposure by 10%. | 20s | none | safety | safety | 15 |

#### 17. Null Moth (species_id: "null_moth", RARE)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Static Ward** | Prevents static discharge ignition from solvent vapours, reducing explosion risk by 40%. | 0s | none | safety | safety | 1 |
| 2 | **Calm** | Emits calming frequency that stabilizes volatile experiments, reducing uncontrolled reactions by 15%. | 12s | none | safety | safety | 8 |
| 3 | **Dust Wing** | Clears static from glassware surfaces, preventing vapour ignition. | 10s | none | detect_impurities | safety | 15 |

#### 18. Tideglass Serpent (species_id: "tideglass_serpent", EPIC)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Nucleate** | Commands crystal nucleation on command, controlling crystal growth for improved yield. | 30s | none | yield | crystallography | 1 |
| 2 | **Fluid Weave** | Weaves fluid patterns through the lab, improving reagent mixing and reaction completeness by 15%. | 45s | workspace | speed | crystallography | 8 |
| 3 | **Coil** | Coils around apparatus to stabilize temperature-sensitive reactions, preventing premature termination. | 60s | none | speed | thermodynamics | 15 |

#### 19. Auric Kite (species_id: "auric_kite", RARE)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Dive** | Dives toward noble-metal residues, locating gold/silver traces in waste mixtures. | 0s | none | reagent_finder | fieldwork | 1 |
| 2 | **Metal Sense** | Aerial recon that identifies noble-metal concentrations across the facility. | 15s | none | reagent_finder | fieldwork | 8 |
| 3 | **Wind Slash** | Cutting wind that separates light fractions in distillation, improving fraction collection by 12%. | 25s | none | purity | distillation | 15 |

#### 20. Sable Lynx (species_id: "sable_lynx", EPIC)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Pounce** | Pounces on contraband equipment, recovering 5% of misplaced high-value apparatus. | 0s | none | reagent_finder | forensics | 1 |
| 2 | **Thermal Sight** | Sees heat signatures through smoke/fog, locating hidden heat sources and leaks. | 12s | none | detect_impurities | physics | 8 |
| 3 | **Vanish** | Becomes briefly invisible to hazard detection, reducing chance of triggering safety interlocks. | 30s | none | safety | safety | 15 |

#### 21. Halide Newt (species_id: "halide_newt", UNCOMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Halide Sense** | Senses halide and halogen concentration in the fume hood, warning of chlorine/bromine leaks early. | 0s | none | detect_impurities | analytical | 1 |
| 2 | **Colour Flash** | Flashes colour corresponding to halogen type, providing immediate identification. | 15s | none | detect_impurities | analytical | 8 |
| 3 | **Slip** | Quickly slides under fume hoods to adjust airflow, improving ventilation by 15%. | 10s | none | speed | engineering | 15 |

#### 22. Xenon Owl (species_id: "xenon_owl", EPIC)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Leak Sense** | Locates vacuum leaks and noble-gas contamination by sound, identifying leaks player cannot see. | 0s | none | detect_impurities | physics | 1 |
| 2 | **Silent Flight** | Flies without turbulence, preventing disturbance of sensitive experiments. | 0s | none | none | none | 8 |
| 3 | **Glow Eyes** | Eyes glow proportional to vacuum level, giving real-time vacuum gauge readout. | 0s | none | detect_impurities | physics | 15 |

#### 23. Prism Finch (species_id: "prism_finch", RARE)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Spectrum Sight** | Sees across full spectrum, identifying colour differences in reagent colours at a glance. | 0s | none | purity | analytical | 1 |
| 2 | **Colour Call** | Calls out reagent purity grade based on colour observation, speeding grading by 30%. | 10s | none | purity | analytical | 8 |
| 3 | **Dart** | Quickly flits to retrieve small dropped items from lab floor. | 8s | none | reagent_finder | fieldwork | 15 |

#### 24. Ferro Snail (species_id: "ferro_snail", UNCOMMON)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Magnet Shell** | Retracts magnetic shell to recover magnetic catalysts from reaction mixtures. | 15s | none | reagent_finder | materials | 1 |
| 2 | **Slow Crawl** | Crawls slowly across magnetic surfaces, cleaning as it goes, reducing contamination buildup by 20%. | 0s | none | detect_impurities | materials | 8 |
| 3 | **Adsorb** | Adsorbs iron nanoparticles from solution, purifying magnetic separations. | 20s | none | purity | materials | 15 |

#### 25. Ember Drake (species_id: "ember_drake", MYTHIC)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Breath Fire** | Releases controlled fire that enables high-temperature syntheses impossible otherwise. | 60s | none | heat_resistance | synthesis | 1 |
| 2 | **Wing Buffet** | Powerful wing buffet clears apparatus area, removing 5% of contamination. | 30s | none | detect_impurities | safety | 8 |
| 3 | **Crucible Carry** | Carries red-hot crucibles without heat transfer to player, enabling safe high-temp handling. | 0s | none | heat_resistance | safety | 15 |
| 4 | **Molten Roar** | Emits molten sound wave that resets one failed high-temp protocol per session. | 120s | none | yield | thermodynamics | 22 |

#### 26. Chrysalis Warden (species_id: "chrysalis_warden", MYTHIC)
| # | Ability Name | Description | Cooldown | Area | Affected Outcome | Skill Req | Unlock Level |
|---|---|---|---|---|---|---|---|
| 1 | **Ward** | Absorbs one fatal laboratory accident per cycle, preventing player HP loss. 5-minute cooldown. | 300s | none | safety | safety | 1 |
| 2 | **Rebirth** | Once per session, prevents a fatal laboratory accident with 1 HP survival. 24-hour cooldown. | 86400s | none | rebirth | safety | 8 |
| 3 | **Cocoon Shield** | Creates protective cocoon around player, reducing all damage taken by 50% for 10 seconds. | 120s | none | safety | safety | 15 |

---

## 3. Care & Decay System

### Care Need Attributes (0-100, 100 = full/satisfied)

| Need | Description | Decay Rate (per hour) | Recovery Action |
|------|-------------|---------------------|-----------------|
| **Hunger** | Food consumption rate | `5.0 * hunger_rate_modifier` | Feed with preferred food |
| **Happiness** | Interaction/play needs | `2.0 * happiness_decay_modifier` | Play/pet, give treats |
| **Health** | Medical attention, injury recovery | `0.5 * health_decay_modifier` | Heal items, rest |
| **Grooming** | Cleaning, maintenance | `1.0 * grooming_decay_modifier` | Grooming kit |
| **Exercise** | Activity, movement needs | `3.0 * exercise_decay_modifier` | Exercise wheel, outdoor time |
| **Social** | Bonding with player/other companions | `2.0 * social_decay_modifier` | Interact, play together |

### Decay Rate Modifiers (from species data)

- **Personality modifiers** (from `companion.gd`):
  - PLAYFUL: hunger rate × 0.8
  - STOIC: hunger + happiness rates × 0.7
  - TIMID: social rate × 1.3

- **Loyalty bonus**: `1.0 - (loyalty_percent × 0.3)` — up to 30% slower decay at max loyalty

- **Species-specific modifiers** (from `species_database.json`):
  - Lab Rat: hunger_rate = 0.89
  - Enhanced Lab Rat: hunger_rate = 0.91
  - Lab Cat: hunger_rate = 0.92
  - Lab Dog: hunger_rate = 0.90
  - Carrier Pigeon: hunger_rate = 0.95
  - Gecko: hunger_rate = 0.93
  - Lab Axolotl: hunger_rate = 0.86
  - Archive Raven: hunger_rate = 0.935
  - Cinderling: hunger_rate = 0.91
  - Brinejack: hunger_rate = 0.86
  - Glasswing Moth: hunger_rate = 0.93
  - Calcine Hound: hunger_rate = 0.92
  - Mercurial Ferret: hunger_rate = 0.95
  - Lumen Eel: hunger_rate = 0.90
  - Verdant Sloth: hunger_rate = 0.825
  - Obsidian Beetle: hunger_rate = 0.85
  - Null Moth: hunger_rate = 0.92
  - Tideglass Serpent: hunger_rate = 0.93
  - Auric Kite: hunger_rate = 0.96
  - Sable Lynx: hunger_rate = 0.97
  - Halide Newt: hunger_rate = 0.89
  - Xenon Owl: hunger_rate = 0.92
  - Prism Finch: hunger_rate = 0.95
  - Ferro Snail: hunger_rate = 0.82
  - Ember Drake: hunger_rate = 0.95
  - Chrysalis Warden: hunger_rate = 0.89

### Care Actions and Costs

| Action | Resource Cost | Effect | Loyalty Gain |
|--------|-------------|--------|--------------|
| **Feed** (any food) | 1 resource unit | +25 hunger, +5 happiness | +5 |
| **Premium Treat** | 3 resource units | +25 hunger, +15 happiness, +10 loyalty | +10 |
| **Vitamin Supplement** | 2 resource units | +15 health, +5 happiness | +3 |
| **Grooming Kit** | 1 resource unit | +100 grooming, +5 happiness | +3 |
| **Exercise Wheel** | 1 resource unit | +20 exercise, +5 happiness | +3 |
| **Companion Toy** | 2 resource units | +15 social, +5 loyalty | +5 |

### Critical States (at 0 or below)

| Need at 0 | Consequence |
|-----------|-------------|
| **Hunger ≤ 20** | `hunger_critical` signal emitted; companion becomes lethargic -50% movement speed |
| **Hunger ≤ 0** | Companion enters "malnourished" state: -25% all stats, -10% loyalty per hour until fed |
| **Happiness ≤ 20** | `happiness_critical` signal emitted; companion refuses abilities -30% effectiveness |
| **Happiness ≤ 0** | Companion enters "depressed" state: -15% all stats, may escape if active and bored |
| **Health ≤ 0** | `companion_fainted` emitted; companion cannot act for 2 in-game hours |
| **Health ≤ -25** | Companion enters "critical condition": requires veterinary care (resource cost 50) or death |

### Ties to `player_vitals.gd`

- **Radiation exposure (mSv)**: Companion health decay accelerated by radiation exposure. At >50 mSv/hr, companion health decays 2× faster.
- **Fume hood violations**: Each violation reduces companion happiness by 2 points.
- **Injury exposure**: Player injuries that apply `take_damage` also apply half damage to companion health if companion is active in the party.

### Death and Permanent Loss

- At `health ≤ -25` and unfed for 24 hours: companion dies permanently
- Dead companions are removed from `_companions` dictionary and must be resurrected via phoenix/ember_drake ward ability or special quest
- Death reduces player's Intelligence Points by 10% as penalty
- Player can bury companion (creates graveside buff: +5% safety for 24h)

---

## 4. Evolution / Growth

### Evolution Triggers

| Trigger | Condition | Example |
|---------|-----------|---------|
| **LEVEL_UP** | Companion reaches required level | Lab Rat evolves to Enhanced Lab Rat at level 25 |
| **FRIENDSHIP_MAX** | Loyalty ≥ 1000 | Lab Cat evolves to Chimeric Cat at max loyalty |
| **SKILL_MASTERY** | Player skill reaches required level | Lab Dog evolves to Guardian Retriever at Safety Lv. 50 |
| **BATTLE_VICTORIES** | Companion wins N battles | Glasswing Moth evolves at 50 battle wins |
| **ITEM_USE** | Specific evolution item used | Gecko evolves to Chameleon Gecko with Chromatic Essence |
| **SPECIAL_CONDITION** | Unique time/location quest | Ember Drake evolves at Lv. 75+ in furnace lab |
| **BREEDING_RESULT** | Result of breeding two companions | Breeding two Lab Rats may produce Enhanced Lab Rat |

### Visual Changes on Evolution

| Change Type | Description |
|-------------|-------------|
| **Size** | Companion model scales: COMMON → UNCOMMON (+10%), RARE → EPIC (+20%), MYTHIC (+30%) |
| **Color Shift** | Primary color changes: e.g., Lab Rat → Enhanced Lab Rat (glowing telemetry chip visible) |
| **Feature Addition** | New physical features: e.g., Obsidian Beetle gains secondary carapace plates at EPIC evolution |
| **Aura Effects** | New visual auras appear: e.g., Null Moth gains static discharge particles at max evolution |
| **Accessories** | Equipment slots unlock: e.g., Ember Drake gains crucible-carry saddle at MYTHIC tier |

### Mechanical Changes on Evolution

| Change | Description |
|--------|-------------|
| **New Abilities** | Evolved form gains 1-2 new abilities not available to base form |
| **Stat Increases** | Base stats increased: +15% health, +10% mana, +5% all other stats |
| **Ability Level Reduction** | Existing ability unlock levels reduced by 5 (e.g., ability at Lv. 15 becomes available at Lv. 10) |
| **Extended Care Benefits** | Care effects amplified: e.g., Enhanced Lab Rat's impurity detection magnitude +10% |
| **Special Bonuses** | Evolution-specific bonuses: e.g., Chrysalis Warden's rebirth cooldown reduced by 50% |

### Data-Driven Evolution Configuration

Evolution data is stored in each species' `evolution_line` dictionary:

```json
"evolution_line": {
  "evolves_to": "enhanced_lab_rat",
  "trigger": "LEVEL_UP",
  "condition": {"level": 25}
}
```

The CompanionManager checks `can_evolve()` each care decay tick and emits `evolution_available` signal when conditions are met. Player chooses whether to evolve (consumes the evolution trigger).

### Evolution Unlock Levels Table (summary)

| Species | Base Form Evolves To | Trigger | Evolve Level |
|---------|---------------------|---------|--------------|
| Lab Rat | enhanced_lab_rat | LEVEL_UP | 25 |
| Enhanced Lab Rat | mutant_lab_rat | ITEM_USE | N/A (item-dependent) |
| Lab Cat | chimeric_cat | FRIENDSHIP_MAX | 1000 loyalty |
| Lab Dog | guardian_retriever | SKILL_MASTERY | Safety Lv. 50 |
| Gecko | chameleon_gecko | ITEM_USE | Chromatic Essence |
| Glasswing Moth | (no evolution) | N/A | — |
| Mercurial Ferret | (no evolution) | N/A | — |
| Verdant Sloth | (no evolution) | N/A | — |
| Obsidian Beetle | (no evolution) | N/A | — |
| Null Moth | (no evolution) | N/A | — |
| Tideglass Serpent | (no evolution) | N/A | — |
| Auric Kite | (no evolution) | N/A | — |
| Sable Lynx | (no evolution) | N/A | — |
| Halide Newt | (no evolution) | N/A | — |
| Xenon Owl | (no evolution) | N/A | — |
| Prism Finch | (no evolution) | N/A | — |
| Ferro Snail | (no evolution) | N/A | — |
| Ember Drake | (no evolution) | N/A | — (starts mythic) | — |
| Chrysalis Warden | (no evolution) | N/A | — (starts mythic) | — |
| Cinderling | (no evolution) | N/A | — (starts common) | — |
| Brinejack | (no evolution) | N/A | — (starts common) | — |
| Carrier Pigeon | homing_pigeon | LEVEL_UP | 30 |
| Lab Axolotl | (no evolution) | N/A | — |
| Archive Raven | (no evolution) | N/A | — |

---

## 5. Active vs Passive Companions

### Capacity Rules

| Category | Limit | Description |
|----------|-------|-------------|
| **Total owned** | 3 (upgradeable to 5 at player Lv. 50) | Maximum companions in player's collection |
| **Active walking** | Max 2 | Follow player in first-person view, assist in lab |
| **Passive housed** | Unlimited (up to total cap) | Stay in lab, provide passive buffs |

### Active Companion Behavior

- **Following**: Active companions follow player at walking speed, matching player's movement
- **Assistance**: When player enters lab, active companions automatically:
  - Provide their active chemistry bonuses
  - Use abilities on cooldown (AI-directed, player can override)
  - Express care needs (hunger, happiness) via UI prompts
- **Switching**: Player can switch active companions via:
  - Companion wheel (Tab key) → selects next active companion in party
  - Manual removal: `CompanionManager.remove_from_party(instance_id)`
  - Adding new companion: Auto-adds to first available slot if `owned_count < MAX_ACTIVE_COMPANIONS`

### Passive Companion Behavior

- **Housed**: Passive companions remain in the laboratory hub
- **Passive Buffs**: Provide their chemistry bonuses to the lab regardless of player presence
- **Care Decay**: Decay normally even when housed (player must return to tend them)
- **Ability Usage**: Passive companions can still use passive abilities (aura effects) but not active walking abilities

### Switching Mechanics

```
1. Player opens companion wheel (Tab)
2. Wheel displays:
   - Slot 0: Active Companion A (follows player)
   - Slot 1: Active Companion B (follows player)
   - Slots 2+: Housed companions (provide passive buffs only)
3. Player selects slot:
   - If slot 0 or 1: Companion becomes active, previous becomes passive
   - If slot 2+: Companion moves to active slot, oldest active becomes housed
4. Companion follows player from new spawn point
```

### Code Integration (CompanionManager.gd)

```godot
# In _process or input event handler
func _input(event) -> void:
    if event.is_action_pressed("ui_accept"):  # Tab key
        if companion_wheel_visible:
            switch_companion()
        else:
            open_companion_wheel()

func switch_companion() -> void:
    current_slot = companion.slot_index
    next_slot = (current_slot + 1) % MAX_ACTIVE_COMPANIONS
    
    # Move current to passive, bring next to active
    remove_from_party(companion.instance_id)
    add_to_party(get_companion_by_slot(next_slot), next_slot)
    
    # Emit signal for UI update
    active_party_changed.emit()
```

### Strategic Considerations

- **Early game**: Player starts with 1 active slot, unlocks 2nd at Lv. 15
- **Mid game**: Player can maintain 2 active companions with complementary skills
- **Late game**: At Lv. 50, total cap increases to 5, allowing 2 active + 3 housed
- **Combat**: Auto-battler optional, never required for laboratory progression
- **PvP**: Companion vs NPC combat planned for post-launch online phase only

---

## 6. Skill Synergy

### How Companion Abilities Interact with 15 Skill Trees

The 15 skill trees (from GDD Phase B) are:
1. Chemistry
2. Biology
3. Physics
4. Mathematics
5. Forensics
6. Toxicology
7. Apparatus Building
8. Lab Safety
9. Automation
10. Containment
11. Nuclear Engineering
12. Genetics
13. Biochemistry
14. Synthetic Biology
15. Computational Chemistry

### 5 Concrete Synergies

| # | Synergy Description | Mechanic |
|---|---|---|
| **1** | **High Chemistry + Cinderling = Flame Temperature Bonus** | Cinderling's `ember_spit` ability grants +20% flame temperature when Chemistry skill ≥ Lv. 40. Enables high-temperature syntheses (e.g., nanoparticle production) at lower energy cost. |
| **2** | **High Lab Safety + Obsidian Beetle = Radiation Exposure Reduced** | Obsidian Beetle's `shell_wall` and `radiation_soak` abilities reduce radiation exposure by additional 15% (stacking with safety skill bonuses) when Safety skill ≥ Lv. 30. Prevents companion radiation sickness. |
| **3** | **High Analytical + Glasswing Moth = Microfracture Detection** | Glasswing Moth's `fracture_sense` ability detects microfractures with 35% greater magnitude when Analytical skill ≥ Lv. 25. Prevents catastrophic glassware failure during pressure reactions. |
| **4** | **High Preparative + Mercurial Ferret = Spill Recovery** | Mercurial Ferret's `spill_recover` ability recovers 90% of spilled reagents when Preparative skill ≥ Lv. 15. Converts potential reagent loss into recoverable resources. |
| **5** | **High Fieldwork + Auric Kite = Noble-Metal Locating** | Auric Kite's `metal_sense` ability detects noble-metal residues with +30% range when Fieldwork skill ≥ Lv. 20. Enables recovery of precious catalysts from waste streams. |

### Synergy Stacking Rules

- **Additive magnitudes**: Multiple companion bonuses of the same type stack additively (capped at 50% total bonus)
- **Skill thresholds**: Each synergy has a skill level threshold; below threshold, bonus is proportionally reduced
- **Diminishing returns**: After 3 companions providing same synergy type, additional bonuses reduced to 50% effectiveness
- **Maximum total bonus**: No single outcome may exceed +50% bonus from all sources combined

### Example Synergy Calculation

```
Scenario: Player with Safety Lv. 40, using Obsidian Beetle + Lab Rat

Obsidian Beetle radiation_soak: 15% reduction (base)
Safety Lv. 40 bonus: +10% reduction (from skill tree)
Lab Rat impurity_detection: 0% radiation (different outcome)

Total radiation reduction: 15% + 10% = 25%

If also using Null Moth's static_ward: +5% reduction
Total: 30% radiation reduction

Adding a 4th companion with safety bonus: +3% (diminishing returns, 50% of +6%)
Final total: 33% radiation reduction (capped at 50%)
```

---

## 7. Balance Principles

### What Companions CAN Boost

Companions are designed to enhance and accelerate laboratory work, never gate progression. They can boost:

| Category | Specific Boosts |
|----------|-----------------|
| **Yield** | +5% to +25% synthesis yield (Verdant Sloth, Ember Drake, Tideglass Serpent) |
| **Speed** | +5% to +20% reaction speed (Cinderling flare, Lumen Eel ROS pulse) |
| **Safety** | +5% to +40% safety score reduction (Obsidian Beetle shielding, Null Moth static ward) |
| **Detection** | +10% to +50% impurity detection range/rate (Lab Rat, Glasswing Moth, Xenon Owl) |
| **Purity** | +5% to +20% product purity (Brinejack desalinate, Prism Finch spectrum sight) |
| **Resource Recovery** | +10% to +90% spill recovery (Mercurial Ferret, Carrier Pigeon) |
| **XP Gain** | +5% to +15% skill XP multiplier (multiple companions) |
| **Apparatus Efficiency** | -10% to -30% switching time (Lab Dog, Bowtruckle) |

### What Companions MUST Never Bypass

| Category | Never Bypass |
|----------|-------------|
| **Skill Checks** | Companion bonuses do not reduce required skill level for recipes or procedures |
| **Lab Access** | Companions cannot unlock restricted laboratory zones |
| **Recipe Unlocks** | No companion ability permanently unlocks recipes |
| **Time Bypass** | Companions speed up reactions but cannot skip timed protocol steps |
| **Resource Generation** | Companions recover resources but cannot generate infinite resources |
| **PvP/Permadeath** | Companion death is permanent but does not end player game |
| **Progression Blocks** | No companion ability blocks main quest progression |

### Balance Guidelines

1. **Never gate content**: A player without any companion should be able to complete all lab procedures, just at slower efficiency
2. **Diminishing returns**: Additional companions provide less marginal benefit (see stacking rules)
3. **Resource cost balance**: Care actions and evolution costs scale with companion rarity
4. **Level appropriate**: Companion abilities available at levels consistent with species rarity (COMMON: Lv 1-15, UNCOMMON: Lv 8-25, RARE: Lv 15-40, EPIC: Lv 25-60, MYTHIC: Lv 55-100)
5. **Synergy not saturation**: Skill synergies encourage mixing companion types, not stacking same type
6. **Care maintenance**: Companions require regular tending (hunger/happiness decay) to maintain effectiveness
7. **Evolution investment**: Evolving companions requires player investment (level, loyalty, quests, items) — payoff should justify investment

### Numerical Constraints

- **Maximum total yield bonus**: +25% (across all companions)
- **Maximum total safety bonus**: +40% (across all companions, capped at 50% with diminishing returns)
- **Maximum detection range bonus**: +300% (radius increase, not absolute detection)
- **Maximum XP multiplier**: +20% (across all companions, diminishing after 3)
- **Care decay half-life**: Typical companion (medium loyalty) reaches critical hunger in ~20 in-game hours

---

## 8. Implementation File Plan

Files to create/modify in order (referencing existing companion scripts):

### 1. `design/companion_abilities_design.md` — **CREATE**
- New document with full ability schema, per-species designs, care system, evolution, active/passive, skill synergies, balance principles
- This is the deliverable document

### 2. `game/scripts/companions/companion_abilities.gd` — **CREATE**
- Godot script defining ability data structures and runtime logic
- Contains: `CompanionAbility` class, ability execution system, cooldown management, area effect application
- References `species_database.json` for companion-category-specific abilities

### 3. `game/scripts/companions/companion_manager_abilities.gd` — **MODIFY**
- Extend existing `CompanionManager` with ability integration
- Add methods: `use_companion_ability(instance_id, ability_id)`, `get_ability_cooldown_remaining(instance_id, ability_id)`
- Integrate with `get_skill_synergy_bonuses()` and `apply_skill_xp_bonus()`
- Handle ability targeting and area effects

### 4. `game/scripts/companions/companion.gd` — **MODIFY**
- Add `known_abilities: Array[Dictionary]` to store ability definitions (not just IDs)
- Add `_execute_ability(ability_id, target)` method
- Add `_check_ability_conditions(ability_id)` for skill requirements
- Modify `_learn_starting_abilities()` to load from new schema
- Add `_process_ability_decay()` for cooldown timers

### 5. `game/data/companions/species_database.json` — **MODIFY**
- Add `abilities` field to each species entry following the JSON Schema
- Each species gets 2-3 ability entries as designed in Section 2
- Ensure backwards compatibility: existing `chemistry_bonuses` and `battle_abilities` fields kept
- Add `care_profile` enhancements if not already present

### 6. `game/scripts/core/player_vitals.gd` — **MODIFY**
- Add radiation exposure tracking companion-affected
- Modify health decay rate based on active companion radiation shielding
- Add companion care need states to vitals UI
- Handle companion death penalty (IP reduction)

### 7. `game/scripts/progression/skill_manager.gd` — **MODIFY**
- Add `_calculate_companion_skill_bonuses()` method
- Integrate companion synergy bonuses into `apply_skill_xp_bonus()`
- Add skill milestone unlock conditions tied to companion abilities
- Update `get_unlocked_abilities()` to include companion-derived abilities

### 8. `game/scripts/quests/quest_manager.gd` — **MODIFY** (if needed)
- Add quests for companion evolution triggers
- Add quests for care milestones (first feeding, max loyalty achievement)
- Add quests for ability unlock conditions

### 9. `game/ui/companion_ability_ui.gd` — **CREATE**
- Godot UI script for ability cooldown display
- Care need indicators (hunger, happiness bars)
- Evolution availability signals
- Skill synergy tooltips

### 10. `docs/ROADMAP.md` — **UPDATE**
- Mark companion abilities system as PARTIAL → LIVE
- Add milestone: "Companion ability system implemented with 28 species × 2-3 abilities"
- Track: Care system balance, evolution VFX, skill synergy testing

### Implementation Priority Order

1. **Schema definition** (completed — this document)
2. **Species database updates** (add ability entries to all 28 species)
3. **Core companion script modifications** (ability system in companion.gd + CompanionManager)
4. **Care & decay system integration** (decay rates, critical states, player_vitals tie-ins)
5. **Evolution system extension** (new triggers, visual changes, mechanical benefits)
6. **Active/passive companion logic** (switching, following, buff distribution)
7. **Skill synergy implementation** (15 skill trees × companion abilities)
8. **Balance tuning** (numerical constraints, diminishing returns, resource costs)
9. **UI implementation** (ability displays, care indicators, evolution prompts)
10. **Playtesting and balance adjustment** (iterative tuning based on player feedback)

### Data-Driven Design Philosophy

All companion abilities are designed to be **data-driven**:
- Ability definitions live in `species_database.json` alongside species data
- New companions can be added by editing the JSON (no code changes required for basic abilities)
- Ability effects are configured via magnitude, cooldown, and area parameters
- Skill synergies are computed at runtime from skill levels + ability definitions
- Care decay rates and evolution conditions are fully configurable in data

This ensures the system is maintainable, extensible, and consistent with the project's existing data-driven architecture.