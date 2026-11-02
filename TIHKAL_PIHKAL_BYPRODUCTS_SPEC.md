# Technical Specification: Byproducts, Impurities & Side-Reaction Pathways in TiHKAL/PiHKAL Syntheses (Non-Optimal Conditions)

**Scope:** Phenethylamine (PiHKAL) and tryptamine (TiHKAL) synthetic routes. Focus on deviation from optimal conditions, resulting impurity profiles, side-reaction mechanisms, and purification bottlenecks.

---

## 1. Route Taxonomy & Canonical Reaction Schemes

### 1.1 Reductive Amination (most common PiHKAL route)
```
Ar-CHO + R-NH2  --[NaBH3CN or NaBH4, AcOH, MeOH]--> Ar-CH2-NHR  (secondary amine)
Ar-CHO + NH3    --[NaBH3CN]--> Ar-CH2-NH2  (primary amine, e.g. mescaline precursors)
```
**Optimal:** pH 4-6, 1.1 eq amine, 1.5 eq reductant, 0-25°C, 2-12 h.

### 1.2 Nitroalkene Route
```
Ar-CHO + R-NO2  --[NH4OAc, AcOH, reflux]--> Ar-CH=CH-NO2  (nitroalkene, Henry/Knoevenagel)
Ar-CH=CH-NO2  --[LiAlH4 or BH3·THF]--> Ar-CH2-CH2-NH2  (phenethylamine)
```

### 1.3 Leuckart-Wallach
```
Ar-CO-R + HCOONH4  --[150-180°C]--> Ar-CH(NHCHO)-R  --[HCl, reflux]--> Ar-CH(NH2)-R
```

### 1.4 Fischer Indole (tryptamines, TiHKAL)
```
Ar-NHNH2 + R-CO-CH2-R'  --[polyphosphoric acid or ZnCl2, heat]--> indole
```
Followed by: Mannich-type or direct alkylation to tryptamine.

### 1.5 Tryptamine N,N-Dialkylation
```
Tryptamine + 2 R-X  --[K2CO3, DMF]--> N,N-dialkyltryptamine (DMT, DET, DPT, etc.)
```

---

## 2. Byproduct Catalog by Route

### 2.1 Reductive Amination Byproducts

| # | Byproduct | Formation Condition | Structure (SMILES-ish) | Detection |
|---|-----------|---------------------|----------------------|-----------|
| RA-1 | **Over-alkylated tertiary amine** | Excess aldehyde (>1.5 eq), high temp, long reaction | Ar-CH2-N(CH2Ar)2 | GC-MS M+28, TLC less polar |
| RA-2 | **Aldol condensation product** | Basic conditions, enolizable aldehyde, no amine present | Ar-CH=CH-CHO dimer (cinnamaldehyde-type) | UV 300nm, yellow color |
| RA-3 | **Benzyl alcohol (reduction)** | NaBH4 instead of NaBH3CN; pH > 7 | Ar-CH2OH | GC-MS, IR OH stretch |
| RA-4 | **N-formyl derivative** | Formic acid solvent + heat (Leuckart contamination) | Ar-CH2-NH-CHO | MS M+28, NMR formyl H 8.0ppm |
| RA-5 | **Oxazolidine/amine acetal** | Aldehyde + amino alcohol (e.g. ephedrine-derived) | cyclic hemiaminal | NMR, mass spec |
| RA-6 | **Azomethine (imine) dimer** | Dehydrating conditions, no reductant | Ar-CH=N-CH2-Ar | MS, yellow oil |
| RA-7 | **Reductive coupling (pinacol)** | Zn/HCl or low-valent Ti conditions | Ar-CH(OH)-CH(OH)-Ar | TLC, MS |
| RA-8 | **N-oxide** | Air oxidation of tertiary amine product during workup | Ar-CH2-N+(O-)(R)2 | MS M+16 |

**Side-reaction pathway (over-alkylation):**
```
Ar-CHO + R2NH  ->[imine]  Ar-CH=N+R2  ->[NaBH3CN]  Ar-CH2-NR2   (desired secondary)
Ar-CH2-NR2 + Ar-CHO  ->[imine]  Ar-CH=N+(R)(CH2Ar)  ->[NaBH3CN]  Ar-CH2-N(R)(CH2Ar)  (tertiary, undesired)
```
**Mitigation:** Use 2-3 eq amine, add aldehyde slowly, keep temp ≤ 0°C for imine formation, use NaBH3CN (selective for iminium, not aldehyde).

### 2.2 Nitroalkene Route Byproducts

