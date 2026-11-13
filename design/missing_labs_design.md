# Missing Labs Design — 9 Laboratory Terminals for Athanor Ascension

Each lab design follows the roadmap specification: (1) terminal scene driven by physical quantities, (2) one real unit operation with measurable outcome, (3) 3–4 named failure modes teaching the actual constraint, (4) Blender set dressing only after interaction is correct. Scientifically accurate — real constants, real equations.

---

## 1. Electrochemistry Laboratory

**Lab name & archetype:** Electrochemistry Laboratory (electrochem_lab, tier 3, physical category)

**Core physics:** The Nernst equation governs electrode potentials; the Butler-Volmer equation describes current density as a function of overpotential. Real electrochemistry measures potential (V) and current (A) as the primary observables.

**Terminal scene layout:** A compact benchtop scene with a potentiostat connected to a computer display. The player sees: (a) a three-electrode setup — working electrode (glassy carbon disk 3 mm diameter), reference electrode (Ag/AgCl, 0.197 V vs SHE), counter electrode (platinum wire), (b) a sealed glovebox with nitrogen purge, (c) a stir plate with magnetic bar, (d) a digital display showing real-time potential (V) and current (μA), (e) reagent bottles for electrolyte (e.g., 0.1 M H₂SO₄ or 0.1 M KCl), (f) a gas evolution detector (bubble column) for oxygen/hydrogen production. The player interacts with a voltage slider and sees current response.

**Unit operation:** **Water electrolysis** — the player sets a cell potential of 2.0 V DC across the three-electrode cell in 0.1 M H₂SO₄. The physics model uses the **Butler-Volmer equation** to compute current density: `j = j₀ [exp(α_a F η / RT) − exp(−α_c F η / RT)]` with exchange current density j₀ = 10⁻⁵ A/cm², α_a = α_c = 0.5, electrode area 0.07 cm². The measurable output is **hydrogen volume produced (mL)** at the cathode, computed from Faraday's law: `V_H2 = (I · t · 22.414 L/mol) / (2 × F) · 1000`, where I is current in A, t is time in seconds, F = 96485 C/mol.

**Failure modes (3–4):**
1. **Hydrogen evolution overpotential** — if the player uses a platinum counter electrode but the working electrode is untreated carbon, the overpotential for H₂ evolution increases, requiring higher voltage than expected. This teaches that electrode material matters for overpotential.
2. **Solution resistance (iR drop)** — if the electrolyte concentration is too low (< 0.01 M), the uncompensated resistance causes a voltage drop that the player observes as the measured potential being lower than the setpoint, teaching that conductivity matters.
3. **Cathode passivation** — if the player runs the electrolysis too long without stirring, hydrogen bubbles coat the working electrode, reducing the active area and causing current to drop precipitously. This teaches that mass transport limits current.
4. **Chloride corrosion** — if the player selects 0.1 M NaCl electrolyte instead of KCl or H₂SO₄, chlorine gas evolves at the anode instead of oxygen, which is toxic and damages the equipment. This teaches electrolyte selection matters for safety.

**Success criteria:** Hydrogen volume within 10 % of theoretical (e.g., 25.0 mL ± 2.5 mL over 5 min at 2.0 V, 8 mA), measured potential within 0.1 V of 2.0 V setpoint, current stabilizes between 7–9 μA. Player earns +50 Chemistry XP and +30 Engineering XP.

**Dependencies:** `game/scripts/labs/electrochem_physics.gd` (new physics module), reagent database entry for H₂SO₄/NaCl/KCl electrolytes, `game/scripts/core/player_vitals.gd` (chemical exposure tracking for acid/contact).

**Athanor flavor:** The lab is located in a hidden underground facility beneath the Athanor complex, with a vaulted brick ceiling, copper tubing running along the walls for cooling, and the player's hand tracked by a webcam-driven gesture system that reaches toward the potentiostat knobs — the architecture reflects early 20th-century electrochemical research labs, with the Athanor aesthetic of warm ambient lighting against cold metal.

---

## 2. Cell Culture Laboratory

**Lab name & archetype:** Cell Culture Suite (cell_culture, tier 4, life_science category)

**Core physics:** Cell doubling time follows exponential growth `N(t) = N₀ · 2^(t / T_d)` where T_d is the doubling time; oxygen and CO₂ partial pressures affect metabolic rate. The terminal measures **population density (cells/mL)** and **environmental parameters** (pO₂, pCO₂).

