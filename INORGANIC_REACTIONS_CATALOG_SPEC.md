# Inorganic Reactions Catalog — Simulation Specification (50+ Reactions)

## 1. Purpose
Catalog of 50+ inorganic reactions for ChemLab's free-simulation mode: redox, precipitation,
complexation, acid-base. Each entry carries balanced equation, thermodynamic data (ΔH°, ΔG°, K),
conditions, catalysts, byproducts, and simulation metadata (color change, gas evolution, heat,
precipitate, foam, luminescence) plus visual-effect keys.

## 2. Data Model

```python
from dataclasses import dataclass, field
from enum import Enum

class InorganicReactionType(Enum):
    REDOX = "redox"
    PRECIPITATION = "precipitation"
    COMPLEXATION = "complexation"
    ACID_BASE = "acid_base"
    GAS_EVOLUTION = "gas_evolution"
    DISPLACEMENT = "displacement"
    DECOMPOSITION = "decomposition"
    SYNTHESIS = "synthesis"
    HYDROLYSIS = "hydrolysis"

class EnergyProfile(Enum):
    EXOTHERMIC = "exothermic"
    ENDOTHERMIC = "endothermic"
    THERMONEUTRAL = "thermoneutral"

@dataclass
class ThermoData:
    delta_h_kj_per_mol: float | None   # standard enthalpy change
    delta_s_j_per_mol_k: float | None  # standard entropy change
    delta_g_kj_per_mol: float | None   # standard Gibbs free energy
    equilibrium_constant: float | None  # K (unitless or Kc/Ksp as noted)
    k_type: str = "Kc"                 # "Kc","Ksp","Kf","Ka","Kb","Kw"

@dataclass
class VisualEffect:
    color_change: str | None           # e.g. "colorless->yellow"
    gas: str | None                    # gas evolved
    heat: str                          # exothermic_strong | exothermic_mild | endothermic | none
    precipitate: str | None            # solid formed
    foam: bool = False
    luminescence: str | None = None    # wavelength nm if glowing
    particles: str | None = None       # "bubbles","crystals","smoke"
    duration_s: float = 2.0            # animation length

@dataclass
class InorganicReaction:
    id: str
    name: str
    reaction_type: InorganicReactionType
    equation: str                      # balanced molecular equation
    net_ionic: str | None              # net ionic equation
    reactants: tuple[str, ...]
    products: tuple[str, ...]
    byproducts: tuple[str, ...] = ()
    conditions: str = "rt"
    catalyst: str | None = None
    energy: EnergyProfile = EnergyProfile.EXOTHERMIC
    thermo: ThermoData = field(default_factory=lambda: ThermoData(None,None,None,None))
    observable: VisualEffect = field(default_factory=lambda: VisualEffect(None,None,"none",None))
    animation: str = "default_mix"
    hazards: tuple[str, ...] = ()
```

## 3. Conditions & Catalysts (standard tokens)

| Token | Meaning |
|---|---|
| `rt` | room temperature 20-25 C |
| `ice` | 0-5 C |
| `heat` | >100 C / boil |
| `reflux` | reflux at solvent bp |
| `conc` | concentrated reagents |
| `dilute` | dilute aqueous |
| `hv` | UV/visible light |
| `MnO2` | manganese dioxide catalyst |
| `Pt` | Pt catalyst |
| `Fe` | iron catalyst |
| `enzyme` | catalase etc. |

## 4. Reaction Catalog (55)

Format: `id | name | type | equation | ΔH°(kJ/mol) | K | observable`

