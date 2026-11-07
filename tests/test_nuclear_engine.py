"""
Unit and integration tests for the Nuclear Physics and Radiochemistry Engine.
Validates decay chains, half-life calculations, activity, shielding, criticality,
isotope production, fission yields, reactor simulation, and reprocessing.
"""

import math

import pytest

from chemlab.simulation.nuclear_engine import (
    NuclearEngine,
    DecayMode,
    Isotope,
    DecayChain,
    ShieldingMaterial,
    ReactorType,
    ReactorState,
    FuelAssembly,
    ReprocessingStream,
    NUCLEAR_ENGINE,
)


# ============================================================================
# Isotope Catalog Tests (200+ isotopes)
# ============================================================================

def test_isotope_catalog_size():
    """Verify the isotope catalog contains 200+ isotopes."""
    isotopes = NUCLEAR_ENGINE.get_all_isotopes()
    assert len(isotopes) >= 200, f"Expected 200+ isotopes, got {len(isotopes)}"


def test_isotope_lookup_by_z_a():
    """Test isotope retrieval by atomic number Z and mass number A."""
    u235 = NUCLEAR_ENGINE.get_isotope(92, 235)
    assert u235 is not None
    assert u235.z == 92
    assert u235.a == 235
    assert u235.symbol == "U"
    assert u235.name == "Uranium-235"
    assert abs(u235.half_life_seconds - 7.04e8 * 365.25 * 24 * 3600) < 1e13


def test_isotope_lookup_by_symbol():
    """Test isotope retrieval by element symbol and mass number."""
    pu239 = NUCLEAR_ENGINE.get_isotope_by_symbol("Pu-239")
    assert pu239 is not None
    assert pu239.z == 94
    assert pu239.a == 239
    assert pu239.half_life_seconds > 0


def test_uranium_isotopes():
    """Test key uranium isotopes exist with correct properties."""
    u234 = NUCLEAR_ENGINE.get_isotope(92, 234)
    u235 = NUCLEAR_ENGINE.get_isotope(92, 235)
    u238 = NUCLEAR_ENGINE.get_isotope(92, 238)

    assert u234.half_life_seconds == pytest.approx(2.455e5 * 365.25 * 24 * 3600, rel=0.1)
    assert u235.half_life_seconds == pytest.approx(7.04e8 * 365.25 * 24 * 3600, rel=0.1)
    assert u238.half_life_seconds == pytest.approx(4.468e9 * 365.25 * 24 * 3600, rel=0.1)

    # U-235 is fissile
    assert u235.is_fissile is True
    # U-238 is fertile
    assert u238.is_fertile is True


def test_plutonium_isotopes():
    """Test key plutonium isotopes."""
    pu238 = NUCLEAR_ENGINE.get_isotope(94, 238)
    pu239 = NUCLEAR_ENGINE.get_isotope(94, 239)
    pu240 = NUCLEAR_ENGINE.get_isotope(94, 240)
    pu241 = NUCLEAR_ENGINE.get_isotope(94, 241)

    assert pu238.half_life_seconds == pytest.approx(87.7 * 365.25 * 24 * 3600, rel=0.1)
    assert pu239.half_life_seconds == pytest.approx(2.411e4 * 365.25 * 24 * 3600, rel=0.1)
    assert pu240.half_life_seconds == pytest.approx(6561 * 365.25 * 24 * 3600, rel=0.1)
    assert pu241.half_life_seconds == pytest.approx(14.35 * 365.25 * 24 * 3600, rel=0.1)

    assert pu239.is_fissile is True
    assert pu241.is_fissile is True


