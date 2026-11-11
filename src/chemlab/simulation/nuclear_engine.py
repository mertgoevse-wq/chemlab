"""
ChemLab Nuclear Physics and Radiochemistry Engine.

Validates decay chains, half-life calculations, activity, shielding, criticality,
isotope production, fission yields, reactor simulation, and reprocessing.
"""

import math
import random
from dataclasses import dataclass
from enum import Enum


class DecayMode(Enum):
    """Radioactive decay modes."""

    ALPHA = "alpha"
    BETA_MINUS = "beta-"
    BETA_PLUS = "beta+"
    ELECTRON_CAPTURE = "ec"
    GAMMA = "gamma"
    INTERNAL_TRANSITION = "it"
    NEUTRON = "neutron"
    PROTON = "proton"
    SPONTANEOUS_FISSION = "sf"
    DOUBLE_BETA = "2beta"


class ReactorType(Enum):
    """Nuclear reactor types."""

    PWR = "pwr"  # Pressurized Water Reactor
    BWR = "bwr"  # Boiling Water Reactor
    PHWR = "phwr"  # Pressurized Heavy Water Reactor (CANDU)
    RBMK = "rbmk"  # RBMK (Chernobyl type)
    VVER = "vver"  # Russian PWR
    FBR = "fbr"  # Fast Breeder Reactor
    HTGR = "htgr"  # High-Temperature Gas-Cooled Reactor
    MSR = "msr"  # Molten Salt Reactor
    SMR = "smr"  # Small Modular Reactor


@dataclass
class Isotope:
    """Complete isotope data."""

    z: int  # Atomic number
    a: int  # Mass number
    symbol: str  # Element symbol
    name: str  # Full name
    half_life_seconds: float  # Half-life in seconds
    decay_modes: dict[DecayMode, float]  # mode -> branching ratio
    decay_energies: dict[DecayMode, float]  # mode -> MeV
    daughter_z: int | None = None
    daughter_a: int | None = None
    daughter_symbol: str | None = None
    is_stable: bool = False
    is_fissile: bool = False
    is_fertile: bool = False
    natural_abundance: float = 0.0
    atomic_mass: float = 0.0
    binding_energy_per_nucleon: float = 0.0
    neutron_cross_section_barns: float = 0.0
    fission_cross_section_barns: float = 0.0
    fission_yield: float = 0.0


@dataclass
class DecayChain:
    """Radioactive decay chain."""

    parent: Isotope
    chain: list[Isotope]
    total_half_life: float
    equilibrium_type: str  # "secular", "transient", "no_equilibrium"


@dataclass
class ShieldingMaterial:
    """Radiation shielding material."""

    name: str
    density_g_cm3: float
    alpha_stopping_power: float  # MeV·cm²/g
    beta_stopping_power: float
    gamma_mu_cm2_g: float  # Mass attenuation coefficient cm²/g
    neutron_macro_xs: float  # Macroscopic cross section cm⁻¹
    thickness_cm: float = 1.0
    cost_per_kg: float = 1.0


@dataclass
class ReactorState:
    """Nuclear reactor operational state."""

    reactor_type: ReactorType
    thermal_power_mw: float
    electrical_power_mw: float
    capacity_factor: float
    burnup_gwd_mtU: float
    fuel_enrichment_percent: float
    core_life_days: int
    xenon_135_ppm: float
    samarium_149_ppm: float
    boron_ppm: float
    control_rod_position_percent: float
    coolant_temp_in_c: float
    coolant_temp_out_c: float
    pressure_mpa: float


@dataclass
class FuelAssembly:
    """Nuclear fuel assembly."""

    assembly_id: str
    fuel_type: str  # UO2, MOX, ThO2, etc.
    enrichment_percent: float
    mass_kg: float
    burnup_gwd_mtU: float
    initial_u235_kg: float
    current_u235_kg: float
    pu239_kg: float
    pu240_kg: float
    pu241_kg: float
    fission_products_kg: float
    minor_actinides_kg: float


@dataclass
class ReprocessingStream:
    """Nuclear fuel reprocessing stream."""

    stream_name: str
    mass_kg: float
    u235_kg: float
    u238_kg: float
    pu239_kg: float
    pu240_kg: float
    pu241_kg: float
    fp_kg: float  # Fission products
    ma_kg: float  # Minor actinides
    waste_class: str  # HLW, ILW, LLW


# ============================================================================
# Nuclear Data - Complete Isotope Catalog
# ============================================================================

# Natural decay chains
URANIUM_238_CHAIN = [
    (92, 238),
    (90, 234),
    (91, 234),
    (92, 234),
    (90, 230),
    (88, 226),
    (86, 222),
    (84, 218),
    (82, 214),
    (83, 214),
    (84, 214),
    (82, 210),
    (83, 210),
    (84, 210),
    (82, 206),
]

URANIUM_235_CHAIN = [
    (92, 235),
    (90, 231),
    (91, 231),
    (89, 227),
    (90, 227),
    (88, 223),
    (86, 219),
    (84, 215),
    (82, 211),
    (83, 211),
    (84, 211),
    (81, 207),
    (82, 207),
]

THORIUM_232_CHAIN = [
    (90, 232),
    (88, 228),
    (89, 228),
    (90, 228),
    (88, 224),
    (86, 220),
    (84, 216),
    (82, 212),
    (83, 212),
    (84, 212),
    (81, 208),
    (82, 208),
]

NEPTUNIUM_237_CHAIN = [
    (93, 237),
    (91, 233),
    (92, 233),
    (90, 229),
    (88, 225),
    (89, 225),
    (86, 221),
    (84, 217),
    (82, 213),
    (83, 213),
    (81, 209),
    (82, 209),
]

