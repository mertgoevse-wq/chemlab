"""
ChemLab Procedural Open-World Laboratory Matrix & Quest Generator.
Generates dynamic facilities with physical environmental scaling, resident NPCs,
equipment inventories, reagent caches, and procedural quest chains across diverse
scientific and clandestine archetypes:
  • Clandestine Underground Labs (covert synthesis, improvised glassware, volatile hazards)
  • Industrial Pharmaceutical Plants (GMP validation, HPLC, automated pilot reactors)
  • CRISPR Biotechnology Laboratories (Cas9 gene editing, BSL-2/BSL-3, cleanroom incubators)
  • Academic Research Departments (Schlenk lines, multi-step organic total synthesis)
  • Orbital Zero-G Research Modules (microgravity capillary fluidics, crystal growth)
  • Extreme Planetary Outposts (Martian/Venusian/Cryogenic atmospheric containment)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

from chemlab.sandbox.no_mans_sky_matrix import (
    HazardDifficulty,
    LaboratoryEnvironmentMatrix,
    PlanetaryPreset,
)


class LabType(StrEnum):
    """Architectural and functional archetypes of laboratories in the open world."""

    CLANDESTINE_UNDERGROUND = "clandestine_underground"
    INDUSTRIAL_PHARMA = "industrial_pharma"
    CRISPR_BIOTECH = "crispr_biotech"
    ACADEMIC_RESEARCH = "academic_research"
    ORBITAL_ZERO_G = "orbital_zero_g"
    EXTREME_PLANETARY = "extreme_planetary"


class NPCRole(StrEnum):
    """Specialized scientific and operational roles for laboratory NPCs."""

    CHIEF_SCIENTIST = "chief_scientist"
    COVERT_OPERATOR = "covert_operator"
    CONTRABAND_CHEMIST = "contraband_chemist"
    FACILITY_FIXER = "facility_fixer"
    QA_AUDITOR = "qa_auditor"
    GENETIC_ENGINEER = "genetic_engineer"
    POSTDOC_RESEARCHER = "postdoc_researcher"
    STATION_COMMANDER = "station_commander"


class QuestCategory(StrEnum):
    """Categorization for laboratory quest chains."""

    COVERT_SYNTHESIS = "covert_synthesis"
    GMP_VALIDATION = "gmp_validation"
    GENETIC_ENGINEERING = "genetic_engineering"
    ACADEMIC_DISCOVERY = "academic_discovery"
    ZERO_G_PHYSICS = "zero_g_physics"
    PLANETARY_SURVIVAL = "planetary_survival"


@dataclass
class LabEquipment:
    """Specialized analytical or synthetic apparatus present in a laboratory."""

    equipment_id: str
    name: str
    tier: str  # standard, industrial, cleanroom, improvised
    condition: float = 1.0  # 0.0 (broken) to 1.0 (pristine)
    cleanliness: float = 1.0  # 0.0 (contaminated) to 1.0 (sterile)
    features: list[str] = field(default_factory=list)


@dataclass
class LabNPC:
    """Resident non-player character with dialogue trees, trade inventory, and reputation."""

    npc_id: str
    name: str
    role: NPCRole
    reputation: float = 50.0  # 0.0 (hostile) to 100.0 (trusted ally)
    dialog_lines: list[str] = field(default_factory=list)
    trade_inventory: dict[str, float] = field(default_factory=dict)  # reagent_id -> stock_quantity

    @property
    def reputation_tier(self) -> str:
        """Categorizes current player reputation with this NPC."""
        if self.reputation < 20.0:
            return "hostile"
        if self.reputation < 40.0:
            return "suspicious"
        if self.reputation < 60.0:
            return "neutral"
        if self.reputation < 80.0:
            return "friendly"
        return "trusted"

    def adjust_reputation(self, delta: float) -> None:
        """Modulates player reputation within bounds [0.0, 100.0]."""
        self.reputation = max(0.0, min(100.0, self.reputation + delta))

    def get_random_dialog(self) -> str:
        """Returns a random dialogue line appropriate for the character."""
        if not self.dialog_lines:
            return f"Hallo. Ich bin {self.name}."
        return random.choice(self.dialog_lines)

    def buy_reagent(self, reagent_id: str, amount: float) -> tuple[bool, str]:
        """Processes player purchasing reagents from this NPC's inventory."""
        available = self.trade_inventory.get(reagent_id, 0.0)
        if available < amount:
            return False, f"Unzureichender Vorrat an {reagent_id} (Verfügbar: {available:.1f}g/mL)."
        self.trade_inventory[reagent_id] = round(available - amount, 2)
        return True, f"{amount:.1f} von {reagent_id} erfolgreich erworben."


