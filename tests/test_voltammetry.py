"""
Voltammetry tests.

Validates:
  * Randles-Sevcik peak current ~1.88 µA for 1 mM ferrocene
  * Cottrell current decays as t^-0.5
"""

import pytest

from chemlab.simulation.electrochemistry.voltammetry import VoltammetrySimulator


@pytest.mark.unit
def test_randles_sevcik_peak_current() -> None:
    """1 mM ferrocene, D=2.4e-9 m²/s, A=0.07 cm², v=0.1 V/s, n=1 -> ~29 µA."""
    sim = VoltammetrySimulator()
    i_p = sim.peak_current_randles_sevcik(
        n=1,
        area_cm2=0.07,
        concentration_mol_l=0.001,
        scan_rate_v_s=0.1,
        diffusion_coeff_m2_s=2.4e-9,
    )
    expected = 2.9e-5
    assert abs(i_p - expected) < 0.5e-5


@pytest.mark.unit
def test_cottrell_decay() -> None:
    """Cottrell current i ~ t^-0.5: doubling time reduces current by sqrt(2)."""
    sim = VoltammetrySimulator()
    i1 = sim.cottrell_current(
        n=1,
        area_cm2=1.0,
        concentration_mol_l=1.0,
        diffusion_coeff_m2_s=1e-9,
        time_s=1.0,
    )
    i2 = sim.cottrell_current(
        n=1,
        area_cm2=1.0,
        concentration_mol_l=1.0,
        diffusion_coeff_m2_s=1e-9,
        time_s=4.0,
    )
    assert abs(i2 - i1 / 2.0) < 1e-12
    assert i1 > i2 > 0.0
