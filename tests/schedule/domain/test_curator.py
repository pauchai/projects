"""Unit tests for Curator and AvailabilitySlot domain entities."""

import pytest
from datetime import time

from src.schedule.domain.curator import AvailabilitySlot, Curator


def make_slot(
    slot_id: str = "slot-1",
    curator_id: str = "c-1",
    weekday: int = 0,
    start: str = "10:00",
    end: str = "12:00",
) -> AvailabilitySlot:
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return AvailabilitySlot(
        slot_id=slot_id,
        curator_id=curator_id,
        weekday=weekday,
        start_time=time(sh, sm),
        end_time=time(eh, em),
    )


class TestAvailabilitySlot:
    def test_valid_slot_creation(self) -> None:
        slot = make_slot()
        assert slot.weekday == 0
        assert slot.start_time == time(10, 0)
        assert slot.end_time == time(12, 0)

    def test_raises_when_weekday_out_of_range(self) -> None:
        with pytest.raises(ValueError, match="weekday"):
            make_slot(weekday=7)

    def test_raises_when_weekday_negative(self) -> None:
        with pytest.raises(ValueError, match="weekday"):
            make_slot(weekday=-1)

    def test_raises_when_start_equals_end(self) -> None:
        with pytest.raises(ValueError, match="start_time"):
            make_slot(start="10:00", end="10:00")

    def test_raises_when_start_after_end(self) -> None:
        with pytest.raises(ValueError, match="start_time"):
            make_slot(start="14:00", end="12:00")


class TestCuratorCreation:
    def test_creates_curator_with_defaults(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        assert curator.name == "Alice"
        assert curator.skills == []
        assert curator.availability_slots == []

    def test_strips_whitespace_from_name(self) -> None:
        curator = Curator(curator_id="c-1", name="  Bob  ")
        assert curator.name == "Bob"

    def test_raises_when_name_is_empty(self) -> None:
        with pytest.raises(ValueError, match="name"):
            Curator(curator_id="c-1", name="  ")

    def test_creates_with_initial_skills(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice", skills=["Python", "Math"])
        assert "Python" in curator.skills
        assert "Math" in curator.skills


class TestCuratorSkills:
    def test_add_skill(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        curator.add_skill("Python")
        assert "Python" in curator.skills

    def test_add_skill_ignores_duplicate(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        curator.add_skill("Python")
        curator.add_skill("Python")
        assert curator.skills.count("Python") == 1

    def test_add_skill_strips_whitespace(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        curator.add_skill("  Python  ")
        assert "Python" in curator.skills

    def test_add_skill_raises_when_empty(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        with pytest.raises(ValueError, match="empty"):
            curator.add_skill("  ")

    def test_remove_skill(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice", skills=["Python"])
        curator.remove_skill("Python")
        assert "Python" not in curator.skills

    def test_remove_skill_raises_when_not_found(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        with pytest.raises(ValueError, match="not found"):
            curator.remove_skill("Python")


class TestCuratorAvailabilitySlots:
    def test_add_slot(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        slot = make_slot(curator_id="c-1")
        curator.add_availability_slot(slot)
        assert len(curator.availability_slots) == 1

    def test_add_non_overlapping_slots_same_day(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        curator.add_availability_slot(make_slot(slot_id="s1", start="09:00", end="11:00"))
        curator.add_availability_slot(make_slot(slot_id="s2", start="11:00", end="13:00"))
        assert len(curator.availability_slots) == 2

    def test_add_slots_different_days(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        curator.add_availability_slot(make_slot(slot_id="s1", weekday=0))
        curator.add_availability_slot(make_slot(slot_id="s2", weekday=1))
        assert len(curator.availability_slots) == 2

    def test_add_overlapping_slot_raises(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        curator.add_availability_slot(make_slot(slot_id="s1", start="10:00", end="12:00"))
        with pytest.raises(ValueError, match="overlaps"):
            curator.add_availability_slot(make_slot(slot_id="s2", start="11:00", end="13:00"))

    def test_remove_slot(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        slot = make_slot(slot_id="s1", curator_id="c-1")
        curator.add_availability_slot(slot)
        curator.remove_availability_slot("s1")
        assert len(curator.availability_slots) == 0

    def test_remove_slot_raises_when_not_found(self) -> None:
        curator = Curator(curator_id="c-1", name="Alice")
        with pytest.raises(ValueError, match="not found"):
            curator.remove_availability_slot("nonexistent")