# Element symbols
ELEMENT_SYMBOLS = {
    1: "H",
    2: "He",
    3: "Li",
    4: "Be",
    5: "B",
    6: "C",
    7: "N",
    8: "O",
    9: "F",
    10: "Ne",
    11: "Na",
    12: "Mg",
    13: "Al",
    14: "Si",
    15: "P",
    16: "S",
    17: "Cl",
    18: "Ar",
    19: "K",
    20: "Ca",
    21: "Sc",
    22: "Ti",
    23: "V",
    24: "Cr",
    25: "Mn",
    26: "Fe",
    27: "Co",
    28: "Ni",
    29: "Cu",
    30: "Zn",
    31: "Ga",
    32: "Ge",
    33: "As",
    34: "Se",
    35: "Br",
    36: "Kr",
    37: "Rb",
    38: "Sr",
    39: "Y",
    40: "Zr",
    41: "Nb",
    42: "Mo",
    43: "Tc",
    44: "Ru",
    45: "Rh",
    46: "Pd",
    47: "Ag",
    48: "Cd",
    49: "In",
    50: "Sn",
    51: "Sb",
    52: "Te",
    53: "I",
    54: "Xe",
    55: "Cs",
    56: "Ba",
    57: "La",
    58: "Ce",
    59: "Pr",
    60: "Nd",
    61: "Pm",
    62: "Sm",
    63: "Eu",
    64: "Gd",
    65: "Tb",
    66: "Dy",
    67: "Ho",
    68: "Er",
    69: "Tm",
    70: "Yb",
    71: "Lu",
    72: "Hf",
    73: "Ta",
    74: "W",
    75: "Re",
    76: "Os",
    77: "Ir",
    78: "Pt",
    79: "Au",
    80: "Hg",
    81: "Tl",
    82: "Pb",
    83: "Bi",
    84: "Po",
    85: "At",
    86: "Rn",
    87: "Fr",
    88: "Ra",
    89: "Ac",
    90: "Th",
    91: "Pa",
    92: "U",
    93: "Np",
    94: "Pu",
    95: "Am",
    96: "Cm",
    97: "Bk",
    98: "Cf",
    99: "Es",
    100: "Fm",
    101: "Md",
    102: "No",
    103: "Lr",
    104: "Rf",
    105: "Db",
    106: "Sg",
    107: "Bh",
    108: "Hs",
    109: "Mt",
    110: "Ds",
    111: "Rg",
    112: "Cn",
    113: "Nh",
    114: "Fl",
    115: "Mc",
    116: "Lv",
    117: "Ts",
    118: "Og",
}

ELEMENT_NAMES = {
    1: "Hydrogen",
    2: "Helium",
    3: "Lithium",
    4: "Beryllium",
    5: "Boron",
    6: "Carbon",
    7: "Nitrogen",
    8: "Oxygen",
    9: "Fluorine",
    10: "Neon",
    11: "Sodium",
    12: "Magnesium",
    13: "Aluminum",
    14: "Silicon",
    15: "Phosphorus",
    16: "Sulfur",
    17: "Chlorine",
    18: "Argon",
    19: "Potassium",
    20: "Calcium",
    21: "Scandium",
    22: "Titanium",
    23: "Vanadium",
    24: "Chromium",
    25: "Manganese",
    26: "Iron",
    27: "Cobalt",
    28: "Nickel",
    29: "Copper",
    30: "Zinc",
    31: "Gallium",
    32: "Germanium",
    33: "Arsenic",
    34: "Selenium",
    35: "Bromine",
    36: "Krypton",
    37: "Rubidium",
    38: "Strontium",
    39: "Yttrium",
    40: "Zirconium",
    41: "Niobium",
    42: "Molybdenum",
    43: "Technetium",
    44: "Ruthenium",
    45: "Rhodium",
    46: "Palladium",
    47: "Silver",
    48: "Cadmium",
    49: "Indium",
    50: "Tin",
    51: "Antimony",
    52: "Tellurium",
    53: "Iodine",
    54: "Xenon",
    55: "Cesium",
    56: "Barium",
    57: "Lanthanum",
    58: "Cerium",
    59: "Praseodymium",
    60: "Neodymium",
    61: "Promethium",
    62: "Samarium",
    63: "Europium",
    64: "Gadolinium",
    65: "Terbium",
    66: "Dysprosium",
    67: "Holmium",
    68: "Erbium",
    69: "Thulium",
    70: "Ytterbium",
    71: "Lutetium",
    72: "Hafnium",
    73: "Tantalum",
    74: "Tungsten",
    75: "Rhenium",
    76: "Osmium",
    77: "Iridium",
    78: "Platinum",
    79: "Gold",
    80: "Mercury",
    81: "Thallium",
    82: "Lead",
    83: "Bismuth",
    84: "Polonium",
    85: "Astatine",
    86: "Radon",
    87: "Francium",
    88: "Radium",
    89: "Actinium",
    90: "Thorium",
    91: "Protactinium",
    92: "Uranium",
    93: "Neptunium",
    94: "Plutonium",
    95: "Americium",
    96: "Curium",
    97: "Berkelium",
    98: "Californium",
    99: "Einsteinium",
    100: "Fermium",
    101: "Mendelevium",
    102: "Nobelium",
    103: "Lawrencium",
    104: "Rutherfordium",
    105: "Dubnium",
    106: "Seaborgium",
    107: "Bohrium",
    108: "Hassium",
    109: "Meitnerium",
    110: "Darmstadtium",
    111: "Roentgenium",
    112: "Copernicium",
    113: "Nihonium",
    114: "Flerovium",
    115: "Moscovium",
    116: "Livermorium",
    117: "Tennessine",
    118: "Oganesson",
}


def _create_isotope(
    z: int,
    a: int,
    half_life_s: float,
    decay_modes: dict,
    decay_energies: dict,
    is_stable: bool = False,
    is_fissile: bool = False,
    is_fertile: bool = False,
    natural_abundance: float = 0.0,
    atomic_mass: float = 0.0,
    binding_energy: float = 0.0,
    n_xs: float = 0.0,
    f_xs: float = 0.0,
    f_yield: float = 0.0,
) -> Isotope:
    """Helper to create isotope with all properties."""
    symbol = ELEMENT_SYMBOLS.get(z, "X")
    name = f"{ELEMENT_NAMES.get(z, 'Unknown')}-{a}"

    # Calculate binding energy if not provided
    if binding_energy == 0.0:
        # Semi-empirical mass formula approximation
        if a > 0:
            binding_energy = (
                15.75
                - 17.8 * a ** (-1 / 3)
                - 0.711 * z**2 * a ** (-4 / 3)
                - 23.7 * (a - 2 * z) ** 2 / a**2
            )

    return Isotope(
        z=z,
        a=a,
        symbol=symbol,
        name=name,
        half_life_seconds=half_life_s,
        decay_modes=decay_modes,
        decay_energies=decay_energies,
        is_stable=is_stable,
        is_fissile=is_fissile,
        is_fertile=is_fertile,
        natural_abundance=natural_abundance,
        atomic_mass=atomic_mass if atomic_mass > 0 else a,
        binding_energy_per_nucleon=binding_energy,
        neutron_cross_section_barns=n_xs,
        fission_cross_section_barns=f_xs,
        fission_yield=f_yield,
    )


