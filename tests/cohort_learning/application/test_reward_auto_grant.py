"""Tests for reward auto-grant event handlers."""

from __future__ import annotations

from cohort_learning.application.event_handlers.reward_auto_grant import (
    HelperMetricsUpdatedRewardHandler,
    PeerReviewSubmittedRewardHandler,
    TopicExpertPromotedRewardHandler,
)
from cohort_learning.domain.events import (
    HelperMetricsUpdated,
    PeerReviewSubmitted,
    TopicExpertPromoted,
)
from tests.cohort_learning.fakes.fake_unit_of_work import FakeUnitOfWork


class TestPeerReviewSubmittedRewardHandler:
    """Handler grants +10 XP to the reviewer on PeerReviewSubmitted."""

    def test_grants_10_xp_to_reviewer(self) -> None:
        """PeerReviewSubmitted triggers +10 XP for the reviewer."""
        uow = FakeUnitOfWork()
        handler = PeerReviewSubmittedRewardHandler(uow)

        event = PeerReviewSubmitted(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="learner1",
            task_id="task1",
            cohort_id="cohort1",
        )
        handler.handle(event)

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.total_xp == 10

    def test_creates_ledger_if_missing(self) -> None:
        """Handler creates a new ledger when none exists for the reviewer."""
        uow = FakeUnitOfWork()
        handler = PeerReviewSubmittedRewardHandler(uow)

        event = PeerReviewSubmitted(
            review_id="rev1",
            submission_id="sub1",
            reviewer_id="new-reviewer",
            task_id="task1",
            cohort_id="cohort1",
        )
        handler.handle(event)

        ledger = uow.reward_ledgers.find_by_learner("new-reviewer")
        assert ledger is not None

    def test_accumulates_xp_across_multiple_reviews(self) -> None:
        """Each submitted review adds +10 XP to the reviewer's ledger."""
        uow = FakeUnitOfWork()
        handler = PeerReviewSubmittedRewardHandler(uow)

        for i in range(3):
            handler.handle(
                PeerReviewSubmitted(
                    review_id=f"rev{i}",
                    submission_id=f"sub{i}",
                    reviewer_id="learner1",
                    task_id="task1",
                    cohort_id="cohort1",
                )
            )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.total_xp == 30

    def test_stores_triggering_event_name(self) -> None:
        """The entry's triggering_event references the source event."""
        uow = FakeUnitOfWork()
        handler = PeerReviewSubmittedRewardHandler(uow)

        handler.handle(
            PeerReviewSubmitted(
                review_id="rev1",
                submission_id="sub1",
                reviewer_id="learner1",
                task_id="task1",
                cohort_id="cohort1",
            )
        )

        entry = uow.reward_ledgers.find_by_learner("learner1").entries[0]
        assert entry.triggering_event == "PeerReviewSubmitted"

    def test_stores_cohort_id_in_entry(self) -> None:
        """The cohort_id from the event is stored in the reward entry."""
        uow = FakeUnitOfWork()
        handler = PeerReviewSubmittedRewardHandler(uow)

        handler.handle(
            PeerReviewSubmitted(
                review_id="rev1",
                submission_id="sub1",
                reviewer_id="learner1",
                task_id="task1",
                cohort_id="cohort-xyz",
            )
        )

        entry = uow.reward_ledgers.find_by_learner("learner1").entries[0]
        assert entry.cohort_id == "cohort-xyz"


