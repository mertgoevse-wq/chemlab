# ChemLab: Origins — Playable Clandestine Laboratories & Forensic Investigation GDD
**Document Version:** 1.0.0  
**Phase:** Phase B Clandestine Systems, Forensics & Risk Architecture  
**Lead Discipline:** Open World & World Design  
**Target Engine:** Godot 4.7.2 (GDScript) / Headless Simulation Core  

---

## 1. Overview & Criminal Chemistry Gameplay Loop

### 1.1 The Dual-Identity Fantasy
In ChemLab: Origins, clandestine chemistry is not framed as casual criminality, but as high-stakes, technically rigorous chemical engineering operating without institutional safety nets. Players navigate a dual existence:
- By day, a credentialed technician, graduate researcher, or forensic analyst working in municipal universities, certified pharma plants, or crime laboratories.
- By night, a covert operator, contractor for illicit syndicates, or rogue alchemist operating improvised apparatus in basements, bunkers, or diverted industrial reactors.
- Alternatively, players can adopt the dedicated law enforcement track: working as a forensic toxicologist or crime scene investigator (CSI) analyzing abandoned or raided clandestine sites, collecting evidence, profiling chemical impurities, and identifying precursor supply chains.

### 1.2 Core Clandestine Loop
The clandestine loop balances risk, profit, precision, and forensic evasion:

```
  ┌─────────────────────────────────────────────────────────────┐
  │                 1. SOURCING PRECURSORS                      │
  │   Black-market fixers / Diverted university stores /        │
  │   Unregulated hardware store extractions                    │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 2. COVERT LAB ASSEMBLY                      │
  │   Selecting archetype / Rigging improvised apparatus /     │
  │   Configuring scrubbers & power isolation                   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 3. SYNTHESIS EXECUTION                      │
  │   Monitoring stoichiometry / Regulating thermal exotherms / │
  │   Managing odor plumes & volatile exhaust                   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 4. WORKUP & RECRYSTALLIZATION               │
  │   Solvent washing / Vacuum filtration / Purity profiling   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │            5. DISTRIBUTION OR FORENSIC SEIZURE              │
  │   Evaluating yield & purity against buyer contract OR       │
  │   Facing police raid / Forensic trace analysis              │
  └─────────────────────────────────────────────────────────────┘
```

### 1.3 Pedagogical & Safety Framing
In adherence to ChemLab core educational values:
- Syntheses in clandestine mode model real physical chemistry principles: reaction thermodynamics, Le Chatelier shifts, Arrhenius temperature dependence, solvent extraction equilibria, and GHS toxicological hazards.
- All reaction challenges utilize closed, allow-listed chemical catalogs (aspirin, paracetamol, indigo, caffeine, benzaldehyde, nitroethane, salicylic acid, etc.).
- The game emphasizes why safety standards exist: operating without a fume hood or proper cooling leads immediately to glass-shattering exotherms, toxic gas clouds, irreversible batch degradation, and catastrophic failure.

---

## 2. Six Playable Clandestine Lab Archetypes

Every archetype features distinct equipment configurations, resident contacts, reputation gates, quest evaluation criteria, detection risks, and forensic angles.

```
       [ Academic Organic Lab ] <=========> [ Clandestine Improvised Lab ]
            (Institutional Divert)                 (Basement / Remote Shed)
                   ▲                                        ▲
                   │                                        │
                   ▼                                        ▼
       [ Industrial Pharma Lab ] <========> [ Biotech Genetic Lab ]
           (Diverted GMP Pilot)                   (BSL-3 Recombinant)
                   ▲                                        ▲
                   │                                        │
                   ▼                                        ▼
       [ Underground Bunker Lab ] <=======> [ Orbital Zero-G Lab ]
            (Deep Reinforced Vault)              (Free-Fall Enantiomer Core)
```

---

