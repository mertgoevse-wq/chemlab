# ChemLab / Athanor Ascension — Game Balance Design Framework

**Version:** 1.0  
**Date:** 2026-11-06  
**Author:** Game Balance Lead  
**Status:** LIVE — design document for tuning & playtest planning

---

## 1. Current Economy Model

### 1.1 Currencies

| Currency | Source | Sinks | Balance Notes |
|----------|--------|-------|---------------|
| **Chem XP** | Quest completion, daily routines, synthesis stages | Level-up (soft cap 100), prestige respec | Primary progression metric. 4 tracks (Chem, Bio, Forensics, Eng). XP per action scales with action difficulty (titration 50–250 XP, synthesis 500–2500 XP). |
| **Skill XP** (per track) | Same as Chem XP — tracked separately per skill_id | Level-up per track (max 120), soft cap at 100 | Each track has independent progression. Level 100 unlocks Athanor Core; levels 101–120 are "post-mastery" with reduced returns. |
| **Reputation (Faction)** | Quest completion, companion interactions, daily routines | Shop discounts, companion abilities, syndicate access | 5 factions: Academic, Syndicate, Law Enforcement, Industrial, Orbital. Rep 80+ unlocks companion status. |
| **Credits (Money)** | Quest rewards, daily routine completion, sales | Suit purchases, lab upgrades, reagent vouchers | Starting budget 2,000 ₡. Mid-game sink: full suit set ≈ 15,000 ₡. Late-game sink: pilot plant setup ≈ 50,000 ₡. |
| **Daily Tokens** | Daily routine 5/5 completion, streak milestones | Streak freeze (1 token/preservation), shop rerolls | Max carry: 5 tokens. Grace mechanism for safety/synthesis streak breaks. |
| **Codex Entries** | First-time compound synthesis | Discovery bragging rights, category completion rewards | 120+ reagent entries, 200+ spectral library entries. Completing categories grants mastery titles + unique reagents. |

### 1.2 Economy Flow

```
Quest Completion
    ↓ (XP + Credits + Rep)
Skill XP Gain → Level Up → Apparatus/Reagent/Ability Unlock
    ↓
Daily Routine → Daily Tokens → Streak Protection / Shop Rerolls
    ↓
Synthesis → Codex Entry → Category Completion → Mastery Title + Reward
    ↓
Companion Rep Gain → Companion Unlock → Passive/Active Bonuses
    ↓
Safety Score → Grade → Stars (1–3) → XP Multiplier Modification
```

---

## 2. XP Curve Model

### 2.1 Formula

**Formula:** `floor(sum_{i=1}^{level-1} floor(i + 300 * 2^(i/7) / 4))`

**Max Level:** 120  
**Soft Cap:** 100 (beyond 100, XP gains feel "post-mastery" but mechanical progression continues to 120)  
**XP Table Sample** (from skills.json):

| Level | cumulative XP |
|-------|--------------|
| 1 | 0 |
| 2 | 83 |
| 5 | 388 |
| 10 | 1,154 |
| 15 | 2,411 |
| 25 | 7,842 |
| 30 | 13,363 |
| 50 | 101,333 |
| 75 | 1,012,111 |
| 90 | 5,346,332 |
| 99 | 13,034,431 |
| 100 | 14,391,160 |
| 120 | 104,273,167 |

### 2.2 Level-to-XP & XP-to-Level Functions

- **`xp_to_reach_level(level)`**: Returns threshold XP for given level (from `_thresholds` array built in skill_manager.gd)
- **`level_for_xp(xp)`**: Binary search on thresholds to determine player level from XP total
- **`get_progress(skill_id)`**: Returns float 0.0–1.0 showing progress within current level's XP span

### 2.3 Soft Cap Behavior (Levels 100–120)

- **XP required per level increases exponentially** (last 20 levels require ~9× the XP of levels 90–99)
- **Practical soft cap** at 100 for most players — reaching 120 is a "post-game" / prestige goal
- **Prestige multiplier** (Ascension I–V) ×1.5 to ×2.5 accelerates re-leveling, making alt-progression meaningful

### 2.4 XP Reward Balancing

