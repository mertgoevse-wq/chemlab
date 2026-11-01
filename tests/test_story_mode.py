"""
Unit tests for the 10-Level Story Mode Progression System.
Tests quest requirements, unlocks, safety evaluations, and rank promotions.
"""

from __future__ import annotations

import pytest

from chemlab.story.story_manager import (
    PlayerRank,
    QuestStatus,
    StoryLevel,
    StoryProgressionManager,
)


def test_story_manager_initial_state() -> None:
    mgr = StoryProgressionManager()
    assert mgr.current_level_number == 1
    assert mgr.player_rank == PlayerRank.TRAINEE
    assert mgr.get_current_level().title == "Labortaufe & Indikator"
    assert mgr.is_level_unlocked(1)
    assert not mgr.is_level_unlocked(2)


def test_level_1_completion_and_unlock() -> None:
    mgr = StoryProgressionManager()
    # Level 1 objective: Neutralize acid with base using universal indicator
    completed = mgr.submit_reaction_result(
        reagent_ids=["hcl", "naoh", "universal_indicator"],
        final_ph=7.0,
        temperature_c=25.0,
    )
    assert completed
    assert mgr.is_level_completed(1)
    assert mgr.is_level_unlocked(2)
    assert mgr.current_level_number == 2
    assert mgr.player_rank == PlayerRank.APPRENTICE


def test_safety_violation_penalty() -> None:
    mgr = StoryProgressionManager()
    mgr.current_level_number = 5  # Level 5: Goldener Regen (requires fume hood)
    # Toxic reaction outside fume hood should trigger safety deduction
    completed = mgr.submit_reaction_result(
        reagent_ids=["lead_nitrate", "potassium_iodide"],
        final_ph=7.0,
        temperature_c=95.0,
        in_fume_hood=False,
    )
    assert not completed
    assert mgr.safety_score < 100.0
    assert "Sicherheitsabzug" in mgr.last_feedback


def test_unlock_all_sandbox_mode() -> None:
    mgr = StoryProgressionManager()
    # Entering Free Sandbox mode grants immediate access to all 10 levels and reagents
    mgr.unlock_all_for_sandbox()
    for lvl in range(1, 11):
        assert mgr.is_level_unlocked(lvl)
    assert mgr.player_rank == PlayerRank.MASTER_ALCHEMIST
