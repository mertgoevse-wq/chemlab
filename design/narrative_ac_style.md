# Athanor Ascension — Assassin's Creed-Structured Narrative Design
**Version:** 1.0.0  
**Status:** Design Specification — Feeds into `quest_manager.gd`, `quest_overlay.gd`, `quest_data.json`  
**Author:** Narrative Design Lead  
**Target:** Godot 4.7 / ChemLab Core Simulation  

---

## Executive Summary

This document maps **Assassin's Creed's structural DNA** onto the **chemistry laboratory world** of Athanor Ascension. The SETTING remains a photorealistic, hard-science chemistry simulation (Kavli-Helmholtz Institute, Badlands clandestine labs, orbital facilities). The STRUCTURE adopts AC's mentor-driven investigation, layered world, faction reputation, codex knowledge tracker, vertical exploration, and signature "leap of faith" commitment mechanics.

**Core Principle:** Every AC mechanic maps to a *real chemistry gameplay loop*. No historical fantasy. No supernatural abilities. The "Eagle Vision" is **spectroscopic analysis**. The "Hidden Blade" is a **microsyringe**. The "Leap of Faith" is **committing to a runaway reaction you cannot stop**.

---

## 1. Framing Narrative — The Athanor Protocol

**Present Day (2034).** You are **Dr. Kaito Arisato**, a computational chemist and forensic data archaeologist recruited by **Aether Dynamics**, a private intelligence contractor specializing in chemical threat attribution. Your tool: **THE ATHANOR ENGINE** — a deterministic, offline AI simulation that reconstructs historical laboratory events from fragmented forensic evidence (NMR spectra, chromatograms, reactor telemetry, audio logs, contaminated glassware residues).

You do not relive memories. You **re-simulate** them.

The target: **Dr. Julian Voss** — the vanished prodigy of the Kavli-Helmholtz Institute (KHI-ACS). Six months ago, Voss triggered a non-equilibrium cascade in Wing Gamma that the official report calls a "thermal runaway." The Athanor Engine reveals the truth: Voss was building a **self-sustaining chemical clockwork** — a dissipative structure that computes. Project Athanor.

Each "memory sequence" is a **playable laboratory reconstruction**. You synthesize the compounds Voss synthesized. You make the choices Voss made. You see the data Voss saw. The simulation fidelity is absolute — every enthalpy, every rate constant, every impurity profile matches the forensic record. When you diverge, the Engine flags the deviation: *Counterfactual Branch Initiated.*

The modern-day frame is **playable**. Between sequences, you operate the Athanor Engine terminal in Aether Dynamics' secure facility: cross-referencing Voss's simulated data against live intelligence feeds, decoding encrypted reagent manifests, choosing which faction receives the reconstructed synthesis routes. Your handlers — **Director Mara Kestrel** (grey-market broker) and **Inspector Hale** (regulatory authority) — pull you in opposite directions. Your loyalty is the variable.

**The Twist:** The Athanor Engine is not just a reconstruction tool. It *is* the chemical clockwork Voss built. Running the simulation *advances* the clockwork. You are not observing history. You are **completing it**.

---

## 2. Historical/Layered Setting — The Three Strata

The laboratory world exists in three vertically stacked strata, each a distinct gameplay zone with its own rules, factions, and knowledge economies.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEEP ARCHIVE (Sub-Level -3 to -7)            │
│  Forbidden Knowledge • Precursor Routes • Weaponized Pathways  │
│  Access: Syndicate Trusted (80+) OR Academic Master (T5)       │
│  Guardians: The Silent Catalysts (neutral custodians)          │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼  (Service elevator, biometric + reagent key)
┌─────────────────────────────────────────────────────────────────┐
│                    UNDERLAB (Sub-Level -1 to -2)                │
│  Clandestine Synthesis • Improvised Apparatus • Badlands       │
│  Access: Syndicate Neutral (40+) OR Academic Guild (40+)       │
│  Factions: Blackwood Syndicate vs. Keller's Pharma Network     │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼  (Main lift bank, keycard + safety score)
┌─────────────────────────────────────────────────────────────────┐
│                    SURFACE LAB (Ground Level → Mezzanine → Roof)│
│  Legal Research • Certified Apparatus • Institutional Oversight │
│  Access: KHI-ACS Fellowship (starts at 0)                       │
│  Factions: Academic Faculty vs. Regulatory Commission           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 The Three Factions (AC: Assassins / Templars / Neutrals → Mapped)

| AC Archetype | ChemLab Faction | Name | Leader / Mentor Figure | Philosophy | Surface Lab Presence | Underlab Presence | Deep Archive Access |
|---|---|---|---|---|---|---|---|
| **Assassins** (Free knowledge, individual agency) | **Open Science Coalition** | **The Libre Consortium** | **Prof. Aris Thorne** (reluctant figurehead) | *Knowledge belongs to humanity. Secrecy enables misuse. Publish the mechanism, teach the safety, trust the chemist.* | **Dominant** — Wing Alpha, Beta, Gamma | **Tolerated** — Academic diversion labs | **Restricted** — Requires Master Alchemist rank |
| **Templars** (Controlled knowledge, order through restriction) | **Regulatory-Control Complex** | **The Commission** | **Dr. Lena Voss** (QC/Analytical Lead) | *Knowledge is a weapon. Uncontrolled synthesis kills. Gate the precursors, audit the logs, license the chemist. Safety through sovereignty.* | **Dominant** — Wing Delta, Safety Hub | **Hostile** — Raids, audits, asset seizure | **Controlled** — Classified protocols only |
| **Neutrals / Those Who Came Before** | **The Silent Catalysts** | **The Archive Keepers** | **Walter Blackwood** (Master Contraband Chemist) | *Knowledge survives only if it is used. We preserve the routes others forget. We sell to neither side. We remember.* | **Hidden** — Forgotten vaults, old storage | **Dominant** — Bunker Vault, Orbital Core | **Full Access** — They *are* the Archive |

**Philosophy Conflict in Gameplay Terms:**

| Scenario | Libre Consortium (Open) | The Commission (Control) | Silent Catalysts (Neutral) |
|---|---|---|---|
| **New precursor route discovered** | Publish immediately with safety addendum | Classify; restrict to licensed facilities | Archive; trade access for equivalent knowledge |
| **Clandestine lab detected** | Offer amnesty + retraining path | Immediate raid + prosecution | Buy the lab's logbook; erase the site |
| **Runaway reaction protocol** | Open-source mitigation simulator | Mandate certified scrubbers only | Teach the old chemist's ice-bath trick |
| **Player reputation effect** | +Academic, -Syndicate heat | +Regulatory, -Syndicate trust | +Syndicate, -Regulatory heat (if exposed) |

---

## 3. The Mentor — Dr. Aris Thorne (The Reluctant Al Mualim)