@dataclass
class LabQuestObjective:
    """Quantitative objective criteria for completing a laboratory quest."""

    target_compound: str
    min_purity_percent: float = 90.0
    min_yield_grams: float = 5.0
    requires_fume_hood: bool = False
    max_temperature_c: float | None = None
    min_temperature_c: float | None = None


@dataclass
class LabQuest:
    """Procedurally generated or narrative quest offered by laboratory facilities."""

    quest_id: str
    title: str
    category: QuestCategory
    briefing: str
    objective: LabQuestObjective
    reward_reputation: float = 10.0
    reward_credits: float = 200.0
    completed: bool = False

    def evaluate_submission(
        self,
        compound: str,
        purity_percent: float,
        yield_grams: float,
        used_fume_hood: bool = False,
        observed_temp_c: float = 25.0,
    ) -> tuple[bool, str]:
        """
        Evaluates a submitted player reaction product against the quest objective.
        """
        # Compound match
        if compound.lower() != self.objective.target_compound.lower():
            return (
                False,
                f"Falsche Zielverbindung: Erhalten '{compound}', gefordert '{self.objective.target_compound}'.",
            )

        # Safety compliance
        if self.objective.requires_fume_hood and not used_fume_hood:
            return (
                False,
                "Sicherheitsverstoß: Reaktion wurde nicht im vorgeschriebenen Abzug durchgeführt!",
            )

        # Purity check
        if purity_percent < self.objective.min_purity_percent:
            return (
                False,
                f"Reinheit unzureichend: {purity_percent:.1f}% erzielt, mindestens {self.objective.min_purity_percent:.1f}% gefordert.",
            )

        # Yield check
        if yield_grams < self.objective.min_yield_grams:
            return (
                False,
                f"Ausbeute zu gering: {yield_grams:.1f}g erzielt, mindestens {self.objective.min_yield_grams:.1f}g gefordert.",
            )

        # Temperature constraints
        if self.objective.max_temperature_c and observed_temp_c > self.objective.max_temperature_c:
            return (
                False,
                f"Temperaturüberschreitung: {observed_temp_c:.1f}°C überschreitet Maximum von {self.objective.max_temperature_c:.1f}°C.",
            )

        self.completed = True
        return (
            True,
            f"Erfolgreich abgeschlossen! '{self.title}' erfüllt. Belohnung: {self.reward_reputation} Ruf, {self.reward_credits} Credits.",
        )


@dataclass
class ProceduralLab:
    """Comprehensive representation of a procedurally generated laboratory facility."""

    lab_id: str
    name: str
    lab_type: LabType
    room_count: int
    security_level: str
    gmp_certified: bool
    biosafety_level: int
    environment: LaboratoryEnvironmentMatrix
    equipment: list[LabEquipment] = field(default_factory=list)
    reagent_cache: dict[str, float] = field(default_factory=dict)
    npcs: list[LabNPC] = field(default_factory=list)
    quests: list[LabQuest] = field(default_factory=list)


