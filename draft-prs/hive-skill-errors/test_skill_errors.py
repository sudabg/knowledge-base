"""Tests for structured skill error codes and diagnostics."""

import json
import os
import tempfile

import pytest

from framework.skills.errors import (
    SkillError,
    SkillErrorCode,
    REMEDIATION_MAP,
    diagnose_skill,
)


class TestSkillErrorCode:
    def test_all_codes_have_remediation(self):
        """Every error code must have a remediation entry."""
        for code in SkillErrorCode:
            assert code in REMEDIATION_MAP, f"Missing remediation for {code.value}"

    def test_codes_are_prefixed(self):
        """All error codes start with SKILL_."""
        for code in SkillErrorCode:
            assert code.value.startswith("SKILL_"), f"{code.value} missing prefix"


class TestSkillError:
    def test_basic_error(self):
        err = SkillError(
            code=SkillErrorCode.SKILL_NOT_FOUND,
            skill_name="test-skill",
        )
        assert err.code == SkillErrorCode.SKILL_NOT_FOUND
        assert err.skill_name == "test-skill"
        assert "SKILL_NOT_FOUND" in str(err)
        assert "Fix:" in str(err)

    def test_to_dict(self):
        err = SkillError(
            code=SkillErrorCode.SKILL_PARSE_ERROR,
            skill_name="my-skill",
            detail="unquoted colon",
            file_path="/path/to/SKILL.md",
            line_number=5,
        )
        d = err.to_dict()
        assert d["error_code"] == "SKILL_PARSE_ERROR"
        assert d["skill_name"] == "my-skill"
        assert d["detail"] == "unquoted colon" or d["message"] == "unquoted colon"
        assert d["file_path"] == "/path/to/SKILL.md"
        assert d["line_number"] == 5
        assert "remediation" in d

    def test_default_remediation(self):
        err = SkillError(code=SkillErrorCode.SKILL_COLLISION)
        assert "Rename" in err.default_remediation or "namespace" in err.default_remediation

    def test_custom_remediation(self):
        err = SkillError(
            code=SkillErrorCode.SKILL_NOT_FOUND,
            remediation="Install it first: hive skill install foo",
        )
        assert "hive skill install foo" in err.default_remediation

    def test_json_serializable(self):
        """Error dict must be JSON serializable for API responses."""
        err = SkillError(
            code=SkillErrorCode.SKILL_TIMEOUT,
            skill_name="slow-skill",
            detail="Exceeded 30s",
        )
        serialized = json.dumps(err.to_dict())
        assert "SKILL_TIMEOUT" in serialized


class TestDiagnoseSkill:
    def test_missing_directory(self):
        errors = diagnose_skill("/nonexistent/skill")
        assert len(errors) == 1
        assert errors[0].code == SkillErrorCode.SKILL_NOT_FOUND

    def test_missing_skill_md(self, tmp_path):
        errors = diagnose_skill(str(tmp_path))
        assert len(errors) == 1
        assert errors[0].code == SkillErrorCode.SKILL_LOAD_FAILED

    def test_missing_frontmatter(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("# Just markdown, no frontmatter")
        errors = diagnose_skill(str(tmp_path))
        assert any(e.code == SkillErrorCode.SKILL_INVALID_FRONTMATTER for e in errors)

    def test_malformed_yaml(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\nname: test\ninvalid: [unclosed\n---\n")
        errors = diagnose_skill(str(tmp_path))
        assert any(e.code == SkillErrorCode.SKILL_PARSE_ERROR for e in errors)

    def test_missing_name(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\ndescription: A skill without a name\n---\n")
        errors = diagnose_skill(str(tmp_path))
        assert any(e.code == SkillErrorCode.SKILL_MISSING_NAME for e in errors)

    def test_missing_description(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\nname: test-skill\n---\n")
        errors = diagnose_skill(str(tmp_path))
        assert any(e.code == SkillErrorCode.SKILL_MISSING_DESCRIPTION for e in errors)

    def test_name_mismatch(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\nname: different-name\ndescription: Test\n---\n")
        errors = diagnose_skill(str(tmp_path))
        assert any(e.code == SkillErrorCode.SKILL_NAME_MISMATCH for e in errors)

    def test_healthy_skill(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(f"---\nname: {tmp_path.name}\ndescription: A healthy skill\n---\n")
        errors = diagnose_skill(str(tmp_path))
        assert len(errors) == 0

    def test_missing_referenced_dir(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(
            f"---\nname: {tmp_path.name}\ndescription: Test\n---\n"
            "See scripts/ for details.\n"
        )
        errors = diagnose_skill(str(tmp_path))
        assert any(
            e.code == SkillErrorCode.SKILL_RESOURCE_MISSING and "scripts" in (e.detail or "")
            for e in errors
        )
