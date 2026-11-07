"""
Genomic sequence utilities.

Provides functions for DNA/RNA sequence manipulation, translation,
GC content calculation, motif finding, and other sequence operations.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Literal


# DNA complement table
COMPLEMENT_TABLE = str.maketrans("ATGCatgcN", "TACGtacgN")
REV_COMPLEMENT_TABLE = str.maketrans("ATGCatgcN", "TACGtacgN")

# RNA complement (for RNA sequences)
RNA_COMPLEMENT_TABLE = str.maketrans("AUCGaucgN", "UAGCuagcN")

# Genetic code (standard)
GENETIC_CODE = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
}

# Reverse genetic code (amino acid -> codons)
REVERSE_GENETIC_CODE = {}
for codon, aa in GENETIC_CODE.items():
    REVERSE_GENETIC_CODE.setdefault(aa, []).append(codon)

# IUPAC ambiguity codes
IUPAC_CODES = {
    'A': 'A', 'C': 'C', 'G': 'G', 'T': 'T', 'U': 'U',
    'R': '[AG]', 'Y': '[CT]', 'S': '[GC]', 'W': '[AT]',
    'K': '[GT]', 'M': '[AC]', 'B': '[CGT]', 'D': '[AGT]',
    'H': '[ACT]', 'V': '[ACG]', 'N': '[ACGT]',
}

# Amino acid properties
AA_PROPERTIES = {
    'A': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'small'},
    'R': {'hydrophobic': False, 'polar': True, 'charge': 1, 'size': 'large'},
    'N': {'hydrophobic': False, 'polar': True, 'charge': 0, 'size': 'medium'},
    'D': {'hydrophobic': False, 'polar': True, 'charge': -1, 'size': 'medium'},
    'C': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'medium'},
    'Q': {'hydrophobic': False, 'polar': True, 'charge': 0, 'size': 'large'},
    'E': {'hydrophobic': False, 'polar': True, 'charge': -1, 'size': 'large'},
    'G': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'small'},
    'H': {'hydrophobic': False, 'polar': True, 'charge': 0.5, 'size': 'large'},
    'I': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'medium'},
    'L': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'medium'},
    'K': {'hydrophobic': False, 'polar': True, 'charge': 1, 'size': 'large'},
    'M': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'large'},
    'F': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'large'},
    'P': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'medium'},
    'S': {'hydrophobic': False, 'polar': True, 'charge': 0, 'size': 'small'},
    'T': {'hydrophobic': False, 'polar': True, 'charge': 0, 'size': 'small'},
    'W': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'large'},
    'Y': {'hydrophobic': True, 'polar': True, 'charge': 0, 'size': 'large'},
    'V': {'hydrophobic': True, 'polar': False, 'charge': 0, 'size': 'medium'},
    '*': {'hydrophobic': False, 'polar': False, 'charge': 0, 'size': 'stop'},
}


class GenomicSequence:
    """
    Utilities for genomic sequence manipulation.

    All methods are static and operate on string sequences.
    """

    # Valid DNA/RNA bases
    DNA_BASES = frozenset('ATGCN')
    RNA_BASES = frozenset('AUCGN')
    ALL_BASES = DNA_BASES | RNA_BASES

    @staticmethod
    def is_dna(seq: str) -> bool:
        """Check if sequence contains only DNA bases."""
        return all(b.upper() in GenomicSequence.DNA_BASES for b in seq)

    @staticmethod
    def is_rna(seq: str) -> bool:
        """Check if sequence contains only RNA bases."""
        return all(b.upper() in GenomicSequence.RNA_BASES for b in seq)

    @staticmethod
    def validate_sequence(seq: str, alphabet: Literal['dna', 'rna', 'any'] = 'dna') -> bool:
        """Validate sequence against alphabet."""
        if alphabet == 'dna':
            return GenomicSequence.is_dna(seq)
        elif alphabet == 'rna':
            return GenomicSequence.is_rna(seq)
        return GenomicSequence.is_dna(seq) or GenomicSequence.is_rna(seq)

    @staticmethod
    def clean_sequence(seq: str) -> str:
        """Remove whitespace and convert to uppercase."""
        return ''.join(seq.split()).upper()

    @staticmethod
    def complement(seq: str) -> str:
        """
        Return complement of DNA sequence.

        A <-> T, G <-> C, N -> N
        """
        return seq.translate(COMPLEMENT_TABLE)

    @staticmethod
    def reverse_complement(seq: str) -> str:
        """
        Return reverse complement of DNA sequence.

        This is the sequence on the opposite strand.
        """
        return GenomicSequence.complement(seq)[::-1]

    @staticmethod
    def reverse(seq: str) -> str:
        """Return reversed sequence."""
        return seq[::-1]

    @staticmethod
    def transcribe(seq: str) -> str:
        """Convert DNA to RNA (T -> U)."""
        return seq.replace('T', 'U').replace('t', 'u')

    @staticmethod
    def reverse_transcribe(seq: str) -> str:
        """Convert RNA to DNA (U -> T)."""
        return seq.replace('U', 'T').replace('u', 't')

    @staticmethod
    def translate(
        seq: str,
        frame: int = 0,
        stop_at_stop: bool = True,
        genetic_code: dict | None = None
    ) -> str:
        """
        Translate DNA/RNA sequence to protein.

        Args:
            seq: DNA or RNA sequence
            frame: Reading frame (0, 1, or 2)
            stop_at_stop: Stop translation at first stop codon
            genetic_code: Custom genetic code dict

        Returns:
            Amino acid sequence (single letter codes)
        """
        code = genetic_code or GENETIC_CODE
        seq = seq.upper().replace('U', 'T')
        protein = []

        for i in range(frame, len(seq) - 2, 3):
            codon = seq[i:i+3]
            if len(codon) < 3:
                break
            aa = code.get(codon, 'X')
            protein.append(aa)
            if stop_at_stop and aa == '*':
                break

        return ''.join(protein)

    @staticmethod
    def translate_all_frames(seq: str) -> dict[int, str]:
        """Translate sequence in all 6 reading frames."""
        results = {}
        # Forward frames
        for frame in range(3):
            results[frame] = GenomicSequence.translate(seq, frame)
        # Reverse frames
        rev_comp = GenomicSequence.reverse_complement(seq)
        for frame in range(3):
            results[-(frame + 1)] = GenomicSequence.translate(rev_comp, frame)
        return results

    @staticmethod
    def find_orfs(
        seq: str,
        min_length: int = 30,
        genetic_code: dict | None = None
    ) -> list[tuple[int, int, str, str]]:
        """
        Find all open reading frames in sequence.

        Returns:
            List of (start, end, frame, protein_seq) tuples
        """
        code = genetic_code or GENETIC_CODE
        seq = seq.upper().replace('U', 'T')
        orfs = []

        for frame in range(3):
            in_orf = False
            orf_start = 0

            for i in range(frame, len(seq) - 2, 3):
                codon = seq[i:i+3]
                aa = code.get(codon, 'X')

                if not in_orf and aa == 'M':  # Start codon
                    in_orf = True
                    orf_start = i
                elif in_orf and aa == '*':  # Stop codon
                    orf_end = i + 3
                    protein = GenomicSequence.translate(seq[orf_start:orf_end], 0, False, code)
                    if len(protein) >= min_length:
                        orfs.append((orf_start, orf_end, frame, protein))
                    in_orf = False

        # Also check reverse complement
        rev_comp = GenomicSequence.reverse_complement(seq)
        for frame in range(3):
            in_orf = False
            orf_start = 0

            for i in range(frame, len(rev_comp) - 2, 3):
                codon = rev_comp[i:i+3]
                aa = code.get(codon, 'X')

                if not in_orf and aa == 'M':
                    in_orf = True
                    orf_start = i
                elif in_orf and aa == '*':
                    orf_end = i + 3
                    protein = GenomicSequence.translate(rev_comp[orf_start:orf_end], 0, False, code)
                    if len(protein) >= min_length:
                        # Convert back to original coordinates
                        orig_start = len(seq) - orf_end
                        orig_end = len(seq) - orf_start
                        orfs.append((orig_start, orig_end, -(frame + 1), protein))
                    in_orf = False

        return sorted(orfs, key=lambda x: x[0])

    @staticmethod
    def gc_content(seq: str) -> float:
        """Calculate GC content as fraction (0-1)."""
        seq = seq.upper()
        if not seq:
            return 0.0
        gc = seq.count('G') + seq.count('C')
        return gc / len(seq)

    @staticmethod
    def gc_content_pct(seq: str) -> float:
        """Calculate GC content as percentage (0-100)."""
        return GenomicSequence.gc_content(seq) * 100

    @staticmethod
    def at_content(seq: str) -> float:
        """Calculate AT content as fraction."""
        seq = seq.upper()
        if not seq:
            return 0.0
        at = seq.count('A') + seq.count('T') + seq.count('U')
        return at / len(seq)

    @staticmethod
    def base_counts(seq: str) -> dict[str, int]:
        """Count each base in sequence."""
        seq = seq.upper()
        return {
            'A': seq.count('A'),
            'T': seq.count('T'),
            'G': seq.count('G'),
            'C': seq.count('C'),
            'N': seq.count('N'),
            'U': seq.count('U'),
        }

    @staticmethod
    def dinucleotide_counts(seq: str) -> dict[str, int]:
        """Count dinucleotide frequencies."""
        seq = seq.upper().replace('U', 'T')
        counts = {}
        for i in range(len(seq) - 1):
            dinuc = seq[i:i+2]
            if 'N' not in dinuc:
                counts[dinuc] = counts.get(dinuc, 0) + 1
        return counts

    @staticmethod
    def melting_temperature(
        seq: str,
        na_conc: float = 0.05,  # Na+ concentration (M)
        mg_conc: float = 0.0,   # Mg2+ concentration (M)
        dna_conc: float = 50e-9 # DNA concentration (M)
    ) -> float:
        """
        Calculate melting temperature using nearest-neighbor method.

        Simplified SantaLucia 1998 formula for oligonucleotides.
        """
        seq = seq.upper().replace('U', 'T')
        if len(seq) < 2:
            return 0.0

        # Nearest-neighbor thermodynamic parameters (kcal/mol)
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

        delta_h = 0.0  # kcal/mol
        delta_s = 0.0  # cal/(mol·K)

        for i in range(len(seq) - 1):
            dinuc = seq[i:i+2]
            h, s = nn_params.get(dinuc, (0, 0))
            delta_h += h
            delta_s += s

        # Initiation parameters
        if seq[0] in 'GC':
            delta_h += 0.1
            delta_s += -2.8
        else:
            delta_h += 2.3
            delta_s += 4.1

        # Symmetry correction
        if seq == GenomicSequence.reverse_complement(seq):
            delta_s += -1.4

        # Salt correction
        if na_conc > 0:
            delta_s += 0.368 * (len(seq) - 1) * (na_conc ** 0.5)

        # Mg2+ correction (approximate)
        if mg_conc > 0:
            delta_s += 0.368 * (len(seq) - 1) * (mg_conc ** 0.5) * 1.5

        # Calculate Tm
        R = 1.987  # cal/(mol·K)
        tm_k = (delta_h * 1000) / (delta_s + R * (dna_conc ** 0.5))
        tm_c = tm_k - 273.15

        return tm_c

    @staticmethod
    def molecular_weight(seq: str, is_dna: bool = True) -> float:
        """Calculate molecular weight of sequence (g/mol)."""
        seq = seq.upper().replace('U', 'T' if is_dna else 'U')

        # Base molecular weights (g/mol) - monophosphate
        if is_dna:
            weights = {'A': 331.2, 'T': 304.2, 'G': 347.2, 'C': 307.2, 'N': 322.5}
        else:
            weights = {'A': 347.2, 'U': 306.2, 'G': 363.2, 'C': 323.2, 'N': 335.0}

        weight = sum(weights.get(b, 322.5) for b in seq)
        # Subtract water for phosphodiester bonds
        weight -= 18.015 * (len(seq) - 1)
        return weight

    @staticmethod
    def find_motif(
        seq: str,
        motif: str,
        allow_mismatches: int = 0,
        overlap: bool = True
    ) -> list[int]:
        """
        Find all occurrences of a motif in sequence.

        Args:
            seq: Sequence to search
            motif: Motif to find (can contain IUPAC codes)
            allow_mismatches: Number of mismatches allowed
            overlap: Allow overlapping matches

        Returns:
            List of 0-indexed start positions
        """
        seq = seq.upper()
        motif = motif.upper()

        # Convert IUPAC to regex
        pattern = ''.join(IUPAC_CODES.get(b, b) for b in motif)
        regex = re.compile(f'(?={pattern})' if overlap else pattern)

        positions = [m.start() for m in regex.finditer(seq)]

        if allow_mismatches > 0:
            # Use fuzzy matching (simplified)
            positions = GenomicSequence._fuzzy_find(seq, motif, allow_mismatches, overlap)

        return positions

    @staticmethod
    def _fuzzy_find(
        seq: str,
        motif: str,
        max_mismatches: int,
        overlap: bool
    ) -> list[int]:
        """Find motif with mismatches."""
        positions = []
        motif_len = len(motif)
        step = 1 if overlap else motif_len

        for i in range(0, len(seq) - motif_len + 1, step):
            mismatches = sum(1 for a, b in zip(seq[i:i+motif_len], motif) if a != b)
            if mismatches <= max_mismatches:
                positions.append(i)

        return positions

    @staticmethod
    def find_restriction_sites(
        seq: str,
        enzymes: dict[str, str] | None = None
    ) -> dict[str, list[int]]:
        """
        Find restriction enzyme cut sites.

        Args:
            seq: DNA sequence
            enzymes: Dict of enzyme_name -> recognition_sequence

        Returns:
            Dict of enzyme_name -> list of cut positions
        """
        if enzymes is None:
            enzymes = COMMON_RESTRICTION_ENZYMES

        seq = seq.upper()
        results = {}

        for enzyme, site in enzymes.items():
            positions = GenomicSequence.find_motif(seq, site)
            if positions:
                results[enzyme] = positions

        return results

    @staticmethod
    def sliding_window_gc(
        seq: str,
        window: int = 100,
        step: int = 50
    ) -> list[tuple[int, float]]:
        """Calculate GC content in sliding windows."""
        seq = seq.upper()
        results = []

        for i in range(0, len(seq) - window + 1, step):
            window_seq = seq[i:i+window]
            gc = GenomicSequence.gc_content(window_seq)
            results.append((i, gc))

        return results

    @staticmethod
    def get_reverse_complement_primer(seq: str) -> str:
        """Get reverse complement primer sequence (5' -> 3')."""
        return GenomicSequence.reverse_complement(seq)


# Common restriction enzymes
COMMON_RESTRICTION_ENZYMES = {
    'EcoRI': 'GAATTC',
    'BamHI': 'GGATCC',
    'HindIII': 'AAGCTT',
    'NotI': 'GCGGCCGC',
    'XhoI': 'CTCGAG',
    'SalI': 'GTCGAC',
    'PstI': 'CTGCAG',
    'SmaI': 'CCCGGG',
    'KpnI': 'GGTACC',
    'SacI': 'GAGCTC',
    'XbaI': 'TCTAGA',
    'SpeI': 'ACTAGT',
    'NcoI': 'CCATGG',
    'NdeI': 'CATATG',
    'BglII': 'AGATCT',
    'MluI': 'ACGCGT',
    'ApaI': 'GGGCCC',
    'SphI': 'GCATGC',
    'AvrII': 'CCTAGG',
    'AgeI': 'ACCGGT',
}


def codon_usage_table(seq: str) -> dict[str, float]:
    """Calculate codon usage frequencies from coding sequence."""
    seq = seq.upper().replace('U', 'T')
    codons = [seq[i:i+3] for i in range(0, len(seq) - 2, 3)]
    total = len(codons)

    if total == 0:
        return {}

    counts = {}
    for codon in codons:
        if len(codon) == 3 and 'N' not in codon:
            counts[codon] = counts.get(codon, 0) + 1

    return {codon: count / total for codon, count in counts.items()}


def codon_adaptation_index(
    seq: str,
    reference_usage: dict[str, float]
) -> float:
    """
    Calculate Codon Adaptation Index (CAI).

    CAI measures how well codon usage matches a reference set.
    """
    seq = seq.upper().replace('U', 'T')
    codons = [seq[i:i+3] for i in range(0, len(seq) - 2, 3)]

    if not codons:
        return 0.0

    # Get max frequency for each amino acid
    max_freq = {}
    for codon, freq in reference_usage.items():
        aa = GENETIC_CODE.get(codon, '')
        if aa and aa != '*':
            max_freq[aa] = max(max_freq.get(aa, 0), freq)

    # Calculate CAI
    values = []
    for codon in codons:
        aa = GENETIC_CODE.get(codon, '')
        if aa and aa != '*' and aa in max_freq:
            freq = reference_usage.get(codon, 0)
            if freq > 0 and max_freq[aa] > 0:
                values.append(freq / max_freq[aa])

    if not values:
        return 0.0

    # Geometric mean
    import math
    return math.exp(sum(math.log(v) for v in values) / len(values))