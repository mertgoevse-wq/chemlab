# Pyrotechnics Test Bay — Level Design

**Status:** implemented scene `game/scenes/laboratories/pyrotechnics_lab.tscn`
**Framework:** `tools/vendor/awesome-prompts/prompts/Game_Level_Designer.txt`
**Related:** `design/act_ii_nitrogen_age.md`, `game/scripts/labs/pyrotechnics_model.gd`

---

## 1. Level concept

A licensed Class 1.4 test bay is a room designed around **what must not happen**. The player
does not explore a dungeon; they move through a sequence of controlled boundaries, and every
boundary is a gameplay verb: badge in, ground the bench, weigh inside the magazine limit,
carry the sample to the pad, record the burn, clean the pad, file the paperwork.

**Narrative purpose:** the bay is where the player learns that safety is not a dialog box.
It is a floor plan.

**Emotional arc:** procedure → precision → controlled danger → relief → professional pride.

**Reference points:** a real licensed display-magazine site (distance, earth berms, isolated
magazine), a university combustion lab (burn hood, load cell, high-speed camera), and the
Athanor fiction's insistence that every number on screen comes from somewhere.

---

## 2. Spatial architecture

### 2.1 Zoning (implemented as a 3D room plus UI stations)

```
                 NORTH (outdoor, behind earth berm)
        ┌──────────────────────────────────────────────┐
        │  BURN PAD            120 m exclusion zone    │
        │  (open, no roof)     fallout radius marker   │
        └───────────────▲──────────────────────────────┘
                        │ blast wall / viewing window
        ┌───────────────┴──────────────────────────────┐
        │  TEST CELL (indoor)                          │
        │  ┌──────────┐   ┌──────────┐   ┌──────────┐ │
        │  │ Burn     │   │ Prep     │   │ Control  │ │
        │  │ station  │   │ bench    │   │ desk     │ │
        │  └──────────┘   └──────────┘   └──────────┘ │
        │        ▲              ▲              ▲       │
        │        └────── aisle ─┴──────────────┘       │
        └───────────────▲──────────────────────────────┘
                        │ interlock door
        ┌───────────────┴──────────────────────────────┐
        │  MAGAZINE ANNEX (Type D)                     │
        │  oxidiser shelf │ fuel shelf │ logbook       │
        └──────────────────────────────────────────────┘
```

### 2.2 Metrics that matter

| Element | Dimension | Why |
|---|---|---|
| Main aisle | 1.6 m clear | Two people in PPE pass without turning; a stretcher fits. |
| Prep bench depth | 0.75 m | Arm's reach to the back of the bench without leaning over a composition. |
| Burn station to blast wall | ≥2.5 m | Keeps the operator outside the flash envelope during a 25 g burn. |
| Magazine door to oxidiser shelf | 1.2 m | No stored oxidiser behind the door swing. |
| Control desk sightline | direct to burn pad | The operator can see the pad without leaving the interlock. |
| Viewing window | 0.9 × 0.6 m, laminated | Reads as a safety boundary, not a shop window. |

### 2.3 Sightlines and landmarks

- The **burn pad** is the visual landmark: a pale concrete circle against dark ground, visible
  from the interlock door. The player always knows where the dangerous thing happens.
- The **magazine** is deliberately quieter: grey, labelled, no glow. It should read as
  storage, not treasure.
- The **control desk** faces the pad. The player's back is never to the burn.
- The **logbook** is the only warm-coloured object in the bay. It is the one thing the player
  is meant to touch at the end.

---

## 3. Flow and pacing

| Phase | Player path | Tension | Gameplay |
|---|---|---|---|
| **Badge in** | Airlock → control desk | low | Read the licence board, confirm quantity-distance and wind limit. |
| **Prep** | Control desk → prep bench | medium | Weigh oxidiser and fuel separately; static-ground the bench. |
| **Magazine** | Prep bench → annex → prep bench | medium | Reconcile stores; carry only the batch you are licensed for. |
| **Burn** | Prep bench → burn station → interlock | high | Load the pad, retreat behind the wall, arm the remote, record the rate. |
| **Clean** | Burn station → waste bin → logbook | low | Wet-down, sweep, log the residue and the result. |

