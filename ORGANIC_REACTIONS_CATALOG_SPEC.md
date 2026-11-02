# Organic Reactions Catalog — Simulation Specification (100+ Named Reactions)

## 1. Purpose
Catalog of 100+ named organic reactions for ChemLab's free-simulation mode, each with
reactants, products, mechanism class, conditions, catalysts, byproducts, and simulation
metadata (color change, gas evolution, heat, precipitate).

## 2. Data Model

```python
from dataclasses import dataclass, field
from enum import Enum

class MechanismClass(Enum):
    SUBSTITUTION = "SN"
    ELIMINATION = "E"
    ADDITION = "ADD"
    CONDENSATION = "COND"
    OXIDATION = "OX"
    REDUCTION = "RED"
    REARRANGEMENT = "REARR"
    COUPLING = "COUP"
    CYCLOADDITION = "CYCLO"
    PERICYCLIC = "PERI"
    NAMED_REARRANGEMENT = "NAMED"

class EnergyProfile(Enum):
    EXOTHERMIC = "exothermic"
    ENDOTHERMIC = "endothermic"
    THERMONEUTRAL = "thermoneutral"

@dataclass
class OrganicReaction:
    id: str                       # snake_case unique key
    name: str                     # IUPAC/common name
    reaction_class: str            # e.g. "esterification"
    mechanism: MechanismClass
    reactants: tuple[str, ...]    # reagent ids from Reagent catalog
    products: tuple[str, ...]
    byproducts: tuple[str, ...]
    conditions: str               # T, P, solvent
    catalyst: str | None
    energy: EnergyProfile
    delta_h_kj_per_mol: float | None
    observable: dict              # color_change, gas, heat, precipitate, foam
    smarts: str | None            # reaction SMILES/SMARTS pattern
    animation: str                # simulation animation key
    hazards: tuple[str, ...] = ()
```

## 3. Conditions & Catalysts (standard tokens)

| Token | Meaning |
|---|---|
| `reflux` | reflux at solvent bp |
| `rt` | room temperature |
| `ice` | 0-5 C |
| `heat` | >100 C |
| `hv` | UV light |
| `acid_cat` | H2SO4/HCl |
| `base_cat` | NaOH/KOH |
| `Pd/C` | palladium on carbon |
| `Ni` | Raney Ni |
| `Pt` | PtO2 |
| `Zn/Hg` | Clemmensen |
| `AlCl3` | Friedel-Crafts Lewis acid |
| `FeBr3` | halogenation catalyst |
| `Grubbs` | Grubbs catalyst |
| `Pd(PPh3)4` | Suzuki/Pd(0) |

## 4. Reaction Catalog (100+)

Each entry: `id | name | reactants -> products + byproducts | conditions | catalyst`.

