# Companion Combat Design — Athanor-Flavored

**Project:** Athanor Ascension  
**Status:** Design document (blueprint)  
**Feeds into:** `game/scripts/companions/companion_manager.gd`, `game/scripts/companions/companion_data.gd`, `game/scripts/companions/companion.gd`, `game/data/companions/species_database.json`

---

## 0. Guiding Constraints (non-negotiable)

| Constraint | Source |
|---|---|
| Companion vs NPC combat is optional; never required for laboratory progression | game-concept.md §3.2 |
| PvP companion battles are post-launch online phase only — NOT implemented | game-concept.md §3.2 |
| No netcode of any kind | CONTINUE_HERE.md §0.6 |
| Game is a chemistry lab simulator, not a combat game | CONTINUE_HERE.md constraints |
| Athanor-style feel: counter-based, fluid, brutal, brief — serves the story, never dominates it | task brief |

---

## 1. Design Philosophy

### What Athanor combat does well

AC combat works because it is **rhythmic, counter-oriented, brutal, and brief**. The player does not grind fights; each engagement is a punctuation mark in an investigation or infiltration. The fantasy is *controlled violence* — the player (or their operative) is precise, never sloppy, and always in service of a larger goal.

### How that maps to lab-companion combat

In Athanor Ascension, the player is a **chemist**, not a fighter. Combat happens when something has gone wrong in the lab — a containment breach, a hazardous spill turning hostile, a trespasser in a restricted zone. Companions are the ones who engage; the player supports them with chemistry actions (reagent throws, containment foam, fire extinguisher, hazard deployment). Combat is therefore:

- **Brief**: 10–30 seconds per engagement, never more.
- **Counter-based**: companions react to threat tells (wind-up, charge, glow, hiss) with timed counters rather than button-mashing.
- **Brutal but rare**: a single engagement can injure a companion or breach the lab; there is no "combat loop" to farm.
- **Story-serving**: combat exists to protect the lab and the experiment, not to generate loot.

### What you are NOT doing

- **No PvP.** Companion-vs-companion battles are planned for the post-launch online phase and are not implemented. This document only covers companion-vs-NPC (environmental hazard / intruder / breach entity).
- **No grinding.** No XP farm from combat, no battle-only loot, no "kill 10 rats" quests.
- **No combat-as-main-loop.** You cannot progress through the game by fighting. Lab access, synthesis recipes, and skill unlocks are never gated behind combat.
- **No netcode.** All combat is local, single-player, deterministic.

---

## 2. Combat Model — Single-Engagement State Machine

A combat engagement is a self-contained scene with a hard time budget. It starts when a threat enters a companion's detection radius and ends when the threat is neutralized, the companion retreats, or the player evacuates.

### States

| State | Meaning | Entry condition | Exit condition | Max duration |
|---|---|---|---|---|
| **IDLE** | Companion patrols / supervises bench | — | Threat enters detection radius | ∞ |
| **DETECT** | Companion identifies threat, alerts player | Threat within detection radius | Threat confirmed hostile OR player commands hold | 3 s |
| **APPROACH** | Companion closes to engagement radius | Threat confirmed | Threat leaves radius, or in range | 5 s |
| **ENGAGE** | Active combat: counters, abilities, player chemistry actions | Companion within engagement radius | Threat neutralized / retreat threshold / player incapacitated | 25 s (hard cap) |
| **RESOLVE** | Aftermath: injuries, loot, recovery, party status | ENGAGE exit | Cleanup complete | 5 s |

### Transitions & timing

```
IDLE --(threat in detection radius)--> DETECT
DETECT --(hostile confirmed)--> APPROACH
DETECT --(player holds / threat leaves)--> IDLE
APPROACH --(in engagement radius)--> ENGAGE
APPROACH --(threat leaves radius)--> IDLE
ENGAGE --(threat HP <= 0 / neutralized)--> RESOLVE
ENGAGE --(retreat threshold met)--> RESOLVE (retreat)
ENGAGE --(25 s hard cap)--> RESOLVE (forced disengage)
ENGAGE --(player incapacitated)--> RESOLVE (companions cover withdrawal)
```

### Timing budget

- **Total engagement**: 10–30 seconds. The hard cap at 25 s in ENGAGE plus ~5 s RESOLVE keeps it under 30 s.
- **Counter window**: 0.4 s after a threat's attack tell appears. Success = companion avoids damage + ripostes; failure = companion takes reduced damage.
- **Ability cooldown**: 6–12 s per ability, so a companion gets at most 2–3 ability uses per engagement.
- **Post-engagement lockout**: 60 s before the same companion can auto-engage again (prevents chaining fights).

### Hard rules

