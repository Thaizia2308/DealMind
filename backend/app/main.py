from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.db.session import init_db
from app.services.hindsight_service import HindsightError, HindsightNotConfigured, close_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()  # creates SQLite tables automatically
    yield
    close_client()


settings = get_settings()
app = FastAPI(
    title="DealMind API",
    version="1.0.0",
    description="AI sales assistant with persistent customer memory powered by Hindsight.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HindsightNotConfigured)
async def _not_configured(_: Request, exc: HindsightNotConfigured):
    return JSONResponse(status_code=503, content={"detail": str(exc), "code": "hindsight_not_configured"})


@app.exception_handler(HindsightError)
async def _hindsight_error(_: Request, exc: HindsightError):
    return JSONResponse(
        status_code=502,
        content={"detail": f"Hindsight request failed: {exc}", "code": "hindsight_error"},
    )


app.include_router(router)
