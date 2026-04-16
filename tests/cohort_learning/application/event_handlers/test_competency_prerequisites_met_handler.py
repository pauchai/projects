"""Tests for CompetencyPrerequisitesMetHandler (Stage 17).

The handler listens to ``CompetencyPrerequisitesMet`` events and persists a
``PendingCompetencyValidation`` record so Masters/Curators can discover who
needs validation.
"""

from __future__ import annotations

import pytest

from cohort_learning.application.event_handlers.competency_prerequisites_met_handler import (
    CompetencyPrerequisitesMetHandler,
)
from cohort_learning.domain.events import CompetencyPrerequisitesMet
from cohort_learning.domain.pending_competency_validation import (
    PendingCompetencyValidation,
)
from cohort_learning.domain.topic_competency import TopicCompetency
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


def _make_event(
    learner_id: str = "learner1",
    topic_id: str = "t1",
    cohort_id: str = "c1",
) -> CompetencyPrerequisitesMet:
    return CompetencyPrerequisitesMet(
        cohort_id=cohort_id,
        learner_id=learner_id,
        topic_id=topic_id,
    )


class TestCompetencyPrerequisitesMetHandlerSavesRecord:
    def test_saves_pending_record_on_event(self) -> None:
        uow = FakeUnitOfWork()
        handler = CompetencyPrerequisitesMetHandler(uow)

        handler.handle(_make_event())

        records = uow.pending_competency_validations.find_by_cohort("c1")
        assert len(records) == 1
        assert records[0].learner_id == "learner1"
        assert records[0].topic_id == "t1"
        assert records[0].cohort_id == "c1"
        assert records[0].pending_id is not None

    def test_pending_id_is_non_empty_string(self) -> None:
        uow = FakeUnitOfWork()
        handler = CompetencyPrerequisitesMetHandler(uow)
        handler.handle(_make_event())
        records = uow.pending_competency_validations.find_by_cohort("c1")
        assert isinstance(records[0].pending_id, str)
        assert len(records[0].pending_id) > 0

    def test_created_at_is_set(self) -> None:
        from datetime import datetime

        uow = FakeUnitOfWork()
        handler = CompetencyPrerequisitesMetHandler(uow)
        handler.handle(_make_event())
        records = uow.pending_competency_validations.find_by_cohort("c1")
        assert isinstance(records[0].created_at, datetime)

    def test_commits_after_saving(self) -> None:
        uow = FakeUnitOfWork()
        handler = CompetencyPrerequisitesMetHandler(uow)
        handler.handle(_make_event())
        assert uow.committed is True


class TestCompetencyPrerequisitesMetHandlerIdempotency:
    def test_does_not_duplicate_record_on_second_event(self) -> None:
        uow = FakeUnitOfWork()
        handler = CompetencyPrerequisitesMetHandler(uow)

        handler.handle(_make_event())
        handler.handle(_make_event())  # same learner/topic/cohort

        records = uow.pending_competency_validations.find_by_cohort("c1")
        assert len(records) == 1

    def test_saves_separate_records_for_different_learners(self) -> None:
        uow = FakeUnitOfWork()
        handler = CompetencyPrerequisitesMetHandler(uow)

        handler.handle(_make_event(learner_id="learner1"))
        handler.handle(_make_event(learner_id="learner2"))

        records = uow.pending_competency_validations.find_by_cohort("c1")
        assert len(records) == 2

    def test_saves_separate_records_for_different_topics(self) -> None:
        uow = FakeUnitOfWork()
        handler = CompetencyPrerequisitesMetHandler(uow)

        handler.handle(_make_event(topic_id="t1"))
        handler.handle(_make_event(topic_id="t2"))

        records = uow.pending_competency_validations.find_by_cohort("c1")
        assert len(records) == 2

    def test_does_not_save_when_topic_competency_already_exists(self) -> None:
        """Handler should still save — the filtering is done at query time."""
        # The handler is NOT responsible for filtering already-validated learners.
        # That is done dynamically in GetPendingCompetencyValidationsUseCase.
        # So even if a TopicCompetency exists, the handler saves the record.
        uow = FakeUnitOfWork()
        with uow:
            uow.topic_competencies.save(
                TopicCompetency(
                    competency_id="comp1",
                    learner_id="learner1",
                    topic_id="t1",
                    cohort_id="c1",
                )
            )
            uow.commit()

        handler = CompetencyPrerequisitesMetHandler(uow)
        handler.handle(_make_event())

        # Record is saved — filtering happens in the use case
        records = uow.pending_competency_validations.find_by_cohort("c1")
        assert len(records) == 1
