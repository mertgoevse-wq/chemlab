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

from chemlab.genomics.assembly import Chromosome, Exon, Gene, GenomeAssembly, Transcript
from chemlab.genomics.browser import BrowserTrack, ChromosomeBrowser
from chemlab.genomics.crispr import CRISPRGuideDesigner, GuideRNA, GuideScore
from chemlab.genomics.dosage import DosageSimulator
from chemlab.genomics.editor import Edit, EditSimulation, GenomeEditor
from chemlab.genomics.interval_tree import GenomicIntervalTree
from chemlab.genomics.loader import (
    download_assembly,
    get_available_assemblies,
    load_genome_assembly,
)
from chemlab.genomics.primers import Primer, PrimerDesigner, PrimerPair
from chemlab.genomics.regulatory import RegulatoryRegion
from chemlab.genomics.repeats import RepeatElement
from chemlab.genomics.sequence import GenomicSequence
from chemlab.genomics.variants import CNV, SNP, Variant, VariantEffectPredictor

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