1. **Combat never starts without player awareness.** DETECT emits a UI pulse and audio cue; the player can order companions to hold position (stay in IDLE/APPROACH but not ENGAGE).
2. **If no active companion is in the party, combat does not start** — the threat becomes a lab hazard handled by the player (evacuation, containment, extinguisher).
3. **A forced disengage after 25 s** means the threat escapes or the lab goes into lockdown — neither is a "game over"; both are recoverable setbacks.

---

## 3. The Three Pillars of Lab Combat

the game's three approaches — stealth, direct, escape — map to laboratory scenarios:

### 3.1 Containment Breach (stealth pillar)

**Scenario:** A hazardous entity (spill-animate, breached containment, escaped test subject) is loose in the lab but has not yet detected the player. Companions can silently neutralize it before it becomes a full hazard.

**Concrete mechanic:** *Silent takedown via reagent application.*
- A companion with a detection ability (Calcine Hound residue tracking, Halide Newt halogen leak warning, Glasswing Moth microfracture sense) locates the breach source.
- The player applies a neutralising reagent (containment foam, inert solvent, absorbent) at the breach point while the companion keeps the entity distracted.
- Success: breach sealed, no combat state entered, no injury risk.
- Failure (player too slow or wrong reagent): escalates to direct confrontation.

### 3.2 Direct Confrontation (direct pillar)

**Scenario:** A hostile entity is active and attacking — a furnace-spawned ember, a reactive chemical construct, an intruder in a restricted zone. Companions engage openly.

**Concrete mechanic:** *Counter-riposte combat.*
- The entity telegraphs attacks with a 0.4 s tell (glow, hiss, wind-up).
- The companion auto-counters within the window; success avoids damage and deals a riposte.
- The player supports by throwing reagents (extinguisher for fire entities, neutralizer for chemical constructs, coolant for thermal entities) to stagger the entity and open counter windows.
- Combat ends when the entity is neutralized (dissolved, extinguished, contained) — not "killed" in a fantasy sense.

### 3.3 Lab Evacuation (escape pillar)

**Scenario:** The situation is unrecoverable — radiation spike, fire out of control, structural breach. The goal is to disengage and protect personnel.

**Concrete mechanic:** *Covered withdrawal.*
- Companions form a rearguard: the TANK (Obsidian Beetle, Calcine Hound) shells up / radiates soak to absorb damage while the player and other companions retreat to the airlock or safe room.
- Retreat is triggered manually by the player (panic button) or automatically when any companion hits its retreat threshold (see §7).
- Success: everyone reaches the safe room; the lab enters lockdown (recoverable after cleanup).
- Failure: companions faint, player is incapacitated, lab sustains damage (repairable, costs IP/reputation).

---

## 4. Companion Ability Design

Each species gets **1–2 combat-relevant abilities** tied to its lab role. Abilities are added via a new **optional** `combat_abilities` array on each species entry in `species_database.json`. Existing fields (`battle_abilities`, `battle_role`, etc.) are **untouched** — no schema-breaking changes.

### Ability schema (added to each species entry)

```json
"combat_abilities": [
  {
    "ability_id": "ember_spit",
    "display_name": "Ember Spit",
    "pillar": "direct",            // stealth / direct / escape
    "trigger": "counter",         // auto / counter / player_command
    "cooldown_s": 8,
    "unlock_level": 1,
    "effect": {
      "type": "damage_over_time",
      "damage_type": "thermal",
      "magnitude": 4.0,
      "duration_s": 3.0
    },
    "lab_role_tie": "flame_stabilisation"
  }
]
```

`pillar`, `trigger`, `cooldown_s`, `unlock_level`, `effect`, and `lab_role_tie` are all new optional keys — none are required, so existing species without them are unaffected.

### 8 Working Animals

| Species | Combat role | Ability 1 | Ability 2 |
|---|---|---|---|
| Lab Rat | Utility | `sniff_out` (reveal hidden hazards, stealth pillar) | `scurry` (dodge + retreat, escape pillar) |
| Instrumented Rat | Utility | `telemetry_ping` (reveal entity weak point, direct pillar) | `scurry` |
| Contraband Cat | Control | `silent_step` (approach without detection, stealth pillar) | `swipe` (quick counter, direct pillar) |
| Search Dog | Tank | `track` (follow residue trail, stealth pillar) | `guard` (intercept damage to player, escape pillar) |
| Carrier Pigeon | Utility | `fly` (recon, escape pillar) | `homing_return` (deliver sample while retreating) |
| Wall Gecko | Utility | `cling` (reach high breach points, stealth pillar) | `camouflage` (avoid detection, escape pillar) |
| Lab Axolotl | Support | `regenerate` (heal self over time, escape pillar) | `gill_pulse` (clear inhalation hazard, direct pillar) |
| Archive Raven | Utility | `recon` (reveal entity type before engage) | `retrieve` (recover dropped reagent mid-retreat) |

### 18 Aetherkin

