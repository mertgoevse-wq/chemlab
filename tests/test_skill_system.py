"""
Unit tests for the Runescape-style skill & quest system in src/chemlab/skills/.

Covers skill progression (XP curve, leveling), SkillManager runtime state,
milestone unlocks, and the QuestEngine lifecycle (availability, objectives,
failures, skill-XP rewards).
"""

from __future__ import annotations

import math
from typing import Any

import pytest

from chemlab.skills.milestones import (
    Milestone,
    milestones_for_level,
    milestones_up_to_level,
)
from chemlab.skills.quest_engine import (
    EvaluationMode,
    FailureSeverity,
    QuestEngine,
    QuestObjective,
    QuestReward,
    QuestStatus,
    StoryQuestBridge,
    load_quests,
)
from chemlab.skills.skill_manager import SkillManager
from chemlab.skills.skill_progression import (
    MAX_LEVEL,
    level_for_xp,
    level_progress_percent,
    xp_for_level,
    xp_in_level,
    xp_needed_for_next_level,
    xp_to_next_level,
)
from chemlab.skills.skill_types import ALL_SKILLS, SkillType

# --------------------------------------------------------------------------- #
# Skill progression
# --------------------------------------------------------------------------- #


def test_xp_for_level_bounds() -> None:
    assert xp_for_level(1) == 0
    assert xp_for_level(2) == int(math.floor(1 + 300 * 2 ** (1 / 7) / 4))
    assert xp_for_level(MAX_LEVEL) > xp_for_level(MAX_LEVEL - 1)


def test_level_for_xp_clamps() -> None:
    assert level_for_xp(0) == 1
    assert level_for_xp(xp_for_level(5)) == 5
    assert level_for_xp(xp_for_level(MAX_LEVEL)) == MAX_LEVEL
    # Massive XP clamps at MAX_LEVEL.
    assert level_for_xp(10**12) == MAX_LEVEL


def test_xp_to_next_level_zero_at_max() -> None:
    assert xp_to_next_level(xp_for_level(MAX_LEVEL)) == 0


def test_level_progress_percent() -> None:
    assert level_progress_percent(0) == 0.0
    assert level_progress_percent(xp_for_level(MAX_LEVEL)) == 1.0
    mid = xp_for_level(2) + (xp_for_level(3) - xp_for_level(2)) // 2
    assert 0.0 < level_progress_percent(mid) < 1.0


def test_xp_needed_for_next_level() -> None:
    level = 3
    xp = xp_for_level(level)
    assert xp_needed_for_next_level(xp) == xp_for_level(level + 1) - xp_for_level(level)
    assert xp_needed_for_next_level(xp_for_level(MAX_LEVEL)) == 0


def test_xp_in_level() -> None:
    level = 4
    xp = xp_for_level(level)
    assert xp_in_level(xp) == 0
    assert xp_in_level(xp_for_level(level + 1) - 1) > 0


# --------------------------------------------------------------------------- #
# Skill manager
# --------------------------------------------------------------------------- #


class _FakeOnLevelUp:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    def __call__(self, skill_type: Any, level: int) -> None:
        self.calls.append((skill_type.value, level))


class _FakeOnMilestone:
    def __init__(self) -> None:
        self.calls: list[Milestone] = []

    def __call__(self, milestone: Milestone) -> None:
        self.calls.append(milestone)


def test_skill_manager_initial_state() -> None:
    mgr = SkillManager()
    for st in SkillType:
        state = mgr.skill(st)
        assert state.level == 1
        assert state.xp == 0
        assert state.progress_percent == 0.0


def test_add_xp_levels_up() -> None:
    mgr = SkillManager()
    on_level_up = _FakeOnLevelUp()
    mgr._on_level_up = on_level_up  # type: ignore[assignment]

    levels = mgr.add_xp(SkillType.SAFETY, xp_for_level(10))
    assert levels == list(range(2, 11))
    assert mgr.level(SkillType.SAFETY) == 10
    assert mgr.xp(SkillType.SAFETY) == xp_for_level(10)
    assert on_level_up.calls == [("safety", lvl) for lvl in range(2, 11)]


