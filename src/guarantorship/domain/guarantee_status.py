"""GuaranteeStatus enum — lifecycle of a guarantorship relationship."""

from enum import Enum


class GuaranteeStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
