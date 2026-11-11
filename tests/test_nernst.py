"""
Tests for the Nernst equation solver.

Validates:
  * E = E° - (RT/nF) ln Q reduces to E° when Q = 1
  * Daniell cell E°cell = 0.340 - (-0.763) = 1.103 V at unit activities
  * Concentration cell sign and magnitude
"""

import math

import pytest

from chemlab.simulation.electrochemistry.constants import T0, F, R
from chemlab.simulation.electrochemistry.half_reactions import HALF_REACTION_REGISTRY
from chemlab.simulation.electrochemistry.nernst import NernstSolver


@pytest.mark.unit
def test_nernst_reduces_to_standard_when_q_is_one() -> None:
    """At unit reaction quotient Q=1, E must equal E° (ln(1) = 0)."""
    solver = NernstSolver()
    hr = HALF_REACTION_REGISTRY["cu2_cu"]
    activities = {"Cu2+": 1.0}
    e = solver.half_cell_potential(hr, activities, T0)
    assert abs(e - hr.E0_v) < 1e-9


@pytest.mark.unit
def test_daniell_cell_standard_emf() -> None:
    """Daniell cell Zn|Zn2+||Cu2+|Cu: E°cell = 0.340 - (-0.763) = 1.103 V."""
    solver = NernstSolver()
    cu = HALF_REACTION_REGISTRY["cu2_cu"]
    zn = HALF_REACTION_REGISTRY["zn2_zn"]
    # Unit activities -> half-cell potentials equal standard potentials
    e_cu = solver.half_cell_potential(cu, {"Cu2+": 1.0}, T0)
    e_zn = solver.half_cell_potential(zn, {"Zn2+": 1.0}, T0)
    e_cell = e_cu - e_zn
    assert abs(e_cell - 1.103) < 0.001


@pytest.mark.unit
def test_concentration_cell_sign_and_magnitude() -> None:
    """Concentration cell: E = -(0.05916/2) * log10([Zn2+]_anode/[Zn2+]_cathode)."""
    solver = NernstSolver()
    zn = HALF_REACTION_REGISTRY["zn2_zn"]
    e_anode = solver.half_cell_potential(zn, {"Zn2+": 0.1}, T0)  # dilute anode
    e_cath = solver.half_cell_potential(zn, {"Zn2+": 1.0}, T0)  # concentrated cathode
    e_cell = e_cath - e_anode
    expected = -(0.05916 / 2.0) * math.log10(0.1 / 1.0)
    assert abs(e_cell - expected) < 1e-4
    assert e_cell > 0.0  # concentrated cathode drives positive cell potential


@pytest.mark.unit
def test_nernst_temperature_scaling() -> None:
    """Nernst slope scales linearly with temperature."""
    solver = NernstSolver()
    hr = HALF_REACTION_REGISTRY["fe3_fe2"]
    e_298 = solver.half_cell_potential(hr, {"Fe3+": 10.0, "Fe2+": 1.0}, 298.15)
    e_310 = solver.half_cell_potential(hr, {"Fe3+": 10.0, "Fe2+": 1.0}, 310.0)
    # Higher T -> larger |RT/nF ln Q| term
    assert abs(e_310 - hr.E0_v) > abs(e_298 - hr.E0_v)