class ProceduralLabGenerator:
    """
    Deterministic procedural generator for laboratories across all archetypes.
    Generates authentic layouts, environmental matrices, NPC inhabitants, and quests.
    """

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_lab(
        self,
        lab_type: LabType,
        name_override: str | None = None,
        environment_override: LaboratoryEnvironmentMatrix | None = None,
    ) -> ProceduralLab:
        """Generates a complete laboratory facility of the requested archetype."""
        lab_id = f"lab_{self.rng.randint(1000, 9999)}_{lab_type.value[:4]}"

        # Name and physical layout
        name = name_override or self._generate_lab_name(lab_type)
        room_count = self._get_room_count(lab_type)
        security_level = self._get_security_level(lab_type)
        gmp_certified = lab_type == LabType.INDUSTRIAL_PHARMA
        biosafety_level = 3 if lab_type == LabType.CRISPR_BIOTECH else 1

        # Environment Matrix
        environment = environment_override or self._generate_environment(lab_type)

        # Equipment & Reagents
        equipment = self._generate_equipment(lab_type)
        reagents = self._generate_reagent_cache(lab_type)

        # NPCs & Quests
        npcs = self._generate_npcs(lab_type)
        quests = self._generate_quests(lab_type)

        return ProceduralLab(
            lab_id=lab_id,
            name=name,
            lab_type=lab_type,
            room_count=room_count,
            security_level=security_level,
            gmp_certified=gmp_certified,
            biosafety_level=biosafety_level,
            environment=environment,
            equipment=equipment,
            reagent_cache=reagents,
            npcs=npcs,
            quests=quests,
        )

    def _generate_lab_name(self, lab_type: LabType) -> str:
        prefixes = {
            LabType.CLANDESTINE_UNDERGROUND: [
                "Bunker-",
                "Keller-Sektor ",
                "Subterra-",
                "Verlassene Werkstatt ",
            ],
            LabType.INDUSTRIAL_PHARMA: [
                "Synthetica GMP-Werk ",
                "Aeterna Pharmazeutik ",
                "BioPharma Batch-Unit ",
                "Helix Pharma ",
            ],
            LabType.CRISPR_BIOTECH: [
                "Cas9 GeneCore ",
                "Vektor-Genetik ",
                "CellEdit BioLabs ",
                "CRISPR-Transgen-Station ",
            ],
            LabType.ACADEMIC_RESEARCH: [
                "Institut für Organische Chemie ",
                "Fakultätslabor-",
                "Lehrstuhl-Synthesezentrum ",
                "Universitäts-Cluster ",
            ],
            LabType.ORBITAL_ZERO_G: [
                "Orbital-Labor Alpha-",
                "Zero-G Fluid-Modul ",
                "Mir-Station Experiment-Deck ",
                "ISS-Kompensationsmodul ",
            ],
            LabType.EXTREME_PLANETARY: [
                "Elysium Planitia Outpost ",
                "Venusian Cloud Station ",
                "Ishtar Hyperbaric Lab ",
                "Titan Cryo-Vault ",
            ],
        }
        num = self.rng.randint(1, 99)
        prefix = self.rng.choice(prefixes.get(lab_type, ["Labor "]))
        return f"{prefix}{num}"

    def _get_room_count(self, lab_type: LabType) -> int:
        counts = {
            LabType.CLANDESTINE_UNDERGROUND: self.rng.randint(1, 3),
            LabType.INDUSTRIAL_PHARMA: self.rng.randint(6, 14),
            LabType.CRISPR_BIOTECH: self.rng.randint(4, 8),
            LabType.ACADEMIC_RESEARCH: self.rng.randint(3, 7),
            LabType.ORBITAL_ZERO_G: self.rng.randint(2, 5),
            LabType.EXTREME_PLANETARY: self.rng.randint(3, 6),
        }
        return counts.get(lab_type, 3)

    def _get_security_level(self, lab_type: LabType) -> str:
        levels = {
            LabType.CLANDESTINE_UNDERGROUND: self.rng.choice(
                ["clandestine_covert", "improvised", "reinforced_bunker"]
            ),
            LabType.INDUSTRIAL_PHARMA: "high_security_gmp",
            LabType.CRISPR_BIOTECH: "biosafety_containment",
            LabType.ACADEMIC_RESEARCH: "campus_card_access",
            LabType.ORBITAL_ZERO_G: "airlock_sealed_station",
            LabType.EXTREME_PLANETARY: "hyperbaric_airlock",
        }
        return levels.get(lab_type, "standard")

    def _generate_environment(self, lab_type: LabType) -> LaboratoryEnvironmentMatrix:
        if lab_type == LabType.ORBITAL_ZERO_G:
            return LaboratoryEnvironmentMatrix.from_preset(PlanetaryPreset.ORBITAL_ZERO_G)
        if lab_type == LabType.EXTREME_PLANETARY:
            return LaboratoryEnvironmentMatrix.from_preset(PlanetaryPreset.MARTIAN_SURFACE)
        if lab_type == LabType.CLANDESTINE_UNDERGROUND:
            return LaboratoryEnvironmentMatrix(
                gravity_g=1.0,
                ambient_pressure_atm=1.0,
                ambient_temperature_c=16.0,  # Cold damp basement
                hazard_difficulty=HazardDifficulty.HARDCORE_REALISTIC,
            )
        return LaboratoryEnvironmentMatrix.from_preset(PlanetaryPreset.EARTH_STANDARD)

    def _generate_equipment(self, lab_type: LabType) -> list[LabEquipment]:
        eq_list: list[LabEquipment] = []

        if lab_type == LabType.CLANDESTINE_UNDERGROUND:
            eq_list.extend(
                [
                    LabEquipment(
                        "eq_fume_imp",
                        "Improvised Fume Vent / Aktivkohle-Abzug",
                        "improvised",
                        condition=0.7,
                        features=["suction_exhaust"],
                    ),
                    LabEquipment(
                        "eq_flask_set",
                        "Borosilikat-Rundkolben 1000ml mit Liebig-Kühler",
                        "standard",
                        condition=0.85,
                        features=["distillation"],
                    ),
                    LabEquipment(
                        "eq_hotplate",
                        "Heizplatte mit Magnetrührer",
                        "standard",
                        condition=0.65,
                        features=["magnetic_stir"],
                    ),
                ]
            )
        elif lab_type == LabType.INDUSTRIAL_PHARMA:
            eq_list.extend(
                [
                    LabEquipment(
                        "eq_hplc",
                        "Hochleistungs-Flüssigchromatograph (HPLC-DAD)",
                        "industrial",
                        condition=1.0,
                        features=["purity_analysis", "retention_time"],
                    ),
                    LabEquipment(
                        "eq_reactor",
                        "Automatisierter 50L Glasschwing-Reaktor mit Kryo-Mantel",
                        "industrial",
                        condition=0.98,
                        features=["jacket_cooling", "temp_cascade"],
                    ),
                    LabEquipment(
                        "eq_mass_spec",
                        "Triple-Quadrupol Massenspektrometer (LC-MS)",
                        "industrial",
                        condition=0.95,
                        features=["molecular_weight"],
                    ),
                ]
            )
        elif lab_type == LabType.CRISPR_BIOTECH:
            eq_list.extend(
                [
                    LabEquipment(
                        "eq_pcr",
                        "Eppendorf Mastercycler PCR-Thermocycler",
                        "cleanroom",
                        condition=1.0,
                        features=["dna_amplification"],
                    ),
                    LabEquipment(
                        "eq_flow",
                        "Laminar Flow Reinraum-Werkbank Klasse II",
                        "cleanroom",
                        condition=0.99,
                        features=["sterile_air", "hepa_filtration"],
                    ),
                    LabEquipment(
                        "eq_incubator",
                        "CO2-Inkubator mit Schüttelplattform",
                        "cleanroom",
                        condition=0.95,
                        features=["cell_culture"],
                    ),
                ]
            )
        elif lab_type == LabType.ORBITAL_ZERO_G:
            eq_list.extend(
                [
                    LabEquipment(
                        "eq_acoustic_lev",
                        "Akustischer 3D-Schwebemischer (Levitator)",
                        "space_grade",
                        condition=1.0,
                        features=["contactless_mixing"],
                    ),
                    LabEquipment(
                        "eq_capillary",
                        "Kapillar-Fluid-Transfer-Einheit",
                        "space_grade",
                        condition=1.0,
                        features=["zero_g_pour"],
                    ),
                ]
            )
        else:
            eq_list.extend(
                [
                    LabEquipment(
                        "eq_fume_hood",
                        "Labor-Sicherheitsabzug DIN EN 14175",
                        "standard",
                        condition=0.9,
                        features=["fume_exhaust", "sash_window"],
                    ),
                    LabEquipment(
                        "eq_schlenk",
                        "Schlenk-Vakuum-Inertgas-Linie (Argon)",
                        "standard",
                        condition=0.9,
                        features=["inert_atmosphere"],
                    ),
                ]
            )

        return eq_list

    def _generate_reagent_cache(self, lab_type: LabType) -> dict[str, float]:
        if lab_type == LabType.CLANDESTINE_UNDERGROUND:
            return {
                "toluene": 1500.0,
                "benzaldehyde": 400.0,
                "nitroethane": 250.0,
                "acetic_acid": 800.0,
                "h2so4": 300.0,
            }
        if lab_type == LabType.INDUSTRIAL_PHARMA:
            return {
                "salicylic_acid": 5000.0,
                "acetic_anhydride": 5000.0,
                "aminophenol": 3500.0,
                "ethanol": 10000.0,
                "water": 50000.0,
            }
        if lab_type == LabType.CRISPR_BIOTECH:
            return {
                "cas9_nuclease": 50.0,
                "sgrna_pool": 20.0,
                "dna_buffer": 2000.0,
                "agarose": 500.0,
                "gfp_plasmid": 100.0,
            }
        return {
            "water": 5000.0,
            "hcl": 1000.0,
            "naoh": 1000.0,
            "ethanol": 2000.0,
            "universal_indicator": 100.0,
        }

    def _generate_npcs(self, lab_type: LabType) -> list[LabNPC]:
        npcs: list[LabNPC] = []
        if lab_type == LabType.CLANDESTINE_UNDERGROUND:
            npcs.append(
                LabNPC(
                    npc_id=f"npc_{self.rng.randint(100, 999)}_walter",
                    name=self.rng.choice(
                        ["Walter Blackwood", "Viktor 'Kolben' Morozov", "Rusty Miller"]
                    ),
                    role=NPCRole.CONTRABAND_CHEMIST,
                    reputation=35.0,
                    dialog_lines=[
                        "Pass auf die Säuredämpfe auf – die Abluft zieht heute schlecht.",
                        "Reine Vorstufen sind schwer zu finden. Was bringst du mit?",
                        "Niemals Wasser in die konzentrierte Säure schütten, merk dir das!",
                    ],
                    trade_inventory={
                        "nitroethane": 200.0,
                        "benzaldehyde": 350.0,
                        "toluene": 1000.0,
                    },
                )
            )
            npcs.append(
                LabNPC(
                    npc_id=f"npc_{self.rng.randint(100, 999)}_fixer",
                    name=self.rng.choice(["Milo", "Klara", "Spike"]),
                    role=NPCRole.FACILITY_FIXER,
                    reputation=45.0,
                    dialog_lines=["Ich besorge dir jedes Schliffglas, wenn der Preis stimmt."],
                    trade_inventory={"h2so4": 500.0, "acetic_acid": 600.0},
                )
            )
        elif lab_type == LabType.INDUSTRIAL_PHARMA:
            npcs.append(
                LabNPC(
                    npc_id=f"npc_{self.rng.randint(100, 999)}_qa",
                    name="Ingenieur Keller",
                    role=NPCRole.QA_AUDITOR,
                    reputation=60.0,
                    dialog_lines=[
                        "Jede Charge wird per HPLC auditiert. Unter 99.5% Reinheit geht hier nichts durch.",
                        "GMP-Protokolle müssen lückenlos dokumentiert werden.",
                    ],
                    trade_inventory={"salicylic_acid": 2000.0, "aminophenol": 1500.0},
                )
            )
        elif lab_type == LabType.CRISPR_BIOTECH:
            npcs.append(
                LabNPC(
                    npc_id=f"npc_{self.rng.randint(100, 999)}_crispr",
                    name="Dr. Aris Thorne",
                    role=NPCRole.GENETIC_ENGINEER,
                    reputation=65.0,
                    dialog_lines=[
                        "Cas9 schneidet mit Basenpaar-Präzision. Kontamination im Puffer zerstört das gesamte Experiment.",
                        "Laminar Flow eingeschaltet lassen – wir arbeiten hier mit lebenden Vektoren.",
                    ],
                    trade_inventory={"dna_buffer": 500.0, "agarose": 250.0},
                )
            )
        else:
            npcs.append(
                LabNPC(
                    npc_id=f"npc_{self.rng.randint(100, 999)}_chief",
                    name="Prof. Dr. Hartmann",
                    role=NPCRole.CHIEF_SCIENTIST,
                    reputation=50.0,
                    dialog_lines=["Saubere Arbeit am Kolben ist die halbe Ausbeute."],
                    trade_inventory={"water": 5000.0, "ethanol": 1000.0},
                )
            )
        return npcs

    def _generate_quests(self, lab_type: LabType) -> list[LabQuest]:
        quests: list[LabQuest] = []

        if lab_type == LabType.CLANDESTINE_UNDERGROUND:
            quests.append(
                LabQuest(
                    quest_id=f"q_cov_{self.rng.randint(100, 999)}",
                    title="Improvisierte Benzaldehyd-Destillation",
                    category=QuestCategory.COVERT_SYNTHESIS,
                    briefing="Destilliere Benzaldehyd aus Toluol-Vorstufen unter Ausschluss von sauren Dämpfen.",
                    objective=LabQuestObjective(
                        target_compound="benzaldehyde",
                        min_purity_percent=85.0,
                        min_yield_grams=15.0,
                        requires_fume_hood=True,
                    ),
                    reward_reputation=15.0,
                    reward_credits=450.0,
                )
            )
        elif lab_type == LabType.INDUSTRIAL_PHARMA:
            quests.append(
                LabQuest(
                    quest_id=f"q_gmp_{self.rng.randint(100, 999)}",
                    title="GMP-Validierungscharge: Reinst-Aspirin",
                    category=QuestCategory.GMP_VALIDATION,
                    briefing="Führe die Veresterung von Salicylsäure mit Essigsäureanhydrid durch. HPLC fordert mindestens 98% Reinheit.",
                    objective=LabQuestObjective(
                        target_compound="aspirin",
                        min_purity_percent=98.0,
                        min_yield_grams=25.0,
                        requires_fume_hood=True,
                        max_temperature_c=85.0,  # Prevent tarring!
                    ),
                    reward_reputation=25.0,
                    reward_credits=1200.0,
                )
            )
        elif lab_type == LabType.CRISPR_BIOTECH:
            quests.append(
                LabQuest(
                    quest_id=f"q_gen_{self.rng.randint(100, 999)}",
                    title="CRISPR-Cas9 Zielknocking von GFP",
                    category=QuestCategory.GENETIC_ENGINEERING,
                    briefing="Komplexiere Cas9-Nuklease mit zielspezifischer sgRNA zur Inaktivierung des fluoreszierenden GFP-Plasmids.",
                    objective=LabQuestObjective(
                        target_compound="gfp_knockout_construct",
                        min_purity_percent=92.0,
                        min_yield_grams=1.0,
                        requires_fume_hood=False,
                    ),
                    reward_reputation=30.0,
                    reward_credits=1500.0,
                )
            )
        elif lab_type == LabType.ORBITAL_ZERO_G:
            quests.append(
                LabQuest(
                    quest_id=f"q_zg_{self.rng.randint(100, 999)}",
                    title="Kristallisation in Schwerelosigkeit",
                    category=QuestCategory.ZERO_G_PHYSICS,
                    briefing="Züchte makellose Kristalle unter Ausschluss von sedimentärer Konvektion in der 0.0g Umlaufbahn.",
                    objective=LabQuestObjective(
                        target_compound="lead_iodide",
                        min_purity_percent=95.0,
                        min_yield_grams=5.0,
                    ),
                    reward_reputation=20.0,
                    reward_credits=800.0,
                )
            )
        else:
            quests.append(
                LabQuest(
                    quest_id=f"q_acad_{self.rng.randint(100, 999)}",
                    title="Baeyer-Synthese von Indigo-Pigment",
                    category=QuestCategory.ACADEMIC_DISCOVERY,
                    briefing="Synthetisiere blaues Indigo durch Kondensation von o-Nitrobenzaldehyd mit Aceton in Gegenwart von Natronlauge.",
                    objective=LabQuestObjective(
                        target_compound="indigo",
                        min_purity_percent=90.0,
                        min_yield_grams=8.0,
                    ),
                    reward_reputation=15.0,
                    reward_credits=600.0,
                )
            )

        return quests


