"""
Voltammetry simulation: Randles-Sevcik peak current and Cottrell diffusion current.

All currents in amperes, potentials in volts, diffusion coefficients in m²/s,
areas in cm², scan rates in V/s, concentrations in mol/L.
"""

from __future__ import annotations

import math

from chemlab.simulation.electrochemistry.constants import T0, F, R


class VoltammetryResult:
    """Result of a voltammetry scan simulation."""

    def __init__(
        self,
        potentials_v: list[float],
        currents_a: list[float],
        i_peak_a: float,
        e_peak_v: float,
        i_peak_reverse_a: float | None = None,
        delta_e_p_mv: float | None = None,
    ) -> None:
        self.potentials_v = potentials_v
        self.currents_a = currents_a
        self.i_peak_a = i_peak_a
        self.e_peak_v = e_peak_v
        self.i_peak_reverse_a = i_peak_reverse_a
        self.delta_e_p_mv = delta_e_p_mv


class VoltammetrySimulator:
    """Simulates linear-sweep and cyclic voltammetry for a reversible system."""

    def peak_current_randles_sevcik(
        self,
        n: int,
        area_cm2: float,
        concentration_mol_l: float,
        scan_rate_v_s: float,
        diffusion_coeff_m2_s: float,
        temperature_k: float = T0,
    ) -> float:
        """Randles-Sevcik equation at 25 °C:
        i_p = 0.4463 * n * F * A * C * (n * F * v * D / (R * T))^0.5

        A must be in cm²; the standard constant 2.69e5 (at 25 °C) assumes
        A in cm², C in mol/cm³, v in V/s, D in cm²/s. We convert units here.
        """
        # Convert: concentration mol/L -> mol/cm³ (/1000), D m²/s -> cm²/s (*1e4)
        c_mol_cm3 = concentration_mol_l / 1000.0
        d_cm2_s = diffusion_coeff_m2_s * 1e4
        # Constant 0.4463 * n * F * A * C * sqrt(n*F*v*D/(R*T))
        # With F in C/mol, A in cm², C in mol/cm³, D in cm²/s:
        # result in A (because C * V = J and the unit analysis works out)
        inner = (n * F * scan_rate_v_s * d_cm2_s) / (R * temperature_k)
        return 0.4463 * n * F * area_cm2 * c_mol_cm3 * math.sqrt(inner)

    def cottrell_current(
        self,
        n: int,
        area_cm2: float,
        concentration_mol_l: float,
        diffusion_coeff_m2_s: float,
        time_s: float,
    ) -> float:
        """Cottrell equation: i(t) = n * F * A * C * sqrt(D / (pi * t))."""
        c_mol_cm3 = concentration_mol_l / 1000.0
        d_cm2_s = diffusion_coeff_m2_s * 1e4
        return n * F * area_cm2 * c_mol_cm3 * math.sqrt(d_cm2_s / (math.pi * time_s))

    def scan(
        self,
        electrode_id: str,
        electrolyte_species: str,
        v_start: float,
        v_end: float,
        scan_rate_v_s: float,
        waveform: str,
        analyte: str,
        concentration_mol_l: float,
        diffusion_coeff_m2_s: float,
        area_cm2: float,
        n: int = 1,
        temperature_k: float = T0,
        num_points: int = 1001,
    ) -> VoltammetryResult:
        """Generate a synthetic voltammogram with a single reversible peak.

        Peak position is centred on the standard potential of the analyte
        (approximated here), peak height via Randles-Sevcik, peak shape
        Gaussian around E_peak. For cyclic scans, a reverse peak is mirrored.
        """
        # Approximate formal potential from analyte (placeholder: centre of window)
        e0 = 0.0
        if waveform == "cyclic":
            # Triangle wave: start -> end -> start
            n_half = num_points // 2
            v_forward = [
                v_start + (v_end - v_start) * i / max(n_half - 1, 1) for i in range(n_half)
            ]
            v_reverse = [v_end + (v_start - v_end) * i / max(n_half - 1, 1) for i in range(n_half)]
            potentials = v_forward + v_reverse[1:]
        else:
            potentials = [
                v_start + (v_end - v_start) * i / max(num_points - 1, 1) for i in range(num_points)
            ]

        i_peak = self.peak_current_randles_sevcik(
            n, area_cm2, concentration_mol_l, scan_rate_v_s, diffusion_coeff_m2_s, temperature_k
        )

        # Gaussian peak shape (simplified reversible voltammogram)
        sigma = 0.05  # V, peak width
        currents = []
        for v in potentials:
            i = i_peak * math.exp(-0.5 * ((v - e0) / sigma) ** 2)
            currents.append(i)

        # Peak index
        peak_idx = max(range(len(currents)), key=lambda i: currents[i])
        e_peak = potentials[peak_idx]

        i_peak_reverse = None
        delta_e_p = None
        if waveform == "cyclic":
            # Mirrored reverse peak at ~59/n mV separation
            i_peak_reverse = i_peak * 0.9
            delta_e_p = 59.0 / n  # mV, reversible

        return VoltammetryResult(
            potentials_v=potentials,
            currents_a=currents,
            i_peak_a=i_peak,
            e_peak_v=e_peak,
            i_peak_reverse_a=i_peak_reverse,
            delta_e_p_mv=delta_e_p,
        )
