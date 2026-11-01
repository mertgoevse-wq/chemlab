"""
Unit tests for the ChemLab Omniroute / Local AI Reaction Solver Bridge.
Tests local endpoint connectivity (localhost:20128), schema prediction,
deterministic fallback chemistry, Arrhenius time-dilation, and synthesis factor calculation.
"""

from __future__ import annotations

import pytest

from chemlab.ai.omniroute_bridge import (
    ChemicalReactionPrediction,
    LocalReactionAIBridge,
    ReactionFactorRequest,
)
from chemlab.models import LiquidMixture


def test_reaction_prediction_dataclass() -> None:
    pred = ChemicalReactionPrediction(
        reaction_name="Esterification",
        balanced_equation="Salicylic Acid + Acetic Anhydride -> Aspirin + Acetic Acid",
        products={"aspirin": 0.05, "acetic_acid": 0.05},
        enthalpy_kj_mol=-18.4,
        activation_energy_kj_mol=42.0,
        rate_constant_k=0.045,
        target_color_rgb=(0.95, 0.95, 0.98),
        produces_gas=False,
        precipitate_formed=True,
        emission_glow=0.0,
        safety_warnings=["Exothermer Reaktionsansatz. Schutzbrille tragen."],
    )
    assert pred.is_exothermic
    assert pred.precipitate_formed
    assert "aspirin" in pred.products


def test_offline_deterministic_fallback_acid_base() -> None:
    bridge = LocalReactionAIBridge(endpoint="http://127.0.0.1:20128/v1", model="kc/kilo-auto/free")
    req = ReactionFactorRequest(
        reagents=["hcl", "naoh"],
        temperature_c=22.0,
        pressure_atm=1.0,
        volume_ml=100.0,
    )
    pred = bridge.predict_reaction(req)
    assert pred.reaction_name == "Säure-Base-Neutralisation"
    assert pred.enthalpy_kj_mol < 0.0  # Exotherm
    assert pred.is_exothermic
    assert "nacl" in pred.products
    assert pred.target_color_rgb == (0.15, 0.82, 0.25)  # Neutral green with indicator


def test_offline_deterministic_fallback_aspirin_synthesis() -> None:
    bridge = LocalReactionAIBridge()
    req = ReactionFactorRequest(
        reagents=["salicylic_acid", "acetic_anhydride", "h2so4"],
        temperature_c=65.0,
        pressure_atm=1.0,
        volume_ml=150.0,
    )
    pred = bridge.predict_reaction(req)
    assert "Aspirin" in pred.reaction_name
    assert "aspirin" in pred.products
    assert pred.precipitate_formed  # Crystallization on cooling


def test_arrhenius_time_dilation_integration() -> None:
    bridge = LocalReactionAIBridge()
    mixture = LiquidMixture(
        volume_ml=100.0,
        temperature_c=25.0,
        reagent_moles={"salicylic_acid": 0.05, "acetic_anhydride": 0.06, "h2so4": 0.005},
    )
    # Step simulation with 10x time dilation
    updated, pred = bridge.step_with_time_dilation(mixture, dt_s=1.0, time_dilation=10.0)
    assert updated.temperature_c >= 25.0
    assert "aspirin" in updated.reagent_moles
    assert updated.reagent_moles["aspirin"] > 0.0


def test_unreactive_mixture_fallback() -> None:
    bridge = LocalReactionAIBridge()
    req = ReactionFactorRequest(
        reagents=["water", "nacl"],
        temperature_c=20.0,
        pressure_atm=1.0,
        volume_ml=100.0,
    )
    pred = bridge.predict_reaction(req)
    assert pred.reaction_name == "Keine Reaktion (Lösung/Suspension)"
    assert pred.enthalpy_kj_mol == 0.0
    assert not pred.produces_gas
