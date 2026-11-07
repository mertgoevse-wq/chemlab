# Genomic Data Integration Design for ChemLab Genetics Lab

## 1. Overview

This document defines the data schema, architecture, and implementation approach for integrating real genomic data into the ChemLab genetics lab simulation. The system enables:

- Chromosome browser with zoom from whole chromosome to base pair resolution
- Variant effect prediction (VEP-style) for missense, nonsense, splice, and regulatory variants
- Gene dosage simulation (e.g., Trisomy 21: 1.5x expression of chromosome 21 genes)
- CRISPR guide RNA design across the entire genome
- Primer design for any genomic locus
- Interactive genome editor for designing edits and simulating outcomes

## 2. Supported Genome Assemblies

| Organism | Common Name | Accession | Chromosomes |
|----------|-------------|-----------|-------------|
| Homo sapiens | Human | GRCh38 / GRCh38.p14 | 1-22, X, Y, MT |
| Mus musculus | Mouse | GRCm39 | 1-19, X, Y, MT |
| Rattus norvegicus | Rat | GRCr7 | 1-20, X, Y, MT |
| Danio rerio | Zebrafish | GRCz11 | 1-25, X, Y |
| Drosophila melanogaster | Fruit Fly | dm6 / BDGP6 | 2L, 2R, 3L, 3R, 4, X, Y, MT |
| Caenorhabditis elegans | C. elegans | WBcel235 | I, II, III, IV, V, X, MT |
| Arabidopsis thaliana | Mouse-ear Cress | TAIR10 / Araport11 | 1, 2, 3, 4, 5, MT, PT |
| Saccharomyces cerevisiae | Yeast | R64-1-1 / UCSC sacCer3 | 1-16, MT |

## 3. Data Schema

### 3.1 Chromosome Level

```
Chromosome:
  - accession: str           # e.g., "CM000686.2" (RefSeq) or "chr1" (UCSC)
  - name: str                # e.g., "1", "chr1", "X", "MT"
  - organism: str            # e.g., "Homo sapiens"
  - assembly: str           # e.g., "GRCh38"
  - length_bp: int          # Total length in base pairs
  - sequence: bytes         # Full sequence (A, T, G, C, N)
  - is_circular: bool       # True for MT (mitochondrial) chromosomes
  - centromere_start: int   # Centromere region start (bp)
  - centromere_end: int     # Centromere region end (bp)
  - band_count: int         # Number of cytogenetic bands
```

### 3.2 Gene Level

```
Gene:
  - gene_id: str             # Ensembl ID: "ENSG00000139618"
  - symbol: str              # HGNC symbol: "BRCA2"
  - name: str                # Full name: "BRCA2 DNA repair associated"
  - chromosome: str          # "chr13"
  - start_bp: int            # Genomic start position (1-indexed)
  - end_bp: int              # Genomic end position
  - strand: Literal["+", "-"]
  - biotype: str            # protein_coding, lncRNA, miRNA, etc.
  - status: str              # KNOWN, NOVEL, PUTATIVE
  - description: str
  - xref_ids: dict           # External references: {db: id}
  - aliases: list[str]
  - phenotype_ids: list[str]  # OMIM phenotypes
  - dbsnp_ids: list[str]
```

### 3.3 Transcript and Exon Structure

```
Transcript:
  - transcript_id: str       # Ensembl: "ENST00000380152"
  - gene_id: str             # Parent gene
  - chromosome: str
  - start_bp: int
  - end_bp: int
  - strand: Literal["+", "-"]
  - biotype: str
  - is_canonical: bool
  - cds_start_bp: int        # CDS start (if applicable)
  - cds_end_bp: int
  - exons: list[Exon]
  - cds序列: bytes            # Coding sequence

Exon:
  - exon_id: str
  - transcript_id: str
  - chromosome: str
  - start_bp: int
  - end_bp: int
  - strand: Literal["+", "-"]
  - exon_number: int         # Order in transcript
  - cds_start_offset: int   # Offset within CDS
  - cds_end_offset: int
  - sequence: bytes
```

### 3.4 Regulatory Regions

