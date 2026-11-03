"""
GHS Hazard Classification & Chemical Safety Layer
Compliant with Globally Harmonized System of Classification and Labelling of Chemicals (GHS Rev 10)
and OSHA Hazard Communication Standard (29 CFR 1910.1200).
"""

from dataclasses import dataclass, field
from enum import Enum


class GHSClass(str, Enum):
    """GHS Hazard Classes."""
    EXPLOSIVE = "EXPLOSIVE"
    FLAMMABLE = "FLAMMABLE"
    OXIDIZING = "OXIDIZING"
    COMPRESSED_GAS = "COMPRESSED_GAS"
    CORROSIVE = "CORROSIVE"
    TOXIC = "TOXIC"
    HARMFUL_IRRITANT = "HARMFUL_IRRITANT"
    HEALTH_HAZARD = "HEALTH_HAZARD"
    ENVIRONMENTAL = "ENVIRONMENTAL"


class GHSPictogram(str, Enum):
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


class SignalWord(str, Enum):
    """GHS Signal Words."""
    DANGER = "DANGER"
    WARNING = "WARNING"
    NONE = "NONE"


class StorageGroup(str, Enum):
    """Segregated chemical storage classes."""
    FLAMMABLE_CABINET = "FLAMMABLE_CABINET"
    ACID_CABINET = "ACID_CABINET"
    BASE_CABINET = "BASE_CABINET"
    OXIDIZER_STORAGE = "OXIDIZER_STORAGE"
    GENERAL_STORAGE = "GENERAL_STORAGE"
    TOXIC_SECURE = "TOXIC_SECURE"


@dataclass
class GHSHazardStatement:
    code: str
    ghs_class: GHSClass
    category: int
    text: str
    pictogram: GHSPictogram
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
    hazard_classes: set[GHSClass] = field(default_factory=set)
    signal_word: SignalWord = SignalWord.NONE
    pictograms: list[GHSPictogram] = field(default_factory=list)
    h_statements: list[str] = field(default_factory=list)
    p_statements: list[str] = field(default_factory=list)
    storage_group: StorageGroup = StorageGroup.GENERAL_STORAGE
    incompatible_with: list[str] = field(default_factory=list)
    antoine_coefficients: tuple[float, float, float] = (0.0, 0.0, 0.0)  # (A, B, C) for log10(P_mmHg) = A - B/(T+C)

    def calculate_vapor_pressure_kpa(self, temp_c: float) -> float:
        """Calculate vapor pressure using Antoine equation in kPa."""
        a, b, c = self.antoine_coefficients
        if a == 0.0:
            # Fallback estimation using Clausius-Clapeyron approximation
            delta_t = temp_c - 20.0
            return max(0.01, self.vapor_pressure_kpa_20c * (2.0 ** (delta_t / 10.0)))
        # Antoine returns mmHg: log10(P) = A - B / (T + C)
        log10_p_mmhg = a - (b / (temp_c + c))
        p_mmhg = 10.0 ** log10_p_mmhg
        # 1 mmHg = 0.133322 kPa
        return max(0.01, p_mmhg * 0.133322)


