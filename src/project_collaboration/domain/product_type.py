"""ProductType enum — the category of a monetisable product offered by a project."""

from enum import Enum


class ProductType(str, Enum):
    COURSE = "course"
    CONSULTATION = "consultation"
    MENTORING = "mentoring"
    ONBOARDING = "onboarding"
    OTHER = "other"
