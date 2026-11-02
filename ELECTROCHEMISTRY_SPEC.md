# Electrochemistry Simulation — Galvanic Cells, Electrolysis, Voltammetry & Corrosion

## 1. Scope

Design spec for an electrochemistry subsystem in the ChemLab engine covering:
galvanic (voltaic) cells, electrolysis, cyclic/linear-sweep voltammetry, and
corrosion (galvanic + pitting + Pourbaix). Anchored on the Nernst equation and
Faraday's laws. Calculation-only + visual state; no hardware control.

## 2. Core Equations

### 2.1 Standard electrode potential
E°(cell) = E°(cathode) − E°(anode)   (V vs SHE, 25 °C, 1 bar, unit activity)

### 2.2 Nernst equation (general, 25 °C simplified)
E = E° − (RT / nF) ln Q
  = E° − (0.05916 V / n) log10 Q   (T = 298.15 K)
where Q = a_products / a_reactants (activities; approximate with molarity for
dilute). For half-cell: E = E° − (RT/nF) ln(a_red/a_ox).

### 2.3 Gibbs free energy & equilibrium
ΔG = −n F E_cell
ΔG° = −n F E°_cell = −RT ln K
K = 10^(n E°_cell / 0.05916)

### 2.4 Faraday's laws of electrolysis
m = (M I t) / (n F)          # mass deposited (g)
V_gas = (I t R T)/(n F P)     # gas volume (m³) at T,P
n_e = I t / F                # moles of electrons
ξ = I t / (n F)              # extent of reaction (mol)
Current efficiency η = m_actual / m_theoretical.

### 2.5 Cell EMF under load
E_load = E_ocv − I (R_internal + R_external) − η_act − η_conc − η_ohmic
Tafel: η = a + b log10 |i|  (a = −b log10 i0)

### 2.6 Conductivity / transport
κ = Σ z_i F u_i c_i   (S/m);  λ_m = κ/c (molar conductivity, S·m²/mol).
Kohlrausch: Λ_m° = λ°_+ + λ°_-.

### 2.7 Voltammetry (Randles–Sevcik, reversible, 25 °C)
i_p = 0.4463 n F A C (n F v D / R T)^{1/2}
Peak separation ΔE_p ≈ 59/n mV (reversible); ΔE_p grows for quasi-reversible.
Diffusion (Cottrell): i(t) = n F A C* sqrt(D/(π t)).

### 2.8 Corrosion
E_corr where i_a + i_c = 0 (mixed potential). Corrosion rate:
CR (mm/y) = (i_corr · M · K)/(n · ρ · A) with K = 3.27×10⁻³ (mm·g/(μA·cm·y)).
Pourbaix: stability regions from Nernst + ΔG° of oxide/hydroxide formation.
Pitting: E_pit > E_corr + margin; chloride threshold [Cl⁻] > critical.

## 3. Data Structures (Python 3.12, frozen dataclasses)

```python
from dataclasses import dataclass, field
from typing import Literal
from enum import Enum

class CellType(str, Enum):
    GALVANIC = "galvanic"
    ELECTROLYTIC = "electrolytic"
    CONCENTRATION = "concentration"
    FUEL = "fuel"

@dataclass(frozen=True)
class HalfReaction:
    id: str                    # "cu2_cu"
    equation: str              # "Cu2+ + 2e- -> Cu(s)"
    E0_v: float                # standard potential V vs SHE
    n: int                     # electrons transferred
    species_ox: str            # "Cu2+"
    species_red: str           # "Cu(s)"
    deltaG0_kj_mol: float      # -n F E0

@dataclass(frozen=True)
class Electrode:
    id: str
    material: str              # "Cu", "Zn", "Pt", "graphite"
    half_reaction: HalfReaction
    area_cm2: float
    mass_g: float | None       # for deposition tracking

@dataclass
class Electrolyte:
    species: dict[str, float]  # name -> mol/L (activity approx)
    temperature_k: float = 298.15
    ph: float | None = None
    conductivity_s_m: float | None = None

@dataclass
class Cell:
    id: str
    cell_type: CellType
    anode: Electrode
    cathode: Electrode
    electrolyte_anode: Electrolyte
    electrolyte_cathode: Electrolyte
    salt_bridge: bool = True
    internal_resistance_ohm: float = 0.0
    external_load_ohm: float | None = None
    # derived (computed, not stored as truth)
    e_ocv_v: float = 0.0
    current_a: float = 0.0

@dataclass
class VoltammetryScan:
    electrode_id: str
    electrolyte: Electrolyte
    v_start: float
    v_end: float
    scan_rate_v_s: float
    waveform: Literal["linear","cyclic","square_wave","differential_pulse"]
    analyte: str
    concentration_mol_l: float
    diffusion_coeff_m2_s: float
    area_cm2: float
    temperature_k: float = 298.15

@dataclass
class VoltammetryResult:
    potentials_v: list[float]
    currents_a: list[float]
    i_peak_a: float
    e_peak_v: float
    i_peak_reverse_a: float | None
    delta_e_p_mv: float | None

@dataclass
class CorrosionSystem:
    metal: str
    environment: str            # "seawater", "acidic", "atmospheric"
    temperature_k: float
    ph: float
    chloride_mol_l: float
    oxygen_ppm: float
    anodic_tafel_slope_v_dec: float   # b_a
    cathodic_tafel_slope_v_dec: float  # b_c
    i_corr_a_cm2: float | None = None
    e_corr_v: float | None = None
    corrosion_rate_mm_y: float | None = None
    pitting_potential_v: float | None = None

@dataclass
class FaradayResult:
    moles_electrons: float
    mass_deposited_g: float
    volume_gas_m3: float | None
    extent_mol: float
    current_efficiency_pct: float | None
    duration_s: float
```