# Master Chemical Catalog for the Laboratory Simulation
CHEMICAL_DATABASE: dict[str, ChemicalProfile] = {
    "hydrochloric_acid": ChemicalProfile(
        id="hydrochloric_acid",
        name="Hydrochloric Acid 37%",
        formula="HCl(aq)",
        cas_number="7647-01-0",
        molar_mass=36.46,
        density=1.19,
        boiling_point_c=108.6,
        flash_point_c=None,
        vapor_pressure_kpa_20c=16.0,
        is_volatile=True,
        is_acid=True,
        acid_pka=-6.3,
        hazard_classes={GHSClass.CORROSIVE, GHSClass.TOXIC},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS05_CORROSION, GHSPictogram.GHS06_SKULL_CROSSBONES],
        h_statements=[
            "H314: Causes severe skin burns and eye damage",
            "H335: May cause respiratory irritation",
            "H290: May be corrosive to metals"
        ],
        p_statements=[
            "P260: Do not breathe dust/fume/gas/mist/vapours/spray",
            "P280: Wear protective gloves/clothing/eye protection/face protection",
            "P301+P330+P331: IF SWALLOWED: Rinse mouth. Do NOT induce vomiting"
        ],
        storage_group=StorageGroup.ACID_CABINET,
        incompatible_with=["sodium_hydroxide", "sodium_hypochlorite", "potassium_permanganate", "metals"],
        antoine_coefficients=(7.33, 1356.0, 247.0)
    ),
    "sulfuric_acid": ChemicalProfile(
        id="sulfuric_acid",
        name="Sulfuric Acid 96%",
        formula="H2SO4",
        cas_number="7664-93-9",
        molar_mass=98.08,
        density=1.84,
        boiling_point_c=337.0,
        flash_point_c=None,
        vapor_pressure_kpa_20c=0.001,
        is_volatile=False,
        is_acid=True,
        acid_pka=-3.0,
        hazard_classes={GHSClass.CORROSIVE, GHSClass.HEALTH_HAZARD},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS05_CORROSION, GHSPictogram.GHS08_HEALTH_HAZARD],
        h_statements=[
            "H314: Causes severe skin burns and eye damage",
            "H290: May be corrosive to metals"
        ],
        p_statements=[
            "P260: Do not breathe mist or vapor",
            "P280: Wear acid-resistant gloves, apron and face shield",
            "P305+P351+P338: IF IN EYES: Rinse cautiously with water for several minutes"
        ],
        storage_group=StorageGroup.ACID_CABINET,
        incompatible_with=["sodium_hydroxide", "potassium_permanganate", "acetone", "ethanol", "water_shock"],
        antoine_coefficients=(6.0, 1900.0, 190.0)
    ),
    "nitric_acid": ChemicalProfile(
        id="nitric_acid",
        name="Nitric Acid 68%",
        formula="HNO3",
        cas_number="7697-37-2",
        molar_mass=63.01,
        density=1.41,
        boiling_point_c=83.0,
        flash_point_c=None,
        vapor_pressure_kpa_20c=6.4,
        is_volatile=True,
        is_acid=True,
        acid_pka=-1.4,
        hazard_classes={GHSClass.OXIDIZING, GHSClass.CORROSIVE, GHSClass.TOXIC},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS03_FLAME_OVER_CIRCLE, GHSPictogram.GHS05_CORROSION, GHSPictogram.GHS06_SKULL_CROSSBONES],
        h_statements=[
            "H272: May intensify fire; oxidizer",
            "H314: Causes severe skin burns and eye damage",
            "H330: Fatal if inhaled"
        ],
        p_statements=[
            "P220: Keep away from clothing and other combustible materials",
            "P260: Do not breathe dust/fume/gas/mist/vapours/spray",
            "P284: In case of inadequate ventilation wear respiratory protection"
        ],
        storage_group=StorageGroup.OXIDIZER_STORAGE,
        incompatible_with=["acetone", "ethanol", "diethyl_ether", "sodium_hydroxide", "metals"],
        antoine_coefficients=(7.43, 1400.0, 220.0)
    ),
    "sodium_hydroxide": ChemicalProfile(
        id="sodium_hydroxide",
        name="Sodium Hydroxide 1M / Solid Pellets",
        formula="NaOH",
        cas_number="1310-73-2",
        molar_mass=40.00,
        density=2.13,
        boiling_point_c=1388.0,
        flash_point_c=None,
        vapor_pressure_kpa_20c=0.0,
        is_volatile=False,
        is_base=True,
        hazard_classes={GHSClass.CORROSIVE},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS05_CORROSION],
        h_statements=[
            "H314: Causes severe skin burns and eye damage",
            "H290: May be corrosive to metals"
        ],
        p_statements=[
            "P280: Wear protective gloves and eye protection",
            "P301+P330+P331: IF SWALLOWED: Rinse mouth. Do NOT induce vomiting"
        ],
        storage_group=StorageGroup.BASE_CABINET,
        incompatible_with=["hydrochloric_acid", "sulfuric_acid", "nitric_acid", "aluminum"],
        antoine_coefficients=(0.0, 0.0, 0.0)
    ),
    "acetone": ChemicalProfile(
        id="acetone",
        name="Acetone ACS Grade",
        formula="C3H6O",
        cas_number="67-64-1",
        molar_mass=58.08,
        density=0.791,
        boiling_point_c=56.05,
        flash_point_c=-20.0,
        autoignition_temp_c=465.0,
        vapor_pressure_kpa_20c=24.6,
        is_volatile=True,
        hazard_classes={GHSClass.FLAMMABLE, GHSClass.HARMFUL_IRRITANT},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS02_FLAME, GHSPictogram.GHS07_EXCLAMATION_MARK],
        h_statements=[
            "H225: Highly flammable liquid and vapour",
            "H319: Causes serious eye irritation",
            "H336: May cause drowsiness or dizziness"
        ],
        p_statements=[
            "P210: Keep away from heat, hot surfaces, sparks, open flames",
            "P233: Keep container tightly closed",
            "P305+P351+P338: IF IN EYES: Rinse cautiously with water"
        ],
        storage_group=StorageGroup.FLAMMABLE_CABINET,
        incompatible_with=["nitric_acid", "sulfuric_acid", "hydrogen_peroxide", "potassium_permanganate"],
        antoine_coefficients=(7.02447, 1161.0, 224.0)
    ),
    "ethanol": ChemicalProfile(
        id="ethanol",
        name="Ethanol Absolute 99.8%",
        formula="C2H5OH",
        cas_number="64-17-5",
        molar_mass=46.07,
        density=0.789,
        boiling_point_c=78.24,
        flash_point_c=13.0,
        autoignition_temp_c=363.0,
        vapor_pressure_kpa_20c=5.95,
        is_volatile=True,
        hazard_classes={GHSClass.FLAMMABLE, GHSClass.HARMFUL_IRRITANT},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS02_FLAME, GHSPictogram.GHS07_EXCLAMATION_MARK],
        h_statements=[
            "H225: Highly flammable liquid and vapour",
            "H319: Causes serious eye irritation"
        ],
        p_statements=[
            "P210: Keep away from heat, hot surfaces, sparks, open flames",
            "P280: Wear eye protection and gloves"
        ],
        storage_group=StorageGroup.FLAMMABLE_CABINET,
        incompatible_with=["nitric_acid", "potassium_permanganate", "hydrogen_peroxide"],
        antoine_coefficients=(8.04494, 1554.3, 222.65)
    ),
    "diethyl_ether": ChemicalProfile(
        id="diethyl_ether",
        name="Diethyl Ether Anhydrous",
        formula="(C2H5)2O",
        cas_number="60-29-7",
        molar_mass=74.12,
        density=0.713,
        boiling_point_c=34.6,
        flash_point_c=-45.0,
        autoignition_temp_c=160.0,
        vapor_pressure_kpa_20c=58.9,
        is_volatile=True,
        hazard_classes={GHSClass.FLAMMABLE, GHSClass.HARMFUL_IRRITANT},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS02_FLAME, GHSPictogram.GHS07_EXCLAMATION_MARK],
        h_statements=[
            "H224: Extremely flammable liquid and vapour",
            "H302: Harmful if swallowed",
            "H336: May cause drowsiness or dizziness"
        ],
        p_statements=[
            "P210: Keep away from heat/sparks/open flames/hot surfaces. - No smoking",
            "P240: Ground and bond container and receiving equipment",
            "P403+P235: Store in a well-ventilated place. Keep cool"
        ],
        storage_group=StorageGroup.FLAMMABLE_CABINET,
        incompatible_with=["nitric_acid", "potassium_permanganate", "hydrogen_peroxide", "air_prolonged"],
        antoine_coefficients=(6.92032, 1064.07, 228.8)
    ),
    "hydrogen_peroxide": ChemicalProfile(
        id="hydrogen_peroxide",
        name="Hydrogen Peroxide 35% Technical",
        formula="H2O2",
        cas_number="7722-84-1",
        molar_mass=34.01,
        density=1.13,
        boiling_point_c=108.0,
        flash_point_c=None,
        vapor_pressure_kpa_20c=0.2,
        is_volatile=False,
        hazard_classes={GHSClass.OXIDIZING, GHSClass.CORROSIVE, GHSClass.HARMFUL_IRRITANT},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS03_FLAME_OVER_CIRCLE, GHSPictogram.GHS05_CORROSION],
        h_statements=[
            "H272: May intensify fire; oxidizer",
            "H314: Causes severe skin burns and eye damage",
            "H302: Harmful if swallowed"
        ],
        p_statements=[
            "P220: Keep/Store away from clothing/combustible materials",
            "P280: Wear protective gloves/protective clothing/eye protection"
        ],
        storage_group=StorageGroup.OXIDIZER_STORAGE,
        incompatible_with=["acetone", "ethanol", "diethyl_ether", "potassium_permanganate", "copper_sulfate"],
        antoine_coefficients=(7.85, 1850.0, 219.0)
    ),
    "potassium_permanganate": ChemicalProfile(
        id="potassium_permanganate",
        name="Potassium Permanganate Crystalline",
        formula="KMnO4",
        cas_number="7722-64-7",
        molar_mass=158.03,
        density=2.70,
        boiling_point_c=240.0,
        flash_point_c=None,
        vapor_pressure_kpa_20c=0.0,
        is_volatile=False,
        hazard_classes={GHSClass.OXIDIZING, GHSClass.HARMFUL_IRRITANT, GHSClass.ENVIRONMENTAL},
        signal_word=SignalWord.DANGER,
        pictograms=[GHSPictogram.GHS03_FLAME_OVER_CIRCLE, GHSPictogram.GHS07_EXCLAMATION_MARK, GHSPictogram.GHS09_ENVIRONMENT],
        h_statements=[
            "H272: May intensify fire; oxidizer",
            "H302: Harmful if swallowed",
            "H410: Very toxic to aquatic life with long lasting effects"
        ],
        p_statements=[
            "P220: Keep away from combustible materials",
            "P273: Avoid release to the environment"
        ],
        storage_group=StorageGroup.OXIDIZER_STORAGE,
        incompatible_with=["sulfuric_acid", "hydrochloric_acid", "acetone", "ethanol", "glycerol"],
        antoine_coefficients=(0.0, 0.0, 0.0)
    ),
    "sodium_bicarbonate": ChemicalProfile(
        id="sodium_bicarbonate",
        name="Sodium Bicarbonate Powder (Neutralizer)",
        formula="NaHCO3",
        cas_number="144-55-8",
        molar_mass=84.01,
        density=2.20,
        boiling_point_c=851.0,
        flash_point_c=None,
        vapor_pressure_kpa_20c=0.0,
        is_volatile=False,
        is_base=True,
        hazard_classes=set(),
        signal_word=SignalWord.NONE,
        pictograms=[],
        h_statements=[],
        p_statements=["P264: Wash hands thoroughly after handling"],
        storage_group=StorageGroup.GENERAL_STORAGE,
        incompatible_with=[],
        antoine_coefficients=(0.0, 0.0, 0.0)
    ),
    "copper_sulfate": ChemicalProfile(
        id="copper_sulfate",
        name="Copper(II) Sulfate Pentahydrate",
        formula="CuSO4 * 5H2O",
        cas_number="7758-99-8",
        molar_mass=249.68,
        density=2.28,
        boiling_point_c=150.0,
        flash_point_c=None,
        vapor_pressure_kpa_20c=0.0,
        is_volatile=False,
        hazard_classes={GHSClass.HARMFUL_IRRITANT, GHSClass.CORROSIVE, GHSClass.ENVIRONMENTAL},
        signal_word=SignalWord.WARNING,
        pictograms=[GHSPictogram.GHS05_CORROSION, GHSPictogram.GHS07_EXCLAMATION_MARK, GHSPictogram.GHS09_ENVIRONMENT],
        h_statements=[
            "H302: Harmful if swallowed",
            "H318: Causes serious eye damage",
            "H410: Very toxic to aquatic life with long lasting effects"
        ],
        p_statements=[
            "P273: Avoid release to the environment",
            "P280: Wear eye protection and gloves"
        ],
        storage_group=StorageGroup.GENERAL_STORAGE,
        incompatible_with=["strong_reducing_agents", "hydroxylamine"],
        antoine_coefficients=(0.0, 0.0, 0.0)
    ),
    "chlorine": ChemicalProfile(
        id="chlorine",
        name="Chlorine Compressed Gas",
        formula="Cl2",
        cas_number="7782-50-5",
        molar_mass=70.90,
        density=3.21,
        boiling_point_c=-34.04,
        flash_point_c=None,
        vapor_pressure_kpa_20c=680.0,
        is_volatile=True,
        hazard_classes={GHSClass.COMPRESSED_GAS, GHSClass.OXIDIZING, GHSClass.TOXIC, GHSClass.CORROSIVE, GHSClass.ENVIRONMENTAL},
        signal_word=SignalWord.DANGER,
        pictograms=[
            GHSPictogram.GHS03_FLAME_OVER_CIRCLE,
            GHSPictogram.GHS04_GAS_CYLINDER,
            GHSPictogram.GHS05_CORROSION,
            GHSPictogram.GHS06_SKULL_CROSSBONES,
            GHSPictogram.GHS09_ENVIRONMENT
        ],
        h_statements=[
            "H270: May cause or intensify fire; oxidizer",
            "H280: Contains gas under pressure; may explode if heated",
            "H330: Fatal if inhaled",
            "H314: Causes severe skin burns and eye damage"
        ],
        p_statements=[
            "P220: Keep away from clothing and other combustible materials",
            "P260: Do not breathe gas",
            "P284: In case of inadequate ventilation wear respiratory protection"
        ],
        storage_group=StorageGroup.TOXIC_SECURE,
        incompatible_with=["ammonia", "flammable_solvents", "metals"],
        antoine_coefficients=(6.867, 861.34, 246.33)
    )
}


