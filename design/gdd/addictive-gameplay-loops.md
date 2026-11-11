# ChemLab: Origins — Addictive Gameplay Loops & Retention Mechanics Design Document

**Version:** 1.0  
**Status:** Pre-Production (Phase B Expansion)  
**Author:** Game Systems Design Lead  
**Cross-References:** `skill-system.md`, `quest-system.md`, `game-concept.md`, `sandbox-mode.md`

---

## 1. Executive Summary & Psychological Foundation

This document translates the core engagement loops of **classic RPG skill progression**, **World of Warcraft**, **Factorio**, **Subnautica**, and **Stardew Valley** into ChemLab's chemistry simulation context. Every loop is grounded in behavioral psychology: **variable-ratio reinforcement**, **goal-gradient effect**, **completionist drive**, **mastery motivation**, and **social identity signaling**.

**Design Principle:** The chemistry IS the gameplay. No abstracted "crafting bars" — every drop titrated, every crystal filtered, every spectrum interpreted is a real player action with verifiable scientific consequence.

---

## 2. Core Gameplay Loop (The "Heartbeat")

### 2.1 Four-Phase Core Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CHEMLAB CORE LOOP (30–120s)                        │
├──────────────┬──────────────┬──────────────┬────────────────────────────────┤
│   PLAN       │  EXECUTE     │   VERIFY     │        REWARD                  │
├──────────────┼──────────────┼──────────────┼────────────────────────────────┤
│ • Select     │ • Physical   │ • Real-time  │ • XP (Skill + Quest)           │
│   synthesis  │   actions:   │   analytical │ • Reputation (Faction)         │
│   target     │   weigh,     │   feedback:  │ • Unlocks (Reagent/Apparatus)  │
│ • Check      │   dispense,  │   pH curve,  │ • Codex Entry (Discovery)      │
│   prereqs    │   heat, stir,│   NMR peaks, │ • Lab Notebook Entry           │
│ • Prepare    │   filter,    │   GC-MS RT   │ • Safety Score Delta           │
│   station    │   recryst.   │ • Yield/Purity│ • Narrative Progress           │
└──────────────┴──────────────┴──────────────┴────────────────────────────────┘
```

### 2.2 Loop Timing & Pacing

| Loop Tier | Duration | Example | Retention Hook |
|-----------|----------|---------|----------------|
| **Micro** | 3–15s | Single buret drop → color flash | Variable-ratio reinforcement (endpoint uncertainty) |
| **Meso** | 2–8 min | Full titration / crystallization | Goal-gradient (progress bar fills) |
| **Core** | 15–45 min | Multi-step synthesis (Aspirin) | Mastery + Completion (quest checkpoint) |
| **Macro** | 1–4 hrs | Campaign act / Lab upgrade | Identity progression (title, lab, faction) |
| **Meta** | Days/Weeks | Prestige / Mastery cap | Legacy display (Hall of Fame, cosmetic) |

---

## 3. Micro-Loops: Second-to-Second Satisfaction

### 3.1 Titration Drop → Color Change (The "Ping")

**Mechanic:** Player controls buret stopcock with pressure-sensitive input (mouse hold / trigger analog). Each drop falls with physics simulation → hits solution → phenolphthalein equilibrium shifts.

**Psychological Triggers:**
- **Variable-Ratio Reinforcement:** Endpoint volume varies ±0.3 mL per run (concentration drift, temperature). Player never knows *exactly* which drop triggers pink.
- **Sensory Juice:** 
  - Audio: `sfx_buret_drop.wav` (pitch rises as endpoint nears)
  - Visual: Shader transition `Color(1,1,1,0) → Color(1,0.72,0.82,α) → Color(0.92,0.08,0.55,1)` over 3 frames
  - Haptic: Controller vibration on color-change frame
- **Agency:** Player *chooses* drop rate. Fast = risk overshoot. Slow = tedious. Optimal = "dropwise near equivalence" (skill expression).

**Implementation:**
```gdscript
# In titration_buret.gd — called per physics tick when stopcock open
func _on_drop_impacted(vessel_id: String) -> void:
    var ph = SimulationBridge.get_vessel_ph(vessel_id)
    var prev_ph = _last_ph[vessel_id] ?? 7.0
    _last_ph[vessel_id] = ph
    
    # Endpoint detection: pH crosses 8.2 (phenolphthalein pKind)
    if prev_ph < 8.2 and ph >= 8.2:
        # VARIABLE RATIO: endpoint volume has ±5% noise
        _trigger_endpoint_celebration(vessel_id)
        QuestManager.advance_objective("titrate_naoh", 1.0)
    
    # Audio pitch mapping: 0.8→1.2 as pH 7→9
    var pitch = lerpf(0.8, 1.2, clampf((ph - 7.0) / 2.0, 0.0, 1.0))
    AudioServer.set_bus_pitch_drop(pitch)
