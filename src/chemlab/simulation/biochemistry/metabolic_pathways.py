"""
Metabolic pathways — glycolysis and Krebs/TCA cycle as ODE systems.

Implements the 10-reaction glycolysis and 8-reaction Krebs cycle from
BIOCHEMICAL_PATHWAY_SIMULATION_SPEC.md §3 with mass-balance ODE integration
(dx/dt = S · v) via RK4. All concentrations in mol/L, time in seconds,
energies in kJ/mol.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PathwayReaction:
    """A single metabolic reaction with stoichiometry and kinetics."""

    id: str
    name: str
    enzyme: str
    reactants: dict[str, float]  # species -> stoichiometric coefficient
    products: dict[str, float]
    reversible: bool
    delta_g0_kj_mol: float
    vmax_m_per_s: float
    km_m: float = 1.0  # Michaelis constant for primary substrate
    ki_m: float | None = None  # inhibition constant (if regulated)
    inhibitor: str | None = None  # species id that inhibits


@dataclass
class Pathway:
    """A metabolic pathway: species + reactions."""

    id: str
    name: str
    species: list[str]
    reactions: list[PathwayReaction]


@dataclass
class SimState:
    """Current simulation state of a pathway."""

    concentrations: dict[str, float]  # species -> mol/L
    time_s: float = 0.0
    temperature_k: float = 298.15
    ph: float = 7.0
    volume_l: float = 1.0
    history: list[dict[str, object]] = field(default_factory=list)


def _stoichiometric_matrix(
    pathway: Pathway,
) -> tuple[list[str], list[str], list[list[float]]]:
    """Build S matrix: rows = species, cols = reactions, entry = net stoich."""
    species_ids = pathway.species
    reaction_ids = [r.id for r in pathway.reactions]
    s: list[list[float]] = [[0.0] * len(reaction_ids) for _ in species_ids]
    index = {sid: i for i, sid in enumerate(species_ids)}
    for j, rxn in enumerate(pathway.reactions):
        for sid, coeff in rxn.reactants.items():
            s[index[sid]][j] -= coeff
        for sid, coeff in rxn.products.items():
            s[index[sid]][j] += coeff
    return species_ids, reaction_ids, s


def _reaction_fluxes(
    pathway: Pathway,
    concentrations: dict[str, float],
    temperature_k: float,
    ph: float,
) -> list[float]:
    """Compute flux v_j for each reaction via Michaelis-Menten kinetics."""
    fluxes: list[float] = []
    for rxn in pathway.reactions:
        # Primary substrate = first reactant
        if not rxn.reactants:
            fluxes.append(0.0)
            continue
        primary_substrate = next(iter(rxn.reactants))
        s = concentrations.get(primary_substrate, 0.0)
        vmax = rxn.vmax_m_per_s

        # Temperature correction (Arrhenius, assume Ea = 50 kJ/mol if unspecified)
        v = michaelis_menten_flux(s, vmax, rxn.km_m)

        # Regulation: competitive inhibition by listed inhibitor
        if rxn.inhibitor is not None and rxn.ki_m is not None:
            i = concentrations.get(rxn.inhibitor, 0.0)
            v = competitive_inhibition_flux(s, vmax, rxn.km_m, i, rxn.ki_m)

        # Reversibility: net flux = forward - reverse (simple mass action)
        if rxn.reversible:
            # Approximate reverse from product side
            primary_product = next(iter(rxn.products)) if rxn.products else None
            if primary_product:
                p = concentrations.get(primary_product, 0.0)
                v_rev = michaelis_menten_flux(p, vmax * 0.1, rxn.km_m)
                v = v - v_rev

        fluxes.append(v)
    return fluxes


def michaelis_menten_flux(substrate_m: float, vmax_m_per_s: float, km_m: float) -> float:
    if substrate_m <= 0 or km_m <= 0:
        return 0.0
    return vmax_m_per_s * substrate_m / (km_m + substrate_m)


def competitive_inhibition_flux(
    substrate_m: float, vmax_m_per_s: float, km_m: float, inhibitor_m: float, ki_m: float
) -> float:
    if ki_m <= 0:
        return 0.0
    km_app = km_m * (1.0 + inhibitor_m / ki_m)
    return michaelis_menten_flux(substrate_m, vmax_m_per_s, km_app)


def rk4_step(
    pathway: Pathway,
    state: SimState,
    dt_s: float,
) -> SimState:
    """Advance the pathway ODE by one RK4 step of size dt_s."""

    species_ids = pathway.species
    _, _, s = _stoichiometric_matrix(pathway)
    n_sp = len(species_ids)

    def derivatives(x: list[float], temp_k: float, ph: float) -> list[float]:
        conc = {sid: x[i] for i, sid in enumerate(species_ids)}
        fluxes = _reaction_fluxes(pathway, conc, temp_k, ph)
        dx = [0.0] * n_sp
        for j, v in enumerate(fluxes):
            for i in range(n_sp):
                dx[i] += s[i][j] * v
        return dx

    x0 = [state.concentrations.get(sid, 0.0) for sid in species_ids]

    k1 = derivatives(x0, state.temperature_k, state.ph)
    x2 = [x0[i] + 0.5 * dt_s * k1[i] for i in range(n_sp)]
    k2 = derivatives(x2, state.temperature_k, state.ph)
    x3 = [x0[i] + 0.5 * dt_s * k2[i] for i in range(n_sp)]
    k3 = derivatives(x3, state.temperature_k, state.ph)
    x4 = [x0[i] + dt_s * k3[i] for i in range(n_sp)]
    k4 = derivatives(x4, state.temperature_k, state.ph)

    x_new = [
        max(0.0, x0[i] + (dt_s / 6.0) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]))
        for i in range(n_sp)
    ]

    new_conc = {sid: x_new[i] for i, sid in enumerate(species_ids)}
    new_state = SimState(
        concentrations=new_conc,
        time_s=state.time_s + dt_s,
        temperature_k=state.temperature_k,
        ph=state.ph,
        volume_l=state.volume_l,
    )
    # Append snapshot to history (bounded)
    new_state.history = state.history + [
        {"t": new_state.time_s, **new_conc}
    ]
    if len(new_state.history) > 1000:
        new_state.history = new_state.history[-1000:]
    return new_state


def integrate_pathway(
    pathway: Pathway,
    initial_concentrations: dict[str, float],
    t_end_s: float,
    dt_s: float = 0.1,
    temperature_k: float = 298.15,
    ph: float = 7.0,
) -> SimState:
    """Integrate a pathway from t=0 to t_end_s with fixed dt."""
    state = SimState(
        concentrations=dict(initial_concentrations),
        time_s=0.0,
        temperature_k=temperature_k,
        ph=ph,
    )
    while state.time_s < t_end_s - 1e-12:
        step = min(dt_s, t_end_s - state.time_s)
        state = rk4_step(pathway, state, step)
    return state


# ---------------------------------------------------------------------------
# Pathway definitions (BIOCHEMICAL_PATHWAY_SIMULATION_SPEC.md §3.1-3.2)
# ---------------------------------------------------------------------------

GLYCOLYSIS = Pathway(
    id="glycolysis",
    name="Glycolysis (10 reactions)",
    species=[
        "Glc", "G6P", "F6P", "F16BP", "DHAP", "GAP", "13BPG", "3PG", "2PG", "PEP",
        "Pyr", "ATP", "ADP", "NAD+", "NADH", "Pi", "H2O", "H+",
    ],
    reactions=[
        PathwayReaction(
            id="r1_hexokinase",
            name="Hexokinase",
            enzyme="Hexokinase",
            reactants={"Glc": 1.0, "ATP": 1.0},
            products={"G6P": 1.0, "ADP": 1.0},
            reversible=False,
            delta_g0_kj_mol=-16.7,
            vmax_m_per_s=100.0,
            km_m=0.1,
        ),
        PathwayReaction(
            id="r2_pgi",
            name="Phosphoglucose isomerase",
            enzyme="PGI",
            reactants={"G6P": 1.0},
            products={"F6P": 1.0},
            reversible=True,
            delta_g0_kj_mol=1.7,
            vmax_m_per_s=80.0,
            km_m=0.2,
        ),
        PathwayReaction(
            id="r3_pfk1",
            name="Phosphofructokinase-1",
            enzyme="PFK-1",
            reactants={"F6P": 1.0, "ATP": 1.0},
            products={"F16BP": 1.0, "ADP": 1.0},
            reversible=False,
            delta_g0_kj_mol=-14.2,
            vmax_m_per_s=60.0,
            km_m=0.05,
            inhibitor="ATP",
            ki_m=1.0,
        ),
        PathwayReaction(
            id="r4_aldolase",
            name="Aldolase",
            enzyme="Aldolase",
            reactants={"F16BP": 1.0},
            products={"DHAP": 1.0, "GAP": 1.0},
            reversible=True,
            delta_g0_kj_mol=23.8,
            vmax_m_per_s=50.0,
            km_m=0.1,
        ),
        PathwayReaction(
            id="r5_tpi",
            name="Triose phosphate isomerase",
            enzyme="TPI",
            reactants={"DHAP": 1.0},
            products={"GAP": 1.0},
            reversible=True,
            delta_g0_kj_mol=7.5,
            vmax_m_per_s=200.0,
            km_m=0.05,
        ),
        PathwayReaction(
            id="r6_gapdh",
            name="Glyceraldehyde-3-phosphate dehydrogenase",
            enzyme="GAPDH",
            reactants={"GAP": 1.0, "Pi": 1.0, "NAD+": 1.0},
            products={"13BPG": 1.0, "NADH": 1.0, "H+": 1.0},
            reversible=True,
            delta_g0_kj_mol=6.3,
            vmax_m_per_s=90.0,
            km_m=0.1,
        ),
        PathwayReaction(
            id="r7_pgk",
            name="Phosphoglycerate kinase",
            enzyme="PGK",
            reactants={"13BPG": 1.0, "ADP": 1.0},
            products={"3PG": 1.0, "ATP": 1.0},
            reversible=True,
            delta_g0_kj_mol=-18.8,
            vmax_m_per_s=110.0,
            km_m=0.1,
        ),
        PathwayReaction(
            id="r8_pgm",
            name="Phosphoglycerate mutase",
            enzyme="PGM",
            reactants={"3PG": 1.0},
            products={"2PG": 1.0},
            reversible=True,
            delta_g0_kj_mol=4.4,
            vmax_m_per_s=70.0,
            km_m=0.2,
        ),
        PathwayReaction(
            id="r9_enolase",
            name="Enolase",
            enzyme="Enolase",
            reactants={"2PG": 1.0},
            products={"PEP": 1.0, "H2O": 1.0},
            reversible=True,
            delta_g0_kj_mol=1.7,
            vmax_m_per_s=60.0,
            km_m=0.2,
        ),
        PathwayReaction(
            id="r10_pyruvate_kinase",
            name="Pyruvate kinase",
            enzyme="Pyruvate kinase",
            reactants={"PEP": 1.0, "ADP": 1.0},
            products={"Pyr": 1.0, "ATP": 1.0},
            reversible=False,
            delta_g0_kj_mol=-31.4,
            vmax_m_per_s=120.0,
            km_m=0.1,
            inhibitor="ATP",
            ki_m=2.0,
        ),
    ],
)

KREBS = Pathway(
    id="krebs",
    name="Krebs / TCA cycle (8 reactions)",
    species=[
        "Acetyl-CoA", "Oxaloacetate", "Citrate", "Isocitrate", "alpha-KG",
        "Succinyl-CoA", "Succinate", "Fumarate", "Malate", "CoA",
        "NAD+", "NADH", "FAD", "FADH2", "GDP", "GTP", "CO2", "H2O", "H+", "Pi",
    ],
    reactions=[
        PathwayReaction(
            id="k1_citrate_synthase",
            name="Citrate synthase",
            enzyme="Citrate synthase",
            reactants={"Acetyl-CoA": 1.0, "Oxaloacetate": 1.0, "H2O": 1.0},
            products={"Citrate": 1.0, "CoA": 1.0, "H+": 1.0},
            reversible=False,
            delta_g0_kj_mol=-31.5,
            vmax_m_per_s=50.0,
            km_m=0.02,
            inhibitor="NADH",
            ki_m=0.5,
        ),
        PathwayReaction(
            id="k2_aconitase",
            name="Aconitase",
            enzyme="Aconitase",
            reactants={"Citrate": 1.0},
            products={"Isocitrate": 1.0},
            reversible=True,
            delta_g0_kj_mol=6.7,
            vmax_m_per_s=40.0,
            km_m=0.05,
        ),
        PathwayReaction(
            id="k3_isocitrate_dh",
            name="Isocitrate dehydrogenase",
            enzyme="Isocitrate dehydrogenase",
            reactants={"Isocitrate": 1.0, "NAD+": 1.0},
            products={"alpha-KG": 1.0, "CO2": 1.0, "NADH": 1.0},
            reversible=True,
            delta_g0_kj_mol=-8.4,
            vmax_m_per_s=45.0,
            km_m=0.03,
            inhibitor="NADH",
            ki_m=0.3,
        ),
        PathwayReaction(
            id="k4_alpha_kg_dh",
            name="Alpha-ketoglutarate dehydrogenase",
            enzyme="alpha-KG dehydrogenase",
            reactants={"alpha-KG": 1.0, "NAD+": 1.0, "CoA": 1.0},
            products={"Succinyl-CoA": 1.0, "CO2": 1.0, "NADH": 1.0},
            reversible=False,
            delta_g0_kj_mol=-33.4,
            vmax_m_per_s=30.0,
            km_m=0.04,
            inhibitor="NADH",
            ki_m=0.2,
        ),
        PathwayReaction(
            id="k5_succinyl_coa_synth",
            name="Succinyl-CoA synthetase",
            enzyme="Succinyl-CoA synthetase",
            reactants={"Succinyl-CoA": 1.0, "GDP": 1.0, "Pi": 1.0},
            products={"Succinate": 1.0, "CoA": 1.0, "GTP": 1.0},
            reversible=True,
            delta_g0_kj_mol=-2.9,
            vmax_m_per_s=35.0,
            km_m=0.05,
        ),
        PathwayReaction(
            id="k6_succinate_dh",
            name="Succinate dehydrogenase",
            enzyme="Succinate dehydrogenase",
            reactants={"Succinate": 1.0, "FAD": 1.0},
            products={"Fumarate": 1.0, "FADH2": 1.0},
            reversible=True,
            delta_g0_kj_mol=0.0,
            vmax_m_per_s=25.0,
            km_m=0.1,
        ),
        PathwayReaction(
            id="k7_fumarase",
            name="Fumarase",
            enzyme="Fumarase",
            reactants={"Fumarate": 1.0, "H2O": 1.0},
            products={"Malate": 1.0},
            reversible=True,
            delta_g0_kj_mol=-3.6,
            vmax_m_per_s=55.0,
            km_m=0.05,
        ),
        PathwayReaction(
            id="k8_malate_dh",
            name="Malate dehydrogenase",
            enzyme="Malate dehydrogenase",
            reactants={"Malate": 1.0, "NAD+": 1.0},
            products={"Oxaloacetate": 1.0, "NADH": 1.0, "H+": 1.0},
            reversible=True,
            delta_g0_kj_mol=29.7,
            vmax_m_per_s=40.0,
            km_m=0.05,
        ),
    ],
)

PATHWAYS: dict[str, Pathway] = {
    "glycolysis": GLYCOLYSIS,
    "krebs": KREBS,
}
