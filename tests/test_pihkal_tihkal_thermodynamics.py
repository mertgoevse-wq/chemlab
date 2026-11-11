"""
Unit and integration tests for PiHKAL and TiHKAL synthesis thermodynamics,
stoichiometric mass conservation, dual-engine parity, and graphics bridge parameters.
"""

import math
import re
from collections import Counter

import pytest


def _formula_atoms(formula: str, coefficient: float) -> Counter[str]:
    """Expand a simple molecular formula into coefficient-weighted atom counts."""
    atoms: Counter[str] = Counter()
    for element, count_text in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        atoms[element] += coefficient * int(count_text or "1")
    return atoms


def test_pihkal_precursors_have_complete_simulation_properties():
    """Verify PiHKAL catalog entries have complete simulation properties."""
    # Arrange
    from chemlab.chemistry.literature_catalogs import PIHKAL_TIHKAL_SPECIES, LiteratureCatalog

    required_precursors = [
        "3_4_5_trimethoxybenzaldehyde",
        "nitromethane",
        "nitroethane",
        "piperonal",
        "2_5_dimethoxybenzaldehyde",
        "lialh4",
        "nabh4",
        "ammonium_acetate",
        "mescaline",
        "2c_b",
        "dom",
        "mdma",
    ]

    # Act & Assert
    for pid in required_precursors:
        species = PIHKAL_TIHKAL_SPECIES.get(pid)
        assert species is not None, f"Missing precursor {pid} in PIHKAL_TIHKAL_SPECIES"
        assert species.molecular_weight_g_mol > 0.0, f"Invalid MW for {pid}"
        assert species.density_g_cm3 > 0.0, f"Invalid density for {pid}"
        assert species.delta_h_f_kj_mol != 0.0, f"Missing Delta H for {pid}"
        assert species.s_standard_j_mol_k > 0.0, f"Invalid entropy for {pid}"
        assert species.cp_j_mol_k > 0.0, f"Invalid Cp for {pid}"
        assert species.cas_number != "", f"Missing CAS for {pid}"
        assert len(species.ghs_pictograms) > 0, f"Missing GHS for {pid}"


def test_tihkal_precursors_have_complete_simulation_properties():
    """Verify TiHKAL catalog entries have complete simulation properties."""
    # Arrange
    from chemlab.chemistry.literature_catalogs import PIHKAL_TIHKAL_SPECIES

    required_tihkal = [
        "indole",
        "indole_3_carboxaldehyde",
        "tryptamine",
        "5_methoxytryptamine",
        "oxalyl_chloride",
        "dimethylamine",
        "dmt",
        "5_meo_dmt",
        "psilocin",
    ]

    # Act & Assert
    for tid in required_tihkal:
        species = PIHKAL_TIHKAL_SPECIES.get(tid)
        assert species is not None, f"Missing TiHKAL compound {tid}"
        assert species.molecular_weight_g_mol > 0.0
        assert species.delta_h_f_kj_mol != 0.0
        assert species.s_standard_j_mol_k > 0.0
        assert species.cp_j_mol_k > 0.0
        assert species.cas_number != ""


def test_closed_reaction_steps_conserve_each_element():
    """Verify every closed-system catalog equation is atomically balanced."""
    # Arrange
    from chemlab.chemistry.literature_catalogs import LiteratureCatalog

    catalog = LiteratureCatalog()
    routes = catalog.get_all_synthesis_routes()

    # Act & Assert
    for route in routes:
        for step in route.steps:
            if not step.is_closed_system:
                assert step.balance_note.strip(), (
                    f"Open-system step {route.id}:{step.step_number} needs a balance note"
                )
                continue

            reactant_atoms: Counter[str] = Counter()
            product_atoms: Counter[str] = Counter()
            for species_id, coefficient in step.reactants.items():
                reactant_atoms.update(
                    _formula_atoms(catalog.get_species(species_id).formula, coefficient)
                )
            for species_id, coefficient in step.products.items():
                product_atoms.update(
                    _formula_atoms(catalog.get_species(species_id).formula, coefficient)
                )

            assert reactant_atoms == product_atoms, (
                f"Element balance violated in {route.id} step {step.step_number}: "
                f"reactants={dict(reactant_atoms)}, products={dict(product_atoms)}"
            )


def test_open_reaction_steps_are_explicitly_documented():
    """Verify abbreviated process steps cannot masquerade as closed equations."""
    # Arrange
    from chemlab.chemistry.literature_catalogs import LiteratureCatalog

    catalog = LiteratureCatalog()

    # Act
    open_steps = [
        (route.id, step)
        for route in catalog.get_all_synthesis_routes()
        for step in route.steps
        if not step.is_closed_system
    ]

    # Assert
    assert open_steps, "Catalog should identify abbreviated workup boundaries"
    assert all(step.balance_note.strip() for _, step in open_steps)


