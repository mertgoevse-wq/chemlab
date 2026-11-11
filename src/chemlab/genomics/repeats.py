"""
Repeat element data structures.

Defines classes for transposable elements, tandem repeats,
and other repetitive genomic sequences.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RepeatClass(str, Enum):
    """Repeat class (Wicker classification)."""

    RETROTRANSPOSON = "Retrotransposon"
    DNA_TRANSPOSON = "DNA transposon"
    LTR = "LTR"
    LINE = "LINE"
    SINE = "SINE"
    SIMPLE_REPEAT = "Simple_repeat"
    LOW_COMPLEXITY = "Low_complexity"
    SATELLITE = "Satellite"
    RNA = "RNA"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class RepeatFamily(str, Enum):
    """Common repeat families."""

    # Human/mammal repeats
    ALU = "Alu"  # SINE
    L1 = "L1"  # LINE
    L2 = "L2"  # LINE
    MIR = "MIR"  # SINE
    ERV1 = "ERV1"  # LTR
    ERVK = "ERVK"  # LTR
    ERVL = "ERVL"  # LTR
    MAVERICK = "Maverick"  # DNA transposon
    PIGGYBAC = "PiggyBac"  # DNA transposon
    TcMAR = "TcMar"  # DNA transposon
    HAT = "hAT"  # DNA transposon
    MUDR = "MuDR"  # DNA transposon
    # Satellite repeats
    ALPHA_SATELLITE = "Alpha_satellite"
    BETA_SATELLITE = "Beta_satellite"
    GAMMA_SATELLITE = "Gamma_satellite"
    SATELLITE_2 = "Satellite_2"
    SATELLITE_3 = "Satellite_3"
    # Simple repeats
    MICROSATELLITE = "Microsatellite"
    MINISATELLITE = "Minisatellite"
    TELOMERE = "Telomere"
    CENTROMERE = "Centromere"
    # Other
    RRNA = "rRNA"
    SNRNA = "snRNA"
    TRNA = "tRNA"
    SCRNA = "scRNA"
    SRPRNA = "SRP_RNA"


@dataclass(slots=True)
class RepeatElement:
    """
    Repeat element data structure.

    Represents a repetitive genomic element from RepeatMasker or similar.
    """

    repeat_id: str
    chromosome: str
    start_bp: int
    end_bp: int
    repeat_class: RepeatClass
    repeat_family: RepeatFamily | str
    repeat_name: str = ""  # e.g., "AluSx", "L1HS"
    strand: str = "+"
    repeat_unit: str = ""  # Monomer sequence for tandem repeats
    repeat_count: float = 0.0  # Number of repeat units
    divergence_pct: float = 0.0  # % divergence from consensus
    deletions_pct: float = 0.0
    insertions_pct: float = 0.0
    score: float = 0.0  # RepeatMasker score

    @property
    def length_bp(self) -> int:
        """Repeat length in base pairs."""
        return self.end_bp - self.start_bp + 1

    @property
    def midpoint_bp(self) -> int:
        """Repeat midpoint."""
        return (self.start_bp + self.end_bp) // 2

    @property
    def is_tandem_repeat(self) -> bool:
        """Check if this is a tandem/simple repeat."""
        return self.repeat_class in (
            RepeatClass.SIMPLE_REPEAT,
            RepeatClass.LOW_COMPLEXITY,
            RepeatClass.SATELLITE,
            RepeatClass.MICROSATELLITE,
            RepeatClass.MINISATELLITE,
            RepeatClass.TELOMERE,
            RepeatClass.CENTROMERE,
        )

    @property
    def is_transposon(self) -> bool:
        """Check if this is a transposable element."""
        return self.repeat_class in (
            RepeatClass.RETROTRANSPOSON,
            RepeatClass.DNA_TRANSPOSON,
            RepeatClass.LTR,
            RepeatClass.LINE,
            RepeatClass.SINE,
        )

    def contains_position(self, position: int) -> bool:
        """Check if position is within repeat."""
        return self.start_bp <= position <= self.end_bp

    def overlaps(self, other: RepeatElement) -> bool:
        """Check if this repeat overlaps another."""
        if self.chromosome != other.chromosome:
            return False
        return not (self.end_bp < other.start_bp or other.end_bp < self.start_bp)


# RepeatMasker class to family mapping
REPEATMASKER_TO_FAMILY = {
    # SINEs
    "Alu": RepeatFamily.ALU,
    "MIR": RepeatFamily.MIR,
    "tRNA": RepeatFamily.TRNA,
    "7SL": RepeatFamily.OTHER,
    # LINEs
    "L1": RepeatFamily.L1,
    "L2": RepeatFamily.L2,
    "CR1": RepeatFamily.LINE,
    "RTE": RepeatFamily.LINE,
    "Jockey": RepeatFamily.LINE,
    "I": RepeatFamily.LINE,
    # LTR
    "ERV1": RepeatFamily.ERV1,
    "ERVK": RepeatFamily.ERVK,
    "ERVL": RepeatFamily.ERVL,
    "Gypsy": RepeatFamily.ERVK,
    "Copia": RepeatFamily.ERV1,
    # DNA transposons
    "hAT": RepeatFamily.HAT,
    "MuDR": RepeatFamily.MUDR,
    "TcMar": RepeatFamily.TcMAR,
    "PiggyBac": RepeatFamily.PIGGYBAC,
    "Maverick": RepeatFamily.MAVERICK,
    "Merlin": RepeatFamily.DNA_TRANSPOSON,
    "Transib": RepeatFamily.DNA_TRANSPOSON,
    "PIF": RepeatFamily.DNA_TRANSPOSON,
    # Satellites
    "alpha": RepeatFamily.ALPHA_SATELLITE,
    "beta": RepeatFamily.BETA_SATELLITE,
    "gamma": RepeatFamily.GAMMA_SATELLITE,
    "centromere": RepeatFamily.CENTROMERE,
    "telomere": RepeatFamily.TELOMERE,
    "HSAT": RepeatFamily.SATELLITE_2,
    "BSAT": RepeatFamily.SATELLITE_3,
    # Simple
    "Simple_repeat": RepeatFamily.MICROSATELLITE,
    "Low_complexity": RepeatFamily.LOW_COMPLEXITY,
    "Satellite": RepeatFamily.SATELLITE,
    # RNA
    "rRNA": RepeatFamily.RRNA,
    "snRNA": RepeatFamily.SNRNA,
    "scRNA": RepeatFamily.SCRNA,
    "srpRNA": RepeatFamily.SRPRNA,
}


def classify_repeat(rep_name: str, rep_class: str) -> tuple[RepeatClass, RepeatFamily]:
    """
    Classify repeat from RepeatMasker name and class.

    Args:
        rep_name: RepeatMasker repeat name (e.g., "AluSx")
        rep_class: RepeatMasker class (e.g., "SINE")

    Returns:
        Tuple of (RepeatClass, RepeatFamily)
    """
    # Map class
    class_map = {
        "SINE": RepeatClass.SINE,
        "LINE": RepeatClass.LINE,
        "LTR": RepeatClass.LTR,
        "DNA": RepeatClass.DNA_TRANSPOSON,
        "RC": RepeatClass.DNA_TRANSPOSON,  # Rolling circle
        "Retroposon": RepeatClass.RETROTRANSPOSON,
        "Simple_repeat": RepeatClass.SIMPLE_REPEAT,
        "Low_complexity": RepeatClass.LOW_COMPLEXITY,
        "Satellite": RepeatClass.SATELLITE,
        "RNA": RepeatClass.RNA,
        "tRNA": RepeatClass.RNA,
        "rRNA": RepeatClass.RNA,
        "snRNA": RepeatClass.RNA,
        "scRNA": RepeatClass.RNA,
        "srpRNA": RepeatClass.RNA,
        "Unknown": RepeatClass.UNKNOWN,
        "Other": RepeatClass.OTHER,
    }

    rep_class_enum = class_map.get(rep_class, RepeatClass.UNKNOWN)

    # Map family
    family = RepeatFamily.OTHER
    for key, fam in REPEATMASKER_TO_FAMILY.items():
        if key in rep_name or key == rep_class:
            family = fam
            break

    return rep_class_enum, family
