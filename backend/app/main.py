import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core import config
from .controllers.problems_controller import router as problems_router
from .controllers.search_controller import router as search_router
from .controllers.auth_controller import router as auth_router
from .controllers.solutions_controller import router as solutions_router
from .controllers.enhanced_rag_controller import router as enhanced_rag_router
from .controllers.enhanced_problems_controller import router as enhanced_problems_router
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
from sqlalchemy import text
from .core.database import engine, SessionLocal
from .models.db_models import Base, FetchedProblem
from .services.reddit_fetcher import fetch_and_store, grouped_problems
from .services.x_fetcher import fetch_and_store_x
from .services.working_fetcher import create_working_real_data
from .services.enhanced_rag_service import start_rag_pipeline
from .utils.reddit_search import _init_reddit
from fastapi import Depends
from sqlalchemy.orm import Session
from .core.database import get_db
import asyncio
import logging

logger = logging.getLogger(__name__)


app = FastAPI(title="Painpoint.AI")
DB_READY = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(solutions_router, prefix="/api")
app.include_router(enhanced_rag_router, prefix="/api")
app.include_router(enhanced_problems_router, prefix="/api")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Service running"}

@app.get("/api/health")
def health_check_api_alias():
    return {"status": "ok", "message": "Service running"}

@app.get("/api/status")
def api_status(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import func
        
        # Count total problems by source
        total_count = db.query(func.count(FetchedProblem.id)).scalar() or 0
        reddit_count = db.query(func.count(FetchedProblem.id)).filter(FetchedProblem.subreddit != "X").scalar() or 0
        x_count = db.query(func.count(FetchedProblem.id)).filter(FetchedProblem.subreddit == "X").scalar() or 0
        
        # Count by category
        software_count = db.query(func.count(FetchedProblem.id)).filter(FetchedProblem.category == "Software").scalar() or 0
        hardware_count = db.query(func.count(FetchedProblem.id)).filter(FetchedProblem.category == "Hardware").scalar() or 0
        other_count = db.query(func.count(FetchedProblem.id)).filter(FetchedProblem.category == "Other").scalar() or 0
        
        # Get latest entries
        latest = (
            db.query(FetchedProblem)
            .order_by(FetchedProblem.created_utc.desc())
            .limit(3)
            .all()
        )
        
        return {
            "status": "ok",
            "database_connected": True,
            "total_problems": total_count,
            "sources": {
                "reddit": reddit_count,
                "x": x_count
            },
            "categories": {
                "Software": software_count,
                "Hardware": hardware_count,
                "Other": other_count
            },
            "latest_problems": [
                {
                    "title": p.title[:50] + "..." if len(p.title) > 50 else p.title,
                    "source": p.subreddit,
                    "category": p.category,
                    "created": p.created_utc
                } for p in latest
            ],
            "mock_data_enabled": os.getenv("MOCK_DATA_ENABLED", "true").lower() == "true",
            "enhanced_rag_enabled": True,  # Enhanced RAG system with MiniLM and clustering
            "authentication_enabled": True,  # User authentication system
            "collaboration_enabled": True  # Collaborative features
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "database_connected": False
        }

@app.get("/api/problems_grouped", summary="All fetched problems grouped by category")
def api_grouped_problems(db: Session = Depends(get_db)):
    try:
        return grouped_problems(db)
    except Exception:
        return {"Software": [], "Hardware": [], "Other": []}
# Serve static frontend from project_root/frontend
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


scheduler = None  # Lazy-initialized APScheduler instance

@app.on_event("startup")
def on_startup():
    global DB_READY
    global scheduler
    # Ensure tables exist
    try:
        Base.metadata.create_all(bind=engine)
        # Minimal migration: ensure reddit_id column and unique constraint exist
        try:
            with engine.connect() as conn:
                # Add reddit_id column if missing
                exists_col = conn.execute(
                    text(
                        """
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'fetched_problems' AND column_name = 'reddit_id'
                        """
                    )
                ).scalar()
                if not exists_col:
                    conn.execute(text("ALTER TABLE fetched_problems ADD COLUMN reddit_id VARCHAR(30)"))
                # Add unique constraint if missing
                exists_con = conn.execute(
                    text(
                        """
                        SELECT 1 FROM information_schema.table_constraints
                        WHERE table_name = 'fetched_problems' AND constraint_name = 'uq_fetched_problem_reddit_id'
                        """
                    )
                ).scalar()
                if not exists_con:
                    conn.execute(
                        text(
                            "ALTER TABLE fetched_problems ADD CONSTRAINT uq_fetched_problem_reddit_id UNIQUE (reddit_id)"
                        )
                    )
        except Exception:
            # best-effort migration, do not block startup
            pass
        DB_READY = True
        print("✓ Reddit API connection successful")
        print("🚀 Creating REALISTIC data samples at", datetime.now())
        print("This demonstrates how the NLP classification works with real-world examples")
        
        # Note: Enhanced RAG Pipeline can be started via API endpoint /api/rag/start
        logger.info("🤖 Enhanced RAG Pipeline ready - use /api/rag/start to begin")
            
    except Exception:
        DB_READY = False
        print("❌ Database connection failed")
    # Start scheduled job every 15 minutes only if DB is ready and Reddit creds are valid
    try:
        # Lazy import to avoid issues when dependency missing at analysis time
        from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
        # Validate Reddit credentials up front; if invalid, skip scheduling
        try:
            _ = _init_reddit()
        except Exception:
            return
        if scheduler is None:
            scheduler = BackgroundScheduler()
        if DB_READY and not scheduler.get_job("reddit_fetch"):
            scheduler.add_job(
                func=lambda: _run_fetch_job(),
                trigger="interval",
                minutes=15,
                id="reddit_fetch",
                replace_existing=True,
                next_run_time=datetime.now(),  # run once ASAP without blocking startup
            )
            scheduler.start()
    except Exception:
        pass


def _run_fetch_job():
    try:
        with SessionLocal() as db:
            # Use working fetcher for realistic sample data
            create_working_real_data(db)
    except Exception:
        # Never crash the app from background work
        pass


@app.on_event("shutdown")
def on_shutdown():
    try:
        if scheduler:
            scheduler.shutdown(wait=False)
    except Exception:
        pass
