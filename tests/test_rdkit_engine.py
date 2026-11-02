"""
Unit and integration tests for RDKit Cheminformatics & 3D Conformer Generator.
"""

import pytest

from chemlab.simulation.rdkit_engine import RDKIT_ENGINE, RDKitCheminformaticsEngine


def test_rdkit_engine_singleton():
    assert isinstance(RDKIT_ENGINE, RDKitCheminformaticsEngine)


def test_aspirin_3d_generation():
    """Validates 3D conformer and descriptors for Acetylsalicylic acid."""
    smiles = "CC(=O)Oc1ccccc1C(=O)O"
    props = RDKIT_ENGINE.smiles_to_3d_molecule(smiles, name="Aspirin")

    assert props is not None
    assert props.formula == "C9H8O4"
    assert 180.0 <= props.molecular_weight <= 180.2
    assert props.lipinski_rule_of_five_pass is True
    assert props.atom_count == 21  # 13 heavy atoms + 8 hydrogens
    assert "ATOM" in props.pdb_block or "HETATM" in props.pdb_block
    assert "$$$$" in props.sdf_block or "M  END" in props.sdf_block


def test_paracetamol_3d_generation():
    """Validates Paracetamol (Acetaminophen) structure."""
    smiles = "CC(=O)Nc1ccc(O)cc1"
    props = RDKIT_ENGINE.smiles_to_3d_molecule(smiles, name="Paracetamol")

    assert props is not None
    assert props.formula == "C8H9NO2"
    assert 151.1 <= props.molecular_weight <= 151.2
    assert props.num_h_donors == 2  # Phenol OH + Amide NH
    assert props.num_h_acceptors == 2


def test_caffeine_3d_generation():
    """Validates Caffeine structure."""
    smiles = "Cn1cnc2c1c(=O)n(c(=O)n2C)C"
    props = RDKIT_ENGINE.smiles_to_3d_molecule(smiles, name="Caffeine")

    assert props is not None
    assert props.formula == "C8H10N4O2"
    assert 194.1 <= props.molecular_weight <= 194.3
    assert props.num_h_donors == 0
    assert props.num_aromatic_rings >= 1


def test_invalid_smiles_returns_none():
    props = RDKIT_ENGINE.smiles_to_3d_molecule("INVALID_SMILES_STRING_123")
    assert props is None
