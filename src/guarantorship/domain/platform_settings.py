from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PlatformSettings:
    """Singleton platform-wide parameters (id=1)."""

    id: int  # always 1
    required_guarantors_count: int
    guarantor_ward_limit: int
    escalation_levels: int