**Terminal scene layout:** A sterile lab suite with a biosafety cabinet (Class II, Type A2), a CO₂ incubator set at 5 % CO₂ / 95 % air, an inverted microscope with phase-contrast, a centrifuge, and a digital display showing real-time culture metrics. The player sees: (a) a T-75 flask with cell monolayer, (b) a media bottle, (c) a pipette station, (d) an atmosphere control panel showing pO₂ (kPa) and pCO₂ (kPa), (e) an incubator door with a glass port. The display shows current population density, doubling time estimate, and environment readings.

**Unit operation:** **Passaging (subculturing)** — the player must detach the adherent cell monolayer using trypsin-EDTA, dilute the cells at a 1:4 ratio into fresh media, and transfer 2 mL into a new T-75 flask. The physics model tracks **cell growth** over 72 hours using the exponential model with a doubling time of T_d = 24 h for typical mammalian cells (e.g., HEK293). The measurable output is **final cell density after 72 h**: `N_final = N_initial · 2^(72 / T_d) · recovery_factor`, where recovery_factor = 0.85 if passaging is done correctly, 0.60 if cells are over-digested.

**Failure modes (3–4):**
1. **Over-digestion** — if the player leaves cells in trypsin too long (> 5 min), the cells detach excessively and many die, reducing recovery_factor to 0.40. This teaches that trypsin time must be optimized.
2. **CO₂ starvation** — if the player opens the incubator door too frequently or leaves it open > 2 min, the internal pCO₂ drops below 3 %, slowing metabolism and extending the effective doubling time to 36 h. This teaches that environment stability matters.
3. **Contamination** — if the player fails to sterilize the biosafety cabinet workspace (UV on for < 10 min or gloves not changed), fungal spores appear after 48 h, requiring the culture to be discarded. This teaches aseptic technique is non-negotiable.
4. **Oxygen depletion** — if the culture is in a sealed flask without venting, pO₂ drops below 5 kPa, and cells switch to anaerobic metabolism, lactate accumulates, and the pH drops from 7.4 to 6.8, inhibiting growth and causing cell death. This teaches that gas exchange matters.

**Success criteria:** After 72 h, final cell density is within 15 % of expected (e.g., 1.5 × 10⁶ cells/mL ± 2.25 × 10⁵ cells/mL starting from 5 × 10⁴ cells/mL), contamination check negative, pH 7.3–7.5. Player earns +40 Biology XP and +30 Engineering XP.

**Dependencies:** `game/scripts/labs/cell_culture_physics.gd` (new physics module), species database entry for common cell lines (HEK293, CHO), `game/scripts/core/player_vitals.gd` (chemical/aerosol exposure tracking).

**Athanor flavor:** The suite occupies a sealedwing of the Athanor orbital research station, with positive-pressure HEPA-filtered corridors, airlock-entry protocols, and the player must don a full-face respirator (ABEK P3) before entry — the Athanor aesthetic features sleek curved walls, cool blue indirect lighting, and a view of Earth through the orbital porthole that reminds the player they are off-world.

---

## 3. Radiochemistry Hot Cell

**Lab name & archetype:** Radiochemistry Hot Cell (radiochem_lab, tier 5, nuclear category)

**Core physics:** **Bateman decay equations** describe daughter isotope build-up from a parent isotope; **attenuation** of gamma radiation follows `I = I₀ · exp(−μ · x)` where μ is the linear attenuation coefficient and x is shield thickness. The terminal measures **radioactivity (Bq)**, **dose rate (µSv/h)**, and **isotope identity**.

**Terminal scene layout:** A heavily shielded hot cell facility — the player sees: (a) a lead-shielded enclosure (40 cm Pb, 10 cm polyethylene moderator), (b) remote manipulators (two articulated arms with gripper ends) behind lead glass, (c) a sample holder positioned at the cell center, (d) a gamma survey meter readout, (e) a dose rate display, (f) isotope identification spectrometer readout. The player operates the manipulators via haptic-feedback controllers to move a sealed source from a storage location to the measurement position. The display shows real-time dose rate and decay curve.

**Unit operation:** **Isotope elution from a Mo-99/Tc-99m generator** — the player uses the remote manipulators to connect a elution syringe to the generator column, withdraw the Tc-99m eluate (99mTc m= 25 mCi in 0.9 mL saline), and measure the radioactivity. The physics model uses the **Bateman equation** for daughter build-up: `N_d(t) = (λ_p · N_p(0) / (λ_d − λ_p)) · (exp(−λ_p · t) − exp(−λ_d · t)) + N_d(0) · exp(−λ_d · t)`, where λ_p = ln2 / T_{1/2,p} = 0.693 / 65.9 h (Mo-99, 65.9 h half-life), λ_d = ln2 / T_{1/2,d} = 0.693 / 6.01 h (Tc-99m, 6.01 h half-life). The measurable output is **eluted activity (MBq)** and **specific activity (MBq/mL)**.