| Action | XP Range | Notes |
|--------|----------|-------|
| Single titration drop | 1–5 XP | Variable-ratio reinforcement |
| Complete orientation quest | 500 XP | Tier 1, tutorial |
| Complete iodine clock quest | 750 XP | Tier 2 kinetics |
| Complete aspirin synthesis (full) | 2,500 XP | Tier 3–4, multi-step |
| Complete weekly project (replication) | 2,500 XP | Tier 2 req, 3 syntheses ≥95% |
| Complete weekly project (total synthesis sprint) | 15,000 XP | Tier 4 req, multi-stage |
| Daily routine 5/5 completion | 1,500 XP + 3 tokens | Daily reset 04:00 local |

---

## 3. Lab Unlock Pacing

### 3.1 Lab Tier vs. Required Skill Level

| Lab Tier | Lab ID | Unlock Condition | XP / Skill Req | Assessment |
|----------|--------|-----------------|----------------|------------|
| 1 | teaching_lab | Start game | None | ✅ Proper — first lab, no barrier |
| 1 | analytical_lab | Quest `quest_01_orientation` complete | Chem basic | ✅ Gates behind tutorial |
| 1 | synthesis_lab | Quest `quest_01_orientation` complete | Chem basic | ✅ Same |
| 2 | electrochem_lab | Skill `physics` Lv 20 | `skill_physics_20` | ⚠️ May be slow — physics track may lag |
| 2 | genomics_lab | Quest `quest_genome` | `skill_biology_25` | ✅ Biology-gated |
| 2 | cell_culture | Skill `biology` Lv 25 | `skill_biology_25` | ✅ |
| 2 | materials_lab | Skill `materials` Lv 20 | `skill_materials_20` | ✅ |
| 2 | forensic_lab | Quest `quest_04_contaminated_batch` | Forensics progression | ✅ Quest-gated |
| 3 | accelerator | Quest `quest_beam` | `skill_physics_30` | ⚠️ High skill req — may gate late-game |
| 3 | fusor_workshop | Skill `physics` Lv 30 | `skill_physics_30` | ⚠️ Same |
| 3 | cleanroom_fab | Skill `engineering` Lv 30 | `skill_engineering_30` | ✅ |
| 4 | pilot_plant | Quest `quest_scaleup` | `quest_scaleup` + Chem 25 + Eng 15 | ✅ Quest + skill gates |
| 4 | cryo_lab | Skill `physics` Lv 35 | `skill_physics_35` | ⚠️ Physics-gated |
| 4 | genomics_lab (duplicate tier) | Already at tier 4 | `skill_biology_25` | ✅ |
| 5 | radiochem_lab | Quest `quest_isotope` | `quest_isotope` | ✅ Quest-gated |
| 5 | microgravity | Quest `quest_orbital` | Eng 50 + Bio 30 | ⚠️ High req — endgame |
| 6 | orbital station 'Apex' | Quest `quest_orbital` | Eng 50 + Bio 30 | Same as above |

### 3.2 Pacing Assessment

**Progression Flow (Typical Player):**

| Stage | Approx. Level | Available Labs | Suits Unlocked |
|-------|---------------|----------------|----------------|
| **Early (Levels 1–10)** | Chem 1–10 | Teaching, Analytical, Synthesis | Lab coat, FR coat, Acid apron |
| **Mid (Levels 10–25)** | Chem 10–25 | Electrochem, Materials, Forensics (quest) | Full-face respirator, Acid suit |
| **Mid-High (Levels 25–40)** | Chem 25–40 | Accelerator, Fusor, Cleanroom | Hazmat A, Lead apron, Lead glass visor |
| **High (Levels 40–60)** | Chem 40–60 | Pilot Plant, Cryo, Radiochem | Cleanroom bunny, Cryo suit, Arc flash |
| **Endgame (Levels 60–100)** | Chem 60–100 | Orbital, Athanor Core | Positive-pressure BSL-4, Remote manipulator |

**Key Observations:**
- ✅ Lab unlocks are well-gated by both skill level AND quest progression
- ⚠️ Physics track (electrochem, accelerator, fusor, cryo) may bottleneck if players focus only on chemistry
- ✅ Quest-gated labs (radiochem, forensic, pilot plant) provide natural pacing breaks
- ⚠️ Tier 5–6 labs (microgravity, orbital) require endgame skill investment (50+) — appropriate for late-game

