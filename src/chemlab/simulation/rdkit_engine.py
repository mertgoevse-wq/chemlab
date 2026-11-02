"""
ChemLab RDKit Cheminformatics & 3D Conformer Generator.
Converts SMILES strings into validated 3D molecular conformations,
computes physicochemical properties, and exports PDB/SDF blocks
for seamless visualization in Blender via MolecularNodes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Lipinski

logger = logging.getLogger("chemlab.simulation.rdkit_engine")


@dataclass
class MolecularProperties:
    """Physicochemical descriptors calculated from molecular graph."""

    smiles: str
    iupac_name: str
    formula: str
    molecular_weight: float
    exact_mass: float
    log_p: float  # Octanol-water partition coefficient
    tpsa: float  # Topological polar surface area
    num_rotatable_bonds: int
    num_h_donors: int
    num_h_acceptors: int
    num_heavy_atoms: int
    num_rings: int
    num_aromatic_rings: int
    lipinski_rule_of_five_pass: bool
    pdb_block: str = ""
    sdf_block: str = ""
    atom_count: int = 0


class RDKitCheminformaticsEngine:
    """Calculates molecular properties and generates 3D conformations using RDKit."""

    def __init__(self) -> None:
        pass

    def smiles_to_3d_molecule(
        self,
        smiles: str,
        name: str = "Compound",
        num_conformations: int = 1,
    ) -> MolecularProperties | None:
        """
        Parses SMILES, adds hydrogens, embeds 3D coordinates using Distance Geometry,
        optimizes geometry with the Universal Force Field (UFF), and calculates all descriptors.
        """
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.error("Failed to parse SMILES: %s", smiles)
                return None

            # Add explicit hydrogens for realistic 3D geometries
            mol_h = Chem.AddHs(mol)

            # Generate 3D Conformation via Distance Geometry (ETKDGv3)
            params = AllChem.ETKDGv3()
            params.randomSeed = 42
            conformer_ids = AllChem.EmbedMultipleConfs(
                mol_h, numConfs=num_conformations, params=params
            )

            if not conformer_ids:
                # Fallback to standard embedding if ETKDGv3 fails
                AllChem.EmbedMolecule(mol_h, randomSeed=42)

            # Energy minimize conformation using UFF
            try:
                AllChem.UFFOptimizeMolecule(mol_h, maxIters=500)
            except Exception as e:
                logger.warning("UFF optimization completed with warning: %s", e)

            # Assign Name
            mol_h.SetProp("_Name", name)

            # Serialize 3D structure for Blender / MolecularNodes
            pdb_str = Chem.MolToPDBBlock(mol_h)
            sdf_str = Chem.MolToMolBlock(mol_h)

            # Compute Descriptors
            formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
            mw = Descriptors.MolWt(mol)
            exact_mass = Descriptors.ExactMolWt(mol)
            logp = Descriptors.MolLogP(mol)
            tpsa = Descriptors.TPSA(mol)
            n_rot = Descriptors.NumRotatableBonds(mol)
            h_donors = Lipinski.NumHDonors(mol)
            h_acceptors = Lipinski.NumHAcceptors(mol)
            heavy_atoms = mol.GetNumHeavyAtoms()
            rings = Chem.rdMolDescriptors.CalcNumRings(mol)
            arom_rings = Chem.rdMolDescriptors.CalcNumAromaticRings(mol)

            # Lipinski Rule of 5 check (MW <= 500, LogP <= 5, HBD <= 5, HBA <= 10)
            ro5_pass = mw <= 500.0 and logp <= 5.0 and h_donors <= 5 and h_acceptors <= 10

            return MolecularProperties(
                smiles=smiles,
                iupac_name=name,
                formula=formula,
                molecular_weight=round(mw, 3),
                exact_mass=round(exact_mass, 4),
                log_p=round(logp, 2),
                tpsa=round(tpsa, 2),
                num_rotatable_bonds=n_rot,
                num_h_donors=h_donors,
                num_h_acceptors=h_acceptors,
                num_heavy_atoms=heavy_atoms,
                num_rings=rings,
                num_aromatic_rings=arom_rings,
                lipinski_rule_of_five_pass=ro5_pass,
                pdb_block=pdb_str,
                sdf_block=sdf_str,
                atom_count=mol_h.GetNumAtoms(),
            )

        except Exception as exc:
            logger.error("RDKit 3D generation error for '%s': %s", smiles, exc)
            return None


# Global singleton instance
RDKIT_ENGINE = RDKitCheminformaticsEngine()