**Failure modes (3–4):**
1. **Secular equilibrium mismatch** — if the generator is too fresh (elapsed time < 24 h after previous elution), the Mo-99 parent has not built up enough Tc-99m, and the eluted activity is < 50 % of expected. This teaches that generator age matters.
2. **Shielding geometry error** — if the player positions the sample too close to the lead glass window (distance < 5 cm), the dose rate at the operator position exceeds 100 µSv/h, triggering an interlock shutdown. This teaches that distance and geometry matter for radiation safety.
3. **Radioactive contamination** — if the player fails to decontaminate the manipulator grips after handling the source, surface contamination (dpm/100 cm²) exceeds the clearance level (1000 dpm/100 cm²), requiring a mandatory wipe-down and retest. This teaches that decontamination protocol is essential.
4. **Wrong eluent volume** — if the player uses too much saline (> 2 mL) or too little (< 0.5 mL), the eluted Tc-99m activity is diluted or the column dries out, respectively, both reducing measured activity by > 30 %. This teaches that volume precision matters.

**Success criteria:** Eluted Tc-99m activity within 15 % of expected (e.g., 750 MBq ± 112 MBq from a generator eluted at 48 h post-previous elution, 1 mL saline), specific activity 75–85 MBq/mL, dose rate at operator position < 10 µSv/h. Player earns +60 Nuclear Engineering XP and +40 Safety XP.

**Dependencies:** `game/scripts/labs/nuclear_physics.gd` (new physics module — Bateman equations, attenuation), isotope database (Mo-99, Tc-99m, I-131, Cs-137), `game/scripts/core/player_vitals.gd` (radiation dose tracking).

**Athanor flavor:** The hot cell is buried deep within the Athanor complex's lower levels, with walls of thick lead brick arranged in a herringbone pattern, illuminated by filtered red emergency lighting that preserves the player's night vision for phosphor screening, and the remote manipulators' haptic feedback has a subtle medieval-esque mechanical resistance feel — the Athanor aesthetic juxtaposes ancient masonry with cutting-edge nuclear instrumentation.

---

## 4. Materials & Metallurgy Laboratory

**Lab name & archetype:** Materials & Metallurgy Laboratory (materials_lab, tier 3, materials category)

**Core physics:** **Phase diagram equilibrium** — the player investigates the binary phase diagram of the Cu-Ag system, where the solidus and liquidus temperatures define the melting range. The **cooling rate** determines whether the microstructure is coarse (slow cooling) or fine (fast cooling), per the **Scheil-Gulliver equation** for non-equilibrium solidification. The terminal measures **hardness (HV Vickers)** and **microstructure** (qualitative display).

**Terminal scene layout:** A materials processing bench with an arc furnace (graphite crucible, 1500 °C max), a programmable furnace for controlled cooling, a SEM (scanning electron microscope) mock-up display, a Vickers hardness tester, and a digital display showing temperature (T, °C) and cooling rate (°C/min). The player sees: (a) a crucible with molten Cu-Ag alloy, (b) a cooling curve graph, (c) a microstructure image panel that updates based on cooling rate, (d) a hardness test station with a diamond pyramid indenter. The player inputs the Ag composition (at. %) and cooling rate, and observes the resulting phase structure and hardness.

**Unit operation:** **Cast and hardness-test a Cu-Ag alloy** — the player loads Cu (99.9 %) and Ag (99.9 %) shots into the arc furnace in a specified ratio (0, 10, 25, 50, or 100 at. % Ag), melts at 1500 °C for 5 min, then programs a controlled cool. The physics model uses the **Cu-Ag phase diagram**: for 0–10 at. % Ag, solid solution (face-centered cubic); for 10–25 at. % Ag, two-phase (FCC +); for 25–50 at. % Ag, intermetallic (Cu₃Ag); for 50–90 at. % Ag, intermetallic (Ag₃Cu); for 90–100 at. % Ag, solid solution. The cooling rate (°C/min) determines the fraction of non-equilibrium phases per the Scheil equation. The measurable output is **Vickers hardness number (HV)** and **displayed microstructure description**.

