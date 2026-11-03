"""
ChemLab Runescape-Style Skill & Quest System.

Provides 5 scientific disciplines with Runescape-style XP progression
(levels 1-120), milestone-based unlocks of apparatus/reagents/abilities,
and a data-driven quest engine integrated with the story progression manager.
"""

from chemlab.skills.milestones import (
    MILESTONES,
    Milestone,
    milestones_for_level,
    milestones_up_to_level,
)
from chemlab.skills.quest_engine import (
    Quest,
    QuestEngine,
    QuestStatus,
    StoryQuestBridge,
    load_quests,
)
from chemlab.skills.skill_manager import SkillManager
from chemlab.skills.skill_progression import SKILL_XP_FOR_LEVEL, level_for_xp, xp_for_level
from chemlab.skills.skill_types import ALL_SKILLS, SkillDefinition, SkillType

__all__ = [
    "SkillType",
    "SkillDefinition",
    "ALL_SKILLS",
    "SKILL_XP_FOR_LEVEL",
    "level_for_xp",
    "xp_for_level",
    "Milestone",
    "MILESTONES",
    "milestones_for_level",
    "milestones_up_to_level",
    "SkillManager",
    "QuestEngine",
    "Quest",
    "QuestStatus",
    "StoryQuestBridge",
    "load_quests",
]
