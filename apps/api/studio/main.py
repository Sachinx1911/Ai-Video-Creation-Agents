"""FastAPI application entry point.

Run (dev):  uvicorn studio.main:app --host 127.0.0.1 --port 8000 --reload
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from studio.api.routes import assets, jobs, projects, system
from studio.core.config import get_settings
from studio.core.errors import StudioError
from studio.core.logging import configure_logging
from studio.core.paths import UnsafePathError

log = logging.getLogger("studio.api")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="AI Video Studio API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

    @app.exception_handler(StudioError)
    async def studio_error(_: Request, exc: StudioError):
        return JSONResponse({"error": exc.code, "detail": exc.message}, status_code=exc.status_code)

    @app.exception_handler(UnsafePathError)
    async def unsafe_path(_: Request, exc: UnsafePathError):
        log.warning("blocked unsafe path: %s", exc)
        return JSONResponse({"error": "unsafe_path", "detail": "invalid file path"}, status_code=400)

    for r in (system.router, projects.router, assets.router, jobs.router):
        app.include_router(r, prefix="/api")
    return app


app = create_app()