```

### 3.2 Crystallization Watch → Nucleation Burst

**Mechanic:** After reflux, player quenches in ice bath. Crystals nucleate stochastically (Poisson process, λ = supersaturation × seed surface area).

**Triggers:**
- **Anticipation Buildup:** 30–90s of "nothing visible" → sudden crystal explosion
- **Player Agency:** Scratching flask wall (input action) seeds nucleation → player feels "I caused this"
- **Variable Reward:** Crystal size distribution follows power law. Rare "perfect needles" (melting point sharp) vs. "amorphous powder" (impure)

### 3.3 Vacuum Filtration → Cake Reveal

**Mechanic:** Player pours slurry onto Büchner funnel. Vacuum pulls liquid. Cake remains.

**Triggers:**
- **Completion Visual:** Transparent liquid → solid white cake (progress bar 100%)
- **Yield Reveal:** Mass readout on analytical balance (target ±2%)
- **Purity Signal:** Melting point capillary test → sharp vs. broad range

---

## 4. Meso-Loops: Session-Level Progression (5–45 min)

### 4.1 Synthesis Quest Arc (The "Multi-Stage Mastery Quest" Model)

```
QUEST STRUCTURE (per quest-system.md §4):
┌────────────────────────────────────────────────────────────────┐
│  q_synth_aspirin (Chemistry Lvl 5)                            │
├────────────────────────────────────────────────────────────────┤
│  Stage 1: Weigh Salicylic Acid (Metrology)        → 2 min      │
│  Stage 2: Charge Acetic Anhydride + H₂SO₄         → 1 min      │
│  Stage 3: Reflux 15 min @ 70–75°C (Thermal Mgmt)   → 4 min*    │
│  Stage 4: Quench + Ice Bath Crystallization       → 3 min      │
│  Stage 5: Vacuum Filter + Wash                    → 2 min      │
│  Stage 6: Melting Point Assay (Verification)      → 2 min      │
│  ────────────────────────────────────────────────────────────  │
│  TOTAL ACTIVE TIME: ~14 min  |  WALL TIME: ~20 min             │
│  REWARD: 2,500 Chem XP + 1,000 Eng XP + 750 Credits           │
│  PURITY BONUS: ≥98% → +50% XP + "Analytical Grade" reagent    │
└────────────────────────────────────────────────────────────────┘
*Reflux is real-time but player manages cooling bath temp (active monitoring)
```

**Retention Mechanics:**
- **Checkpoint Saves:** Auto-save at each stage completion (no progress loss on crash)
- **Stage Skip Token:** Unlocked at Chemistry 25 — skip *one* trivial stage per quest
- **Parallel Questing:** Two quests can run simultaneously (e.g., reflux Aspirin WHILE setting up Paracetamol reagents)

### 4.2 Kinetic Reaction Monitoring (The "Factorio Belt Watch" Loop)

**Mechanic:** Iodine Clock / Belousov-Zhabotinsky / H₂O₂ decomposition. Player watches real-time concentration curves, adjusts temperature/stirring to hit target rate.

**Loop:**
```
MONITOR → INTERVENE → OBSERVE RESULT → REPEAT
  │           │              │            │
  ▼           ▼              ▼            ▼
