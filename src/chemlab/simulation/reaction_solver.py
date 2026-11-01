"""
ChemLab Reaction Solver Engine
Handles all chemical reaction state machines, mixing logic, pH transitions,
and visual-event emission for the virtual chemistry lab.
"""

from __future__ import annotations

import numpy as np

from chemlab.models import (
    LiquidMixture,
    ReactionType,
)

# ── Reaction rate constants ───────────────────────────────────────────────

MIXING_KW: float = 0.6  # Thermal equilibration rate (s⁻¹)
NEUTRALIZATION_KW: float = 1.2  # Acid-base neutralization speed
OBSCILLATOR_KW: float = 0.08  # Briggs–Rauscher oscillating clock base rate
CATALYST_MULTIPLIER: dict[str, float] = {
    "potassium_iodide": 5.0,
    "manganese_sulfate": 4.0,
    "manganese_dioxide": 3.5,
}


# ── Reaction classification helpers ───────────────────────────────────────


def _classify_reaction_type(
    mixture: LiquidMixture,
    reacting_reagents: list[str],
) -> ReactionType:
    """Heuristic classification of what kind of reaction just occurred."""
    # Acid + base => neutralization
    has_hcl = "hcl" in mixture.reagent_moles or "universal_indicator" in mixture.reagent_moles
    has_naoh = "naoh" in mixture.reagent_moles
    has_h2o2 = "hydrogen_peroxide" in mixture.reagent_moles
    has_ki = "potassium_iodide" in mixture.reagent_moles

    if has_hcl and has_naoh:
        return ReactionType.ACID_BASE_NEUTRALIZATION

    if has_h2o2 and has_ki:
        return ReactionType.CATALYTIC_FOAM_ERUPTION

    if "malonic_acid" in mixture.reagent_moles and has_h2o2 and has_ki:
        return ReactionType.OSCILLATING_COLOR_WAVE

    # Precipitation
    if "lead_nitrate" in mixture.reagent_moles:
        return ReactionType.PRECIPITATION_FALL

    # Chemiluminescence fallback
    if "luminol" in mixture.reagent_moles:
        return ReactionType.CHEMILUMINESCENT_GLOW

    return ReactionType.NONE


# ── Core simulation primitive: mixing ─────────────────────────────────────


def mix_liquids(
    a: LiquidMixture,
    b: LiquidMixture,
) -> LiquidMixture:
    """
    Blend two liquid mixtures conserving total volume, weighted colour,
    and thermal equilibrium. No reaction chemistry applied yet.
    """
    total_volume = a.volume_ml + b.volume_ml
    if total_volume == 0:
        return a.clone()

    # Weighted colour interpolation
    w_a = a.volume_ml / total_volume
    w_b = b.volume_ml / total_volume
    mixed_rgb = tuple(round(w_a * a.color_rgb[i] + w_b * b.color_rgb[i], 4) for i in range(3))

    # Weighted temperature equilibrium (Newton's law of cooling analogue)
    mixed_t = round(
        (a.volume_ml * a.temperature_c + b.volume_ml * b.temperature_c) / total_volume,
        4,
    )

    # Merged reagent inventory
    merged: dict[str, float] = dict(a.reagent_moles)
    for reagent, moles in b.reagent_moles.items():
        merged[reagent] = merged.get(reagent, 0.0) + moles

    # Weighted turbidity & bubble rate
    mixed_turbidity = round(w_a * a.turbidity + w_b * b.turbidity, 4)
    mixed_bubble_rate = round(w_a * a.bubble_rate + w_b * b.bubble_rate, 4)
    mixed_foam = round(w_a * a.foam_volume_ml + w_b * b.foam_volume_ml, 4)

    return LiquidMixture(
        volume_ml=total_volume,
        temperature_c=mixed_t,
        reagent_moles=merged,
        color_rgb=mixed_rgb,
        turbidity=mixed_turbidity,
        bubble_rate=mixed_bubble_rate,
        foam_volume_ml=mixed_foam,
    )


# ── Core simulation primitive: one simulation step ───────────────────────