def test_add_xp_non_positive_returns_empty() -> None:
    mgr = SkillManager()
    assert mgr.add_xp(SkillType.SAFETY, 0) == []
    assert mgr.add_xp(SkillType.SAFETY, -5) == []
    assert mgr.level(SkillType.SAFETY) == 1


def test_add_xp_string_skill_type() -> None:
    mgr = SkillManager()
    mgr.add_xp("safety", xp_for_level(3))
    assert mgr.level(SkillType.SAFETY) == 3


def test_skill_state_unlocks_on_level_up() -> None:
    mgr = SkillManager()
    mgr.add_xp(SkillType.SAFETY, xp_for_level(10))
    state = mgr.skill(SkillType.SAFETY)
    assert state.level >= 10
    # Level 10 milestone grants Fume Hood Sash Control etc.
    assert mgr.is_apparatus_unlocked(SkillType.SAFETY, "Fume Hood Sash Control")
    assert mgr.is_reagent_unlocked(SkillType.SAFETY, "hcl")
    assert mgr.is_reagent_unlocked(SkillType.SAFETY, "naoh")


def test_set_xp_rebuilds_unlocks() -> None:
    mgr = SkillManager()
    # Add XP to unlock level-10 content, then reload via set_xp.
    mgr.add_xp(SkillType.SAFETY, xp_for_level(10))
    assert mgr.is_apparatus_unlocked(SkillType.SAFETY, "Fume Hood Sash Control")

    mgr2 = SkillManager()
    mgr2.set_xp(SkillType.SAFETY, xp_for_level(10), notify=False)
    assert mgr2.level(SkillType.SAFETY) == 10
    assert mgr2.is_apparatus_unlocked(SkillType.SAFETY, "Fume Hood Sash Control")
    assert mgr2.is_reagent_unlocked(SkillType.SAFETY, "hcl")


def test_to_dict_from_dict_roundtrip() -> None:
    mgr = SkillManager()
    mgr.add_xp(SkillType.SAFETY, xp_for_level(25))
    mgr.add_xp(SkillType.ANALYTICAL, xp_for_level(15))

    data = mgr.to_dict()
    assert "safety" in data and "analytical" in data
    assert data["safety"]["level"] == 25
    assert data["analytical"]["level"] == 15

    mgr2 = SkillManager()
    mgr2.from_dict(data, notify=False)
    assert mgr2.level(SkillType.SAFETY) == 25
    assert mgr2.level(SkillType.ANALYTICAL) == 15
    assert mgr2.is_apparatus_unlocked(SkillType.SAFETY, "Fume Hood Sash Control")


def test_rank_title() -> None:
    mgr = SkillManager()
    mgr.add_xp(SkillType.SAFETY, xp_for_level(50))
    state = mgr.skill(SkillType.SAFETY)
    titles = ALL_SKILLS[SkillType.SAFETY].rank_titles
    idx = min(state.level - 1, len(titles) - 1)
    assert state.rank_title == titles[idx]


# --------------------------------------------------------------------------- #
# Milestones
# --------------------------------------------------------------------------- #


def test_milestones_for_level() -> None:
    lvl_1 = milestones_for_level("safety", 1)
    assert len(lvl_1) == 1
    assert lvl_1[0].title == "PPE Protocol & Donning Discipline"

    lvl_10 = milestones_for_level("safety", 10)
    assert len(lvl_10) == 1
    assert lvl_10[0].title == "Aerodynamic Containment"

    assert milestones_for_level("safety", 999) == []


def test_milestones_up_to_level() -> None:
    up_to_10 = milestones_up_to_level("safety", 10)
    levels = {m.level for m in up_to_10}
    assert levels == {1, 10}

    # Analytical has milestones at 1, 15, 30, 50, 75, 100.
    up_to_15 = milestones_up_to_level("analytical", 15)
    assert {m.level for m in up_to_15} == {1, 15}


