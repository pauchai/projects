"""ProductVisibility enum — who can see this product."""

from enum import Enum


class ProductVisibility(str, Enum):
    PUBLIC = "public"
    MEMBERS_ONLY = "members_only"
