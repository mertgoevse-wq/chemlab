# Act II — The Nitrogen Age

**Status:** implemented narrative pass (quests live in `game/scripts/quests/quest_manager.gd`)
**Framework:** `tools/vendor/awesome-prompts/prompts/Immersive_Narrative_Designer.txt`
**Related:** `design/narrative_style.md`, `design/pyrotechnics_bay_layout.md`

---

## 1. Vision

**One sentence:** Every fertiliser, every explosive and every protein begins with fixed nitrogen, and the player has to decide who gets to own that fact.

**Thematic pillars**

| Pillar | Question the player is asked |
|---|---|
| Fixation | Can you turn an inert gas into something alive — and should you? |
| Scale | A bench result is a proof; a pilot plant is a political act. |
| Complicity | Thorne needs your clean record more than he needs your hands. |
| Dual use | The same ammonia that feeds a province also feeds a war. |

**Emotional arc:** curiosity → competence → unease → complicity → consequence.
The player should end Act II proud of a working reactor and uncomfortable about who is
standing behind them when it starts.

**Tone:** hard-science laboratory realism, restrained dialogue, no villain monologue.
Thorne never lies outright; he withholds. Hale never threatens; she schedules an audit.

---

## 2. Cast and voice

### Dr. Aris Thorne — mentor, kineticist, borrower of other people's records
- **Voice:** fast, warm, interrupts himself, thinks in rates and activation energies.
- **Tell:** taps glassware with a stirring rod when he is about to ask for something.
- **Want:** a bench demonstration clean enough to unlock Institute pilot funding.
- **Withholds:** that the pilot board is chaired by Commissioner Hale's office, and that
  the funding line is the same one that paid for Voss's last reactor.
- **Act II arc:** from "you see what others miss" to "sign here, I cannot."

> "Ammonia is not a chemical. It is a negotiating position with a boiling point."
> — Thorne, before the first run

### Mara Kestrel — grey-market broker
- **Voice:** short sentences, prices before pleasantries.
- **Offer:** buy the pilot-plant yield data before the Institute publishes it.
- **Leverage:** she has the missing catalyst-promoter sample and no receipt.
- **Function:** gives the player a second buyer for the same result, so the choice is
  economic rather than abstract.

> "You made a hundred grams. The Institute will make a press release. I make an offer."

### Inspector Hale — regulatory authority
- **Voice:** procedural, precise, never raises her voice.
- **Want:** the 200 bar hydrogen safety case, in writing, before commissioning.
- **Function:** makes safety a gate the player cannot skip, not a scold.
- **Hidden cost:** if the player files the full evidence, the Institute loses the pilot slot
  and Thorne loses his last patron.

### The player — Dr. Kaito Arisato
Defined enough to have a history (computational chemist, forensic data archaeologist),
silent enough that the moral choice belongs to the player. Act II is where the player
stops being Thorne's instrument and starts being a variable Thorne cannot control.

---

## 3. Beat sheet

### Beat 1 — The grant is not the goal (Act II opening)
Thorne asks for a bench-scale Haber-Bosch demonstration "for the board". The lab is
already prepared; the player has to make it work. The first run is deliberately
under-insulated: the feed line frosts over, the ammonia scrubber reads low, and the
player learns that conversion is a function of pressure, temperature and how fast you
throw away the product.

**Playable:** `quest_act2_nitrogen_fixation`
- Objectives: 1:3 N₂/H₂ feed → 200 bar at 450 °C → titrate scrubber liquor for conversion.
- Target: ≥15 % ammonia yield (a bench-scale figure, not an industrial one).
- Reward: 5,200 XP, `haber_bosch_microreactor`, gas chromatograph.

### Beat 2 — The pilot board
The demonstration works. Hale's office attaches a condition: the 200 bar hydrogen case
must be approved before the pilot loop is pressurised. Thorne wants the case signed
"provisionally"; Hale wants it signed properly. Mara offers to make the pilot problem
disappear for a share of the yield data.

**Playable:** `quest_act2_ammonia_pilot`
- Objectives: recover ≥60 % loop heat into the feed preheater; hold loop dew point below
  −20 °C; complete the 200 bar hydrogen hazard review.
- Reward: 6,800 XP, `pilot_plant_platinum_seal`.

### Beat 3 — The choice (narrative fork, next implementation step)
At the commissioning screen the player chooses one of three dispositions:

