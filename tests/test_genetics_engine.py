"""Tests for the Genetics/PCR Simulation Engine."""

import pytest
import math
from typing import List, Dict, Any

# Import the genetics engine
import sys
sys.path.insert(0, '/c/Users/Win11 Pro/Desktop/chemlab/src')

from chemlab.simulation.genetics_engine import (
    # PCR Thermal Cycling
    PCRStep,
    PCRCycle,
    PCRProtocol,
    simulate_pcr_cycle,
    simulate_pcr,
    # Primer Design
    Primer,
    calculate_tm,
    calculate_gc_content,
    check_hairpin,
    check_dimer,
    check_specificity,
    design_primers,
    # Gel Electrophoresis
    GelElectrophoresis,
    simulate_gel_electrophoresis,
    # Restriction Digestion
    RestrictionEnzyme,
    digest_dna,
    # Sanger Sequencing
    SangerSequencing,
    simulate_sanger_sequencing,
    # CRISPR-Cas9
    CRISPRCas9,
    SgRNA,
    design_sgrna,
    check_pam,
    predict_off_targets,
    simulate_indels,
    # qPCR
    qPCRSimulation,
    simulate_qpcr,
    calculate_ct,
    generate_melt_curve,
    # Genomic Data
    GenomicDatabase,
    load_genomic_data,
    get_chromosome_sequence,
    # Trisomy 21
    Trisomy21Simulation,
    simulate_trisomy_21,
    GeneDosageEffect,
    simulate_gene_dosage,
)


class TestPCRThermalCycling:
    """Test PCR thermal cycling simulation."""

    def test_pcr_step_creation(self):
        """Test PCR step creation with all parameters."""
        step = PCRStep(
            name="denaturation",
            temperature_c=98.0,
            hold_time_s=10.0,
            ramp_rate_c_per_s=4.0
        )
        assert step.name == "denaturation"
        assert step.temperature_c == 98.0
        assert step.hold_time_s == 10.0
        assert step.ramp_rate_c_per_s == 4.0

    def test_pcr_cycle_creation(self):
        """Test PCR cycle with denaturation, annealing, extension."""
        cycle = PCRCycle(
            denaturation=PCRStep("denaturation", 98.0, 10.0, 4.0),
            annealing=PCRStep("annealing", 60.0, 20.0, 2.0),
            extension=PCRStep("extension", 72.0, 30.0, 2.0),
        )
        assert cycle.denaturation.temperature_c == 98.0
        assert cycle.annealing.temperature_c == 60.0
        assert cycle.extension.temperature_c == 72.0

    def test_pcr_protocol_creation(self):
        """Test PCR protocol with multiple cycles."""
        cycle = PCRCycle(
            denaturation=PCRStep("denaturation", 95.0, 30.0, 4.0),
            annealing=PCRStep("annealing", 55.0, 30.0, 2.0),
            extension=PCRStep("extension", 72.0, 60.0, 2.0),
        )
        protocol = PCRProtocol(
            initial_denaturation=PCRStep("initial_denat", 98.0, 120.0, 4.0),
            cycles=[cycle] * 30,
            final_extension=PCRStep("final_ext", 72.0, 300.0, 1.0),
            final_hold=PCRStep("hold", 4.0, 3600.0, 0.5),
        )
        assert len(protocol.cycles) == 30
        assert protocol.initial_denaturation.temperature_c == 98.0

    def test_simulate_pcr_cycle(self):
        """Test single PCR cycle simulation returns temperature profile."""
        cycle = PCRCycle(
            denaturation=PCRStep("denaturation", 98.0, 10.0, 4.0),
            annealing=PCRStep("annealing", 60.0, 20.0, 2.0),
            extension=PCRStep("extension", 72.0, 30.0, 2.0),
        )
        profile = simulate_pcr_cycle(cycle)

        assert "time_points" in profile
        assert "temperatures" in profile
        assert len(profile["time_points"]) == len(profile["temperatures"])
        assert max(profile["temperatures"]) >= 97.0
        assert min(profile["temperatures"]) <= 61.0

    def test_simulate_pcr_full_protocol(self):
        """Test full PCR protocol simulation."""
        cycle = PCRCycle(
            denaturation=PCRStep("denaturation", 95.0, 30.0, 4.0),
            annealing=PCRStep("annealing", 55.0, 30.0, 2.0),
            extension=PCRStep("extension", 72.0, 60.0, 2.0),
        )
        protocol = PCRProtocol(
            initial_denaturation=PCRStep("initial_denat", 98.0, 120.0, 4.0),
            cycles=[cycle] * 3,
            final_extension=PCRStep("final_ext", 72.0, 300.0, 1.0),
            final_hold=PCRStep("hold", 4.0, 60.0, 0.5),
        )
        profile = simulate_pcr(protocol)

        assert "time_points" in profile
        assert "temperatures" in profile
        assert "cycle_phases" in profile
        assert profile["cycle_phases"].count("denaturation") == 3
        assert profile["cycle_phases"].count("annealing") == 3
        assert profile["cycle_phases"].count("extension") == 3