@dataclass
class IncompatibilityResult:
    compatible: bool
    risk_level: str  # "NONE", "LOW", "MODERATE", "SEVERE", "CRITICAL"
    reaction_type: str | None = None
    hazard_description: str | None = None
    byproducts: list[str] = field(default_factory=list)


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

    # Check explicit incompatible lists
    direct_conflict = (chem_b_id in chem_a.incompatible_with) or (chem_a_id in chem_b.incompatible_with)

    # 1. Oxidizer + Flammable / Organic (Explosive / Deflagration hazard)
    has_oxidizer = (GHSClass.OXIDIZING in chem_a.hazard_classes) or (GHSClass.OXIDIZING in chem_b.hazard_classes)
    has_flammable = (GHSClass.FLAMMABLE in chem_a.hazard_classes) or (GHSClass.FLAMMABLE in chem_b.hazard_classes)
    if has_oxidizer and has_flammable:
        return IncompatibilityResult(
            compatible=False,
            risk_level="CRITICAL",
            reaction_type="EXPLOSIVE_OXIDATION",
            hazard_description=(
                f"Severe fire and detonation danger: Oxidizer ({chem_a.name if GHSClass.OXIDIZING in chem_a.hazard_classes else chem_b.name}) "
                f"violently reacts with flammable solvent ({chem_b.name if GHSClass.FLAMMABLE in chem_b.hazard_classes else chem_a.name})."
            ),
            byproducts=["Thermal blast wave", "Carbon monoxide", "Dense smoke", "Flaming projectiles"]
        )

    # 2. Strong Acid + Strong Base (Violent Exothermic Neutralization / Splashing)
    if (chem_a.is_acid and chem_b.is_base) or (chem_a.is_base and chem_b.is_acid):
        # Neutralization with NaHCO3 is controlled; with NaOH it is violently boiling
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

    # 3. Acid + Oxidizing salt (e.g., KMnO4 + H2SO4 -> Mn2O7 explosive oil)
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

    # 4. Storage Segregation Violations
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