The loop is intentionally short (5–8 minutes) because the bay is a **side-arc laboratory**,
not a campaign chapter. The player should leave with one number (mm/s), one colour
(nm), and one signed page.

---

## 4. Challenge design

Not combat. The challenges are **procedure under constraint**:

1. **Quantity-distance puzzle** — the player must place the pad and the magazine at legal
   separations; moving either invalidates the licence.
2. **Static control** — a grounding check that fails if the player skips the bench strap.
3. **Oxidiser/fuel separation** — the magazine has two shelves; mixing them is an immediate
   fail state (contamination, not explosion).
4. **Burn-rate measurement** — a real timing/measurement task: the player reads the burn
   front against a scale, not a scripted animation.
5. **Display choreography** — nine cues, each with duration, colour, wind limit and abort
   condition. The constraint is the fallout radius, not the budget.

**Failure states are educational:** a skipped ground strap produces a "no reading" result and
a safety note, not a game over. A mixed magazine produces a contamination lockout that the
player must clean up. Only an armed pad with a person inside the exclusion zone is a hard fail.

---

## 5. Accessibility and readability

- All hazard boundaries use shape and label, not colour alone: dashed floor markings,
  GHS pictograms, and a written zone name on the floor.
- The burn-pad timer uses a large numeric readout plus a progress ring, so it is readable
  at a distance and without audio.
- The control desk buttons are ordered by procedure, not by importance; the next legal
  action is always the leftmost enabled control.
- No quick-time events. The bay rewards preparation, not reflexes.

---

## 6. Performance budget (Dell Latitude 5530, Iris Xe)

| Budget | Target | Implementation |
|---|---|---|
| Draw calls in bay | < 120 | Reuse materials; merge static room geometry; no per-screw meshes. |
| Dynamic lights | 3 (key, pad flood, control desk) | No shadows on the desk light. |
| Particles | 0 until burn; one GPUParticles3D burst | Burn effect is pooled and reused. |
| Textures | 1 epoxy roughness noise, 1 steel ORM | No 4K maps; 256–512 px is enough at gameplay distance. |
| Physics | Static room + one Area3D per station | No rigid-body simulation for the burn. |
| Frame target | 60 FPS at 1280×720, 30 FPS floor | The bay is a side room, not the open world. |

---

## 7. Implemented scene mapping

`game/scenes/laboratories/pyrotechnics_lab.tscn` currently provides:

- a 3D test cell with prep bench, burn pad, blast shield, magazine annex and control desk;
- UI stations for licensing, black-powder batch, colour stars and nine-cue choreography;
- the offline model in `game/scripts/labs/pyrotechnics_model.gd`:
  oxygen balance, burn rate, flame colour and hazard classification;
- six formulations in `game/data/synthesis/pyrotechnics.json`.

**Deliberate gaps (next pass):**

- The exclusion zone is represented by a floor marking, not a full 120 m outdoor terrain.
  A full outdoor pad would cost more draw calls than the side arc justifies.
- The burn animation is a timed shader/particle burst, not a fluid simulation. The number
  the player records comes from the model, not from the visual.
- The magazine annex is a single room; a second locked shelf is planned but not built.

---

## 8. Safety framing

The bay is a **licensed test range**, not a workshop. The design teaches:

- quantity-distance and exclusion zones;
- static grounding and magazine separation;
- burn-rate measurement as a characterisation method;
- display choreography under wind, noise and fallout constraints.

It does **not** teach device construction, composition ratios for effect, or initiation
systems. The black-powder quest uses the historical 75/15/10 reference only to discuss
fuel-rich formulation and burn rate; the player never assembles a device.