class TestPrimerDesign:
    """Test primer design and validation."""

    def test_calculate_gc_content(self):
        """Test GC content calculation."""
        assert calculate_gc_content("ATGC") == 0.5
        assert calculate_gc_content("GGGG") == 1.0
        assert calculate_gc_content("AAAA") == 0.0
        assert calculate_gc_content("ATGCATGC") == 0.5

    def test_calculate_tm_basic(self):
        """Test Tm calculation using nearest-neighbor method."""
        # Simple test case
        tm = calculate_tm("ATGCATGCATGCATGC")  # 16mer, 50% GC
        assert 45.0 <= tm <= 65.0  # Typical range for 16-mer

        # High GC primer
        tm_high_gc = calculate_tm("GCGCGCGCGCGCGCGC")
        assert tm_high_gc > calculate_tm("ATATATATATATATAT")

    def test_calculate_tm_with_salt_correction(self):
        """Test Tm with salt concentration correction."""
        tm_low_salt = calculate_tm("ATGCATGCATGCATGC", na_conc_m=0.01)
        tm_high_salt = calculate_tm("ATGCATGCATGCATGC", na_conc_m=0.1)
        assert tm_high_salt > tm_low_salt  # Higher salt = higher Tm

    def test_check_hairpin(self):
        """Test hairpin detection."""
        # Primer with strong hairpin potential (palindromic)
        hairpin_primer = "GCGCGCATATATGCGCGC"
        has_hairpin, delta_g = check_hairpin(hairpin_primer)

        # Primer without hairpin
        no_hairpin = "ATGCATGCATGCATGC"
        no_hairpin_result, _ = check_hairpin(no_hairpin)

        assert isinstance(has_hairpin, bool)
        assert isinstance(delta_g, float)

    def test_check_dimer(self):
        """Test primer dimer detection."""
        primer1 = "ATGCATGCATGCATGC"
        primer2 = "GCATGCATGCATGCAT"  # Complementary

        has_dimer, delta_g = check_dimer(primer1, primer2)
        assert isinstance(has_dimer, bool)
        assert isinstance(delta_g, float)

        # Non-complementary primers
        primer3 = "AAAAAAAAAAAAAAAA"
        primer4 = "TTTTTTTTTTTTTTTT"
        has_dimer2, _ = check_dimer(primer3, primer4)
        assert has_dimer2  # These are complementary

    def test_design_primers(self):
        """Test primer design for a target sequence."""
        target = "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC"  # 48bp
        primers = design_primers(
            target_sequence=target,
            target_length=20,
            min_tm=55.0,
            max_tm=65.0,
            min_gc=0.4,
            max_gc=0.6,
        )

        assert "forward" in primers
        assert "reverse" in primers
        assert len(primers["forward"].sequence) >= 18
        assert len(primers["reverse"].sequence) >= 18
        assert 55.0 <= primers["forward"].tm <= 65.0
        assert 55.0 <= primers["reverse"].tm <= 65.0

    def test_check_specificity(self):
        """Test primer specificity against genome."""
        primer = Primer("test", "ATGCATGCATGCATGC", 60.0, 0.5)
        # Should not match random sequence
        genome = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        matches = check_specificity(primer, genome)
        assert len(matches) == 0