### 3.3 Recommendations

1. **Add a low-skill electrochem accessibility path** — perhaps a "basic electrochemistry" tutorial at Chem 10 that unlocks the electrochem_lab at Chem 15 (instead of 20)
2. **Consider reducing physics unlock reqs by 5 levels** or add a "cross-track" alternative (e.g., Chem 25 + Eng 15 → accelerator at Chem 25)
3. ✅ Keep quest-gated locks — they provide narrative pacing and prevent sandbox mode from being available too early

---

## 4. Quest Reward Distribution Audit

### 4.1 Quest XP Rewards

| Quest | Tier | XP Reward | Safety Max | IP Reward | Money | Reputation |
|-------|------|-----------|------------|-----------|-------|------------|
| quest_01_orientation | 1 | 500 | 100 → A+ | 0 | 500 ₡ | 5 Academic |
| quest_02_iodine_clock | 2 | 750 | — | 0 | 750 ₡ | 10 Academic |
| quest_03_bz_oscillator | 3 | 1,200 | — | 0 | 1,200 ₡ | 15 Academic |
| quest_04_contaminated_batch | 4 | 1,600 | — | 0 | 1,600 ₡ | 20 Forensics |
| quest_05_quiet_synthesis | 5 | 2,200 | — | 0 | 2,200 ₡ | 25 Syndicate |
| quest_06_riverbank_contract | 6 | 3,000 | — | 0 | 3,000 ₡ | 30 Orbital |

**Cumulative XP from all 6 quests:** 9,250 XP  
**Average per quest:** ~1,542 XP

### 4.2 Sustainability Analysis

**XP Economy:**
- **Daily routine** (5/5 completion): 1,500 XP + 3 tokens per day ≈ 10,500 XP/week
- **Weekly projects**: 2,500–15,000 XP depending on tier
- **Quest chain** (all 6): 9,250 XP one-time
- **Steak multipliers**: Safety A+ gives 3★ = full XP; C warning gives 1★ = 1/3 XP

**Sustainability:** ✅ **Healthy** — daily routines + weekly projects provide steady XP flow. Quest chain is a one-time campaign (9.25k ≈ 1/11th of soft-cap at 100).

**IP Economy:**
- Currently **no IP (Invention Points) system** in evidence — only XP and money
- ⚠️ **Gap:** Should design IP economy if invention/research crafting is planned
- IP could be awarded for: novel syntheses (codex entries), apparatus innovations, reagent discoveries

**Money Economy:**
- Starting: 2,000 ₡
- Full suit set cost: ≈ 15,000 ₡
- Weekly project earnings: 2,500–15,000 ₡
- **Sink balance:** ✅ — weekly projects can fund full suit set in 1–6 weeks depending on tier

### 4.3 Reward Distribution Assessment

| Metric | Value | Assessment |
|--------|-------|------------|
| **Quests vs. Daily** | 6 quests ≈ 4 days of dailies | ✅ Quests are milestone milestones, dailies are steady flow |
| **XP per Hour** | Core synthesis ≈ 2,500 XP / 15 min = 10,000 XP/hr | ✅ Within design target (35 min/session ≈ 23k XP) |
| **Safety Penalty Impact** | F shutdown reduces safety score → 1★ → 1/3 XP multiplier | ✅ Strong incentive maintenance |
| **Money/XP Ratio** | 500 ₡ / 500 XP = 1 ₡/XP base rate | ✅ Consistent across tiers (scales 1:1) |

### 4.4 Recommendations

1. ✅ **Add IP (Invention Points) reward type** to quests for novel syntheses — feed into crafting/research subsystem
2. ✅ **Add reputation tiers** beyond " friendly/"trusted"/"respected" for companion unlock at Rep 80+
3. ⚠️ **Balance safety score impact** — currently F shutdown (score < 50%) gives 1★ XP multiplier. Consider gradual scaling:
   - A+ (95–100%): 3★ ×1.0 normal
   - A (85–94%): 2★ ×0.85
   - B (70–84%): 1★ ×0.65
   - C (50–69%): 0.5★ ×0.4
   - F (<50%): 0★ ×0.2 (but quest still completable, just no stars)
4. ✅ **Keep money rewards scaling** — tier 6 quest 3,000 ₡ vs tier 1 500 ₡ = 6× scaling, appropriate for difficulty

