"""
Tests for the galvanic (voltaic) cell model.

Validates open-circuit voltage, load current, power, and discharge.
"""

import pytest

from chemlab.simulation.electrochemistry.galvanic import GalvanicCell
from chemlab.simulation.electrochemistry.half_reactions import HALF_REACTION_REGISTRY


@pytest.mark.unit
def test_daniell_open_circuit_voltage() -> None:
    """E_ocv = E_cathode - E_anode = 1.103 V at unit activities."""
    cell = GalvanicCell(
        anode_material="Zn",
        cathode_material="Cu",
        anode_concentration=1.0,
        cathode_concentration=1.0,
        internal_resistance_ohm=0.1,
    )
    emf = cell.open_circuit_voltage()
    assert abs(emf - 1.103) < 0.005


@pytest.mark.unit
def test_load_current_and_power() -> None:
    """I = E / (R_int + R_load); P = I^2 * R_load = E^2 * R_load / (R_int+R_load)^2."""
    cell = GalvanicCell(
        anode_material="Zn",
        cathode_material="Cu",
        anode_concentration=1.0,
        cathode_concentration=1.0,
        internal_resistance_ohm=1.0,
    )
    load = 9.0
    i = cell.load_current(load_ohm=load)
    assert abs(i - cell.open_circuit_voltage() / (1.0 + load)) < 1e-9
    p = cell.power_w(load_ohm=load)
    assert abs(p - i * i * load) < 1e-9


@pytest.mark.unit
def test_max_power_transfer() -> None:
    """Maximum power is delivered when R_load = R_internal."""
    cell = GalvanicCell(
        anode_material="Zn",
        cathode_material="Cu",
        anode_concentration=1.0,
        cathode_concentration=1.0,
        internal_resistance_ohm=2.0,
    )
    emf = cell.open_circuit_voltage()
    best_p = 0.0
    best_r = 0.0
    for r in [0.5, 1.0, 2.0, 4.0, 8.0]:
        p = cell.power_w(load_ohm=r)
        if p > best_p:
            best_p = p
            best_r = r
    assert abs(best_r - 2.0) < 1e-6
    # Theoretical max: E^2 / (4 * R_int)
    assert abs(best_p - (emf * emf) / (4.0 * 2.0)) < 0.01
