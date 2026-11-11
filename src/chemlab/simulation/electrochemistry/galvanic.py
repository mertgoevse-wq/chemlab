"""
Galvanic (voltaic) cell model.

Computes open-circuit voltage, load current, and power delivery for a
two-electrode galvanic cell under an external resistive load.
"""

from __future__ import annotations

from chemlab.simulation.electrochemistry.constants import T0
from chemlab.simulation.electrochemistry.half_reactions import HALF_REACTION_REGISTRY
from chemlab.simulation.electrochemistry.nernst import NernstSolver

# Map common electrode material names to half-reaction registry keys.
MATERIAL_TO_HALF_REACTION: dict[str, str] = {
    "Cu": "cu2_cu",
    "Zn": "zn2_zn",
    "Ag": "ag_ag",
    "Fe": "fe2_fe",
    "Al": "al3_al",
    "Na": "na_na",
}


class GalvanicCell:
    """A galvanic cell with anode/cathode half-reactions and internal resistance."""

    def __init__(
        self,
        anode_material: str,
        cathode_material: str,
        anode_concentration: float = 1.0,
        cathode_concentration: float = 1.0,
        internal_resistance_ohm: float = 0.0,
        temperature_k: float = T0,
    ) -> None:
        self.anode_material = anode_material
        self.cathode_material = cathode_material
        self.anode_concentration = anode_concentration
        self.cathode_concentration = cathode_concentration
        self.internal_resistance_ohm = internal_resistance_ohm
        self.temperature_k = temperature_k

        self._solver = NernstSolver()

        try:
            self.anode_hr = HALF_REACTION_REGISTRY[MATERIAL_TO_HALF_REACTION[anode_material]]
        except KeyError:
            self.anode_hr = HALF_REACTION_REGISTRY[anode_material]
        try:
            self.cathode_hr = HALF_REACTION_REGISTRY[MATERIAL_TO_HALF_REACTION[cathode_material]]
        except KeyError:
            self.cathode_hr = HALF_REACTION_REGISTRY[cathode_material]

    def open_circuit_voltage(self) -> float:
        """E_ocv = E_cathode - E_anode at the given concentrations."""
        return self._solver.cell_emf(
            self.cathode_hr,
            {self.cathode_hr.species_ox: self.cathode_concentration},
            self.anode_hr,
            {self.anode_hr.species_ox: self.anode_concentration},
            self.temperature_k,
        )

    def load_current(self, load_ohm: float) -> float:
        """I = E_ocv / (R_internal + R_load)."""
        if load_ohm < 0:
            raise ValueError("Load resistance must be non-negative.")
        total_r = self.internal_resistance_ohm + load_ohm
        if total_r <= 0.0:
            return 0.0
        return self.open_circuit_voltage() / total_r

    def power_w(self, load_ohm: float) -> float:
        """P = I^2 * R_load."""
        i = self.load_current(load_ohm)
        return i * i * load_ohm

    def max_power_point(self) -> tuple[float, float]:
        """(R_load, P_max) at maximum power transfer: R_load = R_internal."""
        emf = self.open_circuit_voltage()
        r_int = self.internal_resistance_ohm
        p_max = (emf * emf) / (4.0 * r_int) if r_int > 0.0 else 0.0
        return r_int, p_max
