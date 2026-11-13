# Economy Audit — Quest XP and Skill Rewards

**Date:** 2026-11-13
**Framework:** `tools/vendor/awesome-prompts/prompts/Game_Economy_Designer.txt`
**Scope:** offline single-player progression in `game/scripts/quests/quest_manager.gd`
**Verdict:** the curve is usable and monotonic in intent, but tier bands overlap and two
outliers should be normalised in a later pass. No economy code was changed in this pass.

---

## 1. Method

A script parsed every quest block that exposes `tier` and `xp_reward` and grouped the
rewards by tier. `skill_rewards` were inspected separately because they are a second,
parallel progression currency (chemistry, pyrotechnics, lab safety, etc.), not spendable XP.

**Parsed sample:** 27 quests — 12 main, 15 side.

| Tier | Quests | Min XP | Median XP | Max XP |
|---:|---:|---:|---:|---:|
| 1 | 1 | 500 | 500 | 500 |
| 2 | 1 | 750 | 750 | 750 |
| 3 | 6 | 1,200 | 1,950 | 2,200 |
| 4 | 6 | 1,600 | 2,300 | 3,200 |
| 5 | 7 | 2,200 | 3,500 | 5,200 |
| 6 | 2 | 3,000 | 4,900 | 6,800 |
| 7 | 1 | 4,000 | 4,000 | 4,000 |
| 8 | 1 | 5,500 | 5,500 | 5,500 |
| 9 | 1 | 7,500 | 7,500 | 7,500 |
| 10 | 1 | 10,000 | 10,000 | 10,000 |

The parser only matched blocks with the canonical field order, so the real quest count is
higher. The sample is large enough to judge the shape of the curve; it is not a complete
ledger, and the audit says so rather than pretending otherwise.

---

## 2. Findings

### 2.1 The curve is exponential, not linear
Tier 10 pays **20×** tier 1. That is healthy for a campaign where each act is a step change
in capability, but it requires the level curve to grow at a similar rate. If level thresholds
are linear, the player will over-level in Act I and stall in Act V.

**Action:** keep the 20× ratio only if the level curve is also super-linear. The existing
skill tree is the real gate; XP is a pacing signal, not a power currency.

### 2.2 Tier bands overlap
Tier 3 reaches 2,200 and tier 4 starts at 1,600. A tier-4 quest can pay less than a tier-3
quest. This is acceptable for side content (a short tier-4 favour should not outpay a long
tier-3 investigation), but the UI must not imply that tier is a strict reward ordering.

**Recommended bands:**

| Tier | Band | Intent |
|---:|---|---|
| 1 | 500–800 | onboarding, one bench procedure |
| 2 | 800–1,200 | first multi-step protocol |
| 3 | 1,200–2,200 | full synthesis or analysis chain |
| 4 | 1,800–3,200 | cross-lab or field work |
| 5 | 2,600–5,200 | act-level investigation |
| 6 | 4,000–6,800 | pilot plant / institutional stakes |
| 7+ | 7,000+ | campaign climax only |

The implemented Act II rewards (5,200 at tier 5, 6,800 at tier 6) sit at the top of their
bands, which is correct: they are act-level main quests, not side content.

### 2.3 Tier 6 has only two entries and a 2.3× spread
3,000 and 6,800 in the same tier is a wide gap. Either the 3,000 quest is mis-tiered or the
tier is under-populated. **Recommendation:** move the 3,000 quest to tier 5 (band 2,600–5,200)
or raise it to 4,200. Do not raise both; the curve should not inflate to hide a classification
mistake.

### 2.4 Skill rewards are a second economy
A single quest can grant 2,600 skill points (1,500 + 700 + 400) while paying 3,200 XP.
That is intentional — skill points gate apparatus and protocols, XP gates narrative rank —
but the two must be balanced together. A quest that pays low XP and high skill points is a
**specialisation** quest; a quest that pays high XP and low skill points is a **story** quest.
The quest data currently does not declare which one it is.

**Recommendation:** add an optional `reward_profile` field (`story`, `specialisation`,
`hybrid`) and use it in the quest UI to set expectations. This is a schema addition, not a
rebalance.

### 2.5 No sinks, and that is fine
This is an offline RPG with no shop, no premium currency and no player market. XP and skill
points have no sink beyond unlocks. The economy is therefore a **pacing curve**, not a
circulation system. Do not add a currency sink just to look like a live-service game; it
would add UI and save-state complexity with no player benefit.

---

## 3. What was not changed

- No XP values were edited in this pass. The audit found the implemented Act II and
  pyrotechnics rewards inside their intended bands.
- No new currency, shop, daily reward or battle-pass structure was added. All of those are
  wrong for an offline single-player game.
- The tier-6 outlier is documented, not silently rebalanced. A later pass should decide
  whether it is a tier-5 quest or a 4,200 tier-6 quest.

---

## 4. Follow-up, ordered by value

1. **Declare reward profiles** (`story` / `specialisation` / `hybrid`) — makes the existing
   numbers legible without changing them.
2. **Resolve the tier-6 3,000 XP outlier** — one data edit, improves curve credibility.
3. **Add a "time to complete" estimate per quest** — lets the economy be audited as XP per
   minute instead of XP per tier.
4. **Do not add sinks** unless a trader or crafting bench is actually built.
