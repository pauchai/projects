"""FastAPI application with exception handlers and route registration.

This is the main application factory that combines the project collaboration
routes with the auth routes (mounted from the auth bounded context).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth.api.dependencies import AuthenticationError as AuthAuthenticationError
from auth.api.routes.admin import router as admin_router
from auth.api.routes.auth import router as auth_router
from auth.api.routes.credentials import router as credentials_router
from auth.api.routes.oauth import router as oauth_router
from auth.api.routes.telegram import router as telegram_router
from auth.domain.oauth import OAuthAccountAlreadyLinkedError, OAuthError
from cohort_learning.api.dependencies import set_event_bus as set_cohort_event_bus
from cohort_learning.api.routes.cohorts import router as cohorts_router
from cohort_learning.api.routes.modules import router as modules_router
from cohort_learning.api.routes.progression import router as progression_router
from cohort_learning.api.routes.rewards import router as rewards_router
from cohort_learning.api.routes.tasks import router as tasks_router
from cohort_learning.application.event_handlers.competency_prerequisites_met_handler import (
    CompetencyPrerequisitesMetHandler,
)
from cohort_learning.application.event_handlers.curator_promotion_eligible_handler import (
    CuratorPromotionEligibleHandler,
)
from cohort_learning.application.event_handlers.reward_auto_grant import (
    HelperMetricsUpdatedRewardHandler,
    PeerReviewSubmittedRewardHandler,
    TopicExpertPromotedRewardHandler,
)
from cohort_learning.application.sagas.competency_achievement_saga import (
    CompetencyAchievementSaga,
)
from cohort_learning.application.sagas.curator_promotion_saga import (
    CuratorPromotionSaga,
)
from cohort_learning.domain.events import (
    CohortGraduated,
    CompetencyPrerequisitesMet,
    CuratorPromotionEligible,
    HelperMetricsUpdated,
    PeerReviewSubmitted,
    TopicExpertPromoted,
)
from cohort_learning.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork as CohortSqlAlchemyUnitOfWork,
)
from partnership.api.dependencies import set_event_bus as set_partnership_event_bus
from partnership.api.routes.earnings import router as earnings_router
from schedule.api.routes.schedule import router as schedule_router
from partnership.application.calculate_curation_commission import (    CalculateCurationCommissionUseCase,
)
from partnership.application.sagas.cohort_graduation_saga import CohortGraduationSaga
from partnership.infrastructure.sqlalchemy_unit_of_work import (
    SqlAlchemyUnitOfWork as PartnershipSqlAlchemyUnitOfWork,
)
import partnership.infrastructure.orm  # noqa: F401 — registers Partnership ORM mappings
import schedule.infrastructure.orm  # noqa: F401 — registers Schedule ORM mappings
import guarantorship.infrastructure.orm  # noqa: F401 — registers Guarantorship ORM mappings
from project_collaboration.api.dependencies import AuthenticationError
from project_collaboration.api.routes.features import router as features_router
from project_collaboration.api.routes.fund import router as fund_router
from project_collaboration.api.routes.needs import router as needs_router
from project_collaboration.api.routes.products import router as products_router
from project_collaboration.api.routes.projects import router as projects_router
from project_collaboration.infrastructure.database import (
    get_engine,
    get_session_factory,
)
from shared_kernel.in_process_event_bus import InProcessEventBus
from shared_kernel.migration import run_migrations

# CORS origins: allow frontend dev server and any custom origins.
_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run Alembic migrations on startup and wire up the EventBus."""
    engine = get_engine()
    run_migrations(engine)
    session_factory = get_session_factory(engine)

    # ---- Build shared InProcessEventBus ----
    bus = InProcessEventBus()

    # Cohort UoW factory (used by reward handlers)
    cohort_uow_factory = lambda: CohortSqlAlchemyUnitOfWork(
        session_factory, event_bus=bus
    )  # noqa: E731
    # Partnership UoW factory (used by CohortGraduatedHandler)
    partnership_uow_factory = lambda: PartnershipSqlAlchemyUnitOfWork(
        session_factory, event_bus=bus
    )  # noqa: E731

    # ---- Cohort reward auto-grant handlers ----
    bus.subscribe(
        PeerReviewSubmitted, PeerReviewSubmittedRewardHandler(cohort_uow_factory())
    )
    bus.subscribe(
        TopicExpertPromoted, TopicExpertPromotedRewardHandler(cohort_uow_factory())
    )
    bus.subscribe(
        HelperMetricsUpdated, HelperMetricsUpdatedRewardHandler(cohort_uow_factory())
    )

    # ---- Cohort sagas ----
    bus.subscribe(
        PeerReviewSubmitted,
        CompetencyAchievementSaga(uow=cohort_uow_factory(), event_bus=bus),
    )
    bus.subscribe(
        HelperMetricsUpdated,
        CuratorPromotionSaga(uow=cohort_uow_factory(), event_bus=bus),
    )

    # ---- Eligibility notification handlers (Stage 17-18) ----
    bus.subscribe(
        CompetencyPrerequisitesMet,
        CompetencyPrerequisitesMetHandler(cohort_uow_factory()),
    )
    bus.subscribe(
        CuratorPromotionEligible,
        CuratorPromotionEligibleHandler(cohort_uow_factory()),
    )

    # ---- Partnership: commission on cohort graduation ----
    calculate_commission_uc = CalculateCurationCommissionUseCase(
        partnership_uow_factory()
    )
    bus.subscribe(
        CohortGraduated,
        CohortGraduationSaga(cohort_uow_factory(), calculate_commission_uc),
    )

    # ---- Wire bus into both bounded contexts' dependency modules ----
    set_cohort_event_bus(bus)
    set_partnership_event_bus(bus)

    yield

    # Cleanup: detach bus so tests/reloads start fresh
    set_cohort_event_bus(None)
    set_partnership_event_bus(None)


def create_app() -> FastAPI:
    """Application factory: creates and configures the FastAPI app."""
    app = FastAPI(
        title="Project Collaboration API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ----- CORS middleware -----

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ----- Exception handlers -----

    @app.exception_handler(AuthenticationError)
    def handle_authentication_error(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(AuthAuthenticationError)
    def handle_auth_authentication_error(
        request: Request, exc: AuthAuthenticationError
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(OAuthError)
    def handle_oauth_error(request: Request, exc: OAuthError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(OAuthAccountAlreadyLinkedError)
    def handle_oauth_account_already_linked(
        request: Request, exc: OAuthAccountAlreadyLinkedError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(LookupError)
    def handle_lookup_error(request: Request, exc: LookupError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(PermissionError)
    def handle_permission_error(request: Request, exc: PermissionError) -> JSONResponse:
        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    # ----- Health check (used by Traefik / Docker healthcheck) -----

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    # ----- Routes -----

    app.include_router(admin_router)
    app.include_router(auth_router)
    app.include_router(credentials_router)
    app.include_router(oauth_router)
    app.include_router(projects_router)
    app.include_router(needs_router)
    app.include_router(products_router)
    app.include_router(fund_router)
    app.include_router(features_router)
    app.include_router(cohorts_router)
    app.include_router(modules_router)
    app.include_router(tasks_router)
    app.include_router(progression_router)
    app.include_router(rewards_router)
    app.include_router(earnings_router)
    app.include_router(telegram_router)
    app.include_router(schedule_router)

    return app


app = create_app()
