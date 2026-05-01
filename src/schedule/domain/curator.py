"""Schedule domain entity: Curator."""

from dataclasses import dataclass, field
from datetime import datetime, time, timezone


@dataclass(frozen=True)
class AvailabilitySlot:
    """A recurring weekly availability window for a curator.

    ``weekday`` follows Python's ``datetime.weekday()`` convention:
    0 = Monday, 6 = Sunday.
    """

    slot_id: str
    curator_id: str
    weekday: int  # 0–6
    start_time: time
    end_time: time

    def __post_init__(self) -> None:
        if not 0 <= self.weekday <= 6:
            raise ValueError("weekday must be between 0 (Mon) and 6 (Sun)")
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")


class Curator:
    """Curator aggregate root for the Schedule bounded context.

    A curator has a list of free-text skills and availability slots
    that define when they can accept consultations.
    """

    def __init__(
        self,
        curator_id: str,
        name: str,
        skills: list[str] | None = None,
    ) -> None:
        name = name.strip()
        if not name:
            raise ValueError("Curator name cannot be empty")

        self.curator_id = curator_id
        self.name = name
        self.skills: list[str] = skills or []
        self.availability_slots: list[AvailabilitySlot] = []
        self.created_at: datetime = datetime.now(timezone.utc)

    def add_skill(self, skill: str) -> None:
        """Add a free-text skill. Duplicate skills are ignored."""
        skill = skill.strip()
        if not skill:
            raise ValueError("Skill cannot be empty")
        if skill not in self.skills:
            self.skills.append(skill)

    def remove_skill(self, skill: str) -> None:
        """Remove a skill. Raises if skill not found."""
        if skill not in self.skills:
            raise ValueError(f"Skill '{skill}' not found")
        self.skills.remove(skill)

    def add_availability_slot(self, slot: AvailabilitySlot) -> None:
        """Add an availability slot. Raises if it overlaps an existing slot."""
        for existing in self.availability_slots:
            if existing.weekday == slot.weekday and self._overlaps(existing, slot):
                raise ValueError(
                    f"Slot overlaps with existing slot on weekday {slot.weekday}"
                )
        self.availability_slots.append(slot)

    def remove_availability_slot(self, slot_id: str) -> None:
        """Remove an availability slot by ID. Raises if not found."""
        for slot in self.availability_slots:
            if slot.slot_id == slot_id:
                self.availability_slots.remove(slot)
                return
        raise ValueError(f"Slot '{slot_id}' not found")

    @staticmethod
    def _overlaps(a: AvailabilitySlot, b: AvailabilitySlot) -> bool:
        return a.start_time < b.end_time and b.start_time < a.end_time