1. fischer_esterification | Fischer Esterification | RCOOH + R'OH -> RCOOR' + H2O | reflux | acid_cat
2. saponification | Saponification | RCOOR' + NaOH -> RCOONa + R'OH | reflux | base_cat
3. grignard_addition | Grignard Addition | RMgX + carbonyl -> alcohol | ice->rt | none
4. diels_alder | Diels-Alder | diene + dienophile -> cyclohexene | heat | none
5. wittig | Wittig Reaction | phosphonium ylide + carbonyl -> alkene + Ph3P=O | rt | base
6. aldol_condensation | Aldol Condensation | 2 carbonyl -> beta-hydroxy carbonyl / enone | base_cat | NaOH
7. claisen_condensation | Claisen Condensation | 2 esters -> beta-keto ester + EtOH | base_cat | NaOEt
8. cannizzaro | Cannizzaro Reaction | 2 ArCHO -> ArCH2OH + ArCOOH | conc base | NaOH
9. friedel_crafts_alkylation | Friedel-Crafts Alkylation | ArH + RCl -> ArR + HCl | rt | AlCl3
10. friedel_crafts_acylation | Friedel-Crafts Acylation | ArH + RCOCl -> ArCOR + HCl | rt | AlCl3
11. nitration | Nitration | ArH + HNO3 -> ArNO2 + H2O | heat | H2SO4
12. sulfonation | Sulfonation | ArH + H2SO4 -> ArSO3H + H2O | heat | none
13. halogenation_aromatic | Electrophilic Aromatic Halogenation | ArH + X2 -> ArX + HX | rt | FeBr3
14. bromination_alkene | Bromination of Alkene | C=C + Br2 -> vic-dibromide | ice | none
15. hydrohalogenation | Hydrohalogenation | C=C + HX -> alkyl halide | rt | none
16. hydration_alkene | Acid-Catalyzed Hydration | C=C + H2O -> alcohol | heat | acid_cat
17. oxymercuration | Oxymercuration-Demercuration | C=C + H2O -> alcohol (Markovnikov) | rt | Hg(OAc)2/NaBH4
18. hydroboration | Hydroboration-Oxidation | C=C + BH3 then H2O2/OH- -> anti-Markovnikov alcohol | 0 C | none
19. ozonolysis | Ozonolysis | C=C + O3 -> carbonyls | -78 C | Zn/AcOH
20. epoxidation | Epoxidation | C=C + mCPBA -> epoxide | rt | none
21. dihydroxylation | Syn Dihydroxylation | C=C + OsO4 -> vic-diol | rt | NMO
22. wacker_oxidation | Wacker Oxidation | terminal alkene + O2 -> methyl ketone | rt | PdCl2/CuCl
23. heck | Heck Reaction | ArX + alkene -> substituted alkene | heat | Pd(OAc)2
24. suzuki | Suzuki Coupling | ArX + Ar'B(OH)2 -> biaryl | heat | Pd(PPh3)4/base
25. stille | Stille Coupling | ArX + RSnR'3 -> coupled | heat | Pd(0)
26. sonogashira | Sonogashira Coupling | ArX + terminal alkyne -> arylalkyne | rt | Pd/CuI
27. negishi | Negishi Coupling | ArX + RZnX -> coupled | heat | Pd/Ni
28. buchwald_hartwig | Buchwald-Hartwig Amination | ArX + amine -> aniline | heat | Pd/Xantphos
29. mitsunobu | Mitsunobu Reaction | ROH + nucleophile -> inverted product | rt | DEAD/PPh3
30. swern_oxidation | Swern Oxidation | primary/secondary alcohol -> aldehyde/ketone | -78 C | (COCl)2/DMSO
31. pcc_oxidation | PCC Oxidation | alcohol -> aldehyde/ketone | rt | PCC
32. jones_oxidation | Jones Oxidation | alcohol -> carboxylic acid/ketone | 0 C | CrO3/H2SO4
33. dess_martin | Dess-Martin Oxidation | alcohol -> aldehyde/ketone | rt | DMP
34. na_borohydride | NaBH4 Reduction | carbonyl -> alcohol | rt | none
35. li_al_hydride | LiAlH4 Reduction | carbonyl/ester/acid -> alcohol | 0 C | none
36. catalytic_hydrogenation | Catalytic Hydrogenation | C=C/C=O -> saturated | rt | Pd/C,H2
37. clemmensen | Clemmensen Reduction | carbonyl -> CH2 | reflux | Zn/Hg,HCl
38. wolff_kishner | Wolff-Kishner Reduction | carbonyl -> CH2 | heat | NH2NH2,KOH
39. birch_reduction | Birch Reduction | aromatic -> 1,4-cyclohexadiene | -78 C | Na/NH3
40. dissolving_metal | Dissolving Metal Reduction | alkyne -> trans-alkene | -78 C | Na/NH3
41. pinacol_rearrangement | Pinacol Rearrangement | vic-diol -> carbonyl | acid | H2SO4
42. beckmann | Beckmann Rearrangement | oxime -> amide | acid | H2SO4
43. curtius | Curtius Rearrangement | acyl azide -> isocyanate | heat | none
44. hofmann_rearrangement | Hofmann Rearrangement | primary amide -> amine + CO2 | base/halogen | Br2/NaOH
45. lossen | Lossen Rearrangement | hydroxamic acid -> isocyanate | base | none
46. favorskii | Favorskii Rearrangement | alpha-haloketone -> acid | base | NaOH
47. wagner_meerwein | Wagner-Meerwein Rearrangement | carbocation -> rearranged carbocation | acid | none
48. semipinacol | Semipinacol Rearrangement | beta-hydroxy carbocation -> carbonyl | Lewis acid | none
49. mannich | Mannich Reaction | amine + formaldehyde + ketone -> beta-amino carbonyl | acid | none
50. michael_addition | Michael Addition | nucleophile + alpha,beta-unsaturated carbonyl | base | none
51. robinson_annulation | Robinson Annulation | ketone + MVK -> cyclohexenone | base | none
52. knoevenagel | Knoevenagel Condensation | carbonyl + active methylene -> alkene | base | piperidine
53. horner_wadsworth_emmons | HWE Reaction | phosphonate + carbonyl -> E-alkene | base | NaH
54. petasis | Petasis Reaction | amine + formaldehyde + vinyl boronic acid -> allylamine | rt | none
55. reductive_amination | Reductive Amination | carbonyl + amine -> amine | rt | NaBH3CN
56. amide_coupling | Amide Coupling | acid + amine -> amide | rt | DCC/EDC
57. schotten_baumann | Schotten-Baumann | acid chloride + amine -> amide | base aq | NaOH
58. hofmann_elimination | Hofmann Elimination | quaternary ammonium salt -> least substituted alkene | heat | base
59. e2_elimination | E2 Elimination | alkyl halide + base -> alkene | heat | strong base
60. e1_elimination | E1 Elimination | tertiary alkyl halide -> alkene | heat | none
61. dehydrohalogenation | Dehydrohalogenation | alkyl halide -> alkene | base/heat | KOH
62. dehydration_alcohol | Dehydration of Alcohol | alcohol -> alkene | heat | acid_cat
63. dehydrogenation | Dehydrogenation | alkane -> alkene + H2 | heat | Pt/Ni
64. decarboxylation | Decarboxylation | beta-keto acid -> ketone + CO2 | heat | none
65. hunsdiecker | Hunsdiecker Reaction | silver carboxylate + Br2 -> alkyl bromide + CO2 | heat | none
66. kolbe_electrolysis | Kolbe Electrolysis | carboxylate -> alkane + CO2 | electrolysis | none
67. barton_mccombie | Barton-McCombie Deoxygenation | alcohol -> deoxygenated | rt | Bu3SnH
68. barton_decarboxylation | Barton Decarboxylation | thiohydroxamate ester -> radical | heat | none
69. barton_kellogg | Barton-Kellogg Olefination | thioketone + diazo -> alkene | heat | none
70. corey_house | Corey-House Synthesis | organocuprate + alkyl halide -> coupled | rt | none
71. gilman | Gilman Reagent Coupling | R2CuLi + RX -> R-R' | rt | none
72. wurtz | Wurtz Coupling | 2 RX + Na -> R-R | heat | Na
73. ullmann | Ullmann Coupling | 2 ArX + Cu -> biaryl | heat | Cu
74. glaser | Glaser Coupling | 2 terminal alkynes + Cu -> diyne | rt | Cu/O2
75. eglington | Eglinton Coupling | terminal alkyne + Cu(OAc)2 -> diyne | rt | none
76. hay | Hay Coupling | terminal alkyne -> diyne | rt | CuI/TMEDA
77. castro_stephens | Castro-Stephens Coupling | Cu acetylide + ArX -> arylalkyne | heat | none
78. rosenmund_von_braun | Rosenmund-von Braun | ArX + CuCN -> ArCN | heat | CuCN
79. sandmeyer | Sandmeyer Reaction | diazonium + CuX -> ArX | rt | CuX
80. diazotization | Diazotization | ArNH2 + NaNO2/HCl -> diazonium | 0-5 C | none
81. azo_coupling | Azo Coupling | diazonium + phenol/aniline -> azo dye | 0-5 C | none
82. schiemann | Schiemann Reaction | diazonium + HBF4 -> ArF | heat | none
83. pschorr | Pschorr Cyclization | diazonium -> phenanthrene | Cu | none
84. gattermann_koch | Gattermann-Koch Formylation | ArH + CO/HCl -> ArCHO | heat | AlCl3/CuCl
85. vilsmeier_haack | Vilsmeier-Haack Formylation | activated arene + POCl3/DMF -> aldehyde | 0-rt | POCl3
86. reimer_tiemann | Reimer-Tiemann Formylation | phenol + CHCl3/base -> salicylaldehyde | heat | NaOH
87. kolbe_schmitt | Kolbe-Schmitt | phenol + CO2/base -> salicylic acid | heat/pressure | NaOH
88. claisen_rearrangement | Claisen Rearrangement | allyl vinyl ether -> gamma,delta-unsaturated carbonyl | heat | none
89. cope | Cope Rearrangement | 1,5-diene -> isomeric 1,5-diene | heat | none
90. oxy_cope | Oxy-Cope Rearrangement | 1,5-diene-3-ol -> enol -> ketone | heat | none
91. anionic_oxy_cope | Anionic Oxy-Cope | 1,5-diene-3-ol (deprotonated) -> delta,delta-unsat carbonyl | rt | base
92. carroll_rearrangement | Carroll Rearrangement | allyl beta-keto ester -> gamma,delta-unsat ketone + CO2 | heat | none
93. fischer_indole | Fischer Indole Synthesis | phenylhydrazone -> indole | acid/heat | ZnCl2
94. bischler_napieralski | Bischler-Napieralski | beta-phenethylamide -> dihydroisoquinoline | heat | POCl3
95. pictet_spengler | Pictet-Spengler | tryptamine + aldehyde -> tetrahydroisoquinoline | acid | none
96. paal_knorr | Paal-Knorr | 1,4-dicarbonyl -> pyrrole/furan/thiophene | heat | acid
97. hantzsch_pyridine | Hantzsch Pyridine Synthesis | beta-keto ester + aldehyde + ammonia -> dihydropyridine | heat | NH3
98. biginelli | Biginelli Reaction | aldehyde + urea + beta-keto ester -> dihydropyrimidinone | acid/heat | HCl
99. ugi | Ugi Reaction | amine + aldehyde + acid + isocyanide -> bis-amide | rt | none
100. passerini | Passerini Reaction | carbonyl + acid + isocyanide -> alpha-acyloxy amide | rt | none
101. diels_alder_hetero | Hetero-Diels-Alder | diene + carbonyl imine -> heterocycle | heat | Lewis acid
102. ene_reaction | Ene Reaction | alkene with allylic H + enophile -> homoallylic product | heat | Lewis acid
103. prins | Prins Reaction | alkene + formaldehyde -> 1,3-diol/dioxane | acid | none
104. sakurai | Sakurai (Allylation) | allylsilane + carbonyl -> homoallylic alcohol | Lewis acid | TiCl4
105. mukaiyama_aldol | Mukaiyama Aldol | silyl enol ether + carbonyl -> beta-hydroxy carbonyl | Lewis acid | TiCl4
106. peterson | Peterson Olefination | beta-hydroxysilane -> alkene | base/acid | none
107. tebbe | Tebbe Olefination | carbonyl + Tebbe reagent -> alkene | 0 C | none
108. julia | Julia Olefination | phenylsulfone + carbonyl -> alkene | base | NaH
109. corey_fuchs | Corey-Fuchs | aldehyde -> terminal alkyne | base | CBr4/PPh3
110. seymour_carpenter | Seyferth-Gilbert Homologation | aldehyde -> terminal alkyne | base | none