def _build_isotope_catalog() -> dict[tuple[int, int], Isotope]:
    """Build complete isotope catalog with 200+ isotopes."""
    isotopes = {}

    # Stable isotopes (light elements)
    stable_data = [
        (1, 1, 99.985, 1.007825, 7.29),  # H-1
        (1, 2, 0.015, 2.014102, 2.22),  # H-2 (D)
        (2, 3, 0.0001, 3.016029, 2.57),  # He-3
        (2, 4, 99.999, 4.002603, 7.07),  # He-4
        (3, 6, 7.59, 6.015123, 5.33),  # Li-6
        (3, 7, 92.41, 7.016003, 5.61),  # Li-7
        (4, 9, 100, 9.012183, 6.46),  # Be-9
        (5, 10, 19.9, 10.012937, 6.48),  # B-10
        (5, 11, 80.1, 11.009305, 6.93),  # B-11
        (6, 12, 98.93, 12.0, 7.68),  # C-12
        (6, 13, 1.07, 13.003355, 7.47),  # C-13
        (7, 14, 99.63, 14.003074, 7.52),  # N-14
        (7, 15, 0.37, 15.000109, 7.70),  # N-15
        (8, 16, 99.76, 15.994915, 7.98),  # O-16
        (8, 17, 0.04, 16.999132, 7.75),  # O-17
        (8, 18, 0.20, 17.999160, 7.98),  # O-18
    ]

    for z, a, abund, mass, be in stable_data:
        isotopes[(z, a)] = _create_isotope(
            z,
            a,
            float("inf"),
            {},
            {},
            is_stable=True,
            natural_abundance=abund,
            atomic_mass=mass,
            binding_energy=be,
        )

    # Major radioactive isotopes
    # Tuple format: (z, a, hl, modes, energies, fissile, fertile, abund, mass, be, nxs, fxs, fy, is_stable)
    radioactive_data = [
        # Uranium series
        (
            92,
            238,
            4.468e9 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.267},
            False,
            True,
            99.27,
            238.050788,
            7.57,
            2.7,
            0.0,
            0.0,
            False,
        ),
        (
            92,
            235,
            7.04e8 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.679},
            True,
            False,
            0.72,
            235.043930,
            7.59,
            98.7,
            585.0,
            0.0,
            False,
        ),
        (
            92,
            234,
            2.455e5 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.857},
            False,
            False,
            0.0055,
            234.040952,
            7.60,
            100.0,
            0.0,
            0.0,
            False,
        ),
        # U-236
        (
            92,
            236,
            2.342e7 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.572},
            False,
            False,
            0.0,
            236.045568,
            7.58,
            5.0,
            0.0,
            0.0,
            False,
        ),
        # Thorium series
        (
            90,
            232,
            1.405e10 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.081},
            False,
            True,
            100.0,
            232.038055,
            7.61,
            7.4,
            0.0,
            0.0,
            False,
        ),
        (
            90,
            230,
            7.54e4 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.770},
            False,
            False,
            0.0,
            230.033134,
            7.60,
            0.0,
            0.0,
            0.0,
            False,
        ),
        # Plutonium isotopes
        (
            94,
            238,
            87.7 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.593},
            False,
            False,
            0.0,
            238.049560,
            7.56,
            560.0,
            18.0,
            0.0,
            False,
        ),
        (
            94,
            239,
            2.411e4 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.244},
            True,
            False,
            0.0,
            239.052157,
            7.56,
            270.0,
            750.0,
            0.0,
            False,
        ),
        (
            94,
            240,
            6561 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.256},
            False,
            True,
            0.0,
            240.053814,
            7.56,
            290.0,
            0.0,
            0.0,
            False,
        ),
        (
            94,
            241,
            14.35 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.021},
            True,
            False,
            0.0,
            241.056851,
            7.56,
            360.0,
            1010.0,
            0.0,
            False,
        ),
        (
            94,
            242,
            3.733e5 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.984},
            False,
            True,
            0.0,
            242.058743,
            7.55,
            19.0,
            0.0,
            0.0,
            False,
        ),
        # Americium & Curium
        (
            95,
            241,
            432.2 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.638},
            False,
            False,
            0.0,
            241.056829,
            7.55,
            600.0,
            0.0,
            0.0,
            False,
        ),
        (
            95,
            243,
            7370 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.439},
            False,
            False,
            0.0,
            243.061381,
            7.54,
            75.0,
            0.0,
            0.0,
            False,
        ),
        (
            96,
            244,
            18.1 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.902},
            False,
            False,
            0.0,
            244.062753,
            7.53,
            15.0,
            0.0,
            0.0,
            False,
        ),
        (
            96,
            245,
            8500 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.623},
            True,
            False,
            0.0,
            245.065491,
            7.53,
            370.0,
            0.0,
            0.0,
            False,
        ),
        # Fission products
        (
            55,
            137,
            30.17 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.514},
            False,
            False,
            0.0,
            136.907089,
            8.39,
            0.0,
            0.0,
            6.2,
            False,
        ),
        (
            38,
            90,
            28.8 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.546},
            False,
            False,
            0.0,
            89.907738,
            8.72,
            0.0,
            0.0,
            5.8,
            False,
        ),
        (
            53,
            131,
            8.02 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.971},
            False,
            False,
            0.0,
            130.906125,
            8.40,
            0.0,
            0.0,
            2.9,
            False,
        ),
        (
            54,
            135,
            9.14 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.910},
            False,
            False,
            0.0,
            134.907227,
            8.40,
            2.6e6,
            0.0,
            6.5,
            False,
        ),
        (62, 149, float("inf"), {}, {}, True, False, 0.0, 148.917185, 8.22, 4.1e4, 0.0, 1.1, True),
        (
            62,
            151,
            90 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.076},
            False,
            False,
            0.0,
            150.919854,
            8.20,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            43,
            99,
            2.11e5 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.294},
            False,
            False,
            0.0,
            98.906255,
            8.74,
            0.0,
            0.0,
            6.1,
            False,
        ),
        (
            55,
            135,
            2.3 * 10**6 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.269},
            False,
            False,
            0.0,
            134.905977,
            8.39,
            0.0,
            0.0,
            6.5,
            False,
        ),
        (
            55,
            134,
            2.06 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 2.059},
            False,
            False,
            0.0,
            133.906923,
            8.39,
            140.0,
            0.0,
            0.0,
            False,
        ),
        # Activation products
        (
            27,
            60,
            5.27 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.318},
            False,
            False,
            0.0,
            59.933822,
            8.77,
            37.0,
            0.0,
            0.0,
            False,
        ),
        (
            26,
            55,
            2.73 * 365.25 * 24 * 3600,
            {DecayMode.ELECTRON_CAPTURE: 1.0},
            {DecayMode.ELECTRON_CAPTURE: 0.231},
            False,
            False,
            0.0,
            54.938293,
            8.80,
            12.0,
            0.0,
            0.0,
            False,
        ),
        (
            28,
            63,
            100.1 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.067},
            False,
            False,
            0.0,
            62.929670,
            8.79,
            4.5,
            0.0,
            0.0,
            False,
        ),
        # Medical isotopes
        (
            27,
            57,
            271.8 * 24 * 3600,
            {DecayMode.ELECTRON_CAPTURE: 1.0},
            {DecayMode.ELECTRON_CAPTURE: 0.836},
            False,
            False,
            0.0,
            56.936291,
            8.78,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            43,
            99,
            6.01 * 3600,
            {DecayMode.GAMMA: 0.88, DecayMode.BETA_MINUS: 0.12},
            {DecayMode.GAMMA: 0.1405, DecayMode.BETA_MINUS: 0.294},
            False,
            False,
            0.0,
            98.906255,
            8.74,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            53,
            123,
            13.2 * 3600,
            {DecayMode.ELECTRON_CAPTURE: 1.0},
            {DecayMode.ELECTRON_CAPTURE: 0.159},
            False,
            False,
            0.0,
            122.905589,
            8.45,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            81,
            201,
            73.1 * 3600,
            {DecayMode.ELECTRON_CAPTURE: 1.0},
            {DecayMode.ELECTRON_CAPTURE: 0.167},
            False,
            False,
            0.0,
            200.970714,
            7.87,
            0.0,
            0.0,
            0.0,
            False,
        ),
        # Natural radioisotopes
        (
            19,
            40,
            1.25e9 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 0.893, DecayMode.ELECTRON_CAPTURE: 0.107},
            {DecayMode.BETA_MINUS: 1.311, DecayMode.ELECTRON_CAPTURE: 1.505},
            False,
            False,
            0.012,
            39.963998,
            8.54,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            87,
            87,
            4.9e10 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.283},
            False,
            False,
            0.0,
            86.909184,
            7.59,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (55, 133, float("inf"), {}, {}, True, False, 100.0, 132.905452, 8.39, 29.0, 0.0, 0.0, True),
        # Neptunium-237 (for decay chain)
        (
            93,
            237,
            2.14e6 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.959},
            False,
            False,
            0.0,
            237.048173,
            7.52,
            0.0,
            0.0,
            0.0,
            False,
        ),
        # U-238 decay chain intermediates
        (
            90,
            234,
            24.1 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.273},
            False,
            False,
            0.0,
            234.043601,
            7.60,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            91,
            234,
            1.17 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.523},
            False,
            False,
            0.0,
            234.043308,
            7.60,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            92,
            234,
            2.455e5 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.857},
            False,
            False,
            0.0055,
            234.040952,
            7.60,
            100.0,
            0.0,
            0.0,
            False,
        ),
        (
            90,
            230,
            7.54e4 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.770},
            False,
            False,
            0.0,
            230.033134,
            7.60,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            88,
            226,
            1600 * 365.25 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 4.871},
            False,
            False,
            0.0,
            226.025410,
            7.66,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            86,
            222,
            3.8235 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.590},
            False,
            False,
            0.0,
            222.017578,
            7.68,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            84,
            218,
            3.1 * 60,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 6.115},
            False,
            False,
            0.0,
            218.008973,
            7.70,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            82,
            214,
            26.8 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 1.024},
            False,
            False,
            0.0,
            214.000000,
            7.72,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            83,
            214,
            19.9 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 1.540},
            False,
            False,
            0.0,
            214.000000,
            7.72,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            84,
            214,
            164.3 * 1e-6,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 7.833},
            False,
            False,
            0.0,
            214.000000,
            7.72,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            82,
            210,
            22.3 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.064},
            False,
            False,
            0.0,
            210.000000,
            7.74,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            83,
            210,
            5.012 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 1.162},
            False,
            False,
            0.0,
            210.000000,
            7.74,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            84,
            210,
            138.376 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.407},
            False,
            False,
            0.0,
            210.000000,
            7.74,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (82, 206, float("inf"), {}, {}, True, False, 0.0, 205.974465, 7.88, 0.0, 0.0, 0.0, True),
        # U-235 chain intermediates
        (
            90,
            231,
            25.5 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.305},
            False,
            False,
            0.0,
            231.036304,
            7.59,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            91,
            231,
            3.276 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.305},
            False,
            False,
            0.0,
            231.035884,
            7.59,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            89,
            227,
            21.8 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.045},
            False,
            False,
            0.0,
            227.027752,
            7.61,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            90,
            227,
            18.7 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.045},
            False,
            False,
            0.0,
            227.027752,
            7.61,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            88,
            223,
            11.4 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.979},
            False,
            False,
            0.0,
            223.019737,
            7.63,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            86,
            219,
            3.96 * 1.0,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 6.946},
            False,
            False,
            0.0,
            219.009480,
            7.65,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            84,
            215,
            1.78 * 1e-3,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 7.526},
            False,
            False,
            0.0,
            215.000000,
            7.67,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            82,
            211,
            36.1 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 1.367},
            False,
            False,
            0.0,
            211.000000,
            7.69,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            83,
            211,
            2.14 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.045},
            False,
            False,
            0.0,
            211.000000,
            7.69,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            84,
            211,
            0.52 * 1.0,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 7.595},
            False,
            False,
            0.0,
            211.000000,
            7.69,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (81, 207, float("inf"), {}, {}, True, False, 0.0, 206.975897, 7.87, 0.0, 0.0, 0.0, True),
        # Th-232 chain intermediates
        (
            88,
            228,
            5.75 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.046},
            False,
            False,
            0.0,
            228.028741,
            7.64,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            89,
            228,
            6.1 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.046},
            False,
            False,
            0.0,
            228.028741,
            7.64,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            90,
            228,
            1.91 * 365.25 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.046},
            False,
            False,
            0.0,
            228.028741,
            7.64,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            88,
            224,
            3.66 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.685},
            False,
            False,
            0.0,
            224.020212,
            7.65,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            86,
            220,
            55.6 * 1.0,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 6.405},
            False,
            False,
            0.0,
            220.011394,
            7.67,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            84,
            216,
            0.145 * 1.0,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 6.906},
            False,
            False,
            0.0,
            216.000000,
            7.69,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            82,
            212,
            10.6 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.578},
            False,
            False,
            0.0,
            212.000000,
            7.71,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            83,
            212,
            60.6 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.578},
            False,
            False,
            0.0,
            212.000000,
            7.71,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            84,
            212,
            0.299 * 1e-6,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 8.954},
            False,
            False,
            0.0,
            212.000000,
            7.71,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (81, 208, float("inf"), {}, {}, True, False, 0.0, 207.976652, 7.86, 0.0, 0.0, 0.0, True),
        # Np-237 chain intermediates
        (
            91,
            233,
            27.0 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.571},
            False,
            False,
            0.0,
            233.039742,
            7.57,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            92,
            233,
            1.59 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.005},
            False,
            False,
            0.0,
            233.039541,
            7.57,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            90,
            229,
            7.34 * 24 * 3600,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 5.168},
            False,
            False,
            0.0,
            229.031944,
            7.60,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            88,
            225,
            14.9 * 24 * 3600,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.058},
            False,
            False,
            0.0,
            225.023936,
            7.62,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            89,
            225,
            10.1 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 0.058},
            False,
            False,
            0.0,
            225.023936,
            7.62,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            86,
            221,
            2.8 * 1.0,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 6.337},
            False,
            False,
            0.0,
            221.000000,
            7.64,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            84,
            217,
            1.8 * 1e-3,
            {DecayMode.ALPHA: 1.0},
            {DecayMode.ALPHA: 6.737},
            False,
            False,
            0.0,
            217.000000,
            7.66,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            82,
            213,
            10.2 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 1.397},
            False,
            False,
            0.0,
            213.000000,
            7.70,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (
            83,
            213,
            45.6 * 60,
            {DecayMode.BETA_MINUS: 1.0},
            {DecayMode.BETA_MINUS: 1.397},
            False,
            False,
            0.0,
            213.000000,
            7.70,
            0.0,
            0.0,
            0.0,
            False,
        ),
        (81, 209, float("inf"), {}, {}, True, False, 0.0, 208.980400, 7.87, 0.0, 0.0, 0.0, True),
    ]

    for data in radioactive_data:
        z, a, hl, modes, energies, fissile, fertile, abund, mass, be, nxs, fxs, fy, is_stable = data
        isotopes[(z, a)] = _create_isotope(
            z,
            a,
            hl,
            modes,
            energies,
            is_fissile=fissile,
            is_fertile=fertile,
            is_stable=is_stable,
            natural_abundance=abund,
            atomic_mass=mass,
            binding_energy=be,
            n_xs=nxs,
            f_xs=fxs,
            f_yield=fy,
        )

    # Fill in decay chain daughters
    chain_data = [
        (92, 238, 90, 234),
        (90, 234, 91, 234),
        (91, 234, 92, 234),
        (92, 234, 90, 230),
        (90, 230, 88, 226),
        (88, 226, 86, 222),
        (86, 222, 84, 218),
        (84, 218, 82, 214),
        (82, 214, 83, 214),
        (83, 214, 84, 214),
        (84, 214, 82, 210),
        (82, 210, 83, 210),
        (83, 210, 84, 210),
        (84, 210, 82, 206),
        # U-235 chain
        (92, 235, 90, 231),
        (90, 231, 91, 231),
        (91, 231, 89, 227),
        (89, 227, 90, 227),
        (90, 227, 88, 223),
        (88, 223, 86, 219),
        (86, 219, 84, 215),
        (84, 215, 82, 211),
        (82, 211, 83, 211),
        (83, 211, 84, 211),
        (84, 211, 81, 207),
        (81, 207, 81, 207),
        # Th-232 chain
        (90, 232, 88, 228),
        (88, 228, 89, 228),
        (89, 228, 90, 228),
        (90, 228, 88, 224),
        (88, 224, 86, 220),
        (86, 220, 84, 216),
        (84, 216, 82, 212),
        (82, 212, 83, 212),
        (83, 212, 84, 212),
        (84, 212, 81, 208),
        (81, 208, 81, 208),
    ]

    for pz, pa, dz, da in chain_data:
        if (pz, pa) in isotopes and (dz, da) in isotopes:
            isotopes[(pz, pa)].daughter_z = dz
            isotopes[(pz, pa)].daughter_a = da
            isotopes[(pz, pa)].daughter_symbol = ELEMENT_SYMBOLS.get(dz, "X")

    return isotopes