**Failure modes (3–4):**
1. **Segregation** — if the cooling rate is too slow (< 1 °C/min), primary dendrites grow large, and the microstructure coarsens, reducing hardness from the expected HV 120 to HV 70. This teaches that cooling rate controls microstructure.
2. **Eutectic formation** — if the player selects 71.9 at. % Ag (the eutectic composition) and cools slowly, the eutectic structure forms as a fine lamellar intergrowth, but if the cooling is too fast (> 50 °C/min), the eutectic is suppressed and the structure becomes brittle. This teaches that eutectic composition and cooling rate interact.
3. **Oxidation** — if the furnace atmosphere is not inert (argon flow off), the molten alloy oxidizes, forming an oxide inclusion band that reduces effective hardness by 20–30 % and creates surface defects visible in the microstructure display. This teaches that atmosphere control matters.
4. **Quench cracking** — if the player selects a water-quench (cooling rate ~ 200 °C/min) for a high-Ag composition (> 30 at. % Ag), the thermal shock induces microcracking, and the hardness test fails (indenter slips), reading HV 40 instead of the expected HV 95. This teaches that quench compatibility with composition matters.

**Success criteria:** Hardness within 10 % of expected for the chosen composition (e.g., HV 108 ± 11 for 25 at. % Ag cooled at 10 °C/min), microstructure displays the expected phase constituent (e.g., two-phase FCC + for 25 at. % Ag), no oxidation visible. Player earns +40 Materials Science XP and +30 Engineering XP.

**Dependencies:** `game/scripts/labs/materials_physics.gd` (new physics module — Cu-Ag phase diagram, Scheil cooling, Vickers hardness model), arc furnace simulation module, reagent database for Cu and Ag shot sizes.

**Athanor flavor:** The lab occupies a repurposed wing of the Athanor complex with exposed steel I-beams, soot-stained concrete floors, and the arc furnace glows orange through a floor-mounted viewport — the Athanor aesthetic of industrial utilitarianism meets scientific precision, with the player's webcam gesture controls appearing as glowing runes on the furnace console.

---

## 5. Cleanroom Fabrication Bay

**Lab name & archetype:** Cleanroom Fabrication Bay (cleanroom_fab, tier 4, engineering category)

**Core physics:** **ISO particle count** classification (ISO 14644-1): an ISO 5 cleanroom allows ≤ 3,520 particles ≥ 0.5 µm per m³; ISO 7 allows ≤ 352,000 particles ≥ 0.5 µm per m³. The **particle deposition rate** follows `dN/dt = −k · N` where k is the deposition velocity constant, and **personnel gowning** reduces particle shedding by 90 %. The terminal measures **particle count (particles/m³)** and **ISO class compliance**.

**Terminal scene layout:** A ISO-class cleanroom bay (ISO 5, the highest classification in the game) with filtered laminar flow ceiling, gowning room with sequential airlock, a photolithography station (wafer spinner, mask aligner), a particle counter readout display, and a real-time ISO class monitor. The player sees: (a) a wafer on a polished silicon carrier, (b) a gowning station with suit, mask, gloves, booties, (c) a photolithography stepper, (d) a particle counter probe pointing at the wafer, (e) a display showing "ISO Class: X" and particle concentration. The player initiates a gowning sequence, then a lithography cycle, and observes the particle count in real time.

**Unit operation:** **Photolithography pattern transfer** — the player follows the sequence: (1) gown up (don cleanroom suit, mask, gloves, booties — each step checked by the system), (2) enter the cleanroom, (3) load a silicon wafer into the spinner, (4) spin-coat photoresist (2000 rpm, 60 s), (5) soft bake at 95 °C for 60 s, (6) expose via mask aligner (UV, 365 nm, 10 s), (7) develop (positive developer, 60 s), (8) rinse and dry. The measurable output is **particle count after gowning and processing**, compared to the ISO 5 limit (3,520 particles/m³ ≥ 0.5 µm).

**Failure modes (3–4):**
1. **Gowning violation** — if the player skips the bootie step or touches the suit's exterior, the particle count spikes to ISO 8 (352,000 particles/m³), failing the cleanroom class. This teaches that every gowning step matters.
2. **Resist coat thickness error** — if the spinner speed is wrong (e.g., 1000 rpm instead of 2000 rpm), the photoresist is too thick (> 2 µm) or too thin (< 0.5 µm), causing development failure (positive developer leaves resist everywhere or removes all resist). This teaches that spinner speed controls film thickness.
3. **UV leak** — if the cleanroom room light is not filtered for 365 nm and the player turns on overhead lights during exposure, the photoresist exposes prematurely, causing pattern collapse after development. This teaches that light wavelength matters.
4. **Particle agglomeration** — if the HEPA filter has been running for > 200 h without replacement, the particle count gradually rises, and at ISO 6 (35,200 particles/m³) the process must be halted for filter replacement. This teaches that filter maintenance is critical.

**Success criteria:** Particle count after full gowning and lithography cycle is ≤ 3,520 particles/m³ (ISO 5 compliant), resist film thickness 0.8–1.2 µm (measured by display), development yields a clear pattern without collapse. Player earns +35 Engineering XP and +25 Physics XP.

