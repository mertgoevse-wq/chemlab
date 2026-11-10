"""
Tests for Faraday's laws of electrolysis.

Validates:
  * m = M * I * t / (n * F)
  * n_e = I * t / F
  * extent xi = I * t / (n * F)
"""

import pytest

from chemlab.simulation.electrochemistry.constants import F, M_COPPER
from chemlab.simulation.electrochemistry.electrolysis import ElectrolysisCell, faraday_mass_deposited, faraday_moles_electrons


@pytest.mark.unit
def test_copper_deposition_mass() -> None:
    """Cu2+ + 2e- -> Cu: 1 A for 1800 s deposits M*I*t/(nF) grams."""
    mass = faraday_mass_deposited(M_COPPER, current_a=1.0, duration_s=1800.0, n_electrons=2)
    expected = M_COPPER * 1.0 * 1800.0 / (2.0 * F)
    assert abs(mass - expected) < 1e-6
    # ~0.593 g for n=2 (physically correct for Cu2+ reduction)
    assert abs(mass - 0.5927) < 0.001


@pytest.mark.unit
def test_moles_of_electrons() -> None:
    """n_e = I * t / F."""
    n_e = faraday_moles_electrons(current_a=1.0, duration_s=96485.33212)
    assert abs(n_e - 1.0) < 1e-6


@pytest.mark.unit
def test_electrolysis_cell_run() -> None:
    """ElectrolysisCell.run returns a FaradayResult with consistent fields."""
    cell = ElectrolysisCell()
    result = cell.run(
        electrode_material="Cu",
        current_a=0.5,
        duration_s=3600.0,
        target_species="Cu2+",
        n_electrons=2,
    )
    assert result.moles_electrons == pytest.approx(0.5 * 3600.0 / F)
    assert result.extent_mol == pytest.approx(result.moles_electrons / 2.0)
    assert result.duration_s == 3600.0
    assert result.current_efficiency_pct is None or 0.0 <= result.current_efficiency_pct <= 100.0
