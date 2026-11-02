# Photochemistry Simulation — Design Specification

## 1. Purpose
Simulate UV-Vis absorption, fluorescence, phosphorescence, and photoreactions with quantum yield calculations for ChemLab's photochemistry bench (spectrophotometer, fluorimeter, photoreactor).

## 2. Physical Model

### 2.1 Beer-Lambert Absorption
A(λ) = ε(λ) · c · l   ;   T = 10^{-A} ;   %T = 100·10^{-A}
where ε in L·mol⁻¹·cm⁻¹, c in mol/L, l in cm.

Absorbance additivity for mixtures: A_total(λ) = Σ_i ε_i(λ) c_i l.

### 2.2 UV-Vis Spectrum
Discrete samples λ ∈ [190, 1100] nm, step 1 nm. Each species has peaks (λ_max, ε_max, FWHM) modeled as Gaussian:
ε(λ) = ε_max · exp(-(λ-λ_max)²/(2σ²)), σ = FWHM/(2√(2 ln2)).

### 2.3 Fluorescence
Excitation at λ_ex → emission at λ_em (Stokes shift Δλ = λ_em - λ_ex > 0).
Intensity I_f = Φ_f · I_0 · (1 - 10^{-A_ex}) · (ε_em/ε_ex correction) · instrument factor.
Quantum yield: Φ_f = k_r/(k_r + k_nr) = photons emitted / photons absorbed.

### 2.4 Phosphorescence
Triplet emission with lifetime τ_p = 1/(k_p + k_nr^T). Intensity decays I(t) = I_0 exp(-t/τ_p). Delayed relative to fluorescence (μs–s).

### 2.5 Photoreaction Kinetics
d[C]/dt = -Φ · I_abs · σ_abs · [C]  (first-order in absorbed photons).
Quantum yield of reaction: Φ_rxn = (moles product formed)/(moles photons absorbed).
Conversion: X = 1 - exp(-Φ·I_abs·σ·t).

## 3. Data Structures

```python
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

class EmissionType(Enum):
    FLUORESCENCE = "fluorescence"
    PHOSPHORESCENCE = "phosphorescence"

@dataclass
class SpectralPeak:
    lambda_nm: float
    epsilon: float          # L mol^-1 cm^-1
    fwhm_nm: float

@dataclass
class PhotoSpecies:
    id: str
    name: str
    absorption_peaks: list[SpectralPeak]
    emission_peaks: list[SpectralPeak]   # lambda_em, relative intensity
    quantum_yield_fluorescence: float     # Phi_f
    quantum_yield_reaction: float         # Phi_rxn
    triplet_lifetime_s: float             # for phosphorescence
    molar_mass_g_mol: float

@dataclass
class Cuvette:
    path_length_cm: float = 1.0
    species: dict[str, float] = field(default_factory=dict)  # species_id -> mol/L
    temperature_k: float = 298.15

@dataclass
class LightSource:
    wavelength_nm: float
    intensity_w_m2: float   # irradiance at sample
    bandwidth_nm: float = 1.0

@dataclass
class Spectrum:
    wavelengths_nm: np.ndarray   # shape (N,)
    absorbance: np.ndarray       # shape (N,)
    transmittance: np.ndarray    # shape (N,)
    emission: np.ndarray | None = None

@dataclass
class PhotoResult:
    absorbance_at_lambda: float
    transmittance_pct: float
    fluorescence_intensity: float
    phosphorescence_intensity: float
    conversion: float            # reaction conversion 0..1
    quantum_yield_measured: float
```

## 4. Core Algorithms (Python)

```python
import numpy as np

def gaussian_peak(wl, peak: SpectralPeak) -> np.ndarray:
    sigma = peak.fwhm_nm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    return peak.epsilon * np.exp(-((wl - peak.lambda_nm) ** 2) / (2 * sigma * sigma))

def absorption_spectrum(species_list, cuvette, wl):
    A = np.zeros_like(wl, dtype=float)
    for sp in species_list:
        c = cuvette.species.get(sp.id, 0.0)
        if c <= 0: continue
        eps = np.zeros_like(wl)
        for pk in sp.absorption_peaks:
            eps += gaussian_peak(wl, pk)
        A += eps * c * cuvette.path_length_cm
    return A

def transmittance(A):
    return np.power(10.0, -A)

def fluorescence_intensity(species, cuvette, source, wl_em):
    c = cuvette.species.get(species.id, 0.0)
    A_ex = absorption_at(species, cuvette, source.wavelength_nm)
    absorbed_fraction = 1.0 - 10.0 ** (-A_ex)
    I0 = source.intensity_w_m2
    # emission spectrum shape
    em = np.zeros_like(wl_em)
    for pk in species.emission_peaks:
        em += gaussian_peak(wl_em, pk)
    em = em / em.max() if em.max() > 0 else em
    return species.quantum_yield_fluorescence * I0 * absorbed_fraction * em

def phosphorescence_decay(species, t):
    return np.exp(-t / species.triplet_lifetime_s)

def photoreaction_advance(species, cuvette, source, dt):
    c = cuvette.species.get(species.id, 0.0)
    A_ex = absorption_at(species, cuvette, source.wavelength_nm)
    I_abs = source.intensity_w_m2 * (1.0 - 10.0**(-A_ex))  # W/m2 absorbed
    # convert to mol photons / L / s approx: I_abs/(N_A*h*c/lambda) / volume_factor
    # Use simplified: rate = Phi * I_abs * sigma * c
    k = species.quantum_yield_reaction * I_abs * 1e-3  # scaling
    dc = -k * c * dt
    cuvette.species[species.id] = max(0.0, c + dc)
    return -dc
```

## 5. UI / Visualization
- Spectrum plot: x = wavelength nm, y = absorbance (0..3) and emission (relative).
- Color of solution: derive from transmission spectrum converted to sRGB (CIE 1931).
- Fluorescence glow: additive bloom on sample when excitation active.
- Phosphorescence: delayed glow after light off, exponential fade.
- Photoreactor: progress bar of conversion, time slider.

## 6. Validation
- Beer-Lambert: A=1 → T=10%.
- Quantum yields sum ≤ 1 for competing processes.
- Stokes shift positive.
- Conservation: absorbed photons = fluorescence + phosphorescence + reaction + heat.

## 7. Test Cases
1. Single species, A=εcl with known values.
2. Mixture additivity.
3. Fluorescence intensity scales with concentration then saturates.
4. Photoreaction conversion exponential.

## 8. Integration
Plug into `chemlab_core.chemistry` as `photochemistry.py`. Add `PhotoBench` entity type. Reuse `lerp_color` for glow. Export spectrum as CSV/PNG.