```
RegulatoryRegion:
  - region_id: str           # Unique identifier
  - chromosome: str
  - start_bp: int
  - end_bp: int
  - feature_type: str        # promoter, enhancer, silencer, insulator, CTFC binding site
  - activity: str             # active, poised, repressed, inactive
  - associated_genes: list[str]
  - cell_types: list[str]    # Cell types where active
  - эпигенetic_marks: dict  # H3K27ac, H3K4me1, etc.
```

### 3.5 Genetic Variants

```
SNP/SNV:
  - variant_id: str          # rsID: "rs699" or coordinate-based
  - chromosome: str
  - position_bp: int        # 1-indexed position
  - ref_allele: str          # Reference base(s)
  - alt_allele: str          # Alternate base(s)
  - variant_type: str        # SNP, insertion, deletion, MN V, structural
  - allele_freq: float       # Global minor allele frequency
  - population_freqs: dict   # {african: 0.2, european: 0.4, ...}
  - clinical_significance: list[str]  # benign, pathogenic, likely_pathogenic, etc.
  - associated_traits: list[str]
  - sift_prediction: str     # damaging, tolerated
  - polyphen_prediction: str  # probably_damaging, benign
  - consequence: str         # upstream_gene_variant, missense_variant, etc.

CNV (Copy Number Variation):
  - cnv_id: str
  - chromosome: str
  - start_bp: int
  - end_bp: int
  - copy_number: int         # 0=deleted, 1=hemizygous, 2=diploid, 3=trisomy
  - cnv_type: str            # deletion, duplication, amplification
  - confidence: float
  - allele_freq: float
```

### 3.6 Repeat Elements

```
RepeatElement:
  - repeat_id: str
  - chromosome: str
  - start_bp: int
  - end_bp: int
  - repeat_class: str        # SINE, LINE, LTR, DNA, Simple_repeat, etc.
  - repeat_family: str       # Alu, L1, ERV1, etc.
  - repeat_unit: str         # Monomer repeat unit
  - repeat_count: float     # Number of repeat units
  - divergence_pct: float   # Divergence from consensus
```

## 4. Core Data Structures

### 4.1 Genome Assembly

```python
@dataclass
class GenomeAssembly:
    organism: str
    name: str                 # e.g., "GRCh38"
    accession: str            # GCF_000001405.39
    chromosomes: dict[str, Chromosome]
    genes: dict[str, Gene]
    transcripts: dict[str, Transcript]
    regulatory_regions: list[RegulatoryRegion]
    variants: dict[str, list[Variant]]  # variants by chromosome
    repeats: list[RepeatElement]
    metadata: dict            # Build date, source, version
```

### 4.2 Interval Tree for Spatial Queries

For efficient range queries (e.g., "find all genes in region chr1:1000000-2000000"):

```python
class GenomicIntervalTree:
    """Interval tree optimized for genomic coordinate queries."""
    
    def __init__(self):
        self._intervals: dict[str, IntervalTree] = {}  # by chromosome
    
    def add_interval(self, chrom: str, start: int, end: int, data: Any):
        """Add an interval to the tree."""
    
    def query(self, chrom: str, start: int, end: int) -> list[tuple[int, int, Any]]:
        """Return all intervals overlapping [start, end]."""
    
    def query_point(self, chrom: str, position: int) -> list[tuple[int, int, Any]]:
        """Return all intervals containing this position."""
```

### 4.3 Sequence Utilities

```python
class GenomicSequence:
    """Handle genomic sequences with efficient subsequence access."""
    
    BASES = {'A', 'T', 'G', 'C', 'N'}
    COMPLEMENT = str.maketrans('ATGC', 'TACG')
    
    @staticmethod
    def complement(seq: str) -> str:
        """Return reverse complement of DNA sequence."""
    
    @staticmethod
    def reverse_complement(seq: str) -> str:
        """Return reverse complement of DNA sequence."""
    
    @staticmethod
    def transcribe(seq: str) -> str:
        """Convert DNA to RNA (T -> U)."""
    
    @staticmethod
    def translate(seq: str, frame: int = 0) -> str:
        """Translate DNA/RNA to amino acid sequence."""
    
    @staticmethod
    def gc_content(seq: str) -> float:
        """Calculate GC content percentage."""
    
    @staticmethod
    def find_motifs(seq: str, motif: str) -> list[int]:
        """Find all occurrences of a motif."""
```

