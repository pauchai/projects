"""Skill tag value object."""

from __future__ import annotations

import re
from dataclasses import dataclass


_VALID_PATTERN = re.compile(r"^[a-z0-9\-]+$")


@dataclass(frozen=True)
class SkillTag:
    """Immutable keyword describing a competency.

    Normalized to lowercase, stripped of whitespace.
    Only lowercase letters, digits, and hyphens are allowed.
    Maximum length: 50 characters.
    """

    value: str

    def __init__(self, raw: str) -> None:
        normalized = raw.strip().lower()
        if not normalized:
            raise ValueError("SkillTag cannot be empty")
        if len(normalized) > 50:
            raise ValueError("SkillTag cannot exceed 50 characters")
        if not _VALID_PATTERN.match(normalized):
            raise ValueError(
                "SkillTag must contain only lowercase letters, digits, and hyphens"
            )
        object.__setattr__(self, "value", normalized)
