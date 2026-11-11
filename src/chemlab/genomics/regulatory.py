"""
Regulatory region data structures.

Defines classes for promoters, enhancers, silencers, insulators,
and other regulatory elements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RegulatoryFeatureType(str, Enum):
    """Types of regulatory features."""

    PROMOTER = "promoter"
    ENHANCER = "enhancer"
    SILENCER = "silencer"
    INSULATOR = "insulator"
    CTCF_BINDING_SITE = "ctcf_binding_site"
    TF_BINDING_SITE = "tf_binding_site"
    OPEN_CHROMATIN = "open_chromatin"
    HISTONE_MODIFICATION = "histone_modification"
    DNASE_HYPERSENSITIVE = "dnase_hypersensitive_site"
    MIRNA_TARGET = "miRNA_target_site"


class ActivityState(str, Enum):
    """Activity states of regulatory regions."""

    ACTIVE = "active"
    POISED = "poised"
    REPRESSED = "repressed"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class RegulatoryRegion:
    """
    Regulatory region data structure.

    Represents a genomic region with regulatory function.
    """

    region_id: str
    chromosome: str
    start_bp: int
    end_bp: int
    feature_type: RegulatoryFeatureType
    activity: ActivityState = ActivityState.UNKNOWN
    associated_genes: list[str] = field(default_factory=list)
    cell_types: list[str] = field(default_factory=list)
    transcription_factors: list[str] = field(default_factory=list)
    epigenetic_marks: dict[str, float] = field(default_factory=dict)  # mark -> signal
    conservation_score: float = 0.0
    evidence: list[str] = field(default_factory=list)
    source: str = ""  # e.g., "ENCODE", "Roadmap", "FANTOM5"
    score: float = 0.0  # Confidence/activity score

    @property
    def length_bp(self) -> int:
        """Region length in base pairs."""
        return self.end_bp - self.start_bp + 1

    @property
    def midpoint_bp(self) -> int:
        """Region midpoint."""
        return (self.start_bp + self.end_bp) // 2

    def contains_position(self, position: int) -> bool:
        """Check if position is within region."""
        return self.start_bp <= position <= self.end_bp

    def overlaps(self, other: RegulatoryRegion) -> bool:
        """Check if this region overlaps another."""
        if self.chromosome != other.chromosome:
            return False
        return not (self.end_bp < other.start_bp or other.end_bp < self.start_bp)

    def get_epigenetic_mark(self, mark: str) -> float | None:
        """Get signal for specific epigenetic mark."""
        return self.epigenetic_marks.get(mark)

    def has_epigenetic_mark(self, mark: str, threshold: float = 0.5) -> bool:
        """Check if region has epigenetic mark above threshold."""
        value = self.epigenetic_marks.get(mark, 0.0)
        return value >= threshold


# Common epigenetic marks
EPIGENETIC_MARKS = {
    "H3K4me1": "Enhancer mark",
    "H3K4me3": "Promoter mark",
    "H3K27ac": "Active enhancer/promoter",
    "H3K27me3": "Polycomb repression",
    "H3K9me3": "Heterochromatin",
    "H3K36me3": "Transcription elongation",
    "H3K9ac": "Active chromatin",
    "H4K20me1": "Active chromatin",
    "DNase": "Open chromatin",
    "ATAC": "Open chromatin",
    "CTCF": "Insulator/boundary",
    "Cohesin": "Loop extrusion",
}

# Cell type ontology mappings
COMMON_CELL_TYPES = {
    "K562": "Chronic myelogenous leukemia",
    "HepG2": "Hepatocellular carcinoma",
    "GM12878": "Lymphoblastoid cell line",
    "H1-hESC": "Human embryonic stem cells",
    "IMR90": "Fetal lung fibroblasts",
    "NHEK": "Normal human epidermal keratinocytes",
    "HUVEC": "Umbilical vein endothelial cells",
    "MCF-7": "Breast adenocarcinoma",
    "A549": "Lung adenocarcinoma",
    "SK-N-SH": "Neuroblastoma",
}
