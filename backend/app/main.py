from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import analytics, faq, tickets
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API
    api_prefix = settings.api_v1_prefix
    app.include_router(tickets.router, prefix=api_prefix)
    app.include_router(faq.router, prefix=api_prefix)
    app.include_router(analytics.router, prefix=api_prefix)

    # Статические файлы (фронтенд React)
    project_root = Path(__file__).resolve().parents[2]
    frontend_root = project_root / "frontend"
    dist_dir = frontend_root / "dist"
    static_dir = dist_dir if dist_dir.exists() else frontend_root
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return app


app = create_app()


@app.on_event("startup")
def on_startup():
    # Импорт моделей для регистрации в metadata перед create_all
    from app.models import department, faq, message, model_log, ticket  # noqa: F401

    Base.metadata.create_all(bind=engine)
