"""
Genomic Data Integration Package for ChemLab Genetics Lab.

Provides:
- Real genome assembly loading (Human GRCh38, Mouse GRCm39, etc.)
- Chromosome-level data structures (genes, exons, regulatory regions)
- Variant effect prediction (VEP-style)
- Gene dosage simulation
- CRISPR guide design
- Primer design
- Interactive genome editor
"""

from chemlab.genomics.assembly import GenomeAssembly, Chromosome, Gene, Transcript, Exon
from chemlab.genomics.variants import Variant, SNP, CNV, VariantEffectPredictor
from chemlab.genomics.regulatory import RegulatoryRegion
from chemlab.genomics.repeats import RepeatElement
from chemlab.genomics.sequence import GenomicSequence
from chemlab.genomics.interval_tree import GenomicIntervalTree
from chemlab.genomics.browser import ChromosomeBrowser, BrowserTrack
from chemlab.genomics.dosage import DosageSimulator
from chemlab.genomics.crispr import CRISPRGuideDesigner, GuideRNA, GuideScore
from chemlab.genomics.primers import PrimerDesigner, Primer, PrimerPair
from chemlab.genomics.editor import GenomeEditor, Edit, EditSimulation
from chemlab.genomics.loader import (
    load_genome_assembly,
    get_available_assemblies,
    download_assembly,
)

__version__ = "1.0.0"

__all__ = [
    # Core data structures
    "GenomeAssembly",
    "Chromosome",
    "Gene",
    "Transcript",
    "Exon",
    "RegulatoryRegion",
    "RepeatElement",
    # Variants
    "Variant",
    "SNP",
    "CNV",
    "VariantEffectPredictor",
    # Sequence utilities
    "GenomicSequence",
    "GenomicIntervalTree",
    # Browser
    "ChromosomeBrowser",
    "BrowserTrack",
    # Dosage simulation
    "DosageSimulator",
    # CRISPR
    "CRISPRGuideDesigner",
    "GuideRNA",
    "GuideScore",
    # Primers
    "PrimerDesigner",
    "Primer",
    "PrimerPair",
    # Editor
    "GenomeEditor",
    "Edit",
    "EditSimulation",
    # Loader
    "load_genome_assembly",
    "get_available_assemblies",
    "download_assembly",
]