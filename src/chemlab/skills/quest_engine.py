"""
Data-driven quest engine for ChemLab's skill progression system.

Quests are defined as JSON-compatible dictionaries (matching the schema in
docs/STORY_AND_QUESTS.md §3) and evaluated against live simulation context
plus skill levels. Supports 100+ quests across 5 acts with skill-level
prerequisites, milestone unlocks, and skill-XP rewards.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chemlab.compat import StrEnum


class QuestStatus(StrEnum):
    """State machine for individual quests."""

    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationMode(StrEnum):
    """How a quest objective is evaluated against live context."""

    EQUIPMENT_STATE = "EQUIPMENT_STATE"
    METROLOGY_VALUE = "METROLOGY_VALUE"
    CHEMICAL_REACTION = "CHEMICAL_REACTION"
    SAFETY_COMPLIANCE = "SAFETY_COMPLIANCE"
    SPECTRAL_MATCH = "SPECTRAL_MATCH"
    SKILL_LEVEL = "SKILL_LEVEL"


class FailureSeverity(StrEnum):
    WARNING = "WARNING"
    SCORE_PENALTY = "SCORE_PENALTY"
    INSTANT_FAIL_EXPLOSION = "INSTANT_FAIL_EXPLOSION"
    CONTAINMENT_LOCKDOWN = "CONTAINMENT_LOCKDOWN"


@dataclass(frozen=True)
class QuestObjective:
    """A single measurable objective within a quest."""

    objective_id: str
    description: str
    target_entity: str
    evaluation_mode: EvaluationMode
    target_value: Any
    tolerance: float | None = None
    hints: list[str] = field(default_factory=list)

    def evaluate(self, live_context: dict[str, Any]) -> bool:
        current = live_context.get(self.target_entity)
        if current is None:
            return False

        if self.evaluation_mode == EvaluationMode.EQUIPMENT_STATE:
            return bool(current == self.target_value)

        if self.evaluation_mode == EvaluationMode.METROLOGY_VALUE:
            if self.tolerance is None:
                return bool(current == self.target_value)
            return bool(abs(float(current) - float(self.target_value)) <= self.tolerance)

        if self.evaluation_mode == EvaluationMode.CHEMICAL_REACTION:
            return bool(live_context.get("reaction_type") == self.target_value)

        if self.evaluation_mode == EvaluationMode.SAFETY_COMPLIANCE:
            return bool(float(live_context.get("safety_score", 0.0)) >= float(self.target_value))

        if self.evaluation_mode == EvaluationMode.SKILL_LEVEL:
            return bool(int(current) >= int(self.target_value))

        if self.evaluation_mode == EvaluationMode.SPECTRAL_MATCH:
            return bool(current == self.target_value)

        return False


@dataclass(frozen=True)
class FailureCondition:
    """A failure trigger evaluated each simulation tick."""

    condition_id: str
    severity: FailureSeverity
    trigger_metric: str
    operator: str  # ">", "<", "==", "!=", ">=", "<="
    threshold: Any
    narrative_reprimand: str

    def check(self, live_context: dict[str, Any]) -> bool:
        val = live_context.get(self.trigger_metric)
        if val is None:
            return False
        threshold = self.threshold
        try:
            val_f = float(val)
            threshold_f = float(threshold)
        except (TypeError, ValueError):
            return bool(val == threshold)

        if self.operator == ">":
            return val_f > threshold_f
        if self.operator == "<":
            return val_f < threshold_f
        if self.operator == "==":
            return val_f == threshold_f
        if self.operator == "!=":
            return val_f != threshold_f
        if self.operator == ">=":
            return val_f >= threshold_f
        if self.operator == "<=":
            return val_f <= threshold_f
        return False


@dataclass(frozen=True)
class QuestReward:
    """Rewards granted on quest completion."""

    skill_xp: dict[str, int] = field(default_factory=dict)  # skill_id -> xp
    unlocked_nodes: list[str] = field(default_factory=list)
    unlocked_apparatus: list[str] = field(default_factory=list)
    unlocked_reagents: list[str] = field(default_factory=list)
    academic_credential: str | None = None
    narrative_unlock: str | None = None


@dataclass
class Quest:
    """A complete quest definition with runtime state."""

    quest_id: str
    act: int
    title: str
    narrative_briefing: dict[str, Any]
    prerequisites: dict[str, Any]
    objectives: list[QuestObjective]
    failure_conditions: list[FailureCondition]
    state_validation: dict[str, Any]
    rewards: QuestReward
    status: QuestStatus = QuestStatus.LOCKED
    completed_objectives: set[str] = field(default_factory=set)
    current_objective_idx: int = 0

    def is_unlocked(
        self,
        completed_quests: set[str],
        skill_levels: dict[str, int],
        safety_score: float,
    ) -> bool:
        """Check whether prerequisites are met to start this quest."""
        if self.status == QuestStatus.COMPLETED:
            return False
        pre = self.prerequisites
        required = set(pre.get("completed_quests", []))
        if not required.issubset(completed_quests):
            return False
        min_safety = float(pre.get("min_safety_score", 0.0))
        if safety_score < min_safety:
            return False
        for skill_id in pre.get("required_skills", []):
            # required_skills entries may be "skill:level" or plain skill names.
            if ":" in skill_id:
                skill_name, min_level = skill_id.split(":", 1)
                if int(skill_levels.get(skill_name, 1)) < int(min_level):
                    return False
            else:
                # bare skill name means level >= 1
                if skill_id not in skill_levels:
                    return False
        return True

    def check_failures(self, live_context: dict[str, Any]) -> FailureCondition | None:
        for fail in self.failure_conditions:
            if fail.check(live_context):
                return fail
        return None

    def evaluate_objective(self, objective_id: str, live_context: dict[str, Any]) -> bool:
        for obj in self.objectives:
            if obj.objective_id == objective_id:
                return obj.evaluate(live_context)
        return False

    def complete_objective(self, objective_id: str) -> None:
        self.completed_objectives.add(objective_id)

    def all_objectives_complete(self) -> bool:
        return all(obj.objective_id in self.completed_objectives for obj in self.objectives)

    def to_dict(self) -> dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "act": self.act,
            "title": self.title,
            "status": self.status.value,
            "completed_objectives": sorted(self.completed_objectives),
            "current_objective_idx": self.current_objective_idx,
        }


class QuestEngine:
    """
    Runtime manager for all quests. Tracks availability, progression, and
    completion, dispatching skill-XP rewards on completion.
    """

    def __init__(
        self,
        skill_manager: Any,  # SkillManager (duck-typed to avoid import cycles)
        on_quest_completed: Callable[..., None] | None = None,
    ) -> None:
        self._quests: dict[str, Quest] = {}
        self._skill_manager = skill_manager
        self._on_quest_completed = on_quest_completed
        self.completed_quests: set[str] = set()

    # ------------------------------------------------------------------ #
    # Loading / registration
    # ------------------------------------------------------------------ #
    def register_quest(self, quest: Quest) -> None:
        self._quests[quest.quest_id] = quest

    def load_quests_from_list(self, quest_defs: list[dict[str, Any]]) -> None:
        """Bulk-register quests from JSON-compatible dicts."""
        for qd in quest_defs:
            quest = self._parse_quest_dict(qd)
            self.register_quest(quest)

    def load_quests_from_json(self, path: str) -> None:
        with Path(path).open(encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "quests" in data:
            self.load_quests_from_list(data["quests"])
        elif isinstance(data, list):
            self.load_quests_from_list(data)
        else:
            raise ValueError("Quest JSON must be a list or {'quests': [...]}")

    # ------------------------------------------------------------------ #
    # Query API
    # ------------------------------------------------------------------ #
    def get_quest(self, quest_id: str) -> Quest | None:
        return self._quests.get(quest_id)

    def all_quests(self) -> dict[str, Quest]:
        return dict(self._quests)

    def available_quests(
        self,
        skill_levels: dict[str, int],
        safety_score: float,
    ) -> list[Quest]:
        """Quests whose prerequisites are met and not yet completed."""
        return [
            q
            for q in self._quests.values()
            if q.is_unlocked(self.completed_quests, skill_levels, safety_score)
        ]

    def in_progress_quests(self) -> list[Quest]:
        return [q for q in self._quests.values() if q.status == QuestStatus.IN_PROGRESS]

    def completed_count(self) -> int:
        return len(self.completed_quests)

    def to_dict(self) -> dict[str, Any]:
        """Serialize all quest runtime states for JSON save games."""
        return {
            "completed_quests": sorted(self.completed_quests),
            "quests": [_quest_to_dict(q) for q in self._quests.values()],
        }

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore quest runtime states from a JSON save game."""
        self.completed_quests = set(data.get("completed_quests", []))
        for qd in data.get("quests", []):
            _quest_from_dict(qd, self._quests)

    # ------------------------------------------------------------------ #
    # Progression
    # ------------------------------------------------------------------ #
    def start_quest(self, quest_id: str) -> bool:
        quest = self._quests.get(quest_id)
        if quest is None:
            return False
        skill_levels = (
            {st.value: self._skill_manager.level(st) for st in self._skill_manager.all_skills()}
            if self._skill_manager is not None
            else {}
        )
        safety_score = (
            float(getattr(self._skill_manager, "safety_score", 100.0))
            if self._skill_manager is not None
            else 100.0
        )
        if not quest.is_unlocked(self.completed_quests, skill_levels, safety_score):
            return False
        quest.status = QuestStatus.IN_PROGRESS
        quest.current_objective_idx = 0
        return True

    def complete_objective(
        self, quest_id: str, objective_id: str, live_context: dict[str, Any]
    ) -> bool:
        """Mark an objective complete if it evaluates true against live context."""
        quest = self._quests.get(quest_id)
        if quest is None or quest.status != QuestStatus.IN_PROGRESS:
            return False
        if objective_id in quest.completed_objectives:
            return True
        if not quest.evaluate_objective(objective_id, live_context):
            return False
        quest.complete_objective(objective_id)

        if quest.all_objectives_complete():
            self._complete_quest(quest)
        return True

    def check_failures(
        self, quest_id: str, live_context: dict[str, Any]
    ) -> FailureCondition | None:
        quest = self._quests.get(quest_id)
        if quest is None or quest.status != QuestStatus.IN_PROGRESS:
            return None
        return quest.check_failures(live_context)

    def _complete_quest(self, quest: Quest) -> None:
        quest.status = QuestStatus.COMPLETED
        self.completed_quests.add(quest.quest_id)

        # Grant skill XP rewards.
        if self._skill_manager is not None:
            for skill_id, xp_amount in quest.rewards.skill_xp.items():
                with suppress(KeyError, ValueError):
                    # Unknown skill id — skip gracefully.
                    self._skill_manager.add_xp(skill_id, xp_amount)

        if self._on_quest_completed is not None:
            self._on_quest_completed(quest)

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_quest_dict(qd: dict[str, Any]) -> Quest:
        objectives = [
            QuestObjective(
                objective_id=o["objective_id"],
                description=o["description"],
                target_entity=o["target_entity"],
                evaluation_mode=EvaluationMode(o["evaluation_mode"]),
                target_value=o["target_value"],
                tolerance=o.get("tolerance"),
                hints=o.get("hints", []),
            )
            for o in qd.get("objectives", [])
        ]

        failure_conditions = [
            FailureCondition(
                condition_id=f["condition_id"],
                severity=FailureSeverity(f["severity"]),
                trigger_metric=f["trigger_metric"],
                operator=f["operator"],
                threshold=f["threshold"],
                narrative_reprimand=f["narrative_reprimand"],
            )
            for f in qd.get("failure_conditions", [])
        ]

        rewards = qd.get("rewards", {})
        quest_reward = QuestReward(
            skill_xp=rewards.get("skill_xp", {}),
            unlocked_nodes=rewards.get("unlocked_nodes", []),
            unlocked_apparatus=rewards.get("unlocked_apparatus", []),
            unlocked_reagents=rewards.get("unlocked_reagents", []),
            academic_credential=rewards.get("academic_credential"),
            narrative_unlock=rewards.get("narrative_unlock"),
        )

        return Quest(
            quest_id=qd["quest_id"],
            act=int(qd["act"]),
            title=qd["title"],
            narrative_briefing=qd.get("narrative_briefing", {}),
            prerequisites=qd.get("prerequisites", {}),
            objectives=objectives,
            failure_conditions=failure_conditions,
            state_validation=qd.get("state_validation", {}),
            rewards=quest_reward,
        )


