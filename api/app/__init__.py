
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.test_seed import run_test_seed
from app.core.config import settings
from app.db.session import engine, SessionLocal
from app.db.base import Base

import app.models.user
import app.models.role
import app.models.log_file
import app.models.analysis
import app.models.threat_event
import app.models.explanation
import app.models.model_version
import app.models.report
import app.models.alert
import app.models.audit_log

from app.routes import auth, logs, reports, analysis, admin, dashboard
from app.db.seed import run_seed



def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    # run seeder — safe to call every startup (all checks are idempotent)
    db = SessionLocal()
    try:
        run_seed(db)
        run_test_seed(db)
    finally:
        db.close()

    application = FastAPI(
        title       = settings.APP_NAME,
        version     = settings.APP_VERSION,
        description = "AI-powered log analysis platform",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins  = ["*"],
        allow_methods  = ["*"],
        allow_headers  = ["*"],
    )

    application.include_router(auth.router)
    application.include_router(logs.router)
    application.include_router(reports.router)
    application.include_router(analysis.router)
    application.include_router(admin.router)
    application.include_router(dashboard.router)

    @application.get("/health", tags=["Health"])
    def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    return application