---

## 5. Difficulty Curve Design

### 5.1 Early / Mid / Late Game Objectives

| Phase | Player Level | Primary Objectives | Difficulty Estimate |
|-------|--------------|-------------------|---------------------|
| **Early Game** | Levels 1–10 | Orientation, first synthesis (aspirin), basic lab access | ⭐⭐☆☆☆ — Tutorial density high, mechanics introduction |
| **Mid Game** | Levels 10–40 | Multiple syntheses, first lab upgrades, companion unlocks | ⭐⭐⭐☆☆ — Variety increases, resource management begins |
| **Late Game** | Levels 40–80 | Pilot plant, radiological labs, full companion collection | ⭐⭐⭐⭐☆ — Complex multi-step syntheses, safety criticality |
| **Endgame** | Levels 80–120 | Athanor Core, orbital labs, prestige | ⭐⭐⭐⭐⭐ — Mastery optimization, min-maxing, legacy progression |

### 5.2 Early Game Difficulty Anchors

| Objective | Estimated Time | Success Rate Target | Failure Penalty |
|-----------|---------------|---------------------|-----------------|
| Orientation quest (all objectives) | 20 min | ≥90% on first attempt | Safety -20 → grade B, XP ×0.65 |
| First aspirin synthesis | 30 min | ≥75% at purity ≥98% | Chemical exposure + safety penalty, lose reagents if >90% impurity |
| Single titration | 3–5 min | ≥80% endpoint detection | Variable-ratio; miss → retry, no penalty beyond time |

### 5.3 Mid Game Difficulty Anchors

| Objective | Estimated Time | Success Rate Target | Failure Penalty |
|-----------|---------------|---------------------|-----------------|
| Weekly project (replication) | 45–60 min | ≥70% complete 3/5 syntheses ≥95% | Safety penalties accumulate, streak may break |
| Cross-track milestone (Chem 25 + Bio 10) | Varies | Gate for lab unlocks | No direct penalty, but gates content access |
| Companion unlock (Rep 80) | 3–5 quests | ≥50% rep gain per quest | Loss of companion abilities if rep decays |

### 5.4 Late Game Difficulty Anchors

| Objective | Estimated Time | Success Rate Target | Failure Penalty |
|-----------|---------------|---------------------|-----------------|
| Pilot plant scale-up | 60–120 min | ≥60% yield ≥90% | Thermal runaway risk → safety violation, potential injury |
| Radiochemistry (isotope handling) | 45–90 min | ≥70% safety compliance | Radiation dose → permanent injury if >100 mSv |
| Full companion collection (10/10) | 10+ quests | ≥40% rep gain per quest | Long-term grind — grace tokens mitigate |

### 5.5 Difficulty Scaling Mechanisms

1. **Adaptive Weekly Projects** (A/B test candidate): Fixed difficulty vs. adaptive based on player's average skill level across tracks
2. **Safety Score-Dependent Rewards**: 
   - Safety A+: Full XP + bonus reagent
   - Safety C: Reduced XP + safety drill daily routine unlock
3. **Catch-Up Mechanics** (A/B test):
   - Literature Review daily gives bonus XP for lowest-skill track
   - Weekly "Replication Study" always available at Chem 10 req regardless of actual level

---

## 6. Companion Engagement Pacing

### 6.1 Companion Unlock Conditions

| Companion | Faction | Unlock Condition | XP / Skill Req | Assessment |
|-----------|---------|-----------------|----------------|------------|
| Dr. Thorne | Academic | Chem 25 + Rep 80 | Chem 25 (mid-game) | ✅ Appropriate — mid-game goal |
| "Nails" Morau | Syndicate | Forensics 15 + Rep 80 | Forensics 15 (mid-high) | ✅ |
| Agent Reyes | Law Enforcement | Forensics 30 + Rep 80 | Forensics 30 (mid-high) | ✅ |
| Prof. Kowalski | Industrial | Eng 25 + Rep 80 | Eng 25 (mid-game) | ✅ |
| Dr. Sato | Orbital | Bio 30 + Eng 50 | Bio 30 + Eng 50 (endgame) | ✅ — late-game reward |

### 6.2 Reputation Gain Rates