class TestTopicExpertPromotedRewardHandler:
    """Handler grants a Topic Expert badge on TopicExpertPromoted."""

    def test_grants_badge_on_promotion(self) -> None:
        """TopicExpertPromoted triggers a Topic Expert Badge for the learner."""
        uow = FakeUnitOfWork()
        handler = TopicExpertPromotedRewardHandler(uow)

        event = TopicExpertPromoted(
            cohort_id="cohort1",
            learner_id="learner1",
            topic_id="topic-python",
        )
        handler.handle(event)

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert "topic-python" in balance.badges

    def test_badge_idempotent_for_same_topic(self) -> None:
        """Handling the same promotion event twice does not duplicate the badge."""
        uow = FakeUnitOfWork()
        handler = TopicExpertPromotedRewardHandler(uow)

        event = TopicExpertPromoted(
            cohort_id="cohort1",
            learner_id="learner1",
            topic_id="topic-python",
        )
        handler.handle(event)
        handler.handle(event)

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.badges.count("topic-python") == 1

    def test_badges_for_different_topics_are_independent(self) -> None:
        """Promotions for different topics each grant their own badge."""
        uow = FakeUnitOfWork()
        handler = TopicExpertPromotedRewardHandler(uow)

        handler.handle(
            TopicExpertPromoted(
                cohort_id="c1", learner_id="learner1", topic_id="topic-a"
            )
        )
        handler.handle(
            TopicExpertPromoted(
                cohort_id="c1", learner_id="learner1", topic_id="topic-b"
            )
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert "topic-a" in balance.badges
        assert "topic-b" in balance.badges


class TestHelperMetricsUpdatedRewardHandler:
    """Handler grants credits at 10-learner milestones and updates reputation."""

    def test_no_credits_below_10_learners_helped(self) -> None:
        """No credits granted when learners_helped is 9."""
        uow = FakeUnitOfWork()
        handler = HelperMetricsUpdatedRewardHandler(uow)

        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=9,
                tasks_reviewed=5,
            )
        )

        ledger = uow.reward_ledgers.find_by_learner("learner1")
        if ledger is None:
            balance_credits = 0
        else:
            balance_credits = ledger.get_balance().total_credits
        assert balance_credits == 0

    def test_grants_5_percent_credits_at_10_learners_helped(self) -> None:
        """5% credits granted when learners_helped reaches 10."""
        uow = FakeUnitOfWork()
        handler = HelperMetricsUpdatedRewardHandler(uow)

        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=10,
                tasks_reviewed=0,
            )
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.total_credits == 5

    def test_grants_credits_at_20_learners_helped(self) -> None:
        """Another 5% credits granted at each subsequent multiple of 10."""
        uow = FakeUnitOfWork()
        handler = HelperMetricsUpdatedRewardHandler(uow)

        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=10,
                tasks_reviewed=0,
            )
        )
        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=20,
                tasks_reviewed=0,
            )
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.total_credits == 10

    def test_no_credits_at_non_milestone_count(self) -> None:
        """No credits granted for a count like 11 (between milestones)."""
        uow = FakeUnitOfWork()
        handler = HelperMetricsUpdatedRewardHandler(uow)

        # Grant at 10 first to establish state
        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=10,
                tasks_reviewed=0,
            )
        )
        credits_at_10 = (
            uow.reward_ledgers.find_by_learner("learner1").get_balance().total_credits
        )

        # Then event with 11 — should not add more credits
        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=11,
                tasks_reviewed=0,
            )
        )
        credits_at_11 = (
            uow.reward_ledgers.find_by_learner("learner1").get_balance().total_credits
        )

        assert credits_at_11 == credits_at_10

    def test_updates_reputation_score(self) -> None:
        """Handler updates the learner's reputation score from tasks_reviewed."""
        uow = FakeUnitOfWork()
        handler = HelperMetricsUpdatedRewardHandler(uow)

        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=5,
                tasks_reviewed=8,
            )
        )

        balance = uow.reward_ledgers.find_by_learner("learner1").get_balance()
        assert balance.reputation_score is not None

    def test_reputation_score_reflects_tasks_reviewed(self) -> None:
        """The reputation score is derived from tasks_reviewed count."""
        uow = FakeUnitOfWork()
        handler = HelperMetricsUpdatedRewardHandler(uow)

        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=0,
                tasks_reviewed=10,
            )
        )
        score_10 = (
            uow.reward_ledgers.find_by_learner("learner1")
            .get_balance()
            .reputation_score
        )

        handler.handle(
            HelperMetricsUpdated(
                learner_id="learner1",
                cohort_id="cohort1",
                learners_helped=0,
                tasks_reviewed=20,
            )
        )
        score_20 = (
            uow.reward_ledgers.find_by_learner("learner1")
            .get_balance()
            .reputation_score
        )

        assert score_20 > score_10  # type: ignore[operator]


class TestRecordHelperActivityEmitsHelperMetricsUpdated:
    """RecordHelperActivity use case emits HelperMetricsUpdated."""

    def test_emits_helper_metrics_updated_on_learner_helped(self) -> None:
        """RecordHelperActivityUseCase emits HelperMetricsUpdated after saving."""
        from shared_kernel.events import DomainEvent
        from shared_kernel.in_process_event_bus import InProcessEventBus
        from cohort_learning.application.record_helper_activity import (
            RecordHelperActivityUseCase,
        )
        from cohort_learning.domain.events import HelperMetricsUpdated
        from tests.cohort_learning.factories import make_active_cohort

        captured: list[DomainEvent] = []

        class CapturingHandler:
            def handle(self, event: DomainEvent) -> None:
                captured.append(event)

        bus = InProcessEventBus()
        bus.subscribe(HelperMetricsUpdated, CapturingHandler())

        cohort = make_active_cohort(cohort_id="cohort1", master_id="master1")
        uow = FakeUnitOfWork(event_bus=bus)
        uow.cohorts.save(cohort)

        use_case = RecordHelperActivityUseCase(uow)
        use_case.execute(
            learner_id="learner1",
            cohort_id="cohort1",
            activity_type="learner_helped",
            helped_learner_id="learner2",
        )

        assert len(captured) == 1
        event = captured[0]
        assert isinstance(event, HelperMetricsUpdated)
        assert event.learner_id == "learner1"
        assert event.cohort_id == "cohort1"
        assert event.learners_helped == 1
