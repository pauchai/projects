from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Guarantorship:
    """Active guarantorship created when a GuaranteeRequest is accepted."""

    guarantorship_id: str
    guarantor_id: str
    ward_id: str
    request_id: str
    created_at: datetime
