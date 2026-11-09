"""
ChemLab Genetics/PCR Simulation Engine.

Implements PCR thermal cycling, primer design, gel electrophoresis,
restriction digestion, Sanger sequencing, CRISPR-Cas9, qPCR, and Trisomy 21 simulation.
"""

import math
import random
from dataclasses import dataclass, field
from typing import Optional

try:
    from rdkit import Chem
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PCRStep:
    """Single step in a PCR thermal cycle."""
    name: str
    temperature_c: float
    hold_time_s: float
    ramp_rate_c_per_s: float = 4.0


@dataclass
class PCRCycle:
    """One PCR cycle with denaturation, annealing, extension."""
    denaturation: PCRStep
    annealing: PCRStep
    extension: PCRStep


@dataclass
class PCRProtocol:
    """Complete PCR protocol with initial denaturation, cycles, final extension, hold."""
    initial_denaturation: PCRStep
    cycles: list[PCRCycle]
    final_extension: PCRStep
    final_hold: PCRStep


@dataclass
class PCRResult:
    """Result of a PCR simulation."""
    protocol: PCRProtocol
    amplicon_copies: int
    amplification_efficiency: float
    ct_value: Optional[float] = None
    melt_curve: dict[float, float] = field(default_factory=dict)
    gel_bands: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class Primer:
    """PCR primer with sequence and properties."""
    sequence: str
    name: str = ""
    tm_c: float = 0.0
    gc_content_percent: float = 0.0
    length: int = 0
    hairpin_dg: float = 0.0
    dimer_dg: float = 0.0
    specificity_score: float = 1.0


@dataclass
class GelBand:
    """Band in gel electrophoresis."""
    size_bp: int
    intensity: float
    distance_mm: float
    label: str = ""


@dataclass
class GelElectrophoresisResult:
    """Result of gel electrophoresis simulation."""
    bands: list[GelBand]
    gel_percent: float
    voltage_v: float
    run_time_min: float
    marker_lanes: list[int] = field(default_factory=list)
    ladder: list[int] = field(default_factory=lambda: [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1500, 2000, 3000, 5000, 10000])


@dataclass
class RestrictionSite:
    """Single restriction enzyme cut site."""
    enzyme_name: str
    position: int
    sequence: str
    is_palindromic: bool = True


@dataclass
class DigestionResult:
    """Result of restriction digestion."""
    fragments: list[dict]  # {start, end, size_bp, sequence}
    enzyme_names: list[str]
    total_sites: int


@dataclass
class SangerResult:
    """Sanger sequencing result."""
    sequence: str
    quality_scores: list[int]
    chromatogram_peaks: list[dict]
    read_length: int
    trim_start: int = 0
    trim_end: int = 0


@dataclass
class SgRNA:
    """CRISPR guide RNA design."""
    target_sequence: str  # 20 nt target
    pam_sequence: str     # NGG for SpCas9
    genomic_position: int
    on_target_score: float
    off_targets: list[dict] = field(default_factory=list)
    gc_content: float = 0.0


@dataclass
class CRISPRResult:
    """CRISPR-Cas9 editing simulation result."""
    sgRNA: SgRNA
    indel_spectrum: dict[str, float]  # indel_type -> frequency
    editing_efficiency: float
    predicted_knockout: bool = False


@dataclass
class qPCRResult:
    """qPCR simulation result."""
    ct_value: float
    amplification_curve: list[tuple[int, float]]  # (cycle, fluorescence)
    melt_curve: dict[float, float]
    efficiency: float
    r_squared: float
    initial_copies: int


@dataclass
class Trisomy21Result:
    """Trisomy 21 (Down syndrome) simulation result."""
    chromosome_21_genes: list[dict]
    gene_dosage_effects: dict[str, float]
    phenotype_predictions: dict[str, float]
    aneuploidy_score: float


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_tm(sequence: str, na_conc_m: float = 0.05, mg_conc_m: float = 0.0015, dna_conc_nM: float = 250) -> float:
    """Calculate melting temperature using nearest-neighbor method (SantaLucia 1998)."""
    # Nearest-neighbor thermodynamic parameters (ΔH kcal/mol, ΔS cal/mol·K)
    nn_params = {
        'AA': (-7.9, -22.2), 'TT': (-7.9, -22.2),
        'AT': (-7.2, -20.4), 'TA': (-7.2, -21.3),
        'CA': (-8.5, -22.7), 'TG': (-8.5, -22.7),
        'GT': (-8.4, -22.4), 'AC': (-8.4, -22.4),
        'CT': (-7.8, -21.0), 'AG': (-7.8, -21.0),
        'GA': (-8.2, -22.2), 'TC': (-8.2, -22.2),
        'CG': (-10.6, -27.2), 'GC': (-9.8, -24.4),
        'GG': (-8.0, -19.9), 'CC': (-8.0, -19.9),
    }

    seq = sequence.upper()
    if len(seq) < 2:
        return 0.0

    delta_h = 0.0  # kcal/mol
    delta_s = 0.0  # cal/mol·K

    # Initiation terms
    delta_h += 0.2  # helix initiation
    delta_s += -5.7

    for i in range(len(seq) - 1):
        pair = seq[i:i+2]
        if pair in nn_params:
            h, s = nn_params[pair]
            delta_h += h
            delta_s += s

    # Symmetry correction for self-complementary
    if seq == str(Seq(seq).reverse_complement()):
        delta_s += -1.4

    # Salt correction (SantaLucia 1998)
    # Na+ correction
    delta_s += 0.368 * (len(seq) - 1) * math.log(na_conc_m)
    # Mg2+ correction
    if mg_conc_m > 0:
        delta_s += 0.368 * (len(seq) - 1) * math.log(mg_conc_m / (2 * na_conc_m))

    # Concentration correction
    r = 1.987  # cal/mol·K
    ct = dna_conc_nM * 1e-9
    tm_k = (delta_h * 1000) / (delta_s + r * math.log(ct / 4))
    tm_c = tm_k - 273.15

    return tm_c


