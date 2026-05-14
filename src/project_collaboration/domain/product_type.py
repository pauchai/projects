"""ProductType enum — the category of a monetisable product offered by a project.

ref_id semantics by type:
  course   → cohort_id  (cohort_learning bounded context)
  mentoring → user_id   (mentor / curator)
  donation  → None      (free-form donation to project fund)
  onboarding → None
  other    → None
"""

from enum import Enum


class ProductType(str, Enum):
    COURSE = "course"
    MENTORING = "mentoring"
    ONBOARDING = "onboarding"
    DONATION = "donation"
    OTHER = "other"

    @property
    def requires_ref_id(self) -> bool:
        """True for types that must link to an external entity via ref_id."""
        return self in (ProductType.COURSE, ProductType.MENTORING)