## 5. Variant Effect Prediction

### 5.1 VEP-Style Consequence Prediction

```python
class VariantEffectPredictor:
    """Predict variant effects on genes and transcripts."""
    
    CONSEQUENCE_TERMS = {
        'transcript_ablation',           # >90% of coding sequence deleted
        'splice_donor_variant',          # First two bases of intron
        'splice_acceptor_variant',        # Last two bases of intron
        'stop_gained',                    # Nonsense mutation
        'frameshift_variant',             # Insertion/deletion not multiple of 3
        'stop_lost',                      # Stop codon changed
        'start_lost',                     # Start codon changed
        'stop_retained_variant',          # Stop codon unchanged
        'missense_variant',               # Amino acid change
        'protein_altering_variant',       # In-frame insertion/deletion
        'splice_region_variant',          # Within 3bp of splice site
        'incomplete_terminal_codon_variant',
        'synonymous_variant',            # No amino acid change
        'coding_sequence_variant',
        'mature_miRNA_variant',
        '5_prime_UTR_variant',
        '3_prime_UTR_variant',
        'intron_variant',
        'upstream_gene_variant',         # >1kb upstream
        'downstream_gene_variant',        # >1kb downstream
        'intergenic_variant',
        'regulatory_region_variant',
        'feature_elongation',
        'feature_truncation',
    }
    
    def predict(
        self,
        variant: Variant,
        assembly: GenomeAssembly,
        transcripts: list[Transcript]
    ) -> list[VariantConsequence]:
        """Predict all consequences of a variant."""
    
    def get_protein_effect(
        self,
        ref_aa: str,
        alt_aa: str,
        position: int
    ) -> ProteinEffect:
        """Determine protein-level effect."""
```

### 5.2 SIFT/PolyPhen-style Scoring

```python
@dataclass
class ConservationScore:
    phastcons: float          # 0-1, evolutionary conservation
    phylop: float             # -1 to 1, conservation magnitude
    primate_phastcons: float
    mammalian_phastcons: float
    
@dataclass
class FunctionalScore:
    sift_score: float          # 0-1, lower = more damaging
    sift_prediction: str
    polyphen_score: float      # 0-1, higher = more damaging
    polyphen_prediction: str
    fathmm_score: float
    fathmm_prediction: str
    revel_score: float         # 0-1, higher = more damaging
```

## 6. Gene Dosage Simulation

### 6.1 Dosage Effect Model

```python
class DosageSimulator:
    """Simulate gene dosage effects (e.g., trisomies, deletions)."""
    
    def simulate_trisomy(
        self,
        assembly: GenomeAssembly,
        chromosome: str,
        extra_copy_factor: float = 1.5  # 1.5 = 50% increase (trisomy)
    ) -> DosageEffect:
        """Simulate effect of extra chromosome copy."""
    
    def get_gene_expression_multiplier(
        self,
        gene: Gene,
        copy_number: int,
        baseline: float = 1.0
    ) -> float:
        """Calculate expression multiplier based on copy number."""
        # diploid = 1.0, trisomy = 1.5, monosomy = 0.5, deletion = 0
    
    def predict_phenotype(
        self,
        assembly: GenomeAssembly,
        dosage_changes: dict[str, int]  # chr -> copy_number
    ) -> list[PhenotypeAssociation]:
        """Predict phenotypic consequences."""
```

### 6.2 Example: Trisomy 21 Phenotype Mapping

```python
# Human chromosome 21 contains ~500 genes
# Trisomy 21 -> 1.5x expression of all chr21 genes
# Key phenotype-relevant genes:
# - APP (Alzheimer's disease)
# - SOD1 (Amyotrophic lateral sclerosis)
# - CBS (Homocystinuria)
# - HLCS (Holocarboxylase synthetase)
```

## 7. CRISPR Guide Design

### 7.1 Guide RNA Design