Temp drift  Add ice bath   Rate matches  Next phase
detected    / adjust stir  target?       unlocks
```

**Psychology:** 
- **Flow State:** Continuous micro-adjustments match player skill to challenge (Csikszentmihalyi)
- **Ownership:** "I stabilized this runaway" — internal locus of control

---

## 5. Macro-Loops: Long-Term Mastery & Identity (Hours–Months)

### 5.1 Skill Mastery → New Lab → New Synthesis (The "Skill Tree" Loop)

**Chemistry Track Milestones (from skill-system.md §3.6):**

| Level | Milestone Title | Unlocks | Psychological Payoff |
|-------|-----------------|---------|----------------------|
| 1 | Stockroom Baseline | Erlenmeyer, Balance, Pipette | **Competence** — "I can measure" |
| 3 | Reflux Rigging | Liebig/Dimroth Condenser | **Agency** — "I control heat" |
| 10 | Distillation & Titration | Buret 50mL, UV-Vis | **Precision** — "I see the invisible" |
| 15 | Separation Science | Büchner, Ion Exchange | **Mastery** — "I purify" |
| 25 | Inert Atmosphere | Schlenk Line, Glovebox | **Exclusivity** — "I handle air-sensitive" |
| 50 | Instrument Suite | HPLC, GC-MS, FT-NMR | **Authority** — "I prove structure" |
| 75 | Analytical Depth | ICP-MS, XRF, DSC | **Expertise** — "I quantify trace" |
| 100 | Athanor Core | Total Synthesis Autonomy | **Transcendence** — "I design molecules" |

**Cross-Track Synergy (Macro-Loop Engine):**

```
CHEMISTRY 50 (HPLC/GC-MS)  ──────►  FORENSICS 30 (Ballistics/GC-MS match)
      │                                    │
      ▼                                    ▼
ENGINEERING 30 (Buret Calib)  ◄───  BIOLOGY 25 (PCR/qPCR quantification)
      │
      ▼