### 2.1 Academic Organic Laboratory (After-Hours University Diversion)
- **Concept:** Working after lock-in hours inside St. Jude University's Department of Chemistry. Legitimate state-of-the-art apparatus used for unsanctioned, off-the-books total syntheses.
- **Equipment Catalog:**
  - Schlenk vacuum-inert gas (Argon) double manifold line.
  - Heidolph Rotary Evaporator with digital chiller.
  - 400 MHz Superconducting FT-NMR Spectrometer (shared campus core).
  - Standard certified DIN EN 14175 Fume Hoods with sliding sash.
  - Pyrex borosilicate multi-neck round bottom flasks, addition funnels, Dimroth condensers.
- **NPC Contacts:**
  - *Prof. Dr. Hartmann:* Department Chair, oblivious if lab cleanliness and consumable logs balance out.
  - *Milo:* Graduate lab assistant willing to look away and falsify solvent withdrawal logs for a 15% credit cut.
- **Reputation Thresholds:**
  - Academic Guild: Requires >= 40.0 reputation to maintain keycard access. Falling below 20.0 revokes access and launches an institutional ethics audit.
  - Syndicate Standing: Neutral (30.0).
- **Quest Evaluation:**
  - High purity demand (minimum 92.0% - 98.0%).
  - Objective failure if unwashed glassware or missing reagents trigger a campus auditor inspection.
- **Risk of Detection:**
  - Primary driver: Consumable auditing and campus security patrols.
  - Secondary driver: Liquid nitrogen or argon tank depletion spikes.
- **Police / Forensics Investigation Angle:**
  - Campus security or police forensic investigators inspect suspect benches using UV light and swab chromatography to detect diverted precursor residue.

---

### 2.2 Clandestine Improvised Laboratory (Basement / Off-Grid Shed)
- **Concept:** A covert, unregulated facility set up in an abandoned basement or remote wilderness cabin. Heavy reliance on jury-rigged hardware, modified domestic appliances, and hardware-store precursors.
- **Equipment Catalog:**
  - Improvised heating mantle using electric hotplates and iron sand baths.
  - Mason-jar thumper condenser loops and modified automotive copper tubing.
  - Acid-resistant plastic buckets and manual hand-pump siphon lines.
  - Makeshift inline blower fan pulling through activated charcoal fish-tank filters.
  - Alcohol thermometers and hand-held digital pH probes.
- **NPC Contacts:**
  - *Viktor 'Kolben' Morozov:* Veteran clandestine glassblower; sells annealed custom glassware and welded stainless condensers.
  - *Spike:* Low-level chemical courier; delivers technical-grade acids and battery solvents.
- **Reputation Thresholds:**
  - Underworld Syndicate: Accessible at >= 10.0 reputation.
  - Regulatory Board: Permanent hostile (0.0). Discovery results in instant raid.
- **Quest Evaluation:**
  - Modest purity tolerance (75.0% - 85.0%), high volume expectations.
  - Strict thermal runaway penalties: improvised vessels shatter if reaction temperature exceeds 110.0°C without ice-bath tempering.
- **Risk of Detection:**
  - Extreme thermal signature on infrared sensors.
  - Distinctive pungent odor plumes (acetic acid, sulfurous byproducts, amine odors) venting into residential areas.
- **Police / Forensics Investigation Angle:**
  - Prime target for tactical HazMat police raids. Investigating players collect soot samples, identify crude battery-acid extraction residues, and profile heavy metal contamination in runoff soil.

---

### 2.3 Industrial Pharma Laboratory (Diverted GMP Pilot Plant)
- **Concept:** An active pharmaceutical manufacturing suite (Synthetica Batch Plant) where off-spec or rogue batches are secretly scheduled between official validated runs.
- **Equipment Catalog:**
  - 50L Jacketed Borosilicate Glass Pilot Reactor with computerized PID cascade heating/cooling.
  - Preparative High-Performance Liquid Chromatograph with UV-Vis Diode Array (HPLC-DAD).
  - Industrial automated gas scrubbers with sodium hydroxide neutralizer loops.
  - Nitrogen-blanketed explosion-proof (ATEX Zone 1) centrifugal separation units.
  - Digital analytical microbalance (0.0001g resolution).
