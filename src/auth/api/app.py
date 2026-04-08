"""FastAPI application factory for the Auth bounded context.

Provides a standalone app for testing. In production, the auth router
will be mounted into the main project_collaboration app (Phase 5).
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auth.api.dependencies import AuthenticationError
from auth.api.routes.auth import router as auth_router
from auth.api.routes.credentials import router as credentials_router
from auth.api.routes.oauth import router as oauth_router
from auth.api.routes.telegram import router as telegram_router
from auth.domain.oauth import OAuthError


def create_auth_app() -> FastAPI:
    """Application factory: creates and configures the Auth FastAPI app."""
    app = FastAPI(title="Auth API", version="0.1.0")

    # ----- Exception handlers -----

    @app.exception_handler(AuthenticationError)
    def handle_authentication_error(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(OAuthError)
    def handle_oauth_error(request: Request, exc: OAuthError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(LookupError)
    def handle_lookup_error(request: Request, exc: LookupError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    # ----- Routes -----

    app.include_router(auth_router)
    app.include_router(credentials_router)
    app.include_router(oauth_router)
    app.include_router(telegram_router)

    return app