SANDBOX MODE UNLOCK (Eng 5 = Safe, Eng 100 = Full)
```

**Retention:** Players *must* cross-train to unlock highest-tier content. No single track is sufficient.

### 5.2 Laboratory Evolution (The "Stardew Farm Upgrade" Loop)

| Lab Tier | Unlock Condition | New Capabilities | Visual Identity |
|----------|------------------|------------------|-----------------|
| **Backyard Shed** | Tutorial complete | Basic glassware, hotplate | Cluttered, plastic, single bench |
| **University Teaching Lab** | Chemistry 10 + Safety A+ | Fume hoods, rotovap, UV-Vis | Clean, institutional, shared |
| **Industrial Process Lab** | Chemistry 25 + Engineering 15 | Jacketed reactors, HPLC, pilot scale | Stainless, piped services, PLC |
| **Clandestine Cellar** | Forensics 15 + Syndicate Rep 60 | Improvised gear, precursor access | Dim, concealed, jury-rigged |
| **Orbital Microgravity** | Engineering 50 + Biology 30 | Zero-G crystallization, protein crystals | Sleek, sealed, floating |
| **Athanor Core** | All tracks 100 | Quantum chem interface, auto-synthesis | Transcendent, adaptive, alive |

**Progression Feel:** Each lab is a *physical space* the player walks through. Upgrades are visible (new benches, instruments appearing). NPCs react to lab tier.

---

## 6. Daily / Weekly Goal Systems (Retention Anchors)

### 6.1 Daily "Lab Routine" (5–15 min, resets 04:00 local)

```jsonc
{
  "daily_routine": {
    "categories": [
      { "id": "calibration", "name": "Morning Calibration", "xp": 200, "tasks": [
        "Tare analytical balance (3×)",
        "Verify pH meter buffers (pH 4, 7, 10)",
        "Check buret tip for air bubbles"
      ]},
      { "id": "synthesis", "name": "Daily Synthesis", "xp": 500, "tasks": [
        "Complete any synthesis quest stage",
        "Or: Produce 10g of any unlocked compound"
      ]},
      { "id": "analysis", "name": "Instrumental Analysis", "xp": 300, "tasks": [
        "Run 1 UV-Vis / GC-MS / NMR sample",
        "Log spectrum in notebook with interpretation"
      ]},
      { "id": "safety", "name": "Safety Drill", "xp": 150, "tasks": [
        "Fume hood flow verification",
        "Emergency shower/eyewash test",
        "Waste segregation audit"
      ]},
      { "id": "literature", "name": "Literature Review", "xp": 100, "tasks": [
        "Read 1 procedurally-generated paper abstract",
        "Extract 1 synthesis insight → notebook"
      ]}
    ],
    "completion_bonus": {
      "3_of_5": "500 XP + 1 Daily Token",
      "5_of_5": "1,500 XP + 3 Daily Tokens + Streak Protection"
    },
    "streak_rewards": {
      "3_days": "Reagent: Benzaldehyde (unlock early)",
      "7_days": "Apparatus: Magnetic Stirrer PID upgrade",
      "14_days": "Cosmetic: Lab Coat — 'Dedicated Researcher'",
      "30_days": "Title: 'Creature of Habit' + Permanent +5% XP gain",
      "100_days": "Unique Apparatus: 'Routine Master' Autotitrator"
    }
  }
}
```

**Psychology:**
- **Low Friction:** 3/5 completion = meaningful progress (no "all or nothing" pressure)
- **Streak Protection:** 1 "freeze" per 7-day streak (prevents churn from missed day)
- **Variable Rewards:** Daily synthesis target rotates (aspirin → paracetamol → indigo → caffeine)

### 6.2 Weekly "Research Project" (1–3 hrs, resets Monday 04:00)

```jsonc
{
  "weekly_project": {
    "tiers": [
      { "name": "Replication Study", "req": "Chem 10", "target": "Reproduce 3 known syntheses ≥95% purity", "reward": "2,500 XP + Reagent Voucher" },
      { "name": "Method Development", "req": "Chem 25", "target": "Optimize yield of 1 synthesis by ≥10% vs. literature", "reward": "5,000 XP + Custom Protocol Slot" },
      { "name": "Total Synthesis Sprint", "req": "Chem 50", "target": "Complete multi-stage synthesis (e.g., Indole → Tryptamine)", "reward": "15,000 XP + Named Compound Entry in Codex" },
      { "name": "Forensic Case File", "req": "Foren 25", "target": "Solve 1 procedural crime scene + expert report", "reward": "10,000 XP + Syndicate Rep" },
      { "name": "Bio-Assay Campaign", "req": "Bio 15", "target": "Run 5 PCR/qPCR assays with quantification", "reward": "7,500 XP + Primer Design Unlock" }
    ],
    "cross_track_bonus": "Complete 2+ different tier types → +50% total XP",
    "leaderboard": "Top 100 weekly → cosmetic lab decoration"
  }
}
```

---

## 7. Streak Systems (Loss Aversion & Consistency)

### 7.1 Safety Streak (The "OSHA Compliance" Streak)

**Mechanic:** Consecutive days with **zero safety violations** (score ≥ 95).

| Streak | Reward | Visual |
|--------|--------|--------|
| 3 days | +2% XP multiplier (all skills) | Green checkmark on HUD |
| 7 days | Unlock: "Safety Officer" cosmetic badge | Badge on lab coat |
| 14 days | Apparatus: Automatic fume hood sash controller | New device on bench |
| 30 days | Title: "Zero Incident" + Permanent safety score floor 90% | HUD title prefix |
| 60 days | Unique: "Guardian Angel" — 1×/session auto-catch critical error | Particle effect on save |

**Loss Aversion:** Breaking streak resets multiplier to 1.0, shows "Incident Report" animation. *But* player can spend **Daily Tokens** (from daily routine) to "file appeal" and preserve streak once per 14 days.

### 7.2 Synthesis Streak (The "Daily Synthesis" Streak)

**Mechanic:** Complete ≥1 synthesis quest stage daily.

| Streak | Reward |
|--------|--------|
| 5 days | Reagent purity bonus +2% (all syntheses) |
| 10 days | Unlock: "Parallel Synthesis" — run 2 quests simultaneously |
| 21 days | Apparatus: "Continuous Flow Reactor" (automates reflux stage) |
| 50 days | Title: "Synthesis Savant" + Cosmetic: Golden spatula |

### 7.3 Streak Design Principles

1. **Multiple Independent Streaks:** Safety, Synthesis, Analysis, Literature — player chooses focus
2. **Grace Mechanisms:** Daily Tokens = streak insurance (earned, not purchased)
3. **Visual Persistence:** Streak counters visible in lab notebook, HUD, save file
4. **Social Proof:** Leaderboards show "Longest Active Streak" per category

---

## 8. Discovery Dopamine: The Codex System

### 8.1 Compound Codex (The "Pokédex" for Molecules)

**Mechanic:** Every *novel* compound synthesized (first time by player) creates a Codex entry.

```jsonc
{
  "codex_entry": {
    "compound_id": "aspirin",
    "discovery_timestamp": "2026-11-04T14:23:12Z",
    "synthesis_context": {
      "quest_id": "q_synth_aspirin",
      "purity_pct": 97.3,
      "yield_pct": 89.1,
      "safety_score": 98.0,
      "lab_tier": "University Teaching Lab"
    },
    "analytical_data": {
      "mp_experimental_c": 135.2,
      "mp_literature_c": 136.0,
      "uv_vis_lambda_max_nm": [230, 275],
      "nmr_shifts_ppm": [2.3, 7.2, 7.8, 8.1],
      "gc_ms_rt_min": 4.23
    },
    "player_notes": "First API synthesis! Crystals beautiful needles. Slight acetic acid smell on wash.",
    "milestone_flags": ["First_API", "First_Recrystallization", "Melting_Point_Match"]
  }
}
```

**Psychological Triggers:**
- **First-Discovery Rush:** "NEW ENTRY" animation + unique sound (`sfx_quest_complete.wav` variant)
- **Collection Completion:** Codex has **categories** (Analgesics, Dyes, Precursors, Natural Products, Forensic Standards, Psychoactives). Completing a category grants **Mastery Title** + unique reagent.
- **Social Sharing:** "Publish to Codex Network" → shares anonymized entry to global leaderboard (opt-in). Top purity/yield entries highlighted weekly.

### 8.2 Apparatus & Reagent Catalog Completion

| Catalog | Total Entries | Completion Reward |
|---------|---------------|-------------------|
| **Reagent Catalog** | 120+ | "Chemist's Library" — all reagent properties visible without lookup |
| **Apparatus Registry** | 60+ | "Master Workbench" — all apparatus craftable at 50% material cost |
| **Spectral Library** | 200+ | "Spectral Intuition" — auto-peak-assist on NMR/GC-MS |
| **Safety Data Sheets** | 90+ | "Safety Oracle" — real-time hazard prediction during synthesis |

### 8.3 Companion Collection (NPC Relationships)

**Mechanic:** Faction NPCs become "Companions" at Trusted (80+) reputation. Each provides unique passive/active bonuses.

| Companion | Faction | Unlock Condition | Passive Bonus | Active Ability (1×/session) |
|-----------|---------|------------------|---------------|----------------------------|
| Dr. Thorne | Academic | Chem 25 + Rep 80 | +10% XP from Synthesis quests | "Peer Review" — reroll one purity check |
| "Nails" Morau | Syndicate | Foren 15 + Rep 80 | Precursor cost -20% | "Diversion" — hide 1 clandestine action |
| Agent Reyes | Law Enforcement | Foren 30 + Rep 80 | Safety score decay -50% | "Warrant" — instant forensic scan of any lab |
| Prof. Kowalski | Industrial | Eng 25 + Rep 80 | Apparatus crafting time -30% | "Pilot Run" — simulate synthesis without materials |
| Dr. Sato | Orbital | Bio 30 + Eng 50 | Zero-G crystallization yield +25% | "Microgravity Drop" — 1 free orbital run |

**Collection Drive:** 5 companions → "Scientific Council" cosmetic (round table in lab). All 10 → "Director's Office" lab tier.

---

## 9. Prestige & Respec Systems (Long-Term Retention)

### 9.1 Prestige: "Athanor Ascension" (New Game+)

**Trigger:** All four Phase B tracks (Chemistry, Biology, Forensics, Engineering) reach Level 100.

**Mechanic:**
```
ASCENSION SEQUENCE:
1. Player enters Athanor Core Reactor (unlocked at Chem 100)
2. Initiates "Transmutation Sequence" — consumes ALL unlocked reagents/apparatus
3. Cinematic: Lab dissolves → reforms as "Athanor Prime" (cosmetic)
4. All skill levels RESET to 1
5. XP curve modifier: ×1.5 (faster re-leveling)
6. Permanent unlocks retained:
   - Codex entries (knowledge persists)
   - Companion relationships (NPCs remember)
   - Cosmetic titles/lab decorations
   - "Athanor" prefix on all future lab tiers