def test_fission_products():
    """Test key fission product isotopes exist."""
    cs137 = NUCLEAR_ENGINE.get_isotope(55, 137)
    sr90 = NUCLEAR_ENGINE.get_isotope(38, 90)
    i131 = NUCLEAR_ENGINE.get_isotope(53, 131)
    xe135 = NUCLEAR_ENGINE.get_isotope(54, 135)
    sm149 = NUCLEAR_ENGINE.get_isotope(62, 149)

    assert cs137 is not None
    assert cs137.half_life_seconds == pytest.approx(30.17 * 365.25 * 24 * 3600, rel=0.05)
    assert sr90.half_life_seconds == pytest.approx(28.8 * 365.25 * 24 * 3600, rel=0.05)
    assert i131.half_life_seconds == pytest.approx(8.02 * 24 * 3600, rel=0.05)
    assert xe135.half_life_seconds == pytest.approx(9.14 * 3600, rel=0.05)
    assert sm149.half_life_seconds > 1e15  # Effectively stable


def test_activation_products():
    """Test neutron activation products."""
    co60 = NUCLEAR_ENGINE.get_isotope(27, 60)
    fe55 = NUCLEAR_ENGINE.get_isotope(26, 55)
    ni63 = NUCLEAR_ENGINE.get_isotope(28, 63)

    assert co60.half_life_seconds == pytest.approx(5.27 * 365.25 * 24 * 3600, rel=0.05)
    assert fe55.half_life_seconds == pytest.approx(2.73 * 365.25 * 24 * 3600, rel=0.05)
    assert ni63.half_life_seconds == pytest.approx(100.1 * 365.25 * 24 * 3600, rel=0.1)


def test_superheavy_elements():
    """Test superheavy elements (Z > 100) have predicted properties."""
    # Flerovium (Fl, Z=114)
    fl289 = NUCLEAR_ENGINE.get_isotope(114, 289)
    assert fl289 is not None
    assert fl289.z == 114
    assert fl289.a == 289
    assert fl289.is_superheavy is True
    assert fl289.predicted_chemistry is not None
    assert "relativistic" in fl289.predicted_chemistry.lower()

    # Livermorium (Lv, Z=116)
    lv293 = NUCLEAR_ENGINE.get_isotope(116, 293)
    assert lv293 is not None
    assert lv293.predicted_chemistry is not None

    # Oganesson (Og, Z=118)
    og294 = NUCLEAR_ENGINE.get_isotope(118, 294)
    assert og294 is not None


def test_isotope_decay_modes():
    """Test decay modes are correctly assigned."""
    u238 = NUCLEAR_ENGINE.get_isotope(92, 238)
    assert DecayMode.ALPHA in u238.decay_modes

    cs137 = NUCLEAR_ENGINE.get_isotope(55, 137)
    assert DecayMode.BETA_MINUS in cs137.decay_modes

    # Positron emitter
    f18 = NUCLEAR_ENGINE.get_isotope(9, 18)
    assert DecayMode.BETA_PLUS in f18.decay_modes or DecayMode.EC in f18.decay_modes

    # Gamma emitter (metastable)
    tc99m = NUCLEAR_ENGINE.get_isotope(43, 99, metastable=True)
    if tc99m:
        assert DecayMode.GAMMA in tc99m.decay_modes


def test_isotope_gamma_energies():
    """Test gamma ray energies are populated."""
    co60 = NUCLEAR_ENGINE.get_isotope(27, 60)
    assert len(co60.gamma_energies_mev) > 0
    # Co-60 has prominent gammas at 1.17 and 1.33 MeV
    assert any(abs(e - 1.173) < 0.01 for e in co60.gamma_energies_mev)
    assert any(abs(e - 1.333) < 0.01 for e in co60.gamma_energies_mev)


def test_isotope_chemical_properties():
    """Test chemical properties for key isotopes."""
    u238 = NUCLEAR_ENGINE.get_isotope(92, 238)
    assert u238.oxidation_states == [3, 4, 5, 6]
    assert u238.common_compounds is not None
    assert "UO2" in u238.common_compounds or "UO2(NO3)2" in u238.common_compounds

    # Uranyl ion properties
    assert u238.uranyl_fluorescence is True
    assert u238.uranyl_color == "green"


# ============================================================================
# Half-Life and Activity Calculations
# ============================================================================

def test_half_life_calculations():
    """Test half-life to decay constant conversion."""
    u238 = NUCLEAR_ENGINE.get_isotope(92, 238)
    lambda_u238 = NUCLEAR_ENGINE.decay_constant(u238)
    expected_lambda = math.log(2) / u238.half_life_seconds
    assert lambda_u238 == pytest.approx(expected_lambda, rel=1e-10)