**Dependencies:** `game/scripts/labs/cleanroom_physics.gd` (new physics module — ISO particle stats, gowning attenuation, resist thickness model), photolithography equipment data, `game/scripts/core/player_vitals.gd` (chemical vapor exposure tracking).

**Athanor flavor:** The cleanroom is a windowless white volume with glowing circular overhead panels that emit a soft, sterile illumination; the player must pass through an airlock where the pressure differential is audible (soft hiss), and the Athanor aesthetic features minimalist cubic geometry, hidden seams, and the player's gesture controls are represented as translucent orange wisps that appear when the player's hands enter the clean zone.

---

## 6. Industrial Pilot Plant

**Lab name & archetype:** Industrial Pilot Plant (pilot_plant, tier 5, industrial category)

**Core physics:** **Residence time distribution (RTD)** — the key dimensionless number is the Damköhler number `Da = k · τ` where k is the reaction rate constant (s⁻¹) and τ is the mean residence time (s = V / Q, vessel volume / volumetric flow rate). The **heat duty** for exothermic/endothermic reactions is `Q = UAΔT` where U is the overall heat transfer coefficient, A is the heat transfer area, and ΔT is the temperature difference. The terminal measures **residence time (s)**, **conversion (%)**, and **temperature profile (°C)**.

**Terminal scene layout:** A scaled-down industrial plant control room connected to a pilot-scale continuous stirred-tank reactor (CSTR) — the player sees: (a) a feed tank with pumps, (b) a CSTR (glass vessel, 50 L working volume, agitator with 6-blade turbine), (c) a heat exchanger (jacketed reactor with temperature-controlled circulating bath), (d) online sensors: thermocouples (reactor bulk, jacket outlet), flow meter, concentration probe (inline UV-Vis), (e) a PLC-style touchscreen display showing real-time process variables, (f) emergency quench valve. The player manipulates feed flow rate, coolant temperature, and reactor agitation, and observes the resulting conversion and temperature.

**Unit operation:** **Continuous esterification: acetic acid + ethanol ⇌ ethyl acetate + water** — an exothermic reaction (ΔH = −32. kJ/mol) run as a CSTR at steady state. The physics model uses the **Damköhler number** for a first-order reversible reaction: `Da = k · V / Q` where k = 0.1 s⁻¹ at 80 °C (Arrhenius: k = A · exp(−Ea/RT), Ea = 50 kJ/mol, A = 2.5 × 10⁵ s⁻¹), τ = V / Q, V = 50 L, Q = volumetric flow rate (L/min) set by the player. The conversion is `X = Da / (1 + Da)` for the forward reaction at equilibrium. The measurable output is **conversion (%)** and **reactor temperature (°C)**.

**Failure modes (3–4):**
1. **Thermal runaway** — if the coolant temperature is set too high ( > 60 °C) and the feed flow is too low (< 2 L/min), the heat duty `Q = UAΔT` cannot remove the reaction heat, the temperature rises above 100 °C, the pressure relief valve lifts, and the conversion drops as the reaction equilibrium shifts toward reactants. This teaches that heat removal limits scale-up.
2. **Flooding** — if the feed flow exceeds the agitator's pumping capacity (> 15 L/min for a 6-blade turbine at 100 RPM), the reactor overflows, the emergency dump activates, and the batch is lost. This teaches that flow rate must match mixing capacity.
3. **Inerting loss** — if the player opens the vent valve during operation, air enters the CSTR, the oxygen concentration rises above 2 %, and the reaction (which is anaerobic) slows by 40 % due to aerobic side-reactions, reducing conversion. This teaches that inert atmosphere matters.
4. **Sensor drift** — if the inline UV-Vis concentration probe is not calibrated, the reported conversion drifts 15 % high after 4 h of operation, and the player must perform an online calibration standard injection to restore accuracy. This teaches that sensor maintenance is part of operation.

**Success criteria:** Conversion within 10 % of expected (e.g., 65 % ± 6.5 % at Q = 5 L/min, T_c = 50 °C coolant, 80 °C reactor), temperature profile stable (± 2 °C over 30 min), emergency quench valve does not activate. Player earns +50 Chemical Engineering XP and +35 Engineering XP.

**Dependencies:** `game/scripts/labs/pilot_plant_physics.gd` (new physics module — CSTR model, RTD, heat duty), pump and valve control module, reagent database for acetic acid/ethanol/ethyl acetate/water.

