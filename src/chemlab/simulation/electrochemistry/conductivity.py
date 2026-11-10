"""
Conductivity and molar conductivity (Kohlrausch's law).

kappa = sum(z_i * F * u_i * c_i)   (S/m)
Lambda_m = kappa / c               (S·m²/mol)
Kohlrausch: Lambda_m° = lambda°_+ + lambda°_-
"""

from __future__ import annotations


def conductivity_s_m(
    ions: list[tuple[float, float, float]],
) -> float:
    """Electrolyte conductivity.

    ``ions`` is a list of (charge z, mobility u_i in m²/(V·s), concentration c_i in mol/m³).
    Returns kappa in S/m.
    """
    from chemlab.simulation.electrochemistry.constants import F

    return sum(z * F * u * c for z, u, c in ions)


def molar_conductivity_s_m2_mol(
    conductivity_s_m: float,
    concentration_mol_m3: float,
) -> float:
    """Lambda_m = kappa / c in S·m²/mol."""
    if concentration_mol_m3 <= 0:
        return 0.0
    return conductivity_s_m / concentration_mol_m3


def kohlrausch_limiting(
    lambda_plus_s_cm2_mol: float,
    lambda_minus_s_cm2_mol: float,
) -> float:
    """Lambda_m° = lambda°_+ + lambda°_- (independent migration of ions)."""
    return lambda_plus_s_cm2_mol + lambda_minus_s_cm2_mol