def test_activity_becquerel():
    """Test activity calculation in Becquerel."""
    # 1 mole of U-238
    u238 = NUCLEAR_ENGINE.get_isotope(92, 238)
    activity_bq = NUCLEAR_ENGINE.activity_bq(u238, moles=1.0)
    expected = math.log(2) / u238.half_life_seconds * 6.02214076e23
    assert activity_bq == pytest.approx(expected, rel=1e-10)


def test_activity_curie():
    """Test activity calculation in Curie."""
    u238 = NUCLEAR_ENGINE.get_isotope(92, 238)
    activity_ci = NUCLEAR_ENGINE.activity_ci(u238, moles=1.0)
    expected_ci = (math.log(2) / u238.half_life_seconds * 6.02214076e23) / 3.7e10
    assert activity_ci == pytest.approx(expected_ci, rel=1e-10)


def test_specific_activity():
    """Test specific activity (Bq/g)."""
    co60 = NUCLEAR_ENGINE.get_isotope(27, 60)
    spec_act = NUCLEAR_ENGINE.specific_activity_bq_g(co60)
    # Co-60 specific activity ~ 1.13e15 Bq/g
    assert spec_act == pytest.approx(1.13e15, rel=0.1)


def test_decay_heat():
    """Test decay heat calculation (W/g)."""
    pu238 = NUCLEAR_ENGINE.get_isotope(94, 238)
    heat = NUCLEAR_ENGINE.decay_heat_w_g(pu238)
    # Pu-238 decay heat ~ 0.57 W/g
    assert heat == pytest.approx(0.57, rel=0.1)

    cs137 = NUCLEAR_ENGINE.get_isotope(55, 137)
    heat_cs = NUCLEAR_ENGINE.decay_heat_w_g(cs137)
    # Cs-137 decay heat ~ 0.42 W/g (including Ba-137m)
    assert heat_cs == pytest.approx(0.42, rel=0.2)


def test_time_evolution():
    """Test isotope decay over time."""
    i131 = NUCLEAR_ENGINE.get_isotope(53, 131)
    initial_moles = 1.0
    # After one half-life (8.02 days), should have 0.5 moles
    remaining = NUCLEAR_ENGINE.remaining_moles(i131, initial_moles, 8.02 * 24 * 3600)
    assert remaining == pytest.approx(0.5, rel=0.01)

    # After two half-lives
    remaining2 = NUCLEAR_ENGINE.remaining_moles(i131, initial_moles, 16.04 * 24 * 3600)
    assert remaining2 == pytest.approx(0.25, rel=0.01)


# ============================================================================
# Decay Chains
# ============================================================================

def test_u238_decay_chain():
    """Test U-238 decay chain (U-238 -> Th-234 -> Pa-234 -> U-234 -> ... -> Pb-206)."""
    chain = NUCLEAR_ENGINE.get_decay_chain(92, 238)
    assert chain is not None
    assert chain.parent_isotope.z == 92
    assert chain.parent_isotope.a == 238
    assert len(chain.steps) >= 10

    # Verify key daughters
    daughter_symbols = [step.daughter.symbol + str(step.daughter.a) for step in chain.steps]
    assert "Th-234" in daughter_symbols
    assert "Pa-234" in daughter_symbols
    assert "U-234" in daughter_symbols
    assert "Th-230" in daughter_symbols
    assert "Ra-226" in daughter_symbols
    assert "Rn-222" in daughter_symbols
    assert "Pb-206" in daughter_symbols


def test_u235_decay_chain():
    """Test U-235 decay chain (Actinium series -> Pb-207)."""
    chain = NUCLEAR_ENGINE.get_decay_chain(92, 235)
    assert chain is not None
    daughter_symbols = [step.daughter.symbol + str(step.daughter.a) for step in chain.steps]
    assert "Th-231" in daughter_symbols
    assert "Pa-231" in daughter_symbols
    assert "Ac-227" in daughter_symbols
    assert "Pb-207" in daughter_symbols


