"""FastAPI application factory for the Schedule bounded context."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from schedule.api.routes.schedule import router as schedule_router


def create_schedule_app() -> FastAPI:
    """Application factory for the Schedule API."""
    app = FastAPI(title="Schedule API", version="0.1.0")

    @app.exception_handler(ValueError)
    def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(LookupError)
    def handle_lookup_error(request: Request, exc: LookupError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    app.include_router(schedule_router)

    return app