- **NPC Contacts:**
  - *Ingenieur Keller:* Corrupt Quality Assurance Auditor; alters SCADA batch logs and certifies contaminated runs for a fee.
  - *Marcus "The Chemist" Vance:* High-level syndicate broker demanding multi-kilogram batches of pure pharmaceutical intermediates.
- **Reputation Thresholds:**
  - Requires Industrial Pharma Guild >= 65.0 reputation and GMP Certification perk.
  - Underworld Syndicate >= 50.0.
- **Quest Evaluation:**
  - Strict GMP compliance: minimum 99.0% purity, zero detectable heavy metal peaks on HPLC.
  - Yields must exceed 500 grams per run.
- **Risk of Detection:**
  - Corporate regulatory audits, mass-balance discrepancy reports, SCADA telemetry tamper alerts.
- **Police / Forensics Investigation Angle:**
  - White-collar regulatory investigation: reviewing electronic batch records, HPLC retention time logs, and raw material balance sheets for missing feedstocks.

---

### 2.4 Biotech Laboratory (Unregulated CRISPR & Genetic Synthesis)
- **Concept:** A cleanroom facility dedicated to recombinant protein expression, plasmid design, and unlicensed CRISPR-Cas9 genetic editing outside governmental bioethics oversight.
- **Equipment Catalog:**
  - Eppendorf Mastercycler PCR Thermocycler.
  - Class II Type A2 Biosafety Cabinet (Laminar Flow with HEPA H14 filtration).
  - Horizontal Agarose Gel Electrophoresis rig with blue-light transilluminator.
  - High-speed refrigerated centrifuge (15,000 RPM).
  - CO2 Incubator with orbital shaker platform.
- **NPC Contacts:**
  - *Dr. Aris Thorne:* Renegade bioengineer specializing in viral vectors and modified bacterial expression strains.
  - *Klara:* Biomedical supply smuggler supplying synthetic oligonucleotides and enzyme buffers.
- **Reputation Thresholds:**
  - Biotech / Genetics Skill Level >= 35.
  - Underworld Syndicate >= 45.0.
- **Quest Evaluation:**
  - Transformation efficiency scoring; purity evaluated via restriction digest gel band brightness.
  - Zero biological contamination tolerance (bacterial culture collapse on improper autoclave protocols).
- **Risk of Detection:**
  - Biohazard surveillance monitors, genetic sequencing database flags on ordered primer sequences.
- **Police / Forensics Investigation Angle:**
  - BSL-3 Crime Scene: Specialized hazmat suit investigation, collecting Petri dish swabs, running PCR assays to identify genetically modified weaponized or illicit recombinant strains.

---

### 2.5 Underground Bunker Laboratory (Deep Subterra Vault)
- **Concept:** A blast-reinforced subterranean laboratory buried beneath the Badlands. Engineered for hazardous, high-pressure, and volatile chemical processes that would level a city block if detonated.
- **Equipment Catalog:**
  - 10L High-Pressure Stainless Steel Parr Autoclave with rupture disc relief.
  - Dual-tower industrial vacuum distillation column with structured silver packing.
  - Heavy-duty positive-pressure multi-port glovebox line.
  - Multi-stage packed-bed caustic gas scrubber with automatic pH monitoring.
  - Diesel generator with vibration dampening and thermal exhaust cooling.
- **NPC Contacts:**
  - *Walter Blackwood:* Master contraband chemist; provides advanced multi-step synthetic recipes and bulk precursors.
  - *Facility Fixer Milo:* Manages air filtration filters, generator maintenance, and clandestine supply deliveries.
- **Reputation Thresholds:**
  - Underworld Syndicate >= 60.0.
  - Requires completing "Bunker-7 Commissioning" quest line.
- **Quest Evaluation:**
  - Complex organic total syntheses (e.g. multi-step reduction of substituted benzaldehydes).
  - Demands high yield (> 85.0%) and strict exotherm management under pressure.
- **Risk of Detection:**
  - Ground-penetrating radar, seismic vibrations from industrial pumps, bulk solvent transport tracking across the Badlands.
