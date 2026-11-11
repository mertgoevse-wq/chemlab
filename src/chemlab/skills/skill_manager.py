"""
SkillManager — Skill progression runtime state.

Tracks XP, level, and unlocked content per skill discipline. Emits callbacks
(observable via simple observer list) when a skill levels up or a milestone
unlocks, so the Godot HUD and Python story manager can react.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

from chemlab.skills.milestones import Milestone, milestones_for_level
from chemlab.skills.skill_progression import (
    level_for_xp,
    level_progress_percent,
    xp_needed_for_next_level,
)
from chemlab.skills.skill_types import ALL_SKILLS, SkillType


@dataclass
class SkillState:
    """Live runtime state for a single skill discipline."""

    skill_type: SkillType
    xp: int = 0
    level: int = 1
    unlocked_apparatus: set[str] = field(default_factory=set)
    unlocked_reagents: set[str] = field(default_factory=set)
    unlocked_abilities: set[str] = field(default_factory=set)
    milestones_reached: set[int] = field(default_factory=set)

    @property
    def display_name(self) -> str:
        return ALL_SKILLS[self.skill_type].display_name

    @property
    def progress_percent(self) -> float:
        return level_progress_percent(self.xp)

    @property
    def xp_to_next(self) -> int:
        return xp_needed_for_next_level(self.xp)

    @property
    def rank_title(self) -> str:
        titles = ALL_SKILLS[self.skill_type].rank_titles
        idx = min(self.level - 1, len(titles) - 1)
        return titles[idx]


class SkillManager:
    """
    Manages all five skill disciplines with exponential skill progression.

    Observers are callables(skill_type: SkillType, level: int) invoked on
    level-up; milestone_observers are callables(milestone: Milestone) invoked
    when a milestone unlocks.
    """

    def __init__(
        self,
        on_level_up: Callable[[SkillType, int], None] | None = None,
        on_milestone: Callable[[Milestone], None] | None = None,
    ) -> None:
        self._skills: dict[SkillType, SkillState] = {
            st: SkillState(skill_type=st) for st in SkillType
        }
        self._on_level_up = on_level_up
        self._on_milestone = on_milestone

    # ------------------------------------------------------------------ #
    # Read access
    # ------------------------------------------------------------------ #
    def skill(self, skill_type: SkillType | str) -> SkillState:
        if isinstance(skill_type, str):
            skill_type = SkillType(skill_type)
        return self._skills[skill_type]

    def level(self, skill_type: SkillType | str) -> int:
        return self.skill(skill_type).level

    def xp(self, skill_type: SkillType | str) -> int:
        return self.skill(skill_type).xp

    def all_skills(self) -> dict[SkillType, SkillState]:
        return dict(self._skills)

    def is_apparatus_unlocked(self, skill_type: SkillType | str, apparatus: str) -> bool:
        return apparatus in self.skill(skill_type).unlocked_apparatus

    def is_reagent_unlocked(self, skill_type: SkillType | str, reagent: str) -> bool:
        return reagent in self.skill(skill_type).unlocked_reagents

    def is_ability_unlocked(self, skill_type: SkillType | str, ability: str) -> bool:
        return ability in self.skill(skill_type).unlocked_abilities

    # ------------------------------------------------------------------ #
    # Mutation
    # ------------------------------------------------------------------ #
    def add_xp(
        self,
        skill_type: SkillType | str,
        amount: int,
        notify: bool = True,
    ) -> list[int]:
        """
        Add XP to a skill. Returns list of new levels reached (may be multiple
        if a large XP grant crosses several levels).
        """
        if isinstance(skill_type, str):
            skill_type = SkillType(skill_type)
        amount = int(amount)
        if amount <= 0:
            return []

        state = self._skills[skill_type]
        old_level = state.level
        state.xp += amount
        new_level = level_for_xp(state.xp)
        state.level = new_level

        levels_reached: list[int] = []
        if new_level > old_level:
            levels_reached = list(range(old_level + 1, new_level + 1))
            if notify and self._on_level_up is not None:
                for lvl in levels_reached:
                    self._on_level_up(skill_type, lvl)

        # Unlock milestones at newly reached levels.
        for lvl in levels_reached:
            for milestone in milestones_for_level(skill_type.value, lvl):
                if lvl not in state.milestones_reached:
                    state.milestones_reached.add(lvl)
                    self._apply_milestone(state, milestone)
                    if notify and self._on_milestone is not None:
                        self._on_milestone(milestone)

        return levels_reached

    def set_xp(self, skill_type: SkillType | str, amount: int, notify: bool = True) -> list[int]:
        """Convenience: set absolute XP (useful for save-game loading)."""
        if isinstance(skill_type, str):
            skill_type = SkillType(skill_type)
        state = self._skills[skill_type]
        state.xp = max(0, int(amount))
        state.level = level_for_xp(state.xp)
        # Recompute all unlocked content from milestones up to current level.
        state.unlocked_apparatus.clear()
        state.unlocked_reagents.clear()
        state.unlocked_abilities.clear()
        state.milestones_reached.clear()
        for lvl in range(1, state.level + 1):
            for milestone in milestones_for_level(skill_type.value, lvl):
                state.milestones_reached.add(lvl)
                self._apply_milestone(state, milestone)
                if notify and self._on_milestone is not None:
                    self._on_milestone(milestone)
        if notify and self._on_level_up is not None:
            self._on_level_up(skill_type, state.level)
        return [state.level]

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #
    def _apply_milestone(self, state: SkillState, milestone: Milestone) -> None:
        state.unlocked_apparatus.update(milestone.unlocked_apparatus)
        state.unlocked_reagents.update(milestone.unlocked_reagents)
        state.unlocked_abilities.update(milestone.unlocked_abilities)

    # ------------------------------------------------------------------ #
    # Serialization (save/load)
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict[str, dict[str, object]]:
        """Serialize all skill states for JSON save games."""
        out: dict[str, dict[str, object]] = {}
        for st, state in self._skills.items():
            out[st.value] = {
                "xp": state.xp,
                "level": state.level,
                "unlocked_apparatus": sorted(state.unlocked_apparatus),
                "unlocked_reagents": sorted(state.unlocked_reagents),
                "unlocked_abilities": sorted(state.unlocked_abilities),
                "milestones_reached": sorted(state.milestones_reached),
            }
        return out

    def from_dict(self, data: dict[str, dict[str, object]], notify: bool = False) -> None:
        """Restore skill states from a JSON save game (does not re-apply XP math)."""
        for st in SkillType:
            block = data.get(st.value)
            if not block:
                continue
            state = self._skills[st]
            state.xp = int(cast(Any, block.get("xp", 0)))
            state.level = int(cast(Any, block.get("level", level_for_xp(state.xp))))
            state.unlocked_apparatus = set(cast(Any, block.get("unlocked_apparatus", [])))
            state.unlocked_reagents = set(cast(Any, block.get("unlocked_reagents", [])))
            state.unlocked_abilities = set(cast(Any, block.get("unlocked_abilities", [])))
            state.milestones_reached = {
                int(m) for m in cast(Any, block.get("milestones_reached", []))
            }
