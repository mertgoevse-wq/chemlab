"""
Unit tests for the ChemLab Precursor & Starting Material Synthesis Engine.
Tests complete retrosynthetic ancestor generation, including Benzaldehyde,
Nitroethane, 4-Aminophenol, Indole, and Salicylic Acid from base feedstocks.
"""

from __future__ import annotations

import pytest

from chemlab.simulation.precursor_synthesis import (
    PrecursorPathway,
    PrecursorRegistry,
    ReactionStep,
)


def test_precursor_registry_contains_fundamental_feedstocks() -> None:
    registry = PrecursorRegistry()
    available = registry.list_precursors()

    assert "benzaldehyde" in available
    assert "nitroethane" in available
    assert "aminophenol" in available
    assert "indole" in available
    assert "salicylic_acid" in available


def test_benzaldehyde_synthesis_from_toluene() -> None:
    registry = PrecursorRegistry()
    pathway = registry.get_pathway("benzaldehyde")

    assert pathway.target_compound == "Benzaldehyd"
    assert pathway.primary_feedstock == "Toluol"
    assert len(pathway.steps) >= 2
    # Step 1: Side-chain chlorination, Step 2: Hydrolysis
    assert any("Chlorierung" in step.name or "Oxidation" in step.name for step in pathway.steps)
    assert any("Hydrolyse" in step.name for step in pathway.steps)


def test_salicylic_acid_kolbe_schmitt_carboxylation() -> None:
    registry = PrecursorRegistry()
    pathway = registry.get_pathway("salicylic_acid")

    assert pathway.target_compound == "Salicylsäure"
    assert pathway.primary_feedstock == "Phenol"
    # Kolbe-Schmitt involves CO2 and NaOH
    kolbe_step = next(s for s in pathway.steps if "Kolbe-Schmitt" in s.name)
    assert "co2" in kolbe_step.reagents
    assert kolbe_step.pressure_bar > 1.0


def test_nitroethane_nucleophilic_substitution() -> None:
    registry = PrecursorRegistry()
    pathway = registry.get_pathway("nitroethane")

    assert pathway.target_compound == "Nitroethan"
    assert "Bromoethan" in pathway.primary_feedstock or "Ethylbromid" in pathway.primary_feedstock
    assert any("nanot2" in s.reagents or "nano2" in s.reagents for s in pathway.steps)


def test_indole_fischer_synthesis() -> None:
    registry = PrecursorRegistry()
    pathway = registry.get_pathway("indole")

    assert pathway.target_compound == "Indol"
    fischer_step = next(s for s in pathway.steps if "Fischer" in s.name)
    assert "phenylhydrazine" in fischer_step.reagents
    assert fischer_step.acid_catalyst == "zncl2" or fischer_step.acid_catalyst == "h2so4"
