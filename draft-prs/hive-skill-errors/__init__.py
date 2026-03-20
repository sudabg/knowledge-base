"""Hive Skill System — Structured errors and diagnostics."""

from framework.skills.errors import (
    SkillError,
    SkillErrorCode,
    SkillWarning,
    diagnose_skill,
)

__all__ = [
    "SkillError",
    "SkillErrorCode",
    "SkillWarning",
    "diagnose_skill",
]
