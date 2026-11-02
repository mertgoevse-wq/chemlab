# TiHKAL/PiHKAL Stoichiometry & Yield Calculation — In-Game Challenge Specification

## 1. Scope & Safety Framing

This spec defines a *calculation-only* subsystem for the ChemLab game engine. It extracts
stoichiometric relationships, molar masses, and yield math from published synthesis
literature (TiHKAL/PiHKAL) **as educational data**, and exposes them as deterministic
in-game calculation challenges. It does NOT provide step-by-step synthetic procedures,
reagent sourcing, or equipment guidance for controlled substances. All challenge inputs
are validated against a closed, allow-listed reagent set; no free-form reaction entry.

## 2. Core Data Model

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass(frozen=True)
class Reagent:
    id: str                 # canonical snake_case key, e.g. "anisaldehyde"
    name: str               # display name
    formula: str            # molecular formula
    molar_mass_g_mol: float # IUPAC atomic weights, 4 sig figs
    role: Literal["limiting","excess","catalyst","solvent","workup"]
    stoich_coeff: float     # coefficient in balanced equation (relative to product = 1)
    purity_pct: float = 100.0

@dataclass(frozen=True)
class SynthesisEntry:
    entry_id: str           # e.g. "tihkal_042"
    source: Literal["TiHKAL","PiHKAL"]
    target_name: str
    target_formula: str
    target_molar_mass_g_mol: float
    balanced_equation: str   # display-only, e.g. "A + B -> C + H2O"
    reagents: tuple[Reagent, ...]
    theoretical_yield_basis: str  # "limiting reagent mass"
    reported_yield_pct: float | None  # literature value, nullable
    stages: int
    notes: str = ""

@dataclass
class YieldResult:
    limiting_reagent_id: str
    moles_limiting: float
    theoretical_mass_g: float
    actual_mass_g: float | None
    percent_yield: float | None
    atom_economy_pct: float
```

## 3. Equations

Let `n_lr` = moles of limiting reagent, `M_target` = molar mass of product (g/mol),
`ν_lr` = stoichiometric coefficient of limiting reagent, `ν_prod` = coefficient of product.

- Moles of product (theoretical): `n_prod = n_lr * (ν_prod / ν_lr)`
- Theoretical mass: `m_theo = n_prod * M_target`
- Percent yield: `Y% = (m_actual / m_theo) * 100`
- Atom economy: `AE% = (M_target / Σ M_reagents_stoich) * 100`
- Mass of excess reagent consumed: `m_excess = n_lr * (ν_excess/ν_lr) * M_excess`
- Reagent mass input total: `m_in = Σ (n_i * M_i)` over stoichiometric amounts
- E-factor: `E = (m_in - m_theo) / m_theo`

Precision: round to 4 significant figures for display; keep full float internally.

## 4. Registry Contract

```python
class SynthesisRegistry:
    def list_entries(self, source: str | None = None) -> list[str]: ...
    def get_entry(self, entry_id: str) -> SynthesisEntry: ...
    def compute_yield(self, entry_id: str, limiting_mass_g: float,
                      actual_mass_g: float | None = None) -> YieldResult: ...
    def challenge_set(self, difficulty: int) -> list[Challenge]: ...
```

Entry IDs follow `"{source.lower()}_{index:03d}"`. Indexes are stable; renumbering forbidden.

## 5. In-Game Calculation Challenges

Challenge types (deterministic, seeded RNG per session):

1. **Limiting-Reagent ID** (easy): Given masses of two reagents, identify limiting one.
   - Inputs: masses m_A, m_B; M_A, M_B; coeffs. Output: "A" or "B".
   - Check: `n_A/ν_A < n_B/ν_B`.

2. **Theoretical Yield** (medium): Compute `m_theo` from limiting mass.
   - Tolerance: ±0.5%.

3. **Percent Yield** (medium): Given actual isolated mass, compute Y%.
   - Tolerance: ±0.1 percentage point.

4. **Atom Economy** (hard): Compute AE% for the balanced equation.
   - Tolerance: ±0.1%.

5. **Multi-Stage Overall Yield** (hard): Given per-stage yields y1..yn, compute overall
   `Y_overall = ∏ y_i` (as fractions). Tolerance: ±0.1%.

6. **E-Factor** (expert): Compute E-factor; classify waste category.

Scoring: base 100 pts per challenge, -10 per hint, time bonus `max(0, 60 - t_seconds)*2`.

## 6. Validation & Anti-AI-Slop

- All molar masses verified against IUPAC 2023 atomic weights in `chemlab_core/chemistry/atomic_weights.py`.
- Every entry must pass `test_stoichiometry_balance.py`: atom counts LHS == RHS.
- Challenge generator must be deterministic given seed; snapshot tests in `tests/test_tihkal_challenges.py`.
- No synthesis procedure text exposed in challenge payloads (only equation + masses).

## 7. Integration Points

- `simulation/total_syntheses.py` extended with `SynthesisEntry`/`YieldResult` (non-breaking).
- New module `simulation/stoichiometry.py` houses generic math.
- Game UI: `CalculationChallengePanel` (React) consumes `/api/challenges/next`.
- Leaderboard keyed by (user, difficulty, entry_id).

## 8. Test Plan

- Unit: stoichiometry math (10 cases), registry lookup, determinism.
- Property: atom balance for all entries.
- Snapshot: challenge generation for seed=42.

## 9. Deliverables

1. `src/chemlab/simulation/stoichiometry.py`
2. `src/chemlab/simulation/tihkal_registry.py` (data-only, no procedures)
3. `tests/test_stoichiometry.py`, `tests/test_tihkal_challenges.py`
4. `docs/STOICHIOMETRY_API.md`
```

Note: This spec intentionally avoids reproducing controlled-substance synthesis recipes.
TiHKAL/PiHKAL entries are stored as abstract stoichiometric records (equation + masses)
for educational calculation practice only.