def test_all_five_skills_have_six_milestones() -> None:
    for st in SkillType:
        milestones = milestones_up_to_level(st.value, 100)
        assert len(milestones) == 6, f"{st.value} should have 6 milestones"
        assert all(m.skill == st.value for m in milestones)


# --------------------------------------------------------------------------- #
# Quest engine
# --------------------------------------------------------------------------- #


def _make_quest_objective(
    objective_id: str = "obj1",
    target_entity: str = "ph",
    evaluation_mode: EvaluationMode = EvaluationMode.METROLOGY_VALUE,
    target_value: Any = 7.0,
    tolerance: float | None = 0.5,
) -> QuestObjective:
    return QuestObjective(
        objective_id=objective_id,
        description="Test objective",
        target_entity=target_entity,
        evaluation_mode=evaluation_mode,
        target_value=target_value,
        tolerance=tolerance,
    )


def _make_reward(skill_xp: dict[str, int] | None = None) -> QuestReward:
    return QuestReward(skill_xp=skill_xp or {})


def _engine_with_skill_manager() -> tuple[QuestEngine, SkillManager]:
    skill_mgr = SkillManager()
    engine = QuestEngine(skill_mgr)
    return engine, skill_mgr


def _sample_quest() -> dict[str, Any]:
    return {
        "quest_id": "q_titration_01",
        "act": 1,
        "title": "First Titration",
        "narrative_briefing": {"briefing": "Neutralize acid with base."},
        "prerequisites": {
            "completed_quests": [],
            "min_safety_score": 0.0,
            "required_skills": ["safety:1"],
        },
        "objectives": [
            {
                "objective_id": "obj_neutralize",
                "description": "Bring pH to 7.0",
                "target_entity": "ph",
                "evaluation_mode": "METROLOGY_VALUE",
                "target_value": 7.0,
                "tolerance": 0.5,
            }
        ],
        "failure_conditions": [],
        "state_validation": {},
        "rewards": {"skill_xp": {"safety": 100}},
    }


def test_engine_loads_quest_from_dict() -> None:
    engine, _ = _engine_with_skill_manager()
    engine.load_quests_from_list([_sample_quest()])
    quest = engine.get_quest("q_titration_01")
    assert quest is not None
    assert quest.title == "First Titration"
    assert quest.status == QuestStatus.LOCKED


def test_engine_available_quests_requires_prerequisites() -> None:
    engine, skill_mgr = _engine_with_skill_manager()
    engine.load_quests_from_list([_sample_quest()])

    # Skill level 1 meets "safety:1" prerequisite.
    available = engine.available_quests(
        {st.value: skill_mgr.level(st) for st in skill_mgr.all_skills()}, 100.0
    )
    assert any(q.quest_id == "q_titration_01" for q in available)

    # Quest requiring safety:50 should not be available at level 1.
    hard_quest = dict(_sample_quest())
    hard_quest["quest_id"] = "q_hard"
    hard_quest["prerequisites"]["required_skills"] = ["safety:50"]
    engine.load_quests_from_list([hard_quest])
    available = engine.available_quests(
        {st.value: skill_mgr.level(st) for st in skill_mgr.all_skills()}, 100.0
    )
    assert not any(q.quest_id == "q_hard" for q in available)


def test_engine_start_and_complete_quest_grants_xp() -> None:
    engine, skill_mgr = _engine_with_skill_manager()
    engine.load_quests_from_list([_sample_quest()])

    assert engine.start_quest("q_titration_01")
    quest = engine.get_quest("q_titration_01")
    assert quest.status == QuestStatus.IN_PROGRESS

    old_xp = skill_mgr.xp(SkillType.SAFETY)
    live_context = {"ph": 7.0}
    assert engine.complete_objective("q_titration_01", "obj_neutralize", live_context)
    assert quest.status == QuestStatus.COMPLETED
    assert skill_mgr.xp(SkillType.SAFETY) == old_xp + 100