class TestGelElectrophoresis:
    """Test gel electrophoresis simulation."""

    def test_gel_creation(self):
        """Test gel electrophoresis setup."""
        gel = GelElectrophoresis(
            agarose_percent=1.0,
            voltage_v=100,
            length_cm=10,
            ladder_sizes_bp=[100, 500, 1000, 2000, 5000, 10000]
        )
        assert gel.agarose_percent == 1.0
        assert gel.voltage_v == 100

    def test_migration_distance(self):
        """Test DNA fragment migration distance calculation."""
        gel = GelElectrophoresis(agarose_percent=1.0, voltage_v=100, length_cm=10)

        # Smaller fragments migrate further
        dist_100bp = gel.migration_distance(100)
        dist_1000bp = gel.migration_distance(1000)
        dist_10000bp = gel.migration_distance(10000)

        assert dist_100bp > dist_1000bp > dist_10000bp
        assert 0 < dist_10000bp < gel.length_cm

    def test_band_intensity(self):
        """Test band intensity vs DNA quantity."""
        gel = GelElectrophoresis(agarose_percent=1.0, voltage_v=100, length_cm=10)

        intensity_1ng = gel.band_intensity(500, 1.0)  # 1ng of 500bp
        intensity_10ng = gel.band_intensity(500, 10.0)  # 10ng of 500bp

        assert intensity_10ng > intensity_1ng
        assert intensity_1ng > 0

    def test_ladder_calibration(self):
        """Test ladder calibration curve."""
        gel = GelElectrophoresis(
            agarose_percent=1.0,
            voltage_v=100,
            length_cm=10,
            ladder_sizes_bp=[100, 500, 1000, 2000, 5000, 10000]
        )
        ladder_bands = gel.get_ladder_bands()

        assert len(ladder_bands) == 6
        for band in ladder_bands:
            assert "size_bp" in band
            assert "distance_cm" in band
            assert "intensity" in band

    def test_simulate_gel_electrophoresis(self):
        """Test full gel electrophoresis simulation."""
        gel = GelElectrophoresis(agarose_percent=1.0, voltage_v=100, length_cm=10)
        fragments = [
            {"size_bp": 500, "quantity_ng": 10, "label": "PCR product"},
            {"size_bp": 1000, "quantity_ng": 5, "label": "Vector"},
            {"size_bp": 3000, "quantity_ng": 20, "label": "Insert"},
        ]
        result = simulate_gel_electrophoresis(gel, fragments)

        assert "bands" in result
        assert "ladder" in result
        assert len(result["bands"]) == 3
        for band in result["bands"]:
            assert "size_bp" in band
            assert "distance_cm" in band
            assert "intensity" in band
            assert "label" in band


class TestRestrictionDigestion:
    """Test restriction enzyme digestion."""

    def test_restriction_enzyme_creation(self):
        """Test restriction enzyme definition."""
        ecoRI = RestrictionEnzyme(
            name="EcoRI",
            recognition_site="GAATTC",
            cut_offset=1,  # Cuts between G and A
            is_palindromic=True,
            overhang="sticky_5prime",
        )
        assert ecoRI.name == "EcoRI"
        assert ecoRI.recognition_site == "GAATTC"

    def test_digest_dna_simple(self):
        """Test simple DNA digestion."""
        sequence = "AAAGAATTCCTTTGAATTCGGG"
        ecoRI = RestrictionEnzyme("EcoRI", "GAATTC", 1, True, "sticky_5prime")

        fragments = digest_dna(sequence, [ecoRI])

        # Should find 2 sites, produce 3 fragments
        assert len(fragments) == 3
        # Check fragments
        assert "AAAG" in fragments[0]
        assert "CTTTG" in fragments[1]
        assert "GGG" in fragments[2]

    def test_digest_dna_multiple_enzymes(self):
        """Test digestion with multiple enzymes."""
        sequence = "AAAGAATTCCTTTGGATCCGGG"
        ecoRI = RestrictionEnzyme("EcoRI", "GAATTC", 1, True, "sticky_5prime")
        bamHI = RestrictionEnzyme("BamHI", "GGATCC", 1, True, "sticky_5prime")

        fragments = digest_dna(sequence, [ecoRI, bamHI])

        # Should find 2 sites (one each), produce 3 fragments
        assert len(fragments) == 3

    def test_digest_no_site(self):
        """Test digestion when no recognition site exists."""
        sequence = "AAAAAAAAAATTTTTTTTTT"
        ecoRI = RestrictionEnzyme("EcoRI", "GAATTC", 1, True, "sticky_5prime")

        fragments = digest_dna(sequence, [ecoRI])
        assert len(fragments) == 1
        assert fragments[0] == sequence