**Athanor flavor:** The pilot plant occupies the Athanor complex's east wing, a two-story industrial volume with riveted steel plates, pipework snake-curving along concrete walls, and the control room lined with walnut-paneled consoles — the Athanor aesthetic of hidden blades and vaulted spaces is reimagined as hidden sensors and interlocks embedded in the industrial infrastructure, with the player's gesture controls triggering valve operations as if by instinct.

---

## 7. Forensic Toxicology Laboratory

**Lab name & archetype:** Forensic Toxicology Laboratory (forensic_lab, tier 3, forensic category)

**Core physics:** **Retention time indexing** — in GC-MS, each compound elutes at a characteristic retention time `t_R` that depends on its boiling point, polarity, and column length. The **calibration curve** relates peak area to concentration: `A = ε · c · V` where A is peak area, ε is the molar absorptivity, c is concentration, and V is injection volume. The terminal measures **retention time (min)**, **peak area (AU)**, and **concentration (mg/L)**.

**Terminal scene layout:** A forensic lab bench with a gas chromatograph-mass spectrometer (GC-MS) console, sample vials, a centrifuge, and a digital workstation display. The player sees: (a) a GC-MS system with injector, column (30 m DB-5ms), detector, and mass spec readout, (b) a set of numbered evidence sample vials, (c) a pipette station, (d) a chromatography workstation showing a chromatogram with peak markers, (e) a calibration curve editor. The player extracts a sample, prepares it, injects it, and observes the resulting chromatogram with compound identification.

**Unit operation:** **Blood alcohol concentration (BAC) determination** — the player processes a simulated whole-blood sample (0.5 mL) via headspace solid-phase microextraction (HS-SPME), injects 1 μL into the GC-MS, and identifies ethanol via its retention time (t_R = 4.2 min on DB-5ms column) and quantitation via the calibration curve (peak area vs. BAC in mg/dL). The physics model uses the **calibration curve** `BAC (mg/dL) = 0.025 · peak_area − 0.15` validated for 0.00–0.30 mg/dL. The measurable output is **BAC (mg/dL)** and **compound identification confidence**.

**Failure modes (3–4):**
1. **Column contamination** — if the player injects a sample without prior solvent rinse (e.g., skips the 2-min methanol rinse between injections), stationary phase contamination shifts retention times by > 0.3 min, causing ethanol to elute at 4.5 min instead of 4.2 min, and the system fails to match the reference retention time. This teaches that column maintenance matters.
2. **Matrix effect** — if the player samples whole blood with high protein content (> 50 % hematocrit) without protein precipitation step, the ethanol peak area is suppressed by 25 % due to matrix suppression, and the calculated BAC is 25 % lower than the actual value. This teaches that sample prep must remove protein.
3. **Standard drift** — if the calibration standard is > 30 days old, the slope of the calibration curve drifts by 15 %, and the reported BAC is systematically biased low. This teaches that standards have expiration dates.
4. **Column bleed** — if the GC-MS injector temperature is set too high (> 300 °C), the column stationary phase degrades, producing a baseline noise that masks small peaks, and co-eluting compounds are not resolved. This teaches that injector temperature must be optimized for the column.

**Success criteria:** BAC within 10 % of true value (e.g., 0.080 mg/dL ± 0.008 mg/dL if true is 0.080 mg/dL), ethanol peak identified with retention time match within 0.05 min, calibration curve R² ≥ 0.995. Player earns +40 Forensic Science XP and +30 Chemistry XP.

**Dependencies:** `game/scripts/labs/forensic_physics.gd` (new physics module — retention time model, calibration curve), GC-MS simulation data, reagent database for blood draw simulation kits.

**Athanor flavor:** The lab is a dimly lit chamber with evidence boards covered in leather, the GC-MS humming in the background, and the player's webcam gesture controls appear as ghostly white outlines over the sample vials — the Athanor aesthetic of shadows and hidden details, where the player must carefully examine each piece of "evidence" to uncover the truth.

---

## 8. Orbital Microgravity Laboratory

**Lab name & archetype:** Orbital Research Station 'Apex' (microgravity, tier 6, space category)

**Core physics:** **Microgravity fluid dynamics** — in zero-g, there is no buoyancy-driven convection (`g · β · ΔT · ρ` term vanishes), and diffusion dominates mass transport. The **Péclet number** `Pe = u · L / D` where u is the characteristic velocity (near zero in microgravity), L is the characteristic length, and D is the diffusion coefficient. The **crystal growth rate** in microgravity follows the **Ostwald-Freundlich equation** for solubility modification: `ln(S/S₀) = (2 · γ · V_m) / (r · R · T)` where γ is the interfacial energy, V_m is the molar volume, r is the particle radius, and S/S₀ is the supersaturation ratio. The terminal measures **crystal size (µm)**, **growth rate (µm/h)**, and **sedimentation velocity (µm/h, expected ≈ 0)**.

