"""Structured error codes and diagnostics for the Hive Skill System.

Implements DX-1, DX-2, DX-3 from docs/skill-registry-prd.md §7.5.

Every error includes:
- A machine-readable error code (e.g., SKILL_NOT_FOUND)
- A human-readable message
- Actionable remediation guidance
- Optional context (skill name, file path, line number)

Usage:
    from framework.skills.errors import SkillError, SkillErrorCode

    raise SkillError(
        code=SkillErrorCode.SKILL_PARSE_ERROR,
        skill_name="my-skill",
        detail="unquoted colon in description field",
        remediation="Wrap the value in quotes: description: 'My skill: a demo'",
    )
"""

from __future__ import annotations

import enum
from typing import Optional


class SkillErrorCode(enum.Enum):
    """Structured error codes for the skill system."""

    # Discovery & Loading
    SKILL_NOT_FOUND = "SKILL_NOT_FOUND"
    SKILL_NAME_MISMATCH = "SKILL_NAME_MISMATCH"
    SKILL_COLLISION = "SKILL_COLLISION"
    SKILL_LOAD_FAILED = "SKILL_LOAD_FAILED"

    # Parsing & Validation
    SKILL_PARSE_ERROR = "SKILL_PARSE_ERROR"
    SKILL_YAML_FIXUP = "SKILL_YAML_FIXUP"
    SKILL_MISSING_DESCRIPTION = "SKILL_MISSING_DESCRIPTION"
    SKILL_MISSING_NAME = "SKILL_MISSING_NAME"
    SKILL_INVALID_FRONTMATTER = "SKILL_INVALID_FRONTMATTER"

    # Activation & Runtime
    SKILL_ACTIVATION_FAILED = "SKILL_ACTIVATION_FAILED"
    SKILL_SCRIPT_ERROR = "SKILL_SCRIPT_ERROR"
    SKILL_TIMEOUT = "SKILL_TIMEOUT"
    SKILL_RESOURCE_MISSING = "SKILL_RESOURCE_MISSING"

    # Registry
    SKILL_REGISTRY_UNREACHABLE = "SKILL_REGISTRY_UNREACHABLE"
    SKILL_INSTALL_FAILED = "SKILL_INSTALL_FAILED"
    SKILL_VERSION_CONFLICT = "SKILL_VERSION_CONFLICT"


# Remediation templates for each error code
REMEDIATION_MAP: dict[SkillErrorCode, str] = {
    SkillErrorCode.SKILL_NOT_FOUND: (
        "The referenced skill is not installed or discoverable. "
        "Run 'hive skill list' to see installed skills, or "
        "'hive skill install {name}' to install from the registry."
    ),
    SkillErrorCode.SKILL_NAME_MISMATCH: (
        "The 'name' field in SKILL.md does not match the directory name. "
        "Rename the directory to match the 'name' field, or update the 'name' "
        "field to match the directory."
    ),
    SkillErrorCode.SKILL_COLLISION: (
        "Two skills have the same name. Rename one of them or use a namespace "
        "prefix. Check installed skills with 'hive skill list'."
    ),
    SkillErrorCode.SKILL_LOAD_FAILED: (
        "Failed to read the skill directory. Check file permissions: "
        "'chmod -R 755 {skill_path}'. Ensure SKILL.md exists in the skill root."
    ),
    SkillErrorCode.SKILL_PARSE_ERROR: (
        "YAML frontmatter in SKILL.md could not be parsed. Common causes: "
        "1) Unquoted colons in values — wrap in quotes, "
        "2) Incorrect indentation — use 2-space indent, "
        "3) Missing closing '---' delimiter."
    ),
    SkillErrorCode.SKILL_YAML_FIXUP: (
        "The YAML was auto-fixed (likely unquoted colons). This is a warning. "
        "To silence: quote any values containing colons."
    ),
    SkillErrorCode.SKILL_MISSING_DESCRIPTION: (
        "SKILL.md has no 'description' field in YAML frontmatter. "
        "Add: description: What this skill does"
    ),
    SkillErrorCode.SKILL_MISSING_NAME: (
        "SKILL.md has no 'name' field in YAML frontmatter. "
        "Add: name: my-skill"
    ),
    SkillErrorCode.SKILL_INVALID_FRONTMATTER: (
        "YAML frontmatter is missing or malformed. Ensure SKILL.md starts with "
        "'---' on line 1, has valid YAML metadata, and closes with '---'."
    ),
    SkillErrorCode.SKILL_ACTIVATION_FAILED: (
        "Skill loaded but failed to activate. Check that all referenced files "
        "(scripts/, references/, assets/) exist and are readable."
    ),
    SkillErrorCode.SKILL_SCRIPT_ERROR: (
        "A script in scripts/ failed. Check execute permission (chmod +x) and "
        "shebang line (#!/usr/bin/env python3 or #!/bin/bash)."
    ),
    SkillErrorCode.SKILL_TIMEOUT: (
        "Skill activation or script timed out. Optimize scripts or increase: "
        "'hive config set skill_timeout 60'"
    ),
    SkillErrorCode.SKILL_RESOURCE_MISSING: (
        "A resource file (references/ or assets/) was not found. "
        "Verify file paths in SKILL.md match actual locations."
    ),
    SkillErrorCode.SKILL_REGISTRY_UNREACHABLE: (
        "Cannot connect to skill registry. Check network and registry URL: "
        "'hive config get registry_url'"
    ),
    SkillErrorCode.SKILL_INSTALL_FAILED: (
        "Skill installation failed. Check disk space and permissions. "
        "Try: 'hive skill install {name} --verbose'"
    ),
    SkillErrorCode.SKILL_VERSION_CONFLICT: (
        "Version conflict with installed skill. Uninstall first: "
        "'hive skill uninstall {name}', then reinstall."
    ),
}