| Species | Combat role | Ability 1 | Ability 2 |
|---|---|---|---|
| Cinderling | DPS | `ember_spit` (flame stabilisation → sets entity burning) | `flare` (blinding flash, opens counter window) |
| Brinejack | Tank | `brine_spray` (slows entity, desalination residue) | `shell_guard` (damage absorption) |
| Glasswing Moth | Utility | `fracture_sense` (reveal structural weak point) | `uv_flash` (reveal hidden entity, stealth pillar) |
| Calcine Hound | Tank | `track_ash` (residue tracking, reveals entity) | `heat_wave` (radiant heat pulse, direct pillar) |
| Mercurial Ferret | Utility | `spill_recover` (neutralizes chemical spill hazard) | `slip_through` (evade, escape pillar) |
| Lumen Eel | Support | `ros_pulse` (reactive-oxygen burst, damages chemical entities) | `shock` (stagger, direct pillar) |
| Verdant Sloth | Support | `slow_aura` (slows entity in radius, escape pillar) | `regrow` (self-heal over time) |
| Obsidian Beetle | Tank | `shell_wall` (blocks line of fire, protects player) | `radiation_soak` (absorbs radiation damage) |
| Null Moth | Support | `static_ward` (prevents electrical/ignition hazards) | `calm` (reduces entity aggression, escape pillar) |
| Tideglass Serpent | Control | `nucleate` (crystallizes entity in place, direct pillar) | `coil` (constrains movement) |
| Auric Kite | DPS | `dive` (high-speed strike, direct pillar) | `wind_slash` (knockback, escape pillar) |
| Sable Lynx | DPS | `pounce` (ambush strike from stealth) | `vanish` (break engagement, escape pillar) |
| Halide Newt | Support | `halide_sense` (reveal halogen hazards) | `colour_flash` (disorient entity) |
| Xenon Owl | Utility | `leak_sense` (reveal vacuum/pressure breach) | `silent_flight` (approach undetected) |
| Prism Finch | Utility | `spectrum_sight` (reveal entity composition/weakness) | `dart` (quick evasive strike) |
| Ferro Snail | Utility | `magnet_shell` (deflects metallic projectiles) | `adsorb` (absorbs spill residue) |
| Ember Drake | DPS | `breath_fire` (high damage, risks lab fire) | `molten_roar` (stagger + thermal DoT) |
| Chrysalis Warden | Support | `ward` (intercepts fatal damage once per cycle) | `cocoon_shield` (protects player/companion) |

**Chrysalis Warden special rule:** `ward` prevents one fatal accident per cycle (per its existing `REBIRTH` chemistry bonus). After triggering, it enters a 24-hour cooldown before it can prevent another fatal accident. This is the game's only "permanent loss prevention" mechanic — without Warden active, a companion that reaches 0 HP is injured (not permanently lost), but a *player* fatality is a serious setback.

---

## 5. Player Involvement — Chemistry Actions, Not Combat Actions

The player never swings a weapon or throws a punch. Every player contribution is a chemistry action:

| Player action | Chemistry basis | Combat effect | pillar |
|---|---|---|---|
| Throw neutralizing reagent | Acid/base neutralization | Staggers chemical constructs; opens counter window | direct |
| Deploy containment foam | Polymer foam / spill control | Seals breach; prevents entity spread | stealth / escape |
| Use fire extinguisher | CO₂ / dry chemical suppression | Extinguishes fire entities; reduces thermal damage | direct |
| Throw coolant | Endothermic reaction | Shuts down thermal entities / furnace-spawns | direct |
| Deploy absorbent | Inert absorbent (vermiculite, clay) | Neutralizes spill hazards; reduces slip/DoT | stealth |
| Set environmental hazard | Controlled reaction setup | Pre-placed reaction that triggers on entity approach | stealth |
| Patch containment | Gasket / seal replacement | Stops leak source; ends breach | stealth |

**Design rule:** Every player input in combat maps to a real lab procedure the player already knows from synthesis gameplay. If it doesn't look like chemistry, it doesn't belong in combat.

---

## 6. Risk/Reward — Injury States & Recovery

Combat is risky but recoverable. There is no permadeath for companions; the Chrysalis Warden's `ward` is the single fatal-accident prevention per cycle.

### Companion injury states

| State | HP | Effect | Recovery |
|---|---|---|---|
| Healthy | 100–70% | Full ability use | — |
| Winded | 69–40% | Ability cooldowns +25% | Rest (bench supervision) |
| Injured | 39–10% | Cannot engage; slow movement | First aid kit + 10–30 min real time |
| Fainted | 0% | Withdrawn from party; `companion_fainted` signal | Recovery crate; 2–6 hours; no permanent loss |