def test_th232_decay_chain():
    """Test Th-232 decay chain (Thorium series -> Pb-208)."""
    chain = NUCLEAR_ENGINE.get_decay_chain(90, 232)
    assert chain is not None
    daughter_symbols = [step.daughter.symbol + str(step.daughter.a) for step in chain.steps]
    assert "Ra-228" in daughter_symbols
    assert "Ac-228" in daughter_symbols
    assert "Th-228" in daughter_symbols
    assert "Ra-224" in daughter_symbols
    assert "Rn-220" in daughter_symbols
    assert "Pb-208" in daughter_symbols


def test_decay_chain_activity_equilibrium():
    """Test secular equilibrium in decay chain."""
    # For U-238 chain, after long time all daughters reach same activity as parent
    chain = NUCLEAR_ENGINE.get_decay_chain(92, 238)
    activities = NUCLEAR_ENGINE.decay_chain_activities(chain, moles_parent=1.0, time_seconds=1e15)
    # All activities should be ~equal in secular equilibrium
    parent_act = activities[0]
    for act in activities[1:]:
        assert act == pytest.approx(parent_act, rel=0.01)


# ============================================================================
# Shielding Calculations (HVL, TVL)
# ============================================================================

def test_shielding_hvl_lead():
    """Test Half-Value Layer for lead."""
    co60 = NUCLEAR_ENGINE.get_isotope(27, 60)
    hvl = NUCLEAR_ENGINE.hvl(ShieldingMaterial.LEAD, co60.gamma_energies_mev[0])
    # HVL for 1.25 MeV gamma in lead ~ 1.2 cm
    assert hvl == pytest.approx(1.2, rel=0.2)


def test_shielding_hvl_concrete():
    """Test HVL for concrete."""
    cs137 = NUCLEAR_ENGINE.get_isotope(55, 137)
    hvl = NUCLEAR_ENGINE.hvl(ShieldingMaterial.CONCRETE, 0.662)  # Cs-137 662 keV
    # HVL for 662 keV in concrete ~ 4.5 cm
    assert hvl == pytest.approx(4.5, rel=0.2)


def test_shielding_hvl_water():
    """Test HVL for water."""
    hvl = NUCLEAR_ENGINE.hvl(ShieldingMaterial.WATER, 1.0)
    # HVL for 1 MeV in water ~ 18 cm
    assert hvl == pytest.approx(18.0, rel=0.2)


def test_shielding_tvl():
    """Test Tenth-Value Layer (TVL = HVL * log2(10) ≈ HVL * 3.32)."""
    co60 = NUCLEAR_ENGINE.get_isotope(27, 60)
    hvl = NUCLEAR_ENGINE.hvl(ShieldingMaterial.LEAD, co60.gamma_energies_mev[0])
    tvl = NUCLEAR_ENGINE.tvl(ShieldingMaterial.LEAD, co60.gamma_energies_mev[0])
    assert tvl == pytest.approx(hvl * 3.3219, rel=0.01)


def test_shielding_attenuation():
    """Test gamma attenuation through shielding."""
    co60 = NUCLEAR_ENGINE.get_isotope(27, 60)
    energy = co60.gamma_energies_mev[0]
    # 5 cm lead should attenuate by ~ (1/2)^(5/1.2) ≈ 0.05
    attenuation = NUCLEAR_ENGINE.gamma_attenuation(ShieldingMaterial.LEAD, energy, 5.0)
    assert attenuation == pytest.approx(0.05, rel=0.5)


# ============================================================================
# Criticality Safety
# ============================================================================

def test_k_effective_calculation():
    """Test k-effective calculation for simple geometry."""
    # Bare sphere of U-235 (Godiva-like)
    k_eff = NUCLEAR_ENGINE.k_effective(
        fuel_isotope=NUCLEAR_ENGINE.get_isotope(92, 235),
        mass_kg=50.0,
        density_g_cm3=18.7,
        reflector=None,
        geometry="sphere",
    )
    # Godiva critical mass ~ 50 kg, k_eff ~ 1.0
    assert 0.95 <= k_eff <= 1.05