ISOTOPE_CATALOG = _build_isotope_catalog()


# ============================================================================
# Nuclear Engine
# ============================================================================


class NuclearEngine:
    """Complete nuclear physics and radiochemistry simulation engine."""

    def __init__(self):
        self.isotopes = ISOTOPE_CATALOG
        self._build_decay_chains()

    def _build_decay_chains(self):
        """Build complete decay chains."""
        self.decay_chains = {}

        # U-238 chain
        u238_chain = self._build_chain(92, 238)
        self.decay_chains["U-238"] = DecayChain(
            parent=self.isotopes[(92, 238)],
            chain=u238_chain,
            total_half_life=4.468e9 * 365.25 * 24 * 3600,
            equilibrium_type="secular",
        )

        # U-235 chain
        u235_chain = self._build_chain(92, 235)
        self.decay_chains["U-235"] = DecayChain(
            parent=self.isotopes[(92, 235)],
            chain=u235_chain,
            total_half_life=7.04e8 * 365.25 * 24 * 3600,
            equilibrium_type="secular",
        )

        # Th-232 chain
        th232_chain = self._build_chain(90, 232)
        self.decay_chains["Th-232"] = DecayChain(
            parent=self.isotopes[(90, 232)],
            chain=th232_chain,
            total_half_life=1.405e10 * 365.25 * 24 * 3600,
            equilibrium_type="secular",
        )

        # Np-237 chain
        np237_chain = self._build_chain(93, 237)
        self.decay_chains["Np-237"] = DecayChain(
            parent=self.isotopes[(93, 237)],
            chain=np237_chain,
            total_half_life=2.14e6 * 365.25 * 24 * 3600,
            equilibrium_type="transient",
        )

    def _build_chain(self, z: int, a: int) -> list[Isotope]:
        """Build decay chain starting from parent isotope."""
        chain = []
        current = self.isotopes.get((z, a))
        visited = set()

        while current and (current.z, current.a) not in visited:
            chain.append(current)
            visited.add((current.z, current.a))

            if current.daughter_z and current.daughter_a:
                current = self.isotopes.get((current.daughter_z, current.daughter_a))
            else:
                break

        return chain

    # -----------------------------------------------------------------------
    # Isotope Catalog Access
    # -----------------------------------------------------------------------

    def get_isotope(self, z: int, a: int) -> Isotope | None:
        """Get isotope by atomic number Z and mass number A."""
        return self.isotopes.get((z, a))

    def get_isotope_by_symbol(self, symbol: str) -> Isotope | None:
        """Get isotope by symbol like 'U-235' or 'Pu-239'."""
        try:
            parts = symbol.split("-")
            if len(parts) == 2:
                elem = parts[0].capitalize()
                mass = int(parts[1])
                z = None
                for z_num, sym in ELEMENT_SYMBOLS.items():
                    if sym.lower() == elem.lower():
                        z = z_num
                        break
                if z:
                    return self.get_isotope(z, mass)
        except (ValueError, IndexError):
            pass
        return None

    def get_all_isotopes(self) -> list[Isotope]:
        """Get all isotopes in catalog."""
        return list(self.isotopes.values())

    def get_isotopes_by_element(self, z: int) -> list[Isotope]:
        """Get all isotopes of an element."""
        return [iso for (iz, ia), iso in self.isotopes.items() if iz == z]

    def get_fissile_isotopes(self) -> list[Isotope]:
        """Get all fissile isotopes."""
        return [iso for iso in self.isotopes.values() if iso.is_fissile]

    def get_fertile_isotopes(self) -> list[Isotope]:
        """Get all fertile isotopes."""
        return [iso for iso in self.isotopes.values() if iso.is_fertile]

    def get_fission_products(self) -> list[Isotope]:
        """Get key fission product isotopes."""
        fp_z = [
            38,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
        ]
        return [
            iso
            for (z, a), iso in self.isotopes.items()
            if z in fp_z and not iso.is_stable and iso.half_life_seconds < 1e12
        ]

    # -----------------------------------------------------------------------
    # Decay Calculations
    # -----------------------------------------------------------------------

    def decay_constant(self, isotope: Isotope) -> float:
        """Calculate decay constant λ = ln(2) / T½."""
        if isotope.half_life_seconds == float("inf") or isotope.half_life_seconds <= 0:
            return 0.0
        return math.log(2) / isotope.half_life_seconds

    def activity(self, isotope: Isotope, num_atoms: float) -> float:
        """Calculate activity A = λN in Bq."""
        return self.decay_constant(isotope) * num_atoms

    def half_life(self, isotope: Isotope) -> float:
        """Get half-life in seconds."""
        return isotope.half_life_seconds

    def remaining_fraction(self, isotope: Isotope, time_seconds: float) -> float:
        """Calculate fraction remaining after time t: N/N0 = e^(-λt)."""
        lam = self.decay_constant(isotope)
        if lam == 0:
            return 1.0
        return math.exp(-lam * time_seconds)

    def time_for_fraction(self, isotope: Isotope, fraction: float) -> float:
        """Calculate time for fraction to remain."""
        lam = self.decay_constant(isotope)
        if lam == 0 or fraction <= 0 or fraction > 1:
            return float("inf")
        return -math.log(fraction) / lam

    def decay_chain_activity(
        self, parent: Isotope, initial_atoms: float, time_seconds: float
    ) -> dict[str, float]:
        """Calculate activities of all chain members at time t (Bateman equations)."""
        chain = self._build_chain(parent.z, parent.a)
        activities = {}

        for i, iso in enumerate(chain):
            if i == 0:
                # Parent
                n = initial_atoms * self.remaining_fraction(iso, time_seconds)
                activities[iso.name] = self.activity(iso, n)
            else:
                # Daughter - Bateman equation
                # Simplified: assume secular equilibrium for long-lived parents
                parent_iso = chain[0]
                if self.decay_constant(parent_iso) < self.decay_constant(iso) * 0.01:
                    # Secular equilibrium: A_daughter = A_parent
                    activities[iso.name] = activities[parent_iso.name]
                else:
                    # Transient or no equilibrium
                    lam_d = self.decay_constant(iso)
                    lam_p = self.decay_constant(parent_iso)
                    if lam_d != lam_p:
                        n = (
                            initial_atoms
                            * (lam_p / (lam_d - lam_p))
                            * (math.exp(-lam_p * time_seconds) - math.exp(-lam_d * time_seconds))
                        )
                        activities[iso.name] = self.activity(iso, max(0, n))
                    else:
                        activities[iso.name] = 0.0

        return activities

    # -----------------------------------------------------------------------
    # Radiation Physics
    # -----------------------------------------------------------------------

    def alpha_range_cm(self, energy_mev: float, material: ShieldingMaterial) -> float:
        """Calculate alpha particle range in material (cm)."""
        # Simplified: R = 0.318 * E^1.5 / density for E in MeV
        # But need to convert from mg/cm² to cm: range_cm = range_mg_cm2 / (density * 1000)
        # More accurate: R(cm) = 0.005 * E^1.5 / density for E in MeV (air)
        # For solids: much shorter range
        range_mg_cm2 = 0.318 * energy_mev**1.5  # mg/cm² in air
        range_cm = range_mg_cm2 / (material.density_g_cm3 * 1000)
        return range_cm

    def beta_range_cm(self, energy_mev: float, material: ShieldingMaterial) -> float:
        """Calculate beta particle range in material (cm)."""
        # Katz-Penfold: R(g/cm²) = 0.412 * E^1.265 - 0.0954 for E > 0.8 MeV
        if energy_mev <= 0.8:
            range_mg_cm2 = 0.53 * energy_mev**2  # approximate
        else:
            range_mg_cm2 = (0.412 * energy_mev**1.265 - 0.0954) * 1000
        range_cm = range_mg_cm2 / (material.density_g_cm3 * 1000)
        return range_cm

    def gamma_attenuation(
        self, energy_mev: float, material: ShieldingMaterial, thickness_cm: float
    ) -> float:
        """Calculate gamma attenuation I/I0 = exp(-μx)."""
        # Mass attenuation coefficient (simplified)
        # Photoelectric ~ E^-3, Compton ~ constant, Pair ~ E
        if energy_mev < 0.1:
            mu_rho = 100 * energy_mev**-3
        elif energy_mev < 5:
            mu_rho = 0.1
        elif energy_mev < 10:
            mu_rho = 0.05
        else:
            mu_rho = 0.04

        mu = mu_rho * material.density_g_cm3
        return math.exp(-mu * thickness_cm)

    def neutron_attenuation(self, material: ShieldingMaterial, thickness_cm: float) -> float:
        """Calculate neutron attenuation."""
        return math.exp(-material.neutron_macro_xs * thickness_cm)

    def dose_rate_gamma(
        self, activity_bq: float, energy_mev: float, distance_m: float, yield_per_decay: float = 1.0
    ) -> float:
        """Calculate gamma dose rate in µSv/h at distance."""
        # Simplified: 6 * E(MeV) * A(GBq) / d(m)² * yield
        a_gbq = activity_bq / 1e9
        dose = 6.0 * energy_mev * a_gbq * yield_per_decay / (distance_m**2)
        return dose  # µSv/h

    def shielding_thickness(
        self,
        material: ShieldingMaterial,
        initial_dose: float,
        target_dose: float,
        energy_mev: float,
    ) -> float:
        """Calculate required shielding thickness for dose reduction."""
        if target_dose >= initial_dose:
            return 0.0
        ratio = target_dose / initial_dose
        if energy_mev < 0.1:
            mu_rho = 100 * energy_mev**-3
        elif energy_mev < 5:
            mu_rho = 0.1
        elif energy_mev < 10:
            mu_rho = 0.05
        else:
            mu_rho = 0.04
        mu = mu_rho * material.density_g_cm3
        return -math.log(ratio) / mu

    # -----------------------------------------------------------------------
    # Reactor Physics
    # -----------------------------------------------------------------------

    def reactor_criticality(self, fuel: FuelAssembly, moderator_ratio: float = 2.0) -> float:
        """Calculate k-effective for a reactor configuration."""
        # Four-factor formula: k = η * f * p * ε
        # η = neutrons produced per absorption in fuel
        # f = thermal utilization factor
        # p = resonance escape probability
        # ε = fast fission factor

        # U-235 enrichment (as fraction)
        enr = fuel.enrichment_percent / 100.0

        # η (eta) - neutrons produced per absorption in fuel
        if fuel.fuel_type == "UO2":
            # eta = neutrons per absorption in fuel
            # For UO2: dominated by U-235 (eta=2.07) vs U-238 (eta≈0)
            # Fraction of absorptions in U-235 ≈ enr / (enr + 0.01*(1-enr))
            eta = 2.07 * enr / (enr + 0.01 * (1 - enr))
        elif fuel.fuel_type == "MOX":
            pu_total = fuel.pu239_kg + fuel.pu240_kg + fuel.pu241_kg
            if pu_total > 0:
                eta = 2.1 * fuel.pu239_kg / pu_total
            else:
                eta = 2.0
        else:
            eta = 2.0

        # f - thermal utilization (moderator-to-fuel ratio effect)
        f = 1.0 / (1.0 + 0.1 * moderator_ratio)

        # p - resonance escape probability (approximate)
        # Higher enrichment -> better resonance escape
        p = 0.7 + 0.3 * enr  # simplified linear interpolation

        # ε - fast fission factor
        eps = 1.02 + 0.05 * enr

        k_inf = eta * f * p * eps

        # Leakage (geometric buckling)
        # Assume 10% leakage for typical core
        leakage = 0.90

        k_eff = k_inf * leakage
        return min(max(k_eff, 0.0), 1.5)

    def xenon_135_equilibrium(
        self, flux_n_cm2_s: float, power_mw: float, core_volume_cm3: float = 3e7
    ) -> float:
        """Calculate equilibrium Xe-135 concentration (atoms/cm³)."""
        # I-135 yield ~6.3%, Xe-135 yield ~0.3% + from I-135 decay
        # λ_I = 2.9e-5 s^-1, λ_Xe = 2.1e-5 s^-1
        # σ_Xe = 2.6e6 barns = 2.6e-18 cm²
        gamma_I = 0.063
        gamma_Xe = 0.003
        sigma_Xe = 2.6e6 * 1e-24  # cm² (2.6e6 barns = 2.6e-18 cm²)

        # Production rate: fissions per second per MW thermal
        # 1 MW = 1e6 J/s, each fission ~200 MeV = 3.2e-11 J
        # So 1 MW = 1e6 / 3.2e-11 ≈ 3.12e16 fissions/s
        fission_rate = power_mw * 3.12e16  # fissions/s
        I_production = gamma_I * fission_rate
        Xe_production = gamma_Xe * fission_rate

        # Equilibrium: dXe/dt = 0 = Xe_production + λ_I * I_eq - (λ_Xe + σ_Xe * φ) * Xe_eq
        # where φ = flux_n_cm2_s
        lambda_I = 2.9e-5
        lambda_Xe = 2.1e-5
        I_eq = I_production / lambda_I
        Xe_eq = (Xe_production + lambda_I * I_eq) / (lambda_Xe + sigma_Xe * flux_n_cm2_s)

        # Convert to concentration per cm³ (assuming uniform core volume)
        return Xe_eq / core_volume_cm3  # atoms/cm³

    def samarium_149_equilibrium(self, flux_n_cm2_s: float) -> float:
        """Calculate equilibrium Sm-149 concentration."""
        # Sm-149 from Nd-149 -> Pm-149 -> Sm-149 decay chain
        # Pm-149: λ = 3.6e-6 s^-1, fission yield ~1.1%
        # Sm-149: stable, σ = 4.1e4 barns = 4.1e-20 cm²
        gamma_Pm = 0.011  # Pm-149 yield (1.1%)
        lambda_Pm = 3.6e-6  # s^-1
        sigma_Sm = 4.1e4 * 1e-24  # cm²

        # Typical thermal flux for PWR: ~3e13 n/cm²/s
        # Typical fission rate density: flux * macroscopic fission cross section
        # For 1e13 n/cm²/s flux and ~0.1 cm^-1 macroscopic fission XS: ~1e12 fissions/cm³/s
        fission_rate_density = flux_n_cm2_s * 0.1  # approximate fissions/cm³/s
        Pm_production = gamma_Pm * fission_rate_density
        Pm_eq = Pm_production / 3.6e-6
        Sm_eq = lambda_Pm * Pm_eq / (sigma_Sm * flux_n_cm2_s)

        return Sm_eq  # atoms/cm³

    def fuel_burnup(
        self, initial_enrichment: float, power_mw: float, days: float, mass_mtU: float
    ) -> dict:
        """Calculate fuel burnup and isotopic evolution."""
        # Simplified burnup calculation
        energy_per_fission = 200e6 * 1.602e-13  # J
        # Use thermal power (3x electrical for typical PWR)
        thermal_power_mw = power_mw * 3.0
        total_energy = thermal_power_mw * 1e6 * days * 24 * 3600
        fissions = total_energy / energy_per_fission

        # Atoms of U-235 initially
        u235_mass_kg = mass_mtU * 1000 * (initial_enrichment / 100)
        u235_atoms = u235_mass_kg / 0.235 * 6.022e23

        # Burnup fraction
        burnup_frac = fissions / u235_atoms if u235_atoms > 0 else 0

        # Isotopic evolution (simplified)
        u235_remaining = max(0, 1 - burnup_frac)
        pu239_produced = min(0.01, burnup_frac * 0.5)  # approx
        pu240_produced = pu239_produced * 0.2
        fp_produced = burnup_frac * 0.9

        # Standard burnup in GWd/tU
        thermal_power_mw = power_mw * 3.0  # typical PWR thermal/electrical ratio
        burnup_gwd_mtU = thermal_power_mw * days / mass_mtU / 1000 if mass_mtU > 0 else 0

        return {
            "burnup_gwd_mtU": burnup_gwd_mtU,
            "u235_fraction_remaining": u235_remaining,
            "pu239_produced_kg": pu239_produced * mass_mtU * 1000,
            "pu240_produced_kg": pu240_produced * mass_mtU * 1000,
            "fission_products_kg": fp_produced * mass_mtU * 1000,
            "fissions": fissions,
        }

    # -----------------------------------------------------------------------
    # Reprocessing
    # -----------------------------------------------------------------------

    def reprocess_fuel(
        self, fuel: FuelAssembly, pu_recovery: float = 0.99, u_recovery: float = 0.995
    ) -> dict[str, ReprocessingStream]:
        """Simulate PUREX reprocessing of spent fuel."""
        heavy_metal = fuel.mass_kg

        # Fission products
        fp = fuel.fission_products_kg
        # Minor actinides
        ma = fuel.minor_actinides_kg

        # Recovered U and Pu
        u235_rec = fuel.current_u235_kg * u_recovery
        u238_rec = (
            heavy_metal - fuel.initial_u235_kg - fuel.pu239_kg - fuel.pu240_kg - fuel.pu241_kg
        ) * u_recovery
        pu239_rec = fuel.pu239_kg * pu_recovery
        pu240_rec = fuel.pu240_kg * pu_recovery
        pu241_rec = fuel.pu241_kg * pu_recovery

        streams = {
            "uranium_product": ReprocessingStream(
                "Uranium Product", u235_rec + u238_rec, u235_rec, u238_rec, 0, 0, 0, 0, 0, "LLW"
            ),
            "plutonium_product": ReprocessingStream(
                "Plutonium Product",
                pu239_rec + pu240_rec + pu241_rec,
                0,
                0,
                pu239_rec,
                pu240_rec,
                pu241_rec,
                0,
                0,
                "HLW",
            ),
            "high_level_waste": ReprocessingStream(
                "High-Level Waste", fp + ma, 0, 0, 0, 0, 0, fp, ma, "HLW"
            ),
            "hull_end_fittings": ReprocessingStream(
                "Hulls & End Fittings", heavy_metal * 0.1, 0, 0, 0, 0, 0, 0, 0, "ILW"
            ),
        }

        return streams

    # -----------------------------------------------------------------------
    # Detection & Measurement
    # -----------------------------------------------------------------------

    def geiger_muller_count_rate(
        self,
        activity_bq: float,
        distance_cm: float,
        detector_area_cm2: float = 10.0,
        efficiency: float = 0.01,
    ) -> float:
        """Calculate GM count rate (cps)."""
        # Solid angle fraction
        solid_angle = detector_area_cm2 / (4 * math.pi * distance_cm**2)
        return activity_bq * solid_angle * efficiency

    def scintillator_efficiency(self, energy_mev: float, detector: str = "NaI") -> float:
        """Scintillator detection efficiency."""
        if detector == "NaI":
            if energy_mev < 0.1:
                return 0.8
            elif energy_mev < 1.0:
                return 0.5
            elif energy_mev < 3.0:
                return 0.3
            else:
                return 0.15  # non-zero for higher energies
        elif detector == "LaBr3":
            return min(1.0, 0.7 * energy_mev**0.5)
        elif detector == "HPGe":
            return min(1.0, 0.3 * energy_mev**0.3)
        return 0.1

    def gamma_spectrum_simulation(
        self,
        isotopes: list[tuple[Isotope, float]],
        detector: str = "HPGe",
        live_time_s: float = 3600,
    ) -> dict:
        """Simulate gamma spectrum."""
        peaks = {}
        for iso, activity in isotopes:
            for mode, energy in iso.decay_energies.items():
                if mode in [DecayMode.GAMMA, DecayMode.INTERNAL_TRANSITION]:
                    eff = self.scintillator_efficiency(energy, detector)
                    counts = activity * eff * live_time_s
                    peaks[energy] = counts
                # Also check for gamma energies in decay modes
                if (
                    mode == DecayMode.BETA_MINUS
                    or mode == DecayMode.BETA_PLUS
                    or mode == DecayMode.ELECTRON_CAPTURE
                ):
                    # Many beta decays have accompanying gammas
                    # Add common gamma energies for known isotopes
                    if iso.z == 55 and iso.a == 137:  # Cs-137
                        eff = self.scintillator_efficiency(0.662, detector)
                        counts = activity * eff * live_time_s
                        peaks[0.662] = counts
                    elif iso.z == 27 and iso.a == 60:  # Co-60
                        eff = self.scintillator_efficiency(1.173, detector)
                        counts = activity * eff * live_time_s
                        peaks[1.173] = counts
                        eff = self.scintillator_efficiency(1.332, detector)
                        counts = activity * eff * live_time_s
                        peaks[1.332] = counts
                    elif iso.z == 43 and iso.a == 99:  # Tc-99m
                        eff = self.scintillator_efficiency(0.141, detector)
                        counts = activity * eff * live_time_s
                        peaks[0.141] = counts

        return {"peaks": peaks, "continuum": {}, "live_time_s": live_time_s, "detector": detector}

    def dosimeter_reading(
        self, dose_rate_uSv_h: float, time_h: float, dosimeter_type: str = "TLD"
    ) -> dict:
        """Simulate dosimeter reading."""
        total_dose = dose_rate_uSv_h * time_h

        # Add noise
        if dosimeter_type == "TLD":
            uncertainty = 0.05  # 5%
        elif dosimeter_type == "OSL":
            uncertainty = 0.03
        elif dosimeter_type == "EPD":
            uncertainty = 0.10
        else:
            uncertainty = 0.10

        reading = total_dose * (1 + random.uniform(-uncertainty, uncertainty))

        return {
            "dose_uSv": reading,
            "dose_rate_uSv_h": dose_rate_uSv_h,
            "time_h": time_h,
            "uncertainty_percent": uncertainty * 100,
            "alarm": reading > 20.0,  # 20 µSv alarm threshold
        }


# Global instance
NUCLEAR_ENGINE = NuclearEngine()