| Action | Rep Gain | Max per Day | Notes |
|--------|----------|-------------|-------|
| Quest completion | 5–30 per quest | ~90 (all 6 quests) | Varies by quest tier |
| Daily routine 5/5 | 10 per day | 10 | Steady, capped |
| Weekly project completion | 50–200 per project | 1 per week | High reward, infrequent |
| Companion gift/interaction | 5–15 per gift | Unlimited | Social sink |

**Time to first companion (Dr. Thorne):** ≈ 3–5 days of active play (quests + dailies) or ≈ 1 week of casual play.

### 6.3 Companion Bonding Economy

| Bond Level | Rep Required | Unlock | Cost |
|------------|-------------|--------|------|
| **Stranger** | 0–30 | Basic dialogue | — |
| **Acquaintance** | 31–60 | Access to passive bonus | — |
| **Trusted** | 61–80 | Active ability (1×/session) | — |
| **Valued** | 81–100 | Additional passive bonus | — |
| **Friend** | 101–150 | Unique cosmetic gift | Daily token cost: 1 |
| **Confidant** | 151+ | Story branch, narrative fork | Daily token cost: 2 |

### 6.4 Pacing Assessment

✅ **Good pacing:** First companion unlock at ~Chem 25 (mid-game, ~15–20 hours).  
✅ **Bonding is gradual:** Trusted status requires deliberate play, not grind.  
⚠️ **Orbital companion (Dr. Sato)** requires Eng 50 + Bio 30 — may be gated too late for players who don't diversify tracks.  
**Recommendation:** Add a "bridge" companion unlock at Eng 30 + Bio 25 (earlier, lower-tier companion) for players focusing on single tracks.

### 6.5 Recommendations

1. Add a **mid-game companion** at Eng 20 + Chem 20 (faction-neutral, e.g., lab assistant) to bridge the gap before Thorne at 25
2. Add **companion rep decay** if not interacted with for 7 real-world days — encourages regular engagement
3. ✅ Keep current rep gain rates — they feel natural and unforced

---

## 7. Companion Care/Bonding Economy

### 7.1 Time & Resource Costs

| Activity | Time Cost | Resource Cost | Rep Gain | Frequency |
|----------|-----------|---------------|----------|-----------|
| **Companion dialogue** | 1–3 min | None | 1–5 rep | Unlimited, cooldown 5 min |
| **Companion gift** | 2 min | Reagent cost (varies) | 5–15 rep | 1 per companion per day |
| **Companion ability use** | 0 min (instant) | None (cooldown 1×/session) | 0 rep | 1× per companion per session |
| **Quest with companion** | +15 min per quest | None | +10 rep per quest | Once per companion |

### 7.2 Resource Sinks for Bonding

| Companion | Gift Cost (per day) | Effect | Availability |
|-----------|---------------------|--------|--------------|
| Dr. Thorne | Reagent: 1× salicylic_acid or 1× universal_indicator | +10 rep, "Peer Review" ability (reroll 1 purity check) | Unlocked at Chem 25 |
| "Nails" Morau | Reagent: 1× ninhydrin_spray_aerosol or 1× latent_black_fingerprint_powder | +10 rep, "Diversion" ability (hide 1 clandestine action) | Unlocked at Forensics 15 |
| Agent Reyes | Reagent: 1× luminol_free_base or 1× sodium_perborate_oxidizer | +10 rep, "Warrant" ability (forensic scan any lab) | Unlocked at Forensics 30 |
| Prof. Kowalski | Reagent: 1× heat_transfer_silicone_fluid or 1× calibration_thermistor_probe | +10 rep, "Pilot Run" ability (simulate synthesis without materials) | Unlocked at Eng 25 |
| Dr. Sato | Reagent: 1× deuterated_solvents_full_library or 1× nanopore_flow_cell_r10_4 | +10 rep, "Microgravity Drop" ability (1 free orbital run) | Unlocked at Bio 30 + Eng 50 |

### 7.3 Bonding Economy Assessment