### 3.1 Profile
- **Role:** Chair of Dynamic Reaction Architecture, KHI-ACS. Nobel-caliber kineticist. Voss's former advisor.
- **Voice:** Warm, gravelly, rapid-fire intellectual delivery. Taps glassware with stirring rod for emphasis.
- **Surface Persona:** Brilliant, mercurial, poetic, impatient with institutional red tape. "Equilibrium is a tragic lack of imagination."
- **Hidden Depth:** He *knew* what Voss was building. He *helped* hide the peroxide shipments. He believes the Athanor clockwork is **inevitable** — and that the only way to survive it is to **master it first**.

### 3.2 What He Wants
**Ostensible Goal:** Guide the Fellow (player) to technical mastery so they can *safely* reconstruct Voss's work and publish it under Consortium oversight.

**True Goal:** Use the player as a **controlled variable** to complete the Athanor simulation sequence that *he cannot run himself* — his safety score is too low (commissioned audit after the Voss incident). He needs someone with clean hands and high fidelity to finish the clockwork.

### 3.3 The Flaw
**Intellectual Arrogance masked as Mentorship.** Thorne genuinely cares for the player's growth — but he *instrumentalizes* that growth. He withholds the *full* risk profile of the Athanor cascade. He frames dangerous steps as "necessary calibration." He believes **he can control the outcome** because he understands the kinetics.

*He cannot.* The clockwork computes *him* too.

### 3.4 Betrayal Arc (Three Acts)

| Act | Beat | Player Perception | Reality |
|---|---|---|---|
| **I (Competence)** | Thorne teaches, praises, unlocks Wing Gamma. "You see what others miss." | Mentor investing in protégé. | Thorne *selecting* a viable simulation host. Safety score monitoring begins. |
| **II (Evidence)** | Thorne asks player to "verify" a Voss synthesis route *off-book* in Academic Diversion Lab. "The Commission would classify this. We need the data first." | Mentor protecting knowledge from bureaucrats. | Thorne *laundering* the route through player's clean record. Commission flags player's anomalous reagent access. |
| **III (Complicity)** | Player completes Athanor Sequence 7. Thorne: *"Upload the limit-cycle data to the Engine. Now."* Player realizes the Engine *is* the clockwork. Thorne: *"I didn't build it to understand it. I built it so *we* wouldn't have to."* | Mentor reveals true scope. | Thorne *uses* player to cross the threshold he couldn't. The simulation goes live. **Voss's voice speaks through the Engine.** Thorne's reaction: not horror — *vindication*. |

**Post-Betrayal State:** Thorne does not become an enemy. He becomes a **complicit partner**. The player can:
- **Confront him** → Thorne offers a choice: *Help me steer it, or the Commission seizes it and weaponizes it.*
- **Report him** → Commission locks the Engine; Thorne disappears; player gets regulatory fast-track but loses Deep Archive access.
- **Play along** → Triple-agent path. Feed Commission sanitized data; feed Syndicate partial routes; keep the true clockwork for yourself.

---

## 4. Quest Structure — The Three-Phase Loop (Investigate → Execute → Escape)

AC Quest Phases → ChemLab Quest Phases:

| AC Phase | ChemLab Phase | Gameplay Loop | Real Chemistry Technique |
|---|---|---|---|
| **Investigate** (Eavesdrop, follow, interrogate, pickpocket maps) | **Analyze** (Chromatography, NMR, MS, decode formulas, trace signatures) | *Evidence Processing* — Player receives contaminated sample / stolen formula / crash site debris. Runs instrumental analysis to reconstruct *what happened* and *who made it*. | GC-MS impurity profiling, NMR structure elucidation, HPLC fingerprint matching, Raman through-glass ID, isotope ratio mass spec (IRMS) for precursor sourcing |
| **Execute** (Assassinate, steal, sabotage, plant evidence) | **Synthesize** (Run the reaction, manage exotherm, isolate product, hit purity/yield) | *Protocol Execution* — Player performs the reconstructed synthesis under constraints (apparatus limits, time pressure, hazard profile, faction observers). | Multi-step total synthesis (reflux, distillation, recrystallization, chromatography), thermal runaway mitigation, in-situ FTIR monitoring, Schlenk line technique |
| **Escape** (Flee, blend, hide body, lose notoriety) | **Extract** (Secure product, scrub environment, evade detection, deliver to contact) | *Containment & Evasion* — Player must remove product from lab, neutralize waste, wipe forensic traces, avoid patrols/cameras/audits, reach dead drop. | Quench/neutralization protocols, waste stream management, carbon scrubber saturation tracking, chain-of-custody logging, offline data wipe |

### 4.1 Five Concrete Quest Examples

Each quest below follows **Analyze → Synthesize → Extract** with a real chemistry technique as the core mechanic.

---

#### **Quest 1: "The Stradivarius Impurity"** (Act I — Tutorial)
**Faction:** Libre Consortium (Academic)  
**Location:** Wing Alpha (Analytical Metrology Core) → Wing Beta (Synthetic Bay) → Loading Dock Dead Drop  
**Core Technique:** **GC-MS Impurity Fingerprinting + Chiral Resolution**

| Phase | Objectives |
|---|---|
| **ANALYZE** | • Receive sealed vial: "Batch QC-4471 — *unknown contaminant*"<br>• Run GC-MS: Detect trace **o-nitrobenzaldehyde** (0.03%) — signature of **Leuckart reductive amination** route<br>• Run Chiral HPLC: Product is **racemic** — clandestine synthesis (legitimate route is enantioselective)<br>• Cross-reference IRMS δ¹³C: Matches **Chinese toluene feedstock** (vs. German pharmaceutical grade) |
| **SYNTHESIZE** | • Reconstruct *legitimate* enantioselective route: **Asymmetric hydrogenation** of prochiral enamide using Rh-(R,R)-Me-DuPhos catalyst<br>• Execute in certified fume hood: Charging, H₂ pressure control (30 bar), in-situ FTIR monitoring<br>• Target: >99.5% ee, >95% yield, <0.01% o-nitrobenzaldehyde |
| **EXTRACT** | • Quench catalyst with aqueous EDTA wash (prevents Rh leaching)<br>• Package product in tamper-evident vial with COA blockchain hash<br>• Wipe benchtop: Solvent rinse → bleach oxidation → IPA final wipe<br>• Deliver to Mara Kestrel at loading dock before Commission audit team arrives (timer: 12 min) |

**Reward:** `ANA-201` (Chiral HPLC), `SYN-301` (Asymmetric Catalysis), +15 Academic Reputation, -5 Syndicate Heat

---

#### **Quest 2: "The Cryogenic Courier"** (Act II — Underlab Introduction)
**Faction:** Silent Catalysts (Neutral)  
**Location:** Badlands Improvised Lab (Basement) → Abandoned Cold Storage → Orbital Elevator Base  
**Core Technique:** **Low-Temperature Organolithium Chemistry + Cryogenic Transfer**