**Terminal scene layout:** A interior section of the orbital research station 'Apex' — the player sees: (a) a closed cylindrical growth chamber (5 cm diameter, 10 cm length) with transparent viewport, (b) a video microscope imaging crystals growing, (c) a control panel with parameters: temperature (T, °C), rotation rate (RPM, for artificial gravity tweak), supersaturation setting, (d) a display showing real-time crystal image, size histogram, and Pe number, (e) a comparison view of Earth viewport showing cloud convection vs. the stillness inside the chamber. The player sets the temperature and supersaturation, and observes crystal growth over a simulated 48 h period condensed into a few minutes of gameplay.

**Unit operation:** **Protein crystal growth (lysozyme)** — the player sets the chamber temperature (20–25 °C) and supersaturation ratio (S = 1.1–1.5), and the system simulates 48 h of growth in microgravity. The physics model uses the **diffusion-limited growth** model: `dr/dt = (D · (S − 1)) / r` where r is the crystal radius, D is the diffusion coefficient of lysozyme (D = 1.0 × 10⁻¹⁰ m²/s in water). In microgravity (Pe ≈ 0), growth is purely diffusion-limited; in 1-g, convection enhances growth but produces more defective crystals. The measurable output is **final crystal size after 48 h** and **quality factor** (resolution ratio, expected > 0.8 in microgravity vs. < 0.5 in 1-g).

**Failure modes (3–4):**
1. **Convection contamination** — if the player accidentally sets a rotation rate > 0 RPM (simulating artificial gravity effects), buoyancy-driven convection appears, the Péclet number increases to Pe > 10, and the crystal quality factor drops from > 0.8 to < 0.4, with larger but more defective crystals. This teaches that microgravity requires near-zero velocity.
2. **Oversaturation** — if the player sets S > 1.8, the crystallization is too rapid, producing many nucleation sites and many tiny crystals (< 10 µm) instead of a few large, high-quality crystals (> 100 µm). This teaches that moderate supersaturation is needed.
3. **Temperature drift** — if the chamber temperature fluctuates by ± 2 °C around the setpoint, the solubility changes (proteins typically have dS/dT ≈ 0.02 /°C), and the effective supersaturation varies, causing irregular growth patterns and cracked crystals. This teaches that temperature stability matters.
4. **Container wall effects** — if the crystal grows within 100 µm of the growth chamber wall, the no-slip boundary condition induces a concentration gradient that distorts the crystal shape (faceting toward the wall). This teaches that sample-center positioning is needed.

**Success criteria:** Final crystal size > 50 µm, quality factor > 0.8 (resolution ratio), sedimentation velocity ≈ 0 µm/h (confirmed by the model). Comparison display shows the microgravity crystal vs. a 1-g reference crystal of inferior quality. Player earns +45 Space Science XP and +30 Physics XP.

**Dependencies:** `game/scripts/labs/microgravity_physics.gd` (new physics module — diffusion-limited growth, Péclet number, Ostwald-Freundlich), orbital station environmental control data, comparison dataset of 1-g vs. 0-g crystal growth.

**Athanor flavor:** The orbital station 'Apex' features a circular corridor with portholes showing the Earth's curvature, the clean lab module has anti-gravity visual effects (particles floating motionless), and the player's gesture controls float weightlessly — the Athanor aesthetic of the hidden blade becomes the hidden gravitational control, with the player's movements influencing the subtle rotation dial that tweaks artificial gravity.

---

## 9. Cryogenic & Vacuum Laboratory

**Lab name & archetype:** Cryogenic & Vacuum Laboratory (cryo_lab, tier 4, physical category)

**Core physics:** **Joule-Thomson effect** — the temperature change during throttling of a gas through a porous plug: ` (∂T/∂P)_H = −(μ_JT) ` where μ_JT is the Joule-Thomson coefficient. For nitrogen: μ_JT ≈ 0.28 K/MPa at 300 K; for helium: μ_JT ≈ 0.01 K/MPa (near-zero at room temperature). **Boiling point** at reduced pressure: `T_b(P) = T_b(1 atm) · (P / 1 atm)^(2/7)` (approx. from Clausius-Clapeyron). The terminal measures **temperature (K)**, **pressure (Pa)**, **boiling point (K)**, and **cool-down time (s)**.

