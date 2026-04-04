"""FastAPI application with exception handlers and route registration."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from project_collaboration.api.routes.projects import router as projects_router


def create_app() -> FastAPI:
    """Application factory: creates and configures the FastAPI app."""
    app = FastAPI(title="Project Collaboration API", version="0.1.0")

    # ----- Exception handlers -----

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

    app.include_router(projects_router)

    return app


app = create_app()