| Choice | Immediate effect | Faction effect | Narrative consequence |
|---|---|---|---|
| **Publish the full case** | Pilot runs at 70 % capacity | Academic +15, Commission +10, Syndicate −10 | Thorne is sidelined; Hale becomes a recurring ally; the Institute publishes the route. |
| **Sign provisionally for Thorne** | Pilot runs at 100 % capacity | Academic +20, Commission −15 | Thorne gets his reactor; the missing safety annex becomes an Act III liability. |
| **Sell the yield data to Mara** | Pilot runs at 85 %, player receives catalyst stock | Syndicate +20, Academic −10, Commission −10 | The player now has a second supply chain and a debt to Kestrel. |

Implementation note: the quests currently end at the pilot objective. The fork is designed
here and flagged for the next quest-graph pass; no code path claims it exists yet.

---

## 4. Quest-to-fiction mapping

| Quest ID | Tier | Fiction | Chemistry the player actually performs |
|---|---|---|---|
| `quest_act2_nitrogen_fixation` | 5 | Thorne's funding demonstration | Stoichiometric feed preparation, high-pressure/temperature operation, acid titration of ammonia |
| `quest_act2_ammonia_pilot` | 6 | Commissioning under Hale's condition | Heat integration, dew-point control, pressure-systems hazard review |
| `side_quest_pyro_licensing` | 3 | The test bay has its own jurisdiction | Quantity-distance, static grounding, magazine reconciliation |
| `side_quest_pyro_black_powder` | 3 | Historical reference batch, burn-rate only | Milling/screening/granulation and a burn-rate measurement |
| `side_quest_pyro_color_stars` | 4 | Colour development for a licensed display | Strontium/barium/copper emission chemistry and flame temperature |
| `side_quest_pyro_display_choreography` | 5 | A nine-cue show that has to fit the law | Fallout radius, noise limit, wind abort conditions |

The pyrotechnics arc is deliberately **characterisation and safety**, not a recipe game:
the black-powder quest asks why the mixture is fuel-rich and what the burn rate means,
not how to build a device. See `design/pyrotechnics_bay_layout.md` for the spatial design.

---

## 5. Dialogue samples

**Thorne, after a successful run:**
> "Fifteen percent. Do you know what that number cost Haber? Six years and a patent
> war. You did it before lunch. Don't look pleased — look at the scrubber. The board
> will ask what happens at twenty percent, and you will need an answer that is not
> 'more pressure'."

**Hale, on the hydrogen case:**
> "I am not asking you to be afraid of hydrogen. I am asking you to write down what
> happens when the seal fails at 200 bar, who is in the room, and how they leave.
> If that takes more than a page, the answer is no."

**Mara, on the offer:**
> "The Institute will publish the yield and keep the plant. I will pay for the yield
> and keep the plant. You will keep the part nobody writes down: the choice."

**Thorne, if the player pushes back:**
> "You think I am using you. Of course I am. Everyone in this building is using everyone.
> The only question is whether the work survives the using."

---

## 6. Environmental storytelling

- **Feed line frost:** a white rime on the 1:3 manifold that only appears when the
  preheater is under-specified. It is the first visual hint that the bench is not the plant.
- **Scrubber sight glass:** the ammonia solution turns faintly blue with Nessler's reagent;
  the intensity is the only yield readout the player gets before the titration.
- **Pilot loop:** a polished platinum seal in a display case, engraved with the commissioning
  date. It is the item reward, and it is also a monument to the pressure the player approved.
- **Hale's clipboard:** physical, paper, no tablet. She writes while the player talks.
- **Thorne's stirring rod:** the same rod taps the reactor in the success shot and the
  evidence bag in the failure shot. Reuse the prop; do not add a new one.

---

## 7. Implementation status

| Element | Status |
|---|---|
| Two Act II quests with objectives, XP, skill rewards, apparatus/reagent unlocks | implemented |
| Quest chain `nitrogen_fixation → ammonia_pilot` | implemented |
| Pyrotechnics side arc (4 quests, chained) | implemented |
| Narrative text in quest `briefing` fields | implemented |
| Three-way disposition fork | designed, not implemented |
| Faction reputation deltas for the fork | designed, not wired |
| Voice-over / cutscene | intentionally out of scope (offline text-first) |

**Next step (highest value):** add the disposition choice as a quest objective with three
`next_quest_id` branches, then reuse the existing reputation autoload rather than adding a
second system. Do not add a new currency for the pilot; the existing XP + item reward is
enough for a single-player offline RPG.

---

## 8. Safety framing

- The Haber-Bosch quest teaches pressure, temperature, conversion and heat recovery; it does
  not provide industrial construction specifications.
- The pyrotechnics arc is licensed-test-bay fiction. It teaches quantity-distance, static
  control, magazine separation, burn rate and display safety. It deliberately does not
  provide device construction instructions.
- All reagents in the player-facing inventory remain allow-listed laboratory chemicals; the
  forensic "clandestine route" markers in `narrative_style.md` stay fictionalised.