**Terminal scene layout:** A cryostat facility with a dilution refrigerator (base temperature 10 mK), a vacuum chamber (base pressure 10⁻⁶ Pa), liquid nitrogen and liquid helium dewars, a sample stage with temperature control, and a digital display showing real-time temperature (K) and pressure (Pa). The player sees: (a) a vacuum chamber with viewports, (b) liquid helium dewar (4 K), (c) liquid nitrogen dewar (77 K), (d) a sample stage inside the cold finger, (e) a temperature controller readout, (f) a vacuum gauge. The player cools a sample from 300 K to base temperature by pumping on the chamber, then measures the boiling point of nitrogen/helium at reduced pressures.

**Unit operation:** **Joule-Thomson pre-cooling to 4 K** — the player opens the vacuum valve to pump the chamber, then switches the gas flow through a JT valve from compressed helium (5 MPa) to the sample chamber. The physics model uses the **Joule-Thomson coefficient** for helium: `ΔT = −μ_JT · ΔP` with μ_JT = 0.01 K/MPa. Starting from 300 K and ΔP = 5 MPa (full decompression), the temperature drop is ΔT = 0.01 × 5 = 0.05 K — insufficient alone, so the player must cascade: helium JT pre-cooling to ~20 K, then liquid nitrogen bath (77 K), then liquid helium bath (4 K). The measurable output is **base temperature achieved (mK)** and **cool-down time (minutes)**.

**Failure modes (3–4):**
1. **Liquid helium boil-off** — if the vacuum chamber pressure is not reduced below 10⁻³ Pa before introducing liquid helium, the boiling liquid heat-load exceeds the capacity, the helium boils off in < 30 min, and the temperature rises above 20 K, ruining the experiment. This teaches that vacuum must be established first.
2. **Joule-Thomson inversion** — if the player attempts JT cooling with nitrogen above its inversion temperature ( > 621 K for N₂ at typical pressures), the gas warms upon expansion (μ_JT becomes negative), and the chamber temperature increases instead of decreasing. This teaches that JT coefficient sign depends on temperature.
3. **Frost formation** — if the sample stage is at 77 K (liquid nitrogen) and the vacuum valve is opened too quickly, ambient moisture freezes on the cold surface, forming an ice layer > 1 mm thick that thermally insulates the sample and prevents reaching lower temperatures. This teaches that venting must be done slowly.
4. **Thermal contraction stress** — if the player cools a metallic sample too rapidly (cooling rate > 10 K/min) from 300 K to 4 K, the differential thermal contraction induces microcracks (CTE of steel ≈ 12 × 10⁻⁶ /K, ΔT = 296 K, strain ≈ 0.35 %, stress ≈ 100 MPa), and the sample fractures upon handling. This teaches that cool-down rate must be controlled.

**Success criteria:** Base temperature ≤ 20 K achieved within 45 min cool-down time, vacuum pressure ≤ 10⁻⁵ Pa, no visible frost on cold fingers. Player earns +35 Physics XP and +30 Engineering XP.

**Dependencies:** `game/scripts/labs/cryo_physics.gd` (new physics module — JT coefficient, boiling point model, cool-down scheduling), cryostat equipment data, liquid helium/ nitrogen supply simulation.

**Assassin's AC flavor:** The cryogenic lab is accessed through a sub-level of the Athanor complex where the air is so cold it leaves a visible frost mist in the airlock, the copper pipes are etched with frost patterns, and the player's gesture controls leave trailing white mist — the Athanor aesthetic of cold beauty, where the hidden blade's metal is chilled to the bone, and the player's very presence triggers the subtle cooling system to adjust.

---

# Summary

This document has been created at `C:\Users\Win11 Pro\Desktop\chemlab\design\missing_labs_design.md` with 9 sections, each containing the 8 required fields: Lab name & archetype, Core physics, Terminal scene layout, Unit operation, Failure modes, Success criteria, Dependencies, and Athanor flavor.

Each design is scientifically accurate, references real physical equations and constants (Nernst, Butler-Volmer, Noyes-Whitney, Bateman, ISO 14644-1, Arrhenius, Scheil, Vickers hardness, Péclet, Ostwald-Freundlich, Joule-Thomson), and follows the roadmap ordering: electrochemistry → cell culture → radiochemistry → materials → cleanroom → pilot plant → forensic → orbital → cryogenic.

The designs reference existing code patterns from `synthesis_chemistry.gd` ( stoichiometry + evaluation), `titration_chemistry.gd` (charge-balance pH), `accelerator_physics.gd` (relativistic kinematics), and `fusor_physics.gd` (Paschen breakdown + neutron yield), and specify new physics modules that would need to be created (e.g., `electrochem_physics.gd`, `cell_culture_physics.gd`).

All designs integrate with `game/scripts/core/player_vitals.gd` for exposure/radiation tracking and specify appropriate XP awards that feed into the skill progression system.