class TestSangerSequencing:
    """Test Sanger sequencing simulation."""

    def test_sanger_sequencing_creation(self):
        """Test Sanger sequencing setup."""
        sanger = SangerSequencing(
            read_length=800,
            error_rate=0.01,
            quality_decay_start=500,
        )
        assert sanger.read_length == 800
        assert sanger.error_rate == 0.01

    def test_simulate_sanger_sequencing(self):
        """Test Sanger sequencing chromatogram generation."""
        template = "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC"
        sanger = SangerSequencing(read_length=100, error_rate=0.0)

        result = simulate_sanger_sequencing(template, sanger)

        assert "sequence" in result
        assert "quality_scores" in result
        assert "chromatogram" in result
        assert len(result["sequence"]) <= 100
        assert len(result["quality_scores"]) == len(result["sequence"])
        assert all(0 <= q <= 60 for q in result["quality_scores"])

        # Chromatogram should have 4 channels (A, C, G, T)
        assert "A" in result["chromatogram"]
        assert "C" in result["chromatogram"]
        assert "G" in result["chromatogram"]
        assert "T" in result["chromatogram"]

    def test_quality_scores_decay(self):
        """Test quality score decay with read length."""
        template = "A" * 1000
        sanger = SangerSequencing(read_length=800, error_rate=0.001, quality_decay_start=400)

        result = simulate_sanger_sequencing(template, sanger)

        # Early quality should be higher than late quality
        early_q = result["quality_scores"][:50]
        late_q = result["quality_scores"][-50:]
        assert sum(early_q) / len(early_q) > sum(late_q) / len(late_q)


class TestCRISPRCas9:
    """Test CRISPR-Cas9 editing simulation."""

    def test_sgrna_creation(self):
        """Test sgRNA design."""
        sgrna = SgRNA(
            sequence="GUUUUAGAGCUAGAAAUAGCAAGUUAAAAUAAGGCUAGUCCGUUAUCAACUUGAAAAAGUGGCACCGAGUCGGUGCUUUU",
            target_sequence="ATGCATGCATGCATGCATGC",
            pam="NGG",
            target_start=100,
            target_end=120,
        )
        assert len(sgrna.target_sequence) == 20
        assert sgrna.pam == "NGG"

    def test_check_pam(self):
        """Test PAM recognition."""
        # SpCas9 PAM = NGG
        assert check_pam("ATGCATGCATGCATGCATGCGG", "NGG") == True
        assert check_pam("ATGCATGCATGCATGCATGCAG", "NGG") == False
        assert check_pam("ATGCATGCATGCATGCATGCCG", "NGG") == True
        assert check_pam("ATGCATGCATGCATGCATGCTG", "NGG") == False

    def test_design_sgrna(self):
        """Test sgRNA design for a target gene."""
        target_gene = "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC"
        sgrnas = design_sgrna(target_gene, pam="NGG", max_results=5)

        assert len(sgrnas) <= 5
        for sgrna in sgrnas:
            assert len(sgrna.target_sequence) == 20
            assert sgrna.target_sequence in target_gene or sgrna.target_sequence[::-1].translate(str.maketrans("ATGC", "TACG")) in target_gene

    def test_predict_off_targets(self):
        """Test off-target prediction."""
        sgrna = SgRNA(
            sequence="GUUUUAGAGCUAGAAAUAGCAAGUUAAAAUAAGGCUAGUCCGUUAUCAACUUGAAAAAGUGGCACCGAGUCGGUGCUUUU",
            target_sequence="ATGCATGCATGCATGCATGC",
            pam="NGG",
            target_start=100,
            target_end=120,
        )
        genome = "ATGCATGCATGCATGCATGC" + "A" * 100 + "ATGCATGCATGCATGCATGG"  # One off-target with 1 mismatch
        off_targets = predict_off_targets(sgrna, genome, max_mismatches=3)

        assert isinstance(off_targets, list)
        for ot in off_targets:
            assert "position" in ot
            assert "mismatches" in ot
            assert "sequence" in ot

    def test_simulate_indels(self):
        """Test indel simulation after CRISPR cut."""
        target = "ATGCATGCATGCATGCATGC"
        cut_position = 10  # 0-indexed

        indels = simulate_indels(target, cut_position, n_simulations=100)

        assert len(indels) == 100
        for indel in indels:
            assert "sequence" in indel
            assert "type" in indel  # "insertion", "deletion", "substitution"
            assert "length_change" in indel


