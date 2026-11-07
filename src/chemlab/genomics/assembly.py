"""
Core genomic data structures for genome assemblies.

Defines the fundamental classes for representing chromosomes, genes,
transcripts, exons, and complete genome assemblies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from enum import Enum


class Strand(str, Enum):
    """DNA strand orientation."""
    POSITIVE = "+"
    NEGATIVE = "-"


class Biotype(str, Enum):
    """Gene/transcript biotype classifications."""
    PROTEIN_CODING = "protein_coding"
    LNCRNA = "lncRNA"
    MIRNA = "miRNA"
    SNRNA = "snRNA"
    SNO_RNA = "snoRNA"
    RRNA = "rRNA"
    TRNA = "tRNA"
    PSEUDOGENE = "pseudogene"
    PROCESSED_TRANSCRIPT = "processed_transcript"
    RETAINED_INTRON = "retained_intron"
    NONSENSE_MEDIATED_DECAY = "nonsense_mediated_decay"
    NON_CODING = "non_coding"
    UNKNOWN = "unknown"


class GeneStatus(str, Enum):
    """Gene status classifications."""
    KNOWN = "KNOWN"
    NOVEL = "NOVEL"
    PUTATIVE = "PUTATIVE"
    PREDICTED = "PREDICTED"
    KNOWN_BY_PROJECTION = "KNOWN_BY_PROJECTION"


@dataclass(slots=True)
class Chromosome:
    """
    Chromosome-level data structure.

    Represents a single chromosome/scaffold with sequence and metadata.
    """
    accession: str
    name: str
    organism: str
    assembly: str
    length_bp: int
    sequence: bytes = field(default_factory=bytes)
    is_circular: bool = False
    centromere_start: int = 0
    centromere_end: int = 0
    band_count: int = 0
    _seq_cache: bytes | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self._seq_cache is None:
            self._seq_cache = self.sequence

    def get_sequence(self, start: int = 0, end: int | None = None) -> bytes:
        """
        Get subsequence (0-indexed, end-exclusive).

        Args:
            start: Start position (0-indexed)
            end: End position (exclusive), or None for end of chromosome

        Returns:
            Sequence bytes
        """
        if end is None:
            end = self.length_bp
        if not self.sequence:
            return b"N" * (end - start)
        return self.sequence[start:end]

    def get_sequence_str(self, start: int = 0, end: int | None = None) -> str:
        """Get subsequence as string."""
        return self.get_sequence(start, end).decode("ascii")

    def __len__(self) -> int:
        return self.length_bp

    def __contains__(self, position: int) -> bool:
        return 0 <= position < self.length_bp


@dataclass(slots=True)
class Gene:
    """
    Gene-level data structure.

    Represents a gene locus with genomic coordinates and metadata.
    """
    gene_id: str
    symbol: str
    name: str
    chromosome: str
    start_bp: int
    end_bp: int
    strand: Strand
    biotype: Biotype
    status: GeneStatus
    description: str = ""
    xref_ids: dict[str, str] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    phenotype_ids: list[str] = field(default_factory=list)
    dbsnp_ids: list[str] = field(default_factory=list)

    @property
    def length_bp(self) -> int:
        """Gene length in base pairs."""
        return self.end_bp - self.start_bp + 1

    @property
    def midpoint_bp(self) -> int:
        """Gene midpoint position."""
        return (self.start_bp + self.end_bp) // 2

    def contains_position(self, position: int) -> bool:
        """Check if position is within gene bounds."""
        return self.start_bp <= position <= self.end_bp

    def overlaps(self, other: Gene) -> bool:
        """Check if this gene overlaps another gene."""
        if self.chromosome != other.chromosome:
            return False
        return not (self.end_bp < other.start_bp or other.end_bp < self.start_bp)


@dataclass(slots=True)
class Exon:
    """
    Exon data structure.

    Represents a single exon within a transcript.
    """
    exon_id: str
    transcript_id: str
    chromosome: str
    start_bp: int
    end_bp: int
    strand: Strand
    exon_number: int
    cds_start_offset: int = 0
    cds_end_offset: int = 0
    sequence: bytes = field(default_factory=bytes)

    @property
    def length_bp(self) -> int:
        """Exon length in base pairs."""
        return self.end_bp - self.start_bp + 1

    @property
    def is_coding(self) -> bool:
        """Check if exon has coding sequence."""
        return self.cds_start_offset < self.cds_end_offset

    @property
    def cds_length_bp(self) -> int:
        """Coding sequence length in base pairs."""
        return max(0, self.cds_end_offset - self.cds_start_offset)


@dataclass(slots=True)
class Transcript:
    """
    Transcript data structure.

    Represents a transcript with exon structure and coding sequence.
    """
    transcript_id: str
    gene_id: str
    chromosome: str
    start_bp: int
    end_bp: int
    strand: Strand
    biotype: Biotype
    is_canonical: bool = False
    cds_start_bp: int = 0
    cds_end_bp: int = 0
    exons: list[Exon] = field(default_factory=list)
    cds_sequence: bytes = field(default_factory=bytes)

    def __post_init__(self) -> None:
        # Sort exons by genomic position
        self.exons.sort(key=lambda e: (e.start_bp, e.end_bp))

    @property
    def length_bp(self) -> int:
        """Transcript length in base pairs."""
        return self.end_bp - self.start_bp + 1

    @property
    def is_protein_coding(self) -> bool:
        """Check if transcript is protein coding."""
        return self.biotype == Biotype.PROTEIN_CODING

    @property
    def cds_length_bp(self) -> int:
        """CDS length in base pairs."""
        if self.cds_start_bp == 0 or self.cds_end_bp == 0:
            return 0
        return self.cds_end_bp - self.cds_start_bp + 1

    def get_exon_by_number(self, exon_number: int) -> Exon | None:
        """Get exon by its number in transcript."""
        for exon in self.exons:
            if exon.exon_number == exon_number:
                return exon
        return None

    def get_coding_exons(self) -> list[Exon]:
        """Get exons that contain coding sequence."""
        return [e for e in self.exons if e.is_coding]

    def genomic_to_transcript_coord(self, genomic_pos: int) -> int | None:
        """
        Convert genomic coordinate to transcript coordinate (1-indexed).

        Returns None if position is not in any exon.
        """
        if self.strand == Strand.POSITIVE:
            pos = 0
            for exon in self.exons:
                exon_len = exon.length_bp
                if exon.start_bp <= genomic_pos <= exon.end_bp:
                    return pos + (genomic_pos - exon.start_bp + 1)
                pos += exon_len
        else:
            # Reverse strand: exons are in genomic order but transcript is reverse
            pos = 0
            for exon in reversed(self.exons):
                exon_len = exon.length_bp
                if exon.start_bp <= genomic_pos <= exon.end_bp:
                    return pos + (exon.end_bp - genomic_pos + 1)
                pos += exon_len
        return None

    def transcript_to_genomic_coord(self, transcript_pos: int) -> int | None:
        """
        Convert transcript coordinate (1-indexed) to genomic coordinate.

        Returns None if position is out of bounds.
        """
        if transcript_pos <= 0:
            return None

        if self.strand == Strand.POSITIVE:
            pos = 0
            for exon in self.exons:
                exon_len = exon.length_bp
                if pos + exon_len >= transcript_pos:
                    return exon.start_bp + (transcript_pos - pos - 1)
                pos += exon_len
        else:
            pos = 0
            for exon in reversed(self.exons):
                exon_len = exon.length_bp
                if pos + exon_len >= transcript_pos:
                    return exon.end_bp - (transcript_pos - pos - 1)
                pos += exon_len
        return None


@dataclass(slots=True)
class GenomeAssembly:
    """
    Complete genome assembly data structure.

    Contains all chromosomes, genes, transcripts, and annotations
    for a single genome build.
    """
    organism: str
    name: str
    accession: str
    chromosomes: dict[str, Chromosome] = field(default_factory=dict)
    genes: dict[str, Gene] = field(default_factory=dict)
    transcripts: dict[str, Transcript] = field(default_factory=dict)
    regulatory_regions: list = field(default_factory=list)
    variants: dict[str, list] = field(default_factory=dict)  # by chromosome
    repeats: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Build reverse indexes
        self._genes_by_chrom: dict[str, list[Gene]] = {}
        self._transcripts_by_gene: dict[str, list[Transcript]] = {}
        self._transcripts_by_chrom: dict[str, list[Transcript]] = {}
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Build reverse lookup indexes."""
        for gene in self.genes.values():
            self._genes_by_chrom.setdefault(gene.chromosome, []).append(gene)

        for transcript in self.transcripts.values():
            self._transcripts_by_gene.setdefault(transcript.gene_id, []).append(transcript)
            self._transcripts_by_chrom.setdefault(transcript.chromosome, []).append(transcript)

        # Sort for consistent ordering
        for chrom in self._genes_by_chrom:
            self._genes_by_chrom[chrom].sort(key=lambda g: g.start_bp)
        for chrom in self._transcripts_by_chrom:
            self._transcripts_by_chrom[chrom].sort(key=lambda t: t.start_bp)

    def get_chromosome(self, name: str) -> Chromosome | None:
        """Get chromosome by name."""
        return self.chromosomes.get(name)

    def get_gene(self, gene_id: str) -> Gene | None:
        """Get gene by ID."""
        return self.genes.get(gene_id)

    def get_gene_by_symbol(self, symbol: str) -> Gene | None:
        """Get gene by HGNC symbol (first match)."""
        for gene in self.genes.values():
            if gene.symbol.upper() == symbol.upper():
                return gene
        return None

    def get_transcript(self, transcript_id: str) -> Transcript | None:
        """Get transcript by ID."""
        return self.transcripts.get(transcript_id)

    def get_genes_on_chromosome(self, chromosome: str) -> list[Gene]:
        """Get all genes on a chromosome."""
        return self._genes_by_chrom.get(chromosome, [])

    def get_transcripts_for_gene(self, gene_id: str) -> list[Transcript]:
        """Get all transcripts for a gene."""
        return self._transcripts_by_gene.get(gene_id, [])

    def get_canonical_transcript(self, gene_id: str) -> Transcript | None:
        """Get canonical transcript for a gene."""
        for transcript in self.get_transcripts_for_gene(gene_id):
            if transcript.is_canonical:
                return transcript
        # Fallback: first protein-coding transcript
        for transcript in self.get_transcripts_for_gene(gene_id):
            if transcript.is_protein_coding:
                return transcript
        # Last resort: first transcript
        transcripts = self.get_transcripts_for_gene(gene_id)
        return transcripts[0] if transcripts else None

    def get_transcripts_on_chromosome(self, chromosome: str) -> list[Transcript]:
        """Get all transcripts on a chromosome."""
        return self._transcripts_by_chrom.get(chromosome, [])

    def find_genes_in_region(
        self,
        chromosome: str,
        start_bp: int,
        end_bp: int
    ) -> list[Gene]:
        """Find all genes overlapping a genomic region."""
        result = []
        for gene in self.get_genes_on_chromosome(chromosome):
            if gene.end_bp >= start_bp and gene.start_bp <= end_bp:
                result.append(gene)
        return result

    def find_transcripts_in_region(
        self,
        chromosome: str,
        start_bp: int,
        end_bp: int
    ) -> list[Transcript]:
        """Find all transcripts overlapping a genomic region."""
        result = []
        for transcript in self.get_transcripts_on_chromosome(chromosome):
            if transcript.end_bp >= start_bp and transcript.start_bp <= end_bp:
                result.append(transcript)
        return result

    @property
    def total_genome_size_bp(self) -> int:
        """Total genome size in base pairs."""
        return sum(chrom.length_bp for chrom in self.chromosomes.values())

    @property
    def chromosome_names(self) -> list[str]:
        """List of chromosome names in order."""
        # Standard ordering: 1-22, X, Y, MT
        def sort_key(name: str) -> tuple:
            name_clean = name.replace("chr", "")
            if name_clean in ("X", "Y", "MT", "M"):
                return (100, name_clean)
            try:
                return (0, int(name_clean))
            except ValueError:
                return (200, name)

        return sorted(self.chromosomes.keys(), key=sort_key)