class WorldMatrixHub:
    """
    Central hub managing the open-world laboratory universe.
    Allows players to select their starting laboratory, procedural expansion,
    multiplayer laboratory registry, and unified environmental physics.
    """

    def __init__(self, player_name: str = "Player") -> None:
        self.player_name = player_name
        self.player_lab: ProceduralLab | None = None
        self.discovered_labs: dict[str, ProceduralLab] = {}
        self.generator = ProceduralLabGenerator(seed=1337)

    def setup_player_starting_lab(
        self,
        lab_type: LabType,
        lab_name: str | None = None,
        environment_override: LaboratoryEnvironmentMatrix | None = None,
    ) -> ProceduralLab:
        """
        Allows the player to configure their personal starting laboratory facility.
        """
        lab = self.generator.generate_lab(
            lab_type=lab_type,
            name_override=lab_name,
            environment_override=environment_override,
        )
        self.player_lab = lab
        self.discovered_labs[lab.lab_id] = lab
        return lab

    def discover_nearby_labs(self, count: int = 4) -> list[ProceduralLab]:
        """
        Populates the open world around the player with diverse neighboring facilities.
        """
        all_types = list(LabType)
        new_labs: list[ProceduralLab] = []

        for i in range(count):
            chosen_type = all_types[i % len(all_types)]
            lab = self.generator.generate_lab(chosen_type)
            self.discovered_labs[lab.lab_id] = lab
            new_labs.append(lab)

        return new_labs

    def get_available_world_quests(self) -> list[LabQuest]:
        """Collects all pending quests across all discovered laboratories."""
        quests: list[LabQuest] = []
        for lab in self.discovered_labs.values():
            quests.extend([q for q in lab.quests if not q.completed])
        return quests
