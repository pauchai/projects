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
from auth.api.routes.auth import router as auth_router
from auth.api.routes.credentials import router as credentials_router
from auth.api.routes.oauth import router as oauth_router
from auth.api.routes.telegram import router as telegram_router
from auth.domain.oauth import OAuthAccountAlreadyLinkedError, OAuthError
from project_collaboration.api.dependencies import AuthenticationError
from project_collaboration.api.routes.features import router as features_router
from project_collaboration.api.routes.projects import router as projects_router
from project_collaboration.infrastructure.database import get_engine
from project_collaboration.infrastructure.database import (
    create_tables as create_project_tables,
)
from auth.infrastructure.database import create_tables as create_auth_tables

# CORS origins: allow frontend dev server and any custom origins.
_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:3000"
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup (idempotent)."""
    engine = get_engine()
    create_project_tables(engine)
    create_auth_tables(engine)
    yield


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

    # ----- Routes -----

    app.include_router(auth_router)
    app.include_router(credentials_router)
    app.include_router(oauth_router)
    app.include_router(projects_router)
    app.include_router(features_router)
    app.include_router(telegram_router)

    return app


app = create_app()