- **Police / Forensics Investigation Angle:**
  - Post-raid forensic reconstruction: mapping blast residue, analyzing solvent drum chemical fingerprints, reconstructing broken glassware fragments to identify reaction schematics.

---

### 2.6 Orbital Zero-G Clandestine Laboratory (Aeterna Microgravity Core)
- **Concept:** A clandestine pressurized module on Aeterna Station Alpha or a hijacked orbital satellite deck. Utilizes microgravity to produce ultra-pure, defect-free pharmaceutical enantiomers that cannot be synthesized cleanly inside Earth's gravity well.
- **Equipment Catalog:**
  - 3D Acoustic Ultrasonic Levitator for containerless fluid manipulation.
  - Microgravity Capillary-Fluidics Reactor with syringe injection pumps.
  - Peltier-cooled vapor diffusion crystallization array.
  - High-Vacuum external line venting directly to outer space ($10^{-5}\text{ mbar}$).
  - Enantiomeric polarimeter and circular dichroism spectrometer.
- **NPC Contacts:**
  - *Commander Elena Vance:* Station commander who turns a blind eye to unregistered orbital experiments in exchange for research kickbacks.
  - *Orbital Courier Jax:* Handles spacecraft launch manifest smuggling and cargo drop-capsules.
- **Reputation Thresholds:**
  - Orbital Research Consortium >= 70.0.
  - Physical Chemistry Skill Level >= 60.
- **Quest Evaluation:**
  - Enantiomeric excess ($ee > 99.5\%$), zero sedimentation defects in crystalline lattice.
  - Liquids must never detach or drift into air circulation vents (catastrophic station hazard).
- **Risk of Detection:**
  - Space station life-support atmospheric sensors (detecting traces of volatile solvents in cabin air), orbital telemetry audits.
- **Police / Forensics Investigation Angle:**
  - Spacecraft accident investigation: analyzing microgravity chemical residue droplets adhering to station bulkheads; reviewing orbital flight recorder telemetry.

---

## 3. Equipment Catalog & Improvisation Matrix

Clandestine operations frequently require substituting commercial, certified instruments with improvised hardware. This introduces physical performance trade-offs, drift, and failure modes.

### 3.1 Equipment Comparison Specification

| Instrument Type | Certified Commercial Grade | Improvised Clandestine Grade | Failure Mode / Trade-off |
|---|---|---|---|
| Heating Apparatus | PID Digital Ceramic Hotplate (±0.5°C) | Electric Camp Stove + Sand Bath | Severe thermal lag; hot spots cause pyrolysis/charring. |
| Condenser | Double-Surface Dimroth Borosilicate | Copper Coil in Ice Water Bucket | Copper leaching into acidic mixtures; vapor leaks. |
| Distillation Column | 30 cm Vacuum-Jacketed Vigreux | Mason Jar Multi-Stage Thumper | Vapor pressure surges; gasket blowout under heat. |
| Filtration | Buchner Funnel with Diaphragm Pump | Coffee Filters in Cut Funnel + Siphon | Slow flow; paper fibers contaminate product (drops purity 8%). |
| Gas Exhaust | Certified EN 14175 Fume Hood (0.5 m/s) | Bathroom Blower + PVC Pipe + Charcoal | Blower motor sparks ignite solvent vapors (explosion risk). |
| Analytical Testing | Agilent 1260 HPLC with DAD (600 bar) | Thin-Layer Chromatography (TLC) Silica Plates | Semi-quantitative; cannot distinguish similar impurities. |
| Inert Atmosphere | Argon 5.0 Line with Schlenk Bubbler | Argon Balloon with Syringe Needle | Slow oxygen/moisture leakage; hydrolyzes sensitive reagents. |

### 3.2 Equipment Degradation & Maintenance
All laboratory apparatus tracks a `condition` rating ($0.00$ to $1.00$):
- **Glassware Stress Fatigue:** Borosilicate vessels accumulate micro-fractures with each rapid thermal cycle ($> 5.0^\circ\text{C/sec}$). At condition $< 0.40$, applying heat carries a 25% chance of catastrophic thermal shattering.
- **Carbon Scrubber Saturation:** Activated carbon filters degrade by 0.05 per gram of volatile solvent passed through them. When condition reaches 0.0, volatile odors vent directly into the atmosphere, causing immediate police heat spikes.
- **Cleaning & Maintenance:** Glassware must be washed with acetone and deionized water. Unwashed vessels carry contamination residues that penalize subsequent reaction purity by up to 15%.