def test_engine_complete_objective_wrong_context_fails() -> None:
    engine, _ = _engine_with_skill_manager()
    engine.load_quests_from_list([_sample_quest()])
    engine.start_quest("q_titration_01")

    # pH far from target → objective does not evaluate true.
    assert not engine.complete_objective("q_titration_01", "obj_neutralize", {"ph": 2.0})
    quest = engine.get_quest("q_titration_01")
    assert quest.status == QuestStatus.IN_PROGRESS
    assert "obj_neutralize" not in quest.completed_objectives


def test_engine_check_failures() -> None:
    failing_quest = dict(_sample_quest())
    failing_quest["quest_id"] = "q_fail"
    failing_quest["failure_conditions"] = [
        {
            "condition_id": "explosion",
            "severity": "INSTANT_FAIL_EXPLOSION",
            "trigger_metric": "temperature",
            "operator": ">",
            "threshold": 100.0,
            "narrative_reprimand": "The mixture exploded!",
        }
    ]
    engine, _ = _engine_with_skill_manager()
    engine.load_quests_from_list([failing_quest])
    engine.start_quest("q_fail")

    fail = engine.check_failures("q_fail", {"temperature": 150.0})
    assert fail is not None
    assert fail.condition_id == "explosion"

    fail = engine.check_failures("q_fail", {"temperature": 50.0})
    assert fail is None


def test_engine_load_from_json(tmp_path) -> None:
    import json

    quest_file = tmp_path / "quests.json"
    quest_file.write_text(json.dumps([_sample_quest()]), encoding="utf-8")

    engine, _ = _engine_with_skill_manager()
    engine.load_quests_from_json(str(quest_file))
    assert engine.get_quest("q_titration_01") is not None


def test_load_quests_alias() -> None:
    skill_mgr = SkillManager()
    engine = load_quests([_sample_quest()], skill_mgr)
    assert engine.get_quest("q_titration_01") is not None
    assert engine._skill_manager is skill_mgr


def test_engine_unknown_quest_noop() -> None:
    engine, _ = _engine_with_skill_manager()
    assert not engine.start_quest("nonexistent")
    assert not engine.complete_objective("nonexistent", "obj", {})
    assert engine.check_failures("nonexistent", {}) is None


def test_engine_serialization_roundtrip() -> None:
    engine, skill_mgr = _engine_with_skill_manager()
    engine.load_quests_from_list([_sample_quest()])
    engine.start_quest("q_titration_01")
    engine.complete_objective("q_titration_01", "obj_neutralize", {"ph": 7.0})

    data = engine.to_dict()
    assert "q_titration_01" in data["completed_quests"]
    assert any(
        qd["quest_id"] == "q_titration_01" and qd["status"] == "completed" for qd in data["quests"]
    )

    engine2 = QuestEngine(skill_mgr)
    engine2.load_quests_from_list([_sample_quest()])
    engine2.from_dict(data)
    q = engine2.get_quest("q_titration_01")
    assert q is not None
    assert q.status == QuestStatus.COMPLETED
    assert "obj_neutralize" in q.completed_objectives


class _FakeStoryMgr:
    """Minimal stand-in for StoryProgressionManager used by StoryQuestBridge tests."""

    def __init__(self, level_number: int = 1, safety_score: float = 100.0) -> None:
        self.current_level_number = level_number
        self.safety_score = safety_score


def test_story_quest_bridge_levels() -> None:
    story = _FakeStoryMgr(level_number=5, safety_score=88.0)
    bridge = StoryQuestBridge(story)
    assert bridge.level(SkillType.SAFETY) == 5
    assert bridge.level(SkillType.ANALYTICAL) == 5
    assert bridge.safety_score == 88.0
    assert len(bridge.all_skills()) == 5
    for state in bridge.all_skills().values():
        assert state.level == 5


def test_story_quest_bridge_drives_quest_engine() -> None:
    story = _FakeStoryMgr(level_number=1, safety_score=100.0)
    bridge = StoryQuestBridge(story)
    engine = QuestEngine(bridge)
    engine.load_quests_from_list([_sample_quest()])

    available = engine.available_quests(
        {st.value: bridge.level(st) for st in bridge.all_skills()}, bridge.safety_score
    )
    assert any(q.quest_id == "q_titration_01" for q in available)