Injuries tie to `player_vitals.gd`: when a companion takes damage, the same `INJURY_PROFILES` types apply (chemical_burn, thermal_burn, laceration, inhalation). A companion with a `laceration` bleeds HP over time until healed, mirroring the player's injury system. Companion injuries do **not** damage the player directly, but a fainted companion reduces the party's chemistry bonuses and combat capacity.

### Recovery mechanics

- **First aid kit**: consumable, heals a fainted companion to Injured state instantly.
- **Recovery crate**: lab bench interaction, heals Injured → Healthy over 10–30 minutes (can be done while the player continues synthesizing).
- **Chrysalis Warden `ward`**: prevents one fatal accident per cycle. If the Warden is active and a companion would reach 0 HP from a fatal source, the Warden absorbs it instead (companion survives at 1 HP, Warden enters 24 h cooldown).

### Permanent loss risk

There is **no permanent companion loss from combat**. The only way a companion leaves the party is `release_companion()` (player choice). This respects the constraint that combat is optional and never punishing — a player who avoids combat entirely loses nothing.

### Player injury

The player uses `player_vitals.gd` normally. If the player is incapacitated during combat, companions auto-cover the withdrawal (escape pillar) and the player revives at 25 HP per `_stabilise()`. Combat cannot directly kill the player — it can only contribute to lab hazards that the player's vitals system already handles.

---

## 7. Auto-Battler Rules

Companions auto-act within a radius. The player sets tactics (aggressive / defensive / hold) but does not micromanage individual attacks.

| Parameter | Value | Notes |
|---|---|---|
| Detection radius | 12 m | Companions notice threats here; DETECT state |
| Engagement radius | 6 m | Companions enter ENGAGE here |
| Retreat threshold | 30% HP | Any companion at/below this auto-retreats (escape pillar) |
| Hold distance | 8 m | When player commands "hold", companions stay here and do not engage |
| Friendly fire | **None** | Companions never damage each other or the player |
| Player incapacitated | Companions form rearguard and withdraw to safe room | Escape pillar; no combat continues without the player |

### Auto-act priority (per companion, each ENGAGE tick)

1. If HP <= retreat threshold → retreat (escape pillar).
2. If enemy has a tell active and counter is ready → counter.
3. If ability off cooldown and situation matches (TANK absorbs, DPS strikes, Support heals/buffs) → use ability.
4. Otherwise → basic attack / positioning.

---

## 8. Balancing Principles — Combat Never Gates Progression

| Combat can reward | Combat must NEVER gate |
|---|---|
| Companion XP (loyalty, battle_record) | Lab access tiers |
| Intelligence Points (small, one-time per unique entity type) | Synthesis recipes |
| Reputation with factions | Skill unlocks |
| Rare reagents (spill residue, entity byproducts) | Quest advancement |
| Codex entries | Story progression |

**Hard rule:** Every lab, recipe, skill, and quest is completable without entering a single ENGAGE state. Combat rewards are *bonuses*, not *requirements*. If a player never fights, they can still reach Master Alchemist.

---

## 9. Implementation File Plan

| # | File | Action | Purpose |
|---|---|---|---|
| 1 | `game/data/companions/species_database.json` | Modify | Add optional `combat_abilities` array to all 26 species (8 animals + 18 Aetherkin), no existing fields touched |
| 2 | `game/scripts/companions/companion_data.gd` | Modify | Add `CombatAbility` dictionary schema docs + `CombatPillar`/`CombatTrigger` enums; add `MAX_ENGAGE_SECONDS`, `COUNTER_WINDOW_S`, `RETREAT_THRESHOLD_HP` constants |
| 3 | `game/scripts/companions/companion.gd` | Modify | Add combat state machine (IDLE→DETECT→APPROACH→ENGAGE→RESOLVE), `combat_state` var, `take_combat_damage()`, injury-state mapping to `player_vitals.gd` `INJURY_PROFILES`, `combat_abilities` runtime handling |
| 4 | `game/scripts/companions/companion_manager.gd` | Modify | Add auto-battler loop (detection/engagement/retreat radii), `get_battle_party()` extension with combat state, retreat handling, Warden `ward` cooldown tracking, `on_battle_end()` injury integration |
| 5 | `game/scripts/core/player_vitals.gd` | Modify (minimal) | Add `companion_injury` handling hook so companion injuries use the same `INJURY_PROFILES`/`_add_injury` patterns; expose `apply_companion_hazard_damage()` |
| 6 | `design/companion_combat_ac.md` | Create | This design document |

Order matters: species data first (schema), then data structures (enums/constants), then the runtime companion state machine, then the manager auto-battler, then the vitals integration last.

---

**Acceptance criteria (from CONTINUE_HERE.md §5):** Run `pytest` (256 tests), Godot headless smoke tests, and lint before marking this design ready for implementation. No netcode, no PvP, no combat-gated progression.
