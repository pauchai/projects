"""Tests for PendingCuratorPromotion domain entity (Stage 18)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cohort_learning.domain.pending_curator_promotion import PendingCuratorPromotion


def _make_record(**overrides: object) -> PendingCuratorPromotion:
    defaults: dict[str, object] = {
        "pending_id": "p1",
        "learner_id": "learner1",
        "module_id": "module1",
        "cohort_id": "c1",
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return PendingCuratorPromotion(**defaults)  # type: ignore[arg-type]


class TestPendingCuratorPromotionCreation:
    def test_stores_all_fields(self) -> None:
        ts = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
        record = PendingCuratorPromotion(
            pending_id="p1",
            learner_id="learner1",
            module_id="m1",
            cohort_id="c1",
            created_at=ts,
        )
        assert record.pending_id == "p1"
        assert record.learner_id == "learner1"
        assert record.module_id == "m1"
        assert record.cohort_id == "c1"
        assert record.created_at == ts

    def test_two_records_with_same_pending_id_are_equal(self) -> None:
        r1 = _make_record(pending_id="same")
        r2 = _make_record(pending_id="same", learner_id="other")
        assert r1 == r2

    def test_two_records_with_different_pending_id_are_not_equal(self) -> None:
        r1 = _make_record(pending_id="p1")
        r2 = _make_record(pending_id="p2")
        assert r1 != r2

    def test_is_hashable_by_pending_id(self) -> None:
        r1 = _make_record(pending_id="p1")
        r2 = _make_record(pending_id="p1", learner_id="other")
        assert hash(r1) == hash(r2)

    def test_different_pending_ids_give_different_hashes(self) -> None:
        r1 = _make_record(pending_id="p1")
        r2 = _make_record(pending_id="p2")
        assert hash(r1) != hash(r2)

    def test_can_be_used_in_set(self) -> None:
        records = {_make_record(pending_id="p1"), _make_record(pending_id="p2")}
        assert len(records) == 2

    def test_repr_contains_key_fields(self) -> None:
        record = _make_record(pending_id="p1", learner_id="learner1")
        r = repr(record)
        assert "p1" in r
        assert "learner1" in r