### 4.1 Acid-Base Neutralization (8)
1. hcl_naoh_neutralization | HCl + NaOH neutralization | acid_base | HCl + NaOH -> NaCl + H2O | -57.3 | 1e14 (Kw^-1) | none; heat exothermic_strong
2. h2so4_naoh_neutralization | H2SO4 + 2NaOH | acid_base | H2SO4 + 2NaOH -> Na2SO4 + 2H2O | -114.6 | 1e14 | heat
3. hno3_koh_neutralization | HNO3 + KOH | acid_base | HNO3 + KOH -> KNO3 + H2O | -57.6 | 1e14 | heat
4. h3po4_naoh_neutralization | H3PO4 + 3NaOH | acid_base | H3PO4 + 3NaOH -> Na3PO4 + 3H2O | -167.2 | 1e14 | heat
5. nh3_hcl_gas | Ammonia + HCl gas | acid_base | NH3 + HCl -> NH4Cl (white smoke) | -176.0 | 1e17 | white smoke; particles smoke
6. co2_naoh_absorption | CO2 + 2NaOH | acid_base | CO2 + 2NaOH -> Na2CO3 + H2O | -109.4 | 1e6 | none
7. h2co3_decomposition | Carbonic acid decomposition | acid_base | H2CO3 -> CO2 + H2O | +19.0 | 1e-7 | bubbles CO2
8. borax_acid | Borax + HCl | acid_base | Na2B4O7 + 2HCl + 5H2O -> 4H3BO3 + 2NaCl | -50.0 | 1e4 | heat

### 4.2 Precipitation (15)
9. pb_no3_ki_yellow | Lead(II) iodide (golden rain) | precipitation | Pb(NO3)2 + 2KI -> PbI2(s) + 2KNO3 | -? Ksp 9.8e-9 | yellow precipitate crystals
10. agno3_nacl_white | Silver chloride | precipitation | AgNO3 + NaCl -> AgCl(s) + NaNO3 | Ksp 1.8e-10 | white precipitate
11. bacl2_naso4_white | Barium sulfate | precipitation | BaCl2 + Na2SO4 -> BaSO4(s) + 2NaCl | Ksp 1.1e-10 | white precipitate
12. cacl2_naco3_white | Calcium carbonate | precipitation | CaCl2 + Na2CO3 -> CaCO3(s) + 2NaCl | Ksp 3.3e-9 | white precipitate
13. fecl3_naoh_brown | Iron(III) hydroxide | precipitation | FeCl3 + 3NaOH -> Fe(OH)3(s) + 3NaCl | Ksp 2.8e-39 | brown precipitate
14. cu_so4_naoh_blue | Copper(II) hydroxide | precipitation | CuSO4 + 2NaOH -> Cu(OH)2(s) + Na2SO4 | Ksp 2.2e-20 | blue precipitate
15. zn_so4_naoh_white | Zinc hydroxide | precipitation | ZnSO4 + 2NaOH -> Zn(OH)2(s) + Na2SO4 | Ksp 3e-17 | white precipitate
16. pb_no3_nai_yellow | Lead(II) iodide (alt) | precipitation | Pb(NO3)2 + 2NaI -> PbI2(s) + 2NaNO3 | Ksp 9.8e-9 | yellow
17. agno3_nh4oh_dissolve | Silver diammine complex (dissolve) | complexation | AgCl + 2NH3 -> [Ag(NH3)2]+ + Cl- | Kf 1.6e7 | clear; crystals dissolve
18. mg_so4_naoh_white | Magnesium hydroxide (milk of magnesia) | precipitation | MgSO4 + 2NaOH -> Mg(OH)2(s) + Na2SO4 | Ksp 5.6e-12 | white milky
19. al2_so4_naoh_gel | Aluminium hydroxide gel | precipitation | Al2(SO4)3 + 6NaOH -> 2Al(OH)3(s) + 3Na2SO4 | Ksp 3e-34 | white gel
20. pb_acetate_ki_yellow | Lead acetate + KI | precipitation | Pb(CH3COO)2 + 2KI -> PbI2(s) + 2KCH3COO | Ksp 9.8e-9 | yellow
21. h2s_cuso4_black | Copper(II) sulfide | precipitation | CuSO4 + H2S -> CuS(s) + H2SO4 | Ksp 6e-36 | black precipitate
22. h2s_pbs_black | Lead(II) sulfide | precipitation | Pb(NO3)2 + H2S -> PbS(s) + 2HNO3 | Ksp 8e-28 | black
23. agno3_k2cro4_red | Silver chromate (red) | precipitation | 2AgNO3 + K2CrO4 -> Ag2CrO4(s) + 2KNO3 | Ksp 1.1e-12 | red precipitate