---

## 4. NPC Contacts & Syndicate Network

### 4.1 Narrative Profiles & Specializations

#### 4.1.1 Walter Blackwood — The Master Contraband Chemist
- *Role:* Contraband Chemist (Senior Syndicate Mentor).
- *Background:* Former industrial chemical engineer forced out during regulatory crackdowns. Now the premier synthesis consultant for the Badlands underworld.
- *Personality:* Methodical, impatient with sloppy technique, obsessive about yield and stoichiometry.
- *Trade Inventory:*
  - Benzaldehyde (Reagent Grade, 99%): 500 mL @ 120 Credits.
  - Nitroethane (Technical Grade, 95%): 250 mL @ 250 Credits.
  - Toluene (Dry, Anhydrous): 1,000 mL @ 80 Credits.
  - Concentrated Sulfuric Acid (98%): 500 mL @ 95 Credits.
- *Signature Dialogue:*
  - *"Reines Produkt erfordert absolute Geduld, Kollege. Wer die Temperatur überfährt, erntet Teer statt Kristalle."*
  - *"Pass auf die Säuredämpfe auf – mein Abzug zieht nicht mehr richtig."*

#### 4.1.2 Viktor 'Kolben' Morozov — Master Glassblower & Hardware Fixer
- *Role:* Facility Fixer / Glassblower.
- *Background:* Former scientific glass apparatus craftsman. Sells custom borosilicate glassware, jacketed adapters, and repairs shattered vessels.
- *Trade Inventory:*
  - 1000 mL 3-Neck Round Bottom Flask (24/40 Joint): 150 Credits.
  - Friedrichs High-Efficiency Condenser: 220 Credits.
  - Custom Improvised Vacuum Manifold: 310 Credits.
- *Signature Dialogue:*
  - *"Schliff 24/40 passt auf alles. Aber wenn du den Kolben trocken kochst, kann ich das Glas auch nicht mehr retten."*

#### 4.1.3 Inspector Diane Sterling — Municipal Forensics Lead
- *Role:* Senior Forensic Toxicologist / Law Enforcement Supervisor.
- *Background:* Veteran head of Safehaven Police Forensics. Ruthless against unsafe clandestine polluters, but values brilliant analytical minds.
- *Function:* In CSI mode, assigns investigative bounties. In clandestine mode, represents the primary adversarial heat investigator.
- *Signature Dialogue:*
  - *"Die Chromatographie lügt nie. Jedes Lösungsmittel hinterlässt einen chemischen Fingerabdruck."*

---

## 5. Reputation Thresholds & Faction Heat System

### 5.1 The Dual-Axis Axis Matrix
Player actions are balanced across two antagonistic meters:
1. **Syndicate Reputation ($0.0$ to $100.0$):** Measures trust, access to high-tier precursors, and lucrative contracts.
2. **Police Heat Index ($0.0$ to $100.0$):** Measures municipal law enforcement awareness and active surveillance of player facilities.

```
            High Heat (100)
                  │   [ Tactical HazMat Raid ]
                  │   [ Undercover Sting Operation ]
                  │
  Low Syndicate   │                  High Syndicate
  ────────────────┼────────────────────────────────
  (Broke Amateur) │   [ Criminal Kingpin / Master Chemist ]
                  │   [ Unregulated High-Purity Supply ]
                  │
             Low Heat (0)
```

### 5.2 Heat Generation Mechanics
Heat accumulates dynamically based on observable laboratory signatures:

$$\Delta\text{Heat} = \text{Emission Signature} + \text{Transaction Flag} + \text{Hazard Incident}$$

