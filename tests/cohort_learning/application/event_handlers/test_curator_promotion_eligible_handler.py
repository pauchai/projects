"""Tests for CuratorPromotionEligibleHandler (Stage 18).

The handler listens to ``CuratorPromotionEligible`` events and persists a
``PendingCuratorPromotion`` record so Masters can discover who
needs promotion.
"""

from __future__ import annotations

import pytest

from cohort_learning.application.event_handlers.curator_promotion_eligible_handler import (
    CuratorPromotionEligibleHandler,
)
from cohort_learning.domain.events import CuratorPromotionEligible
from cohort_learning.domain.module_curator import ModuleCurator
from cohort_learning.domain.pending_curator_promotion import PendingCuratorPromotion
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


def _make_event(
    learner_id: str = "learner1",
    module_id: str = "mod1",
    cohort_id: str = "c1",
) -> CuratorPromotionEligible:
    return CuratorPromotionEligible(
        cohort_id=cohort_id,
        learner_id=learner_id,
        module_id=module_id,
    )


class TestCuratorPromotionEligibleHandlerSavesRecord:
    def test_saves_pending_record_on_event(self) -> None:
        uow = FakeUnitOfWork()
        handler = CuratorPromotionEligibleHandler(uow)

        handler.handle(_make_event())

        records = uow.pending_curator_promotions.find_by_cohort("c1")
        assert len(records) == 1
        assert records[0].learner_id == "learner1"
        assert records[0].module_id == "mod1"
        assert records[0].cohort_id == "c1"
        assert records[0].pending_id is not None

    def test_pending_id_is_non_empty_string(self) -> None:
        uow = FakeUnitOfWork()
        handler = CuratorPromotionEligibleHandler(uow)
        handler.handle(_make_event())
        records = uow.pending_curator_promotions.find_by_cohort("c1")
        assert isinstance(records[0].pending_id, str)
        assert len(records[0].pending_id) > 0

    def test_created_at_is_set(self) -> None:
        from datetime import datetime

        uow = FakeUnitOfWork()
        handler = CuratorPromotionEligibleHandler(uow)
        handler.handle(_make_event())
        records = uow.pending_curator_promotions.find_by_cohort("c1")
        assert isinstance(records[0].created_at, datetime)

    def test_commits_after_saving(self) -> None:
        uow = FakeUnitOfWork()
        handler = CuratorPromotionEligibleHandler(uow)
        handler.handle(_make_event())
        assert uow.committed is True


class TestCuratorPromotionEligibleHandlerIdempotency:
    def test_does_not_duplicate_record_on_second_event(self) -> None:
        uow = FakeUnitOfWork()
        handler = CuratorPromotionEligibleHandler(uow)

        handler.handle(_make_event())
        handler.handle(_make_event())  # same learner/module/cohort

        records = uow.pending_curator_promotions.find_by_cohort("c1")
        assert len(records) == 1

    def test_saves_separate_records_for_different_learners(self) -> None:
        uow = FakeUnitOfWork()
        handler = CuratorPromotionEligibleHandler(uow)

        handler.handle(_make_event(learner_id="learner1"))
        handler.handle(_make_event(learner_id="learner2"))

        records = uow.pending_curator_promotions.find_by_cohort("c1")
        assert len(records) == 2

    def test_saves_separate_records_for_different_modules(self) -> None:
        uow = FakeUnitOfWork()
        handler = CuratorPromotionEligibleHandler(uow)

        handler.handle(_make_event(module_id="mod1"))
        handler.handle(_make_event(module_id="mod2"))

        records = uow.pending_curator_promotions.find_by_cohort("c1")
        assert len(records) == 2

    def test_does_not_skip_save_when_module_curator_already_exists(self) -> None:
        """Handler saves unconditionally — filtering happens at query time."""
        from datetime import datetime, timezone

        uow = FakeUnitOfWork()
        with uow:
            uow.module_curators.save(
                ModuleCurator(
                    curator_id="cur1",
                    learner_id="learner1",
                    module_id="mod1",
                    cohort_id="c1",
                    promoted_at=datetime.now(tz=timezone.utc),
                    promoted_by="master1",
                )
            )
            uow.commit()

        handler = CuratorPromotionEligibleHandler(uow)
        handler.handle(_make_event())

        records = uow.pending_curator_promotions.find_by_cohort("c1")
        assert len(records) == 1
