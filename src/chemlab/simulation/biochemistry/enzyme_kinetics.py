"""
Enzyme kinetics — Michaelis–Menten, Hill, inhibition models and temperature/pH
dependence. All rate laws return reaction velocity v in mol·L⁻¹·s⁻¹.

References: Briggs–Haldane steady state, Hill cooperative binding, standard
competitive/uncompetitive/non-competitive/mixed inhibition, Arrhenius temperature
correction, bell-shaped pH profile.
"""

from __future__ import annotations

import math

from chemlab.simulation.electrochemistry.constants import R, T0


def michaelis_menten(
    substrate_m: float,
    vmax_m_per_s: float,
    km_m: float,
) -> float:
    """v = Vmax * [S] / (Km + [S])."""
    if substrate_m < 0 or vmax_m_per_s < 0 or km_m <= 0:
        raise ValueError("substrate >= 0, vmax >= 0, km > 0 required")
    return vmax_m_per_s * substrate_m / (km_m + substrate_m)


def hill_equation(
    substrate_m: float,
    vmax_m_per_s: float,
    k05_m: float,
    hill_coefficient: float,
) -> float:
    """v = Vmax * [S]^n / (K0.5^n + [S]^n). n > 1 positive cooperativity."""
    if substrate_m < 0 or vmax_m_per_s < 0 or k05_m <= 0 or hill_coefficient <= 0:
        raise ValueError("substrate >= 0, vmax >= 0, k05 > 0, n > 0 required")
    s_n = substrate_m ** hill_coefficient
    k_n = k05_m ** hill_coefficient
    return vmax_m_per_s * s_n / (k_n + s_n)


def competitive_inhibition(
    substrate_m: float,
    vmax_m_per_s: float,
    km_m: float,
    inhibitor_m: float,
    ki_m: float,
) -> float:
    """Competitive: v = Vmax[S] / (Km(1+[I]/Ki) + [S]); Vmax unchanged, Km↑."""
    if inhibitor_m < 0 or ki_m <= 0:
        raise ValueError("inhibitor >= 0, Ki > 0 required")
    km_app = km_m * (1.0 + inhibitor_m / ki_m)
    return michaelis_menten(substrate_m, vmax_m_per_s, km_app)


def uncompetitive_inhibition(
    substrate_m: float,
    vmax_m_per_s: float,
    km_m: float,
    inhibitor_m: float,
    ki_m: float,
) -> float:
    """Uncompetitive: v = Vmax[S] / (Km + [S](1+[I]/Ki)); Vmax↓, Km↓."""
    if inhibitor_m < 0 or ki_m <= 0:
        raise ValueError("inhibitor >= 0, Ki > 0 required")
    alpha = 1.0 + inhibitor_m / ki_m
    vmax_app = vmax_m_per_s / alpha
    km_app = km_m / alpha
    return michaelis_menten(substrate_m, vmax_app, km_app)


def non_competitive_inhibition(
    substrate_m: float,
    vmax_m_per_s: float,
    km_m: float,
    inhibitor_m: float,
    ki_m: float,
) -> float:
    """Non-competitive: v = Vmax[S] / ((Km + [S])(1+[I]/Ki)); Vmax↓, Km unchanged."""
    if inhibitor_m < 0 or ki_m <= 0:
        raise ValueError("inhibitor >= 0, Ki > 0 required")
    alpha = 1.0 + inhibitor_m / ki_m
    vmax_app = vmax_m_per_s / alpha
    return michaelis_menten(substrate_m, vmax_app, km_m)


def mixed_inhibition(
    substrate_m: float,
    vmax_m_per_s: float,
    km_m: float,
    inhibitor_m: float,
    ki_m: float,
    kii_m: float,
) -> float:
    """Mixed: v = Vmax[S] / (Km(1+[I]/Ki) + [S](1+[I]/Ki'))."""
    if inhibitor_m < 0 or ki_m <= 0 or kii_m <= 0:
        raise ValueError("inhibitor >= 0, Ki > 0, Ki' > 0 required")
    alpha = 1.0 + inhibitor_m / ki_m
    alpha_prime = 1.0 + inhibitor_m / kii_m
    return vmax_m_per_s * substrate_m / (km_m * alpha + substrate_m * alpha_prime)


def substrate_inhibition(
    substrate_m: float,
    vmax_m_per_s: float,
    km_m: float,
    ksi_m: float,
) -> float:
    """Substrate inhibition: v = Vmax[S] / (Km + [S] + [S]²/Ksi)."""
    if substrate_m < 0 or vmax_m_per_s < 0 or km_m <= 0 or ksi_m <= 0:
        raise ValueError("substrate >= 0, vmax >= 0, km > 0, Ksi > 0 required")
    return vmax_m_per_s * substrate_m / (km_m + substrate_m + substrate_m ** 2 / ksi_m)


def arrhenius_rate(
    rate_ref_m_per_s: float,
    activation_energy_kj_mol: float,
    temperature_k: float,
    reference_temperature_k: float = T0,
) -> float:
    """Arrhenius temperature correction: k(T) = k_ref * exp(-Ea/R * (1/T - 1/T_ref))."""
    if temperature_k <= 0 or reference_temperature_k <= 0 or activation_energy_kj_mol < 0:
        raise ValueError("temperatures > 0, Ea >= 0 required")
    exponent = (
        -(activation_energy_kj_mol * 1000.0 / R) * (1.0 / temperature_k - 1.0 / reference_temperature_k)
    )
    exponent = max(-700.0, min(700.0, exponent))  # clamp against overflow
    return rate_ref_m_per_s * math.exp(exponent)


def ph_profile(
    rate_max_m_per_s: float,
    ph: float,
    ph_opt: float,
    pka1: float,
    pka2: float,
) -> float:
    """Bell-shaped pH profile: k = kmax / (1 + 10^(pKa1-pH) + 10^(pH-pKa2))."""
    if rate_max_m_per_s < 0 or pka1 >= pka2:
        raise ValueError("rate_max >= 0, pKa1 < pKa2 required")
    denom = 1.0 + 10.0 ** (pka1 - ph) + 10.0 ** (ph - pka2)
    return rate_max_m_per_s / denom