- **Odor Plume Venting:** Venting volatile organic vapors (benzene, ether, methylamine) without active carbon scrubbers: $+5.0\text{ to }+15.0\text{ Heat/hour}$.
- **Electrical Grid Anomaly:** Running 3,500W heating mantles or chillers on residential power lines: $+3.0\text{ Heat/run}$.
- **Precursor Requisition:** Purchasing Schedule II chemicals from flagged vendors without forged permits: $+8.0\text{ Heat/transaction}$.
- **Catastrophic Explosion / Fire:** Glass rupture or runaway exotherm emitting visible smoke: $+35.0\text{ Instant Heat}$.

### 5.3 Heat Decay & Countermeasures
- **Cooling Period:** Halting all synthesis operations for 48 in-game hours: $-10.0\text{ Heat/day}$.
- **Evidence Incineration:** Destroying batch waste and contaminated glassware in a high-temperature kiln: $-15.0\text{ Heat}$, costs glassware.
- **Bribery & Corrupt Audits:** Paying Facility Fixers or corrupt QA auditors (Keller) to scrub police dispatch logs: $-25.0\text{ Heat}$ (costs 1,000 Credits).

---

## 6. Quest Evaluation Engine: Purity, Stoichiometry & Yield

The simulation validates completed laboratory products through algorithmic evaluation in `LabQuest.evaluate_submission()`.

### 6.1 Evaluation Parameters

```python
class LabQuestObjective:
    target_compound: str             # e.g. "aspirin", "benzaldehyde", "indigo"
    min_purity_percent: float = 90.0 # Tested via HPLC, GC-MS, or melting point
    min_yield_grams: float = 5.0     # Final dry mass recovered
    requires_fume_hood: bool = False # Safety protocol compliance
    max_temperature_c: float | None  # Thermal degradation ceiling
    min_temperature_c: float | None  # Activation energy floor
```

### 6.2 Evaluation Scoring Rules
1. **Target Compound Verification:** Submitted product must match `target_compound` exactly. Submitting wrong compounds or unreacted precursors triggers immediate rejection.
2. **Safety Protocol Gate:** If `requires_fume_hood` is active and the player executed the reaction on an open bench, the submission fails with a critical safety violation:
   ```
   "Sicherheitsverstoß: Reaktion wurde nicht im vorgeschriebenen Abzug durchgeführt!"
   ```
3. **Analytical Purity Verification:**
   - If tested purity $\ge \text{min\_purity\_percent}$, check passes.
   - If tested purity $< \text{min\_purity\_percent}$, rejection feedback is generated:
   ```
   "Reinheit unzureichend: {purity:.1f}% erzielt, mindestens {min_purity:.1f}% gefordert."
   ```
4. **Yield Verification:**
   - Calculated against limiting reagent stoichiometry. If actual mass $< \text{min\_yield\_grams}$:
   ```
   "Ausbeute zu gering: {yield:.1f}g erzielt, mindestens {min_yield:.1f}g gefordert."
   ```
5. **Thermal Boundary Enforcement:**
   - Exceeding `max_temperature_c` results in thermal degradation (tarring/charring) and quest rejection:
   ```
   "Temperaturüberschreitung: {temp:.1f}°C überschreitet Maximum von {max_temp:.1f}°C."
   ```

---

## 7. Risk of Detection, Mitigation & Raid Mechanics

### 7.1 Surveillance Tiers

```
  Heat Index Range      Surveillance Tier          Operational Consequences
  --------------------------------------------------------------------------------------
  0.0 – 24.9            Dormant                    Normal operations. Zero inspection risk.
  25.0 – 49.9           Monitored                  Utility company meter audits; courier shipping delays.
  50.0 – 74.9           Active Investigation       Undercover drones scan perimeter; 20% trade surcharge.
  75.0 – 89.9           Warrant Pending            Police checkpoint outside district; random stop-and-search.
  90.0 – 100.0          Imminent Tactical Raid     Armed HazMat SWAT breach event within 12–24 in-game hours.
```