| # | Byproduct | Formation Condition | Notes |
|---|-----------|---------------------|-------|
| NA-1 | **Nitroalkane (Henry adduct, unreduced)** | Incomplete reduction, low LiAlH4 eq | Ar-CH2-CH2-NO2; MS M+45 vs amine |
| NA-2 | **Hydroxylamine** | Partial reduction (1 eq LAH) | Ar-CH2-CH2-NHOH; oxidizes to nitroso |
| NA-3 | **Nitroso dimer (azoxy)** | LAH quench with water, basic pH | Ar-CH2-CH2-N=N(O)-CH2CH2-Ar |
| NA-4 | **Aldoxime** | Nitroalkene + reducing agent (nitro → oxime) | Ar-CH2-CH=NOH; hydrolyzes to ketone |
| NA-5 | **Saturated ketone (hydrolysis of oxime)** | Acidic workup of oxime impurity | Ar-CO-CH3 (phenylacetone analog) |
| NA-6 | **Nitroalkene E/Z isomers** | Thermodynamic control in condensation | E-isomer desired; Z-isomer reduces slower |
| NA-7 | **Bis-nitro adduct (Michael addition)** | Excess nitromethane, base catalysis | Ar-CH(NO2)-CH2-CH(NO2)-Ar (dimer) |
| NA-8 | **Over-reduction to alcohol** | BH3 excess, high temp | Ar-CH2-CH2-OH (phenethyl alcohol analog) |

**Critical side reaction — nitro reduction stoichiometry:**
```
R-NO2  --[4e-, 4H+]--> R-NHOH  (hydroxylamine, stable if quenched early)
R-NHOH --[2e-, 2H+]--> R-NH2   (desired)
R-NHOH + R-NO2  ->  R-N=N(O)-R  (azoxy, if mixing nitro + hydroxylamine)
```
**Mitigation:** Use ≥4 eq LAH, slow addition of nitroalkene to LAH (not reverse), quench with saturated Na2SO4 (not water), keep anhydrous.

### 2.3 Leuckart-Wallach Byproducts

| # | Byproduct | Condition | Notes |
|---|-----------|-----------|-------|
| LW-1 | **N-formyl amine (unhydrolyzed)** | Insufficient HCl reflux, short time | Ar-CH(NHCHO)-R; bp differs, separable by distillation |
| LW-2 | **Diformyl derivative** | Excess formic acid, high temp | Ar-CH(N(CHO)2)-R |
| LW-3 | **Alcohol (ketone reduction)** | Formic acid as reductant (Meerwein-Ponndorf) | Ar-CH(OH)-R |
| LW-4 | **Aldol condensation of ketone** | Basic ammonium formate, prolonged heating | α,β-unsaturated ketone |
| LW-5 | **Enamine** | Dehydration of amine + ketone | cyclic enamine if cyclic ketone |

### 2.4 Fischer Indole Byproducts (Tryptamines)

