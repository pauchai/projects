"""Tests for SkillTag value object."""

import pytest

from project_collaboration.domain.skill_tag import SkillTag


class TestSkillTagCreation:
    """SkillTag normalizes and validates input."""

    def test_creates_from_lowercase_string(self) -> None:
        tag = SkillTag("python")
        assert tag.value == "python"

    def test_normalizes_to_lowercase(self) -> None:
        tag = SkillTag("Python")
        assert tag.value == "python"

    def test_strips_whitespace(self) -> None:
        tag = SkillTag("  python  ")
        assert tag.value == "python"

    def test_allows_hyphens(self) -> None:
        tag = SkillTag("machine-learning")
        assert tag.value == "machine-learning"

    def test_allows_digits(self) -> None:
        tag = SkillTag("python3")
        assert tag.value == "python3"

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            SkillTag("")

    def test_rejects_whitespace_only(self) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            SkillTag("   ")

    def test_rejects_longer_than_50_chars(self) -> None:
        with pytest.raises(ValueError, match="cannot exceed 50"):
            SkillTag("a" * 51)

    def test_rejects_special_characters(self) -> None:
        with pytest.raises(ValueError, match="only lowercase letters"):
            SkillTag("python!")

    def test_rejects_spaces_inside(self) -> None:
        with pytest.raises(ValueError, match="only lowercase letters"):
            SkillTag("machine learning")


class TestSkillTagEquality:
    """SkillTag compares by value."""

    def test_equal_tags_are_equal(self) -> None:
        assert SkillTag("python") == SkillTag("python")

    def test_different_case_tags_are_equal(self) -> None:
        assert SkillTag("Python") == SkillTag("python")

    def test_different_tags_are_not_equal(self) -> None:
        assert SkillTag("python") != SkillTag("java")

    def test_can_be_used_in_set(self) -> None:
        tags = {SkillTag("python"), SkillTag("Python"), SkillTag("java")}
        assert len(tags) == 2