def test_critical_mass():
    """Test critical mass calculation."""
    crit_mass = NUCLEAR_ENGINE.critical_mass(
        NUCLEAR_ENGINE.get_isotope(92, 235),
        density_g_cm3=18.7,
        reflector="natural_uranium",
        geometry="sphere",
    )
    # U-235 with U reflector ~ 15-16 kg
    assert 14.0 <= crit_mass <= 18.0


def test_neutron_flux():
    """Test neutron flux calculation."""
    pu239 = NUCLEAR_ENGINE.get_isotope(94, 239)
    flux = NUCLEAR_ENGINE.neutron_flux(
        fuel_isotope=pu239,
        power_mw=1000.0,
        core_volume_m3=20.0,
    )
    # Typical PWR flux ~ 1e14 n/cm2/s
    assert 1e13 <= flux <= 1e15


def test_subcritical_multiplication():
    """Test subcritical multiplication factor."""
    k_eff = 0.95
    source_strength = 1e6  # n/s
    mult = NUCLEAR_ENGINE.subcritical_multiplication(k_eff, source_strength)
    # M = 1 / (1 - k_eff) = 20
    assert mult == pytest.approx(20.0, rel=0.01)


# ============================================================================
# Isotope Production (Neutron Activation)
# ============================================================================

def test_neutron_activation():
    """Test isotope production via neutron activation."""
    # Co-59 -> Co-60
    co59 = NUCLEAR_ENGINE.get_isotope(27, 59)
    co60_production = NUCLEAR_ENGINE.activation_rate(
        target_isotope=co59,
        neutron_flux=1e14,  # n/cm2/s
        cross_section_barns=37.0,  # Co-59 capture cross section
        target_mass_g=10.0,
    )
    # Production rate in atoms/s
    expected = 1e14 * 37e-24 * (10.0 / 58.93) * 6.022e23
    assert co60_production == pytest.approx(expected, rel=0.1)


def test_activation_with_decay():
    """Test activation with simultaneous decay (saturation)."""
    co59 = NUCLEAR_ENGINE.get_isotope(27, 59)
    co60 = NUCLEAR_ENGINE.get_isotope(27, 60)
    saturation_activity = NUCLEAR_ENGINE.saturation_activity(
        target_isotope=co59,
        product_isotope=co60,
        neutron_flux=1e14,
        cross_section_barns=37.0,
        target_mass_g=10.0,
    )
    # Should approach production rate at saturation
    prod_rate = NUCLEAR_ENGINE.activation_rate(co59, 1e14, 37.0, 10.0)
    assert saturation_activity == pytest.approx(prod_rate, rel=0.01)


# ============================================================================
# Fission Product Yields
# ============================================================================

def test_fission_yields_u235_thermal():
    """Test U-235 thermal fission product yields."""
    yields = NUCLEAR_ENGINE.fission_yields(92, 235, "thermal")
    # Sum of yields should be ~200% (two fission fragments per fission)
    total = sum(yields.values())
    assert 1.95 <= total <= 2.05

    # Check key fission products
    assert yields.get((55, 137), 0) > 0.05  # Cs-137 ~ 6%
    assert yields.get((38, 90), 0) > 0.05   # Sr-90 ~ 5%
    assert yields.get((54, 135), 0) > 0.05  # Xe-135 ~ 6%
    assert yields.get((62, 149), 0) > 0.005 # Sm-149 ~ 1%


def test_fission_yields_pu239_thermal():
    """Test Pu-239 thermal fission product yields."""
    yields = NUCLEAR_ENGINE.fission_yields(94, 239, "thermal")
    total = sum(yields.values())
    assert 1.95 <= total <= 2.05


def test_fission_yields_u235_fast():
    """Test U-235 fast fission product yields."""
    yields = NUCLEAR_ENGINE.fission_yields(92, 235, "fast")
    total = sum(yields.values())
    assert 1.95 <= total <= 2.05


