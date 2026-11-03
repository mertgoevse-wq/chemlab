"""
Runescape-style XP-to-level progression curve.

Formula (Runescape classic):
    XP for level N = floor(sum_{i=1}^{N-1} floor(i + 300 * 2^(i/7) / 4))

This gives ~83 million XP at level 99 and ~13 million at level 85,
matching the classic Runescape progression feel for a skill-based game.
Levels are capped at 120 for ChemLab (100 for the main campaign, 120 max
with prestige/post-game content).
"""

from __future__ import annotations

import math

MAX_LEVEL: int = 120
SOFT_CAP: int = 100  # main campaign cap; prestige extends to 120


def _xp_difference(level: int) -> int:
    """XP required to go from `level` to `level + 1`."""
    return int(math.floor(level + 300.0 * math.pow(2.0, level / 7.0) / 4.0))


def _build_xp_table() -> list[int]:
    """XP required to reach each level (index = level, value = total XP).

    table[1] = 0 (you start at level 1 with 0 XP); table[N] for N >= 2 is the
    cumulative sum of _xp_difference(i) for i in 1..N-1, matching the Runescape
    formula XP for level N = sum_{i=1}^{N-1} floor(i + 300*2^(i/7)/4).
    """
    table: list[int] = [0] * (MAX_LEVEL + 1)
    running: int = 0
    for level in range(2, MAX_LEVEL + 1):
        running += _xp_difference(level - 1)
        table[level] = running
    return table


SKILL_XP_FOR_LEVEL: list[int] = _build_xp_table()


def xp_for_level(target_level: int) -> int:
    """Total XP required to reach `target_level` (clamped to valid range)."""
    level = max(1, min(MAX_LEVEL, int(target_level)))
    return SKILL_XP_FOR_LEVEL[level]


def level_for_xp(total_xp: int) -> int:
    """Return the skill level for a given total XP (clamped to MAX_LEVEL)."""
    xp = max(0, int(total_xp))
    level = 1
    while level < MAX_LEVEL and xp >= SKILL_XP_FOR_LEVEL[level + 1]:
        level += 1
    return level


def xp_to_next_level(total_xp: int) -> int:
    """XP remaining until the next level."""
    level = level_for_xp(total_xp)
    if level >= MAX_LEVEL:
        return 0
    return SKILL_XP_FOR_LEVEL[level + 1] - total_xp


def xp_in_level(total_xp: int) -> int:
    """XP earned within the current level (progress toward next level)."""
    level = level_for_xp(total_xp)
    return total_xp - SKILL_XP_FOR_LEVEL[level]


def xp_needed_for_next_level(total_xp: int) -> int:
    """Total XP needed for the next level (delta within current level)."""
    level = level_for_xp(total_xp)
    if level >= MAX_LEVEL:
        return 0
    return SKILL_XP_FOR_LEVEL[level + 1] - SKILL_XP_FOR_LEVEL[level]


def level_progress_percent(total_xp: int) -> float:
    """Progress (0.0–1.0) within the current level."""
    level = level_for_xp(total_xp)
    if level >= MAX_LEVEL:
        return 1.0
    needed = xp_needed_for_next_level(total_xp)
    if needed <= 0:
        return 1.0
    return min(1.0, xp_in_level(total_xp) / needed)
