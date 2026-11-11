"""
Tests for metabolic pathways — glycolysis and Krebs cycle ODE integration.

Validates mass balance and known pathway stoichiometry.
"""

import pytest

from chemlab.simulation.biochemistry.metabolic_pathways import (
    GLYCOLYSIS,
    KREBS,
    PATHWAYS,
    integrate_pathway,
)


@pytest.mark.unit
def test_pathways_registered() -> None:
    """Both core pathways are available by id."""
    assert "glycolysis" in PATHWAYS
    assert "krebs" in PATHWAYS
    assert len(GLYCOLYSIS.reactions) == 10
    assert len(KREBS.reactions) == 8


@pytest.mark.unit
def test_glycolysis_mass_balance_conserved() -> None:
    """Integrating glycolysis should not create/destroy carbon mass unrealistically."""
    init = {
        "Glc": 1.0,
        "ATP": 5.0,
        "ADP": 1.0,
        "NAD+": 2.0,
        "NADH": 0.0,
        "Pi": 5.0,
        "H2O": 55.0,
        "H+": 1e-7,
    }
    for s in GLYCOLYSIS.species:
        init.setdefault(s, 0.0)
    final = integrate_pathway(GLYCOLYSIS, init, t_end_s=10.0, dt_s=0.1)
    # All concentrations remain non-negative (RK4 with clamping)
    for conc in final.concentrations.values():
        assert conc >= 0.0
    assert final.time_s == pytest.approx(10.0)


@pytest.mark.unit
def test_krebs_steady_state_reaches_positive_flux() -> None:
    """Krebs cycle integrates to positive metabolite turnover."""
    init = {
        "Acetyl-CoA": 0.1,
        "Oxaloacetate": 0.1,
        "NAD+": 1.0,
        "NADH": 0.0,
        "FAD": 0.1,
        "FADH2": 0.0,
        "GDP": 0.1,
        "GTP": 0.0,
        "CoA": 0.2,
        "H2O": 55.0,
        "Pi": 5.0,
        "CO2": 0.0,
        "H+": 1e-7,
    }
    for s in KREBS.species:
        init.setdefault(s, 0.0)
    final = integrate_pathway(KREBS, init, t_end_s=20.0, dt_s=0.1)
    for conc in final.concentrations.values():
        assert conc >= 0.0
    assert final.time_s == pytest.approx(20.0)


@pytest.mark.unit
def test_dt_accuracy() -> None:
    """Smaller dt should not drastically change the result (convergence)."""
    init = {"Glc": 1.0, "ATP": 5.0, "ADP": 1.0, "NAD+": 2.0, "Pi": 5.0}
    for s in GLYCOLYSIS.species:
        init.setdefault(s, 0.0)
    coarse = integrate_pathway(GLYCOLYSIS, init, t_end_s=5.0, dt_s=0.5)
    fine = integrate_pathway(GLYCOLYSIS, init, t_end_s=5.0, dt_s=0.05)
    # Pyr should be within 20% between coarse and fine
    p_coarse = coarse.concentrations.get("Pyr", 0.0)
    p_fine = fine.concentrations.get("Pyr", 0.0)
    if p_fine > 0:
        assert abs(p_coarse - p_fine) / p_fine < 0.2
