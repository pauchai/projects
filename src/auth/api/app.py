"""FastAPI application factory for the Auth bounded context.

Provides a standalone app for testing. In production, the auth router
will be mounted into the main project_collaboration app (Phase 5).
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auth.api.routes.auth import router as auth_router


def create_auth_app() -> FastAPI:
    """Application factory: creates and configures the Auth FastAPI app."""
    app = FastAPI(title="Auth API", version="0.1.0")

    # ----- Exception handlers -----

    @app.exception_handler(ValueError)
    def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(LookupError)
    def handle_lookup_error(request: Request, exc: LookupError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    # ----- Routes -----

    app.include_router(auth_router)

    return app