### 4.3 Redox (16)
24. zn_hcl_hydrogen | Zn + 2HCl | redox | Zn + 2HCl -> ZnCl2 + H2(g) | -153.9 | K 1e25 | bubbles H2; heat
25. fe_cuso4_displacement | Fe + CuSO4 | redox | Fe + CuSO4 -> FeSO4 + Cu(s) | -154.6 | K 1e26 | copper deposits; blue->green
26. cu_agno3_displacement | Cu + 2AgNO3 | redox | Cu + 2AgNO3 -> Cu(NO3)2 + 2Ag(s) | -92.0 | K 1e15 | silver crystals; blue
27. mg_hcl_vigorous | Mg + 2HCl | redox | Mg + 2HCl -> MgCl2 + H2(g) | -466.0 | K 1e40 | vigorous bubbles; heat
28. al_hcl_hydrogen | 2Al + 6HCl | redox | 2Al + 6HCl -> 2AlCl3 + 3H2(g) | -1049 | K 1e60 | vigorous; heat
29. k_permanganate_fe2 | MnO4- + 5Fe2+ + 8H+ | redox | MnO4- + 5Fe2+ + 8H+ -> Mn2+ + 5Fe3+ + 4H2O | ΔH -? | K 1e63 | purple->colorless
30. dichromate_fe2 | Cr2O7^2- + 6Fe2+ + 14H+ | redox | Cr2O7^2- + 6Fe2+ + 14H+ -> 2Cr3+ + 6Fe3+ + 7H2O | -? | K 1e50 | orange->green
31. h2o2_decomposition | 2H2O2 -> 2H2O + O2 | redox | 2H2O2 -> 2H2O + O2(g) | -196.0 | kcat | bubbles O2; MnO2 catalyst
32. h2o2_ki_foam | elephant toothpaste | redox | 2H2O2 --KI--> 2H2O + O2(g) | -196.0 | fast | foam; heat
33. chlorate_decomposition | 2KClO3 -> 2KCl + 3O2 | redox | 2KClO3 -> 2KCl + 3O2(g) | +? (endothermic) | heat/MnO2 | O2 evolution
34. permanganate_oxalate | 2MnO4- + 5C2O4^2- + 16H+ | redox | 2MnO4- + 5C2O4^2- + 16H+ -> 2Mn2+ + 10CO2 + 8H2O | -? | K 1e100 | purple->colorless; CO2
35. iodine_thiosulfate | I2 + 2S2O3^2- | redox | I2 + 2S2O3^2- -> 2I- + S4O6^2- | -? | K 1e? | brown->colorless
36. chlorine_water_disproportionation | Cl2 + H2O | redox | Cl2 + H2O -> HCl + HOCl | -? | K 4e-4 | yellow-green
37. bromine_disproportionation | Br2 + H2O | redox | Br2 + H2O -> HBr + HOBr | -? | K 7e-9 | brown
38. copper_zinc_galvanic | Cu2+ + Zn -> Cu + Zn2+ | redox | Cu2+ + Zn -> Cu(s) + Zn2+ | -212.0 | K 1e37 | voltage; copper plates
39. iron_copper_cell | Fe2+ + Cu2+? no | redox | placeholder: Fe + Cu2+ -> Fe2+ + Cu | -154.6 | K 1e26 | same as 25

### 4.4 Complexation (8)
40. cu_nh3_deep_blue | Cu2+ + 4NH3 | complexation | Cu2+ + 4NH3 -> [Cu(NH3)4]2+ | Kf 2.1e13 | deep blue
41. fe_scn_blood_red | Fe3+ + SCN- | complexation | Fe3+ + SCN- -> [Fe(SCN)]2+ | Kf 1.4e2 | blood red
42. ag_nh3_diammine | Ag+ + 2NH3 | complexation | Ag+ + 2NH3 -> [Ag(NH3)2]+ | Kf 1.6e7 | clear
43. aluminon_lake | Al3+ + aluminon | complexation | Al3+ + aluminon -> red lake | Kf high | red
44. ni_dimethylglyoxime_red | Ni2+ + DMG | complexation | Ni2+ + 2DMG -> Ni(DMG)2(s) + 2H+ | Kf high | red precipitate
45. co_cl4_blue | Co2+ + 4Cl- | complexation | [Co(H2O)6]2+ + 4Cl- -> [CoCl4]2- + 6H2O | Kf 1e-? (temp) | pink->blue; heat
46. fe_salicylate_violet | Fe3+ + salicylate | complexation | Fe3+ + salicylate -> violet complex | Kf 1e? | violet
47. cu_edta_blue | Cu2+ + EDTA | complexation | Cu2+ + EDTA4- -> [Cu(EDTA)]2- | Kf 6.3e18 | blue

