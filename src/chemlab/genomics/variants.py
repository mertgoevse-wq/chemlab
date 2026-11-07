"""
Variant data structures and effect prediction.

Implements VEP-style consequence prediction for genetic variants
including SNPs, SNVs, CNVs, and structural variants.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class VariantType(str, Enum):
    """Variant type classifications."""
    SNP = "SNP"
    SNV = "SNV"
    INSERTION = "insertion"
    DELETION = "deletion"
    MNV = "MNV"  # Multi-nucleotide variant
    INDEL = "indel"
    CNV = "CNV"
    STRUCTURAL = "structural"
    COMPLEX = "complex"


class ConsequenceType(str, Enum):
    """
    VEP-style consequence terms (ordered by severity).

    From most severe to least severe:
    """
    TRANSCRIPT_ABLATION = "transcript_ablation"
    SPLICE_DONOR_VARIANT = "splice_donor_variant"
    SPLICE_ACCEPTOR_VARIANT = "splice_acceptor_variant"
    STOP_GAINED = "stop_gained"
    FRAMESHIFT_VARIANT = "frameshift_variant"
    STOP_LOST = "stop_lost"
    START_LOST = "start_lost"
    STOP_RETAINED_VARIANT = "stop_retained_variant"
    MISSENSE_VARIANT = "missense_variant"
    PROTEIN_ALTERING_VARIANT = "protein_altering_variant"
    SPLICE_REGION_VARIANT = "splice_region_variant"
    INCOMPLETE_TERMINAL_CODON_VARIANT = "incomplete_terminal_codon_variant"
    SYNONYMOUS_VARIANT = "synonymous_variant"
    CODING_SEQUENCE_VARIANT = "coding_sequence_variant"
    MATURE_MIRNA_VARIANT = "mature_miRNA_variant"
    FIVE_PRIME_UTR_VARIANT = "5_prime_UTR_variant"
    THREE_PRIME_UTR_VARIANT = "3_prime_UTR_variant"
    INTRON_VARIANT = "intron_variant"
    UPSTREAM_GENE_VARIANT = "upstream_gene_variant"
    DOWNSTREAM_GENE_VARIANT = "downstream_gene_variant"
    INTERGENIC_VARIANT = "intergenic_variant"
    REGULATORY_REGION_VARIANT = "regulatory_region_variant"
    FEATURE_ELONGATION = "feature_elongation"
    FEATURE_TRUNCATION = "feature_truncation"


class ClinicalSignificance(str, Enum):
    """Clinical significance classifications (ClinVar-style)."""
    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN_SIGNIFICANCE = "uncertain_significance"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"
    CONFLICTING = "conflicting_interpretations"
    NOT_PROVIDED = "not_provided"
    DRUG_RESPONSE = "drug_response"
    ASSOCIATION = "association"
    RISK_FACTOR = "risk_factor"
    PROTECTIVE = "protective"


@dataclass(slots=True)
class Variant:
    """
    Base variant data structure.

    Represents a genetic variant with genomic coordinates and alleles.
    """
    variant_id: str
    chromosome: str
    position_bp: int
    ref_allele: str
    alt_allele: str
    variant_type: VariantType = VariantType.SNP
    allele_freq: float = 0.0
    population_freqs: dict[str, float] = field(default_factory=dict)
    clinical_significance: list[ClinicalSignificance] = field(default_factory=list)
    associated_traits: list[str] = field(default_factory=list)
    quality: float = 0.0
    filters: list[str] = field(default_factory=list)
    info: dict = field(default_factory=dict)

    @property
    def is_snp(self) -> bool:
        """Check if variant is a single nucleotide polymorphism."""
        return len(self.ref_allele) == 1 and len(self.alt_allele) == 1

    @property
    def is_indel(self) -> bool:
        """Check if variant is an insertion/deletion."""
        return len(self.ref_allele) != len(self.alt_allele)

    @property
    def is_insertion(self) -> bool:
        """Check if variant is an insertion."""
        return len(self.alt_allele) > len(self.ref_allele)

    @property
    def is_deletion(self) -> bool:
        """Check if variant is a deletion."""
        return len(self.ref_allele) > len(self.alt_allele)

    @property
    def variant_length(self) -> int:
        """Length difference between alt and ref alleles."""
        return len(self.alt_allele) - len(self.ref_allele)

    @property
    def end_position_bp(self) -> int:
        """End position of variant (for deletions)."""
        return self.position_bp + len(self.ref_allele) - 1


@dataclass(slots=True)
class SNP(Variant):
    """Single Nucleotide Polymorphism variant."""
    variant_type: VariantType = VariantType.SNP
    rsid: str = ""
    sift_prediction: str = ""
    sift_score: float | None = None
    polyphen_prediction: str = ""
    polyphen_score: float | None = None
    fathmm_prediction: str = ""
    fathmm_score: float | None = None
    revel_score: float | None = None
    clinvar_rcv: str = ""


@dataclass(slots=True)
class CNV(Variant):
    """Copy Number Variation variant."""
    variant_type: VariantType = VariantType.CNV
    cnv_id: str = ""
    start_bp: int = 0
    end_bp: int = 0
    copy_number: int = 2  # 0=deleted, 1=hemizygous, 2=diploid, 3=trisomy
    cnv_type: str = "deletion"  # deletion, duplication, amplification
    confidence: float = 0.0
    genes_affected: list[str] = field(default_factory=list)

    @property
    def length_bp(self) -> int:
        """CNV length in base pairs."""
        return self.end_bp - self.start_bp + 1


@dataclass(slots=True)
class StructuralVariant(Variant):
    """Structural variant (inversion, translocation, etc.)."""
    variant_type: VariantType = VariantType.STRUCTURAL
    sv_type: str = ""  # INV, TRA, DUP, DEL, INS, BND
    mate_chromosome: str = ""
    mate_position_bp: int = 0
    mate_orientation: str = ""  # +/-
    assembly_breakpoint: str = ""


@dataclass(slots=True)
class ConservationScore:
    """Evolutionary conservation scores."""
    phastcons: float = 0.0
    phylop: float = 0.0
    primate_phastcons: float = 0.0
    mammalian_phastcons: float = 0.0
    vertebrate_phastcons: float = 0.0


@dataclass(slots=True)
class FunctionalScore:
    """Functional prediction scores."""
    sift_score: float | None = None
    sift_prediction: str = ""
    polyphen_score: float | None = None
    polyphen_prediction: str = ""
    fathmm_score: float | None = None
    fathmm_prediction: str = ""
    revel_score: float | None = None
    cadd_score: float | None = None
    cadd_phred: float | None = None
    meta_svm_score: float | None = None
    meta_svm_prediction: str = ""
    meta_lr_score: float | None = None
    meta_lr_prediction: str = ""


@dataclass(slots=True)
class VariantConsequence:
    """
    Predicted consequence of a variant on a transcript.

    VEP-style consequence with detailed annotation.
    """
    variant_id: str
    transcript_id: str
    gene_id: str
    gene_symbol: str
    consequence_terms: list[ConsequenceType]
    most_severe_consequence: ConsequenceType
    impact: str  # HIGH, MODERATE, LOW, MODIFIER

    # Genomic coordinates
    variant_position: int
    transcript_position: int | None = None
    protein_position: int | None = None

    # Alleles
    ref_allele: str = ""
    alt_allele: str = ""

    # Sequence changes
    cdna_change: str = ""  # e.g., c.123A>G
    cds_change: str = ""   # e.g., c.123A>G
    protein_change: str = ""  # e.g., p.Arg41Gly

    # Codon details
    codon_change: str = ""  # e.g., CGG>TGG
    amino_acid_change: str = ""  # e.g., R>W
    codon_number: int = 0

    # Splice effects
    splice_ai_score: float | None = None
    splice_region_dist: int | None = None  # distance to splice site
    splice_donor_gain: bool = False
    splice_donor_loss: bool = False
    splice_acceptor_gain: bool = False
    splice_acceptor_loss: bool = False

    # Conservation and functional scores
    conservation: ConservationScore = field(default_factory=ConservationScore)
    functional: FunctionalScore = field(default_factory=FunctionalScore)

    # Flags
    is_canonical: bool = False
    is_mane: bool = False  # MANE Select transcript
    existing_variation: list[str] = field(default_factory=list)  # dbSNP IDs

    def get_highest_impact(self) -> str:
        """Get the highest impact level."""
        if ConsequenceType.TRANSCRIPT_ABLATION in self.consequence_terms:
            return "HIGH"
        if ConsequenceType.SPLICE_DONOR_VARIANT in self.consequence_terms:
            return "HIGH"
        if ConsequenceType.SPLICE_ACCEPTOR_VARIANT in self.consequence_terms:
            return "HIGH"
        if ConsequenceType.STOP_GAINED in self.consequence_terms:
            return "HIGH"
        if ConsequenceType.FRAMESHIFT_VARIANT in self.consequence_terms:
            return "HIGH"
        if ConsequenceType.STOP_LOST in self.consequence_terms:
            return "HIGH"
        if ConsequenceType.START_LOST in self.consequence_terms:
            return "HIGH"
        if ConsequenceType.MISSENSE_VARIANT in self.consequence_terms:
            return "MODERATE"
        if ConsequenceType.PROTEIN_ALTERING_VARIANT in self.consequence_terms:
            return "MODERATE"
        if ConsequenceType.SPLICE_REGION_VARIANT in self.consequence_terms:
            return "MODERATE"
        if ConsequenceType.INCOMPLETE_TERMINAL_CODON_VARIANT in self.consequence_terms:
            return "MODERATE"
        if ConsequenceType.SYNONYMOUS_VARIANT in self.consequence_terms:
            return "LOW"
        if ConsequenceType.CODING_SEQUENCE_VARIANT in self.consequence_terms:
            return "LOW"
        return "MODIFIER"

    def __lt__(self, other: VariantConsequence) -> bool:
        """Sort by consequence severity (most severe first)."""
        severity_order = {
            ConsequenceType.TRANSCRIPT_ABLATION: 0,
            ConsequenceType.SPLICE_DONOR_VARIANT: 1,
            ConsequenceType.SPLICE_ACCEPTOR_VARIANT: 2,
            ConsequenceType.STOP_GAINED: 3,
            ConsequenceType.FRAMESHIFT_VARIANT: 4,
            ConsequenceType.STOP_LOST: 5,
            ConsequenceType.START_LOST: 6,
            ConsequenceType.STOP_RETAINED_VARIANT: 7,
            ConsequenceType.MISSENSE_VARIANT: 8,
            ConsequenceType.PROTEIN_ALTERING_VARIANT: 9,
            ConsequenceType.SPLICE_REGION_VARIANT: 10,
            ConsequenceType.INCOMPLETE_TERMINAL_CODON_VARIANT: 11,
            ConsequenceType.SYNONYMOUS_VARIANT: 12,
            ConsequenceType.CODING_SEQUENCE_VARIANT: 13,
            ConsequenceType.MATURE_MIRNA_VARIANT: 14,
            ConsequenceType.FIVE_PRIME_UTR_VARIANT: 15,
            ConsequenceType.THREE_PRIME_UTR_VARIANT: 16,
            ConsequenceType.INTRON_VARIANT: 17,
            ConsequenceType.UPSTREAM_GENE_VARIANT: 18,
            ConsequenceType.DOWNSTREAM_GENE_VARIANT: 19,
            ConsequenceType.INTERGENIC_VARIANT: 20,
            ConsequenceType.REGULATORY_REGION_VARIANT: 21,
            ConsequenceType.FEATURE_ELONGATION: 22,
            ConsequenceType.FEATURE_TRUNCATION: 23,
        }
        return severity_order.get(self.most_severe_consequence, 99) < \
               severity_order.get(other.most_severe_consequence, 99)


class VariantEffectPredictor:
    """
    Variant Effect Predictor - VEP-style consequence prediction.

    Predicts the effects of genetic variants on genes, transcripts,
    and proteins. Supports multiple consequence types and severity scoring.
    """

    # Consequence severity ranking (lower = more severe)
    CONSEQUENCE_RANK = {
        ConsequenceType.TRANSCRIPT_ABLATION: 1,
        ConsequenceType.SPLICE_DONOR_VARIANT: 2,
        ConsequenceType.SPLICE_ACCEPTOR_VARIANT: 3,
        ConsequenceType.STOP_GAINED: 4,
        ConsequenceType.FRAMESHIFT_VARIANT: 5,
        ConsequenceType.STOP_LOST: 6,
        ConsequenceType.START_LOST: 7,
        ConsequenceType.STOP_RETAINED_VARIANT: 8,
        ConsequenceType.MISSENSE_VARIANT: 9,
        ConsequenceType.PROTEIN_ALTERING_VARIANT: 10,
        ConsequenceType.SPLICE_REGION_VARIANT: 11,
        ConsequenceType.INCOMPLETE_TERMINAL_CODON_VARIANT: 12,
        ConsequenceType.SYNONYMOUS_VARIANT: 13,
        ConsequenceType.CODING_SEQUENCE_VARIANT: 14,
        ConsequenceType.MATURE_MIRNA_VARIANT: 15,
        ConsequenceType.FIVE_PRIME_UTR_VARIANT: 16,
        ConsequenceType.THREE_PRIME_UTR_VARIANT: 17,
        ConsequenceType.INTRON_VARIANT: 18,
        ConsequenceType.UPSTREAM_GENE_VARIANT: 19,
        ConsequenceType.DOWNSTREAM_GENE_VARIANT: 20,
        ConsequenceType.INTERGENIC_VARIANT: 21,
        ConsequenceType.REGULATORY_REGION_VARIANT: 22,
        ConsequenceType.FEATURE_ELONGATION: 23,
        ConsequenceType.FEATURE_TRUNCATION: 24,
    }

    # Impact mapping
    CONSEQUENCE_IMPACT = {
        ConsequenceType.TRANSCRIPT_ABLATION: "HIGH",
        ConsequenceType.SPLICE_DONOR_VARIANT: "HIGH",
        ConsequenceType.SPLICE_ACCEPTOR_VARIANT: "HIGH",
        ConsequenceType.STOP_GAINED: "HIGH",
        ConsequenceType.FRAMESHIFT_VARIANT: "HIGH",
        ConsequenceType.STOP_LOST: "HIGH",
        ConsequenceType.START_LOST: "HIGH",
        ConsequenceType.MISSENSE_VARIANT: "MODERATE",
        ConsequenceType.PROTEIN_ALTERING_VARIANT: "MODERATE",
        ConsequenceType.SPLICE_REGION_VARIANT: "MODERATE",
        ConsequenceType.INCOMPLETE_TERMINAL_CODON_VARIANT: "MODERATE",
        ConsequenceType.SYNONYMOUS_VARIANT: "LOW",
        ConsequenceType.CODING_SEQUENCE_VARIANT: "LOW",
        ConsequenceType.MATURE_MIRNA_VARIANT: "LOW",
        ConsequenceType.FIVE_PRIME_UTR_VARIANT: "MODIFIER",
        ConsequenceType.THREE_PRIME_UTR_VARIANT: "MODIFIER",
        ConsequenceType.INTRON_VARIANT: "MODIFIER",
        ConsequenceType.UPSTREAM_GENE_VARIANT: "MODIFIER",
        ConsequenceType.DOWNSTREAM_GENE_VARIANT: "MODIFIER",
        ConsequenceType.INTERGENIC_VARIANT: "MODIFIER",
        ConsequenceType.REGULATORY_REGION_VARIANT: "MODIFIER",
        ConsequenceType.FEATURE_ELONGATION: "MODIFIER",
        ConsequenceType.FEATURE_TRUNCATION: "MODIFIER",
        ConsequenceType.STOP_RETAINED_VARIANT: "LOW",
    }

    def __init__(self) -> None:
        self._consequence_cache: dict[str, list[VariantConsequence]] = {}

    def predict(
        self,
        variant: Variant,
        assembly,
        transcripts: list
    ) -> list[VariantConsequence]:
        """
        Predict all consequences of a variant on given transcripts.

        Args:
            variant: The variant to predict effects for
            assembly: GenomeAssembly with gene/transcript data
            transcripts: List of transcripts overlapping the variant

        Returns:
            List of VariantConsequence objects, sorted by severity
        """
        cache_key = f"{variant.variant_id}:{','.join(t.transcript_id for t in transcripts)}"
        if cache_key in self._consequence_cache:
            return self._consequence_cache[cache_key]

        consequences = []

        for transcript in transcripts:
            consequence = self._predict_for_transcript(variant, transcript)
            if consequence:
                consequences.append(consequence)

        # Sort by severity (most severe first)
        consequences.sort()

        self._consequence_cache[cache_key] = consequences
        return consequences

    def _predict_for_transcript(
        self,
        variant: Variant,
        transcript
    ) -> VariantConsequence | None:
        """Predict consequence for a single transcript."""
        # Check if variant overlaps transcript
        if not self._overlaps_transcript(variant, transcript):
            return None

        # Get transcript-relative position
        tx_pos = self._get_transcript_position(variant, transcript)
        if tx_pos is None:
            return None

        # Determine consequence terms
        consequence_terms = self._determine_consequences(variant, transcript, tx_pos)
        if not consequence_terms:
            return None

        most_severe = min(
            consequence_terms,
            key=lambda c: self.CONSEQUENCE_RANK.get(c, 99)
        )
        impact = self.CONSEQUENCE_IMPACT.get(most_severe, "MODIFIER")

        # Get protein position if in CDS
        protein_pos = self._get_protein_position(variant, transcript, tx_pos)

        # Build consequence object
        consequence = VariantConsequence(
            variant_id=variant.variant_id,
            transcript_id=transcript.transcript_id,
            gene_id=transcript.gene_id,
            gene_symbol="",  # Will be filled by caller
            consequence_terms=consequence_terms,
            most_severe_consequence=most_severe,
            impact=impact,
            variant_position=variant.position_bp,
            transcript_position=tx_pos,
            protein_position=protein_pos,
            ref_allele=variant.ref_allele,
            alt_allele=variant.alt_allele,
        )

        # Add sequence changes
        self._add_sequence_changes(consequence, variant, transcript, tx_pos)

        return consequence

    def _overlaps_transcript(self, variant: Variant, transcript) -> bool:
        """Check if variant overlaps transcript."""
        var_start = variant.position_bp
        var_end = variant.end_position_bp
        return not (var_end < transcript.start_bp or var_start > transcript.end_bp)

    def _get_transcript_position(self, variant: Variant, transcript) -> int | None:
        """Get variant position within transcript (1-indexed)."""
        return transcript.genomic_to_transcript_coord(variant.position_bp)

    def _get_protein_position(
        self,
        variant: Variant,
        transcript,
        tx_pos: int
    ) -> int | None:
        """Get protein position if variant is in CDS."""
        if not transcript.is_protein_coding:
            return None
        if transcript.cds_start_bp == 0 or transcript.cds_end_bp == 0:
            return None

        # Convert transcript position to CDS position
        cds_start_tx = transcript.genomic_to_transcript_coord(transcript.cds_start_bp)
        if cds_start_tx is None:
            return None

        cds_pos = tx_pos - cds_start_tx + 1
        if cds_pos <= 0:
            return None

        # Protein position (1-indexed, codon-based)
        protein_pos = (cds_pos + 2) // 3
        return protein_pos

    def _determine_consequences(
        self,
        variant: Variant,
        transcript,
        tx_pos: int
    ) -> list[ConsequenceType]:
        """Determine all consequence terms for variant on transcript."""
        terms = []

        # Check if in CDS
        in_cds = transcript.is_protein_coding and \
                 transcript.cds_start_bp <= variant.position_bp <= transcript.cds_end_bp

        # Check if in UTR
        in_five_prime_utr = False
        in_three_prime_utr = False
        if transcript.is_protein_coding:
            if tx_pos < transcript.genomic_to_transcript_coord(transcript.cds_start_bp) or \
               transcript.cds_start_bp == 0:
                in_five_prime_utr = True
            elif tx_pos > transcript.genomic_to_transcript_coord(transcript.cds_end_bp):
                in_three_prime_utr = True

        # Check if in intron
        in_exon = self._is_in_exon(variant, transcript)
        in_intron = not in_exon

        # Check splice sites
        splice_donor_dist = self._distance_to_splice_donor(variant, transcript)
        splice_acceptor_dist = self._distance_to_splice_acceptor(variant, transcript)

        is_splice_donor = abs(splice_donor_dist) <= 2
        is_splice_acceptor = abs(splice_acceptor_dist) <= 2
        is_splice_region = abs(splice_donor_dist) <= 8 or abs(splice_acceptor_dist) <= 8

        # Variant type
        is_snp = variant.is_snp
        is_insertion = variant.is_insertion
        is_deletion = variant.is_deletion
        is_indel = variant.is_indel

        # Determine consequences
        if is_splice_donor and in_exon:
            terms.append(ConsequenceType.SPLICE_DONOR_VARIANT)
        if is_splice_acceptor and in_exon:
            terms.append(ConsequenceType.SPLICE_ACCEPTOR_VARIANT)
        if is_splice_region and in_exon and not is_splice_donor and not is_splice_acceptor:
            terms.append(ConsequenceType.SPLICE_REGION_VARIANT)

        if in_cds:
            if is_snp:
                terms.append(ConsequenceType.CODING_SEQUENCE_VARIANT)
                # Check specific CDS changes
                if self._is_start_lost(variant, transcript):
                    terms.append(ConsequenceType.START_LOST)
                elif self._is_stop_gained(variant, transcript):
                    terms.append(ConsequenceType.STOP_GAINED)
                elif self._is_stop_lost(variant, transcript):
                    terms.append(ConsequenceType.STOP_LOST)
                elif self._is_frameshift(variant, transcript):
                    terms.append(ConsequenceType.FRAMESHIFT_VARIANT)
                elif self._is_missense(variant, transcript):
                    terms.append(ConsequenceType.MISSENSE_VARIANT)
                elif self._is_synonymous(variant, transcript):
                    terms.append(ConsequenceType.SYNONYMOUS_VARIANT)
                elif self._is_protein_altering(variant, transcript):
                    terms.append(ConsequenceType.PROTEIN_ALTERING_VARIANT)
        elif in_five_prime_utr:
            terms.append(ConsequenceType.FIVE_PRIME_UTR_VARIANT)
        elif in_three_prime_utr:
            terms.append(ConsequenceType.THREE_PRIME_UTR_VARIANT)
        elif in_intron:
            terms.append(ConsequenceType.INTRON_VARIANT)
        else:
            # Intergenic or regulatory
            terms.append(ConsequenceType.REGULATORY_REGION_VARIANT)

        return terms

    def _is_in_exon(self, variant: Variant, transcript) -> bool:
        """Check if variant position falls within any exon."""
        for exon in transcript.exons:
            if exon.start_bp <= variant.position_bp <= exon.end_bp:
                return True
        return False

    def _distance_to_splice_donor(self, variant: Variant, transcript) -> int:
        """Distance to nearest splice donor site (5' end of intron)."""
        min_dist = float('inf')
        for exon in transcript.exons:
            if transcript.strand.value == "+":
                donor = exon.end_bp
            else:
                donor = exon.start_bp
            dist = variant.position_bp - donor
            if abs(dist) < abs(min_dist):
                min_dist = dist
        return min_dist if min_dist != float('inf') else 0

    def _distance_to_splice_acceptor(self, variant: Variant, transcript) -> int:
        """Distance to nearest splice acceptor site (3' end of intron)."""
        min_dist = float('inf')
        for exon in transcript.exons:
            if transcript.strand.value == "+":
                acceptor = exon.start_bp
            else:
                acceptor = exon.end_bp
            dist = variant.position_bp - acceptor
            if abs(dist) < abs(min_dist):
                min_dist = dist
        return min_dist if min_dist != float('inf') else 0

    def _is_start_lost(self, variant: Variant, transcript) -> bool:
        """Check if variant disrupts start codon."""
        if transcript.cds_start_bp == 0:
            return False
        return variant.position_bp == transcript.cds_start_bp and \
               variant.ref_allele != variant.alt_allele

    def _is_stop_gained(self, variant: Variant, transcript) -> bool:
        """Check if variant creates a stop codon."""
        # Simplified: check if variant changes codon to stop
        return False  # Requires actual sequence translation

    def _is_stop_lost(self, variant: Variant, transcript) -> bool:
        """Check if variant removes a stop codon."""
        if transcript.cds_end_bp == 0:
            return False
        return variant.position_bp == transcript.cds_end_bp and \
               variant.ref_allele != variant.alt_allele

    def _is_frameshift(self, variant: Variant, transcript) -> bool:
        """Check if variant causes frameshift."""
        return variant.is_indel and len(variant.ref_allele) != len(variant.alt_allele) \
               and abs(len(variant.alt_allele) - len(variant.ref_allele)) % 3 != 0

    def _is_missense(self, variant: Variant, transcript) -> bool:
        """Check if variant causes missense mutation."""
        return variant.is_snp  # Simplified

    def _is_synonymous(self, variant: Variant, transcript) -> bool:
        """Check if variant is synonymous."""
        return variant.is_snp  # Simplified

    def _is_protein_altering(self, variant: Variant, transcript) -> bool:
        """Check if variant alters protein without frameshift."""
        return variant.is_indel and abs(len(variant.alt_allele) - len(variant.ref_allele)) % 3 == 0

    def _add_sequence_changes(
        self,
        consequence: VariantConsequence,
        variant: Variant,
        transcript,
        tx_pos: int
    ) -> None:
        """Add sequence change annotations (cDNA, CDS, protein)."""
        # cDNA change
        consequence.cdna_change = f"c.{tx_pos}{variant.ref_allele}>{variant.alt_allele}"

        # CDS change (if in CDS)
        if transcript.is_protein_coding and transcript.cds_start_bp > 0:
            cds_start_tx = transcript.genomic_to_transcript_coord(transcript.cds_start_bp)
            if cds_start_tx and tx_pos >= cds_start_tx:
                cds_pos = tx_pos - cds_start_tx + 1
                consequence.cds_change = f"c.{cds_pos}{variant.ref_allele}>{variant.alt_allele}"

        # Protein change (requires translation)
        # This is simplified - real implementation needs codon translation
        if consequence.protein_position:
            # Placeholder - would need actual amino acid change
            consequence.protein_change = f"p.{consequence.protein_position}?"