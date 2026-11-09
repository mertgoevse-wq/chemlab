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
        assert cooh_peak.multiplicity in ("br s", "broad singlet")

    def test_1h_nmr_paracetamol_peaks(self):
        """Paracetamol 1H NMR should have acetyl methyl and aromatic peaks."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(PARACETAMOL_SMILES, solvent="cdcl3")

        acetyl = next((p for p in result.peaks if abs(p.chemical_shift_ppm - 2.10) < 0.15), None)
        assert acetyl is not None
        assert acetyl.integral_h == 3

    def test_1h_nmr_solvent_peak(self):
        """NMR result should include residual solvent peak."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ASPIRIN_SMILES, solvent="cdcl3")

        solvent_peaks = [p for p in result.peaks if p.assignment and "cdcl3" in p.assignment.lower()]
        assert len(solvent_peaks) >= 1
        assert abs(solvent_peaks[0].chemical_shift_ppm - 7.26) < 0.1

    def test_13c_nmr_basic_output(self):
        """13C NMR should produce spectrum with carbon peaks."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_13c(ASPIRIN_SMILES, solvent="cdcl3")

        assert isinstance(result, NMRResult)
        assert result.nucleus == "13C"
        assert result.frequency_mhz == pytest.approx(100.03, rel=0.01)
        assert len(result.peaks) > 0

    def test_nmr_peak_structure(self):
        """NMR peaks should have all required fields."""
        engine = AnalyticalEngine()
        result = engine.run_nmr_1h(ASPIRIN_SMILES)

        for peak in result.peaks:
            assert isinstance(peak.chemical_shift_ppm, float)
            assert isinstance(peak.multiplicity, str)
            assert isinstance(peak.integral_h, int)
            assert peak.integral_h >= 0
            assert isinstance(peak.coupling_constant_hz, float)
            assert isinstance(peak.assignment, str)


class TestGCMS:
    """Test GC-MS simulation."""

    def test_gcms_basic_output(self):
        """GC-MS should produce peaks with retention times and mass spectra."""
        engine = AnalyticalEngine()
        result = engine.run_gc_ms(ASPIRIN_SMILES)

        assert isinstance(result, GCMSResult)
        assert len(result.peaks) > 0
        assert result.column == "DB-5MS"
        assert result.carrier_gas == "He"

    def test_gcms_aspirin_molecular_ion(self):
        """Aspirin GC-MS should show molecular ion at m/z 180."""
        engine = AnalyticalEngine()
        result = engine.run_gc_ms(ASPIRIN_SMILES)

        aspirin_peak = next((p for p in result.peaks if p.molecular_ion_mz == 180), None)
        assert aspirin_peak is not None
        assert aspirin_peak.base_peak_mz == 43  # CH3CO+
        assert aspirin_peak.nist_match_factor > 90
        assert aspirin_peak.area_percent > 95

    def test_gcms_mass_spectrum_structure(self):
        """GC-MS peaks should have proper mass spectrum."""
        engine = AnalyticalEngine()
        result = engine.run_gc_ms(ASPIRIN_SMILES)

        for peak in result.peaks:
            assert isinstance(peak.retention_time_min, float)
            assert peak.retention_time_min > 0
            assert isinstance(peak.mass_spectrum, dict)
            assert len(peak.mass_spectrum) > 0
            assert isinstance(peak.base_peak_mz, int)
            assert peak.base_peak_mz > 0


class TestHPLC:
    """Test HPLC simulation."""

    def test_hplc_basic_output(self):
        """HPLC should produce peaks with retention times and UV spectra."""
        engine = AnalyticalEngine()
        result = engine.run_hplc(ASPIRIN_SMILES)

        assert isinstance(result, HPLCResult)
        assert len(result.peaks) > 0
        assert result.column == "C18"
        assert result.detection_wavelength_nm == 254.0

    def test_hplc_aspirin_retention_time(self):
        """Aspirin HPLC should have reasonable retention time."""
        engine = AnalyticalEngine()
        result = engine.run_hplc(ASPIRIN_SMILES)

        aspirin_peak = result.peaks[0]
        assert 5.0 <= aspirin_peak.retention_time_min <= 12.0
        assert aspirin_peak.purity_percent > 95
        assert len(aspirin_peak.uv_spectrum) > 0

    def test_hplc_uv_spectrum(self):
        """HPLC peaks should have UV spectrum data."""
        engine = AnalyticalEngine()
        result = engine.run_hplc(ASPIRIN_SMILES)

        for peak in result.peaks:
            assert isinstance(peak.uv_spectrum, dict)
            assert 220.0 in peak.uv_spectrum or 254.0 in peak.uv_spectrum
            for wl, abs_val in peak.uv_spectrum.items():
                assert isinstance(wl, float)
                assert isinstance(abs_val, float)
                assert abs_val >= 0


class TestMeltingPoint:
    """Test melting point apparatus simulation."""

    def test_melting_point_aspirin(self):
        """Aspirin melting point should match literature (135-136°C)."""
        engine = AnalyticalEngine()
        result = engine.run_melting_point(ASPIRIN_SMILES)

        assert isinstance(result, MeltingPointResult)
        assert 134.0 <= result.onset_c <= 137.0
        assert 135.0 <= result.clear_c <= 137.0
        assert result.range_c < 2.0  # Sharp melting point

    def test_melting_point_paracetamol(self):
        """Paracetamol melting point should match literature (169-170.5°C)."""
        engine = AnalyticalEngine()
        result = engine.run_melting_point(PARACETAMOL_SMILES)

        assert 168.0 <= result.onset_c <= 171.0
        assert result.range_c < 2.0

    def test_melting_point_purity_estimate(self):
        """Melting point range should correlate with purity estimate."""
        engine = AnalyticalEngine()
        result = engine.run_melting_point(ASPIRIN_SMILES)

        assert result.purity_estimate_percent > 90
        assert result.heating_rate_c_min == 1.0


class TestAnalyticalBalance:
    """Test analytical balance simulation."""

    def test_balance_weighing(self):
        """Balance should return mass with proper uncertainty."""
        engine = AnalyticalEngine()
        result = engine.run_balance(1.0000, num_measurements=10)

        assert isinstance(result, BalanceResult)
        assert 0.9995 <= result.mass_g <= 1.0005
        assert result.readability_g == 0.0001
        assert result.uncertainty_g > 0
        assert result.calibration_status == "calibrated"

    def test_balance_repeatability(self):
        """Balance should show realistic repeatability."""
        engine = AnalyticalEngine()
        result = engine.run_balance(5.0000, num_measurements=20)

        assert result.repeatability_g <= 0.0002
        assert result.draft_shield_closed is True

    def test_balance_linearity(self):
        """Balance linearity specification should be present."""
        engine = AnalyticalEngine()
        result = engine.run_balance(10.0000)

        assert result.linearity_g == 0.0002


class TestPHMeter:
    """Test pH meter simulation."""

    def test_ph_meter_neutral(self):
        """pH meter should read 7.0 for neutral solution."""
        engine = AnalyticalEngine()
        result = engine.run_ph_meter(7.0, 25.0)

        assert isinstance(result, PHMeterResult)
        assert 6.95 <= result.ph <= 7.05
        assert result.temperature_c == 25.0
        assert result.stability_criteria_met is True

    def test_ph_meter_acidic(self):
        """pH meter should read correctly for acidic solution."""
        engine = AnalyticalEngine()
        result = engine.run_ph_meter(1.0, 25.0)

        assert 0.95 <= result.ph <= 1.05

    def test_ph_meter_basic(self):
        """pH meter should read correctly for basic solution."""
        engine = AnalyticalEngine()
        result = engine.run_ph_meter(13.0, 25.0)

        assert 12.95 <= result.ph <= 13.05

    def test_ph_meter_slope(self):
        """pH meter should have proper Nernstian slope."""
        engine = AnalyticalEngine()
        result = engine.run_ph_meter(7.0, 25.0)

        # At 25°C, ideal slope = 59.16 mV/pH
        assert 55.0 <= result.slope_mv_per_ph <= 62.0

    def test_ph_meter_calibration_buffers(self):
        """pH meter should use standard calibration buffers."""
        engine = AnalyticalEngine()
        result = engine.run_ph_meter(7.0, 25.0)

        assert 4.01 in result.calibration_points
        assert 7.00 in result.calibration_points
        assert 10.01 in result.calibration_points


class TestTitration:
    """Test titration simulation."""

    def test_titration_strong_acid_strong_base(self):
        """HCl + NaOH titration should have equivalence at 7.0 pH."""
        engine = AnalyticalEngine()
        result = engine.run_titration(
            analyte="HCl", titrant="NaOH",
            analyte_volume_ml=25.0, analyte_concentration_m=0.1,
            titrant_concentration_m=0.1
        )

        assert isinstance(result, TitrationResult)
        assert result.equivalence_volume_ml == pytest.approx(25.0, rel=0.02)
        assert result.equivalence_ph == 7.0
        assert len(result.curve_data) > 0

    def test_titration_weak_acid_strong_base(self):
        """Acetic acid + NaOH titration should have equivalence > 7."""
        engine = AnalyticalEngine()
        result = engine.run_titration(
            analyte="CH3COOH", titrant="NaOH",
            analyte_volume_ml=25.0, analyte_concentration_m=0.1,
            titrant_concentration_m=0.1
        )

        assert result.equivalence_ph > 7.0
        assert result.equivalence_ph < 10.0

    def test_titration_curve_shape(self):
        """Titration curve should have proper sigmoidal shape."""
        engine = AnalyticalEngine()
        result = engine.run_titration("HCl", "NaOH", 25.0, 0.1, 0.1)

        curve = result.curve_data
        assert len(curve) > 20

        # Check pH starts low
        assert curve[0][1] < 2.0
        # Check pH ends high
        assert curve[-1][1] > 11.0
        # Check equivalence region has steep rise
        eq_region = [(v, ph) for v, ph in curve if 20 <= v <= 30]
        assert len(eq_region) > 5

    def test_titration_indicator_phenolphthalein(self):
        """Phenolphthalein endpoint should be in 8.2-10.0 range."""
        engine = AnalyticalEngine()
        result = engine.run_titration("HCl", "NaOH", 25.0, 0.1, 0.1, "phenolphthalein")

        # Find point where pH enters indicator range
        in_range = [(v, ph) for v, ph in result.curve_data if 8.2 <= ph <= 10.0]
        assert len(in_range) > 0


class TestAnalyticalEngineIntegration:
    """Integration tests for multiple instruments on same sample."""

    def test_aspirin_full_analysis(self):
        """Full analytical characterization of aspirin."""
        engine = AnalyticalEngine()
        smiles = ASPIRIN_SMILES

        nmr = engine.run_nmr_1h(smiles)
        gcms = engine.run_gc_ms(smiles)
        hplc = engine.run_hplc(smiles)
        mp = engine.run_melting_point(smiles)
        balance = engine.run_balance(0.5000)
        ph = engine.run_ph_meter(3.5)  # Aspirin solution pH

        assert nmr.nucleus == "1H"
        assert gcms.peaks[0].molecular_ion_mz == 180
        assert hplc.peaks[0].purity_percent > 95
        assert 134.0 <= mp.onset_c <= 137.0
        assert abs(balance.mass_g - 0.5000) < 0.001

    def test_paracetamol_full_analysis(self):
        """Full analytical characterization of paracetamol."""
        engine = AnalyticalEngine()
        smiles = PARACETAMOL_SMILES

        nmr = engine.run_nmr_1h(smiles)
        gcms = engine.run_gc_ms(smiles)
        mp = engine.run_melting_point(smiles)

        assert len(nmr.peaks) > 3
        assert gcms.peaks[0].molecular_ion_mz == 151
        assert 168.0 <= mp.onset_c <= 171.0


class TestInstrumentConfig:
    """Test instrument configuration loading."""

    def test_custom_config_file(self, tmp_path):
        """Engine should load custom configuration from file."""
        config = {
            "nmr": {"spectrometer_frequency_mhz": 600.0, "default_scans_1h": 32},
            "gc_ms": {"column": "DB-17MS"}
        }
        config_path = tmp_path / "custom_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)

        engine = AnalyticalEngine(str(config_path))
        assert engine.config["nmr"]["spectrometer_frequency_mhz"] == 600.0
        assert engine.config["nmr"]["default_scans_1h"] == 32
        assert engine.config["gc_ms"]["column"] == "DB-17MS"
        # Other values should remain default
        assert engine.config["nmr"]["default_scans_13c"] == 512


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])