def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content percentage."""
    seq = sequence.upper()
    gc = seq.count('G') + seq.count('C')
    return (gc / len(seq)) * 100 if seq else 0.0


def check_hairpin(sequence: str, min_stem: int = 4, max_loop: int = 30) -> tuple[bool, float]:
    """Check for hairpin formation, return (has_hairpin, deltaG)."""
    seq = sequence.upper()
    rev_comp = str(Seq(seq).reverse_complement())
    best_dg = 0.0
    has_hp = False

    for i in range(len(seq)):
        for stem_len in range(min_stem, min(10, len(seq) - i)):
            for loop_len in range(3, min(max_loop, len(seq) - i - stem_len)):
                stem1 = seq[i:i+stem_len]
                loop_end = i + stem_len + loop_len
                if loop_end + stem_len > len(seq):
                    continue
                stem2 = seq[loop_end:loop_end+stem_len]
                if stem1 == str(Seq(stem2).reverse_complement()):
                    # Calculate dG for this hairpin
                    dg = calculate_tm(stem1) * -0.1  # rough approximation
                    if dg < best_dg:
                        best_dg = dg
                        has_hp = True

    return has_hp, best_dg


def check_dimer(primer1: str, primer2: str) -> tuple[bool, float]:
    """Check for primer-dimer formation."""
    # Check 3' complementarity
    max_check = min(8, len(primer1), len(primer2))
    best_dg = 0.0
    has_dimer = False

    for i in range(1, max_check + 1):
        end1 = primer1[-i:]
        end2 = primer2[-i:]
        if end1 == str(Seq(end2).reverse_complement()):
            dg = calculate_tm(end1) * -0.1
            if dg < best_dg:
                best_dg = dg
                has_dimer = True

    return has_dimer, best_dg


def check_specificity(primer: str, genome: str, max_mismatches: int = 3) -> float:
    """Check primer specificity against genome."""
    # Simplified: count approximate matches
    primer_len = len(primer)
    matches = 0
    for i in range(len(genome) - primer_len + 1):
        mismatches = sum(1 for a, b in zip(primer, genome[i:i+primer_len]) if a != b)
        if mismatches <= max_mismatches:
            matches += 1

    # Specificity score: 1.0 = unique, 0.0 = many matches
    if matches <= 1:
        return 1.0
    return max(0.0, 1.0 - (matches - 1) * 0.1)


def design_primers(template: str, target_start: int, target_end: int,
                   opt_tm: float = 60.0, min_tm: float = 55.0, max_tm: float = 65.0,
                   min_gc: float = 40.0, max_gc: float = 60.0,
                   min_len: int = 18, max_len: int = 27) -> tuple[Optional[Primer], Optional[Primer]]:
    """Design forward and reverse primers for a target region."""
    target_seq = template[target_start:target_end]

    best_fwd = None
    best_rev = None
    best_score = -1

    # Search for forward primer
    for length in range(min_len, max_len + 1):
        for start in range(max(0, target_start - 100), target_start):
            if start + length > len(template):
                continue
            seq = template[start:start+length]
            tm = calculate_tm(seq)
            gc = calculate_gc_content(seq)
            if min_tm <= tm <= max_tm and min_gc <= gc <= max_gc:
                hairpin, hp_dg = check_hairpin(seq)
                if not hairpin:
                    score = 1.0 - abs(tm - opt_tm) / 10.0
                    if score > best_score:
                        best_score = score
                        best_fwd = Primer(
                            sequence=seq, name=f"Fwd_{start}",
                            tm_c=tm, gc_content_percent=gc, length=length,
                            hairpin_dg=hp_dg, specificity_score=check_specificity(seq, template)
                        )

    # Search for reverse primer (on reverse complement)
    rev_template = str(Seq(template).reverse_complement())
    target_rev_start = len(template) - target_end
    target_rev_end = len(template) - target_start

    best_score = -1
    for length in range(min_len, max_len + 1):
        for start in range(max(0, target_rev_start - 100), target_rev_start):
            if start + length > len(rev_template):
                continue
            seq = rev_template[start:start+length]
            tm = calculate_tm(seq)
            gc = calculate_gc_content(seq)
            if min_tm <= tm <= max_tm and min_gc <= gc <= max_gc:
                hairpin, hp_dg = check_hairpin(seq)
                if not hairpin:
                    dimer_check, _ = check_dimer(seq, best_fwd.sequence) if best_fwd else (False, 0)
                    if not dimer_check:
                        score = 1.0 - abs(tm - opt_tm) / 10.0
                        if score > best_score:
                            best_score = score
                            best_rev = Primer(
                                sequence=seq, name=f"Rev_{start}",
                                tm_c=tm, gc_content_percent=gc, length=length,
                                hairpin_dg=hp_dg, specificity_score=check_specificity(seq, rev_template)
                            )

    return best_fwd, best_rev


# Helper class for sequence operations
class Seq:
    """Simple DNA sequence operations."""
    def __init__(self, seq: str):
        self.seq = seq.upper()

    def reverse_complement(self) -> str:
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
        return ''.join(complement.get(b, 'N') for b in reversed(self.seq))

    def __str__(self):
        return self.seq


# ============================================================================
# Genetics Engine
# ============================================================================

class GeneticsEngine:
    """Complete genetics/PCR simulation engine."""

    def __init__(self):
        self.genomic_database = self._load_genomic_data()

    def _load_genomic_data(self) -> dict:
        """Load reference genomic sequences."""
        # Minimal reference data for human chromosome 21
        return {
            "chr21": "N" * 48000000,  # Placeholder - in reality would load from FASTA
            "genes_chr21": {
                "APP": {"start": 27000000, "end": 27300000, "function": "Amyloid precursor protein"},
                "SOD1": {"start": 33000000, "end": 33100000, "function": "Superoxide dismutase"},
                "DSCR1": {"start": 35000000, "end": 35100000, "function": "Down syndrome critical region"},
                "ETS2": {"start": 38000000, "end": 38200000, "function": "Transcription factor"},
                "RUNX1": {"start": 36000000, "end": 36200000, "function": "Runt-related transcription factor"},
            }
        }

    # -----------------------------------------------------------------------
    # PCR Thermal Cycling
    # -----------------------------------------------------------------------

    def simulate_pcr_cycle(self, cycle: PCRCycle, initial_copies: int = 1) -> dict:
        """Simulate a single PCR cycle."""
        # Denaturation
        denat_eff = 1.0 - math.exp(-cycle.denaturation.hold_time_s / 30.0)

        # Annealing
        anneal_eff = 1.0 - math.exp(-cycle.annealing.hold_time_s / 20.0)

        # Extension
        ext_eff = 1.0 - math.exp(-cycle.extension.hold_time_s / 60.0)

        cycle_efficiency = denat_eff * anneal_eff * ext_eff
        new_copies = initial_copies * (1 + cycle_efficiency)

        return {
            "cycles_completed": 1,
            "copies": new_copies,
            "cycle_efficiency": cycle_efficiency,
        }

    def simulate_pcr(self, protocol: PCRProtocol, initial_copies: int = 1) -> PCRResult:
        """Simulate complete PCR protocol."""
        copies = initial_copies
        total_efficiency = 0.0

        for cycle in protocol.cycles:
            result = self.simulate_pcr_cycle(cycle, copies)
            copies = result["copies"]
            total_efficiency += result["cycle_efficiency"]

        avg_efficiency = total_efficiency / len(protocol.cycles) if protocol.cycles else 0

        # Calculate Ct value (threshold at 1e9 copies)
        threshold = 1e9
        if copies >= threshold and initial_copies > 0:
            ct = math.log(threshold / initial_copies) / math.log(1 + avg_efficiency)
        else:
            ct = None

        # Generate melt curve
        melt_curve = self.generate_melt_curve(copies)

        # Predict gel bands
        gel_bands = self._predict_gel_bands(protocol)

        return PCRResult(
            protocol=protocol,
            amplicon_copies=int(copies),
            amplification_efficiency=avg_efficiency,
            ct_value=ct,
            melt_curve=melt_curve,
            gel_bands=gel_bands,
        )

    def _predict_gel_bands(self, protocol: PCRProtocol) -> list[dict]:
        """Predict gel electrophoresis bands from PCR."""
        amplicon_size = 1000  # default
        # Calculate final copies
        copies = 1
        for cycle in protocol.cycles:
            result = self.simulate_pcr_cycle(cycle, copies)
            copies = result["copies"]
        return [
            {"size_bp": amplicon_size, "intensity": min(1.0, copies / 1e12), "label": "PCR Product"},
            {"size_bp": 50, "intensity": 0.1, "label": "Primer Dimer"},
        ]

    # -----------------------------------------------------------------------
    # Primer Design - Module-level functions as class methods
    # -----------------------------------------------------------------------

    def calculate_tm(self, sequence: str, na_conc_m: float = 0.05, mg_conc_m: float = 0.0015, dna_conc_nM: float = 250) -> float:
        """Calculate melting temperature using nearest-neighbor method (SantaLucia 1998)."""
        # Nearest-neighbor thermodynamic parameters (ΔH kcal/mol, ΔS cal/mol·K)
        nn_params = {
            'AA': (-7.9, -22.2), 'TT': (-7.9, -22.2),
            'AT': (-7.2, -20.4), 'TA': (-7.2, -21.3),
            'CA': (-8.5, -22.7), 'TG': (-8.5, -22.7),
            'GT': (-8.4, -22.4), 'AC': (-8.4, -22.4),
            'CT': (-7.8, -21.0), 'AG': (-7.8, -21.0),
            'GA': (-8.2, -22.2), 'TC': (-8.2, -22.2),
            'CG': (-10.6, -27.2), 'GC': (-9.8, -24.4),
            'GG': (-8.0, -19.9), 'CC': (-8.0, -19.9),
        }

        seq = sequence.upper()
        if len(seq) < 2:
            return 0.0

        delta_h = 0.0  # kcal/mol
        delta_s = 0.0  # cal/mol·K

        # Initiation terms
        delta_h += 0.2  # helix initiation
        delta_s += -5.7

        for i in range(len(seq) - 1):
            pair = seq[i:i+2]
            if pair in nn_params:
                h, s = nn_params[pair]
                delta_h += h
                delta_s += s

        # Symmetry correction for self-complementary
        if seq == str(Seq(seq).reverse_complement()):
            delta_s += -1.4

        # Salt correction (SantaLucia 1998)
        # Na+ correction
        delta_s += 0.368 * (len(seq) - 1) * math.log(na_conc_m)
        # Mg2+ correction
        if mg_conc_m > 0:
            delta_s += 0.368 * (len(seq) - 1) * math.log(mg_conc_m / (2 * na_conc_m))

        # Concentration correction
        r = 1.987  # cal/mol·K
        ct = dna_conc_nM * 1e-9
        tm_k = (delta_h * 1000) / (delta_s + r * math.log(ct / 4))
        tm_c = tm_k - 273.15

        return tm_c

    def calculate_gc_content(self, sequence: str) -> float:
        """Calculate GC content percentage."""
        seq = sequence.upper()
        gc = seq.count('G') + seq.count('C')
        return (gc / len(seq)) * 100 if seq else 0.0

    def check_hairpin(self, sequence: str, min_stem: int = 4, max_loop: int = 30) -> tuple[bool, float]:
        """Check for hairpin formation, return (has_hairpin, deltaG)."""
        seq = sequence.upper()
        rev_comp = str(Seq(seq).reverse_complement())
        best_dg = 0.0
        has_hp = False

        for i in range(len(seq)):
            for stem_len in range(min_stem, min(10, len(seq) - i)):
                for loop_len in range(3, min(max_loop, len(seq) - i - stem_len)):
                    stem1 = seq[i:i+stem_len]
                    loop_end = i + stem_len + loop_len
                    if loop_end + stem_len > len(seq):
                        continue
                    stem2 = seq[loop_end:loop_end+stem_len]
                    if stem1 == str(Seq(stem2).reverse_complement()):
                        # Calculate dG for this hairpin
                        dg = self.calculate_tm(stem1) * -0.1  # rough approximation
                        if dg < best_dg:
                            best_dg = dg
                            has_hp = True

        return has_hp, best_dg

    def check_dimer(self, primer1: str, primer2: str) -> tuple[bool, float]:
        """Check for primer-dimer formation."""
        # Check 3' complementarity
        max_check = min(8, len(primer1), len(primer2))
        best_dg = 0.0
        has_dimer = False

        for i in range(1, max_check + 1):
            end1 = primer1[-i:]
            end2 = primer2[-i:]
            if end1 == str(Seq(end2).reverse_complement()):
                dg = self.calculate_tm(end1) * -0.1
                if dg < best_dg:
                    best_dg = dg
                    has_dimer = True

        return has_dimer, best_dg

    def check_specificity(self, primer: str, genome: str, max_mismatches: int = 3) -> float:
        """Check primer specificity against genome."""
        # Simplified: count approximate matches
        primer_len = len(primer)
        matches = 0
        for i in range(len(genome) - primer_len + 1):
            mismatches = sum(1 for a, b in zip(primer, genome[i:i+primer_len]) if a != b)
            if mismatches <= max_mismatches:
                matches += 1

        # Specificity score: 1.0 = unique, 0.0 = many matches
        if matches <= 1:
            return 1.0
        return max(0.0, 1.0 - (matches - 1) * 0.1)

    def design_primers(self, template: str, target_start: int, target_end: int,
                       opt_tm: float = 60.0, min_tm: float = 55.0, max_tm: float = 65.0,
                       min_gc: float = 40.0, max_gc: float = 60.0,
                       min_len: int = 18, max_len: int = 27) -> tuple[Optional[Primer], Optional[Primer]]:
        """Design PCR primers for a target region."""
        target_seq = template[target_start:target_end]

        best_fwd = None
        best_rev = None
        best_score = -1

        # Search for forward primer
        for length in range(min_len, max_len + 1):
            for start in range(max(0, target_start - 100), target_start):
                if start + length > len(template):
                    continue
                seq = template[start:start+length]
                tm = self.calculate_tm(seq)
                gc = self.calculate_gc_content(seq)
                if min_tm <= tm <= max_tm and min_gc <= gc <= max_gc:
                    hairpin, hp_dg = self.check_hairpin(seq)
                    if not hairpin:
                        score = 1.0 - abs(tm - opt_tm) / 10.0
                        if score > best_score:
                            best_score = score
                            best_fwd = Primer(
                                sequence=seq, name=f"Fwd_{start}",
                                tm_c=tm, gc_content_percent=gc, length=length,
                                hairpin_dg=hp_dg, specificity_score=self.check_specificity(seq, template)
                            )

        # Search for reverse primer (on reverse complement)
        rev_template = str(Seq(template).reverse_complement())
        target_rev_start = len(template) - target_end
        target_rev_end = len(template) - target_start

        best_score = -1
        for length in range(min_len, max_len + 1):
            for start in range(max(0, target_rev_start - 100), target_rev_start):
                if start + length > len(rev_template):
                    continue
                seq = rev_template[start:start+length]
                tm = self.calculate_tm(seq)
                gc = self.calculate_gc_content(seq)
                if min_tm <= tm <= max_tm and min_gc <= gc <= max_gc:
                    hairpin, hp_dg = self.check_hairpin(seq)
                    if not hairpin:
                        dimer_check, _ = self.check_dimer(seq, best_fwd.sequence) if best_fwd else (False, 0)
                        if not dimer_check:
                            score = 1.0 - abs(tm - opt_tm) / 10.0
                            if score > best_score:
                                best_score = score
                                best_rev = Primer(
                                    sequence=seq, name=f"Rev_{start}",
                                    tm_c=tm, gc_content_percent=gc, length=length,
                                    hairpin_dg=hp_dg, specificity_score=self.check_specificity(seq, rev_template)
                                )

        return best_fwd, best_rev

    # -----------------------------------------------------------------------
    # Gel Electrophoresis
    # -----------------------------------------------------------------------

    def simulate_gel_electrophoresis(self, fragments: list[dict],
                                     gel_percent: float = 1.0,
                                     voltage_v: float = 100,
                                     run_time_min: float = 45) -> GelElectrophoresisResult:
        """Simulate agarose gel electrophoresis."""
        bands = []
        for frag in fragments:
            size = frag.get("size_bp", 1000)
            # Migration distance (simplified)
            distance = 100 - (math.log10(size) * 15) + random.uniform(-2, 2)
            distance = max(5, min(95, distance))

            bands.append(GelBand(
                size_bp=size,
                intensity=frag.get("intensity", 1.0),
                distance_mm=distance,
                label=frag.get("label", f"{size} bp")
            ))

        return GelElectrophoresisResult(
            bands=sorted(bands, key=lambda b: -b.distance_mm),
            gel_percent=gel_percent,
            voltage_v=voltage_v,
            run_time_min=run_time_min,
        )

    # -----------------------------------------------------------------------
    # Restriction Digestion
    # -----------------------------------------------------------------------

    def digest_dna(self, sequence: str, enzymes: list[str]) -> DigestionResult:
        """Simulate restriction enzyme digestion."""
        # Common restriction enzymes
        enzyme_sites = {
            "EcoRI": "GAATTC",
            "BamHI": "GGATCC",
            "HindIII": "AAGCTT",
            "XhoI": "CTCGAG",
            "NotI": "GCGGCCGC",
            "SacI": "GAGCTC",
            "KpnI": "GGTACC",
            "PstI": "CTGCAG",
            "SalI": "GTCGAC",
            "SmaI": "CCCGGG",
            "BglII": "AGATCT",
            "XbaI": "TCTAGA",
            "ClaI": "ATCGAT",
            "NcoI": "CCATGG",
            "NdeI": "CATATG",
        }

        sites = []
        for enzyme in enzymes:
            if enzyme not in enzyme_sites:
                continue
            site_seq = enzyme_sites[enzyme]
            pos = 0
            while True:
                idx = sequence.find(site_seq, pos)
                if idx == -1:
                    break
                sites.append(RestrictionSite(
                    enzyme_name=enzyme,
                    position=idx,
                    sequence=site_seq,
                    is_palindromic=True
                ))
                pos = idx + 1

        sites.sort(key=lambda s: s.position)

        # Generate fragments
        fragments = []
        last_pos = 0
        for site in sites:
            fragments.append({
                "start": last_pos,
                "end": site.position + len(enzyme_sites[site.enzyme_name]),
                "size_bp": site.position - last_pos + len(enzyme_sites[site.enzyme_name]),
                "sequence": sequence[last_pos:site.position + len(enzyme_sites[site.enzyme_name])]
            })
            last_pos = site.position + len(enzyme_sites[site.enzyme_name])

        # Last fragment
        if last_pos < len(sequence):
            fragments.append({
                "start": last_pos,
                "end": len(sequence),
                "size_bp": len(sequence) - last_pos,
                "sequence": sequence[last_pos:]
            })

        return DigestionResult(
            fragments=fragments,
            enzyme_names=enzymes,
            total_sites=len(sites)
        )

    # -----------------------------------------------------------------------
    # Sanger Sequencing
    # -----------------------------------------------------------------------

    def simulate_sanger_sequencing(self, template: str, primer: str,
                                   read_length: int = 800,
                                   error_rate: float = 0.005) -> SangerResult:
        """Simulate Sanger sequencing."""
        # Find primer binding site
        primer_rc = str(Seq(primer).reverse_complement())
        start = template.find(primer_rc)
        if start == -1:
            start = 0

        # Read sequence
        end = min(start + read_length, len(template))
        seq = template[start:end]

        # Add errors
        quality = []
        chromatogram = []
        seq_list = list(seq)
        bases = ['A', 'T', 'G', 'C']

        for i, base in enumerate(seq_list):
            q = int(-10 * math.log10(error_rate)) if random.random() > error_rate else int(-10 * math.log10(0.5))
            quality.append(q)

            if random.random() < error_rate:
                seq_list[i] = random.choice([b for b in bases if b != base])

            # Chromatogram peak
            chromatogram.append({
                "position": i,
                "base": seq_list[i],
                "height": random.uniform(0.5, 1.0),
                "width": random.uniform(0.8, 1.2)
            })

        return SangerResult(
            sequence=''.join(seq_list),
            quality_scores=quality,
            chromatogram_peaks=chromatogram,
            read_length=len(seq_list),
            trim_start=0,
            trim_end=len(seq_list)
        )

    # -----------------------------------------------------------------------
    # CRISPR-Cas9
    # -----------------------------------------------------------------------

    def design_sgrna(self, target_sequence: str, genome: str = "") -> SgRNA:
        """Design sgRNA for CRISPR-Cas9 (SpCas9, NGG PAM)."""
        if len(target_sequence) != 20:
            raise ValueError("Target sequence must be 20 nucleotides")

        # Check for PAM
        pam = "NGG"
        has_pam = target_sequence[-2:] == "GG" or (len(target_sequence) > 20 and target_sequence[20:22] == "GG")

        # Calculate scores
        gc = calculate_gc_content(target_sequence)

        # On-target score (simplified Doench 2016)
        on_target = 0.5 + (gc - 50) * 0.01 + random.uniform(-0.1, 0.1)
        on_target = max(0.0, min(1.0, on_target))

        # Off-target prediction
        off_targets = []
        if genome:
            for i in range(len(genome) - 22):
                window = genome[i:i+23]
                if window[-2:] == "GG":
                    mismatches = sum(1 for a, b in zip(target_sequence, window[:20]) if a != b)
                    if 1 <= mismatches <= 4:
                        off_targets.append({
                            "position": i,
                            "sequence": window[:20],
                            "mismatches": mismatches,
                            "score": 1.0 / (mismatches * 2)
                        })

        return SgRNA(
            target_sequence=target_sequence,
            pam_sequence="NGG",
            genomic_position=0,
            on_target_score=on_target,
            off_targets=off_targets[:10],
            gc_content=gc
        )

    def simulate_indels(self, sgRNA: SgRNA, cell_type: str = "HEK293") -> CRISPRResult:
        """Simulate CRISPR indel outcomes."""
        # Indel spectrum based on empirical data (Allen et al. 2018)
        indel_types = {
            "-1": 0.35,   # 1bp deletion (most common)
            "+1": 0.25,   # 1bp insertion
            "-2": 0.10,
            "-3": 0.08,
            "-4": 0.05,
            "-5": 0.04,
            "-10": 0.03,
            "-20": 0.02,
            "+2": 0.03,
            "+3": 0.02,
            "complex": 0.03,
        }

        # Normalize
        total = sum(indel_types.values())
        indel_spectrum = {k: v/total for k, v in indel_types.items()}

        # Knockout prediction: frameshift in coding region
        frameshift_prob = sum(v for k, v in indel_spectrum.items() if k.startswith('-') and int(k[1:]) % 3 != 0)
        frameshift_prob += sum(v for k, v in indel_spectrum.items() if k.startswith('+') and int(k[1:]) % 3 != 0)

        return CRISPRResult(
            sgRNA=sgRNA,
            indel_spectrum=indel_spectrum,
            editing_efficiency=sgRNA.on_target_score,
            predicted_knockout=frameshift_prob > 0.5
        )

    def predict_off_targets(self, sgRNA: SgRNA, genome: str) -> list[dict]:
        """Predict off-target effects for an sgRNA."""
        off_targets = []
        target = sgRNA.target_sequence
        if not genome:
            return off_targets

        for i in range(len(genome) - 22):
            window = genome[i:i+23]
            if window[-2:] == "GG":
                mismatches = sum(1 for a, b in zip(target, window[:20]) if a != b)
                if 1 <= mismatches <= 4:
                    off_targets.append({
                        "position": i,
                        "sequence": window[:20],
                        "mismatches": mismatches,
                        "score": 1.0 / (mismatches * 2)
                    })
        return off_targets[:10]

    def check_pam(self, target_sequence: str) -> bool:
        """Check for PAM sequence (NGG)."""
        return len(target_sequence) >= 2 and target_sequence[-2:] == "GG"

    def simulate_gene_dosage(self, gene_symbol: str, copy_number: int) -> dict:
        """Simulate gene dosage effect for a specific gene."""
        baseline = 2  # Normal diploid
        fold_change = copy_number / baseline

        # Non-linear compensation
        if fold_change > 1:
            # Overexpression with compensation
            effective_fc = 1 + (fold_change - 1) * 0.7
        else:
            # Underexpression
            effective_fc = fold_change

        return {
            "gene": gene_symbol,
            "copy_number": copy_number,
            "theoretical_fold_change": fold_change,
            "effective_fold_change": effective_fc,
            "compensation_factor": effective_fc / fold_change if fold_change != 1 else 1.0
        }

    # -----------------------------------------------------------------------
    # qPCR
    # -----------------------------------------------------------------------

    def simulate_qpcr(self, initial_copies: int, efficiency: float = 0.9,
                      cycles: int = 40, threshold_fluorescence: float = 1000.0) -> qPCRResult:
        """Simulate qPCR amplification curve and Ct calculation."""
        fluorescence = []
        copies = initial_copies

        for cycle in range(cycles + 1):
            if cycle == 0:
                fluo = 100.0  # Baseline
            else:
                copies *= (1 + efficiency)
                fluo = 100.0 + copies * 0.001  # Arbitrary scaling
                # Add noise
                fluo += random.gauss(0, fluo * 0.02)

            fluorescence.append((cycle, max(0, fluo)))

        # Calculate Ct
        ct = None
        for cycle, fluo in fluorescence:
            if fluo >= threshold_fluorescence:
                # Interpolate
                if cycle > 0:
                    prev_fluo = fluorescence[cycle - 1][1]
                    ct = cycle - 1 + (threshold_fluorescence - prev_fluo) / (fluo - prev_fluo)
                else:
                    ct = 0.0
                break

        if ct is None:
            ct = cycles + 1

        # Melt curve
        melt_curve = self.generate_melt_curve(copies)

        # R-squared (simplified)
        r2 = 0.99 - random.uniform(0, 0.02)

        return qPCRResult(
            ct_value=ct,
            amplification_curve=fluorescence,
            melt_curve=melt_curve,
            efficiency=efficiency,
            r_squared=r2,
            initial_copies=initial_copies
        )

    def calculate_ct(self, initial_copies: int, efficiency: float, threshold: float = 1000.0) -> float:
        """Calculate theoretical Ct value."""
        if initial_copies <= 0:
            return 40.0
        return math.log(threshold / 100.0 / initial_copies) / math.log(1 + efficiency)

    def generate_melt_curve(self, copies: int) -> dict[float, float]:
        """Generate melting curve data."""
        # Simulate melt curve for typical amplicon (Tm ~ 82°C)
        tm = 82.0 + random.uniform(-1, 1)
        curve = {}
        for temp in [i * 0.5 for i in range(120, 200)]:  # 60-100°C
            # Derivative of sigmoid
            diff = temp - tm
            deriv = math.exp(-diff * 2) / (1 + math.exp(-diff * 2))**2
            curve[temp] = deriv * 1000 + random.uniform(-5, 5)
        return curve

    # -----------------------------------------------------------------------
    # Genomic Data
    # -----------------------------------------------------------------------

    def load_genomic_data(self, chromosome: str = "chr21") -> dict:
        """Load genomic reference data."""
        if chromosome == "chr21":
            return {
                "sequence": self.genomic_database.get("chr21", "N" * 48000000),
                "genes": self.genomic_database.get("genes_chr21", {}),
                "length": 48000000
            }
        return {}

    def get_chromosome_sequence(self, chromosome: str = "chr21") -> str:
        """Get chromosome sequence."""
        return self.genomic_database.get(chromosome, "N" * 1000000)

    # -----------------------------------------------------------------------
    # Trisomy 21
    # -----------------------------------------------------------------------

    def simulate_trisomy_21(self) -> Trisomy21Result:
        """Simulate Trisomy 21 (Down syndrome) gene dosage effects."""
        chr21_genes = self.genomic_database.get("genes_chr21", {})

        # Gene dosage effect: 1.5x expression for chr21 genes
        dosage_effects = {}
        for gene, info in chr21_genes.items():
            # Expression increase proportional to copy number (3/2 = 1.5x)
            # But with compensation (typically 1.2-1.4x observed)
            dosage_effects[gene] = 1.3 + random.uniform(-0.1, 0.1)

        # Phenotype predictions based on gene overexpression
        phenotypes = {
            "intellectual_disability": 0.99,
            "characteristic_facial_features": 0.95,
            "congenital_heart_defect": 0.50,
            "hypotonia": 0.80,
            "alzheimer_pathology": 0.75,
            "leukemia_risk": 0.02,
            "thyroid_dysfunction": 0.15,
            "hearing_loss": 0.75,
            "vision_impairment": 0.60,
        }

        # Aneuploidy detection score
        aneuploidy = 0.95 + random.uniform(-0.05, 0.05)

        return Trisomy21Result(
            chromosome_21_genes=[{"symbol": k, **v} for k, v in chr21_genes.items()],
            gene_dosage_effects=dosage_effects,
            phenotype_predictions=phenotypes,
            aneuploidy_score=aneuploidy
        )

    def simulate_gene_dosage(self, gene_symbol: str, copy_number: int) -> dict:
        """Simulate gene dosage effect for a specific gene."""
        baseline = 2  # Normal diploid
        fold_change = copy_number / baseline

        # Non-linear compensation
        if fold_change > 1:
            # Overexpression with compensation
            effective_fc = 1 + (fold_change - 1) * 0.7
        else:
            # Underexpression
            effective_fc = fold_change

        return {
            "gene": gene_symbol,
            "copy_number": copy_number,
            "theoretical_fold_change": fold_change,
            "effective_fold_change": effective_fc,
            "compensation_factor": effective_fc / fold_change if fold_change != 1 else 1.0
        }


# Global instance
GENETICS_ENGINE = GeneticsEngine()

# Module-level function exports for backward compatibility with tests
def simulate_pcr_cycle(cycle: PCRCycle, initial_copies: int = 1) -> dict:
    """Simulate a single PCR cycle."""
    return GENETICS_ENGINE.simulate_pcr_cycle(cycle, initial_copies)

def simulate_pcr(protocol: PCRProtocol, initial_copies: int = 1) -> PCRResult:
    """Simulate complete PCR protocol."""
    return GENETICS_ENGINE.simulate_pcr(protocol, initial_copies)

def calculate_tm(sequence: str, na_conc_m: float = 0.05, mg_conc_m: float = 0.0015, dna_conc_nM: float = 250) -> float:
    """Calculate melting temperature using nearest-neighbor method."""
    return GENETICS_ENGINE.calculate_tm(sequence, na_conc_m, mg_conc_m, dna_conc_nM)

def calculate_gc_content(sequence: str) -> float:
    """Calculate GC content percentage."""
    return GENETICS_ENGINE.calculate_gc_content(sequence)

def check_hairpin(sequence: str, min_stem: int = 4, max_loop: int = 30) -> tuple[bool, float]:
    """Check for hairpin formation."""
    return GENETICS_ENGINE.check_hairpin(sequence, min_stem, max_loop)

def check_dimer(primer1: str, primer2: str) -> tuple[bool, float]:
    """Check for primer-dimer formation."""
    return GENETICS_ENGINE.check_dimer(primer1, primer2)

def check_specificity(primer: str, genome: str, max_mismatches: int = 3) -> float:
    """Check primer specificity against genome."""
    return GENETICS_ENGINE.check_specificity(primer, genome, max_mismatches)

def design_primers(template: str, target_start: int, target_end: int,
                   opt_tm: float = 60.0, min_tm: float = 55.0, max_tm: float = 65.0,
                   min_gc: float = 40.0, max_gc: float = 60.0,
                   min_len: int = 18, max_len: int = 27) -> tuple[Optional[Primer], Optional[Primer]]:
    """Design PCR primers for a target region."""
    return GENETICS_ENGINE.design_primers(template, target_start, target_end,
                                           opt_tm=opt_tm, min_tm=min_tm, max_tm=max_tm,
                                           min_gc=min_gc, max_gc=max_gc,
                                           min_len=min_len, max_len=max_len)

def simulate_gel_electrophoresis(fragments: list[dict],
                                 gel_percent: float = 1.0,
                                 voltage_v: float = 100,
                                 run_time_min: float = 45) -> GelElectrophoresisResult:
    """Simulate agarose gel electrophoresis."""
    return GENETICS_ENGINE.simulate_gel_electrophoresis(fragments, gel_percent, voltage_v, run_time_min)

def digest_dna(sequence: str, enzymes: list[str]) -> DigestionResult:
    """Simulate restriction enzyme digestion."""
    return GENETICS_ENGINE.digest_dna(sequence, enzymes)

def simulate_sanger_sequencing(template: str, primer: str,
                               read_length: int = 800,
                               error_rate: float = 0.005) -> SangerResult:
    """Simulate Sanger sequencing."""
    return GENETICS_ENGINE.simulate_sanger_sequencing(template, primer, read_length, error_rate)

def design_sgrna(target_sequence: str, genome: str = "") -> SgRNA:
    """Design sgRNA for CRISPR-Cas9."""
    return GENETICS_ENGINE.design_sgrna(target_sequence, genome)

def check_pam(target_sequence: str) -> bool:
    """Check for PAM sequence (NGG)."""
    return target_sequence[-2:] == "GG" if len(target_sequence) >= 2 else False

def predict_off_targets(sgRNA: SgRNA, genome: str) -> list[dict]:
    """Predict off-target effects."""
    return GENETICS_ENGINE.predict_off_targets(sgRNA, genome)

def simulate_indels(sgRNA: SgRNA, cell_type: str = "HEK293") -> CRISPRResult:
    """Simulate CRISPR indel outcomes."""
    return GENETICS_ENGINE.simulate_indels(sgRNA, cell_type)

def simulate_qpcr(initial_copies: int, efficiency: float = 0.9,
                  cycles: int = 40, threshold_fluorescence: float = 1000.0) -> qPCRResult:
    """Simulate qPCR amplification curve and Ct calculation."""
    return GENETICS_ENGINE.simulate_qpcr(initial_copies, efficiency, cycles, threshold_fluorescence)

def calculate_ct(initial_copies: int, efficiency: float, threshold: float = 1000.0) -> float:
    """Calculate theoretical Ct value."""
    return GENETICS_ENGINE.calculate_ct(initial_copies, efficiency, threshold)

def generate_melt_curve(copies: int) -> dict[float, float]:
    """Generate melting curve data."""
    return GENETICS_ENGINE.generate_melt_curve(copies)

def load_genomic_data(chromosome: str = "chr21") -> dict:
    """Load genomic reference data."""
    return GENETICS_ENGINE.load_genomic_data(chromosome)

def get_chromosome_sequence(chromosome: str = "chr21") -> str:
    """Get chromosome sequence."""
    return GENETICS_ENGINE.get_chromosome_sequence(chromosome)

def simulate_trisomy_21() -> Trisomy21Result:
    """Simulate Trisomy 21 (Down syndrome) gene dosage effects."""
    return GENETICS_ENGINE.simulate_trisomy_21()

def simulate_gene_dosage(gene_symbol: str, copy_number: int) -> dict:
    """Simulate gene dosage effect for a specific gene."""
    return GENETICS_ENGINE.simulate_gene_dosage(gene_symbol, copy_number)