```

**Prestige Tiers (up to 5):**

| Ascension | Requirement | Permanent Bonus | Cosmetic |
|-----------|-------------|-----------------|----------|
| I | All tracks 100 | +50% XP gain | Athanor Prime lab skin |
| II | Ascension I + All tracks 100 again | +100% XP, +1 simultaneous quest | Golden Athanor sigil |
| III | Ascension II + All tracks 100 | +150% XP, Safety streak immune to 1 break/week | Platinum sigil + particle aura |
| IV | Ascension III + All tracks 100 | +200% XP, All reagents unlocked from L1 | Iridescent sigil + custom music |
| V | Ascension IV + All tracks 100 | +250% XP, "Athanor Architect" — design custom apparatus | Unique lab: "Athanor Citadel" |

**Why Prestige Works:**
- **Progress Preservation:** Knowledge (Codex), relationships (Companions), cosmetics NEVER lost
- **Accelerated Replay:** XP multiplier makes re-leveling feel *different* (faster, more agency)
- **New Constraints:** Each ascension adds a "Challenge Modifier" (optional, +bonus):
  - Ascension I: "Glass Only" — no plastic apparatus
  - Ascension II: "No Fume Hood" — improvised ventilation only
  - Ascension III: "Analytical Only" — no spectroscopic instruments
  - Ascension IV: "Solo" — no companion abilities
  - Ascension V: "Hardcore" — permadeath on safety F

### 9.2 Respec: "Paradigm Shift" (Skill Reallocation)

**Mechanic:** At any time, player can initiate a **Paradigm Shift** at the Athanor Core (unlocked Chem 50 or Ascension I).

```
COST: 50% of total XP in ONE track → redistributed to OTHER tracks
LIMIT: 1× per real-world week (prevents optimization churn)
VISUAL: "Thesis Defense" cutscene — player presents research, committee reassigns focus
```

**Example:** Player has Chemistry 75, Biology 10, Forensics 5, Engineering 20.
→ Paradigm Shift Chemistry → lose 37.5 levels worth of Chem XP
→ Gain ~1.8M XP to distribute: Biology 45, Forensics 30, Engineering 40.

**Psychology:** 
- **Meaningful Choice:** Not free — sacrifices mastery for breadth
- **Narrative Framing:** "Changing research focus" not "respec"
- **Rate Limit:** Weekly cooldown prevents min-maxing, encourages commitment

---

## 10. Retention Mechanics Summary: The "Engagement Stack"

### 10.1 Hook Hierarchy (Short → Long Term)

| Timescale | Mechanic | Psychological Principle | Churn Defense |
|-----------|----------|-------------------------|---------------|
| **Seconds** | Titration color flash | Variable-ratio reinforcement | Micro-dopamine prevents boredom |
| **Minutes** | Quest stage completion | Goal-gradient effect | Checkpoint saves = no wasted effort |
| **Session** | Daily routine + Weekly project | Habit formation (Cue→Routine→Reward) | Streak protection = forgiveness |
| **Days** | Safety/Synthesis streaks | Loss aversion + Consistency bias | Grace tokens = agency over failure |
| **Weeks** | Skill milestones → New lab | Mastery + Identity progression | Cross-track gating = varied gameplay |
| **Months** | Codex completion + Companions | Collecting + Social bonding | Completionist drive |
| **Quarters** | Prestige (Athanor Ascension) | Legacy + Renewal | Progress preserved, curve accelerated |

### 10.2 Anti-Churn Safeguards

1. **Returning Player Bonus:** Offline XP accumulation (capped at 24h worth) — "Your experiments continued running"
2. **Catch-Up Mechanics:** 
   - "Literature Review" daily gives bonus XP for lowest skill
   - Weekly project tier "Replication Study" always available (low req)
3. **Social Anchors:** Companion dialogue changes with player progress — "NPCs notice"
4. **Narrative Hooks:** Story acts unlock at specific milestones — "What happened to Dr. Voss?"
5. **Seasonal Events:** 
   - "Nobel Week" (October): +50% Analytical XP, special synthesis targets
   - "Holiday Synthesis" (December): Cinnamaldehyde → cinnamon oil, cosmetic rewards
   - "April Fools": "Impossible Synthesis" — joke compounds with real mechanics

---

## 11. Integration with Existing Systems

### 11.1 Quest Engine Integration (quest-system.md)

- Daily/Weekly quests use **same QuestEngine** — auto-generated from templates
- Streak rewards = `reward_type: "streak_milestone"` in quest JSON
- Codex entries created via `QuestEngine._complete_quest()` → `CodexManager.register_discovery()`

### 11.2 Skill System Integration (skill-system.md)

- Milestone unlocks gate daily/weekly tier availability
- XP rewards from dailies/weeklies feed `SkillManager.add_xp()`
- Prestige checks `SkillManager.get_all_levels()` for ascension eligibility

### 11.3 Save Manager Integration (save_manager.gd)

```gdscript
# Extended save_data schema additions:
"daily_routine": {
    "last_reset": "2026-11-04T04:00:00Z",
    "completed_categories": ["calibration", "synthesis"],
    "streak_days": 12,
    "daily_tokens": 3
},
"weekly_project": {
    "last_reset": "2026-11-02T04:00:00Z",
    "active_tier": "method_development",
    "progress": {"target_syntheses": 3, "completed": 1}
},
"streaks": {
    "safety": {"current": 12, "longest": 28, "freeze_tokens": 1},
    "synthesis": {"current": 5, "longest": 21}
},
"codex": {
    "discovered_compounds": ["aspirin", "paracetamol", "indigo"],
    "completed_categories": [],
    "published_entries": 2
},
"companions": {
    "unlocked": ["dr_thorne", "nails_morau"],
    "active": "dr_thorne"
},
"prestige": {
    "ascension_tier": 0,
    "paradigm_shifts_available": 1,
    "last_shift": "2026-10-28T10:00:00Z"
}
```

### 11.4 Simulation Bridge Integration (simulation_bridge.gd)

- Titration endpoint detection → triggers micro-loop celebration
- Crystallization nucleation → stochastic event with player agency (scratch)
- Safety violations → feed `QuestManager.trigger_safety_violation()` → streak break check

---

## 12. Analytics & LiveOps Telemetry

### 12.1 Key Retention Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **D1 Retention** | ≥45% | Session count day 1 vs day 0 |
| **D7 Retention** | ≥25% | Weekly project start rate |
| **D30 Retention** | ≥15% | Prestige-eligible players |
| **Avg Session Length** | 35 min | Core loop completions per session |
| **Daily Routine Completion** | ≥60% DAU | 3/5 categories done |
| **Streak Maintenance** | ≥40% DAU | Safety streak ≥7 days |
| **Codex Discovery Rate** | 2.5/session | New entries per play session |
| **Cross-Track Engagement** | ≥70% | Players with ≥2 tracks >Lvl 10 |

### 12.2 A/B Test Candidates

1. **Streak Freeze Cost:** 1 Daily Token vs 2 vs 3
2. **Daily Routine Categories:** 5 vs 6 vs 7 (cognitive load)
3. **Prestige XP Multiplier:** 1.5× vs 2.0× vs 1.75×
4. **Companion Unlock Threshold:** Rep 70 vs 80 vs 85
5. **Weekly Project Difficulty Scaling:** Fixed vs Adaptive (based on skill levels)

---

## 13. Implementation Roadmap

### Phase 1: Core Micro-Loops (Week 1–2)
- [ ] Titration endpoint celebration (audio/visual/haptic)
- [ ] Crystallization nucleation with player scratch action
- [ ] Vacuum filtration cake reveal animation
- [ ] Safety violation → streak break integration

### Phase 2: Daily/Weekly Systems (Week 3–4)
- [ ] Daily routine UI + reset logic (save_manager)
- [ ] Weekly project generator (procedural from quest templates)
- [ ] Streak tracking + grace token economy
- [ ] HUD streak counters + notifications

### Phase 3: Codex & Collection (Week 5–6)
- [ ] Compound Codex UI (discovery log, analytical data viewer)
- [ ] Apparatus/Reagent catalog completion tracking
- [ ] Companion system (NPC relationship → passive/active bonuses)
- [ ] Social sharing (anonymized leaderboard)

### Phase 4: Macro Progression (Week 7–8)
- [ ] Lab tier upgrade visual progression
- [ ] Cross-track milestone gating enforcement
- [ ] Prestige: Athanor Ascension sequence
- [ ] Respec: Paradigm Shift mechanic

### Phase 5: LiveOps & Polish (Week 9–10)
- [ ] Analytics event pipeline
- [ ] A/B test framework
- [ ] Seasonal event calendar
- [ ] Returning player catch-up
- [ ] Accessibility: Colorblind modes for titration, audio cues for safety

---

## 14. Design Validation Checklist

- [ ] **No Pay-to-Win:** All loops achievable through play; no real-money shortcuts
- [ ] **Respect Player Time:** Daily routine ≤15 min; weekly ≤3 hrs; no mandatory grind
- [ ] **Graceful Failure:** Streak breaks are recoverable; progress never fully lost
- [ ] **Scientific Integrity:** All rewards tied to *real* chemical achievement (purity, yield, safety)
- [ ] **Accessibility:** Colorblind-safe phenolphthalein transition; audio cues for all visual events; one-handed mode for buret control
- [ ] **No Dark Patterns:** No artificial scarcity, no FOMO timers, no social pressure
- [ ] **Educational Alignment:** Every loop teaches real chemistry technique or principle

---

## 15. Appendix: Reference Game Loop Deconstructions

### 15.1 Classic Skill Progression → ChemLab Mapping

| Classic Progression System | ChemLab Equivalent |
|------------------|-------------------|
| Skill XP (1–99/120) | 4 Track Skills (1–100) + 5 Legacy Skills |
| Quest Points → Cape | Quest Completion → Lab Tier + Titles |
| Collection Log (Boss drops) | Codex (Compound/Analytical data) |
| Daily Challenges | Daily Lab Routine |
| Leagues / Fresh Start Worlds | Athanor Ascension (Prestige) |
| Achievement Diaries | Weekly Research Projects |

### 15.2 Factorio → ChemLab Mapping

| Factorio System | ChemLab Equivalent |
|-----------------|-------------------|
| Belt/Inserter optimization | Reaction condition tuning (T, stir, conc.) |
| Science pack production | Synthesis quest chains |
| Blueprint library | Protocol Codex (player saves) |
| Infinite research | Post-100 mastery (Athanor Core) |
| Pollution/biters | Safety violations / Thermal runaway |

### 15.3 Subnautica → ChemLab Mapping

| Subnautica System | ChemLab Equivalent |
|-------------------|-------------------|
| Depth progression → Vehicle upgrades | Skill milestones → Apparatus unlocks |
| Scanning → Encyclopedia entries | Synthesis → Codex entries |
| Base building → Safe zones | Lab tier upgrades → Safe/automated zones |
| Story beats (Degasi, Precursors) | Campaign Acts (Dr. Voss, Project Athanor) |

### 15.4 Stardew Valley → ChemLab Mapping

| Stardew System | ChemLab Equivalent |
|----------------|-------------------|
| Farming/XP → Seasonal crops | Skills → Synthesis unlocks |
| Community Center bundles | Codex category completion |
| Villager hearts → Cutscenes | Companion rep → Abilities |
| Year cycles → Greenhouse | Prestige → Athanor Ascension |
| Museum completion | Spectral Library completion |

### 15.5 WoW → ChemLab Mapping

| WoW System | ChemLab Equivalent |
|------------|-------------------|
| Talent trees | Skill milestone ability unlocks |
| Daily/World quests | Daily Lab Routine / Weekly Project |
| Reputation factions | Faction rep (Academic/Syndicate/LE/Industrial) |
| Mythic+ keys | Weekly Project tiers (scaling difficulty) |
| Transmog/Collections | Cosmetic lab decorations / Titles |
| New Game+ (Timewalking) | Athanor Ascension (accelerated replay) |

---

**Document Status:** Ready for review. Cross-references validated against `skill-system.md`, `quest-system.md`, `game-concept.md`, `save_manager.gd`, `simulation_bridge.gd`, `quest_manager.gd`.

**Next Steps:** 
1. `/design-review addictive-gameplay-loops` — validate against GDD standards
2. `/create-stories` — break Phase 1–2 implementation into dev stories
3. `/ux-design hud` — design streak/Codex HUD integration