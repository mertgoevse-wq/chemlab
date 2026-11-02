"""
Unit tests for the ChemLab Side-Reaction & Non-Ideal Impurity Engine.
Tests thermal runaway, tarring/polymerization, water-to-acid violent splashing,
missing catalyst penalties, and side-product yield calculation.
"""

from __future__ import annotations

import pytest

from chemlab.simulation.side_reactions import (
    ImpuritySeverity,
    ReactionConditionParameters,
    SideReactionAnalyzer,
)


def test_ideal_conditions_produce_negligible_impurities() -> None:
    analyzer = SideReactionAnalyzer()
    params = ReactionConditionParameters(
        reaction_id="aspirin_acylation",
        temperature_c=65.0,  # Optimal: 65 °C
        has_catalyst=True,
        addition_order_correct=True,
        stirring_rpm=400,
        reaction_time_s=60.0,
    )
    report = analyzer.evaluate_conditions(params)

    assert report.is_successful
    assert report.purity_percentage >= 95.0
    assert report.tarring_extent == 0.0
    assert len(report.impurities) == 0 or all(
        imp.severity == ImpuritySeverity.NEGLIGIBLE for imp in report.impurities
    )


def test_overheating_causes_thermal_degradation_and_tarring() -> None:
    analyzer = SideReactionAnalyzer()
    params = ReactionConditionParameters(
        reaction_id="aspirin_acylation",
        temperature_c=110.0,  # Severe overheating (target: 65 °C)
        has_catalyst=True,
        addition_order_correct=True,
        stirring_rpm=400,
        reaction_time_s=120.0,
    )
    report = analyzer.evaluate_conditions(params)

    assert not report.is_successful
    assert report.purity_percentage < 60.0
    assert report.tarring_extent > 0.4
    assert any("Polysalicylat" in imp.name or "Verharzung" in imp.name for imp in report.impurities)
    assert any("Überhitzung" in warn for warn in report.warnings)


def test_water_onto_concentrated_acid_triggers_violent_splash() -> None:
    analyzer = SideReactionAnalyzer()
    params = ReactionConditionParameters(
        reaction_id="acid_quenching",
        temperature_c=25.0,
        has_catalyst=True,
        addition_order_correct=False,  # Adding water to concentrated H2SO4!
        stirring_rpm=0,
        reaction_time_s=10.0,
    )
    report = analyzer.evaluate_conditions(params)

    assert report.violent_exotherm
    assert report.aerosol_splashing
    assert any("Erst das Wasser, dann die Säure" in warn for warn in report.warnings)


def test_missing_catalyst_leads_to_unreacted_starting_materials() -> None:
    analyzer = SideReactionAnalyzer()
    params = ReactionConditionParameters(
        reaction_id="aspirin_acylation",
        temperature_c=65.0,
        has_catalyst=False,  # Missing H2SO4 catalyst
        addition_order_correct=True,
        stirring_rpm=400,
        reaction_time_s=60.0,
    )
    report = analyzer.evaluate_conditions(params)

    assert report.unreacted_fraction > 0.65
    assert report.purity_percentage < 40.0
    assert any("Katalysator" in warn for warn in report.warnings)


def test_paracetamol_oxidation_under_aerobic_overheating() -> None:
    analyzer = SideReactionAnalyzer()
    params = ReactionConditionParameters(
        reaction_id="paracetamol_acylation",
        temperature_c=95.0,  # Overheating
        has_catalyst=True,
        addition_order_correct=True,
        stirring_rpm=100,
        reaction_time_s=180.0,
    )
    report = analyzer.evaluate_conditions(params)

    assert any("Benzochinon" in imp.name or "Diacetyl" in imp.name for imp in report.impurities)
    assert report.color_discoloration_rgb[0] < 0.6  # Dark brown/violet discoloration


def test_acetanilide_acylation_side_reactions() -> None:
    analyzer = SideReactionAnalyzer()
    # 1. Ideal conditions (60°C)
    ideal_p = ReactionConditionParameters(
        reaction_id="acetanilide_synthesis",
        temperature_c=60.0,
        has_catalyst=True,
    )
    ideal_rep = analyzer.evaluate_conditions(ideal_p)
    assert ideal_rep.is_successful is True
    assert ideal_rep.purity_percentage >= 90.0
    assert ideal_rep.tarring_extent == 0.0

    # 2. Overheating (125°C) -> Azobenzene & tar formation
    hot_p = ReactionConditionParameters(
        reaction_id="acetanilide_synthesis",
        temperature_c=125.0,
    )
    hot_rep = analyzer.evaluate_conditions(hot_p)
    assert hot_rep.is_successful is False
    assert any("Azobenzol" in imp.name for imp in hot_rep.impurities)
    assert hot_rep.tarring_extent > 0.1