class TestQPCR:
    """Test qPCR simulation."""

    def test_qpcr_simulation_creation(self):
        """Test qPCR simulation setup."""
        qpcr = qPCRSimulation(
            efficiency=0.95,
            initial_copies=1000,
            baseline_cycles=10,
            max_cycles=40,
        )
        assert qpcr.efficiency == 0.95
        assert qpcr.initial_copies == 1000

    def test_simulate_qpcr(self):
        """Test qPCR amplification curve generation."""
        qpcr = qPCRSimulation(
            efficiency=0.95,
            initial_copies=1000,
            baseline_cycles=10,
            max_cycles=40,
        )

        result = simulate_qpcr(qpcr)

        assert "cycles" in result
        assert "fluorescence" in result
        assert "ct_value" in result
        assert len(result["cycles"]) == 40
        assert len(result["fluorescence"]) == 40
        assert result["ct_value"] > 0
        assert result["ct_value"] < 40

    def test_calculate_ct(self):
        """Test Ct value calculation."""
        # Exponential amplification: N = N0 * (1+E)^cycle
        # Ct is cycle where fluorescence crosses threshold
        cycles = list(range(40))
        fluorescence = [100 * (1.95)**c for c in cycles]  # E=0.95
        threshold = 10000

        ct = calculate_ct(cycles, fluorescence, threshold)
        assert ct > 0
        assert ct < 40

    def test_generate_melt_curve(self):
        """Test melt curve generation."""
        amplicon = "ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC"

        melt_curve = generate_melt_curve(amplicon)

        assert "temperatures" in melt_curve
        assert "derivative" in melt_curve
        assert len(melt_curve["temperatures"]) == len(melt_curve["derivative"])
        # Should have a peak at Tm
        max_deriv_idx = melt_curve["derivative"].index(max(melt_curve["derivative"]))
        tm = melt_curve["temperatures"][max_deriv_idx]
        assert 70.0 <= tm <= 95.0


class TestGenomicData:
    """Test genomic data integration."""

    def test_load_genomic_data(self):
        """Test loading genomic databases."""
        # Should work with built-in mock data
        db = load_genomic_data("human", "GRCh38")
        assert isinstance(db, GenomicDatabase)
        assert db.species == "human"
        assert db.assembly == "GRCh38"
        assert len(db.chromosomes) > 0

    def test_get_chromosome_sequence(self):
        """Test retrieving chromosome sequences."""
        db = load_genomic_data("human", "GRCh38")

        # Get a small region
        seq = get_chromosome_sequence(db, "chr21", 0, 1000)
        assert isinstance(seq, str)
        assert len(seq) == 1000
        assert all(c in "ATGCN" for c in seq)

    def test_mouse_genome(self):
        """Test mouse GRCm39 genome."""
        db = load_genomic_data("mouse", "GRCm39")
        assert db.species == "mouse"
        assert db.assembly == "GRCm39"
        assert "chr1" in db.chromosomes

    def test_drosophila_genome(self):
        """Test Drosophila genome."""
        db = load_genomic_data("drosophila", "dm6")
        assert db.species == "drosophila"

    def test_c_elegans_genome(self):
        """Test C. elegans genome."""
        db = load_genomic_data("c_elegans", "ce11")
        assert db.species == "c_elegans"


class TestTrisomy21:
    """Test Trisomy 21 simulation."""

    def test_trisomy21_simulation_creation(self):
        """Test Trisomy 21 simulation setup."""
        sim = Trisomy21Simulation(
            chromosome_21_genes=["APP", "SOD1", "DYRK1A", "RCAN1", "ETS2"],
            dosage_factor=1.5,  # 3 copies vs 2 = 1.5x
        )
        assert sim.dosage_factor == 1.5
        assert len(sim.chromosome_21_genes) == 5

    def test_simulate_gene_dosage(self):
        """Test gene dosage effect simulation."""
        normal_expression = {"APP": 100, "SOD1": 50, "DYRK1A": 75, "RCAN1": 60, "ETS2": 80}
        effects = simulate_gene_dosage(normal_expression, dosage_factor=1.5)

        assert len(effects) == 5
        for gene, effect in effects.items():
            assert "expression_level" in effect
            assert "fold_change" in effect
            assert "phenotypic_impact" in effect
            # Expression should increase with dosage
            assert effect["fold_change"] >= 1.0

    def test_simulate_trisomy_21(self):
        """Test full Trisomy 21 phenotypic simulation."""
        sim = Trisomy21Simulation(
            chromosome_21_genes=["APP", "SOD1", "DYRK1A", "RCAN1", "ETS2"],
            dosage_factor=1.5,
        )

        phenotype = simulate_trisomy_21(sim)

        assert "gene_effects" in phenotype
        assert "phenotypic_traits" in phenotype
        assert "cognitive_impact" in phenotype
        assert "physical_traits" in phenotype

        # Check specific known traits
        traits = phenotype["phenotypic_traits"]
        assert "intellectual_disability" in traits
        assert "facial_features" in traits
        assert "heart_defects" in traits
        assert "immune_dysfunction" in traits


if __name__ == "__main__":
    pytest.main([__file__, "-v"])