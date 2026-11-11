"""
ChemLab Analytical Instruments Simulation Engine.

Verifies all 6 core analytical instruments generate realistic data structures
for Godot UI rendering with proper physical models.
"""

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors

    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


# ============================================================================
# Data Classes for Instrument Results
# ============================================================================


@dataclass
class InstrumentConfig:
    """Configuration for an analytical instrument."""

    name: str
    enabled: bool = True
    parameters: dict = field(default_factory=dict)


@dataclass
class NMRPeak:
    """Single NMR peak with chemical shift, multiplicity, and integral."""

    chemical_shift_ppm: float
    multiplicity: str  # s, d, t, q, m, br s, dd, dt, etc.
    integral_h: int
    coupling_constant_hz: float = 0.0
    assignment: str = ""


@dataclass
class NMRResult:
    """NMR spectrometer result (1H or 13C)."""

    nucleus: str  # "1H" or "13C"
    frequency_mhz: float
    solvent: str
    peaks: list[NMRPeak]
    acquisition_time_s: float = 0.0
    scans: int = 16
    temperature_c: float = 25.0
    processing: dict = field(default_factory=dict)


@dataclass
class GCMSPeak:
    """Single GC-MS peak with retention time and mass spectrum."""

    retention_time_min: float
    mass_spectrum: dict[int, float]  # m/z -> relative intensity
    base_peak_mz: int
    molecular_ion_mz: int | None = None
    compound_name: str = ""
    nist_match_factor: float = 0.0
    area_percent: float = 0.0


@dataclass
class GCMSResult:
    """GC-MS instrument result."""

    peaks: list[GCMSPeak]
    column: str = "DB-5MS"
    temperature_program: str = "60-300°C @ 10°C/min"
    carrier_gas: str = "He"
    flow_rate_ml_min: float = 1.0
    injection_mode: str = "splitless"
    total_ion_chromatogram: list[tuple[float, float]] = field(default_factory=list)


@dataclass
class HPLCPeak:
    """Single HPLC peak with retention time and UV spectrum."""

    retention_time_min: float
    area: float
    height: float
    width_min: float
    uv_spectrum: dict[float, float] = field(default_factory=dict)  # wavelength nm -> absorbance
    compound_name: str = ""
    purity_percent: float = 100.0


@dataclass
class HPLCResult:
    """HPLC instrument result."""

    peaks: list[HPLCPeak]
    column: str = "C18"
    mobile_phase_a: str = "H2O + 0.1% TFA"
    mobile_phase_b: str = "MeCN + 0.1% TFA"
    gradient: str = "5-95% B over 20 min"
    flow_rate_ml_min: float = 1.0
    detection_wavelength_nm: float = 254.0
    column_temp_c: float = 30.0


@dataclass
class MeltingPointResult:
    """Melting point apparatus result."""

    onset_c: float
    clear_c: float
    range_c: float
    heating_rate_c_min: float = 1.0
    atmosphere: str = "air"
    sample_mass_mg: float = 2.0
    purity_estimate_percent: float = 0.0


@dataclass
class BalanceResult:
    """Analytical balance result."""

    mass_g: float
    readability_g: float = 0.0001
    repeatability_g: float = 0.0001
    linearity_g: float = 0.0002
    uncertainty_g: float = 0.0001
    calibration_status: str = "calibrated"
    draft_shield_closed: bool = True
    temperature_c: float = 22.0


@dataclass
class PHMeterResult:
    """pH meter result."""

    ph: float
    temperature_c: float = 25.0
    electrode_type: str = "glass_combination"
    slope_mv_per_ph: float = 59.16
    offset_mv: float = 0.0
    calibration_points: list[float] = field(default_factory=lambda: [4.01, 7.00, 10.01])
    stability_criteria_met: bool = True


@dataclass
class TitrationResult:
    """Titration result."""

    equivalence_volume_ml: float
    equivalence_ph: float
    concentration_m: float
    indicator: str = "phenolphthalein"
    titrant: str = "NaOH"
    analyte: str = "HCl"
    curve_data: list[tuple[float, float]] = field(default_factory=list)  # (volume_ml, pH)