# Backwards-compatible alias for existing code expecting `load_quests`.
def load_quests(quest_defs: list[dict[str, Any]], skill_manager: Any) -> QuestEngine:
    engine = QuestEngine(skill_manager)
    engine.load_quests_from_list(quest_defs)
    return engine


# ---------------------------------------------------------------------- #
# Serialization (save/load) for JSON save-game compatibility
# ---------------------------------------------------------------------- #
def _quest_to_dict(quest: Quest) -> dict[str, Any]:
    """Serialize a single Quest to a JSON-compatible dictionary."""
    return {
        "quest_id": quest.quest_id,
        "act": quest.act,
        "title": quest.title,
        "status": quest.status.value,
        "completed_objectives": sorted(quest.completed_objectives),
        "current_objective_idx": quest.current_objective_idx,
    }


def _quest_from_dict(data: dict[str, Any], quests: dict[str, Quest]) -> None:
    """Restore a single Quest's runtime state from a serialized dictionary."""
    quest = quests.get(data["quest_id"])
    if quest is None:
        return
    quest.status = QuestStatus(data["status"])
    quest.completed_objectives = set(data.get("completed_objectives", []))
    quest.current_objective_idx = int(data.get("current_objective_idx", 0))


# Adapter bridge: exposes StoryProgressionManager as a QuestEngine skill manager.
class StoryQuestBridge:
    """Adapts StoryProgressionManager into a QuestEngine skill-level provider.

    The QuestEngine duck-types its skill manager: it only needs `.level(SkillType)`,
    `.all_skills()`, and an optional `.safety_score` attribute. This bridge maps
    story-mode level progression onto the five skill disciplines so Godot's
    StoryProgressionManager can drive quest availability and rewards.
    """

    def __init__(self, story_mgr: Any) -> None:
        self._story = story_mgr
        self.safety_score: float = getattr(story_mgr, "safety_score", 100.0)

    def level(self, skill_type: Any) -> int:
        """Return the story level mapped onto any skill discipline."""
        return int(self._story.current_level_number)

    def all_skills(self) -> dict[Any, Any]:
        """Return a mapping of all five skill types to dummy state objects."""
        from chemlab.skills.skill_types import SkillType

        level = self._story.current_level_number
        return {st: _DummySkillState(level) for st in SkillType}


class _DummySkillState:
    """Minimal SkillState-like object exposing only `level`."""

    def __init__(self, level: int) -> None:
        self.level = level