### 4.5 Gas Evolution / Decomposition (8)
48. znso4_h2s? no | acid + carbonate | gas_evolution | 2HCl + Na2CO3 -> 2NaCl + H2O + CO2 | -? | bubbles CO2
49. zn_h2so4_hydrogen | Zn + H2SO4 | redox | Zn + H2SO4 -> ZnSO4 + H2(g) | -? | bubbles
50. kclo3_decomp | 2KClO3 -> 2KCl + 3O2 | decomposition | 2KClO3 -> 2KCl + 3O2(g) | endothermic | O2; heat/MnO2
51. nh4cl_heat | NH4Cl -> NH3 + HCl (sublime) | decomposition | NH4Cl(s) -> NH3(g) + HCl(g) | endothermic | white smoke
52. caco3_heat | CaCO3 -> CaO + CO2 | decomposition | CaCO3 -> CaO + CO2(g) | endothermic +178 | CO2
53. h2o2_catalase | 2H2O2 --catalase--> 2H2O + O2 | redox | 2H2O2 -> 2H2O + O2(g) | -196 | bubbles O2
54. zn_acid_nitrate | Zn + 4HNO3 (conc) | redox | Zn + 4HNO3 -> Zn(NO3)2 + 2NO2(g) + 2H2O | -? | brown NO2 gas
55. cu_hno3_conc | Cu + 4HNO3 (conc) | redox | Cu + 4HNO3 -> Cu(NO3)2 + 2NO2(g) + 2H2O | -? | brown NO2; heat
56. cu_hno3_dilute | 3Cu + 8HNO3 (dil) | redox | 3Cu + 8HNO3 -> 3Cu(NO3)2 + 2NO(g) + 4H2O | -? | colorless NO -> brown NO2 in air

## 5. Observable Mapping (simulation)

```python
OBSERVABLES = {
  "neutralization": {"color": "none", "gas": None, "heat": "exothermic_strong", "precipitate": None},
  "golden_rain": {"color": "yellow", "gas": None, "heat": "exothermic_mild", "precipitate": "PbI2", "particles": "crystals"},
  "h2_evolution": {"color": "none", "gas": "H2", "heat": "exothermic", "precipitate": None, "particles": "bubbles"},
  "copper_plating": {"color": "blue->colorless", "gas": None, "heat": "exothermic", "precipitate": "Cu"},
  "permanganate_fade": {"color": "purple->colorless", "gas": None, "heat": "exothermic", "precipitate": None},
  "dichromate_green": {"color": "orange->green", "gas": None, "heat": "exothermic", "precipitate": None},
  "foam_eruption": {"color": "white", "gas": "O2", "heat": "exothermic_strong", "precipitate": None, "foam": True},
  "complex_deep_blue": {"color": "blue", "gas": None, "heat": "none", "precipitate": None},
  "blood_red_complex": {"color": "red", "gas": None, "heat": "none", "precipitate": None},
  "no2_brown_gas": {"color": "brown", "gas": "NO2", "heat": "exothermic", "precipitate": None, "particles": "smoke"},
}
```

## 6. Integration
- Register each reaction in `simulation/catalog.py` INORGANIC_REACTION_CATALOG keyed by id.
- Simulation engine resolves reactant reagent ids, validates stoichiometry, applies conditions, animates observable.
- Thermodynamic data drives temperature change: ΔT = -ΔH·ξ/(Σ n·Cp) (approx).
- Equilibrium constants drive extent of reaction at given concentrations (ICE table).
- Story mode quests reference reaction ids (e.g. level 5 gold rain = `pb_no3_ki_yellow`).

## 7. Validation
- Unit tests in `tests/test_inorganic_reactions.py`: parse all 55 entries, assert unique ids, valid reagent refs, balanced equations, non-null thermo where applicable.
- Type-check with mypy; lint with ruff.
- Verify Ksp/Kf values against CRC Handbook.