## 4. Module Layout

```
src/chemlab/simulation/electrochemistry/
  __init__.py
  constants.py          # F, R, T0, E° table, lambda_molar table
  half_reactions.py     # HALF_REACTION_REGISTRY
  nernst.py             # nernst(E0, Q, n, T)
  galvanic.py           # GalvanicCell (compute E_ocv, I, power)
  electrolysis.py       # ElectrolysisCell (Faraday mass/gas, efficiency)
  voltammetry.py        # Randles-Sevcik, Cottrell, scan simulation
  corrosion.py          # mixed potential, Tafel, Pourbaix, pitting
  conductivity.py       # Kohlrausch, molar conductivity
  models.py             # dataclasses above
tests/
  test_nernst.py
  test_faraday.py
  test_galvanic.py
  test_voltammetry.py
  test_corrosion.py
```

## 5. API Contracts

```python
class NernstSolver:
    def half_cell_potential(self, hr: HalfReaction, activities: dict[str,float], T: float) -> float: ...
    def cell_emf(self, cell: Cell) -> float: ...          # E_cathode - E_anode
    def equilibrium_constant(self, E0: float, n: int, T: float) -> float: ...

class GalvanicCell:
    def open_circuit_voltage(self, cell: Cell) -> float: ...
    def load_current(self, cell: Cell, load_ohm: float) -> float: ...   # I = E/(R_int+R_load)
    def power_w(self, cell: Cell) -> float: ...
    def discharge(self, cell: Cell, dt_s: float, load_ohm: float) -> Cell: ...  # updates masses/concs

class ElectrolysisCell:
    def run(self, cell: Cell, I: float, t: float, target_species: str) -> FaradayResult: ...
    def decomposition_voltage(self, cell: Cell) -> float: ...

class VoltammetrySimulator:
    def scan(self, params: VoltammetryScan) -> VoltammetryResult: ...   # returns i vs E arrays
    def peak_current(self, params: VoltammetryScan) -> float: ...       # Randles-Sevcik
    def diffusion_current(self, params, t: float) -> float: ...         # Cottrell

class CorrosionSimulator:
    def mixed_potential(self, cs: CorrosionSystem) -> tuple[float,float]: ...  # E_corr, i_corr
    def tafel_curves(self, cs, E_range) -> list[tuple[float,float]]: ...
    def corrosion_rate(self, i_corr_a_cm2, M, n, rho, K=3.27e-3) -> float: ...
    def pourbaix_regions(self, metal, T, activity) -> list[Region]: ...
    def pitting_risk(self, cs) -> bool: ...
```

## 6. Standard Potential Table (subset, V vs SHE, 25 °C)

| id | half-reaction | E° (V) |
|---|---|---|
| she | 2H+ + 2e- -> H2(g) | 0.000 |
| cu2_cu | Cu2+ + 2e- -> Cu | +0.340 |
| zn2_zn | Zn2+ + 2e- -> Zn | -0.763 |
| ag_ag | Ag+ + e- -> Ag | +0.7996 |
| fe3_fe2 | Fe3+ + e- -> Fe2+ | +0.771 |
| fe2_fe | Fe2+ + 2e- -> Fe | -0.440 |
| cl2_cl | Cl2 + 2e- -> 2Cl- | +1.358 |
| o2_h2o | O2 + 4H+ + 4e- -> 2H2O | +1.229 |
| o2_oh | O2 + 2H2O + 4e- -> 4OH- | +0.401 |
| al3_al | Al3+ + 3e- -> Al | -1.662 |
| na_na | Na+ + e- -> Na | -2.714 |
| cu_cu2 (rev) | Cu -> Cu2+ + 2e- | -0.340 (anode) |

Store as `HALF_REACTION_REGISTRY: dict[str, HalfReaction]` keyed by id; include
`deltaG0_kj_mol = -n*F*E0/1000`.

## 7. Validation & Tests

- `test_nernst.py`: E(Daniell cell, [Cu2+]=1, [Zn2+]=1) == 1.103 V;
  concentration cell E = -(0.05916/2) log([Zn2+]_an/[Zn2+]_cath).
- `test_faraday.py`: Cu deposition: 1 A × 1800 s → m = M*I*t/(nF) = 1.185 g (Cu, n=2).
- `test_voltammetry.py`: Randles-Sevcik peak for 1 mM ferrocene, D=2.4e-9, A=0.07 cm²,
  v=0.1 V/s, n=1 → i_p ≈ 1.88 μA.
- `test_corrosion.py`: mixed potential convergence; CR units mm/y.
- Property: Nernst reduces to E° when Q=1; ΔG = -nFE.
- All potentials rounded to 6 decimals internally; display 3 decimals.

## 8. Integration

- Reagent registry extended with `standard_potential_v`, `n_electrons`, `conductivity_lambda`.
- Game UI: `ElectrochemicalCellPanel` (3D cell view), `VoltammogramChart`,
  `CorrosionDashboard`, `FaradayCalculator`.
- xAPI: "completed electrolysis", "measured E_cell", "identified corrosion risk".
- Safety: GHS for acids/bases; current limits enforced in electrolysis sim.

## 9. Deliverables

1. `src/chemlab/simulation/electrochemistry/` package (modules above).
2. `tests/test_nernst.py`, `test_faraday.py`, `test_galvanic.py`,
   `tests/test_voltammetry.py`, `tests/test_corrosion.py`.
3. `docs/ELECTROCHEMISTRY_API.md`.
4. Optional: `simulation/electrochemistry_catalog.py` with prebuilt cells
   (Daniell, lead-acid, Li-ion, electrolysis of water/brine).