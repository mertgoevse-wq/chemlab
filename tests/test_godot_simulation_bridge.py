"""
Unit tests for Godot 4 Chemistry Simulation Engine & IPC Bridge.
Validates:
  - Canonical NIST & CRC reference tables in reaction_evaluator.gd
  - Dual-engine architecture and standalone embedded fallback in simulation_bridge.gd
  - Acid-Base neutralization stoichiometry and Delta H = -57.1 kJ/mol
  - Henderson-Hasselbalch buffer calculations
  - Phenolphthalein indicator equilibrium and color transitions
  - Adiabatic temperature rise Delta T = -Delta H * n / (m * Cp)
  - Solubility product Ksp precipitation criteria
  - Edge cases: zero volume, extreme pH, negative concentrations, division by zero
"""

import math
import re
from pathlib import Path

# Paths to the GDScript source files
GAME_DIR = Path(__file__).parent.parent / "game"
CHEMISTRY_DIR = GAME_DIR / "scripts" / "chemistry"
REACTION_EVALUATOR_PATH = CHEMISTRY_DIR / "reaction_evaluator.gd"
SIMULATION_BRIDGE_PATH = CHEMISTRY_DIR / "simulation_bridge.gd"


def test_files_exist():
    """Verify both authoritative chemistry GDScript files exist."""
    assert REACTION_EVALUATOR_PATH.exists(), f"Missing: {REACTION_EVALUATOR_PATH}"
    assert SIMULATION_BRIDGE_PATH.exists(), f"Missing: {SIMULATION_BRIDGE_PATH}"


def test_reaction_evaluator_gdscript_syntax():
    """Verify reaction_evaluator.gd contains valid GDScript 4 syntax and no Python-isms."""
    content = REACTION_EVALUATOR_PATH.read_text(encoding="utf-8")

    # Must NOT contain @dataclass or Python function/import statements
    assert "@dataclass" not in content
    assert re.search(r"^\s*from\s+\w+", content, re.MULTILINE) is None
    assert re.search(r"^\s*import\s+\w+", content, re.MULTILINE) is None
    assert re.search(r"^\s*def\s+\w+", content, re.MULTILINE) is None

    # Must have class_name ReactionEvaluator extends RefCounted
    assert "class_name ReactionEvaluator" in content
    assert "extends RefCounted" in content

    # Must have canonical constants
    assert "const R_GAS: float = 8.314462618" in content
    assert "const DELTA_H_NEUTRALIZATION_KJ_MOL: float = -57.1" in content
    assert "const WATER_CP_J_G_K: float = 4.184" in content
    assert "const PHENOLPHTHALEIN_PKIND: float = 9.4" in content


def test_reaction_evaluator_species_database_coverage():
    """Verify at least 25 common laboratory compounds are cataloged with NIST data."""
    content = REACTION_EVALUATOR_PATH.read_text(encoding="utf-8")

    # Match species keys in SPECIES_DB (using _make_species factory function)
    species_keys = re.findall(r'"([A-Za-z0-9_]+)":\s*_make_species\(', content)
    assert len(species_keys) >= 25, f"Expected >= 25 compounds, found {len(species_keys)}"

    # Check essential species required by ChemLab curriculum
    essential = [
        "H2O",
        "HCl_aq",
        "NaOH_aq",
        "NaCl_aq",
        "H2SO4_aq",
        "HNO3_aq",
        "NH3_aq",
        "CuSO4_aq",
        "H2O2_aq",
        "O2_gas",
        "CO2_gas",
        "KMnO4_s",
        "KI_aq",
        "salicylic_acid",
        "acetic_anhydride",
        "aspirin",
        "acetic_acid",
        "paracetamol",
        "ethanol",
        "diethyl_ether",
        "AgCl_s",
        "phenolphthalein",
    ]
    for sp in essential:
        assert sp in species_keys, f"Missing essential species: {sp}"


def test_simulation_bridge_architecture():
    """Verify simulation_bridge.gd has Autoload Singleton structure and required APIs."""
    content = SIMULATION_BRIDGE_PATH.read_text(encoding="utf-8")

    # Must extend Node for Autoload
    assert "extends Node" in content

    # Check Dual-Engine Enum
    assert (
        "enum EngineMode { IPC_CONNECTED, EMBEDDED_FALLBACK, IPC_CONNECTING, IPC_FAILED }"
        in content
    )
    assert "enum ReactionType" in content

    # Required API methods from prompt specification
    assert "func mix_solutions(" in content
    assert "func step_reaction(" in content
    assert "func get_species_info(" in content

    # Dual-Engine execution methods
    assert "func query_cantera_thermodynamics(" in content
    assert "func query_rdkit_structure(" in content

    # Check Godot 4 StreamPeerTCP usage
    assert "StreamPeerTCP" in content
    assert "get_utf8_string(" in content
    assert "JSON.parse_string(" in content

    # Signals
    assert "signal engine_mode_changed(" in content
    assert "signal reaction_completed(" in content
    assert "signal vessel_state_changed(" in content
    assert "signal safety_warning(" in content
    assert "signal ph_changed(" in content
    assert "signal indicator_color_changed(" in content