### 7.2 Tactical Raid Event Sequence
When Heat reaches 90.0+, a dynamic countdown triggers:
1. **Stage 1: Early Warning (Audio/Visual Siren):** Fixers send an encrypted warning: *"Police vans spotted entering the sector. Scrub the lab immediately!"*
2. **Stage 2: Emergency Response Options:**
   - *Option A: Flush & Neutralize:* Dump reaction mixtures into emergency neutralizer vats (quenches acids with sodium bicarbonate). Saves player from criminal arrest, but destroys all ongoing batches and reagents.
   - *Option B: Rapid Evacuation:* Grab portable analytical gear and finished product; flee to a secondary safehouse. Abandons heavy reactors.
   - *Option C: Falsify & Cover:* If in an Academic or Pharma lab, scramble to replace reaction labels with legitimate student experiment badges. Requires high Deception / Academic reputation check.
3. **Stage 3: Raid Aftermath:** If caught, the facility is quarantined with police crime-scene tape; all unhidden equipment is impounded; player pays heavy bail credits or completes mandatory community remediation quests.

---

## 8. Police & Forensics Crime-Scene Investigation (CSI) Angle

ChemLab offers a complete, playable investigative gameplay loop where the player steps into the role of a forensic chemical investigator.

```
       [ Secure Crime Scene Perimeter ]
                     │
                     ▼
       [ Presumptive Field Screening ] 
       ├── Luminol Spray (Blood / Peroxide detection)
       ├── Ninhydrin Fuming (Fingerprint amino acid visualization)
       └── Handheld Raman Gun (Non-destructive powder scan)
                     │
                     ▼
       [ Confirmatory Instrumental Analysis ]
       ├── GC-MS Separation (Volatile solvents & cutting agents)
       └── HPLC Impurity Profiling (Batch origin fingerprinting)
                     │
                     ▼
       [ Evidence Filing & Warrant Authorization ]
```

### 8.1 Forensic Toolset & Investigative Apparatus
1. **Luminol Chemiluminescent Solution:**
   - *Reaction:* Oxidized by hydrogen peroxide in the presence of iron catalyst (hemoglobin or metal salts) to produce intense blue chemiluminescence ($\lambda_{max} \approx 425\text{ nm}$).
   - *Use:* Reveals wiped chemical spills, cleaned vessel tables, and clandestine splash zones.
2. **Ninhydrin Developer Solution:**
   - *Reaction:* Reacts with primary amino acids deposited in sweat to form Ruhemann's Purple dye.
   - *Use:* Visualizes latent fingerprints on glassware, chemical reagent bottle labels, and synthesis notebooks.
3. **Handheld Raman Spectrometer (HazMat HazMaster Pro):**
   - *Laser Source:* 785 nm near-infrared diode laser.
   - *Use:* Direct through-glass identification of unknown liquids and white powders without opening containers or exposing the investigator to toxic vapors. Returns instant CAS number and spectrum matching.
4. **Benchtop Gas Chromatography - Mass Spectrometry (GC-MS):**
   - *Use:* Resolves volatile solvent mixtures, identifying exact ratios of toluene, acetone, and hydrochloric acid.
   - *Impurity Profiling:* Identifies synthetic routes. For example, detecting residual o-nitrobenzaldehyde and acetone condensation intermediates proves an illegal indigo dye or related precursor batch was processed.
5. **Chain-of-Custody Evidence Packaging:**
   - Player must log, bag, and seal samples in tamper-evident anti-static bags, recording mass, physical state, and discovery location. Flawed chain of custody invalidates forensic quest rewards.

### 8.2 The Inverted CSI Dynamic: Cleaning Your Own Crime Scenes
If a player's clandestine lab is compromised or abandoned, the player can return under cover of darkness to conduct counter-forensics:
- Neutralizing residual acids with sodium bicarbonate to erase corrosive etch marks.
- Solvent-washing workbenches with bleach or ethanol to destroy DNA and latent amino acids.
- Replacing contaminated trap water in gas scrubbers.
- Erasing analytical instrument memory logs on shared campus HPLC or NMR terminals.

---

## 9. Data-Driven Configuration Specifications

All clandestine laboratory archetypes, equipment degradation models, and forensic investigation parameters are defined in machine-readable JSON format.

