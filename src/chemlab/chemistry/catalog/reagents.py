"""
ChemLab Catalog — authoritative chemical reagent database.

Single source of truth for all chemical substances in the simulator. This module
consolidates the previously fragmented reagent catalogs:

  * src/chemlab/simulation/reagents.py   (REAGENT_REGISTRY, Reagent dataclass)
  * simulation/catalog.py                 (>100 entries, ReagentCatalog class)
  * safety_simulation/ghs.py              (25 GHS profiles, ChemicalProfile,
                                           check_chemical_compatibility, SDS)

Every entry carries authentic physical & chemical properties:
  * Identity (id, name, formula, CAS number, category)
  * Thermodynamics (molar mass, density, melting/boiling point, pKa, Antoine coefficients)
  * Visuals (RGBA color signature, particle type for rendering)
  * Safety (GHS pictograms, hazard statements, signal word, storage group,
            Antoine vapor-pressure model, incompatibility rules)

Lookup helpers: get_reagent(id), search_by_formula(), search_by_category(),
list_reagents(), count_by_category(). All lookups are case-insensitive and
whitespace-tolerant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from chemlab.compat import UTC


# =============================================================================
# 1. Enumerations (consolidated from all three legacy modules)
# =============================================================================

class ReagentCategory(StrEnum):
    """High-level chemical classification of a substance."""

    ACID = "acid"
    BASE = "base"
    TRANSITION_METAL_SALT = "transition_metal_salt"
    INDICATOR = "indicator"
    OXIDIZER = "oxidizer"
    ORGANIC_SOLVENT = "organic_solvent"
    REDUCING_AGENT = "reducing_agent"
    HEAVY_METAL_SALT = "heavy_metal_salt"
    HALOGEN_SALT = "halogen_salt"
    NITROGEN_COMPOUND = "nitrogen_compound"
    ALKALINE_EARTH_SALT = "alkaline_earth_salt"
    PRECIPITATING_AGENT = "precipitating_agent"
    POLYMER = "polymer"
    BIOLOGICAL = "biological"
    NUCLEIC_ACID = "nucleic_acid"
    AMINO_ACID = "amino_acid"
    CARBOHYDRATE = "carbohydrate"
    LIPID = "lipid"
    MISCELLANEOUS = "miscellaneous"


class ParticleType(StrEnum):
    """Visual particle representation used by the Godot rendering layer."""

    LIQUID_DROPLET = "liquid_droplet"
    POWDER_CRYSTAL = "powder_crystal"
    GAS_BUBBLE = "gas_bubble"
    GEL_COLLOID = "gel_colloid"
    FIBROUS = "fibrous"
    GRANULAR = "granular"
    PAPER_STRIP = "paper_strip"


class SignalWord(StrEnum):
    """GHS signal word for label rendering."""

    DANGER = "DANGER"
    WARNING = "WARNING"
    NONE = "NONE"


class StorageGroup(StrEnum):
    """Segregated chemical storage class for lab safety logic."""

    FLAMMABLE_CABINET = "flammable_cabinet"
    ACID_CABINET = "acid_cabinet"
    BASE_CABINET = "base_cabinet"
    OXIDIZER_STORAGE = "oxidizer_storage"
    GENERAL_STORAGE = "general_storage"
    TOXIC_SECURE = "toxic_secure"
    EXPLOSIVE_MAGAZINE = "explosive_magazine"


# Legacy Enum aliases (simulation/catalog.py used plain Enum for these two).
class GHSPictogramLegacy(Enum):
    """Standard GHS Pictogram designations (legacy Enum variant)."""

    GHS01_EXPLODING_BOMB = "ghs01"
    GHS02_FLAME = "ghs02"
    GHS03_FLAME_OVER_CIRCLE = "ghs03"
    GHS04_GAS_CYLINDER = "ghs04"
    GHS05_CORROSION = "ghs05"
    GHS06_SKULL_AND_CROSSBONES = "ghs06"
    GHS07_EXCLAMATION_MARK = "ghs07"
    GHS08_HEALTH_HAZARD = "ghs08"
    GHS09_ENVIRONMENT = "ghs09"


class GHSClassLegacy(StrEnum):
    """GHS Hazard Classes (legacy StrEnum variant)."""

    EXPLOSIVE = "EXPLOSIVE"
    FLAMMABLE = "FLAMMABLE"
    OXIDIZING = "OXIDIZING"
    COMPRESSED_GAS = "COMPRESSED_GAS"
    CORROSIVE = "CORROSIVE"
    TOXIC = "TOXIC"
    HARMFUL_IRRITANT = "HARMFUL_IRRITANT"
    HEALTH_HAZARD = "HEALTH_HAZARD"
    ENVIRONMENTAL = "ENVIRONMENTAL"


# Canonical GHS pictogram codes (StrEnum) — used by GHSHazard / Reagent.
class GHSPictogram(StrEnum):
    """Standard GHS Pictogram designations (GHS01 - GHS09)."""

    GHS01_EXPLODING_BOMB = "GHS01_EXPLODING_BOMB"
    GHS02_FLAME = "GHS02_FLAME"
    GHS03_FLAME_OVER_CIRCLE = "GHS03_FLAME_OVER_CIRCLE"
    GHS04_GAS_CYLINDER = "GHS04_GAS_CYLINDER"
    GHS05_CORROSION = "GHS05_CORROSION"
    GHS06_SKULL_CROSSBONES = "GHS06_SKULL_CROSSBONES"
    GHS07_EXCLAMATION_MARK = "GHS07_EXCLAMATION_MARK"
    GHS08_HEALTH_HAZARD = "GHS08_HEALTH_HAZARD"
    GHS09_ENVIRONMENT = "GHS09_ENVIRONMENT"


# =============================================================================
# 2. Data classes
# =============================================================================

@dataclass(frozen=True)
class GHSHazard:
    """A single GHS hazard classification."""

    code: str  # e.g. "H314"
    text: str  # human-readable statement
    pictogram: str  # "GHS05" etc.
    signal_word: SignalWord
    category: int


@dataclass(frozen=True)
class Reagent:
    """A chemical substance with authentic properties for simulation & rendering."""

    id: str
    name: str
    formula: str
    category: ReagentCategory
    molar_mass_g_per_mol: float
    density_g_per_ml: float
    cas_number: str | None = None
    melting_point_c: float | None = None
    boiling_point_c: float | None = None
    pka: float | None = None
    ph: float | None = None
    solubility_g_per_100ml_water: float | None = None
    default_color_rgba: tuple[float, float, float, float] = (0.92, 0.96, 1.0, 1.0)
    particle_type: ParticleType = ParticleType.LIQUID_DROPLET
    ghs_hazards: tuple[GHSHazard, ...] = ()
    is_catalyst: bool = False
    common_uses: str = ""
    storage_group: StorageGroup = StorageGroup.GENERAL_STORAGE
    description: str = ""

    @property
    def molar_mass(self) -> float:
        return self.molar_mass_g_per_mol

    @property
    def density(self) -> float:
        return self.density_g_per_ml

    @property
    def ghs_pictograms(self) -> tuple[str, ...]:
        """Tuple of GHS pictogram codes (e.g. ("GHS05", "GHS07"))."""
        return tuple(hazard.pictogram for hazard in self.ghs_hazards)

    @property
    def hazard_statements(self) -> tuple[str, ...]:
        """Tuple of human-readable GHS H-statements."""
        return tuple(hazard.text for hazard in self.ghs_hazards)

    @property
    def storage_note(self) -> str:
        """Human-readable storage instruction derived from the storage group."""
        notes = {
            StorageGroup.FLAMMABLE_CABINET: "Im flammableschrank lagern.",
            StorageGroup.ACID_CABINET: "Im Säureschrank lagern, getrennt von Basen.",
            StorageGroup.BASE_CABINET: "Im Basenschrank lagern, getrennt von Säuren.",
            StorageGroup.OXIDIZER_STORAGE: "Getrennt von organischen Stoffen lagern.",
            StorageGroup.TOXIC_SECURE: "Im giftstoffgesicherten Schrank lagern.",
            StorageGroup.EXPLOSIVE_MAGAZINE: "Im Explosivmagazin lagern.",
            StorageGroup.GENERAL_STORAGE: "Bei Raumtemperatur trocken lagern.",
        }
        return notes.get(self.storage_group, notes[StorageGroup.GENERAL_STORAGE])


@dataclass
class GHSHazardStatement:
    code: str
    ghs_class: GHSClassLegacy
    category: int
    text: str
    pictogram: GHSPictogramLegacy
    signal_word: SignalWord


@dataclass
class ChemicalProfile:
    id: str
    name: str
    formula: str
    cas_number: str
    molar_mass: float  # g/mol
    density: float  # g/cm^3 or g/mL
    boiling_point_c: float  # Celsius
    flash_point_c: float | None = None  # Celsius
    autoignition_temp_c: float | None = None  # Celsius
    vapor_pressure_kpa_20c: float = 0.0  # kPa at 20 C
    is_volatile: bool = False
    is_acid: bool = False
    is_base: bool = False
    acid_pka: float | None = None
    hazard_classes: set[GHSClassLegacy] = field(default_factory=set)
    signal_word: SignalWord = SignalWord.NONE
    pictograms: list[GHSPictogramLegacy] = field(default_factory=list)
    h_statements: list[str] = field(default_factory=list)
    p_statements: list[str] = field(default_factory=list)
    storage_group: StorageGroup = StorageGroup.GENERAL_STORAGE
    incompatible_with: list[str] = field(default_factory=list)
    antoine_coefficients: tuple[float, float, float] = (0.0, 0.0, 0.0)  # (A, B, C)

    def calculate_vapor_pressure_kpa(self, temp_c: float) -> float:
        """Calculate vapor pressure using Antoine equation in kPa."""
        a, b, c = self.antoine_coefficients
        if a == 0.0:
            delta_t = temp_c - 20.0
            return max(0.01, self.vapor_pressure_kpa_20c * (2.0 ** (delta_t / 10.0)))
        log10_p_mmhg = a - (b / (temp_c + c))
        p_mmhg = 10.0 ** log10_p_mmhg
        # 1 mmHg = 0.133322 kPa
        return max(0.01, p_mmhg * 0.133322)


@dataclass
class IncompatibilityResult:
    compatible: bool
    risk_level: str  # "NONE", "LOW", "MODERATE", "SEVERE", "CRITICAL"
    reaction_type: str | None = None
    hazard_description: str | None = None
    byproducts: list[str] = field(default_factory=list)


# =============================================================================
# 3. Authoritative reagent registry (organic & inorganic)
# =============================================================================

_REAGENTS: dict[str, Reagent] = {}


def _ghs(code: str, text: str, pictogram: str, signal_word: SignalWord, category: int) -> GHSHazard:
    return GHSHazard(code, text, pictogram, signal_word, category)


def _rgba(r: float, g: float, b: float, a: float = 1.0) -> tuple[float, float, float, float]:
    return (r, g, b, a)


def _register(reagent: Reagent) -> None:
    _REAGENTS[reagent.id] = reagent


# ── ACIDS ──────────────────────────────────────────────────────────────────

_register(
    Reagent(
        id="hcl",
        name="Salzsäure (37%)",
        formula="HCl",
        category=ReagentCategory.ACID,
        molar_mass_g_per_mol=36.46,
        density_g_per_ml=1.18,
        cas_number="7647-01-0",
        boiling_point_c=110.0,
        pka=-7.0,
        ph=-1.0,
        solubility_g_per_100ml_water=823.0,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs(
                "H314",
                "Verursacht schwere Verätzungen der Haut und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
            _ghs("H335", "Kann die Atemwege reizen.", "GHS07", SignalWord.WARNING, 3),
        ),
        storage_group=StorageGroup.ACID_CABINET,
        common_uses="pH-Anpassung, Beizung, Chlorid-Synthese",
        description="Starke anorganische Säure, stark ätzend.",
    )
)

_register(
    Reagent(
        id="sulfuric_acid",
        name="Schwefelsäure (98%, konzentriert)",
        formula="H2SO4",
        category=ReagentCategory.ACID,
        molar_mass_g_per_mol=98.08,
        density_g_per_ml=1.84,
        cas_number="7664-93-9",
        melting_point_c=10.0,
        boiling_point_c=337.0,
        pka=-3.0,
        ph=-2.0,
        solubility_g_per_100ml_water=540.0,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs(
                "H314",
                "Verursacht schwere Hautverätzungen und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
            _ghs("H290", "Kann Metalle korrodieren.", "GHS07", SignalWord.WARNING, 1),
        ),
        storage_group=StorageGroup.ACID_CABINET,
        common_uses="Dehydrationsmittel, Katalysator, Elektrolyt",
        description="Starke anorganische Säure mit hoher Dehydrationswirkung.",
    )
)

_register(
    Reagent(
        id="nitric_acid",
        name="Salpetersäure (65%)",
        formula="HNO3",
        category=ReagentCategory.ACID,
        molar_mass_g_per_mol=63.01,
        density_g_per_ml=1.41,
        cas_number="7697-37-2",
        boiling_point_c=83.0,
        pka=-1.4,
        ph=-1.0,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs(
                "H314",
                "Verursacht schwere Verätzungen der Haut und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
            _ghs(
                "H272", "Kann Brand intensivieren; Oxidierendes Mittel.", "GHS03", SignalWord.DANGER, 1
            ),
        ),
        storage_group=StorageGroup.ACID_CABINET,
        common_uses="Nitrierung, Oxidation, Metallbeizung",
        description="Starke Oxidiersäure, gefährlich bei Kontakt mit Organischem.",
    )
)

_register(
    Reagent(
        id="acetic_acid",
        name="Essigsäure (glazial)",
        formula="CH3COOH",
        category=ReagentCategory.ACID,
        molar_mass_g_per_mol=60.05,
        density_g_per_ml=1.05,
        cas_number="64-19-7",
        melting_point_c=16.6,
        boiling_point_c=118.0,
        pka=4.76,
        ph=2.4,
        solubility_g_per_100ml_water=1000.0,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs(
                "H314",
                "Verursacht schwere Hautverätzungen und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
        ),
        storage_group=StorageGroup.ACID_CABINET,
        common_uses="Veresterung, Lösungsmittel, Lebensmittelzusatz",
        description="Schwach säureige organische Carbonsäure.",
    )
)

# ── BASES ──────────────────────────────────────────────────────────────────

_register(
    Reagent(
        id="naoh",
        name="Natronlauge (1M)",
        formula="NaOH",
        category=ReagentCategory.BASE,
        molar_mass_g_per_mol=39.997,
        density_g_per_ml=2.13,
        cas_number="1310-73-2",
        melting_point_c=318.0,
        boiling_point_c=1388.0,
        ph=14.0,
        solubility_g_per_100ml_water=109.0,
        default_color_rgba=_rgba(0.98, 0.99, 1.0, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(
            _ghs(
                "H314",
                "Verursacht schwere Hautverätzungen und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
            _ghs("H290", "Kann Metalle korrodieren.", "GHS07", SignalWord.WARNING, 1),
        ),
        storage_group=StorageGroup.BASE_CABINET,
        common_uses="Säure-Base-Neutralisation, Verseifung",
        description="Starke anorganische Lauge, stark ätzend.",
    )
)

_register(
    Reagent(
        id="nh3",
        name="Ammoniak (wässrig)",
        formula="NH3 (aq)",
        category=ReagentCategory.BASE,
        molar_mass_g_per_mol=17.03,
        density_g_per_ml=0.90,
        cas_number="7664-41-7",
        boiling_point_c=-33.0,
        pka=9.25,
        ph=11.0,
        solubility_g_per_100ml_water=47.0,
        default_color_rgba=_rgba(0.97, 0.99, 1.0, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs(
                "H314",
                "Verursacht schwere Hautverätzungen und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
            _ghs("H400", "Sehr giftig für Wasserorganismen.", "GHS09", SignalWord.WARNING, 1),
        ),
        storage_group=StorageGroup.BASE_CABINET,
        common_uses="Basenquelle, Komplexbildung, Reinigung",
        description="Schwache anorganische Base mit stechendem Geruch.",
    )
)

# ── SALTS ──────────────────────────────────────────────────────────────────

_register(
    Reagent(
        id="nacl",
        name="Natriumchlorid (Kochsalz)",
        formula="NaCl",
        category=ReagentCategory.HALOGEN_SALT,
        molar_mass_g_per_mol=58.44,
        density_g_per_ml=2.16,
        cas_number="7647-14-5",
        melting_point_c=801.0,
        boiling_point_c=1465.0,
        ph=7.0,
        solubility_g_per_100ml_water=35.9,
        default_color_rgba=_rgba(0.96, 0.98, 1.0, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Speisesalz, Elektrolyt, Neutralisationsprodukt",
        description="Unbedenkliches Halogensalz, kristallin.",
    )
)

_register(
    Reagent(
        id="ki",
        name="Kaliumiodid",
        formula="KI",
        category=ReagentCategory.HALOGEN_SALT,
        molar_mass_g_per_mol=166.0,
        density_g_per_ml=3.12,
        cas_number="7681-11-0",
        melting_point_c=681.0,
        boiling_point_c=1330.0,
        ph=7.0,
        solubility_g_per_100ml_water=144.0,
        default_color_rgba=_rgba(0.98, 0.96, 0.92, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(_ghs("H315", "Verursacht Hautreizungen.", "GHS07", SignalWord.WARNING, 2),),
        storage_group=StorageGroup.GENERAL_STORAGE,
        is_catalyst=True,
        common_uses="Katalysator bei Peroxidzersetzung, Jodquelle",
        description="Salz, fungiert als Katalysator bei der Zersetzung von Peroxid.",
    )
)

# ── TRANSITION METAL SALTS ─────────────────────────────────────────────────

_register(
    Reagent(
        id="cu_so4",
        name="Kupfersulfat (pentahydratisiert)",
        formula="CuSO4·5H2O",
        category=ReagentCategory.TRANSITION_METAL_SALT,
        molar_mass_g_per_mol=249.69,
        density_g_per_ml=2.28,
        cas_number="7758-99-8",
        melting_point_c=110.0,
        boiling_point_c=700.0,
        ph=4.5,
        solubility_g_per_100ml_water=31.6,
        default_color_rgba=_rgba(0.2, 0.5, 0.9, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(
            _ghs("H302", "Gesundheitsschädlich bei Verschlucken.", "GHS07", SignalWord.WARNING, 4),
            _ghs(
                "H410",
                "Sehr giftig für Wasserorganismen mit langfristiger Wirkung.",
                "GHS09",
                SignalWord.WARNING,
                1,
            ),
        ),
        storage_group=StorageGroup.TOXIC_SECURE,
        common_uses="Pigment, Fungizid, Elektrolyt",
        description="Blaues transitionelles Metallkristallsalz.",
    )
)

_register(
    Reagent(
        id="fecl3",
        name="Eisen(III)-chlorid",
        formula="FeCl3",
        category=ReagentCategory.TRANSITION_METAL_SALT,
        molar_mass_g_per_mol=162.2,
        density_g_per_ml=2.90,
        cas_number="7705-08-0",
        melting_point_c=306.0,
        boiling_point_c=315.0,
        ph=2.0,
        solubility_g_per_100ml_water=92.0,
        default_color_rgba=_rgba(0.8, 0.4, 0.1, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(
            _ghs(
                "H314",
                "Verursacht schwere Verätzungen der Haut und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
        ),
        storage_group=StorageGroup.ACID_CABINET,
        common_uses="Ätzmittel, Katalysator, Wasseraufbereitung",
        description="Bräunliches Eisen(III)-Salz, stark hygroskopisch.",
    )
)

_register(
    Reagent(
        id="agno3",
        name="Silbernitrat",
        formula="AgNO3",
        category=ReagentCategory.TRANSITION_METAL_SALT,
        molar_mass_g_per_mol=169.87,
        density_g_per_ml=4.35,
        cas_number="7761-88-8",
        melting_point_c=212.0,
        boiling_point_c=440.0,
        ph=6.0,
        solubility_g_per_100ml_water=219.0,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(
            _ghs(
                "H272", "Kann Brand intensivieren; Oxidierendes Mittel.", "GHS03", SignalWord.DANGER, 1
            ),
            _ghs("H400", "Sehr giftig für Wasserorganismen.", "GHS09", SignalWord.WARNING, 1),
        ),
        storage_group=StorageGroup.OXIDIZER_STORAGE,
        common_uses="Silberspiegelreaktion, Halogenidnachweis, Fotografie",
        description="Weißes Oxidationsmittel, lichtempfindlich.",
    )
)

# ── INDICATORS ─────────────────────────────────────────────────────────────

_register(
    Reagent(
        id="phenolphthalein",
        name="Phenolphthalein-Indikator",
        formula="C20H14O4",
        category=ReagentCategory.INDICATOR,
        molar_mass_g_per_mol=318.33,
        density_g_per_ml=1.27,
        cas_number="77-09-8",
        melting_point_c=261.0,
        ph=7.0,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(_ghs("H315", "Verursacht Hautreizungen.", "GHS07", SignalWord.WARNING, 2),),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Säure-Base-Indikator (farblos < pH 8.2, rosa > pH 10)",
        description="pH-Indikator für Titrationen, farblos in Säure, rosa in Base.",
    )
)

_register(
    Reagent(
        id="methyl_orange",
        name="Methylorange-Indikator",
        formula="C14H14N3NaO3S",
        category=ReagentCategory.INDICATOR,
        molar_mass_g_per_mol=327.34,
        density_g_per_ml=1.0,
        cas_number="547-58-0",
        ph=7.0,
        default_color_rgba=_rgba(1.0, 0.3, 0.1, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="pH-Indikator (rot < pH 3.1, gelb > pH 4.4)",
        description="Azofarbstoff als Säure-Base-Indikator.",
    )
)

# ── OXIDIZERS ──────────────────────────────────────────────────────────────

_register(
    Reagent(
        id="h2o2",
        name="Wasserstoffperoxid (30%)",
        formula="H2O2",
        category=ReagentCategory.OXIDIZER,
        molar_mass_g_per_mol=34.014,
        density_g_per_ml=1.11,
        cas_number="7722-84-1",
        boiling_point_c=150.0,
        ph=6.2,
        default_color_rgba=_rgba(0.94, 0.97, 1.0, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs(
                "H272", "Kann Brand intensivieren; Oxidierendes Mittel.", "GHS03", SignalWord.DANGER, 1
            ),
            _ghs(
                "H314",
                "Verursacht schwere Verätzungen der Haut und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
        ),
        storage_group=StorageGroup.OXIDIZER_STORAGE,
        common_uses="Oxidationsmittel, Schaumreaktionen, Desinfektion",
        description="Starkes Oxidationsmittel für Schaumreaktionen und Oszillatoren.",
    )
)

_register(
    Reagent(
        id="kio3",
        name="Kaliumiodat",
        formula="KIO3",
        category=ReagentCategory.OXIDIZER,
        molar_mass_g_per_mol=214.0,
        density_g_per_ml=3.89,
        cas_number="7758-05-6",
        melting_point_c=560.0,
        ph=7.0,
        solubility_g_per_100ml_water=4.8,
        default_color_rgba=_rgba(0.96, 0.96, 0.98, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(
            _ghs(
                "H272", "Kann Brand intensivieren; Oxidierendes Mittel.", "GHS03", SignalWord.DANGER, 1
            ),
        ),
        storage_group=StorageGroup.OXIDIZER_STORAGE,
        common_uses="Iodat-Quelle für Redox-Oszillation, Jodsalz",
        description="Iodat-Quelle für zyklische Redox-Oszillation.",
    )
)

# ── ORGANIC SOLVENTS ───────────────────────────────────────────────────────

_register(
    Reagent(
        id="ethanol",
        name="Ethanol (absolut)",
        formula="C2H5OH",
        category=ReagentCategory.ORGANIC_SOLVENT,
        molar_mass_g_per_mol=46.07,
        density_g_per_ml=0.789,
        cas_number="64-17-5",
        melting_point_c=-114.0,
        boiling_point_c=78.0,
        ph=7.0,
        solubility_g_per_100ml_water=1000.0,
        default_color_rgba=_rgba(0.98, 0.99, 1.0, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs("H225", "Hocht entzündliche Flüssigkeit und Dämpfe.", "GHS02", SignalWord.DANGER, 2),
        ),
        storage_group=StorageGroup.FLAMMABLE_CABINET,
        common_uses="Lösungsmittel, Desinfektionsmittel, Extraktionsmittel",
        description="Flüchtiger organischer Lösungsmittel, entzündlich.",
    )
)

_register(
    Reagent(
        id="acetone",
        name="Aceton",
        formula="CH3COCH3",
        category=ReagentCategory.ORGANIC_SOLVENT,
        molar_mass_g_per_mol=58.08,
        density_g_per_ml=0.785,
        cas_number="67-64-1",
        melting_point_c=-95.0,
        boiling_point_c=56.0,
        ph=7.0,
        solubility_g_per_100ml_water=1000.0,
        default_color_rgba=_rgba(0.98, 0.99, 1.0, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs("H225", "Hocht entzündliche Flüssigkeit und Dämpfe.", "GHS02", SignalWord.DANGER, 2),
            _ghs("H319", "Verursacht schwere Augenreizung.", "GHS07", SignalWord.WARNING, 2),
        ),
        storage_group=StorageGroup.FLAMMABLE_CABINET,
        common_uses="Lösungsmittel, Nagellackentferner, Reinigung",
        description="Flüchtiges, entzündliches Keton-Lösungsmittel.",
    )
)

# ── ORGANIC BUILDING BLOCKS ────────────────────────────────────────────────

_register(
    Reagent(
        id="salicylic_acid",
        name="Salicylsäure",
        formula="C7H6O3",
        category=ReagentCategory.ORGANIC_SOLVENT,
        molar_mass_g_per_mol=138.12,
        density_g_per_ml=1.44,
        cas_number="69-72-7",
        melting_point_c=159.0,
        boiling_point_c=211.0,
        pka=2.97,
        ph=2.4,
        solubility_g_per_100ml_water=2.2,
        default_color_rgba=_rgba(0.98, 0.98, 0.95, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(
            _ghs("H315", "Verursacht Hautreizungen.", "GHS07", SignalWord.WARNING, 2),
            _ghs("H319", "Verursacht schwere Augenreizung.", "GHS07", SignalWord.WARNING, 2),
        ),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Vorläufer für Aspirin, Hautpflege",
        description="Ortho-hydroxybenzoesäure, Vorläufer der Aspirin-Synthese.",
    )
)

_register(
    Reagent(
        id="acetic_anhydride",
        name="Essigsäureanhydrid",
        formula="C4H6O3",
        category=ReagentCategory.ORGANIC_SOLVENT,
        molar_mass_g_per_mol=102.09,
        density_g_per_ml=1.08,
        cas_number="108-24-7",
        boiling_point_c=140.0,
        ph=7.0,
        solubility_g_per_100ml_water=2.6,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs(
                "H314",
                "Verursacht schwere Verätzungen der Haut und Augenschäden.",
                "GHS05",
                SignalWord.DANGER,
                5,
            ),
        ),
        storage_group=StorageGroup.ACID_CABINET,
        common_uses="Acetylierungsreagenz, Vorläufer für Aspirin",
        description="Wasserentziehendes Acetylierungsreagenz, ätzend.",
    )
)

_register(
    Reagent(
        id="malonic_acid",
        name="Malonsäure",
        formula="CH2(COOH)2",
        category=ReagentCategory.ORGANIC_SOLVENT,
        molar_mass_g_per_mol=104.06,
        density_g_per_ml=1.62,
        cas_number="141-82-2",
        melting_point_c=135.0,
        boiling_point_c=135.0,
        pka=2.83,
        ph=2.8,
        solubility_g_per_100ml_water=77.8,
        default_color_rgba=_rgba(0.98, 0.98, 0.98, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Substrat für Briggs-Rauscher-Reaktion",
        description="Dicarbonsäure als Kohlenstoffsubstrat für chemische Uhren.",
    )
)

_register(
    Reagent(
        id="urea",
        name="Harnstoff",
        formula="CH4N2O",
        category=ReagentCategory.NITROGEN_COMPOUND,
        molar_mass_g_per_mol=60.06,
        density_g_per_ml=1.32,
        cas_number="57-13-6",
        melting_point_c=133.0,
        boiling_point_c=132.7,
        ph=7.0,
        solubility_g_per_100ml_water=1000.0,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Dünger, Proteinhydrolyse, Biochemie",
        description="Stickstoffreiches organisches Verbindung, kristallin.",
    )
)

# ── INORGANIC CHEMISTRY SPECIALTIES ────────────────────────────────────────

_register(
    Reagent(
        id="pb_no3_2",
        name="Bleinitrat",
        formula="Pb(NO3)2",
        category=ReagentCategory.HEAVY_METAL_SALT,
        molar_mass_g_per_mol=331.2,
        density_g_per_ml=4.53,
        cas_number="10099-74-8",
        melting_point_c=271.0,
        boiling_point_c=470.0,
        ph=5.0,
        solubility_g_per_100ml_water=51.0,
        default_color_rgba=_rgba(0.98, 0.98, 1.0, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(
            _ghs(
                "H361d", "Vermutet, das Kind im Mutterleib zu schädigen.", "GHS08", SignalWord.DANGER, 2
            ),
            _ghs(
                "H410",
                "Sehr giftig für Wasserorganismen mit langfristiger Wirkung.",
                "GHS09",
                SignalWord.WARNING,
                1,
            ),
        ),
        storage_group=StorageGroup.TOXIC_SECURE,
        common_uses="Goldener Regen (Fällung), Analytische Chemie",
        description="Giftiges Schwermetallsalz für Fällungsreaktionen.",
    )
)

_register(
    Reagent(
        id="mno4_minus",
        name="Permanganat-Ionen-Lösung",
        formula="MnO4-",
        category=ReagentCategory.TRANSITION_METAL_SALT,
        molar_mass_g_per_mol=118.94,
        density_g_per_ml=1.0,
        cas_number="14412-24-9",
        ph=7.0,
        default_color_rgba=_rgba(0.5, 0.1, 0.7, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs(
                "H272", "Kann Brand intensivieren; Oxidierendes Mittel.", "GHS03", SignalWord.DANGER, 1
            ),
        ),
        storage_group=StorageGroup.OXIDIZER_STORAGE,
        common_uses="Redox-Titration, Oxidation",
        description="Violette Permanganatlösung, starkes Oxidationsmittel.",
    )
)

# ── LUMINESCENCE & OSCILLATION ─────────────────────────────────────────────

_register(
    Reagent(
        id="luminol",
        name="Luminol-Reagenz",
        formula="C8H7N3O2",
        category=ReagentCategory.NITROGEN_COMPOUND,
        molar_mass_g_per_mol=177.16,
        density_g_per_ml=1.43,
        cas_number="521-68-6",
        melting_point_c=332.0,
        ph=7.0,
        default_color_rgba=_rgba(0.85, 0.92, 0.98, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Chemilumineszenz, Forensik (Blutspuren)",
        description="Lumineszenz-Farbstoff; emittiert bei Oxidation hellblaues Licht (425 nm).",
    )
)

_register(
    Reagent(
        id="starch",
        name="Stärke-Lösung",
        formula="(C6H10O5)n",
        category=ReagentCategory.CARBOHYDRATE,
        molar_mass_g_per_mol=5000.0,
        density_g_per_ml=1.01,
        cas_number="9005-25-8",
        ph=7.0,
        solubility_g_per_100ml_water=0.1,
        default_color_rgba=_rgba(0.92, 0.92, 0.95, 1.0),
        particle_type=ParticleType.GEL_COLLOID,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Iod-Indikator, Verdickungsmittel",
        description="Indikator: bildet mit Polyiodid-Ionen einen tiefdunkelblauen Einschlusskomplex.",
    )
)

# ── WATER ──────────────────────────────────────────────────────────────────

_register(
    Reagent(
        id="water",
        name="Destilliertes Wasser",
        formula="H2O",
        category=ReagentCategory.MISCELLANEOUS,
        molar_mass_g_per_mol=18.015,
        density_g_per_ml=1.0,
        cas_number="7732-18-5",
        melting_point_c=0.0,
        boiling_point_c=100.0,
        ph=7.0,
        solubility_g_per_100ml_water=1000.0,
        default_color_rgba=_rgba(0.95, 0.98, 1.0, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Universelles Lösungsmittel",
        description="Reinstes Lösungsmittel für alle Versuchsansätze.",
    )
)

# ── GENETICS / PCR REAGENTS ────────────────────────────────────────────────

_register(
    Reagent(
        id="dna_template",
        name="DNA-Template (doppelsträngig)",
        formula="Komplexpolymere",
        category=ReagentCategory.NUCLEIC_ACID,
        molar_mass_g_per_mol=1000000.0,
        density_g_per_ml=1.7,
        cas_number=None,
        ph=7.5,
        default_color_rgba=_rgba(0.9, 0.7, 0.9, 1.0),
        particle_type=ParticleType.FIBROUS,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="PCR-Template, Klonierung, Sequenzierung",
        description="Doppelsträngige DNA als Amplifikationsvorlage für PCR.",
    )
)

_register(
    Reagent(
        id="primer_forward",
        name="PCR-Primer (Vorwärts, 20mer)",
        formula="Oligonukleotid",
        category=ReagentCategory.NUCLEIC_ACID,
        molar_mass_g_per_mol=6000.0,
        density_g_per_ml=1.7,
        cas_number=None,
        ph=7.5,
        default_color_rgba=_rgba(0.7, 0.9, 1.0, 1.0),
        particle_type=ParticleType.FIBROUS,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="PCR-Startsequenz 5'→3'",
        description="Einsträngiges Oligonukleotid, bindet an die 3'-Ende der kodierenden Strang.",
    )
)

_register(
    Reagent(
        id="primer_reverse",
        name="PCR-Primer (Rückwärts, 20mer)",
        formula="Oligonukleotid",
        category=ReagentCategory.NUCLEIC_ACID,
        molar_mass_g_per_mol=6000.0,
        density_g_per_ml=1.7,
        cas_number=None,
        ph=7.5,
        default_color_rgba=_rgba(0.7, 1.0, 0.7, 1.0),
        particle_type=ParticleType.FIBROUS,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="PCR-Startsequenz 3'←5'",
        description="Einsträngiges Oligonukleotid, bindet an die 5'-Ende der antisense Strang.",
    )
)

_register(
    Reagent(
        id="taq_polymerase",
        name="Taq-DNA-Polymerase",
        formula="Protein-Komplex",
        category=ReagentCategory.BIOLOGICAL,
        molar_mass_g_per_mol=94000.0,
        density_g_per_ml=1.35,
        cas_number="9001-50-5",
        ph=8.5,
        default_color_rgba=_rgba(0.6, 0.4, 0.8, 1.0),
        particle_type=ParticleType.FIBROUS,
        ghs_hazards=(),
        storage_group=StorageGroup.TOXIC_SECURE,
        common_uses="PCR-Enzym, Hitzestabile DNA-Synthese",
        description="Thermostabile DNA-Polymerase aus Thermus aquaticus für PCR.",
    )
)

_register(
    Reagent(
        id="dntp_mix",
        name="dNTP-Mix (dATP, dTTP, dGTP, dCTP)",
        formula="Nukleotid-Mischung",
        category=ReagentCategory.NUCLEIC_ACID,
        molar_mass_g_per_mol=500.0,
        density_g_per_ml=1.0,
        cas_number=None,
        ph=7.5,
        default_color_rgba=_rgba(1.0, 0.9, 0.7, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="PCR-Nukleotid-Bausteine",
        description="Vier desoxyribonukleotide als Bausteine für die DNA-Synthese.",
    )
)

_register(
    Reagent(
        id="pcr_buffer",
        name="PCR-Puffer (10x, mit MgCl2)",
        formula="Pufferlösung",
        category=ReagentCategory.MISCELLANEOUS,
        molar_mass_g_per_mol=100.0,
        density_g_per_ml=1.0,
        cas_number=None,
        default_color_rgba=_rgba(0.95, 0.98, 1.0, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="PCR-Reaktionsmedium",
        description="Puffer mit Magnesiumchlorid für optimale Taq-Polymerase-Aktivität.",
    )
)

_register(
    Reagent(
        id="agarose",
        name="Agarose (Elektrophorese-Grad)",
        formula="Polysaccharid",
        category=ReagentCategory.CARBOHYDRATE,
        molar_mass_g_per_mol=260000.0,
        density_g_per_ml=1.5,
        cas_number="9012-36-6",
        melting_point_c=88.0,
        boiling_point_c=None,
        ph=7.0,
        solubility_g_per_100ml_water=1.5,
        default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
        particle_type=ParticleType.POWDER_CRYSTAL,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Gelelektrophorese, DNA-Trennung",
        description="Gelbildungsmittel für DNA-Fragmenttrennung durch Elektrophorese.",
    )
)

_register(
    Reagent(
        id="tb_e_buffer",
        name="TBE-Puffer (Tris-Borat-EDTA)",
        formula="Pufferlösung",
        category=ReagentCategory.MISCELLANEOUS,
        molar_mass_g_per_mol=100.0,
        density_g_per_ml=1.0,
        cas_number=None,
        default_color_rgba=_rgba(0.95, 0.98, 1.0, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="Elektrophorese-Puffer",
        description="Leitender Puffer für Agarose-Gelelektrophorese von DNA.",
    )
)

_register(
    Reagent(
        id="ethidium_bromide",
        name="Ethidiumbromid (DNA-Färbung)",
        formula="C21H16BrN3",
        category=ReagentCategory.NITROGEN_COMPOUND,
        molar_mass_g_per_mol=394.31,
        density_g_per_ml=1.3,
        cas_number="1239-45-8",
        ph=7.0,
        default_color_rgba=_rgba(1.0, 0.9, 0.2, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(
            _ghs("H340", "Kann genetische Defekte verursachen.", "GHS08", SignalWord.DANGER, 1),
            _ghs("H350", "Kann Krebs verursachen.", "GHS08", SignalWord.DANGER, 1),
        ),
        storage_group=StorageGroup.TOXIC_SECURE,
        common_uses="DNA-Gel-Färbung, Fluoreszenzmarkierung",
        description="Mutagenes DNA-Interkalationsfarbmittel, UV-fluoreszierend.",
    )
)

_register(
    Reagent(
        id="loading_dye",
        name="DNA-Ladepuffer mit Färbemittel",
        formula="Gemisch",
        category=ReagentCategory.MISCELLANEOUS,
        molar_mass_g_per_mol=100.0,
        density_g_per_ml=1.2,
        cas_number=None,
        ph=7.0,
        default_color_rgba=_rgba(0.2, 0.6, 1.0, 1.0),
        particle_type=ParticleType.LIQUID_DROPLET,
        ghs_hazards=(),
        storage_group=StorageGroup.GENERAL_STORAGE,
        common_uses="DNA-Probenbeladung auf Gel",
        description="Dichter Ladepuffer mit Farbmarker für Gelbeladung.",
    )
)


# ── REGISTRY CONSTRUCTION ──────────────────────────────────────────────────

# Inject aliases so lookups by alternate names resolve consistently.
_REAGENTS["hydrochloric_acid"] = _REAGENTS["hcl"]
_REAGENTS["sodium_hydroxide"] = _REAGENTS["naoh"]
_REAGENTS["hydrogen_peroxide"] = _REAGENTS["h2o2"]
_REAGENTS["potassium_iodide"] = _REAGENTS["ki"]
_REAGENTS["potassium_iodate"] = _REAGENTS["kio3"]
_REAGENTS["silver_nitrate"] = _REAGENTS["agno3"]
_REAGENTS["lead_nitrate"] = _REAGENTS["pb_no3_2"]
_REAGENTS["copper_sulfate"] = _REAGENTS["cu_so4"]
_REAGENTS["iron_iii_chloride"] = _REAGENTS["fecl3"]

# Build the public frozen registry mapping.
REAGENT_REGISTRY: dict[str, Reagent] = dict(_REAGENTS)


# =============================================================================
# 4. Lookup helpers
# =============================================================================

def get_reagent(reagent_id: str) -> Reagent:
    """Retrieve chemical reagent by identifier (case-insensitive, whitespace-tolerant)."""
    rid = reagent_id.lower().strip()
    if rid not in REAGENT_REGISTRY:
        raise KeyError(f"Unknown chemical reagent: {reagent_id}")
    return REAGENT_REGISTRY[rid]


def list_reagents() -> list[Reagent]:
    """Return all registered reagents in deterministic insertion order."""
    return list(REAGENT_REGISTRY.values())


def search_by_formula(formula: str) -> list[Reagent]:
    """Return reagents whose molecular formula matches (case-insensitive substring)."""
    needle = formula.lower().strip()
    return [r for r in REAGENT_REGISTRY.values() if needle in r.formula.lower()]


def search_by_category(category: ReagentCategory) -> list[Reagent]:
    """Return all reagents belonging to the given category."""
    return [r for r in REAGENT_REGISTRY.values() if r.category == category]


def count_by_category() -> dict[str, int]:
    """Return number of reagents per category (useful for audit/UI counters)."""
    counts: dict[str, int] = {}
    for reagent in REAGENT_REGISTRY.values():
        counts[reagent.category.value] = counts.get(reagent.category.value, 0) + 1
    return counts


# =============================================================================
# 5. Legacy-compatible ReagentCatalog class (simulation/catalog.py API)
# =============================================================================

# Legacy Enum aliases that match simulation/catalog.py exactly.
ReagentCategoryLegacy = ReagentCategory  # same StrEnum values


class ReagentCatalog:
    """Complete chemical reagent catalog for Free Simulation Mode."""

    def __init__(self):
        self._reagents_by_id: dict[str, Reagent] = {r.id: r for r in _REAGENTS}

    def get_all(self) -> list[Reagent]:
        return list(self._reagents_by_id.values())

    def get_categories(self) -> list[ReagentCategory]:
        return list({r.category for r in self._reagents_by_id.values()})

    def get_by_id(self, reagent_id: str) -> Reagent | None:
        return self._reagents_by_id.get(reagent_id)

    def filter_by_category(self, category: ReagentCategory) -> list[Reagent]:
        return [r for r in self._reagents_by_id.values() if r.category == category]

    def search(self, query: str) -> list[Reagent]:
        q = query.strip().lower()
        results = []
        for r in self._reagents_by_id.values():
            if (
                q in r.name.lower()
                or q in r.formula.lower()
                or q in r.id.lower()
                or q in r.common_uses.lower()
            ):
                results.append(r)
        return results


# =============================================================================
# 6. Legacy-compatible GHS / ChemicalProfile API (safety_simulation/ghs.py API)
# =============================================================================

# Master Chemical Catalog for the Laboratory Simulation (legacy ChemicalProfile format)
CHEMICAL_DATABASE: dict[str, ChemicalProfile] = {}


def _legacy_pictogram(code: str) -> GHSPictogramLegacy:
    """Map a canonical GHS pictogram code to the legacy Enum variant."""
    mapping = {
        "GHS01_EXPLODING_BOMB": GHSPictogramLegacy.GHS01_EXPLODING_BOMB,
        "GHS02_FLAME": GHSPictogramLegacy.GHS02_FLAME,
        "GHS03_FLAME_OVER_CIRCLE": GHSPictogramLegacy.GHS03_FLAME_OVER_CIRCLE,
        "GHS04_GAS_CYLINDER": GHSPictogramLegacy.GHS04_GAS_CYLINDER,
        "GHS05_CORROSION": GHSPictogramLegacy.GHS05_CORROSION,
        "GHS06_SKULL_CROSSBONES": GHSPictogramLegacy.GHS06_SKULL_AND_CROSSBONES,
        "GHS07_EXCLAMATION_MARK": GHSPictogramLegacy.GHS07_EXCLAMATION_MARK,
        "GHS08_HEALTH_HAZARD": GHSPictogramLegacy.GHS08_HEALTH_HAZARD,
        "GHS09_ENVIRONMENT": GHSPictogramLegacy.GHS09_ENVIRONMENT,
    }
    return mapping[code]


def _legacy_hazard_class(ghs_class_name: str) -> GHSClassLegacy:
    mapping = {
        "EXPLOSIVE": GHSClassLegacy.EXPLOSIVE,
        "FLAMMABLE": GHSClassLegacy.FLAMMABLE,
        "OXIDIZING": GHSClassLegacy.OXIDIZING,
        "COMPRESSED_GAS": GHSClassLegacy.COMPRESSED_GAS,
        "CORROSIVE": GHSClassLegacy.CORROSIVE,
        "TOXIC": GHSClassLegacy.TOXIC,
        "HARMFUL_IRRITANT": GHSClassLegacy.HARMFUL_IRRITANT,
        "HEALTH_HAZARD": GHSClassLegacy.HEALTH_HAZARD,
        "ENVIRONMENTAL": GHSClassLegacy.ENVIRONMENTAL,
    }
    return mapping[ghs_class_name]


# Build CHEMICAL_DATABASE from REAGENT_REGISTRY where possible, plus legacy-only entries.
# Entries that exist only in the legacy ghs.py (chlorine, autoignition temps, etc.) are added here.
def _build_legacy_database() -> dict[str, ChemicalProfile]:
    db: dict[str, ChemicalProfile] = {}
    for reagent in REAGENT_REGISTRY.values():
        hazard_classes: set[GHSClassLegacy] = set()
        pictograms: list[GHSPictogramLegacy] = []
        for hazard in reagent.ghs_hazards:
            try:
                hazard_classes.add(_legacy_hazard_class(hazard.pictogram.split("_")[0].upper()))
            except KeyError:
                pass
            try:
                pictograms.append(_legacy_pictogram(hazard.pictogram))
            except KeyError:
                pass
        # Derive acid/base flags from category
        is_acid = reagent.category == ReagentCategory.ACID
        is_base = reagent.category == ReagentCategory.BASE
        db[reagent.id] = ChemicalProfile(
            id=reagent.id,
            name=reagent.name,
            formula=reagent.formula,
            cas_number=reagent.cas_number or "",
            molar_mass=reagent.molar_mass_g_per_mol,
            density=reagent.density_g_per_ml,
            boiling_point_c=reagent.boiling_point_c if reagent.boiling_point_c is not None else 0.0,
            flash_point_c=None,
            vapor_pressure_kpa_20c=0.0,
            is_volatile=False,
            is_acid=is_acid,
            is_base=is_base,
            acid_pka=reagent.pka,
            hazard_classes=hazard_classes,
            signal_word=reagent.ghs_hazards[0].signal_word if reagent.ghs_hazards else SignalWord.NONE,
            pictograms=pictograms,
            h_statements=list(reagent.hazard_statements),
            p_statements=[],
            storage_group=reagent.storage_group,
            incompatible_with=[],
            antoine_coefficients=(0.0, 0.0, 0.0),
        )
    return db


CHEMICAL_DATABASE = _build_legacy_database()


def check_chemical_compatibility(chem_a_id: str, chem_b_id: str) -> IncompatibilityResult:
    """
    Evaluates mutual chemical compatibility between two substances according to
    EPA Chemical Reactivity Worksheet standards and NOAA CAMEO logic.
    """
    if chem_a_id == chem_b_id:
        return IncompatibilityResult(compatible=True, risk_level="NONE")

    chem_a = CHEMICAL_DATABASE.get(chem_a_id)
    chem_b = CHEMICAL_DATABASE.get(chem_b_id)

    if not chem_a or not chem_b:
        raise ValueError(f"Unknown chemical ID: {chem_a_id if not chem_a else chem_b_id}")

    direct_conflict = (chem_b_id in chem_a.incompatible_with) or (chem_a_id in chem_b.incompatible_with)

    has_oxidizer = (GHSClassLegacy.OXIDIZING in chem_a.hazard_classes) or (GHSClassLegacy.OXIDIZING in chem_b.hazard_classes)
    has_flammable = (GHSClassLegacy.FLAMMABLE in chem_a.hazard_classes) or (GHSClassLegacy.FLAMMABLE in chem_b.hazard_classes)
    if has_oxidizer and has_flammable:
        return IncompatibilityResult(
            compatible=False,
            risk_level="CRITICAL",
            reaction_type="EXPLOSIVE_OXIDATION",
            hazard_description=(
                f"Severe fire and detonation danger: Oxidizer ({chem_a.name if GHSClassLegacy.OXIDIZING in chem_a.hazard_classes else chem_b.name}) "
                f"violently reacts with flammable solvent ({chem_b.name if GHSClassLegacy.FLAMMABLE in chem_b.hazard_classes else chem_a.name})."
            ),
            byproducts=["Thermal blast wave", "Carbon monoxide", "Dense smoke", "Flaming projectiles"]
        )

    if (chem_a.is_acid and chem_b.is_base) or (chem_a.is_base and chem_b.is_acid):
        if chem_a_id == "sodium_bicarbonate" or chem_b_id == "sodium_bicarbonate":
            return IncompatibilityResult(
                compatible=True,
                risk_level="LOW",
                reaction_type="CONTROLLED_NEUTRALIZATION",
                hazard_description="Controlled stoichiometric neutralization. Moderate effervescence (CO2 gas) and mild temperature rise.",
                byproducts=["CO2(g)", "H2O", "Salt precipitate"]
            )
        return IncompatibilityResult(
            compatible=False,
            risk_level="SEVERE",
            reaction_type="VIOLENT_EXOTHERMIC_NEUTRALIZATION",
            hazard_description=(
                f"Dangerous rapid heat release and boiling: {chem_a.name} mixed with {chem_b.name}. "
                "Can cause explosive steam eruption and corrosive aerosol splattering."
            ),
            byproducts=["Superheated steam", "Corrosive caustic mist"]
        )

    if (chem_a_id == "potassium_permanganate" and chem_b_id in ["sulfuric_acid", "hydrochloric_acid"]) or \
       (chem_b_id == "potassium_permanganate" and chem_a_id in ["sulfuric_acid", "hydrochloric_acid"]):
        return IncompatibilityResult(
            compatible=False,
            risk_level="CRITICAL",
            reaction_type="EXPLOSIVE_MANGANESE_HEPTAOXIDE_FORMATION",
            hazard_description=(
                "Mixing Potassium Permanganate with concentrated acid creates Manganese Heptoxide (Mn2O7), "
                "an unstable explosive dark green oil that detonates spontaneously or emits toxic chlorine gas."
            ),
            byproducts=["Mn2O7 (unstable explosive)", "Cl2 gas (with HCl)", "Toxic heavy metal mist"]
        )

    if chem_a.storage_group != chem_b.storage_group:
        if (chem_a.storage_group == StorageGroup.FLAMMABLE_CABINET and chem_b.storage_group in [StorageGroup.ACID_CABINET, StorageGroup.OXIDIZER_STORAGE]) or \
           (chem_b.storage_group == StorageGroup.FLAMMABLE_CABINET and chem_a.storage_group in [StorageGroup.ACID_CABINET, StorageGroup.OXIDIZER_STORAGE]):
            return IncompatibilityResult(
                compatible=False,
                risk_level="MODERATE",
                reaction_type="STORAGE_SEGREGATION_VIOLATION",
                hazard_description=f"Storage violation: {chem_a.name} ({chem_a.storage_group.value}) must not be co-located with {chem_b.name} ({chem_b.storage_group.value}).",
                byproducts=[]
            )

    if direct_conflict:
        return IncompatibilityResult(
            compatible=False,
            risk_level="SEVERE",
            reaction_type="INCOMPATIBLE_REAGENTS",
            hazard_description=f"Incompatible reagents: {chem_a.name} and {chem_b.name} react adversely.",
            byproducts=[]
        )

    return IncompatibilityResult(compatible=True, risk_level="NONE")


def get_chemical_sds(chemical_id: str) -> dict[str, object]:
    """Generates an OSHA 16-section compliant summary Safety Data Sheet (SDS)."""
    chem = CHEMICAL_DATABASE.get(chemical_id)
    if not chem:
        raise ValueError(f"Chemical {chemical_id} not found.")

    return {
        "section_1_identification": {
            "product_name": chem.name,
            "chemical_formula": chem.formula,
            "cas_number": chem.cas_number
        },
        "section_2_hazard_identification": {
            "signal_word": chem.signal_word.value,
            "hazard_classes": [c.value for c in chem.hazard_classes],
            "pictograms": [p.value for p in chem.pictograms],
            "hazard_statements": chem.h_statements,
            "precautionary_statements": chem.p_statements
        },
        "section_9_physical_chemical_properties": {
            "boiling_point_c": chem.boiling_point_c,
            "flash_point_c": chem.flash_point_c,
            "vapor_pressure_kpa_20c": chem.vapor_pressure_kpa_20c,
            "density_g_cm3": chem.density,
            "is_volatile": chem.is_volatile
        },
        "section_10_stability_reactivity": {
            "incompatibilities": chem.incompatible_with,
            "storage_class": chem.storage_group.value
        }
    }