# ============================================================================
# Spent Fuel Composition
# ============================================================================

def test_spent_fuel_composition_pwr():
    """Test PWR spent fuel composition after typical burnup."""
    composition = NUCLEAR_ENGINE.spent_fuel_composition(
        reactor_type=ReactorType.PWR,
        burnup_mwd_kg=45.0,  # Typical PWR discharge burnup
        initial_enrichment=0.045,  # 4.5% U-235
        cooling_time_years=5.0,
    )
    # Check major actinides
    assert composition["U-235"] < 0.01  # Depleted
    assert composition["U-238"] > 0.90
    assert composition["Pu-239"] > 0.005
    assert composition["Pu-240"] > 0.002

    # Check fission products
    assert composition["Cs-137"] > 0.001
    assert composition["Sr-90"] > 0.001
    assert composition["Xe-135"] < 1e-6  # Decayed away


def test_spent_fuel_decay_heat():
    """Test spent fuel decay heat over time."""
    composition = NUCLEAR_ENGINE.spent_fuel_composition(
        reactor_type=ReactorType.PWR,
        burnup_mwd_kg=45.0,
        initial_enrichment=0.045,
        cooling_time_years=1.0,
    )
    heat = NUCLEAR_ENGINE.spent_fuel_decay_heat(composition)
    # ~1 kW/tonne after 1 year for 45 MWd/kg
    assert 0.5 <= heat <= 2.0


# ============================================================================
# Radioactive Glow Phenomena
# ============================================================================

def test_cherenkov_radiation():
    """Test Cherenkov radiation calculation."""
    # Water, beta energy > threshold
    threshold = NUCLEAR_ENGINE.cherenkov_threshold_energy("water")
    assert threshold == pytest.approx(0.26, rel=0.1)  # MeV for water (n=1.33)

    # Light yield per MeV
    yield_per_mev = NUCLEAR_ENGINE.cherenkov_light_yield("water", 2.0)  # 2 MeV electron
    assert yield_per_mev > 0


def test_radioluminescence():
    """Test radioluminescence (ZnS:Cu, radioluminescent paint)."""
    # Alpha particles on ZnS:Cu
    light_output = NUCLEAR_ENGINE.radioluminescence_light(
        phosphor="ZnS:Cu",
        radiation_type="alpha",
        energy_mev=5.0,
        activity_bq=3.7e10,  # 1 Ci
    )
    assert light_output > 0


def test_actinide_self_glow():
    """Test actinide self-glow (radioluminescence from intense alpha)."""
    pu238 = NUCLEAR_ENGINE.get_isotope(94, 238)
    glow = NUCLEAR_ENGINE.actinide_self_glow(pu238, mass_g=100.0)
    # Pu-238 100g should produce visible glow
    assert glow["visible"] is True
    assert glow["color"] == "blue-white"


# ============================================================================
# Uranyl Chemistry
# ============================================================================

def test_uranyl_properties():
    """Test uranyl ion (UO2^2+) properties."""
    props = NUCLEAR_ENGINE.uranyl_properties()
    assert props["fluorescence_color"] == "green"
    assert props["fluorescence_wavelength_nm"] == pytest.approx(500, rel=0.1)
    assert props["oxidation_state"] == 6
    assert "UO2(NO3)2" in props["common_compounds"]
    assert "UO2(NO3)2·6H2O" in props["common_compounds"]  # Uranyl nitrate hexahydrate
    assert "studtite" in props["minerals"]  # Uranyl peroxide


def test_uranyl_fluorescence():
    """Test uranyl green fluorescence simulation."""
    fluorescence = NUCLEAR_ENGINE.uranyl_fluorescence(
        concentration_mmol_l=1.0,
        excitation_wavelength_nm=420.0,
    )
    assert fluorescence["emission_peak_nm"] == pytest.approx(500, rel=0.05)
    assert fluorescence["quantum_yield"] > 0


# ============================================================================
# Nuclear Reactor Simulation
# ============================================================================