## 5. Observable Mapping (simulation)

```python
OBSERVABLES = {
  "esterification": {"color": "none", "gas": None, "heat": "exothermic_mild", "precipitate": None},
  "grignard": {"color": "cloudy", "gas": None, "heat": "exothermic", "precipitate": "Mg salts"},
  "diels_alder": {"color": "none", "gas": None, "heat": "exothermic", "precipitate": None},
  "wittig": {"color": "yellow->clear", "gas": None, "heat": "exothermic", "precipitate": "Ph3P=O"},
  "aldol": {"color": "yellow", "gas": None, "heat": "exothermic", "precipitate": None},
  "nitration": {"color": "yellow", "gas": "NO2", "heat": "exothermic", "precipitate": None},
  "halogenation": {"color": "brown->clear", "gas": "HX", "heat": "exothermic", "precipitate": None},
  "ozonolysis": {"color": "blue", "gas": "O3", "heat": "exothermic", "precipitate": None},
  "amide_coupling": {"color": "none", "gas": None, "heat": "exothermic", "precipitate": "DCU"},
}
```

## 6. Integration
- Register each reaction in `simulation/catalog.py` REACTION_CATALOG keyed by id.
- Simulation engine resolves reactant reagent ids, validates stoichiometry, applies conditions, animates observable.
- Story mode quests reference reaction ids (e.g. level 5 gold rain = `precipitation_pbI2`).

## 7. Validation
- Unit tests in `tests/test_organic_reactions.py`: parse all 110 entries, assert unique ids, valid reagent refs, non-empty byproducts where applicable.
- Type-check with mypy; lint with ruff.
