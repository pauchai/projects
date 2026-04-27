"""Tests for GetPendingCompetencyValidationsUseCase (Stage 17).

The use case returns PendingCompetencyValidation records for a cohort,
dynamically filtering out learners who already have a TopicCompetency
for the same (learner, topic, cohort).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cohort_learning.application.get_pending_competency_validations import (
    GetPendingCompetencyValidationsUseCase,
)
from cohort_learning.domain.cohort_role import CohortRole
from cohort_learning.domain.pending_competency_validation import (
    PendingCompetencyValidation,
)
from cohort_learning.domain.topic_competency import TopicCompetency
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.cohort_learning.factories import make_active_cohort


def _make_pending(
    learner_id: str = "learner1",
    topic_id: str = "t1",
    cohort_id: str = "c1",
    pending_id: str | None = None,
) -> PendingCompetencyValidation:
    return PendingCompetencyValidation(
        pending_id=pending_id or f"p-{learner_id}-{topic_id}",
        learner_id=learner_id,
        topic_id=topic_id,
        cohort_id=cohort_id,
        created_at=datetime.now(tz=timezone.utc),
    )


class TestGetPendingCompetencyValidationsAuthorization:
    def test_master_can_query(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert isinstance(result, list)

    def test_curator_can_query(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        # Promote learner1 to curator role
        membership = cohort.find_membership_by_learner_id("learner1")
        assert membership is not None
        membership.promote_to(CohortRole.TOPIC_EXPERT)
        membership.promote_to(CohortRole.MODULE_CURATOR)
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="learner1")
        assert isinstance(result, list)

    def test_regular_learner_cannot_query(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        with pytest.raises(PermissionError):
            use_case.execute(cohort_id="c1", caller_id="learner1")

    def test_raises_when_cohort_not_found(self) -> None:
        uow = FakeUnitOfWork()
        use_case = GetPendingCompetencyValidationsUseCase(uow)
        with pytest.raises(LookupError):
            use_case.execute(cohort_id="no-such", caller_id="master1")


class TestGetPendingCompetencyValidationsFiltering:
    def test_returns_pending_records_for_cohort(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_competency_validations.save(
                _make_pending("learner1", "t1", "c1")
            )
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert len(result) == 1
        assert result[0].learner_id == "learner1"

    def test_excludes_already_validated_learners(self) -> None:
        """Records with an existing TopicCompetency are filtered out."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_competency_validations.save(
                _make_pending("learner1", "t1", "c1")
            )
            uow.topic_competencies.save(
                TopicCompetency(
                    competency_id="comp1",
                    learner_id="learner1",
                    topic_id="t1",
                    cohort_id="c1",
                )
            )
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert len(result) == 0

    def test_returns_empty_when_no_pending_records(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert result == []

    def test_does_not_return_records_from_other_cohorts(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_competency_validations.save(
                _make_pending("learner1", "t1", "c2")
            )
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert result == []

    def test_returns_multiple_pending_records(self) -> None:
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_competency_validations.save(
                _make_pending("learner1", "t1", "c1")
            )
            uow.pending_competency_validations.save(
                _make_pending("learner2", "t2", "c1")
            )
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert len(result) == 2

    def test_partial_filter_keeps_unvalidated_records(self) -> None:
        """When one learner is validated and another is not, only unvalidated shown."""
        uow = FakeUnitOfWork()
        cohort = make_active_cohort(cohort_id="c1", master_id="master1")
        with uow:
            uow.cohorts.save(cohort)
            uow.pending_competency_validations.save(
                _make_pending("learner1", "t1", "c1")
            )
            uow.pending_competency_validations.save(
                _make_pending("learner2", "t1", "c1")
            )
            uow.topic_competencies.save(
                TopicCompetency(
                    competency_id="comp1",
                    learner_id="learner1",
                    topic_id="t1",
                    cohort_id="c1",
                )
            )
            uow.commit()

        use_case = GetPendingCompetencyValidationsUseCase(uow)
        result = use_case.execute(cohort_id="c1", caller_id="master1")
        assert len(result) == 1
        assert result[0].learner_id == "learner2"