def test_pwr_thermal_hydraulics():
    """Test PWR thermal-hydraulics."""
    state = NUCLEAR_ENGINE.pwr_thermal_hydraulics(
        power_mw=3000.0,
        primary_flow_kg_s=15000.0,
        primary_inlet_temp_c=290.0,
        primary_pressure_mpa=15.5,
    )
    assert state["primary_outlet_temp_c"] > state["primary_inlet_temp_c"]
    assert state["primary_outlet_temp_c"] == pytest.approx(325.0, rel=0.05)
    assert state["steam_quality"] >= 0.0


def test_bwr_thermal_hydraulics():
    """Test BWR thermal-hydraulics."""
    state = NUCLEAR_ENGINE.bwr_thermal_hydraulics(
        power_mw=3000.0,
        core_flow_kg_s=10000.0,
        feedwater_temp_c=215.0,
        dome_pressure_mpa=7.0,
    )
    assert state["core_exit_quality"] > 0.1
    assert state["core_exit_quality"] < 0.3


def test_fuel_depletion():
    """Test fuel depletion over burnup."""
    initial = {"U-235": 0.045, "U-238": 0.955}
    depleted = NUCLEAR_ENGINE.fuel_depletion(
        initial_composition=initial,
        burnup_mwd_kg=45.0,
        reactor_type=ReactorType.PWR,
    )
    assert depleted["U-235"] < 0.01
    assert depleted["Pu-239"] > 0.005
    assert depleted["Pu-240"] > 0.002


def test_control_rod_worth():
    """Test control rod worth calculation."""
    worth = NUCLEAR_ENGINE.control_rod_worth(
        reactor_type=ReactorType.PWR,
        rod_type="Ag-In-Cd",
        insertion_percent=100.0,
        core_state="hot_zero_power",
    )
    # Typical PWR rod worth ~ 5000-10000 pcm
    assert 3000 <= worth <= 15000


def test_xenon_poisoning():
    """Test xenon-135 poisoning dynamics."""
    # Start from equilibrium
    xe135_eq = NUCLEAR_ENGINE.xenon_equilibrium(flux_n_cm2_s=1e14)
    # After reactor shutdown, xenon peaks at ~10 hours
    xe135_peak = NUCLEAR_ENGINE.xenon_transient(
        initial_xe135=xe135_eq,
        initial_i135=xe135_eq * 0.1,
        flux_n_cm2_s=0.0,  # Shutdown
        time_hours=10.0,
    )
    assert xe135_peak > xe135_eq * 2  # Peak is 2-3x equilibrium


def test_scram_simulation():
    """Test reactor scram (emergency shutdown) simulation."""
    result = NUCLEAR_ENGINE.scram_simulation(
        reactor_type=ReactorType.PWR,
        initial_power_mw=3000.0,
        rod_insertion_time_s=2.0,
        scram_worth_pcm=10000.0,
    )
    assert result["shutdown_margin_pcm"] > 0
    assert result["peak_power_ratio"] < 1.1  # No power excursion


# ============================================================================
# Reprocessing (PUREX)
# ============================================================================

def test_purex_separation():
    """Test PUREX process U/Pu separation."""
    feed = {
        "U": 0.95,
        "Pu": 0.01,
        "FP": 0.04,  # Fission products
    }
    result = NUCLEAR_ENGINE.purex_separation(
        feed_composition=feed,
        stages_extraction=12,
        stages_scrubbing=4,
        stages_stripping=8,
        tbp_concentration=0.3,  # 30% TBP in kerosene
        aqueous_flow=1.0,
        organic_flow=1.0,
    )
    # U product should be > 99.9% pure
    assert result["uranium_product"]["U"] > 0.999
    assert result["uranium_product"]["Pu"] < 1e-6
    # Pu product should be > 99.9% pure
    assert result["plutonium_product"]["Pu"] > 0.999
    assert result["plutonium_product"]["U"] < 0.001
    # Fission products go to waste
    assert result["waste"]["FP"] > 0.95