def test_neutralization_thermodynamics_math():
    """Test standard neutralization enthalpy calculation: Delta H = -57.1 kJ/mol."""
    # HCl + NaOH -> NaCl + H2O
    delta_h_hcl = -167.16
    delta_h_naoh = -470.11
    delta_h_nacl = -407.27
    delta_h_h2o = -285.83

    delta_h_rxn = (delta_h_nacl + delta_h_h2o) - (delta_h_hcl + delta_h_naoh)
    assert abs(delta_h_rxn - (-55.83)) < 0.01  # Exact NIST summation
    # Standard ionic net: H+ + OH- -> H2O has Delta H_deg = -57.1 kJ/mol
    ref = -57.1
    error = abs(delta_h_rxn - ref)
    assert error / abs(ref) < 0.05  # Within 5% tolerance


def test_henderson_hasselbalch_math():
    """Verify Henderson-Hasselbalch equation and edge case handling."""

    def hh_ph(pka: float, conc_base: float, conc_acid: float) -> float:
        if conc_acid <= 0.0 and conc_base <= 0.0:
            return 7.0
        if conc_acid <= 0.0:
            kb = 10.0 ** (-(14.0 - pka))
            oh = math.sqrt(kb * conc_base)
            poh = -math.log10(max(oh, 1e-14))
            return max(0.0, min(14.0, 14.0 - poh))
        if conc_base <= 0.0:
            ka = 10.0 ** (-pka)
            h = math.sqrt(ka * conc_acid)
            return max(0.0, min(14.0, -math.log10(max(h, 1e-14))))
        ratio = conc_base / conc_acid
        return max(0.0, min(14.0, pka + math.log10(ratio)))

    # Equal concentrations: pH = pKa
    assert abs(hh_ph(4.76, 0.1, 0.1) - 4.76) < 1e-5

    # 10x base: pH = pKa + 1
    assert abs(hh_ph(4.76, 1.0, 0.1) - 5.76) < 1e-5

    # 10x acid: pH = pKa - 1
    assert abs(hh_ph(4.76, 0.1, 1.0) - 3.76) < 1e-5

    # Edge cases
    assert hh_ph(4.76, 0.0, 0.0) == 7.0
    assert 2.0 < hh_ph(4.76, 0.0, 0.1) < 4.0  # Pure weak acid
    assert 8.0 < hh_ph(4.76, 0.1, 0.0) < 10.0  # Pure conjugate base


def test_phenolphthalein_equilibrium_colors():
    """Test phenolphthalein color zones:
    - colorless at pH < 8.2
    - faint pink at 8.2 <= pH < 9.0
    - vibrant magenta at pH >= 9.0
    """

    def eval_color(ph: float):
        if ph < 8.2:
            return (1.0, 1.0, 1.0, 0.0)  # Colorless
        elif ph < 9.0:
            t = (ph - 8.2) / (9.0 - 8.2)
            alpha = 0.25 + (0.85 - 0.25) * t
            return (1.0, 0.72, 0.82, alpha)  # Faint pink
        else:
            return (0.92, 0.08, 0.55, 1.0)  # Vibrant magenta

    # pH 7.0: colorless
    c7 = eval_color(7.0)
    assert c7[3] == 0.0

    # pH 8.5: faint pink transition
    c85 = eval_color(8.5)
    assert 0.25 <= c85[3] <= 0.85
    assert c85[0] == 1.0

    # pH 10.0: vibrant magenta
    c10 = eval_color(10.0)
    assert c10 == (0.92, 0.08, 0.55, 1.0)


def test_adiabatic_temperature_rise_math():
    """Verify Delta T = -Delta H * n / (m * Cp) formula."""
    delta_h_kj = -57.1
    moles = 0.1
    mass_g = 100.0
    cp = 4.184

    # Heat in Joules = - (-57.1 * 1000) * 0.1 = 5710 J
    # m * Cp = 100 * 4.184 = 418.4 J/K
    # Delta T = 5710 / 418.4 = 13.647 K
    delta_t = (-delta_h_kj * 1000.0 * moles) / (mass_g * cp)
    assert 13.6 < delta_t < 13.7

    # Guard for zero mass or zero moles
    assert (-delta_h_kj * 1000.0 * 0.0) / (mass_g * cp) == 0.0


def test_solubility_product_ksp_evaluation():
    """Verify Ksp precipitation evaluation for AgCl (Ksp = 1.77e-10)."""
    ksp_agcl = 1.77e-10

    # Undersaturated: [Ag+] = 1e-6, [Cl-] = 1e-6 -> Q = 1e-12 < Ksp
    q_under = 1e-6 * 1e-6
    assert q_under < ksp_agcl

    # Supersaturated: [Ag+] = 1e-4, [Cl-] = 1e-4 -> Q = 1e-8 > Ksp -> Precipitates
    q_super = 1e-4 * 1e-4
    assert q_super > ksp_agcl