### 9.1 Clandestine Archetypes Specification (`clandestine_archetypes.json`)

```json
{
  "$schema": "https://chemlab.sim/schemas/clandestine.json",
  "version": "1.0.0",
  "archetypes": [
    {
      "archetype_id": "academic_organic_divert",
      "display_name": "Academic Organic Lab (After-Hours)",
      "base_security": "campus_card_access",
      "risk_profile": {
        "base_heat_per_hour": 1.5,
        "odor_leak_multiplier": 0.2,
        "power_spike_sensitivity": 0.3,
        "inspection_interval_hours": 72
      },
      "reputation_prerequisites": {
        "academic_guild": 40.0,
        "underworld_syndicate": 20.0
      },
      "key_equipment_ids": [
        "schlenk_line_dual",
        "rotavapor_chiller",
        "fume_hood_certified",
        "nmr_400mhz"
      ],
      "prohibited_byproducts": ["toxic_chloramine_gas", "tarred_polymer_sludge"]
    },
    {
      "archetype_id": "clandestine_improvised_shed",
      "display_name": "Clandestine Improvised Lab",
      "base_security": "improvised_unregulated",
      "risk_profile": {
        "base_heat_per_hour": 8.0,
        "odor_leak_multiplier": 1.8,
        "power_spike_sensitivity": 1.2,
        "inspection_interval_hours": 24
      },
      "reputation_prerequisites": {
        "academic_guild": 0.0,
        "underworld_syndicate": 10.0
      },
      "key_equipment_ids": [
        "makeshift_heating_mantle",
        "clandestine_condenser_loop",
        "diy_carbon_blower",
        "tlc_plate_kit"
      ],
      "thermal_runaway_threshold_c": 115.0
    },
    {
      "archetype_id": "underground_bunker_vault",
      "display_name": "Underground Bunker Complex",
      "base_security": "reinforced_bunker",
      "risk_profile": {
        "base_heat_per_hour": 2.0,
        "odor_leak_multiplier": 0.1,
        "power_spike_sensitivity": 0.1,
        "inspection_interval_hours": 168
      },
      "reputation_prerequisites": {
        "academic_guild": 0.0,
        "underworld_syndicate": 60.0
      },
      "key_equipment_ids": [
        "parr_high_pressure_reactor",
        "industrial_packed_distillation_column",
        "glovebox_inert",
        "caustic_gas_scrubber"
      ],
      "thermal_runaway_threshold_c": 180.0
    }
  ]
}
```

### 9.2 Forensic Investigation & Evidence Registry (`forensic_systems.json`)

```json
{
  "$schema": "https://chemlab.sim/schemas/forensics.json",
  "version": "1.0.0",
  "investigative_tools": [
    {
      "tool_id": "handheld_raman_spectrometer",
      "name": "HazMaster Pro Handheld Raman",
      "technique": "Non-destructive vibrational spectroscopy",
      "scan_duration_sec": 4.5,
      "identifies": ["solids", "pure_liquids", "through_glass"],
      "accuracy_percent": 99.2
    },
    {
      "tool_id": "luminol_chemiluminescent_spray",
      "name": "Forensic Luminol Reagent Solution",
      "technique": "Catalytic oxidation chemiluminescence",
      "scan_duration_sec": 1.0,
      "identifies": ["blood_spatter", "peroxide_residues", "metal_catalyst_traces"],
      "requires_darkness": true
    },
    {
      "tool_id": "ninhydrin_aerosol_developer",
      "name": "Ninhydrin Latent Fingerprint Developer",
      "technique": "Ruhemann purple amino acid condensation",
      "scan_duration_sec": 12.0,
      "identifies": ["porous_surface_fingerprints", "sweat_residues"],
      "requires_thermal_cure": true
    }
  ],
  "forensic_markers": {
    "toluene_pyrolysis_marker": "dibenzyl_trace",
    "acid_spill_marker": "calcium_sulfate_etching",
    "unwashed_flask_marker": "cross_batch_tar_fingerprint"
  }
}
```