def test_purex_extraction_coefficients():
    """Test PUREX extraction coefficients for U and Pu."""
    # U(VI) extracts strongly at high acidity
    d_u = NUCLEAR_ENGINE.purex_distribution_coefficient("U", acidity_m=3.0, tbp_fraction=0.3)
    assert d_u > 10.0

    # Pu(IV) extracts strongly
    d_pu4 = NUCLEAR_ENGINE.purex_distribution_coefficient("Pu4", acidity_m=3.0, tbp_fraction=0.3)
    assert d_pu4 > 10.0

    # Pu(VI) does not extract well
    d_pu6 = NUCLEAR_ENGINE.purex_distribution_coefficient("Pu6", acidity_m=3.0, tbp_fraction=0.3)
    assert d_pu6 < 1.0

    # Fission products don't extract
    d_fp = NUCLEAR_ENGINE.purex_distribution_coefficient("FP", acidity_m=3.0, tbp_fraction=0.3)
    assert d_fp < 0.1


# ============================================================================
# Integration Tests
# ============================================================================

def test_complete_fuel_cycle():
    """Test complete fuel cycle: fresh fuel -> depletion -> cooling -> reprocessing."""
    # Fresh PWR fuel
    fresh = {"U-235": 0.045, "U-238": 0.955}

    # Deplete to 45 MWd/kg
    depleted = NUCLEAR_ENGINE.fuel_depletion(fresh, 45.0, ReactorType.PWR)

    # Cool for 5 years
    cooled = NUCLEAR_ENGINE.cool_fuel(depleted, cooling_years=5.0)

    # Reprocess
    repro = NUCLEAR_ENGINE.purex_separation(
        feed_composition={
            "U": cooled.get("U-235", 0) + cooled.get("U-238", 0),
            "Pu": sum(v for k, v in cooled.items() if k.startswith("Pu-")),
            "FP": sum(v for k, v in cooled.items() if not k.startswith("U-") and not k.startswith("Pu-")),
        },
        stages_extraction=12,
        stages_scrubbing=4,
        stages_stripping=8,
        tbp_concentration=0.3,
    )

    # Verify recovered U and Pu are pure
    assert repro["uranium_product"]["U"] > 0.99
    assert repro["plutonium_product"]["Pu"] > 0.99


def test_radiological_source_term():
    """Test radiological source term for accident analysis."""
    composition = NUCLEAR_ENGINE.spent_fuel_composition(
        ReactorType.PWR, 45.0, 0.045, 1.0
    )
    source_term = NUCLEAR_ENGINE.radiological_source_term(
        fuel_composition=composition,
        release_fractions={
            "noble_gases": 1.0,
            "iodine": 0.1,
            "cesium": 0.01,
            "strontium": 0.001,
            "actinides": 0.0001,
        },
    )
    assert source_term["I-131_bq"] > 0
    assert source_term["Cs-137_bq"] > 0
    assert source_term["Xe-133_bq"] > 0


# ============================================================================
# Edge Cases and Validation
# ============================================================================

def test_unknown_isotope_raises():
    """Test that unknown isotope raises appropriate error."""
    with pytest.raises(KeyError):
        NUCLEAR_ENGINE.get_isotope(999, 999)


def test_invalid_shielding_material():
    """Test invalid shielding material raises error."""
    with pytest.raises(ValueError):
        NUCLEAR_ENGINE.hvl("unobtainium", 1.0)


def test_negative_mass_raises():
    """Test negative mass raises error."""
    u235 = NUCLEAR_ENGINE.get_isotope(92, 235)
    with pytest.raises(ValueError):
        NUCLEAR_ENGINE.activity_bq(u235, moles=-1.0)


def test_zero_time_decay():
    """Test decay at time zero returns initial amount."""
    i131 = NUCLEAR_ENGINE.get_isotope(53, 131)
    remaining = NUCLEAR_ENGINE.remaining_moles(i131, 1.0, 0.0)
    assert remaining == 1.0


def test_infinite_time_decay():
    """Test decay at infinite time returns zero."""
    i131 = NUCLEAR_ENGINE.get_isotope(53, 131)
    remaining = NUCLEAR_ENGINE.remaining_moles(i131, 1.0, float('inf'))
    assert remaining == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])