def step_simulation(
    mixture: LiquidMixture,
    dt_s: float,
) -> tuple[LiquidMixture, ReactionType]:
    """
    Advance the simulation by dt seconds.
    Returns (new_mixture, identified_reaction_type).
    """
    if dt_s <= 0:
        return mixture.clone(), ReactionType.NONE

    # Deep copy for immutable output
    result = mixture.clone()

    # 1) Thermal relaxation toward ambient
    ambient = 22.0  # °C typical room temp
    cooling_rate = 1.0 / 30.0  # time constant 30 s
    result.temperature_c = round(
        result.temperature_c + (ambient - result.temperature_c) / cooling_rate * dt_s,
        4,
    )

    # 2) Reaction classification & engine invocation
    identified = ReactionType.NONE

    # ── Acid–base neutralization ─────────────────────────────────────
    hcl_present = "hcl" in result.reagent_moles
    naoh_present = "naoh" in result.reagent_moles
    if hcl_present and naoh_present:
        hcl_moles = result.reagent_moles.pop("hcl")
        naoh_moles = result.reagent_moles.pop("naoh")
        # Equimolar => NaCl (neutral) + heat
        result.reagent_moles["nacl"] = result.reagent_moles.get("nacl", 0.0) + min(
            hcl_moles, naoh_moles
        )
        result.temperature_c = round(result.temperature_c + 5.0, 4)  # exothermic
        if "universal_indicator" in result.reagent_moles:
            result.color_rgb = (0.15, 0.82, 0.25)  # Shifts to neutral green
        identified = ReactionType.ACID_BASE_NEUTRALIZATION

    # ── Catalytic foam eruption (H2O2 + KI) ───────────────────────────
    h2o2_present = "hydrogen_peroxide" in result.reagent_moles
    ki_present = "potassium_iodide" in result.reagent_moles
    if h2o2_present and ki_present and identified is ReactionType.NONE:
        h2o2_moles = result.reagent_moles.get("hydrogen_peroxide", 0.0)
        catalyst_mult = CATALYST_MULTIPLIER.get("potassium_iodide", 1.0)
        decomposition = h2o2_moles * 0.8 * dt_s * catalyst_mult  # fraction decomposed
        # Produce vigorous gas bubbles + expanding foam
        result.bubble_rate = min(1.0, result.bubble_rate + 0.85)
        result.foam_volume_ml = min(500.0, result.foam_volume_ml + decomposition * 1000.0)
        result.temperature_c = round(result.temperature_c + 8.0, 4)  # strong exothermic
        # Consume peroxide
        result.reagent_moles["hydrogen_peroxide"] = max(0.0, h2o2_moles - decomposition)
        identified = ReactionType.CATALYTIC_FOAM_ERUPTION

    # ── Briggs–Rauscher oscillating iodine clock ──────────────────────
    # 3-phase colour cycle: Clear(0) ➔ Amber(1) ➔ DeepBlue(2) ➔ Clear(0)
    if (
        "malonic_acid" in result.reagent_moles
        and "potassium_iodate" in result.reagent_moles
        and "manganese_sulfate" in result.reagent_moles
    ):
        # Consume malonic acid slowly; shift phase every few seconds
        ma_moles = result.reagent_moles.get("malonic_acid", 0.0)
        if ma_moles > 0.001:
            # Oscillator driver
            osc_delta = OBSCILLATOR_KW * dt_s * (1.0 / max(ma_moles, 0.001))
            phase_shift = int(np.floor(result.oscillation_timer_s + osc_delta)) - int(
                np.floor(result.oscillation_timer_s)
            )
            if phase_shift > 0:
                # Cycle phases 0→1→2→0
                result.oscillation_phase = (result.oscillation_phase + phase_shift) % 3
                result.oscillation_timer_s = 0.0
            else:
                result.oscillation_timer_s += osc_delta

            # Map phase → colour
            phase_to_rgb: dict[int, tuple[float, float, float]] = {
                0: (0.95, 0.98, 1.0),  # Clear
                1: (0.96, 0.72, 0.24),  # Amber
                2: (0.14, 0.22, 0.64),  # Deep midnight blue
            }
            result.color_rgb = phase_to_rgb[result.oscillation_phase]
        else:
            # Reaction exhausted – lock in last observed phase
            pass

    # ── Electronegativity / precipitation heuristic ───────────────────
    # (lead nitrate + potassium iodide → yellow PbI2 precipitate)
    if "lead_nitrate" in result.reagent_moles and "potassium_iodide" in result.reagent_moles:
        pi_moles = min(
            result.reagent_moles.get("lead_nitrate", 0.0),
            result.reagent_moles.get("potassium_iodide", 0.0),
        )
        if pi_moles > 0.001:
            result.turbidity = min(1.0, result.turbidity + 0.1 * dt_s)
            result.reagent_moles["lead_nitrate"] = max(
                0.0, result.reagent_moles.get("lead_nitrate", 0.0) - 0.01 * dt_s
            )
            result.reagent_moles["potassium_iodide"] = max(
                0.0, result.reagent_moles.get("potassium_iodide", 0.0) - 0.01 * dt_s
            )
            identified = ReactionType.PRECIPITATION_FALL

    # ── Chemiluminescence (luminol + H2O2 under basic conditions) ────
    if (
        "luminol" in result.reagent_moles
        and "hydrogen_peroxide" in result.reagent_moles
        and result.ph > 10.0
    ):
        result.emission_glow = min(1.0, result.emission_glow + 0.05 * dt_s)
        identified = ReactionType.CHEMILUMINESCENT_GLOW

    # If nothing else triggered, classify retroactively
    if identified is ReactionType.NONE:
        identified = _classify_reaction_type(result, list(result.reagent_moles))

    return result, identified
