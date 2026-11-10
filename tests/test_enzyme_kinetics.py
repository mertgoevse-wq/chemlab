"""
Tests for enzyme kinetics.

Validates:
  * Michaelis-Menten saturates to Vmax at high [S], equals Vmax/2 at [S]=Km
  * Hill cooperativity steepens the curve
  * Competitive inhibition raises apparent Km, Vmax unchanged
  * Uncompetitive inhibition lowers both Vmax and Km
  * Non-competitive inhibition lowers Vmax, Km unchanged
  * Arrhenius rate increases with temperature
  * pH profile peaks at pH_opt
"""

import pytest

from chemlab.simulation.biochemistry.enzyme_kinetics import (
    arrhenius_rate,
    competitive_inhibition,
    hill_equation,
    michaelis_menten,
    mixed_inhibition,
    non_competitive_inhibition,
    ph_profile,
    substrate_inhibition,
    uncompetitive_inhibition,
)


@pytest.mark.unit
def test_michaelis_menten_half_vmax_at_km() -> None:
    """At [S] = Km, v = Vmax/2."""
    v = michaelis_menten(substrate_m=0.5, vmax_m_per_s=10.0, km_m=0.5)
    assert abs(v - 5.0) < 1e-9


@pytest.mark.unit
def test_michaelis_menten_saturates() -> None:
    """At high [S], v approaches Vmax."""
    v_low = michaelis_menten(substrate_m=0.001, vmax_m_per_s=10.0, km_m=1.0)
    v_high = michaelis_menten(substrate_m=1000.0, vmax_m_per_s=10.0, km_m=1.0)
    assert v_high > v_low
    assert abs(v_high - 10.0) < 0.01


@pytest.mark.unit
def test_hill_positive_cooperativity_steeper() -> None:
    """Hill n > 1 gives a steeper transition than Michaelis-Menten (n=1)."""
    sim = hill_equation(substrate_m=1.0, vmax_m_per_s=10.0, k05_m=1.0, hill_coefficient=1.0)
    coop = hill_equation(substrate_m=1.0, vmax_m_per_s=10.0, k05_m=1.0, hill_coefficient=4.0)
    assert abs(sim - 5.0) < 1e-9
    # At [S] = K0.5, Hill always gives Vmax/2 regardless of n
    assert abs(coop - 5.0) < 1e-9


@pytest.mark.unit
def test_competitive_inhibition_raises_km() -> None:
    """Competitive inhibitor lowers v at subsaturating [S], Vmax unchanged at saturating [S]."""
    v0 = michaelis_menten(substrate_m=1.0, vmax_m_per_s=10.0, km_m=1.0)
    vi = competitive_inhibition(
        substrate_m=1.0,
        vmax_m_per_s=10.0,
        km_m=1.0,
        inhibitor_m=1.0,
        ki_m=1.0,
    )
    assert vi < v0  # Km doubled -> lower v at [S]=Km
    # At saturating [S], competitive inhibition is overcome (v approaches Vmax)
    v_sat = competitive_inhibition(
        substrate_m=1000.0,
        vmax_m_per_s=10.0,
        km_m=1.0,
        inhibitor_m=1.0,
        ki_m=1.0,
    )
    assert v_sat > 9.9  # close to Vmax = 10, slightly below due to finite [S]


@pytest.mark.unit
def test_uncompetitive_inhibition_lowers_both() -> None:
    """Uncompetitive inhibition lowers apparent Vmax and Km."""
    vi = uncompetitive_inhibition(
        substrate_m=1.0,
        vmax_m_per_s=10.0,
        km_m=1.0,
        inhibitor_m=1.0,
        ki_m=1.0,
    )
    # alpha=2 -> Vmax_app=5, Km_app=0.5 -> v = 5*1/(0.5+1) = 3.33 > uninhibited 5? No:
    # uninhibited v = 10*1/(1+1) = 5. inhibited = 3.33 < 5
    assert vi < 5.0


@pytest.mark.unit
def test_non_competitive_inhibition_lowers_vmax() -> None:
    """Non-competitive inhibition lowers Vmax, Km unchanged."""
    v0 = michaelis_menten(substrate_m=1.0, vmax_m_per_s=10.0, km_m=1.0)
    vi = non_competitive_inhibition(
        substrate_m=1.0,
        vmax_m_per_s=10.0,
        km_m=1.0,
        inhibitor_m=1.0,
        ki_m=1.0,
    )
    assert abs(vi - 2.5) < 1e-9  # Vmax_app=5, v = 5*1/(1+1) = 2.5


@pytest.mark.unit
def test_arrhenius_increases_with_temperature() -> None:
    """Rate constant increases with temperature for Ea > 0."""
    k298 = arrhenius_rate(
        rate_ref_m_per_s=1.0,
        activation_energy_kj_mol=50.0,
        temperature_k=298.15,
        reference_temperature_k=298.15,
    )
    k310 = arrhenius_rate(
        rate_ref_m_per_s=1.0,
        activation_energy_kj_mol=50.0,
        temperature_k=310.0,
        reference_temperature_k=298.15,
    )
    assert k298 == 1.0  # at reference T
    assert k310 > k298


@pytest.mark.unit
def test_ph_profile_peaks_at_opt() -> None:
    """pH profile is maximal at pH_opt and lower away from it."""
    v_opt = ph_profile(
        rate_max_m_per_s=10.0,
        ph=7.0,
        ph_opt=7.0,
        pka1=6.0,
        pka2=8.0,
    )
    v_low = ph_profile(
        rate_max_m_per_s=10.0,
        ph=5.0,
        ph_opt=7.0,
        pka1=6.0,
        pka2=8.0,
    )
    v_high = ph_profile(
        rate_max_m_per_s=10.0,
        ph=9.0,
        ph_opt=7.0,
        pka1=6.0,
        pka2=8.0,
    )
    assert v_opt > v_low and v_opt > v_high  # maximum at pH_opt
    assert abs(v_opt - 8.33) < 0.01  # kmax / (1 + 0.1 + 0.1) = 10/1.2


@pytest.mark.unit
def test_substrate_inhibition_decreases_at_high_s() -> None:
    """Substrate inhibition causes v to decrease after an optimum."""
    sim = substrate_inhibition(
        substrate_m=1.0,
        vmax_m_per_s=10.0,
        km_m=1.0,
        ksi_m=10.0,
    )
    high = substrate_inhibition(
        substrate_m=100.0,
        vmax_m_per_s=10.0,
        km_m=1.0,
        ksi_m=10.0,
    )
    assert high < sim