class SkillError(Exception):
    """Structured skill error with code, context, and remediation guidance."""

    def __init__(
        self,
        code: SkillErrorCode = SkillErrorCode.SKILL_NOT_FOUND,
        skill_name: Optional[str] = None,
        detail: Optional[str] = None,
        remediation: Optional[str] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        context: Optional[dict] = None,
    ):
        self.code = code
        self.skill_name = skill_name
        self.detail = detail
        self._remediation = remediation or REMEDIATION_MAP.get(
            code, "No remediation available."
        )
        self.file_path = file_path
        self.line_number = line_number
        self.context = context or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = [f"[{self.code.value}]"]
        if self.skill_name:
            parts.append(f"skill={self.skill_name}")
        if self.detail:
            parts.append(f": {self.detail}")
        if self.file_path:
            loc = f" (file: {self.file_path}"
            if self.line_number:
                loc += f":{self.line_number}"
            loc += ")"
            parts.append(loc)
        parts.append(f"\n→ Fix: {self._remediation}")
        return "".join(parts)

    @property
    def default_remediation(self) -> str:
        return self._remediation

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON logging/API responses."""
        result = {
            "error_code": self.code.value,
            "message": self.detail or self.code.value,
            "remediation": self._remediation,
        }
        if self.skill_name:
            result["skill_name"] = self.skill_name
        if self.file_path:
            result["file_path"] = self.file_path
        if self.line_number:
            result["line_number"] = self.line_number
        if self.context:
            result["context"] = self.context
        return result


class SkillWarning(UserWarning):
    """Non-fatal skill warning (e.g., SKILL_YAML_FIXUP)."""

    def __init__(self, error: SkillError):
        self.error = error
        super().__init__(str(error))


def diagnose_skill(skill_path: str) -> list[SkillError]:
    """Run diagnostics on a skill directory and return any issues found.

    Args:
        skill_path: Path to the skill directory.

    Returns:
        List of SkillError objects for issues found. Empty list if healthy.
    """
    import os

    errors = []
    skill_name = os.path.basename(skill_path)

    if not os.path.isdir(skill_path):
        errors.append(SkillError(
            code=SkillErrorCode.SKILL_NOT_FOUND,
            skill_name=skill_name,
            detail=f"Directory does not exist: {skill_path}",
        ))
        return errors

    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        errors.append(SkillError(
            code=SkillErrorCode.SKILL_LOAD_FAILED,
            skill_name=skill_name,
            detail="SKILL.md file not found",
            file_path=skill_md,
        ))
        return errors

    try:
        import yaml
    except ImportError:
        # Fallback: basic parsing without PyYAML
        yaml = None

    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        parts = content.split("---", 2)
        if len(parts) < 3:
            errors.append(SkillError(
                code=SkillErrorCode.SKILL_INVALID_FRONTMATTER,
                skill_name=skill_name,
                detail="Missing YAML frontmatter delimiters (---)",
                file_path=skill_md,
            ))
            return errors

        if yaml:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except Exception as e:
                errors.append(SkillError(
                    code=SkillErrorCode.SKILL_PARSE_ERROR,
                    skill_name=skill_name,
                    detail=f"YAML parse error: {e}",
                    file_path=skill_md,
                ))
                return errors
        else:
            # Basic fallback parsing
            frontmatter = {}
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    frontmatter[key.strip()] = val.strip().strip("'\"")

    except Exception as e:
        errors.append(SkillError(
            code=SkillErrorCode.SKILL_LOAD_FAILED,
            skill_name=skill_name,
            detail=f"Failed to read SKILL.md: {e}",
            file_path=skill_md,
        ))
        return errors

    # Validate required fields
    if not frontmatter.get("name"):
        errors.append(SkillError(
            code=SkillErrorCode.SKILL_MISSING_NAME,
            skill_name=skill_name,
            file_path=skill_md,
        ))

    if not frontmatter.get("description"):
        errors.append(SkillError(
            code=SkillErrorCode.SKILL_MISSING_DESCRIPTION,
            skill_name=skill_name,
            file_path=skill_md,
        ))

    # Check name matches directory
    fm_name = frontmatter.get("name", "")
    if fm_name and fm_name != skill_name:
        errors.append(SkillError(
            code=SkillErrorCode.SKILL_NAME_MISMATCH,
            skill_name=skill_name,
            detail=f"Frontmatter name '{fm_name}' != directory '{skill_name}'",
            file_path=skill_md,
        ))

    # Check referenced directories
    for subdir in ["scripts", "references", "assets"]:
        subdir_path = os.path.join(skill_path, subdir)
        if subdir in content and not os.path.isdir(subdir_path):
            errors.append(SkillError(
                code=SkillErrorCode.SKILL_RESOURCE_MISSING,
                skill_name=skill_name,
                detail=f"Referenced directory '{subdir}/' not found",
                file_path=subdir_path,
            ))

    return errors
