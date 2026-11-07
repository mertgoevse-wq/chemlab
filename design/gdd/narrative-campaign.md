# ChemLab — Campaign Bible (Act I–VI)

**Runtime source of truth:** `game/scripts/quests/quest_manager.gd` (`_initialize_quest_catalog`).
**Design mirror:** `design/gdd/data/quests.json` (schema reference only; the runtime catalog is what ships).
**HUD presentation:** `game/scripts/quests/quest_overlay.gd` — the `briefing` and `speaker` fields are displayed as an incoming-transmission card when `quest_started` fires.

This document is written in two hands, deliberately: **contract design** (what the player does, with OSHA/EPA references) and **story beats** (what the player feels, in the room). Every contract below exists in code today and is reachable through the chain.

---

## Cast

| Character | Role | Voice |
|---|---|---|
| **Prof. Aris Thorne** | Academic synthesis lead, Bay 1 | Sparse, exact, allergic to enthusiasm. Judges people by their logbooks. |
| **Dr. Lena Voss** | QC / analytical lead, Bay 2 | Commercial, unsentimental, defends the signature more than the result. |
| **Mara Kestrel** | Grey-market broker, Riverside Garage | Charming, transactional, never lies about anything that can be checked. |
| **Inspector Hale** | Regional water authority | Tired, procedural, wants evidence that survives a courtroom. |

The institute, the supplier, and the river plant are all unnamed on purpose: the player's loyalty is the variable, not the institution.

---

## Act I — Competence

### `quest_01_orientation` — Orientation & Safety Protocols (Tier 1, 500 XP)
- **Contract:** PPE, balance tare, 25.0 mL HCl, 3 drops phenolphthalein, titrate to a persistent pink at pH 8.2–9.0.
- **Story beats:** Thorne watches the PPE station, not the flask; the air handlers cycle while the balance settles; the first pink swirl holds and he writes one word — *keepable*.
- **Teaches:** the two unforgivables: unprotected eyes and an untared balance. Both are enforced as real penalties, not dialogue.

### `quest_02_iodine_clock` — Landolt Iodine Clock (Tier 2, 750 XP)
- **Contract:** KI + starch, add H₂O₂, measure the sudden triiodide–starch transition.
- **Story beats:** nothing happens for an embarrassing moment, then the beaker turns ink-blue between heartbeats; Voss taps the stopwatch twice as if doubting it.
- **Teaches:** rate as a measured quantity, and that a result arriving "all at once" is still kinetics.

### `quest_03_bz_oscillator` — Belousov–Zhabotinsky (Tier 3, 1200 XP)
- **Contract:** malonic acid to 45 °C, bromate, ferroin; observe periodic wave fronts.
- **Story beats:** rust-red until blue rings bloom like slow thunder; Thorne stops narrating; *"a clock with no hands — write down how fast it lies to you."*
- **Teaches:** non-equilibrium systems. First hint that the lab is a place where patterns are evidence.

---

## Act II — Evidence

### `quest_04_contaminated_batch` — The Contaminated Batch (Tier 4, 1600 XP)
- **Contract:** isolate sample QC-4471 under the hood, flame-test on platinum, argentometric chloride titration with 0.05 M AgNO₃ to the brick-red chromate endpoint, file a signed report.
- **Story beats:** the bottle has no label, only a dried salt smear; the flame burns a stubborn brick red (strontium, or a clever counterfeit); Voss reads the report twice and signs beneath the player's name without comment.
- **Design intent:** the first contract where the answer is *not* the point — the defensible record is. The moral pressure is commercial, not criminal.
- **References:** OSHA 1910.1450(c), ASTM E1613, EPA 9253, GLP 21 CFR Part 58.

---

## Act III — Complicity

### `quest_05_quiet_synthesis` — The Quiet Synthesis (Tier 5, 2200 XP)
- **Contract:** dry assembly, reflux at 78 °C, recrystallize from hot ethanol, decide disposition.
- **Moral fork (`moral_fork` in data):**
  - `sell_batch` — "Hand over the batch, take the money" → grey reputation, −5 safety.
  - `keep_evidence` — "Seal a sample and call the inspector" → clean reputation, +5 safety.
- **Story beats:** the condenser clicks as it heats; Mara keeps the radio low enough to hear the street; the reflux settles into a rhythm; at the door she doesn't ask what was decided, only whether the glassware is clean.
- **Design intent:** the same physical skill set as Act I, pointed at a different customer. The fork is legible before it is irreversible; there is no "correct" chemistry, only a chosen disposition.
- **Tone constraint:** the fiction names a proprietary precursor (`Proprietary_Precursor_G7`) and never a real illicit route or recipe. No synthesis instructions for controlled substances appear in design docs, code, or UI.

---

## Act IV — Field

### `quest_06_riverbank_contract` — Riverbank Contract (Tier 6, 3000 XP)
- **Contract:** reach three sites, collect preserved samples with chain of custody, calibrate the portable spectrometer, submit to Hale.
- **Story beats:** Site A is clean enough to drink from, if you were foolish; at the outfall the water runs warm and smells faintly of solvent; Hale looks at the downstream reading and says nothing for a long time.
- **Design intent:** moves the skill set out of the building. This is the bridge into the open-world layer: field kits, travel, weather, and evidence that must survive transport.

---

## Chain and gating

```
01 orientation ─▶ 02 iodine clock ─▶ 03 BZ oscillator
      └─▶ 04 contaminated batch ─▶ 05 quiet synthesis ─▶ 06 riverbank contract
```

- Each contract declares `next_quest_id`. On completion, `_complete_active_quest()` promotes the successor from `LOCKED` to `AVAILABLE` and emits `quest_unlocked`.
- Objectives use their own ids, so the shared physical interactions (tare, pour, indicator, heat) fall through to the **active** objective instead of being dropped. This is what lets later contracts be playable with the same hands.
- Safety score gates star ratings (3★ ≥ 90, 2★ ≥ 75, 1★ below) and is the only cross-contract persistent judgement.

## Open threads for the next writing pass

1. **Act V — Consequence.** The `moral_fork` choice should surface in Act V: the buyer's network or the inspector's case reacts to `sell_batch` vs `keep_evidence`.
2. **Companion beats.** `game/data/companions/species_database.json` already gives each companion a nose for something. Give one of them a line in the riverbank contract (solvent detection at the outfall).
3. **Failure writing.** Every contract currently has one path. Authored failure beats (over-titration, contaminated sample, missed hold time) would make the penalties feel like story rather than score.
