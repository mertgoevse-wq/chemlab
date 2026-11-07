"""
Tests for the ChemLab Analytical Instruments Simulation Engine.

Verifies all 6 core analytical instruments generate realistic data structures
for Godot UI rendering with proper physical models.
"""

import json
import pytest
import math
from pathlib import Path

from chemlab.simulation.analytical_engine import (
    AnalyticalEngine,
    NMRResult,
    GCMSResult,
    HPLCResult,
    MeltingPointResult,
    BalanceResult,
    PHMeterResult,
    TitrationResult,
    NMRPeak,
    GCMSPeak,
    HPLCPeak,
    InstrumentConfig,
)


# Test data for common compounds
ASPIRIN_SMILES = "CC(=O)Oc1ccccc1C(=O)O"
PARACETAMOL_SMILES = "CC(=O)Nc1ccc(O)cc1"
BENZALDEHYDE_SMILES = "c1ccc(cc1)C=O"
ETHANOL_SMILES = "CCO"


class TestAnalyticalEngineInit:
    """Test analytical engine initialization and configuration loading."""

    def test_engine_initialization(self):
        """Engine should initialize with default configuration."""
        engine = AnalyticalEngine()
        assert engine is not None
        assert hasattr(engine, "config")

    def test_engine_loads_tuning_config(self):
        """Engine should load tuning constants from JSON config."""
        engine = AnalyticalEngine()
        config = engine.config
        assert "nmr" in config
        assert "gc_ms" in config
        assert "titrator" in config
        assert "analytical_balance" in config
        assert "ph_meter" in config
        assert "melting_point" in config

    def test_nmr_config_values(self):
        """NMR config should have correct default values."""
        engine = AnalyticalEngine()
        nmr_config = engine.config["nmr"]
        assert nmr_config["spectrometer_frequency_mhz"] == 400.13
        assert nmr_config["default_scans_1h"] == 16
        assert nmr_config["default_scans_13c"] == 512
        assert "cdcl3" in nmr_config["residual_solvent_shifts_1h"]


