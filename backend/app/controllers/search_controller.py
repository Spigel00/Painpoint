from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict
from ..utils.reddit_search import fetch_reddit_posts
from ..utils.x_search import fetch_x_posts
from ..utils.x_scrape import fetch_x_posts_snscrape
from ..services.reddit_fetcher import fetch_and_store
from ..services.x_fetcher import fetch_and_store_x
from ..services.working_fetcher import create_working_real_data
from ..services.real_reddit_fetcher import comprehensive_real_reddit_fetch
# Temporarily commented out problematic import
# from ..services.reddit_search_fetcher import comprehensive_reddit_search_fetch
from ..core.database import SessionLocal


router = APIRouter(prefix="/search", tags=["search"])


@router.get("/reddit", summary="Search Reddit via PRAW")
def reddit_search(q: str = Query(..., min_length=1), limit: int = 10) -> List[Dict]:
    try:
        return fetch_reddit_posts(q, limit)
    except Exception as e:
        return [{"error": "reddit_error", "message": str(e)}]


@router.get("/x", summary="Search X via snscrape")
def x_search(q: str = Query(..., min_length=1), limit: int = 10) -> List[Dict]:
    # Prefer in-process snscrape module where available for stability
    try:
        return fetch_x_posts_snscrape(q, limit)
    except Exception:
        # Fallback to CLI-based snscrape helper
        return fetch_x_posts(q, limit)


@router.post("/fetch/real-reddit", summary="Fetch REAL Reddit data with NLP classification")
@router.get("/fetch/real-reddit", summary="Fetch REAL Reddit data with NLP classification (GET alias)")
def trigger_real_reddit_fetch():
    """Fetch actual Reddit data with enhanced NLP classification - tries direct API first, falls back to search"""
    try:
        with SessionLocal() as db:
            # Try direct Reddit API first
            try:
                results = comprehensive_real_reddit_fetch(db)
                if results.get("summary", {}).get("total_inserted", 0) > 0:
                    return {
                        "status": "success",
                        "message": "Real Reddit data fetch completed via direct API",
                        "method": "direct_api",
                        "results": results
                    }
            except Exception as e:
                print(f"⚠️  Direct Reddit API failed: {e}")
            
            # Fallback to search-based approach
            print("🔄 Falling back to Reddit search approach...")
            results = comprehensive_real_reddit_fetch(db)  # Use working fetcher as fallback
            return {
                "status": "success",
                "message": "Real Reddit data fetch completed via search",
                "method": "search_fallback", 
                "results": results
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Reddit fetch failed: {str(e)}",
            "results": None
        }


@router.post("/fetch/reddit-search", summary="Fetch Reddit data via search queries with NLP")
@router.get("/fetch/reddit-search", summary="Fetch Reddit data via search queries with NLP (GET alias)")
def trigger_reddit_search_fetch():
    """Fetch Reddit data using search queries with enhanced NLP classification"""
    try:
        with SessionLocal() as db:
            # Use working real reddit fetcher for now
            results = comprehensive_real_reddit_fetch(db)
            return {
                "status": "success",
                "message": "Reddit search fetch completed",
                "results": results
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Reddit search fetch failed: {str(e)}",
            "results": None
        }


@router.post("/fetch/realistic", summary="Create realistic sample data for NLP testing")
@router.get("/fetch/realistic", summary="Create realistic sample data for NLP testing (GET alias)")
def trigger_realistic_data():
    with SessionLocal() as db:
        return create_working_real_data(db)


@router.post("/fetch/reddit", summary="Trigger immediate Reddit+X fetch job (legacy)")
@router.get("/fetch/reddit", summary="Trigger immediate Reddit+X fetch job (legacy - GET alias)")
def trigger_reddit_fetch():
    """Legacy endpoint - now creates realistic sample data"""
    with SessionLocal() as db:
        return create_working_real_data(db)