| # | Byproduct | Condition | Notes |
|---|-----------|-----------|-------|
| FI-1 | **Regioisomeric indole** | Unsymmetrical ketone (e.g. 2-butanone) | 2- vs 3-substituted indole; separable by chromatography |
| FI-2 | **Bis-indole (2,2'-coupling)** | Excess indole, oxidizing conditions | Dark polymer, low yield |
| FI-3 | **Aniline (cleavage product)** | Strong acid, high temp, hydrazine decomposition | Ar-NH2; volatile, removed by distillation |
| FI-4 | **Indolenine (3H-indole)** | Kinetic product, low temp | Tautomerizes to indole; may trap if quenched cold |
| FI-5 | **Polymeric tar** | Overheating PPA, >180°C | Intractable; reduces yield dramatically |
| FI-6 | **Carbazole (if N-aryl hydrazine)** | Acid-catalyzed rearrangement | Fused ring byproduct |

**Fischer indole mechanism with side branches:**
```
Ar-NHNH2 + R-CO-CH2R'  ->[acid]  hydrazone
hydrazone  ->[3,3-sigmatropic]  enamine intermediate
enamine  ->  indolenine  ->[tautomerization]  indole (desired)
   |->[if R≠R']  regioisomer A or B (kinetic vs thermodynamic)
   |->[if oxidant present]  bis-indole (oxidative coupling)
   |->[if T>180°C]  tar (polymerization)
```

### 2.5 Tryptamine Alkylation Byproducts

| # | Byproduct | Condition | Notes |
|---|-----------|-----------|-------|
| TA-1 | **N-monoalkyl (incomplete)** | <2 eq alkyl halide, short time | Tryptamine → N-methyltryptamine |
| TA-2 | **Quaternary ammonium salt** | >2 eq alkyl halide, heat, polar solvent | Water-soluble, lost in aqueous workup |
| TA-3 | **O-alkylated phenol (if 5-OH-DMT route)** | Phenolic OH present, base | 5-methoxy → 5-alkoxy impurity |
| TA-4 | **N-oxide (tryptamine)** | Air exposure during basic workup | MS M+16, polar |
| TA-5 | **Dehydrogenated (indolenine)** | Oxidizing conditions | Loss of 2H, MS M-2 |
| TA-6 | **Rearrangement (spiro compound)** | Acidic conditions, heat | Spiro[indoline-3,2'-...] |

---

## 3. Cross-Cutting Impurities

### 3.1 Starting Material Residues
- Unreacted aldehyde/ketone (often co-elutes with product on silica)
- Residual nitromethane (bp 101°C, volatile but toxic)
- Hydrazine (toxic, removed by aqueous wash; forms hydrazones with carbonyls)

### 3.2 Reagent-Derived Impurities
- **Boron residues** (from BH3 or NaBH4): form borate esters with product amines; removed by MeOH quench + HCl wash
- **Aluminum residues** (from LAH): form Al-amine complexes; removed by Fieser workup (Na2SO4·10H2O)
- **Palladium** (if catalytic hydrogenation): must be filtered through Celite; residual Pd causes product discoloration
- **Formic acid** (Leuckart): N-formyl byproduct; hydrolyzed with 6M HCl reflux

### 3.3 Solvent-Derived Impurities
- **DMF decomposition** → dimethylamine (contaminates amine product, gives N,N-dimethyl byproduct)
- **DMSO decomposition** at high temp → methylsulfide byproducts
- **Ether peroxides** (old THF/ether): oxidize amines to N-oxides

### 3.4 Degradation Products
- **Oxidative deamination** of primary/secondary amines → aldehyde + NH3 (air, Cu catalysis)
- **Photochemical degradation** of tryptamines → indolenine/oxidation products (UV light)
- **Thermal decomposition** of phenethylamines at >200°C → styrene derivatives

---

## 4. Purification Challenges & Strategies

### 4.1 Amine Salt Formation (Standard First Purification)
```
R-NH2 (free base, oil)  +  HCl (g or conc. aq)  ->  R-NH3+ Cl- (crystalline salt)
```
**Challenge:** Many phenethylamine HCl salts are hygroscopic; some tryptamine salts are oils. Recrystallization solvents: IPA/Et2O, MeOH/Et2O, acetone.

### 4.2 Chromatographic Separation

| Technique | Application | Challenge |
|-----------|-------------|-----------|
| Silica gel (normal phase) | Free base amines | Tailing due to amine-silica interaction; add 1-2% Et3N or NH4OH to eluent |
| Alumina (basic) | Amine products | Less tailing; may cause decomposition of acid-labile groups |
| Reverse phase C18 | Polar impurities | Good for separating N-oxides; expensive for scale |
| Ion exchange (Dowex) | Amine purification | Excellent for removing neutral impurities; requires salt formation |

**Eluent systems (phenethylamines):**
- Hexane/EtOAc/Et3N (70:25:5) — standard
- CH2Cl2/MeOH/NH4OH (90:9:1) — for polar amines
- Toluene/acetone/Et3N (60:35:5) — for tryptamines

### 4.3 Distillation
- **Challenge:** Many phenethylamines have bp >200°C at atm; require high vacuum (<1 mmHg)
- **Decomposition risk:** Amines can undergo elimination at high temp
- **Solution:** Kugelrohr distillation, or convert to salt and recrystallize

### 4.4 Recrystallization Decision Tree
```
Product is solid salt?
  YES -> Recrystallize from IPA/Et2O or MeOH/acetone
  NO (oil) -> 
    Is it a free base oil?
      YES -> Convert to HCl or oxalate salt, then recrystallize
      NO (resin) -> Chromatography first, then salt formation
```

### 4.5 Common Purification Failures

| Symptom | Cause | Solution |
|---------|-------|----------|
| Product oils out during recrystallization | Too much solvent, wrong solvent pair | Add anti-solvent slowly, seed crystal |
| Streaking on TLC | Amine tailing | Add Et3N to eluent; use alumina plates |
| Multiple spots with same Rf | Regioisomers or conformers | Use different solvent system; check by NMR |
| Product darkens on storage | Oxidation (tryptamines) | Store under Ar, -20°C, dark |
| Low recovery from column | Amine adsorbed to silica | Pre-treat silica with Et3N; use basic alumina |

---

## 5. Analytical Identification of Impurities

### 5.1 GC-MS Diagnostic Ions

| Impurity Type | Characteristic Fragment | m/z |
|---------------|------------------------|-----|
| Primary phenethylamine | [M-30]+ (loss of NH2CH2) | M-30 |
| Secondary amine (N-methyl) | [M-44]+ or [M-15]+ | M-44 / M-15 |
| Tertiary amine | [M-58]+ (loss of NMe2CH2) | M-58 |
| N-oxide | [M-16]+ (loss of O) | M-16 |
| Nitroalkane | [M-46]+ (loss of NO2) | M-46 |
| Oxime | [M-17]+ (loss of OH) | M-17 |

### 5.2 NMR Diagnostic Signals

| Impurity | ¹H NMR Signal | Chemical Shift (ppm) |
|----------|---------------|----------------------|
| N-formyl | Formyl H (s, 1H) | 7.9-8.2 |
| Aldol condensation | Vinylic H (d, J=16Hz) | 6.5-7.5 |
| Benzyl alcohol | CH2OH (s, 2H) | 4.5-4.7 |
| Oxime | =N-OH (broad s, 1H) | 9-11 |
| N-oxide | N-CH3 downfield shift | +0.3-0.5 ppm vs amine |
| Quaternary ammonium | N+(CH3)3 | 3.0-3.2 (sharp singlet) |

### 5.3 HPLC Method (General)
```
Column: C18, 5µm, 250×4.6mm
Mobile phase: A = 0.1% TFA in H2O, B = 0.1% TFA in MeCN
Gradient: 5% B → 95% B over 20 min
Flow: 1.0 mL/min
Detection: UV 254nm (phenethylamines), 280nm (tryptamines)
```

---

## 6. Data Structure: Impurity Record Schema

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

class Route(Enum):
    REDUCTIVE_AMINATION = "reductive_amination"
    NITROALKENE = "nitroalkene"
    LEUCKART_WALLACH = "leuckart_wallach"
    FISCHER_INDOLE = "fischer_indole"
    ALKYLATION = "alkylation"

class Severity(Enum):
    CRITICAL = "critical"   # Toxic, must remove
    MAJOR = "major"         # Affects purity >1%
    MINOR = "minor"         # Trace, <0.1%

@dataclass
class Impurity:
    code: str                          # e.g. "RA-1"
    name: str                          # e.g. "Over-alkylated tertiary amine"
    route: Route
    formation_condition: str            # deviation from optimal
    mechanism: str                     # reaction equation
    severity: Severity
    detection_methods: List[str]        # ["GC-MS", "TLC", "NMR"]
    diagnostic: str                    # characteristic signal
    purification: str                  # removal strategy
    mitigation: Optional[str] = None    # prevention strategy

@dataclass
class PurificationStep:
    name: str
    technique: str                     # "crystallization", "chromatography", "distillation"
    solvent_system: str
    expected_recovery: float            # 0.0-1.0
    impurities_removed: List[str]       # codes
    impurities_remaining: List[str]     # codes
    notes: str = ""

@dataclass
class SynthesisProfile:
    target: str                        # compound name
    route: Route
    optimal_conditions: dict
    actual_conditions: dict
    impurities: List[Impurity] = field(default_factory=list)
    purification_steps: List[PurificationStep] = field(default_factory=list)
    final_purity: Optional[float] = None
```

---

## 7. Code Pattern: Impurity Prediction Engine

```python
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum

class Route(Enum):
    REDUCTIVE_AMINATION = "ra"
    NITROALKENE = "na"
    LEUCKART_WALLACH = "lw"
    FISCHER_INDOLE = "fi"
    ALKYLATION = "ta"

# Condition deviation thresholds
DEVIATION_RULES = {
    Route.REDUCTIVE_AMINATION: [
        ("amine_eq", "<", 1.5, ["RA-1"]),       # low amine -> over-alkylation
        ("temp_c", ">", 25, ["RA-1", "RA-6"]),  # high temp -> imine dimer
        ("reductant", "==", "NaBH4", ["RA-3"]), # wrong reductant -> alcohol
        ("ph", ">", 7, ["RA-3", "RA-6"]),       # high pH -> reduction of aldehyde
        ("time_h", ">", 24, ["RA-8"]),          # long time -> N-oxide
    ],
    Route.NITROALKENE: [
        ("lah_eq", "<", 4.0, ["NA-1", "NA-2", "NA-3"]),  # insufficient LAH
        ("addition_order", "==", "reverse", ["NA-3"]),     # wrong addition -> azoxy
        ("quench", "==", "water", ["NA-3"]),                # water quench -> azoxy
        ("temp_c", ">", 50, ["NA-8"]),                     # high temp -> over-reduction
        ("nitromethane_eq", ">", 3.0, ["NA-7"]),           # excess nitromethane -> dimer
    ],
    Route.FISCHER_INDOLE: [
        ("temp_c", ">", 180, ["FI-5"]),          # overheating -> tar
        ("ketone_symmetry", "==", "unsym", ["FI-1"]),  # unsym ketone -> regioisomer
        ("oxidant_present", "==", True, ["FI-2"]), # oxidant -> bis-indole
        ("acid_strength", "==", "strong", ["FI-3", "FI-6"]),  # strong acid -> cleavage
    ],
    Route.ALKYLATION: [
        ("alkyl_halide_eq", ">", 2.2, ["TA-2"]),   # excess -> quaternary
        ("alkyl_halide_eq", "<", 1.8, ["TA-1"]),   # insufficient -> mono
        ("phenol_present", "==", True, ["TA-3"]),   # phenolic OH -> O-alkylation
        ("atmosphere", "==", "air", ["TA-4"]),      # air -> N-oxide
    ],
}

def predict_impurities(route: Route, conditions: Dict) -> List[str]:
    """Given a route and actual conditions, return list of likely impurity codes."""
    impurities = set()
    for param, op, threshold, codes in DEVIATION_RULES.get(route, []):
        val = conditions.get(param)
        if val is None:
            continue
        triggered = False
        if op == "<" and val < threshold:
            triggered = True
        elif op == ">" and val > threshold:
            triggered = True
        elif op == "==" and val == threshold:
            triggered = True
        if triggered:
            impurities.update(codes)
    return sorted(impurities)

# Example usage:
# conditions = {"amine_eq": 1.2, "temp_c": 40, "reductant": "NaBH3CN", "ph": 5.0, "time_h": 6}
# predict_impurities(Route.REDUCTIVE_AMINATION, conditions) -> ['RA-1']
```

---

## 8. Purification Workflow (Standard Operating Procedure)

### Step 1: Quench & Workup
```
Reaction mixture -> quench (ice/water or sat. Na2SO4 for LAH)
-> extract with organic solvent (Et2O or CH2Cl2, 3x)
-> wash organic layer: 1M HCl (removes unreacted amine starting materials)
-> wash: sat. NaHCO3 (neutralize)
-> wash: brine
-> dry (MgSO4 or Na2SO4)
-> concentrate in vacuo (keep bath <40°C for tryptamines)
```

### Step 2: Salt Formation
```
Dissolve crude free base in minimal IPA or Et2O
-> bubble dry HCl gas OR add conc. HCl (1.1 eq) dropwise
-> cool to 0°C, filter precipitate
-> wash with cold Et2O
-> dry under vacuum
```

### Step 3: Recrystallization
```
Dissolve salt in hot solvent (IPA or MeOH)
-> add anti-solvent (Et2O or acetone) until cloudy
-> cool slowly to rt, then 0°C
-> filter, wash, dry
```

### Step 4: Chromatography (if needed)
```
Pre-treat silica with 2% Et3N in hexane
-> load sample as free base (not salt)
-> elute with gradient (hexane -> EtOAc, with 1% Et3N throughout)
-> collect fractions, check by TLC
-> combine, concentrate
```

### Step 5: Final Quality Control
```
- TLC: single spot, Rf consistent with reference
- GC-MS: molecular ion matches, no impurity peaks >0.5%
- ¹H NMR: no diagnostic impurity signals
- Melting point: sharp, matches literature
- HPLC: purity >98% (area normalization)
```

---

## 9. Safety & Handling Notes

- **Nitromethane** is a high explosive when mixed with base; handle with care
- **LAH** reacts violently with water; use Fieser workup
- **Hydrazine** is carcinogenic; use in fume hood, destroy excess with bleach
- **Tryptamines** are light- and air-sensitive; store under inert atmosphere
- **Phenethylamines** can cause severe vasoconstriction; handle with gloves

---

## 10. References & Further Reading

- Shulgin, A. & Shulgin, A. (1991). *PiHKAL: A Chemical Love Story*. Transform Press.
- Shulgin, A. & Shulgin, A. (1997). *TiHKAL: The Continuation*. Transform Press.
- March, J. (2013). *March's Advanced Organic Chemistry*, 7th ed. Wiley.
- Carey, F.A. & Sundberg, R.J. (2007). *Advanced Organic Chemistry*, Part B. Springer.
- Vogel, A.I. (1989). *Vogel's Textbook of Practical Organic Chemistry*, 5th ed. Longman.

---

*Document version: 1.0 | Generated for ChemLab virtual chemistry lab project*