```python
class CRISPRGuideDesigner:
    """Design CRISPR/Cas9 guide RNAs."""
    
    PAM_SITES = {
        'SpCas9': 'NGG',
        'Cas12a': 'TTTN',       # V3: NTTN
        'Cas9_NGG_1': 'NGG',
        'Cas9_NGA_1': 'NGA',    # eSpCas9
        'Cas9_NGC_1': 'NGC',    # HypaCas9
        'Cas9_NGT_1': 'NGT',    # xCas9
    }
    
    def find_guides(
        self,
        sequence: str,
        pam: str = 'NGG',
        min_score: float = 0.5,
        off_target_limit: int = 10
    ) -> list[GuideRNA]:
        """Find all valid guide RNAs in sequence."""
    
    def score_guide(
        self,
        guide: str,
        assembly: GenomeAssembly,
        exclude_genome: bool = True
    ) -> GuideScore:
        """Score guide efficiency and specificity."""
    
    def check_off_targets(
        self,
        guide: str,
        assembly: GenomeAssembly,
        mismatches: int = 4
    ) -> list[OffTargetSite]:
        """Find potential off-target sites."""
```

### 7.2 Guide Score Model

```python
@dataclass
class GuideScore:
    on_target_efficiency: float   # Predicted cleavage efficiency (0-1)
    specificity_score: float      # Off-target specificity (0-1)
    doench_score: float           # Doench et al. 2014 model
    moreno_mateos_score: float    # Moreno-Mateos et al. 2015
    combined_score: float
    
@dataclass
class OffTargetSite:
    chromosome: str
    position: int
    mismatches: int
    alignment_score: float
    gene_context: str
    is_exonic: bool
```

## 8. Primer Design

### 8.1 Primer Design Engine

```python
class PrimerDesigner:
    """Design PCR primers for genomic loci."""
    
    DEFAULT_PARAMS = {
        'min_length': 18,
        'max_length': 25,
        'opt_length': 20,
        'min_tm': 57.0,
        'max_tm': 63.0,
        'opt_tm': 60.0,
        'max_tm_diff': 5.0,      # Between primer pair
        'min_gc': 40.0,
        'max_gc': 60.0,
        'opt_gc': 50.0,
        'max_poly_x': 4,         # Max homopolymer run
        'max_end_stability': 3.0,  # Max 3' stability (kcal/mol)
        'max_ngs_self': -3.0,    # Max self-complementarity
        'max_ngs_pair': -3.0,    # Max pair complementarity
    }
    
    def design_primer_pair(
        self,
        assembly: GenomeAssembly,
        target_start: int,
        target_end: int,
        chromosome: str,
        product_size_range: tuple[int, int] = (100, 300),
        params: dict = None
    ) -> list[PrimerPair]:
        """Design primer pairs for target region."""
    
    def design_sequencing_primers(
        self,
        assembly: GenomeAssembly,
        amplicon: str,
        direction: str = 'forward'
    ) -> list[Primer]:
        """Design Sanger sequencing primers."""
    
    def design_multiplex_primers(
        self,
        assembly: GenomeAssembly,
        targets: list[TargetRegion],
        params: dict = None
    ) -> list[PrimerPair]:
        """Design primers for multiplex PCR."""
```

### 8.2 Primer Dataclass

```python
@dataclass
class Primer:
    sequence: str
    length: int
    tm: float                   # Melting temperature (C)
    gc_content: float           # Percent GC
    position: int               # Genomic start position
    chromosome: str
    strand: str                 # '+' or '-'
    
    # Thermodynamic properties
    delta_g_3_prime: float      # 3' end stability
    self_complementarity: float
    
    # Specificity metrics
    genome_matches: int         # Number of perfect matches
    off_targets: list[GenomicLocation]
    
@dataclass
class PrimerPair:
    forward: Primer
    reverse: Primer
    product_size: int
    product_start: int
    product_end: int
    chromosome: str
    amplicon_sequence: str
    coverage_score: float
```

## 9. Chromosome Browser Data

### 9.1 Multi-resolution View

