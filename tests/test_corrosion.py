"""
Corrosion tests.

Validates:
  * Mixed-potential convergence (E_corr, i_corr)
  * Corrosion rate units mm/y
  * Tafel curve generation
  * Pitting risk assessment
"""

import pytest

from chemlab.simulation.electrochemistry.corrosion import (
    CorrosionSimulator,
    CorrosionSystem,
)


@pytest.fixture
def sim() -> CorrosionSimulator:
    return CorrosionSimulator()


@pytest.mark.unit
def test_mixed_potential_convergence(sim: CorrosionSimulator) -> None:
    """Mixed potential should converge to a finite value within range."""
    cs = CorrosionSystem(
        metal="Zn",
        environment="acidic",
        temperature_k=298.15,
        ph=4.0,
        chloride_mol_l=0.01,
        oxygen_ppm=8.0,
        anodic_tafel_slope_v_dec=0.12,
        cathodic_tafel_slope_v_dec=0.12,
    )
    e_corr, i_corr = sim.mixed_potential(cs)
    assert -2.0 < e_corr < 2.0
    assert i_corr >= 0.0
    assert cs.corrosion_rate_mm_y is not None
    assert cs.corrosion_rate_mm_y >= 0.0


@pytest.mark.unit
def test_corrosion_rate_units(sim: CorrosionSimulator) -> None:
    """CR = i_corr * M * K / (n * rho) should be positive and finite."""
    cr = sim.corrosion_rate(
        i_corr_a_cm2=1e-6,
        molar_mass_g_mol=65.38,
        n_electrons=2,
        density_g_cm3=7.14,
    )
    assert cr > 0.0
    assert cr < 1000.0  # sanity: µm/y scale for µA/cm²


@pytest.mark.unit
def test_tafel_curves(sim: CorrosionSimulator) -> None:
    """Tafel curves should return matching-length arrays."""
    cs = CorrosionSystem(
        metal="Fe",
        environment="seawater",
        temperature_k=298.15,
        ph=8.0,
        chloride_mol_l=0.5,
        oxygen_ppm=8.0,
        anodic_tafel_slope_v_dec=0.12,
        cathodic_tafel_slope_v_dec=0.12,
    )
    curve = sim.tafel_curves(cs, e_range_v=(-1.0, 0.0), num_points=50)
    assert len(curve.potentials_v) == 50
    assert len(curve.anodic_currents_a_cm2) == 50
    assert len(curve.cathodic_currents_a_cm2) == 50


@pytest.mark.unit
def test_pitting_risk(sim: CorrosionSimulator) -> None:
    """High chloride + acidic should flag pitting risk."""
    cs_high = CorrosionSystem(
        metal="Fe",
        environment="seawater",
        temperature_k=298.15,
        ph=4.0,
        chloride_mol_l=0.5,
        oxygen_ppm=8.0,
        anodic_tafel_slope_v_dec=0.12,
        cathodic_tafel_slope_v_dec=0.12,
    )
    at_risk, reason = sim.pitting_risk(cs_high)
    assert at_risk is True
    assert "Pitting risk" in reason

    cs_low = CorrosionSystem(
        metal="Fe",
        environment="atmospheric",
        temperature_k=298.15,
        ph=7.0,
        chloride_mol_l=0.001,
        oxygen_ppm=8.0,
        anodic_tafel_slope_v_dec=0.12,
        cathodic_tafel_slope_v_dec=0.12,
    )
    at_risk_low, _ = sim.pitting_risk(cs_low)
    assert at_risk_low is False