class TestNMRSpectrometer:
    """Test NMR spectrometer simulation (1H/13C, 400MHz)."""

    def test_1h_nmr_basic_output(self):
        """1H NMR should produce spectrum with peaks, integrals, multiplicities."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ASPIRIN_SMILES, solvent="cdcl3")

        assert isinstance(result, NMRResult)
        assert result.nucleus == "1H"
        assert result.frequency_mhz == 400.13
        assert len(result.peaks) > 0
        assert result.solvent == "cdcl3"

    def test_1h_nmr_aspirin_peaks(self):
        """Aspirin 1H NMR should match known literature values."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ASPIRIN_SMILES, solvent="cdcl3")

        # Aspirin expected peaks (literature in CDCl3):
        # 2.35 ppm (s, 3H, COCH3), 7.14 (d), 7.35 (t), 7.62 (t), 8.13 (dd), 11.2 (br s, COOH)
        peak_shifts = [p.chemical_shift_ppm for p in result.peaks]

        # Acetyl methyl singlet ~2.35 ppm
        acetyl_peak = next((p for p in result.peaks if abs(p.chemical_shift_ppm - 2.35) < 0.15), None)
        assert acetyl_peak is not None
        assert acetyl_peak.multiplicity in ("s", "singlet")
        assert acetyl_peak.integral_h == 3

        # Aromatic region 7-8.5 ppm
        aromatic_peaks = [p for p in result.peaks if 7.0 <= p.chemical_shift_ppm <= 8.5]
        assert len(aromatic_peaks) >= 4

        # COOH broad singlet ~11 ppm
        cooh_peak = next((p for p in result.peaks if abs(p.chemical_shift_ppm - 11.2) < 0.5), None)
        assert cooh_peak is not None
        assert cooh_peak.multiplicity in ("br s", "broad singlet", "s")

    def test_1h_nmr_solvent_peaks_included(self):
        """Residual solvent peaks should appear in spectrum."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ASPIRIN_SMILES, solvent="cdcl3")

        # CDCl3 residual peak at 7.26 ppm
        solvent_peak = next((p for p in result.peaks if abs(p.chemical_shift_ppm - 7.26) < 0.05), None)
        assert solvent_peak is not None
        assert "solvent" in solvent_peak.notes.lower() or solvent_peak.is_solvent_peak

    def test_1h_nmr_different_solvents(self):
        """NMR should handle different deuterated solvents."""
        engine = AnalyticalEngine()

        for solvent in ["cdcl3", "dmso_d6", "d2o", "cd3od"]:
            result = engine.run_nmr_1h(ASPIRIN_SMILES, solvent=solvent)
            assert result.solvent == solvent
            # Solvent residual peak should match config
            expected_shift = engine.config["nmr"]["residual_solvent_shifts_1h"][solvent]
            solvent_peak = next((p for p in result.peaks if abs(p.chemical_shift_ppm - expected_shift) < 0.05), None)
            assert solvent_peak is not None

    def test_13c_nmr_basic_output(self):
        """13C NMR should produce spectrum with carbon peaks."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_13c(ASPIRIN_SMILES, solvent="cdcl3")

        assert isinstance(result, NMRResult)
        assert result.nucleus == "13C"
        assert result.frequency_mhz == 100.62  # 400.13 / 4
        assert len(result.peaks) > 0
        assert result.solvent == "cdcl3"

    def test_13c_nmr_aspirin_peaks(self):
        """Aspirin 13C NMR should have 9 distinct carbons."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_13c(ASPIRIN_SMILES, solvent="cdcl3")

        # Aspirin has 9 unique carbons (C9H8O4)
        # Carbonyls ~170 ppm, aromatic 120-140 ppm, methyl ~20 ppm
        carbonyl_peaks = [p for p in result.peaks if 165 <= p.chemical_shift_ppm <= 175]
        assert len(carbonyl_peaks) >= 2  # Two carbonyls (ester + acid)

        methyl_peaks = [p for p in result.peaks if 18 <= p.chemical_shift_ppm <= 25]
        assert len(methyl_peaks) >= 1

    def test_j_coupling_simulation(self):
        """Peaks should include J-coupling constants for multiplets."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ASPIRIN_SMILES, solvent="cdcl3")

        # Aromatic protons should show coupling
        aromatic_peaks = [p for p in result.peaks if 7.0 <= p.chemical_shift_ppm <= 8.5]
        coupled_peaks = [p for p in aromatic_peaks if p.j_coupling_hz and len(p.j_coupling_hz) > 0]
        assert len(coupled_peaks) > 0

        # Coupling constants should be realistic (ortho ~8 Hz, meta ~2 Hz, para ~0-1 Hz)
        for p in coupled_peaks:
            for j in p.j_coupling_hz:
                assert 0 < j <= 20  # Realistic range

    def test_peak_picking_and_integration(self):
        """Engine should perform peak picking with integration values."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ETHANOL_SMILES, solvent="cdcl3")

        # Ethanol: CH3 (t, ~1.2 ppm, 3H), CH2 (q, ~3.7 ppm, 2H), OH (br s, ~2-5 ppm, 1H)
        peaks = result.peaks
        total_integral = sum(p.integral_h for p in peaks if not p.is_solvent_peak)
        assert total_integral >= 6  # C2H6O = 6 protons

    def test_multiplet_analysis(self):
        """Multiplet analysis should identify splitting patterns correctly."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ETHANOL_SMILES, solvent="cdcl3")

        # CH3 should be triplet (n+1 = 3, J ~7 Hz)
        ch3_peak = next((p for p in result.peaks if abs(p.chemical_shift_ppm - 1.2) < 0.3), None)
        assert ch3_peak is not None
        assert ch3_peak.multiplicity in ("t", "triplet")

        # CH2 should be quartet (n+1 = 4, J ~7 Hz)
        ch2_peak = next((p for p in result.peaks if abs(p.chemical_shift_ppm - 3.7) < 0.3), None)
        assert ch2_peak is not None
        assert ch2_peak.multiplicity in ("q", "quartet")

    def test_shimming_simulation(self):
        """Shimming quality should affect peak linewidth."""
        engine = AnalyticalEngine()

        # Good shimming
        result_good = engine.run_nmr_1h(ASPIRIN_SMILES, solvent="cdcl3", shimming_quality=0.95)
        # Poor shimming
        result_poor = engine.run_nmr_1h(ASPIRIN_SMILES, solvent="cdcl3", shimming_quality=0.5)

        # Poor shimming should broaden peaks (higher linewidth)
        avg_linewidth_good = sum(p.linewidth_hz for p in result_good.peaks) / len(result_good.peaks)
        avg_linewidth_poor = sum(p.linewidth_hz for p in result_poor.peaks) / len(result_poor.peaks)
        assert avg_linewidth_poor > avg_linewidth_good

    def test_nmr_output_for_godot(self):
        """NMR result should be serializable for Godot UI."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ASPIRIN_SMILES, solvent="cdcl3")

        # Should have to_dict method for Godot
        data = result.to_dict()
        assert "nucleus" in data
        assert "frequency_mhz" in data
        assert "peaks" in data
        assert "solvent" in data
        assert "fid_data" in data  # Raw FID for processing simulation

        # Peaks should have all needed fields
        for peak_data in data["peaks"]:
            assert "chemical_shift_ppm" in peak_data
            assert "intensity" in peak_data
            assert "integral_h" in peak_data
            assert "multiplicity" in peak_data
            assert "j_coupling_hz" in peak_data
            assert "linewidth_hz" in peak_data


class TestGCMS:
    """Test GC-MS simulation (EI 70eV, retention time, NIST matching)."""

    def test_gcms_basic_output(self):
        """GC-MS should produce TIC chromatogram and mass spectra."""
        engine = AnalyticalEngine()
        result = engine.run_gcms(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        assert isinstance(result, GCMSResult)
        assert result.ionization_energy_ev == 70.0
        assert len(result.chromatogram) > 0  # TIC: list of (time, intensity)
        assert len(result.mass_spectra) > 0  # Mass spectrum per peak

    def test_gcms_retention_time_prediction(self):
        """Retention time should correlate with boiling point and polarity."""
        engine = AnalyticalEngine()

        # Ethanol (low BP, polar) vs Benzaldehyde (higher BP, less polar)
        ethanol_result = engine.run_gcms(ETHANOL_SMILES, concentration_mg_ml=1.0)
        benzaldehyde_result = engine.run_gcms(BENZALDEHYDE_SMILES, concentration_mg_ml=1.0)

        # Get main peak retention times
        ethanol_rt = max(ethanol_result.chromatogram, key=lambda x: x[1])[0]
        benzaldehyde_rt = max(benzaldehyde_result.chromatogram, key=lambda x: x[1])[0]

        # Benzaldehyde should elute later (higher boiling point)
        assert benzaldehyde_rt > ethanol_rt

    def test_gcms_ei_fragmentation_patterns(self):
        """EI 70eV fragmentation should produce characteristic ions."""
        engine = AnalyticalEngine()
        result = engine.run_gcms(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        # Aspirin EI fragments: m/z 180 (M+.), 138 (M-CH2CO), 120 (M-COCH3), 92, 64, 43 (CH3CO+)
        main_spectrum = max(result.mass_spectra, key=lambda s: s.total_ion_current)
        mz_values = [peak.mz for peak in main_spectrum.peaks]
        intensities = [peak.relative_abundance for peak in main_spectrum.peaks]

        # Molecular ion
        assert any(abs(mz - 180) < 1 for mz in mz_values)
        # Acetyl fragment m/z 43
        assert any(abs(mz - 43) < 1 for mz in mz_values)
        # M - CH2CO (138)
        assert any(abs(mz - 138) < 1 for mz in mz_values)

    def test_gcms_nist_library_matching(self):
        """NIST library matching should return similarity scores."""
        engine = AnalyticalEngine()
        result = engine.run_gcms(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        assert result.library_matches is not None
        assert len(result.library_matches) > 0

        # Top match should be aspirin with high similarity
        top_match = result.library_matches[0]
        assert "aspirin" in top_match.compound_name.lower() or "acetylsalicylic" in top_match.compound_name.lower()
        assert top_match.match_factor >= 800  # Good match threshold from config

    def test_gcms_purity_calculation(self):
        """Peak area percentage purity should be calculated."""
        engine = AnalyticalEngine()
        result = engine.run_gcms(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        assert result.purity_percent is not None
        assert 0 <= result.purity_percent <= 100

    def test_gcms_concentration_effects(self):
        """High concentration should show detector saturation warning."""
        engine = AnalyticalEngine()

        # Low concentration
        result_low = engine.run_gcms(ASPIRIN_SMILES, concentration_mg_ml=0.1)
        # High concentration (above config threshold of 2.0 mg/mL)
        result_high = engine.run_gcms(ASPIRIN_SMILES, concentration_mg_ml=5.0)

        assert result_high.detector_saturated or result_high.warnings
        assert not result_low.detector_saturated

    def test_gcms_output_for_godot(self):
        """GC-MS result should be serializable for Godot UI."""
        engine = AnalyticalEngine()
        result = engine.run_gcms(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        data = result.to_dict()
        assert "chromatogram" in data  # List of [time, intensity] pairs
        assert "mass_spectra" in data  # Per-peak mass spectra
        assert "library_matches" in data
        assert "purity_percent" in data
        assert "retention_times" in data
        assert "ionization_energy_ev" in data


class TestHPLC:
    """Test HPLC-DAD simulation (gradient elution, UV-Vis, peak purity)."""

    def test_hplc_basic_output(self):
        """HPLC-DAD should produce chromatograms at multiple wavelengths."""
        engine = AnalyticalEngine()
        result = engine.run_hplc_dad(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        assert isinstance(result, HPLCResult)
        assert len(result.chromatograms) > 0  # Dict of wavelength -> (time, intensity)
        assert len(result.peak_purities) > 0

    def test_hplc_gradient_elution(self):
        """Gradient elution should be simulated with time-varying solvent composition."""
        engine = AnalyticalEngine()
        result = engine.run_hplc_dad(
            ASPIRIN_SMILES,
            concentration_mg_ml=1.0,
            gradient=[(0, 5, 95), (10, 95, 5)]  # (time, %B_start, %B_end)
        )

        assert result.gradient_profile is not None
        assert len(result.gradient_profile) > 0

    def test_hplc_uv_vis_spectra(self):
        """Each peak should have UV-Vis spectrum (diode array)."""
        engine = AnalyticalEngine()
        result = engine.run_hplc_dad(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        # Aspirin has UV max ~230 nm, ~270 nm
        for peak in result.peaks:
            assert peak.uv_spectrum is not None
            assert len(peak.uv_spectrum) > 0  # List of (wavelength, absorbance)

    def test_hplc_peak_purity(self):
        """Peak purity should be assessed from spectral homogeneity."""
        engine = AnalyticalEngine()
        result = engine.run_hplc_dad(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        for peak in result.peaks:
            assert peak.purity_score is not None
            assert 0 <= peak.purity_score <= 1.0

    def test_hplc_output_for_godot(self):
        """HPLC result should be serializable for Godot UI."""
        engine = AnalyticalEngine()
        result = engine.run_hplc_dad(ASPIRIN_SMILES, concentration_mg_ml=1.0)

        data = result.to_dict()
        assert "chromatograms" in data
        assert "peaks" in data
        assert "gradient_profile" in data
        assert "peak_purities" in data


class TestMeltingPoint:
    """Test Melting Point Apparatus simulation."""

    def test_melting_point_basic_output(self):
        """Melting point should return onset, clear, and range."""
        engine = AnalyticalEngine()
        result = engine.run_melting_point(ASPIRIN_SMILES, ramp_rate_c_min=1.0)

        assert isinstance(result, MeltingPointResult)
        assert result.onset_c is not None
        assert result.clear_c is not None
        assert result.range_c is not None
        assert result.clear_c >= result.onset_c

    def test_melting_point_aspirin(self):
        """Aspirin MP should be ~135-136°C."""
        engine = AnalyticalEngine()
        result = engine.run_melting_point(ASPIRIN_SMILES, ramp_rate_c_min=1.0)

        # Literature MP: 135-136°C
        assert 133 <= result.onset_c <= 138
        assert 135 <= result.clear_c <= 138
        assert result.range_c <= 3.0  # Pure substance

    def test_melting_point_paracetamol(self):
        """Paracetamol MP should be ~169-171°C."""
        engine = AnalyticalEngine()
        result = engine.run_melting_point(PARACETAMOL_SMILES, ramp_rate_c_min=1.0)

        # Literature MP: 169-171°C
        assert 168 <= result.onset_c <= 172
        assert 170 <= result.clear_c <= 173
        assert result.range_c <= 3.0

    def test_melting_point_fast_ramp_thermal_lag(self):
        """Fast ramp should show thermal lag error."""
        engine = AnalyticalEngine()

        # Precision ramp (1°C/min)
        result_precise = engine.run_melting_point(ASPIRIN_SMILES, ramp_rate_c_min=1.0)
        # Fast ramp (10°C/min)
        result_fast = engine.run_melting_point(ASPIRIN_SMILES, ramp_rate_c_min=10.0)

        # Fast ramp should read higher due to thermal lag
        assert result_fast.onset_c > result_precise.onset_c
        assert result_fast.thermal_lag_warning is True

    def test_mixed_melting_point(self):
        """Mixed MP with authentic standard should confirm identity."""
        engine = AnalyticalEngine()

        # Pure aspirin
        result_pure = engine.run_melting_point(ASPIRIN_SMILES, ramp_rate_c_min=1.0)
        # Mixed 1:1 with authentic standard (same compound)
        result_mixed = engine.run_melting_point(ASPIRIN_SMILES, ramp_rate_c_min=1.0, mixed_with_standard=True)

        # Mixed with same compound should be identical
        assert abs(result_mixed.onset_c - result_pure.onset_c) <= 1.0
        assert abs(result_mixed.clear_c - result_pure.clear_c) <= 1.0
        assert result_mixed.mixed_mp_result == "identical"

    def test_mixed_melting_point_impure(self):
        """Mixed MP with different compound should show depression."""
        engine = AnalyticalEngine()

        # Pure aspirin mixed with paracetamol (different compound)
        result_mixed = engine.run_melting_point(
            ASPIRIN_SMILES,
            ramp_rate_c_min=1.0,
            mixed_with_standard=False,
            mixture_component_smiles=PARACETAMOL_SMILES
        )

        # Should show depressed MP
        assert result_mixed.mixed_mp_result == "depressed"
        assert result_mixed.mp_depression_c > 5.0  # >5°C depression per spec

    def test_melting_point_output_for_godot(self):
        """Melting point result should be serializable for Godot UI."""
        engine = AnalyticalEngine()
        result = engine.run_melting_point(ASPIRIN_SMILES, ramp_rate_c_min=1.0)

        data = result.to_dict()
        assert "onset_c" in data
        assert "clear_c" in data
        assert "range_c" in data
        assert "ramp_rate_c_min" in data
        assert "thermal_lag_warning" in data
        assert "mixed_mp_result" in data
        assert "capillary_observation" in data  # Visual phase transition description


class TestAnalyticalBalance:
    """Test Analytical Balance simulation (draft shield, tare drift, thermal buoyancy)."""

    def test_balance_basic_weighing(self):
        """Balance should return mass reading with 4-decimal precision."""
        engine = AnalyticalEngine()
        result = engine.weigh_sample(mass_g=1.0000, draft_shield_closed=True)

        assert isinstance(result, BalanceResult)
        assert result.displayed_mass_g is not None
        assert result.stable is True
        assert round(result.displayed_mass_g, 4) == 1.0000

    def test_balance_draft_shield_open_flutter(self):
        """Open draft shield should cause readout flutter."""
        engine = AnalyticalEngine()
        result = engine.weigh_sample(mass_g=1.0000, draft_shield_closed=False)

        assert result.stable is False
        assert result.flutter_amplitude_g > 0
        # Flutter amplitude should be ~0.0003 g per config
        assert abs(result.flutter_amplitude_g - 0.0003) < 0.0001

    def test_balance_draft_shield_closed_stable(self):
        """Closed draft shield should stabilize within 1.5s."""
        engine = AnalyticalEngine()
        result = engine.weigh_sample(mass_g=1.0000, draft_shield_closed=True)

        assert result.stable is True
        assert result.stabilization_time_s <= 1.5
        assert result.flutter_amplitude_g < 0.0001

    def test_balance_tare_drift_from_spill(self):
        """Spilled material should cause tare drift."""
        engine = AnalyticalEngine()
        result = engine.weigh_sample(
            mass_g=1.0000,
            draft_shield_closed=True,
            spill_on_pan_mg=5.0
        )

        assert result.tare_drift_g > 0
        # Config: tare_drift_per_spill_g = 0.0015 per spill
        expected_drift = 0.0015 * (5.0 / 1000.0)  # per mg
        assert abs(result.tare_drift_g - expected_drift) < 0.0001

    def test_balance_thermal_buoyancy(self):
        """Hot vessel should show buoyant lift (mass reads low)."""
        engine = AnalyticalEngine()

        # Room temp vessel
        result_cold = engine.weigh_sample(mass_g=1.0000, vessel_temp_c=22.0)
        # Hot vessel (>30°C)
        result_hot = engine.weigh_sample(mass_g=1.0000, vessel_temp_c=40.0)

        # Hot vessel reads lower due to buoyancy
        assert result_hot.displayed_mass_g < result_cold.displayed_mass_g
        # Config: thermal_buoyancy_coefficient_g_per_c = 0.00008
        expected_diff = 0.00008 * (40.0 - 22.0)
        actual_diff = result_cold.displayed_mass_g - result_hot.displayed_mass_g
        assert abs(actual_diff - expected_diff) < 0.0001

    def test_balance_output_for_godot(self):
        """Balance result should be serializable for Godot UI."""
        engine = AnalyticalEngine()
        result = engine.weigh_sample(mass_g=1.0000, draft_shield_closed=True)

        data = result.to_dict()
        assert "displayed_mass_g" in data
        assert "stable" in data
        assert "stabilization_time_s" in data
        assert "flutter_amplitude_g" in data
        assert "tare_drift_g" in data
        assert "precision_decimals" in data


class TestPHMeter:
    """Test pH Meter simulation (Nernst equation, calibration drift, electrode aging)."""

    def test_ph_meter_basic_measurement(self):
        """pH meter should measure pH with Nernst equation."""
        engine = AnalyticalEngine()
        result = engine.measure_ph(ph_true=7.0, calibrated=True)

        assert isinstance(result, PHMeterResult)
        assert result.measured_ph is not None
        assert abs(result.measured_ph - 7.0) < 0.05  # Accurate when calibrated

    def test_ph_meter_nernst_equation(self):
        """Electrode potential should follow Nernst equation."""
        engine = AnalyticalEngine()

        # At 25°C, ideal Nernst slope = 59.16 mV/pH
        result = engine.measure_ph(ph_true=7.0, calibrated=True, temperature_c=25.0)
        assert abs(result.electrode_potential_mv - 0.0) < 1.0  # pH 7 = 0 mV offset

        result_acid = engine.measure_ph(ph_true=4.0, calibrated=True, temperature_c=25.0)
        # ΔpH = 3, ΔE = 59.16 * 3 = 177.48 mV
        expected_delta = 59.16 * 3.0
        actual_delta = abs(result_acid.electrode_potential_mv - result.electrode_potential_mv)
        assert abs(actual_delta - expected_delta) < 5.0

    def test_ph_meter_calibration_slope(self):
        """Calibration should check slope efficiency (95-105%)."""
        engine = AnalyticalEngine()

        # Good calibration
        result_good = engine.measure_ph(ph_true=7.0, calibrated=True, calibration_slope_percent=100.0)
        assert result_good.calibration_valid is True
        assert 95 <= result_good.slope_percent <= 105

        # Poor calibration (old electrode)
        result_bad = engine.measure_ph(ph_true=7.0, calibrated=True, calibration_slope_percent=85.0)
        assert result_bad.calibration_valid is False
        assert result_bad.slope_percent < 95

    def test_ph_meter_uncalibrated_error(self):
        """Uncalibrated electrode should return large error."""
        engine = AnalyticalEngine()
        result = engine.measure_ph(ph_true=7.0, calibrated=False)

        assert result.calibration_valid is False
        assert abs(result.measured_ph - 7.0) > 0.5  # >0.5 pH error per spec
        assert "uncalibrated" in " ".join(result.warnings).lower()

    def test_ph_meter_electrode_aging(self):
        """Aged electrode should show slower response and drift."""
        engine = AnalyticalEngine()

        result_new = engine.measure_ph(ph_true=7.0, calibrated=True, electrode_age_days=0)
        result_old = engine.measure_ph(ph_true=7.0, calibrated=True, electrode_age_days=365)

        assert result_old.response_time_s > result_new.response_time_s
        assert result_old.drift_mv_per_hour > result_new.drift_mv_per_hour

    def test_ph_meter_temperature_compensation(self):
        """ATC should compensate for temperature."""
        engine = AnalyticalEngine()

        # At different temperatures, Nernst slope changes
        result_25 = engine.measure_ph(ph_true=7.0, calibrated=True, temperature_c=25.0, atc=True)
        result_50 = engine.measure_ph(ph_true=7.0, calibrated=True, temperature_c=50.0, atc=True)

        # With ATC, measured pH should be same
        assert abs(result_25.measured_ph - result_50.measured_ph) < 0.05

    def test_ph_meter_output_for_godot(self):
        """pH meter result should be serializable for Godot UI."""
        engine = AnalyticalEngine()
        result = engine.measure_ph(ph_true=7.0, calibrated=True)

        data = result.to_dict()
        assert "measured_ph" in data
        assert "electrode_potential_mv" in data
        assert "temperature_c" in data
        assert "calibration_valid" in data
        assert "slope_percent" in data
        assert "response_time_s" in data
        assert "atc_active" in data


class TestTitrationBuret:
    """Test Titration Buret simulation (dropwise/stream, meniscus, equivalence)."""

    def test_titration_basic_acid_base(self):
        """Acid-base titration should produce sigmoidal curve."""
        engine = AnalyticalEngine()
        result = engine.run_titration(
            analyte_moles=0.002,  # 20 mL of 0.1 M HCl
            titrant_molarity=0.1,  # 0.1 M NaOH
            mode="dropwise"
        )

        assert isinstance(result, TitrationResult)
        assert len(result.titration_curve) > 0  # List of (volume_ml, ph)
        assert result.equivalence_volume_ml is not None

    def test_titration_equivalence_point_detection(self):
        """Equivalence point should be detected via derivative maximum."""
        engine = AnalyticalEngine()
        result = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="dropwise"
        )

        # 0.002 mol HCl / 0.1 M NaOH = 20 mL equivalence
        assert abs(result.equivalence_volume_ml - 20.0) < 0.5

        # Derivative should peak at equivalence
        assert result.first_derivative_max_volume_ml is not None
        assert abs(result.first_derivative_max_volume_ml - result.equivalence_volume_ml) < 0.2

    def test_titration_dropwise_mode(self):
        """Dropwise mode should deliver 0.05 mL per drop every 0.8s."""
        engine = AnalyticalEngine()
        result = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="dropwise"
        )

        # Check drop volume
        volumes = [v for v, _ in result.titration_curve]
        if len(volumes) > 1:
            drop_volumes = [volumes[i+1] - volumes[i] for i in range(len(volumes)-1)]
            avg_drop = sum(drop_volumes) / len(drop_volumes)
            assert abs(avg_drop - 0.05) < 0.01  # 0.05 mL per drop

    def test_titration_stream_mode(self):
        """Stream mode should deliver fast flow (>2 mL/s)."""
        engine = AnalyticalEngine()
        result = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="stream"
        )

        # Stream should reach equivalence faster (larger volume increments)
        volumes = [v for v, _ in result.titration_curve]
        if len(volumes) > 1:
            avg_increment = sum(volumes[i+1] - volumes[i] for i in range(len(volumes)-1)) / (len(volumes)-1)
            assert avg_increment > 0.5  # Much larger than dropwise

    def test_titration_meniscus_parallax(self):
        """Meniscus reading should have parallax error option."""
        engine = AnalyticalEngine()

        result_correct = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="dropwise",
            meniscus_reading="bottom"  # Correct
        )

        result_wrong = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="dropwise",
            meniscus_reading="top"  # Wrong - parallax error
        )

        # Reading from top adds ~0.15 mL systematic error
        assert result_wrong.equivalence_volume_ml > result_correct.equivalence_volume_ml
        assert abs(result_wrong.equivalence_volume_ml - result_correct.equivalence_volume_ml - 0.15) < 0.05

    def test_titration_air_bubble_error(self):
        """Trapped air bubble should cause volume jump."""
        engine = AnalyticalEngine()

        result_normal = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="dropwise",
            air_bubble=False
        )

        result_bubble = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="dropwise",
            air_bubble=True
        )

        # Bubble dislodges causing false volume jump
        assert result_bubble.air_bubble_detected is True
        assert result_bubble.equivalence_volume_ml < result_normal.equivalence_volume_ml

    def test_titration_phenolphthalein_endpoint(self):
        """Visual endpoint with phenolphthalein should trigger at pH 8.2-10."""
        engine = AnalyticalEngine()
        result = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="dropwise",
            indicator="phenolphthalein"
        )

        assert result.visual_endpoint_ml is not None
        # Phenolphthalein endpoint slightly past equivalence (pH ~8.3-10)
        assert result.visual_endpoint_ml >= result.equivalence_volume_ml
        assert result.visual_endpoint_ml - result.equivalence_volume_ml < 0.5

    def test_titration_output_for_godot(self):
        """Titration result should be serializable for Godot UI."""
        engine = AnalyticalEngine()
        result = engine.run_titration(
            analyte_moles=0.002,
            titrant_molarity=0.1,
            mode="dropwise"
        )

        data = result.to_dict()
        assert "titration_curve" in data
        assert "equivalence_volume_ml" in data
        assert "first_derivative" in data
        assert "second_derivative" in data
        assert "visual_endpoint_ml" in data
        assert "indicator_color" in data  # Color for visual indicator
        assert "mode" in data


class TestInstrumentDataStructures:
    """Test that all instruments produce Godot-compatible data structures."""

    def test_all_results_have_to_dict(self):
        """All instrument results should have to_dict method."""
        engine = AnalyticalEngine()

        nmr_result = engine.run_nmr_1h(ASPIRIN_SMILES)
        gcms_result = engine.run_gcms(ASPIRIN_SMILES)
        hplc_result = engine.run_hplc_dad(ASPIRIN_SMILES)
        mp_result = engine.run_melting_point(ASPIRIN_SMILES)
        bal_result = engine.weigh_sample(1.0)
        ph_result = engine.measure_ph(7.0)
        tit_result = engine.run_titration(0.002, 0.1)

        for result in [nmr_result, gcms_result, hplc_result, mp_result, bal_result, ph_result, tit_result]:
            assert hasattr(result, "to_dict")
            data = result.to_dict()
            assert isinstance(data, dict)
            assert len(data) > 0

    def test_results_json_serializable(self):
        """All results should be JSON serializable for IPC."""
        engine = AnalyticalEngine()

        nmr_result = engine.run_nmr_1h(ASPIRIN_SMILES)
        data = nmr_result.to_dict()

        # Should not raise
        json_str = json.dumps(data)
        assert len(json_str) > 0

        # Should be parseable back
        parsed = json.loads(json_str)
        assert parsed["nucleus"] == "1H"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])