```python
class ChromosomeBrowser:
    """Provide multi-resolution view of chromosome data."""
    
    ZOOM_LEVELS = {
        'chromosome': 'entire chromosome (1 view)',
        'band': 'cytogenetic bands',
        'region': '1-10 Mb regions',
        'gene_cluster': '1-5 Mb with genes',
        'gene': 'individual gene level',
        'exon': 'transcript/exon structure',
        'base': 'single base pair resolution',
    }
    
    def get_chromosome_view(
        self,
        assembly: GenomeAssembly,
        chromosome: str,
        zoom_level: str,
        start_bp: int = None,
        end_bp: int = None
    ) -> ChromosomeView:
        """Get visualization data for chromosome region."""
    
    def get_gene_structure(
        self,
        gene_id: str,
        assembly: GenomeAssembly,
        include_flanking: int = 5000  # bp
    ) -> GeneStructure:
        """Get detailed gene structure for editor view."""
```

### 9.2 Browser Track Types

```python
@dataclass
class BrowserTrack:
    name: str
    track_type: str      # gene, variant, regulatory, repeat, alignment
    data: list           # Track-specific data items
    visibility: str      # hide, collapse, dense, squish, pack, full
    
@dataclass
class GeneTrack(BrowserTrack):
    pass  # Genes with transcript structures

@dataclass
class VariantTrack(BrowserTrack):
    pass  # SNPs, SNVs, CNVs

@dataclass
class RegulationTrack(BrowserTrack):
    pass  # Promoters, enhancers, etc.
```

## 10. Interactive Genome Editor

### 10.1 Edit Types

```python
class GenomeEditor:
    """Support various genomic edit operations."""
    
    @dataclass
    class Edit:
        chromosome: str
        start_bp: int
        end_bp: int
        edit_type: str          # substitution, insertion, deletion, inversion
        sequence: str           # For substitutions/insertions
        description: str
    
    def apply_edit(
        self,
        assembly: GenomeAssembly,
        edit: Edit
    ) -> EditedAssembly:
        """Apply an edit and return modified assembly."""
    
    def simulate_edit_outcome(
        self,
        assembly: GenomeAssembly,
        edit: Edit
    ) -> EditSimulation:
        """Predict consequences of an edit."""
```

### 10.2 Simulation Output

```python
@dataclass
class EditSimulation:
    original_sequence: str
    edited_sequence: str
    effect_on_transcripts: list[TranscriptEffect]
    effect_on_proteins: list[ProteinEffect]
    predicted_phenotype: list[PhenotypePrediction]
    off_target_predictions: list[OffTargetPrediction]
    efficiency_prediction: float
```

## 11. File Formats Supported

### 11.1 Input Formats

- **FASTA**: Raw genome sequences
- **GTF/GFF3**: Gene annotations
- **BED**: Genomic intervals
- **VCF**: Variant calls
- **Chain files**: Liftover between assemblies
- **BigWig/BigBed**: Browser track data

### 11.2 Output Formats

- **JSON**: Full structured data
- **CSV**: Tabular data (primers, variants, guides)
- **GenBank**: Sequence with annotations
- **VCF**: Variant calls
- **BED**: Genomic intervals
- **HTML**: Browser visualizations (UCSC-style)

## 12. Implementation Priorities

1. **Core data structures** (genome assembly, chromosomes, genes)
2. **Sequence utilities** (complement, translate, GC content)
3. **Interval tree** for efficient range queries
4. **Basic chromosome browser** (whole chromosome to gene level)
5. **Variant effect prediction** (consequence terms)
6. **Gene dosage simulation** (trisomy 21 model)
7. **CRISPR guide design** (SpCas9 NGG PAM)
8. **Primer design** (basic PCR primers)
9. **Genome editor** (substitutions, insertions, deletions)
10. **Full integration** with ChemLab game systems

## 13. Performance Considerations

- Chromosome sequences stored as bytes for memory efficiency
- Interval trees for O(log n) range queries
- Lazy loading of chromosome data (load on demand)
- Index files for rapid random access
- Compressed genome builds where memory is constrained
- Batch processing for large variant sets

## 14. Testing Strategy

- Unit tests for each data structure
- Property-based tests for sequence operations
- Integration tests with sample genomes
- Validation against known variant effects
- Primer design validation against Primer-BLAST
- Guide design validation against CRISPOR
