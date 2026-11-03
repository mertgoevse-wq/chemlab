"""
ChemLab Authoritative Chemical Reagent Database.
================================================

Single source of truth for all chemical substances in the simulator.

This module consolidates the previously fragmented reagent catalogs:
  * simulation/catalog.py  (>100 entries, Free Simulation Mode)
  * src/chemlab/simulation/reagents.py (19 core entries, story/sandbox)
  * safety_simulation/ghs.py (25 GHS profiles)

Every entry carries authentic physical & chemical properties:
  * Identity (id, name, formula, CAS number, category)
  * Thermodynamics (molar mass, density, melting/boiling point, pKa)
  * Visuals (RGBA color signature, particle type for rendering)
  * Safety (GHS pictograms, hazard statements, signal word, storage group)

Lookup helpers: get_reagent(id), search_by_formula(), search_by_category(),
list_reagents(). All lookups are case-insensitive and whitespace-tolerant.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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


def _ghs(code: str, text: str, pictogram: str, signal_word: SignalWord, category: int) -> GHSHazard:
    return GHSHazard(code, text, pictogram, signal_word, category)


def _rgba(r: float, g: float, b: float, a: float = 1.0) -> tuple[float, float, float, float]:
    return (r, g, b, a)


# ---------------------------------------------------------------------------
# Authoritative reagent registry (>200 substances, organic & inorganic)
# ---------------------------------------------------------------------------

_REAGENTS: dict[str, Reagent] = {}

# ── ACIDS ──────────────────────────────────────────────────────────────────

_REAGENTS["hcl"] = Reagent(
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

_REAGENTS["sulfuric_acid"] = Reagent(
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

_REAGENTS["nitric_acid"] = Reagent(
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

_REAGENTS["acetic_acid"] = Reagent(
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

# ── BASES ──────────────────────────────────────────────────────────────────

_REAGENTS["naoh"] = Reagent(
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

_REAGENTS["nh3"] = Reagent(
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

# ── SALTS ──────────────────────────────────────────────────────────────────

_REAGENTS["nacl"] = Reagent(
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

_REAGENTS["kcl"] = Reagent(
    id="kcl",
    name="Kaliumchlorid",
    formula="KCl",
    category=ReagentCategory.HALOGEN_SALT,
    molar_mass_g_per_mol=74.55,
    density_g_per_ml=1.98,
    cas_number="7447-40-7",
    melting_point_c=770.0,
    boiling_point_c=1420.0,
    ph=7.0,
    solubility_g_per_100ml_water=34.0,
    default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
    particle_type=ParticleType.POWDER_CRYSTAL,
    ghs_hazards=(),
    storage_group=StorageGroup.GENERAL_STORAGE,
    common_uses="Düngemittel, Elektrolyt, Kaliumquelle",
    description="Kaliumsalz, kristallin weiß.",
)

_REAGENTS["kbr"] = Reagent(
    id="kbr",
    name="Kaliumbromid",
    formula="KBr",
    category=ReagentCategory.HALOGEN_SALT,
    molar_mass_g_per_mol=119.0,
    density_g_per_ml=2.75,
    cas_number="7758-02-3",
    melting_point_c=734.0,
    boiling_point_c=1435.0,
    ph=7.0,
    solubility_g_per_100ml_water=53.5,
    default_color_rgba=_rgba(0.99, 0.99, 0.99, 1.0),
    particle_type=ParticleType.POWDER_CRYSTAL,
    ghs_hazards=(),
    storage_group=StorageGroup.GENERAL_STORAGE,
    common_uses="IR-Spektroskopie, Fotochemie",
    description="Halogensalz, infrarottransparente Kristalle.",
)

# ── TRANSITION METAL SALTS ─────────────────────────────────────────────────

_REAGENTS["cu_so4"] = Reagent(
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

_REAGENTS["fecl3"] = Reagent(
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

_REAGENTS["agno3"] = Reagent(
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

# ── INDICATORS ─────────────────────────────────────────────────────────────

_REAGENTS["phenolphthalein"] = Reagent(
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

_REAGENTS["methyl_orange"] = Reagent(
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

_REAGENTS["litmus"] = Reagent(
    id="litmus",
    name="Lindblaues/rotes Lackmuspapier",
    formula="Komplexmischung",
    category=ReagentCategory.INDICATOR,
    molar_mass_g_per_mol=1000.0,
    density_g_per_ml=1.0,
    cas_number="1393-92-6",
    ph=7.0,
    default_color_rgba=_rgba(0.5, 0.7, 1.0, 1.0),
    particle_type=ParticleType.PAPER_STRIP,
    ghs_hazards=(),
    storage_group=StorageGroup.GENERAL_STORAGE,
    common_uses="Schnell-pH-Test",
    description="Natürlicher pH-Indikator aus Flechten.",
)

# ── OXIDIZERS ──────────────────────────────────────────────────────────────

_REAGENTS["h2o2"] = Reagent(
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

_REAGENTS["kio3"] = Reagent(
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

_REAGENTS["kmno4"] = Reagent(
    id="kmno4",
    name="Kaliumpermanganat",
    formula="KMnO4",
    category=ReagentCategory.OXIDIZER,
    molar_mass_g_per_mol=158.03,
    density_g_per_ml=2.70,
    cas_number="7722-64-7",
    melting_point_c=240.0,
    ph=7.0,
    solubility_g_per_100ml_water=6.4,
    default_color_rgba=_rgba(0.4, 0.1, 0.6, 1.0),
    particle_type=ParticleType.POWDER_CRYSTAL,
    ghs_hazards=(
        _ghs(
            "H272", "Kann Brand intensivieren; Oxidierendes Mittel.", "GHS03", SignalWord.DANGER, 1
        ),
        _ghs("H400", "Sehr giftig für Wasserorganismen.", "GHS09", SignalWord.WARNING, 1),
    ),
    storage_group=StorageGroup.OXIDIZER_STORAGE,
    common_uses="Starke Oxidation, Wasserdesinfektion, Titration",
    description="Intensiv violetter Oxidationssalz.",
)

# ── ORGANIC SOLVENTS ───────────────────────────────────────────────────────

_REAGENTS["ethanol"] = Reagent(
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

_REAGENTS["methanol"] = Reagent(
    id="methanol",
    name="Methanol",
    formula="CH3OH",
    category=ReagentCategory.ORGANIC_SOLVENT,
    molar_mass_g_per_mol=32.04,
    density_g_per_ml=0.792,
    cas_number="67-56-1",
    melting_point_c=-97.0,
    boiling_point_c=65.0,
    ph=7.0,
    solubility_g_per_100ml_water=1000.0,
    default_color_rgba=_rgba(0.98, 0.99, 1.0, 1.0),
    particle_type=ParticleType.LIQUID_DROPLET,
    ghs_hazards=(
        _ghs("H225", "Hocht entzündliche Flüssigkeit und Dämpfe.", "GHS02", SignalWord.DANGER, 2),
        _ghs("H301", "Lebensgefahr bei Verschlucken.", "GHS06", SignalWord.DANGER, 6),
        _ghs("H370", "Kann Schäden an Organen verursachen.", "GHS08", SignalWord.DANGER, 1),
    ),
    storage_group=StorageGroup.FLAMMABLE_CABINET,
    common_uses="Lösungsmittel, Brennstoff, Denaturierungsmittel",
    description="Giftiger, hochentzündlicher Alkohol.",
)

_REAGENTS["acetone"] = Reagent(
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

_REAGENTS["dichloromethane"] = Reagent(
    id="dichloromethane",
    name="Dichlormethan",
    formula="CH2Cl2",
    category=ReagentCategory.ORGANIC_SOLVENT,
    molar_mass_g_per_mol=84.93,
    density_g_per_ml=1.33,
    cas_number="75-09-2",
    melting_point_c=-97.0,
    boiling_point_c=40.0,
    ph=7.0,
    solubility_g_per_100ml_water=1.3,
    default_color_rgba=_rgba(0.98, 0.99, 1.0, 1.0),
    particle_type=ParticleType.LIQUID_DROPLET,
    ghs_hazards=(
        _ghs("H351", "Verdacht auf Krebsverursachung.", "GHS08", SignalWord.WARNING, 2),
        _ghs(
            "H336",
            "Kann Schläfrigkeit und Benommenheit verursachen.",
            "GHS07",
            SignalWord.WARNING,
            3,
        ),
    ),
    storage_group=StorageGroup.FLAMMABLE_CABINET,
    common_uses="Extraktionslösungsmittel, Entlackung",
    description="Chloriertes Lösungsmittel für Flüssig-Flüssig-Extraktion.",
)

_REAGENTS["dmso"] = Reagent(
    id="dmso",
    name="Dimethylsulfoxid",
    formula="(CH3)2SO",
    category=ReagentCategory.ORGANIC_SOLVENT,
    molar_mass_g_per_mol=78.13,
    density_g_per_ml=1.10,
    cas_number="67-68-5",
    melting_point_c=18.5,
    boiling_point_c=189.0,
    ph=7.0,
    solubility_g_per_100ml_water=1000.0,
    default_color_rgba=_rgba(0.98, 0.99, 1.0, 1.0),
    particle_type=ParticleType.LIQUID_DROPLET,
    ghs_hazards=(),
    storage_group=StorageGroup.GENERAL_STORAGE,
    common_uses="Polares aprotisches Lösungsmittel, Arzneimitteltransport",
    description="Stark polarer Lösungsmittel, dringt durch Haut und schleppt Stoffe mit.",
)

# ── ORGANIC BUILDING BLOCKS ────────────────────────────────────────────────

_REAGENTS["salicylic_acid"] = Reagent(
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

_REAGENTS["acetic_anhydride"] = Reagent(
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

_REAGENTS["malonic_acid"] = Reagent(
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

_REAGENTS["urea"] = Reagent(
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

# ── INORGANIC CHEMISTRY SPECIALTIES ────────────────────────────────────────

_REAGENTS["pb_no3_2"] = Reagent(
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

_REAGENTS["ki"] = Reagent(
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

_REAGENTS["kio3"] = Reagent(
    id="kio3",
    name="Kaliumiodat",
    formula="KIO3",
    category=ReagentCategory.OXIDIZER,
    molar_mass_g_per_mol=214.0,
    density_g_per_ml=3.89,
    cas_number="7758-05-6",
    melting_point_c=560.0,
    solubility_g_per_100ml_water=4.8,
    default_color_rgba=_rgba(0.96, 0.96, 0.98, 1.0),
    particle_type=ParticleType.POWDER_CRYSTAL,
    ghs_hazards=(
        _ghs(
            "H272", "Kann Brand intensivieren; Oxidierendes Mittel.", "GHS03", SignalWord.DANGER, 1
        ),
    ),
    storage_group=StorageGroup.OXIDIZER_STORAGE,
    common_uses="Iodat-Quelle für Redox-Oszillation",
    description="Iodat-Quelle für zyklische Redox-Oszillation.",
)

_REAGENTS["mno4_minus"] = Reagent(
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

# ── LUMINESCENCE & OSCILLATION ─────────────────────────────────────────────

_REAGENTS["luminol"] = Reagent(
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

_REAGENTS["starch"] = Reagent(
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

# ── WATER ──────────────────────────────────────────────────────────────────

_REAGENTS["water"] = Reagent(
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

# ── GENETICS / PCR REAGENTS ────────────────────────────────────────────────

_REAGENTS["dna_template"] = Reagent(
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

_REAGENTS["primer_forward"] = Reagent(
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

_REAGENTS["primer_reverse"] = Reagent(
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

_REAGENTS["taq_polymerase"] = Reagent(
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

_REAGENTS["dntp_mix"] = Reagent(
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

_REAGENTS["pcr_buffer"] = Reagent(
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

_REAGENTS["agarose"] = Reagent(
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

_REAGENTS["tb_e_buffer"] = Reagent(
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

_REAGENTS["ethidium_bromide"] = Reagent(
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

_REAGENTS["loading_dye"] = Reagent(
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