# ============================================================================
# Analytical Engine
# ============================================================================


class AnalyticalEngine:
    """Simulation engine for all 6 core analytical instruments."""

    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self._compound_cache: dict[str, dict] = {}

    def _load_config(self, config_path: str | None) -> dict:
        """Load instrument tuning configuration from JSON or use defaults."""
        default_config = {
            "nmr": {
                "spectrometer_frequency_mhz": 400.13,
                "default_scans_1h": 16,
                "default_scans_13c": 512,
                "residual_solvent_shifts_1h": {
                    "cdcl3": 7.26,
                    "dmso_d6": 2.50,
                    "d2o": 4.79,
                    "acetone_d6": 2.05,
                    "methanol_d4": 3.31,
                },
                "residual_solvent_shifts_13c": {
                    "cdcl3": 77.16,
                    "dmso_d6": 39.52,
                    "acetone_d6": 29.84,
                },
                "line_broadening_hz": 0.3,
                "digital_resolution_hz": 0.5,
            },
            "gc_ms": {
                "column": "DB-5MS",
                "column_length_m": 30.0,
                "column_id_mm": 0.25,
                "film_thickness_um": 0.25,
                "temperature_program": "60-300°C @ 10°C/min",
                "carrier_gas": "He",
                "flow_rate_ml_min": 1.0,
                "injection_temp_c": 250.0,
                "transfer_line_temp_c": 280.0,
                "ion_source_temp_c": 230.0,
                "quad_temp_c": 150.0,
                "scan_range_mz": [35, 500],
                "solvent_delay_min": 3.0,
            },
            "hplc": {
                "column": "C18",
                "column_length_mm": 150,
                "column_id_mm": 4.6,
                "particle_size_um": 5.0,
                "mobile_phase_a": "H2O + 0.1% TFA",
                "mobile_phase_b": "MeCN + 0.1% TFA",
                "gradient": "5-95% B over 20 min",
                "flow_rate_ml_min": 1.0,
                "detection_wavelength_nm": 254.0,
                "column_temp_c": 30.0,
                "injection_volume_ul": 10.0,
            },
            "titrator": {
                "burette_volume_ml": 50.0,
                "min_increment_ml": 0.01,
                "default_titrant": "NaOH",
                "default_titrant_concentration_m": 0.1,
                "endpoint_detection": "ph_electrode",
                "stirring_rate_rpm": 300,
            },
            "analytical_balance": {
                "max_capacity_g": 220.0,
                "readability_g": 0.0001,
                "repeatability_g": 0.0001,
                "linearity_g": 0.0002,
                "calibration_weight_class": "E2",
                "warmup_time_min": 60,
            },
            "ph_meter": {
                "electrode_type": "glass_combination",
                "temperature_compensation": "auto",
                "calibration_buffers": [4.01, 7.00, 10.01],
                "slope_tolerance_percent": 5.0,
                "stability_threshold_mv": 0.5,
            },
            "melting_point": {
                "heating_rate_c_min": 1.0,
                "max_temp_c": 400.0,
                "sample_mass_mg": 2.0,
                "capillary_od_mm": 1.5,
                "capillary_id_mm": 1.0,
            },
        }

        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                user_config = json.load(f)
                # Deep merge
                for key, value in user_config.items():
                    if key in default_config and isinstance(default_config[key], dict):
                        default_config[key].update(value)
                    else:
                        default_config[key] = value

        return default_config

    def _get_compound_properties(self, smiles: str) -> dict:
        """Get molecular properties from SMILES using RDKit or fallback."""
        if smiles in self._compound_cache:
            return self._compound_cache[smiles]

        props = {}
        if RDKIT_AVAILABLE:
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                mol = Chem.AddHs(mol)
                AllChem.EmbedMolecule(mol, randomSeed=42)
                AllChem.MMFFOptimizeMolecule(mol)

                props["molecular_weight"] = Descriptors.MolWt(mol)
                props["formula"] = rdMolDescriptors.CalcMolFormula(mol)
                props["num_rotatable_bonds"] = Descriptors.NumRotatableBonds(mol)
                props["num_h_donors"] = Descriptors.NumHDonors(mol)
                props["num_h_acceptors"] = Descriptors.NumHAcceptors(mol)
                props["tpsa"] = Descriptors.TPSA(mol)
                props["logp"] = Descriptors.MolLogP(mol)
                props["num_aromatic_rings"] = Descriptors.NumAromaticRings(mol)
                props["heavy_atom_count"] = mol.GetNumHeavyAtoms()

                # Generate 3D conformer for NMR prediction
                props["conformer"] = mol.GetConformer()
            else:
                props = self._fallback_properties(smiles)
        else:
            props = self._fallback_properties(smiles)

        self._compound_cache[smiles] = props
        return props

    def _fallback_properties(self, smiles: str) -> dict:
        """Fallback properties for known compounds when RDKit unavailable."""
        known = {
            "CC(=O)Oc1ccccc1C(=O)O": {  # Aspirin
                "molecular_weight": 180.158,
                "formula": "C9H8O4",
                "num_rotatable_bonds": 3,
                "num_h_donors": 1,
                "num_h_acceptors": 4,
                "tpsa": 63.6,
                "logp": 1.19,
                "num_aromatic_rings": 1,
                "heavy_atom_count": 13,
            },
            "CC(=O)Nc1ccc(O)cc1": {  # Paracetamol
                "molecular_weight": 151.163,
                "formula": "C8H9NO2",
                "num_rotatable_bonds": 2,
                "num_h_donors": 2,
                "num_h_acceptors": 3,
                "tpsa": 49.3,
                "logp": 0.46,
                "num_aromatic_rings": 1,
                "heavy_atom_count": 11,
            },
            "c1ccc(cc1)C=O": {  # Benzaldehyde
                "molecular_weight": 106.12,
                "formula": "C7H6O",
                "num_rotatable_bonds": 1,
                "num_h_donors": 0,
                "num_h_acceptors": 1,
                "tpsa": 17.1,
                "logp": 1.48,
                "num_aromatic_rings": 1,
                "heavy_atom_count": 8,
            },
            "CCO": {  # Ethanol
                "molecular_weight": 46.07,
                "formula": "C2H6O",
                "num_rotatable_bonds": 1,
                "num_h_donors": 1,
                "num_h_acceptors": 1,
                "tpsa": 20.2,
                "logp": -0.31,
                "num_aromatic_rings": 0,
                "heavy_atom_count": 3,
            },
        }
        return known.get(
            smiles,
            {
                "molecular_weight": 100.0,
                "formula": "CxHyOz",
                "num_rotatable_bonds": 2,
                "num_h_donors": 1,
                "num_h_acceptors": 2,
                "tpsa": 30.0,
                "logp": 1.0,
                "num_aromatic_rings": 0,
                "heavy_atom_count": 6,
            },
        )

    # -----------------------------------------------------------------------
    # NMR Spectrometer (1H / 13C)
    # -----------------------------------------------------------------------

    def run_nmr_1h(
        self, smiles: str, solvent: str = "cdcl3", scans: int | None = None
    ) -> NMRResult:
        """Simulate 1H NMR spectrum at 400 MHz."""
        config = self.config["nmr"]
        freq = config["spectrometer_frequency_mhz"]
        scans = scans or config["default_scans_1h"]

        props = self._get_compound_properties(smiles)
        peaks = self._predict_1h_nmr_peaks(smiles, props, solvent)

        # Add residual solvent peak
        if solvent in config["residual_solvent_shifts_1h"]:
            solvent_shift = config["residual_solvent_shifts_1h"][solvent]
            peaks.append(
                NMRPeak(
                    chemical_shift_ppm=solvent_shift,
                    multiplicity="s",
                    integral_h=0,
                    assignment=f"{solvent} residual",
                )
            )

        return NMRResult(
            nucleus="1H",
            frequency_mhz=freq,
            solvent=solvent,
            peaks=sorted(peaks, key=lambda p: p.chemical_shift_ppm),
            scans=scans,
            acquisition_time_s=scans * 2.0,
        )

    def run_nmr_13c(
        self, smiles: str, solvent: str = "cdcl3", scans: int | None = None
    ) -> NMRResult:
        """Simulate 13C NMR spectrum at 100 MHz."""
        config = self.config["nmr"]
        freq = config["spectrometer_frequency_mhz"] / 4.0  # ~100 MHz
        scans = scans or config["default_scans_13c"]

        props = self._get_compound_properties(smiles)
        peaks = self._predict_13c_nmr_peaks(smiles, props, solvent)

        return NMRResult(
            nucleus="13C",
            frequency_mhz=freq,
            solvent=solvent,
            peaks=sorted(peaks, key=lambda p: p.chemical_shift_ppm),
            scans=scans,
            acquisition_time_s=scans * 1.5,
        )

    def _predict_1h_nmr_peaks(self, smiles: str, props: dict, solvent: str) -> list[NMRPeak]:
        """Predict 1H NMR peaks based on molecular structure."""
        # Known compound databases for common pharmaceuticals
        known_spectra = {
            "CC(=O)Oc1ccccc1C(=O)O": [  # Aspirin
                NMRPeak(2.35, "s", 3, 0.0, "COCH3"),
                NMRPeak(7.14, "d", 1, 7.5, "H-3'"),
                NMRPeak(7.35, "t", 1, 7.5, "H-4'"),
                NMRPeak(7.62, "t", 1, 7.5, "H-5'"),
                NMRPeak(8.13, "dd", 1, 7.5, "H-2',6'"),
                NMRPeak(11.2, "br s", 1, 0.0, "COOH"),
            ],
            "CC(=O)Nc1ccc(O)cc1": [  # Paracetamol
                NMRPeak(2.10, "s", 3, 0.0, "COCH3"),
                NMRPeak(6.70, "d", 2, 8.5, "H-3,5"),
                NMRPeak(7.40, "d", 2, 8.5, "H-2,6"),
                NMRPeak(9.80, "s", 1, 0.0, "OH"),
                NMRPeak(10.2, "s", 1, 0.0, "NH"),
            ],
            "c1ccc(cc1)C=O": [  # Benzaldehyde
                NMRPeak(7.50, "t", 1, 7.5, "H-4"),
                NMRPeak(7.60, "t", 2, 7.5, "H-3,5"),
                NMRPeak(7.90, "d", 2, 7.5, "H-2,6"),
                NMRPeak(10.0, "s", 1, 0.0, "CHO"),
            ],
            "CCO": [  # Ethanol
                NMRPeak(1.25, "t", 3, 7.0, "CH3"),
                NMRPeak(3.72, "q", 2, 7.0, "CH2"),
                NMRPeak(5.30, "br s", 1, 0.0, "OH"),
            ],
        }

        if smiles in known_spectra:
            return known_spectra[smiles]

        # Fallback: generate plausible peaks based on molecular properties
        peaks = []
        mw = props.get("molecular_weight", 100)
        n_h = max(1, int(mw / 15))  # Rough estimate of H count

        # Aliphatic region
        if n_h > 3:
            peaks.append(
                NMRPeak(
                    chemical_shift_ppm=1.2 + random.uniform(-0.3, 0.5),
                    multiplicity="t" if random.random() > 0.5 else "s",
                    integral_h=min(3, n_h // 3),
                    assignment="aliphatic CH3",
                )
            )
            n_h -= 3

        # Methylene
        if n_h > 2:
            peaks.append(
                NMRPeak(
                    chemical_shift_ppm=1.6 + random.uniform(-0.3, 1.0),
                    multiplicity="m",
                    integral_h=min(2, n_h // 2),
                    assignment="CH2",
                )
            )
            n_h -= 2

        # Methine or heteroatom-attached
        if n_h > 0:
            shift = 3.5 + random.uniform(0, 1.5)
            if props.get("num_h_acceptors", 0) > 0:
                shift += 0.5
            peaks.append(
                NMRPeak(
                    chemical_shift_ppm=shift,
                    multiplicity="m",
                    integral_h=min(1, n_h),
                    assignment="CH-X",
                )
            )
            n_h -= 1

        # Aromatic
        if props.get("num_aromatic_rings", 0) > 0:
            n_aromatic_h = min(4, props.get("heavy_atom_count", 6) - 6)
            peaks.append(
                NMRPeak(
                    chemical_shift_ppm=7.2 + random.uniform(-0.3, 0.5),
                    multiplicity="m",
                    integral_h=n_aromatic_h,
                    assignment="Ar-H",
                )
            )

        # Exchangeable protons (OH, NH)
        if props.get("num_h_donors", 0) > 0:
            peaks.append(
                NMRPeak(
                    chemical_shift_ppm=random.uniform(4.0, 12.0),
                    multiplicity="br s",
                    integral_h=props["num_h_donors"],
                    assignment="exchangeable",
                )
            )

        return peaks

    def _predict_13c_nmr_peaks(self, smiles: str, props: dict, solvent: str) -> list[NMRPeak]:
        """Predict 13C NMR peaks."""
        known_13c = {
            "CC(=O)Oc1ccccc1C(=O)O": [  # Aspirin
                NMRPeak(20.8, "s", 1, assignment="COCH3"),
                NMRPeak(128.5, "s", 1, assignment="C-3',5'"),
                NMRPeak(129.8, "s", 1, assignment="C-4'"),
                NMRPeak(130.2, "s", 1, assignment="C-2',6'"),
                NMRPeak(133.5, "s", 1, assignment="C-1'"),
                NMRPeak(169.8, "s", 1, assignment="COCH3"),
                NMRPeak(169.2, "s", 1, assignment="COOAr"),
            ],
        }

        if smiles in known_13c:
            return known_13c[smiles]

        # Generic fallback
        n_c = props.get("heavy_atom_count", 6)
        peaks = []
        for i in range(n_c):
            if i == 0:
                shift = 10.0 + random.uniform(0, 30)  # Methyl
            elif i < n_c * 0.3:
                shift = 20.0 + random.uniform(0, 30)  # Aliphatic
            elif i < n_c * 0.6:
                shift = 60.0 + random.uniform(0, 40)  # Heteroatom-attached
            elif i < n_c * 0.9:
                shift = 120.0 + random.uniform(0, 30)  # Aromatic/olefinic
            else:
                shift = 170.0 + random.uniform(0, 30)  # Carbonyl
            peaks.append(NMRPeak(chemical_shift_ppm=shift, multiplicity="s", integral_h=1))

        return peaks

    # -----------------------------------------------------------------------
    # GC-MS
    # -----------------------------------------------------------------------

    def run_gc_ms(self, smiles: str, column: str | None = None) -> GCMSResult:
        """Simulate GC-MS analysis."""
        config = self.config["gc_ms"]
        column = column or config["column"]

        props = self._get_compound_properties(smiles)
        peaks = self._predict_gc_ms_peaks(smiles, props)

        # Generate TIC
        tic = []
        for peak in peaks:
            for i in range(10):
                rt = peak.retention_time_min - 0.05 + i * 0.01
                intensity = peak.mass_spectrum.get(peak.base_peak_mz, 100) * (1 - abs(i - 5) * 0.1)
                tic.append((rt, intensity))

        return GCMSResult(
            peaks=peaks,
            column=column,
            temperature_program=config["temperature_program"],
            carrier_gas=config["carrier_gas"],
            flow_rate_ml_min=config["flow_rate_ml_min"],
            injection_mode="splitless",
            total_ion_chromatogram=tic,
        )

    def _predict_gc_ms_peaks(self, smiles: str, props: dict) -> list[GCMSPeak]:
        """Predict GC-MS peaks with retention times and mass spectra."""
        known = {
            "CC(=O)Oc1ccccc1C(=O)O": [  # Aspirin
                GCMSPeak(
                    retention_time_min=8.45,
                    mass_spectrum={43: 100, 120: 45, 138: 80, 180: 25, 92: 30, 65: 20},
                    base_peak_mz=43,
                    molecular_ion_mz=180,
                    compound_name="Aspirin",
                    nist_match_factor=96.5,
                    area_percent=98.2,
                ),
            ],
            "CC(=O)Nc1ccc(O)cc1": [  # Paracetamol
                GCMSPeak(
                    retention_time_min=6.82,
                    mass_spectrum={109: 100, 151: 65, 80: 40, 110: 35, 53: 25},
                    base_peak_mz=109,
                    molecular_ion_mz=151,
                    compound_name="Paracetamol",
                    nist_match_factor=94.8,
                    area_percent=97.5,
                ),
            ],
        }

        if smiles in known:
            return known[smiles]

        # Generic prediction
        mw = props.get("molecular_weight", 100)
        rt = 2.0 + (mw / 500) * 25 + random.uniform(-1, 1)

        # Generate plausible mass spectrum
        spectrum = {}
        # Molecular ion
        spectrum[round(mw)] = random.uniform(10, 80)
        # Common fragments
        spectrum[43] = 100  # CH3CO+
        spectrum[77] = random.uniform(20, 60)  # C6H5+
        spectrum[91] = random.uniform(30, 80)  # C7H7+
        spectrum[57] = random.uniform(15, 50)  # C4H9+

        base_peak = max(spectrum, key=spectrum.get)
        mol_ion = round(mw) if spectrum.get(round(mw), 0) > 5 else None

        return [
            GCMSPeak(
                retention_time_min=rt,
                mass_spectrum=spectrum,
                base_peak_mz=base_peak,
                molecular_ion_mz=mol_ion,
                compound_name=f"Unknown (MW {mw:.1f})",
                nist_match_factor=random.uniform(70, 90),
                area_percent=random.uniform(85, 99),
            )
        ]

    # -----------------------------------------------------------------------
    # HPLC
    # -----------------------------------------------------------------------

    def run_hplc(
        self, smiles: str, column: str | None = None, wavelength: float | None = None
    ) -> HPLCResult:
        """Simulate HPLC analysis with UV detection."""
        config = self.config["hplc"]
        column = column or config["column"]
        wavelength = wavelength or config["detection_wavelength_nm"]

        props = self._get_compound_properties(smiles)
        peaks = self._predict_hplc_peaks(smiles, props, wavelength)

        return HPLCResult(
            peaks=peaks,
            column=column,
            mobile_phase_a=config["mobile_phase_a"],
            mobile_phase_b=config["mobile_phase_b"],
            gradient=config["gradient"],
            flow_rate_ml_min=config["flow_rate_ml_min"],
            detection_wavelength_nm=wavelength,
            column_temp_c=config["column_temp_c"],
        )

    def _predict_hplc_peaks(self, smiles: str, props: dict, wavelength: float) -> list[HPLCPeak]:
        """Predict HPLC peaks with UV spectra."""
        known = {
            "CC(=O)Oc1ccccc1C(=O)O": [  # Aspirin
                HPLCPeak(
                    retention_time_min=7.85,
                    area=12450.0,
                    height=1890.0,
                    width_min=0.12,
                    uv_spectrum={220.0: 1.2, 254.0: 0.95, 280.0: 0.6, 300.0: 0.3},
                    compound_name="Aspirin",
                    purity_percent=99.2,
                ),
            ],
        }

        if smiles in known:
            return known[smiles]

        # Generic prediction
        mw = props.get("molecular_weight", 100)
        logp = props.get("logp", 1.0)
        rt = 1.5 + (logp + 2) * 3 + random.uniform(-0.5, 0.5)

        # UV spectrum based on chromophores
        uv_spec = {}
        if props.get("num_aromatic_rings", 0) > 0:
            uv_spec[220.0] = random.uniform(1.0, 1.5)
            uv_spec[254.0] = random.uniform(0.8, 1.2)
            uv_spec[280.0] = random.uniform(0.4, 0.8)
        if props.get("num_h_acceptors", 0) > 2:
            uv_spec[210.0] = random.uniform(1.2, 1.8)
        for w in [200.0, 220.0, 254.0, 280.0, 300.0]:
            if w not in uv_spec:
                uv_spec[w] = random.uniform(0.05, 0.3)

        return [
            HPLCPeak(
                retention_time_min=rt,
                area=random.uniform(5000, 20000),
                height=random.uniform(500, 3000),
                width_min=random.uniform(0.08, 0.15),
                uv_spectrum=uv_spec,
                compound_name=f"Compound (MW {mw:.1f})",
                purity_percent=random.uniform(95, 99.9),
            )
        ]

    # -----------------------------------------------------------------------
    # Melting Point
    # -----------------------------------------------------------------------

    def run_melting_point(
        self, smiles: str, heating_rate: float | None = None
    ) -> MeltingPointResult:
        """Simulate melting point determination."""
        config = self.config["melting_point"]
        heating_rate = heating_rate or config["heating_rate_c_min"]

        known_mp = {
            "CC(=O)Oc1ccccc1C(=O)O": (135.0, 136.0),  # Aspirin
            "CC(=O)Nc1ccc(O)cc1": (169.0, 170.5),  # Paracetamol
            "c1ccc(cc1)C=O": (-26.0, -25.0),  # Benzaldehyde (bp 178°C)
        }

        if smiles in known_mp:
            onset, clear = known_mp[smiles]
        else:
            # Estimate from molecular weight and structure
            mw = props.get("molecular_weight", 100)
            base_mp = 50 + (mw - 100) * 0.5 + random.uniform(-20, 20)
            onset = max(-50, base_mp + random.uniform(-5, 5))
            clear = onset + random.uniform(0.5, 3.0)

        return MeltingPointResult(
            onset_c=onset,
            clear_c=clear,
            range_c=clear - onset,
            heating_rate_c_min=heating_rate,
            atmosphere="air",
            sample_mass_mg=config["sample_mass_mg"],
            purity_estimate_percent=100 - (clear - onset) * 10 + 0.1,
        )

    # -----------------------------------------------------------------------
    # Analytical Balance
    # -----------------------------------------------------------------------

    def run_balance(self, target_mass_g: float, num_measurements: int = 5) -> BalanceResult:
        """Simulate analytical balance weighing."""
        config = self.config["analytical_balance"]

        # Simulate measurement uncertainty
        readability = config["readability_g"]
        repeatability = config["repeatability_g"]

        measurements = []
        for _ in range(num_measurements):
            noise = random.gauss(0, repeatability)
            measurements.append(target_mass_g + noise)

        mean_mass = sum(measurements) / len(measurements)
        std_dev = math.sqrt(
            sum((m - mean_mass) ** 2 for m in measurements) / (len(measurements) - 1)
        )
        uncertainty = max(readability * 2, std_dev * 2)  # k=2 coverage factor

        return BalanceResult(
            mass_g=round(mean_mass, 4),
            readability_g=readability,
            repeatability_g=round(std_dev, 6),
            linearity_g=config["linearity_g"],
            uncertainty_g=round(uncertainty, 6),
            calibration_status="calibrated",
            draft_shield_closed=True,
            temperature_c=22.0,
        )

    # -----------------------------------------------------------------------
    # pH Meter
    # -----------------------------------------------------------------------

    def run_ph_meter(self, solution_ph: float, temperature_c: float = 25.0) -> PHMeterResult:
        """Simulate pH meter measurement."""
        config = self.config["ph_meter"]

        # Electrode response with Nernst equation
        ideal_slope = 59.16 * (temperature_c + 273.15) / 298.15
        slope = ideal_slope * random.uniform(0.95, 1.02)  # 95-102% slope
        offset = random.gauss(0, 2)  # mV

        # Measured potential
        e_measured = offset - slope * (solution_ph - 7.0)

        # Calculate displayed pH (with small noise)
        noise = random.gauss(0, 0.01)
        displayed_ph = round(solution_ph + noise, 2)

        # Stability check
        stability = abs(slope - ideal_slope) / ideal_slope * 100 < config["slope_tolerance_percent"]

        return PHMeterResult(
            ph=displayed_ph,
            temperature_c=temperature_c,
            electrode_type=config["electrode_type"],
            slope_mv_per_ph=round(slope, 2),
            offset_mv=round(offset, 1),
            calibration_points=config["calibration_buffers"],
            stability_criteria_met=stability,
        )

    # -----------------------------------------------------------------------
    # Titration
    # -----------------------------------------------------------------------

    def run_titration(
        self,
        analyte: str = "HCl",
        titrant: str = "NaOH",
        analyte_volume_ml: float = 25.0,
        analyte_concentration_m: float = 0.1,
        titrant_concentration_m: float = 0.1,
        indicator: str = "phenolphthalein",
    ) -> TitrationResult:
        """Simulate acid-base titration."""
        config = self.config["titrator"]

        # Calculate equivalence point
        mmol_analyte = analyte_volume_ml * analyte_concentration_m
        eq_volume_ml = mmol_analyte / titrant_concentration_m

        # pH at equivalence (for strong acid/strong base = 7.0)
        if analyte in ["HCl", "HNO3", "H2SO4"] and titrant in ["NaOH", "KOH"]:
            eq_ph = 7.0
        elif analyte in ["CH3COOH"] and titrant in ["NaOH", "KOH"]:
            eq_ph = 8.7  # Weak acid + strong base
        else:
            eq_ph = 7.0

        # Indicator transition range
        indicator_ranges = {
            "phenolphthalein": (8.2, 10.0),
            "methyl_orange": (3.1, 4.4),
            "bromothymol_blue": (6.0, 7.6),
        }
        ind_range = indicator_ranges.get(indicator, (8.2, 10.0))

        # Generate titration curve
        curve = []
        for i in range(0, int(eq_volume_ml * 2 * 10) + 1):
            vol = i * 0.1
            if vol <= eq_volume_ml * 0.9:
                # Before equivalence - excess analyte
                if analyte in ["HCl", "HNO3"]:
                    excess_mmol = mmol_analyte - vol * titrant_concentration_m
                    total_vol = analyte_volume_ml + vol
                    h_conc = excess_mmol / total_vol
                    ph = -math.log10(max(h_conc, 1e-7))
                else:
                    ph = 2.0 + (vol / (eq_volume_ml * 0.9)) * 4
            elif vol <= eq_volume_ml * 1.1:
                # Equivalence region - steep rise
                frac = (vol - eq_volume_ml * 0.9) / (eq_volume_ml * 0.2)
                ph = 4.0 + frac * (eq_ph + 3 - 4.0)
            else:
                # After equivalence - excess titrant
                excess_mmol = vol * titrant_concentration_m - mmol_analyte
                total_vol = analyte_volume_ml + vol
                oh_conc = excess_mmol / total_vol
                poh = -math.log10(max(oh_conc, 1e-7))
                ph = 14.0 - poh

            curve.append((round(vol, 1), round(ph, 2)))

        return TitrationResult(
            equivalence_volume_ml=round(eq_volume_ml, 2),
            equivalence_ph=eq_ph,
            concentration_m=round(mmol_analyte / analyte_volume_ml, 4),
            indicator=indicator,
            titrant=titrant,
            analyte=analyte,
            curve_data=curve,
        )


# Global instance for easy access
ANALYTICAL_ENGINE = AnalyticalEngine()
