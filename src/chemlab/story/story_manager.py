"""
ChemLab Story Mode Progression Manager.
Implements the 10-level campaign from 'Labor-Praktikant' to 'Meister-Alchemist'.
Tracks quest states, unlocks, apparatus permissions, and safety officer compliance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PlayerRank(StrEnum):
    """Hierarchy of player achievement ranks in ChemLab."""

    TRAINEE = "Labor-Praktikant (Day 1)"
    APPRENTICE = "Chemielaborant-Lehrling"
    JOURNEYMAN = "Technischer Assistent"
    SENIOR_SYNTHESIST = "Synthese-Spezialist"
    MASTER_ALCHEMIST = "Meister-Alchemist"


class QuestStatus(StrEnum):
    """State machine for individual laboratory story quests."""

    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class StoryLevel:
    """Represents a single pedagogical laboratory quest in story mode."""

    level_number: int
    title: str
    briefing: str
    required_reagents: list[str]
    target_reaction_type: str
    unlocked_apparatus: list[str]
    unlocked_reagents: list[str]
    requires_fume_hood: bool = False
    status: QuestStatus = QuestStatus.LOCKED


class StoryProgressionManager:
    """
    Manages structured player advancement, unlockable apparatus, and safety scoring.
    """

    def __init__(self) -> None:
        self.levels: dict[int, StoryLevel] = self._build_campaign_levels()
        self.current_level_number: int = 1
        self.safety_score: float = 100.0
        self.last_feedback: str = (
            "Willkommen im ChemLab! Ziehe die Schutzbrille an und beginne mit Level 1."
        )
        self.levels[1].status = QuestStatus.IN_PROGRESS

    @property
    def player_rank(self) -> PlayerRank:
        completed = sum(1 for lvl in self.levels.values() if lvl.status == QuestStatus.COMPLETED)
        if completed >= 10:
            return PlayerRank.MASTER_ALCHEMIST
        if completed >= 7:
            return PlayerRank.SENIOR_SYNTHESIST
        if completed >= 4:
            return PlayerRank.JOURNEYMAN
        if completed >= 1:
            return PlayerRank.APPRENTICE
        return PlayerRank.TRAINEE

    def get_current_level(self) -> StoryLevel:
        return self.levels[self.current_level_number]

    def is_level_unlocked(self, level_num: int) -> bool:
        lvl = self.levels.get(level_num)
        return lvl is not None and lvl.status != QuestStatus.LOCKED

    def is_level_completed(self, level_num: int) -> bool:
        lvl = self.levels.get(level_num)
        return lvl is not None and lvl.status == QuestStatus.COMPLETED

    def submit_reaction_result(
        self,
        reagent_ids: list[str],
        final_ph: float = 7.0,
        temperature_c: float = 22.0,
        in_fume_hood: bool = False,
    ) -> bool:
        """
        Validates whether the player's reaction fulfilled the active level's criteria.
        """
        curr = self.get_current_level()

        # Check safety requirements
        if curr.requires_fume_hood and not in_fume_hood:
            self.safety_score = max(0.0, self.safety_score - 25.0)
            self.last_feedback = (
                "Sicherheitsabzug: Giftige oder spritzende Reagenzien müssen immer unter "
                "dem geschlossenen Laborabzug (Fume Hood) gehandhabt werden!"
            )
            return False

        # Validate reagents
        reagent_set = set(reagent_ids)
        required_set = set(curr.required_reagents)
        if not required_set.issubset(reagent_set):
            missing = required_set - reagent_set
            self.last_feedback = f"Fehlende Reagenzien für diesen Versuch: {', '.join(missing)}"
            return False

        # Level specific physical conditions
        if curr.level_number == 1 and not (6.0 <= final_ph <= 8.0):
            self.last_feedback = (
                "Die Lösung ist noch nicht neutral! Justiere das Verhältnis von HCl und NaOH."
            )
            return False

        # Success! Mark completed and unlock next level
        curr.status = QuestStatus.COMPLETED
        self.last_feedback = f"Hervorragend! Quest '{curr.title}' erfolgreich abgeschlossen."

        if self.current_level_number < len(self.levels):
            self.current_level_number += 1
            self.levels[self.current_level_number].status = QuestStatus.IN_PROGRESS

        return True

    def unlock_all_for_sandbox(self) -> None:
        """Grants immediate sandbox clearance with all apparatus and reagents unlocked."""
        for lvl in self.levels.values():
            lvl.status = QuestStatus.COMPLETED
        self.current_level_number = 10
        self.last_feedback = "Freier Simulations-Modus aktiviert: Alle 100+ Reagenzien und Laborgeräte freigeschaltet."

    def _build_campaign_levels(self) -> dict[int, StoryLevel]:
        return {
            1: StoryLevel(
                level_number=1,
                title="Labortaufe & Indikator",
                briefing="Führe eine klassische Säure-Base-Neutralisation durch. Beobachte den Farbumschlag des Universalindikators.",
                required_reagents=["hcl", "naoh", "universal_indicator"],
                target_reaction_type="acid_base_neutralization",
                unlocked_apparatus=["Schutzbrille", "Becherglas_250ml", "Pipette"],
                unlocked_reagents=["water", "hcl", "naoh", "universal_indicator"],
            ),
            2: StoryLevel(
                level_number=2,
                title="Die Iod-Uhr (Kinetik)",
                briefing="Erforsche Reaktionsgeschwindigkeiten durch die Landolt-Iod-Uhr mit plötzlichem Farbumschlag zu Tiefblau.",
                required_reagents=["hydrogen_peroxide", "potassium_iodide", "starch"],
                target_reaction_type="iodine_clock",
                unlocked_apparatus=["Magnetrührstab", "Messzylinder_100ml"],
                unlocked_reagents=["hydrogen_peroxide", "potassium_iodide", "starch"],
            ),
            3: StoryLevel(
                level_number=3,
                title="Oszillierende BZ-Reaktion",
                briefing="Beobachte chemische Nichtgleichgewichts-Oszillationen und periodische Farbmusterwellen.",
                required_reagents=["malonic_acid", "potassium_iodate", "manganese_sulfate"],
                target_reaction_type="oscillating_color_wave",
                unlocked_apparatus=["Petrischale", "Magnetrührer_Hotplate"],
                unlocked_reagents=["malonic_acid", "potassium_iodate", "manganese_sulfate"],
            ),
            4: StoryLevel(
                level_number=4,
                title="Thermische Destillation",
                briefing="Trenne ein Flüssigkeitsgemisch durch kontrolliertes Erhitzen und Kondensation im Liebig-Kühler.",
                required_reagents=["water"],
                target_reaction_type="distillation",
                unlocked_apparatus=["Destillierkolben", "Liebig_Kühler", "Heizpilz"],
                unlocked_reagents=["ethanol"],
            ),
            5: StoryLevel(
                level_number=5,
                title="Goldener Regen",
                briefing="Synthetisiere spektakuläre goldgelbe Blei(II)-iodid-Kristalle unter strikten Sicherheitsauflagen im Abzug.",
                required_reagents=["lead_nitrate", "potassium_iodide"],
                target_reaction_type="precipitation_fall",
                unlocked_apparatus=["Erlenmeyerkolben_500ml", "Filtriertrichter"],
                unlocked_reagents=["lead_nitrate"],
                requires_fume_hood=True,
            ),
            6: StoryLevel(
                level_number=6,
                title="Chemisches Leuchten",
                briefing="Erzeuge blaues kaltes Licht durch Chemolumineszenz mit oxidiertem Luminol in alkalischer Lösung.",
                required_reagents=["luminol", "hydrogen_peroxide", "naoh"],
                target_reaction_type="chemiluminescent_glow",
                unlocked_apparatus=["Dunkelkammer-Vorhang", "UV-Lampe"],
                unlocked_reagents=["luminol"],
            ),
            7: StoryLevel(
                level_number=7,
                title="Thermische Sicherheitskontrolle",
                briefing="Bändige eine stark exotherme Runaway-Reaktion rechtzeitig durch Kühlbad und Druckventil.",
                required_reagents=["hcl", "naoh"],
                target_reaction_type="thermal_runaway_mitigation",
                unlocked_apparatus=["Eisbad", "Druckentlastungsventil", "CO2_Feuerlöscher"],
                unlocked_reagents=["eisbad_kryogen"],
            ),
            8: StoryLevel(
                level_number=8,
                title="Katalytische Elefanten-Zahnpasta",
                briefing="Zersetze hochkonzentriertes Peroxid katalytisch und beobachte die massive heiße Schaumeruption.",
                required_reagents=["hydrogen_peroxide", "potassium_iodide", "dish_soap"],
                target_reaction_type="catalytic_foam_eruption",
                unlocked_apparatus=["Standzylinder_1000ml", "Schutzschild"],
                unlocked_reagents=["dish_soap"],
            ),
            9: StoryLevel(
                level_number=9,
                title="Briggs-Rauscher Oszillator",
                briefing="Bringe die ultimative oszillierende Reaktion zum Schwingen: bernsteingelb, nachtblau und glasklar im Minutentakt.",
                required_reagents=[
                    "malonic_acid",
                    "potassium_iodate",
                    "hydrogen_peroxide",
                    "manganese_sulfate",
                    "starch",
                ],
                target_reaction_type="oscillating_color_wave",
                unlocked_apparatus=["Spektrometer_Optik", "Digitales_Thermometer"],
                unlocked_reagents=["h2so4"],
            ),
            10: StoryLevel(
                level_number=10,
                title="Meister-Alchemist",
                briefing="Volle Labor-Autonomie! Kreiere eigene exotische Synthesepfade im uneingeschränkten ChemLab.",
                required_reagents=[],
                target_reaction_type="free_mastery",
                unlocked_apparatus=["Schlenk_Line", "Glovebox", "Rotationsverdampfer"],
                unlocked_reagents=["alle_115_reagenzien"],
            ),
        }