✅ **Resource costs are meaningful but not prohibitive:** Gift reagents are typically available from recent syntheses or can be crafted.  
✅ **Daily token system integrates naturally:** 1 token per companion gift per day = 5 tokens max (all companions).  
✅ **Cooldown of 1×/session on abilities prevents spamming.**  
⚠️ **Late-game reagents become scarce:** Dr. Sato's gifts require orbital/microgravity reagents that may not be available until endgame.  
**Recommendation:** Add a "synthetic substitute" crafting recipe for each companion gift reagent, unlocked at appropriate skill level.

### 7.4 Recommendations

1. Add **companion gift substitute recipes** for all 5 companions using common reagents (unlocked at appropriate skill level)
2. Add **companion rep decay** — -5 rep/week if no interaction, mitigated by daily dialogue (1 rep/day)
3. ✅ Keep current bonding economy — well-balanced between engagement and grind

---

## 8. Hard Cap and Anti-Exploit Rules

### 8.1 Maximum Limits

| Limit | Value | Rationale |
|-------|-------|-----------|
| **Max Skill Level** | 120 (soft cap 100) | Classic RPG progression ceiling; 120 is post-mastery |
| **Max Lab Tier** | 6 (Orbital 'Apex') | Content tier cap; no tier 7 planned |
| **Max Suit Tier** | 6 (Positive-pressure BSL-4 / Remote manipulator) | Safety ceiling — beyond this, simulation abstracts |
| **Max Codex Categories** | 6 (Analgesics, Dyes, Precursors, Natural Products, Forensic Standards, Psychoactives) | Collection completion goal |
| **Max Simultaneous Quests** | 2 (unlock at Eng 25 + "Parallel Synthesis" streak reward) | Prevents overwhelm, encourages focus |
| **Max Daily Tokens** | 5 | Prevents hoarding, encourages daily engagement |
| **Safety Score Hard Floor** | 0 (F grade triggers stop-work) | Game design — cannot progress with unsafe lab |
| **Radiation Annual Limit** | 20 mSv / year (ICRP) | Real-world occupational limit; game anchors to reality |
| **Radiation Hard Limit** | 1,000 mSv acute | Sickness territory — hard stop for extreme neglect |

### 8.2 Anti-Exploit Rules

1. **XP Batching Prevention:** Daily routine XP awarded only once per 24h window (reset 04:00 local). Cannot "farm" by time-traveling.
2. **Streak Break Grace:** 1 Daily Token can preserve one safety or synthesis streak break per 14 real-world days. Tokens are earned, not purchasable.
3. **Quests Per Day Limit:** Maximum 3 quest completions per real-world day (prevents marathon sessions).
4. **Safety Score Decay Floor:** Safety score cannot decay below 20% even with consecutive violations (player always has "minimum safe floor").
5. **Radiation Dose Capping:** Annual radiation accumulation caps at 50 mSv in-game (beyond hard ICRP 20 mSv, game tracks "legacy exposure" as narrative flavor only).
6. **Prestige Reset Safeguard:** On Athanor Ascension, all skill levels reset to 1, but Codex entries, companion relationships, and cosmetic titles are permanently retained. XP curve modifier ×1.5 applies to new run.

### 8.3 Balance Scorecard — Metrics to Track

| Metric | Target | Current (Est.) | Source |
|--------|--------|----------------|--------|
| **Time-to-First-Synthesis** | ≤ 30 min | ~25 min (aspirin) | Quest timing data |
| **D1 Retention** | ≥45% | N/A (not yet tracked) | Session analytics needed |
| **D7 Retention** | ≥25% | N/A | Weekly project start rate |
| **D30 Retention** | ≥15% | N/A | Prestige-eligible players |
| **Avg Session Length** | 35 min | ~20–45 min (varies) | Core loop completions |
| **Daily Routine Completion** | ≥60% DAU | N/A | 3/5 categories done |
| **Streak Maintenance** | ≥40% DAU | N/A | Safety streak ≥7 days |
| **Codex Discovery Rate** | 2.5/session | N/A | New entries per play session |
| **Cross-Track Engagement** | ≥70% | N/A | Players with ≥2 tracks >Lvl 10 |
| **Safety Grade Distribution** | A+: 25%, A: 35%, B: 25%, C: 10%, F: 5% | N/A | Quest safety scoring |
| **Companion Unlock Rate** | ≥50% by Chem 25 | ~60% (Dr. Thorne) | Rep + skill gate data |
| **Prestige Take-Up** | ≥10% of endgame players | N/A | After all tracks 100 |