def test_henry_condensation_standard_state_is_exothermic_but_not_favorable_at_reflux():
    """Verify the catalog's standard-state Henry thermodynamics at 105 C."""
    # Arrange
    from chemlab.chemistry.literature_catalogs import LiteratureCatalog
    from chemlab.chemistry.thermodynamics.engine import CanteraThermodynamicsEngine

    catalog = LiteratureCatalog()
    thermo = CanteraThermodynamicsEngine()

    route = catalog.get_route("mescaline_henry_lah")
    henry_step = route.steps[0]

    # Act
    res = thermo.calculate_reaction_thermodynamics(
        reactants=henry_step.reactants,
        products=henry_step.products,
        temperature_c=105.0,
        activation_energy_kj_mol=henry_step.activation_energy_kj_mol,
    )

    # Assert
    assert res.delta_h_kj_mol < 0.0, "Catalog estimate should be exothermic"
    assert res.delta_s_j_mol_k < 0.0
    assert not res.is_spontaneous, (
        "Standard-state favorability must not be inferred from a heated literature procedure"
    )
    assert res.equilibrium_constant_k_eq < 1.0


def test_lah_reduction_exothermicity_and_safety():
    """Verify LAH reduction reaction exhibits strong exothermicity and triggers hazard alerts."""
    # Arrange
    from chemlab.chemistry.literature_catalogs import LiteratureCatalog
    from chemlab.chemistry.thermodynamics.engine import CanteraThermodynamicsEngine

    catalog = LiteratureCatalog()
    thermo = CanteraThermodynamicsEngine()

    route = catalog.get_route("mescaline_henry_lah")
    lah_step = route.steps[1]

    # Act
    res = thermo.calculate_reaction_thermodynamics(
        reactants=lah_step.reactants,
        products=lah_step.products,
        temperature_c=66.0,
        activation_energy_kj_mol=lah_step.activation_energy_kj_mol,
    )

    # Assert
    assert res.delta_h_kj_mol < -100.0, "LAH reduction must release substantial heat"
    assert res.is_exothermic
    assert len(res.warnings) > 0, "Safety warnings should trigger for strongly exothermic reaction"


def test_graphics_bridge_beer_lambert_absorption():
    """Verify Beer-Lambert Law absorption mapping: A = eps * c * l."""
    # Arrange
    from chemlab.chemistry.literature_catalogs import calculate_beer_lambert_absorption

    epsilon = 12500.0  # M^-1 cm^-1 (e.g. nitrostyrene chromophore)
    conc_m = 0.002  # 2 mM
    path_length_cm = 1.0

    # Act
    absorbance, transmission = calculate_beer_lambert_absorption(epsilon, conc_m, path_length_cm)

    # Assert: A = 12500 * 0.002 * 1.0 = 25.0, T = 10^(-25) ~ 0.0
    assert math.isclose(absorbance, 25.0, rel_tol=1e-5)
    assert transmission < 1e-6


def test_graphics_bridge_stokes_settling_velocity():
    """Verify Stokes' Law particle settling velocity calculation."""
    # Arrange
    from chemlab.chemistry.literature_catalogs import calculate_stokes_settling_velocity

    radius_m = 50e-6  # 50 micron crystal
    rho_p = 1440.0  # crystal density kg/m3
    rho_f = 1000.0  # fluid density kg/m3 (water)
    eta = 1.0e-3  # dynamic viscosity Pa*s

    # Act
    v_settle = calculate_stokes_settling_velocity(radius_m, rho_p, rho_f, eta)

    # Assert
    # v = 2 * r^2 * (rho_p - rho_f) * g / (9 * eta)
    # v = 2 * (25e-10) * 440 * 9.80665 / (9 * 1e-3) ~ 0.002397 m/s
    assert v_settle > 0.0
    expected = (2.0 * (radius_m**2) * (rho_p - rho_f) * 9.80665) / (9.0 * eta)
    assert math.isclose(v_settle, expected, rel_tol=1e-4)


def test_oregonator_rk4_converges_across_external_timesteps():
    """Verify stiff Oregonator integration is bounded and independent of caller cadence."""
    # Arrange
    from chemlab.chemistry.kinetics.oscillator import OregonatorModel

    external_dts = [0.0005, 0.001, 0.002, 1.0 / 60.0]
    horizon_seconds = 2.5
    final_states = []

    # Act
    for dt in external_dts:
        model = OregonatorModel()
        state = (0.5, 0.5, 0.5)
        states = []
        elapsed = 0.0
        while elapsed < horizon_seconds:
            step = min(dt, horizon_seconds - elapsed)
            state = model.step_rk4(state, step)
            states.append(state)
            elapsed += step
        final_states.append(state)

        # Assert: the full trajectory remains finite, non-negative, and within
        # the documented transient envelope of this dimensionless model.
        for x, y, z in states:
            assert all(math.isfinite(value) for value in (x, y, z))
            assert x >= 0.0 and y >= 0.0 and z >= 0.0
            assert x < 2.0 and y < 250.0 and z < 2.0

    reference = final_states[0]
    for candidate in final_states[1:]:
        assert candidate == pytest.approx(reference, rel=2e-3, abs=2e-4)