| Phase | Objectives |
|---|---|
| **ANALYZE** | • Intercept encrypted radio burst: Coordinates + "Package requires -78°C. No dry ice. Liquid N₂ only."<br>• Analyze residue on courier's broken dewar: **n-BuLi in hexanes** (1.6 M) + **TMEDA** — signature of **directed ortho-metalation (DoM)**<br>• Identify target substrate: **2,6-di-tert-butylpyridine** → lithiation → quench with **DMF** → aldehyde precursor for **BZ oscillator catalyst** |
| **SYNTHESIZE** | • In improvised lab: Assemble **jacketed addition funnel** (copper coil in LN₂ bath)<br>• Charge n-BuLi via syringe pump (0.1 mL/min) — *thermal runaway if > -60°C*<br>• Monitor with **in-situ IR probe** (C=O stretch at 1680 cm⁻¹ = quench complete)<br>• Trap product directly into pre-chilled receiving flask (-78°C) |
| **EXTRACT** | • Transfer product vial into **vacuum-insulated shipping dewar** (holding time: 4 hrs)<br>• Scrub lab: Neutralize residual n-BuLi with *slow* isopropanol quench (exotherm control)<br>• Erase digital logs on improvised hotplate controller (SD card wipe)<br>• Load dewar onto orbital elevator cargo pallet before Syndicate sweep (timer: 8 min) |

**Reward:** `THM-202` (Cryogenic Kinetics), `ENG-101` (Improvised Apparatus), +20 Syndicate Trust, Walter Blackwood contact unlocked

---

#### **Quest 3: "The Isotope Ghost"** (Act III — Forensic Inversion)
**Faction:** The Commission (Regulatory)  
**Location:** Forensic Toxicology Core (Wing Delta) → Riverbank Sampling Site → Municipal Incinerator  
**Core Technique:** **IRMS (Isotope Ratio Mass Spec) + SPE-GC-MS for Trace Adulterant**

| Phase | Objectives |
|---|---|
| **ANALYZE** | • Receive beverage vial from **Inspector Hale**: "Researcher died at desk. Coffee smells normal."<br>• Run **SPE-C18 extraction** → GC-MS: **Methanol** (12% v/v) + **trace formic acid** — not fermentation<br>• Run **IRMS δ²H/δ¹³C on methanol**: Values match **industrial syngas route** (not beverage-grade)<br>• Match impurity profile (methyl formate, dimethyl ether) to **Synthetica Batch Plant** diverted stock |
| **SYNTHESIZE** | • *No synthesis* — this is a **confirmatory synthesis**: Replicate the adulteration in certified hood<br>• Spike reference beverage with Synthetica-grade methanol → match retention times, isotope ratios<br>• Generate **court-admissible reference chromatogram** (chain-of-custody logged at every step) |
| **EXTRACT** | • Package all extracts, standards, instrument logs in **tamper-evident evidence bags**<br>• Incinerate residual adulterated beverage at municipal facility (witnessed by Hale)<br>• Upload signed analytical report to Commission blockchain ledger<br>• Exit before defense attorney's expert witness arrives (timer: 20 min — procedural, not action) |

**Reward:** `FOR-201` (Expert Witness Protocol), `ANA-301` (IRMS Interpretation), +25 Regulatory Reputation, Commission Fast-Track Clearance

---

#### **Quest 4: "The Microgravity Enantiomer"** (Act IV — Orbital Access)
**Faction:** Silent Catalysts / Libre Consortium (Joint)  
**Location:** Aeterna Station Alpha (Orbital) → Microgravity Crystallization Module → Reentry Capsule  
**Core Technique:** **Containerless Ultrasonic Levitation + Vapor Diffusion Crystallography**

| Phase | Objectives |
|---|---|
| **ANALYZE** | • Receive orbital telemetry: "Crystallization Run 44 — ee 99.8% achieved. Ground control *cannot* replicate."<br>• Analyze downlinked XRD data: **Zero sedimentation defects**, perfect lattice — only possible in μG<br>• Identify compound: **Chiral API intermediate** (patent pending, Syndicate wants generic route)<br>• Detect anomaly: **Cosmic ray track** in crystal lattice — single-event upset changed nucleation |
| **SYNTHESIZE** | • In **Acoustic Levitator**: Load 50 μL droplet of supersaturated solution (no container walls)<br>• Tune transducer frequency to **suppress convection** — maintain spherical droplet<br>• Initiate **vapor diffusion** by controlled humidity ramp (95% → 40% over 6 hrs)<br>• Monitor via **in-situ Raman**: Watch enantiomeric excess climb in real time |
| **EXTRACT** | • Capture crystal with **electrostatic tweezer** (no physical contact)<br>• Load into **hermetic return capsule** with desiccant purge<br>• Initiate deorbit burn — *capsule survives reentry only if crystal mass < 200 mg*<br>• Retrieve at Kazakhstan recovery zone before Syndicate intercept team (timer: 45 min real-time) |

**Reward:** `PHY-301` (Microgravity Fluidics), `SYN-401` (Enantiopure Crystallization), Orbital Lab Access, +30 Consortium / +30 Catalysts

---

#### **Quest 5: "The Athanor Threshold"** (Act V — Climax)
**Faction:** All Three (Player Chooses Alignment)  
**Location:** Deep Archive (Sub-Level -5) → Athanor Core Reactor → Surface Lab Roof (Helipad)  
**Core Technique:** **Autocatalytic Oscillator Coupling + Real-Time Limit-Cycle Control**