### 8.4 Data Sources for Balance Tuning

| Data Type | Collection Method | Frequency |
|-----------|-------------------|-----------|
| **XP gain/loss per action** | SkillManager signal logging | Per action |
| **Safety score changes** | QuestManager trigger logging | Per violation |
| **Quest completion rates** | QuestManager completion tracking | Per quest |
| **Companion rep gain/loss** | Companion system logging | Per interaction |
| **Daily routine completion** | SaveManager daily reset data | Daily |
| **Weekly project progress** | SaveManager weekly reset data | Weekly |
| **Codex discovery timestamps** | CodexManager registration | Per discovery |
| **Time-to-synthesis** | HUD timer + objective timestamps | Per synthesis |
| **Suit purchase frequency** | Economic system logging | Per purchase |
| **Radiation exposure** | PlayerVitals add_radiation logging | Per event |

### 8.5 Playtests Needed

| Playtest Type | Objective | Duration | Key Metrics |
|---------------|-----------|----------|-------------|
| **New Player Onboarding** | Verify tutorial flow, time-to-first-synthesis, safety learning curve | 2–3 players, 2 hrs each | D1 retention, time-to-first-synthesis, safety violation rate |
| **XP Curve Validation** | Confirm XP rewards feel proportional across all actions and tiers | 5–10 players, 1 wk each | Leveling speed, soft cap feel, prestige take-up rate |
| **Lab Unlock Pacing** | Verify players encounter new labs at expected skill milestones | 5 players, 2 wks each | Lab unlock timing vs. skill level, bottlenecks |
| **Companion Bonding** | Verify rep gain rates feel natural, not grindy | 5 players, 3 wks each | Time to first companion, bonding pace, gift efficacy |
| **Safety Economy** | Verify safety score penalties are deterrent but not frustrating | 5 players, 1 wk each | Safety grade distribution, streak break frequency, token usage |
| **Endgame/Prestige** | Validate Athanor Ascension flow and XP multiplier feel | 3 players, 2 wks each post-100 | Prestige take-up, re-leveling speed, content replay |
| **Daily/Weekly Systems** | Tune daily routine categories, weekly project difficulty scaling | 5 players, 2 wks each | Routine completion rate, weekly project selection, A/B test data |

---

## 9. Summary & Next Steps

### 9.1 Key Balance Findings

1. ✅ **XP curve is well-designed** — Classic mastery formula with soft cap at 100 and exponential climb to 120 feels natural
2. ✅ **Lab unlock pacing is solid** — quest + skill gates provide natural progression without hard walls
3. ✅ **Quest reward distribution is sustainable** — daily routines + weekly projects + quest chain cover all progression axes
4. ⚠️ **Physics track may bottleneck** — consider reducing unlock reqs by 5 levels or adding cross-track alternatives
5. ✅ **Companion pacing is appropriate** — first companion at ~Chem 25 (mid-game, 15–20 hours)
6. ✅ **Safety economy provides strong incentives** — grade-dependent XP multipliers create meaningful choices
7. ✅ **Anti-exploit rules are well-scoped** — daily limits, streak grace, prestige safeguards all in place

### 9.2 Immediate Tuning Priorities

1. **Reduce physics lab unlock reqs** by 5 levels (electrochem at 15 instead of 20, accelerator at 25 instead of 30)
2. **Add IP (Invention Points) reward type** to quests for novel syntheses
3. **Add companion gift substitute recipes** for all 5 companions using common reagents
4. **Implement safety score gradual scaling** (A+/A/B/C/F with progressive XP multipliers rather than binary 3/2/1/0.5/0.2)
5. **Add mid-game companion bridge** at Eng 20 + Chem 20 for single-track players

### 9.3 Playtest Schedule (Next 4 Weeks)

| Week | Focus | Players |
|------|-------|---------|
| Week 1 | New player onboarding + XP curve feel | 5 players |
| Week 2 | Lab unlock pacing + safety economy | 5 players |
| Week 3 | Companion bonding + daily routines | 5 players |
| Week 4 | Endgame/prestige validation (post-100) | 3 players |

---

*Balance design document — live version. Last tuned: 2026-11-06. For tuning changes, update this document and record diff in `design/gdd/balance_changelog.md`.*