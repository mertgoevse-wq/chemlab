"""
Electrolysis cell model and Faraday's laws.

m = M * I * t / (n * F)
n_e = I * t / F
xi  = I * t / (n * F)
"""

from __future__ import annotations

from dataclasses import dataclass

from chemlab.simulation.electrochemistry.constants import F


@dataclass
class FaradayResult:
    moles_electrons: float
    mass_deposited_g: float
    volume_gas_m3: float | None
    extent_mol: float
    current_efficiency_pct: float | None
    duration_s: float


def faraday_moles_electrons(current_a: float, duration_s: float) -> float:
    """Moles of electrons passed: n_e = I * t / F."""
    return current_a * duration_s / F


def faraday_mass_deposited(
    molar_mass_g_mol: float, current_a: float, duration_s: float, n_electrons: int
) -> float:
    """Mass deposited: m = M * I * t / (n * F)."""
    n_e = faraday_moles_electrons(current_a, duration_s)
    return molar_mass_g_mol * n_e / n_electrons


class ElectrolysisCell:
    """Runs an electrolysis simulation at constant current."""

    def run(
        self,
        electrode_material: str,
        current_a: float,
        duration_s: float,
        target_species: str,
        n_electrons: int,
        molar_mass_g_mol: float | None = None,
        current_efficiency_pct: float | None = None,
    ) -> FaradayResult:
        if current_a < 0.0:
            raise ValueError("Current must be non-negative.")
        if duration_s < 0.0:
            raise ValueError("Duration must be non-negative.")
        if n_electrons <= 0:
            raise ValueError("n_electrons must be positive.")

        moles_e = faraday_moles_electrons(current_a, duration_s)
        extent = moles_e / n_electrons

        if molar_mass_g_mol is None:
            # Approximate from electrode material via periodic-table defaults
            molar_mass_g_mol = _default_molar_mass(electrode_material)
        mass = molar_mass_g_mol * extent

        volume_gas: float | None = None
        # For gaseous products (e.g. H2 at cathode), approximate STP molar volume 22.414 L/mol
        if target_species.lower() in ("h2", "o2", "cl2", "co2"):
            volume_gas = extent * 0.022414  # m³ at STP

        return FaradayResult(
            moles_electrons=moles_e,
            mass_deposited_g=mass,
            volume_gas_m3=volume_gas,
            extent_mol=extent,
            current_efficiency_pct=current_efficiency_pct,
            duration_s=duration_s,
        )


def _default_molar_mass(material: str) -> float:
    table = {
        "Cu": 63.546,
        "Ag": 107.8682,
        "Zn": 65.38,
        "Fe": 55.845,
        "Ni": 58.6934,
        "Pb": 207.2,
        "Sn": 118.71,
    }
    return table.get(material, 63.546)