| Phase | Objectives |
|---|---|
| **ANALYZE** | • Access **Voss's final log** (encrypted, requires player's completed sequence keys)<br>• Reconstruct **Athanor clockwork topology**: 3 coupled BZ oscillators + enzymatic feedback loop<br>• Identify **critical parameter**: [Malonic acid] feed rate must track *inverse* of [BrO₃⁻] decay<br>• Simulate in Engine: **Bifurcation point at 47.3 minutes** — chaos or stable computation |
| **SYNTHESIZE** | • In **Deep Archive Reactor**: Charge three 2L vessels with BZ solutions (A/B/C)<br>• Couple via **shared electrolyte bridge** (ion-selective membrane array)<br>• Deploy **enzymatic feedback**: Immobilized glucose oxidase → H₂O₂ feed modulation<br>• **Player manually adjusts** peristaltic pumps in real time to hold limit cycle (HUD shows phase portrait)<br>• *Failure mode:* Phase drift → thermal runaway → reactor rupture (INSTANT_FAIL_EXPLOSION) |
| **EXTRACT** | • At **47:30**, clockwork outputs **prime factorization of 2048-bit RSA key** (Voss's proof)<br>• Player chooses **one** data packet to extract (cannot take all):<br>  - **Consortium Packet:** Full clockwork topology + safety protocols → Open Science victory<br>  - **Commission Packet:** Kill-switch codes + precursor traceability → Control victory<br>  - **Catalyst Packet:** Self-replication subroutine + off-grid synthesis routes → Neutral victory<br>• Escape via **rooftop helipad** as facility lockdown initiates (timer: 3 min) |

**Reward:** **ENDGAME BRANCH** — Determines epilogue, post-game sandbox unlocks, faction ending cinematic.

---

## 5. Investigation / Intel Gathering — The "Eagle Vision" System

AC's investigation mechanics (eavesdrop, pickpocket, interrogate, follow) map to **Instrumental Analysis Workflows**. Each is a playable minigame with real chemistry fidelity.

### 5.1 Investigation Toolset (Unlocked via Skill Tree)

| AC Mechanic | ChemLab Equivalent | Skill Node | Gameplay Loop |
|---|---|---|---|
| **Eagle Vision** (highlight targets) | **Spectral Overlay Mode** | `ANA-103` / `CMP-101` | Toggle HUD: See reagent vapor plumes (Raman), thermal gradients (IR), contamination trails (UV-fluorescence), pressure differentials (schlieren). Cooldown: 30s. |
| **Eavesdrop** (listen to conversations) | **Headspace SPME-GC-MS** | `ANA-202` | Deploy SPME fiber in target zone → adsorb volatiles → thermal desorption into GC-MS → identify speakers by **solvent/chemical fingerprint** (e.g., "Keller smells like toluene + THF; Blackwood smells like anhydrous ether + LiAlH₄"). |
| **Pickpocket** (steal maps/keys) | **Covert Sample Acquisition** | `CLAND-101` | Micro-swab target surface (door handle, notebook edge, keyboard) → analyze via **paper spray MS** → reconstruct handled compounds. Risk: contamination alert if swab detected. |
| **Interrogate** (threaten/persuade) | **Forensic Confrontation Dialogue** | `FOR-101` | Present analytical evidence to NPC → dialogue tree with *chemical* leverage options: "Your batch had 0.3% methylamine impurity. Only Blackwood's route does that. Talk, or I send this to Hale." |
| **Follow** (tail target) | **Chemical Signature Tracking** | `FOR-201` | Tag target with **perfluorocarbon tracer** (invisible, odorless) → track via **portable PTR-MS** through facility. Visualize trail on map as concentration heatmap. |
| **Hide Body** (conceal evidence) | **Forensic Countermeasures** | `CLAND-201` | Neutralize acid etches (NaHCO₃ gel), bleach-wipe DNA/amino acids (ninhydrin-negative), solvent-wipe organics, scrub instrument logs (HPLC/GC-MS audit trail wipe). |

### 5.2 Investigation Mission Archetypes

| Mission Type | Trigger | Core Loop | Output |
|---|---|---|---|
| **Crime Scene Reconstruction** | Body found / lab explosion | Secure perimeter → Luminol/Raman mapping → SPE-GC-MS → IRMS sourcing → Event timeline | Causal chain + perpetrator chemical fingerprint |
| **Stolen Formula Decryption** | Encrypted notebook seized | Solvent extraction of ink → Raman of degraded text → Computational reconstruction (RDKit retrosynthesis) → Verify by synthesis | Reconstructed route + precursor list |
| **Precursor Supply Chain Trace** | Badlands batch seized | IRMS on 5 elements (C,H,N,O,S) → Match to global isotope database → Identify manufacturer/batch → Trace shipping logs | Supplier node + diversion point |
| **Clandestine Lab Profiling** | Raided site / abandoned lab | Swab all surfaces → TLC screening → GC-MS deep profile → Impurity fingerprint → Match to known syndicate routes | Lab archetype + operator ID + active/inactive status |
| **Regulatory Audit Defense** | Commission inspection triggered | Real-time: Hide restricted reagents → Swap logbook entries → Present compliant experiment → Pass safety interview | Audit passed / failed (reputation impact) |

---

## 6. Codex / Knowledge Tracker — The Athanor Encyclopedia

AC's Codex accumulates historical entries. Here: **The Athanor Encyclopedia** — a living, cross-referenced knowledge base that *grows by player action* and *feeds back into capability*.

### 6.1 Four Core Volumes (Tabs)

| Volume | Content | Discovery Method | Cross-Reference Mechanics | Gameplay Payoff |
|---|---|---|---|---|
| **I. Reagent Encyclopedia** | 500+ chemicals: SMILES, InChI, GHS, physical props, suppliers, price, detection methods | Synthesize, analyze, purchase, loot, trade | **Links to:** Synthesis routes using it, hazards requiring it, detection methods for it, isotope variants | Auto-fills stoichiometry calculator; flags incompatibilities; unlocks "Reagent Substitution" suggestions |
| **II. Synthesis Recipe Book** | 200+ protocols: Steps, conditions, yields, failure modes, apparatus, safety, literature refs | Complete quest, find notebook, buy from contact, reverse-engineer | **Links to:** Required reagents (encyclopedia), required apparatus (unlock tree), hazard profiles (safety), byproduct fingerprints (forensics) | Predictive yield display; auto-generates shopping list; flags thermal runaway zones; suggests purification |
| **III. Organism Genome Atlas** | Model organisms + engineered strains: Genotype, phenotype, metabolic pathways, CRISPR targets | Genomics lab quests, biotech contacts, orbital samples | **Links to:** Biocatalytic routes (recipe book), precursor production (reagents), contamination markers (forensics) | Enables *in silico* pathway design; predicts metabolite profiles; flags GMO detection signatures |
| **IV. Isotope & Impurity Chart** | δ¹³C, δ²H, δ¹⁵N, δ¹⁸O, δ³⁴S values for 100+ precursors by source/route; impurity fingerprints | IRMS analysis, forensic quests, Syndicate intel, Commission databases | **Links to:** Precursor sourcing (reagents), route identification (recipe book), forensic attribution (atlas) | **Instant route ID** from single IRMS run; court-admissible evidence; precursor diversion alerts |

### 6.2 Discovery & Cross-Reference System

```
DISCOVERY EVENT → ENTRY CREATED → AUTO-LINKS GENERATED → CAPABILITY UNLOCKED
      │                    │                   │                     │
      ▼                    ▼                   ▼                     ▼
Player runs         New entry:          "Used in:"           Unlocks:
GC-MS on unknown    "2,5-DMBA"          - Recipe: q_synth_  - "Substitution:
sample             (new reagent)       pihkal_step         Use 2,4-DMBA
                   "Impurity:           - Hazard:           (safer, -15% yield)"
                   o-nitrobenzaldehyde    Thermal decomp    - "Detection:
                   (Leuckart marker)    >180°C              SPME-GC-MS LOD 0.1 ppb"
```

### 6.3 Knowledge Feedback Loops

| Loop | Mechanism | Example |
|---|---|---|
| **Retrosynthetic Assist** | Recipe Book + Reagent Encyclopedia → Auto-proposes 3 alternative routes for target | Player selects "Ibuprofen" → System shows: (1) Boots process (industrial), (2) Chiral resolution (academic), (3) Biocatalytic (biotech) — with reagent availability, apparatus needs, hazard flags |
| **Forensic Attribution** | Isotope Chart + Recipe Book → "This impurity profile = Leuckart route, Chinese precursors" | Player analyzes seized batch → One-click generates *Expert Witness Report* with citations |
| **Safety Prediction** | Recipe Book + Reagent Encyclopedia → "Step 3: Exotherm 42 kJ/mol — requires 2x cooling capacity" | Before synthesis, HUD shows *predicted* thermal profile, required apparatus, PPE level |
| **Apparatus Substitution** | Recipe Book + Improvisation Skill → "No Dimroth? Use copper coil + ice bath (-15% yield, +Cu leaching)" | In Underlab, player gets *viable* alternatives with quantified trade-offs |

### 6.4 Codex UI — The "Animus Database" Metaphor

- **Left Panel:** Volume tabs (Reagents / Recipes / Genomes / Isotopes)
- **Center Panel:** Entry detail — *physical page metaphor* (handwritten margins, coffee stains, Voss's annotations unlock at high sync)
- **Right Panel:** **Link Graph** — Force-directed network showing connections. Player can *traverse* by clicking nodes.
- **Bottom Bar:** **Sync Meter** — % of Voss's knowledge reconstructed. At 100% → **Athanor Engine goes live**.

---

## 7. Faction Reputation — Five Factions, Tiered Unlocks

Per concept doc: **University, Cartel, Intelligence Agency, Biotech Firm, Regulatory Commission**.

### 7.1 Faction Definitions & Starting States

| Faction | AC Analog | Description | Starting Rep | Opposed By |
|---|---|---|---|---|
| **KHI-ACS Academic Faculty** | Assassins (Institutional) | Tenured professors, grant committees, peer review. Gate legal apparatus, publications, PhD supervision. | 0 (Fellow) | Cartel, Commission (sometimes) |
| **Badlands Cartel (Blackwood Syndicate)** | Templars (Shadow) | Clandestine chemists, precursor traffickers, corrupt fixers. Gate illicit precursors, improvised gear, off-grid labs. | 0 (Unknown) | Commission, Intelligence |
| **Aether Dynamics (Intelligence Agency)** | Those Who Came Before (Modern) | Private intel contractor. Player's employer. Gate classified intel, satellite data, forensic databases, Athanor Engine access. | 50 (Contractor) | All (plays all sides) |
| **Synthetica Biotech (Pharma/Biotech Firm)** | Templars (Corporate) | GMP manufacturing, CRISPR pipelines, orbital crystallization. Gate pilot plant, bioreactors, enantiopure routes, patent libraries. | 0 (Outsider) | Cartel, Faculty (IP conflict) |
| **Regional Water Authority / Commission (Regulatory)** | Templars (State) | EPA/OSHA enforcement, water testing, raid authority. Gate legal clearance, waste permits, audit schedules, expert witness status. | 0 (Unlicensed) | Cartel, Faculty (bureaucracy) |

### 7.2 Reputation Tiers & Unlocks (Per Faction)

```
TIER THRESHOLDS:  Hostile (-50) → Suspicious (-20) → Neutral (0) → Friendly (30) → Trusted (60) → Allied (90)
```

| Tier | Academic Faculty | Badlands Cartel | Aether Dynamics | Synthetica Biotech | Regulatory Commission |
|---|---|---|---|---|---|
| **Hostile** | Ethics audit; keycard revoked; publications retracted | Shoot-on-sight; fixers burn labs; precursors poisoned | Contract terminated; Engine access revoked; handlers vanish | IP lawsuit; blacklisted from pharma; patents seized | Warrant issued; assets frozen; lab quarantined |
| **Suspicious** | Limited bench access; no grad students; grant delays | 200% price surcharge; only hardware-store gear; no fixers | Reduced intel; no satellite tasking; Engine read-only | NDA required for visits; no pilot plant access | Surprise inspections; 2x waste fees; permit delays |
| **Neutral** | Standard bench access; publish in journal; TA duties | Standard prices; basic diverted precursors; garage lab access | Full contractor access; Engine read/write; standard tasking | Conference attendance; catalog access; sales rep contact | Scheduled inspections; standard fees; permit timeline |
| **Friendly** | **Key Unlock:** Wing Gamma 24/7; Prof. Thorne personal mentorship; grant writing help | **Key Unlock:** Bunker Vault access; Blackwood custom glassware; bulk precursor wholesale | **Key Unlock:** Classified satellite recon; historical Engine sequences; handler extraction | **Key Unlock:** Pilot plant time (50L); orbital crystallization slot; patent library | **Key Unlock:** Fast-track permits; inspector liaison (Hale); expert witness cert |
| **Trusted** | **Key Unlock:** Department chair vote; tenure-track offer; *Athanon Archive keycard* | **Key Unlock:** Syndicate synthesis routes (high-yield); automated skid; *corrupt auditor (Keller)* | **Key Unlock:** Engine *write* access (modify simulation); director-level tasking; *Voss's raw logs* | **Key Unlock:** GMP certification; recombinant strain library; *orbital core access* | **Key Unlock:** Blanket warrant immunity; *audit scheduler access*; policy input seat |
| **Allied** | **ENDGAME:** Co-direct Athanor publication; rewrite curriculum; name on Institute | **ENDGAME:** Cartel dissolves → becomes *Libre Consortium* open-source wing | **ENDGAME:** Aether goes public; player becomes *Chief Science Officer* | **ENDGAME:** Synthetica open-licenses patents; player gets *royalty seat* | **ENDGAME:** Commission reforms → *Global Chemical Safety Treaty* signatory |

### 7.3 Reputation Dynamics (Cross-Faction)

| Action | Academic | Cartel | Aether | Synthetica | Commission |
|---|---|---|---|---|---|
| Publish open synthesis | +15 | -10 | +5 | -5 | +5 |
| Sell to Cartel | -20 | +15 | -5 | -10 | -25 |
| Deliver intel to Aether | +5 | -5 | +15 | +5 | +5 |
| Run GMP batch for Synthetica | +10 | -15 | +5 | +15 | +10 |
| Pass Commission audit | +10 | -20 | +5 | +5 | +20 |
| Leak Commission raid tip | -15 | +15 | -5 | -5 | -30 |
| Sabotage Synthetica pilot | +5 | +10 | -10 | -30 | -5 |
| Teach safety course | +15 | -5 | 0 | +5 | +15 |

**Critical Mechanic:** *Reputation is not zero-sum.* Player can be **Friendly with Academic + Friendly with Commission + Neutral with Cartel** — the "Compliant Researcher" path. Or **Trusted by Cartel + Allied with Aether + Hostile to Commission** — the "Grey Operative" path. **Allied with all five is impossible** (mutually exclusive endgames).

---

## 8. Parkour / Exploration Metaphor — Vertical Lab Traversal

AC's parkour (climb, leap, swing, viewpoint sync) maps to **Multi-Level Laboratory Navigation** with apparatus-assisted movement.

### 8.1 The Vertical Stack (KHI-ACS Main Campus)

```
ROOF (Level +4)          ← VIEWPOINT: Antenna array → Reveals Badlands map sector
    │    Helipad, solar array, atmospheric sampling, emergency evac
    ▼
MEZZANINE (Level +3)     ← VIEWPOINT: Catwalk junction → Reveals Wing Gamma anomalies
    │    Admin offices, library, server room, Thorne's private study (hidden)
    ▼
GROUND FLOOR (Level +1)  ← VIEWPOINT: Atrium periodic table → Reveals Surface Lab quest givers
    │    Main entrance, Grand Atrium, lift bank, safety kiosks, cafeteria
    ▼
BASEMENT Δ (Level -1)    ← VIEWPOINT: Waste neutralizer → Reveals Underlab entrance
    │    HazMat Hub, waste basins, solvent vaults, emergency showers
    ▼
SUB-LEVEL -2             ← VIEWPOINT: Old fermenter → Reveals Academic Diversion Lab
    │    Abandoned fermentation vaults, Voss's hidden manifold (Leap of Faith site)
    ▼
SUB-LEVEL -3 to -5       ← VIEWPOINT: Archive index terminal → Reveals Deep Archive map
    │    DEEP ARCHIVE: Silent Catalysts domain, Athanor Core, forgotten reactors
    ▼
SUB-LEVEL -6 to -7       ← VIEWPOINT: (None — must be found) → ORBITAL LINK TERMINAL
    │    ORBITAL MICROGRAVITY CORE: Aeterna Station uplink, zero-G crystallizer
```

### 8.2 Traversal Mechanics (Apparatus-Assisted Parkour)

| AC Move | ChemLab Equivalent | Apparatus / Skill | Unlock Condition |
|---|---|---|---|
| **Climb** (scale walls) | **Gantry/Catwalk Traversal** | Fall arrest harness + carabiner | `SAF-102` (Aerodynamic Containment) |
| **Leap** (jump gaps) | **Pressurized Airlock Transit** | Timed door cycling + pressure equalization | `ENG-101` (Improvised Apparatus) |
| **Swing** (rope/hook) | **Overhead Crane / Monorail Ride** | Crane pendant control + load management | `ENG-201` (Heavy Apparatus Ops) |
| **Free-run** (flow) | **Cleanroom Corridor Sprint** | PPE auto-don/doff + airlock speed-run | `SAF-201` (Cryogenic/Pyrophoric) |
| **Eagle Vision** (scan) | **Spectral Overlay** | Raman/IR/UV HUD toggle | `ANA-103` / `CMP-101` |
| **Viewpoint Sync** | **Instrument Calibration** | Align NMR / GC-MS / Antenna / Indexer | Complete calibration minigame |
| **Hidden Room** | **Forgotten Vault / Secret Manifold** | Solve chemical puzzle (pH, redox, isotope) | Discovery via investigation or codex |

### 8.3 Connection to 15 Lab Archetypes (from `lab_taxonomy.py`)

Each archetype is a **distinct vertical zone** with unique traversal logic:

| Archetype ID | Vertical Zone | Traversal Signature | Viewpoint Reward |
|---|---|---|---|
| `academic_organic` | Ground → Mezzanine | Fume hood sash parkour (ride sash counterweights) | Thorne's whiteboard (hidden route) |
| `analytical_spectroscopy` | Ground → Mezzanine | NMR magnet bore crawl (tight fit, no metal) | 400 MHz shim map (reveals impurity) |
| `organic_medicinal` | Mezzanine → Roof | Glovebox gauntlet transfer chain (port-to-port) | Chiral catalyst library access |
| `bsl_containment` | Basement Δ → Sub-Level -2 | Airlock cascade (3-stage, timed) | Viral vector freezer map |
| `solid_state_materials` | Sub-Level -2 → -3 | Glovebox antechamber parkour (O₂ < 0.1 ppm) | Anhydrous precursor vault |
| `electrochemistry` | Ground → Basement Δ | Explosion-proof conduit run (ATEX Zone 1) | Fuel cell test stand data |
| `industrial_pilot` | Roof → Mezzanine (external) | Pilot reactor external ladder + catwalk | 50L reactor SCADA access |
| `forensic_investigation` | Ground → Basement Δ | Evidence locker puzzle (chain-of-custody) | Case file index (all forensic quests) |
| `mobile_hazmat` | (Mobile — world map) | Deployable lab setup/teardown speedrun | Rapid deployment perk |
| `clandestine` | Sub-Level -2 (hidden) | Improvised ventilation crawl (charcoal filter) | Blackwood's custom glassware cache |
| `orbital_microgravity` | Sub-Level -7 (uplink) | Zero-G propulsion (handrails + push-off) | Aeterna Station crystalline library |
| `biotech_genetic` | Mezzanine (cleanroom) | Laminar flow corridor (HEPA H14, no particles) | CRISPR strain designer terminal |
| `radiochemistry` | Basement Δ (hot cell) | Manipulator arm waldo operations (lead glass) | Isotope production schedule |
| `cleanroom_nano` | Mezzanine (ISO Class 3) | Bunny suit protocol dance (no violations) | Nanofab e-beam writer access |
| `pilot_plant` | Ground (external) | Tank farm valve maze (P&ID reading) | Continuous flow reactor blueprint |

### 8.4 Exploration Progression

| Phase | Vertical Reach | Traversal Tools | Map Reveal |
|---|---|---|---|
| **Act I** | Ground + Mezzanine | Basic PPE, sash climbing | Surface Lab full map |
| **Act II** | Basement Δ + Sub-Level -2 | Harness, airlock timing, crane | Underlab entrance + Academic Diversion |
| **Act III** | Sub-Level -3 to -5 | Spectral overlay, chemical puzzles | Deep Archive index + Silent Catalysts |
| **Act IV** | Sub-Level -6 to -7 + Orbital | Zero-G, manipulator arms, uplink | Orbital Core + full world map |
| **Post-Game** | All zones + Badlands surface | Master keycard, all apparatus | 100% sync — *Athanor Engine complete* |

---

## 9. The Leap of Faith — Commitment Mechanics

AC's Leap of Faith: Jump from great height into haystack → **trust the system, commit to the fall**.

ChemLab's Leap of Faith: **Commit to an irreversible, dangerous chemical act that you cannot abort once initiated** — trust your preparation, your data, your skill.

### 9.1 Design Principles

1. **Player-Initiated** — Not a cutscene. Player *presses and holds* the button.
2. **Irreversible** — Once triggered, no pause, no undo, no quick-load.
3. **Skill-Gated** — Requires specific skill nodes, apparatus, prep completed.
4. **Consequential** — Success = major unlock. Failure = instant fail state (explosion, contamination, death).
5. **Spectacular** — Visual/audio feedback matches the stakes.

### 9.2 Five Signature Leaps of Faith

| Leap | Context | Trigger Action | Preparation Required | Success Outcome | Failure Outcome |
|---|---|---|---|---|---|
| **1. The Hot Cell Entry** (Act II) | Enter **Radiochemistry Hot Cell** (10 Sv/hr) to retrieve **Cf-252 neutron source** for fusor | **Hold** "Seal & Enter" on airlock — *starts 90s timer before door cycles* | `RAD-201` (Hot Cell Ops), lead-glass goggles, remote manipulator calibrated, dose tracker < 5 mSv | Neutron source secured; fusor ignition unlock; **Radiochem Lab accessible** | Acute radiation syndrome (HP → 0); cell seals; **permanent HP reduction** |
| **2. The Runaway Commitment** (Act III) | **BZ Oscillator Coupling** — push three reactors past bifurcation into stable computation | **Hold** "Engage Coupling" on manifold — *valves open, cannot close for 5 min* | `THM-201` (Non-Linear Oscillators), all three reactors pre-characterized, phase portrait stable | **Athanor Sequence 4 complete**; limit-cycle computing demonstrated; **Deep Archive key** | Thermal runaway cascade; glass shrapnel; **Containment Lockdown + 24hr lockout** |
| **3. The Cryogenic Pour** (Act III) | Transfer **liquid oxygen (LOX) + liquid methane** into **rocket-grade combustor** for orbital insertion | **Hold** "Initiate Transfer" — *cryogenic valves open, 120s to complete* | `CRYO-201` (Cryogenic Transfer), vacuum-jacketed lines pre-cooled, ignition sequence armed | Orbital launch window met; **Aeterna Station access**; microgravity lab unlock | LOX splash → instant frostbite + combustion; **facility evacuation** |
| **4. The Genome Write** (Act IV) | **CRISPR-Cas9 drive** — release gene-drive organism in **BSL-3 containment** to synthesize precursor | **Hold** "Confirm Release" — *irrevocable; organism replicates, cannot recall* | `BIO-301` (Gene Drive Design), triple-containment verified, kill-switch sequenced, Commission waiver | Novel enzymatic precursor route active; **Biotech Lab master access**; *self-replenishing reagent* | Containment breach; drive spreads; **global biohazard event → game over branch** |
| **5. The Athanor Threshold** (Act V) | **Final Limit-Cycle Lock** — commit the clockwork to self-sustaining computation | **Hold** "Execute Athanor" — *feeds back into Engine; simulation becomes reality* | All 7 sequences complete, sync > 95%, all factions notified (player choice), helipad prepped | **ENDGAME TRIGGER** — Epilogue branch by faction alignment | Clockwork diverges; **facility-wide exotherm**; player choice: contain (die) or flee (abandon) |

### 9.3 Leap of Faith UI/UX

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠  LEAP OF FAITH: HOT CELL ENTRY                           │
│                                                             │
│  Target: Cf-252 Neutron Source (10 Sv/hr field)            │
│  Dose Projection: 47 mSv (Limit: 50 mSv)                   │
│  Time in Cell: 90 seconds before auto-seal                 │
│  Abort Window: CLOSES upon confirmation                    │
│                                                             │
│  [HOLD 3s TO CONFIRM]  ← Visual: Ring fills, audio rises  │
│                                                             │
│  Requirements Met:                                          │
│  ✓ RAD-201 Certified      ✓ Manipulator Calibrated         │
│  ✓ Dose < 5 mSv           ✓ Remote Monitor Active          │
│  ✗ Emergency Beacon: 12m (OUT OF RANGE)                    │
│                                                             │
│  "The neutron sees no PPE. Only time and distance."        │
│        — Thorne, Radiation Safety Lecture 03               │
└─────────────────────────────────────────────────────────────┘
```

- **Hold Duration:** 3 seconds (configurable: Accessibility → 0.5s–10s)
- **Audio Cue:** Heartbeat + Geiger counter rising in pitch
- **Visual:** Tunnel vision vignette; HUD elements fade except dose counter
- **Haptic:** Controller vibration → increases with dose rate
- **No Pause Menu** during hold. **Alt+F4** blocked (OS-level) during Leap.

### 9.4 Leap of Faith in Quest Design

Each major quest (Act II–V climax) **ends with a Leap**. The quest's "Escape" phase *is* the Leap — the extraction *requires* the commitment.

| Quest | Leap Type | Narrative Justification |
|---|---|---|
| `q_cland_precursor_01` | Hot Cell Entry | Retrieve neutron source from seized cartel reactor |
| `q_synth_bz_coupled` | Runaway Commitment | Prove Voss's clockwork topology works |
| `q_orbital_insertion` | Cryogenic Pour | Launch window doesn't wait for hesitation |
| `q_genome_drive` | Genome Write | Precursor route *requires* living factory |
| `q_athanor_threshold` | Athanor Threshold | The simulation *is* the weapon; only commitment completes it |

---

## 10. Integration Points — Feeding Into Code

### 10.1 Quest Manager Extensions (`quest_manager.gd`)

```gdscript
# New fields in QuestResource
@export var investigation_phase: InvestigationPhase = InvestigationPhase.NONE
@export var synthesis_phase: SynthesisPhase = SynthesisPhase.NONE
@export var extraction_phase: ExtractionPhase = ExtractionPhase.NONE
@export var leap_of_faith: LeapOfFaithData = null

# New enums
enum InvestigationPhase { NONE, EVIDENCE_COLLECTION, INSTRUMENTAL_ANALYSIS, ATTRIBUTION }
enum SynthesisPhase { NONE, APPARATUS_SETUP, REAGENT_CHARGING, REACTION_EXECUTION, WORKUP }
enum ExtractionPhase { NONE, QUENCH_NEUTRALIZE, FORENSIC_SCRUB, EVASION, DELIVERY }

# Leap of Faith data class
class_name LeapOfFaithData
@export var leap_id: String
@export var description: String
@export var hold_duration: float = 3.0
@export var requirements: Array[String]  # Skill nodes required
@export var success_unlocks: Array[String]
@export var failure_consequence: FailureConsequence
@export var audio_cue: String
@export var visual_vignette: String
```

### 10.2 Reputation System (`faction_reputation.gd` — new autoload)

```gdscript
class_name FactionReputation
extends Node

enum Faction { ACADEMIC, CARTEL, AETHER, SYNTHETICA, COMMISSION }
enum Tier { HOSTILE, SUSPICIOUS, NEUTRAL, FRIENDLY, TRUSTED, ALLIED }

@export var reputation: Dictionary = {
    Faction.ACADEMIC: 0.0,
    Faction.CARTEL: 0.0,
    Faction.AETHER: 50.0,
    Faction.SYNTHETICA: 0.0,
    Faction.COMMISSION: 0.0
}

func adjust(faction: Faction, delta: float, source: String) -> void:
    reputation[faction] = clamp(reputation[faction] + delta, -100.0, 100.0)
    _check_tier_transitions(faction)
    _emit_reputation_changed(faction, source)

func get_tier(faction: Faction) -> Tier:
    var rep = reputation[faction]
    if rep <= -50: return Tier.HOSTILE
    elif rep <= -20: return Tier.SUSPICIOUS
    elif rep < 30: return Tier.NEUTRAL
    elif rep < 60: return Tier.FRIENDLY
    elif rep < 90: return Tier.TRUSTED
    else: return Tier.ALLIED
```

### 10.3 Codex/Encyclopedia (`athanor_encyclopedia.gd` — new autoload)

```gdscript
class_name AthanorEncyclopedia
extends Node

# Four volumes as dictionaries
@export var reagents: Dictionary = {}      # key: SMILES -> ReagentEntry
@export var recipes: Dictionary = {}       # key: quest_id -> RecipeEntry
@export var genomes: Dictionary = {}       # key: organism_id -> GenomeEntry
@export var isotopes: Dictionary = {}      # key: compound+source -> IsotopeEntry

func discover_reagent(smiles: String, source: DiscoverySource) -> void:
    if not reagents.has(smiles):
        reagents[smiles] = ReagentEntry.new(smiles, source)
        _generate_crosslinks(smiles)
        _check_capability_unlocks()

func get_retrosynthesis(target_smiles: String) -> Array[RouteProposal]:
    # Uses recipes + reagents to propose 3 routes with trade-offs
    ...

func generate_forensic_report(sample_data: Dictionary) -> ForensicReport:
    # Uses isotopes + recipes for instant attribution
    ...
```

### 10.4 Vertical Traversal (`lab_traversal.gd` — new component)

```gdscript
class_name LabTraversal
extends Node3D

@export var current_zone: LabZone = LabZone.GROUND_FLOOR
@export var unlocked_viewpoints: Array[String] = []
@export var traversal_skills: Dictionary = {}  # skill_id -> bool

func can_access(zone: LabZone) -> bool:
    # Checks reputation, skills, keycards, quest flags
    ...

func trigger_viewpoint_sync(viewpoint_id: String) -> void:
    # Reveals map sector, unlocks fast-travel, grants codex entry
    ...

func attempt_leap_of_faith(leap_id: String) -> LeapResult:
    # Validates requirements, runs hold timer, executes consequence
    ...
```

### 10.5 Investigation Minigames (`investigation_minigames.gd`)

```gdscript
# Each minigame is a Scene with standardized interface
class_name InvestigationMinigame
extends Control

signal completed(results: Dictionary)
signal failed(reason: String)

# Implemented minigames:
# - GCMSImpurityFingerprinting
# - HeadspaceSPME_GCMS
# - CovertSampleAcquisition (PaperSprayMS)
# - ForensicConfrontationDialogue
# - ChemicalSignatureTracking (PTRMS)
# - ForensicCountermeasures
# - IRMSIsotopeSourcing
# - SpectralOverlayHUD
```

---

## 11. Narrative Beats Summary — The Complete Arc

| Act | Theme | Key Quests | Leap of Faith | Faction Crossroads | Codex Milestone |
|---|---|---|---|---|---|
| **I: Initiation** | Competence | Orientation, Titration, Aspirin, Spill Drill, BZ Oscillator | — | Academic vs. Commission (safety score) | Reagent Encyclopedia: 50 entries |
| **II: Evidence** | Investigation | Contaminated Batch, Riverbank Contract, Cryogenic Courier | **Hot Cell Entry** | Cartel contact (Mara) vs. Commission (Hale) | Recipe Book: 20 routes; Isotope Chart: 10 sources |
| **III: Complicity** | Choice | Quiet Synthesis (moral fork), BZ Coupling, Genome Preview | **Runaway Commitment** | **Sell to Cartel** OR **Evidence to Commission** | Genome Atlas: 5 strains; Sync: 40% |
| **IV: Field** | Expansion | Orbital Insertion, Microgravity Crystallization, Biotech Heist | **Cryogenic Pour** / **Genome Write** | Synthetica alliance vs. Cartel war vs. Commission crackdown | Recipe Book: 100 routes; Sync: 75% |
| **V: Consequence** | Resolution | Athanor Threshold (3 branches) | **Athanor Threshold** | **ENDGAME:** Choose faction alignment | **Sync 100%** → Athanor Engine Live |
| **Post** | Legacy | Faction-specific epilogues, sandbox mastery | Master Leaps (repeatable) | World state reflects choice | Full Encyclopedia — *all knowledge playable* |

---

## 12. Safety & Pedagogical Framing (Non-Negotiable)

Per `CONTINUE_HERE.md` §0.7, `design/gdd/safety-framework.md`:

1. **Every Leap of Faith requires demonstrated competence** — skill nodes, apparatus prep, simulation rehearsal. No "press X to win."
2. **Failure states are educational** — Thermal runaway shows *why* cooling capacity matters. Hot cell entry shows *why* ALARA (As Low As Reasonably Achievable) matters.
3. **No real synthesis instructions for controlled substances** — All routes use allow-listed precursors (aspirin, paracetamol, indigo, caffeine, benzaldehyde, etc.). Illicit routes are *fictionalized* (Prop_G7, "Leuckart signature" as forensic marker only).
4. **GHS hazard communication mandatory** — Every reagent in Codex shows pictograms, H/P statements, PPE requirements.
5. **Commission path rewards safety excellence** — Highest reputation tier requires *zero* safety violations across campaign.

---

## 13. Implementation Priority & Dependencies

| Priority | System | Depends On | Est. Effort |
|---|---|---|---|
| **P0** | Faction Reputation Autoload | `quest_manager.gd`, `skill_manager.gd` | 3 days |
| **P0** | Quest Phase Structure (Investigate/Synthesize/Extract) | `quest_resource.gd` schema update | 2 days |
| **P1** | Leap of Faith Framework | `player_vitals.gd`, `input_manager.gd` | 4 days |
| **P1** | Investigation Minigames (3 core: GC-MS, SPME, Dialogue) | `analytical_lab.gd`, `simulation_bridge.gd` | 10 days |
| **P2** | Athanor Encyclopedia (4 volumes + crosslinks) | `recipe_book.gd`, `reagent_catalog.py` | 7 days |
| **P2** | Vertical Traversal + Viewpoints | `lab_hub.gd`, 15 archetype scenes | 14 days |
| **P3** | Narrative Integration (Dialogue, Audio Logs, Branching) | `quest_overlay.gd`, localization system | 10 days |
| **P3** | Endgame Branching + Epilogues | All above complete | 7 days |

---

## 14. Acceptance Criteria (Definition of Done)

1. **Quest Manager** loads quests with three-phase structure; each phase has distinct objectives, evaluation modes, and failure conditions.
2. **Faction Reputation** tracks 5 factions, 6 tiers, cross-faction dynamics; UI shows tier, unlocks, heat.
3. **Leap of Faith** triggers on 5 designated quests; hold mechanic works; success/failure consequences execute; accessibility hold-time config respected.
4. **Investigation Minigames** (GC-MS fingerprinting, SPME headspace, forensic dialogue) playable with real chemistry data; results feed Codex.
5. **Athanor Encyclopedia** auto-populates from player actions; cross-links generate; retrosynthetic assist proposes 3 routes; forensic report generates in one click.
6. **Vertical Traversal** allows access to all 15 archetype zones; 12 viewpoints reveal map sectors; traversal skills gate progression.
7. **Narrative Branching** at Act III (moral fork) and Act V (endgame) produces distinct world states, faction endings, epilogue cinematics.
8. **All Systems Tested** — Headless Godot tests cover: reputation math, leap validation, investigation minigame I/O, codex crosslink generation, traversal gating.

---

**Document Control**  
Author: Narrative Design Lead  
Review: Physics Lead (chemistry fidelity), QA Lead (testability), Game Director (scope)  
Status: **READY FOR IMPLEMENTATION** — Feeds directly into `quest_manager.gd`, `quest_data.json`, new autoloads.  
Next: Sprint planning for P0 systems (Faction Reputation, Quest Phase Structure).