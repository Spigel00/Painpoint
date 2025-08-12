import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

from sqlalchemy.orm import Session
from praw.models import Submission

from ..core.database import SessionLocal
from ..models.db_models import FetchedProblem
from ..services.ai_service import classify_category
from ..utils.reddit_search import _init_reddit

# Extended subreddits for comprehensive problem/solution discovery
SUBREDDITS = [
    "techsupport",
    "software", 
    "hardware",
    "AskProgramming",
    "learnprogramming",
    "webdev",
    "bugs",
    "startups",
    "Entrepreneur",
    "needadvice",
    "sysadmin",
    "programming",
    "computerscience",
    "ITCareerQuestions",
    "linuxquestions",
    "windows",
    "MacOS",
    "androiddev",
    "iOSProgramming",
    "gamedev"
]

THROTTLE_SECONDS = 2.0  # polite throttle between pages to avoid rate limits


def _validate_reddit() -> None:
    # Ensure env is present and Reddit client works; _init_reddit will raise if missing
    reddit = _init_reddit()
    # Simple no-op call to validate credentials (me attribute reads without extra scopes)
    _ = reddit.read_only


def _classify_keyword(title: str, body: str) -> str:
    """Enhanced keyword classification for comprehensive problem categorization"""
    t = f"{title}\n{body}".lower()
    
    # Software-related keywords (expanded)
    sw_keywords = [
        "bug", "software", "app", "code", "deploy", "crash", "error", "api", 
        "database", "web", "frontend", "backend", "programming", "script",
        "website", "browser", "javascript", "python", "java", "css", "html",
        "framework", "library", "npm", "pip", "git", "github", "deployment",
        "server", "cloud", "aws", "docker", "kubernetes", "microservice",
        "authentication", "authorization", "security", "vulnerability",
        "performance", "optimization", "memory leak", "timeout", "exception",
        "syntax error", "runtime error", "compilation", "debugging"
    ]
    
    # Hardware-related keywords (expanded)  
    hw_keywords = [
        "device", "hardware", "battery", "screen", "keyboard", "printer", 
        "cpu", "gpu", "disk", "router", "sensor", "motherboard", "ram",
        "memory", "storage", "ssd", "hdd", "usb", "hdmi", "bluetooth",
        "wifi", "ethernet", "network card", "graphics card", "power supply",
        "cooling", "fan", "temperature", "overheating", "cable", "port",
        "connector", "peripheral", "monitor", "speaker", "microphone",
        "webcam", "mouse", "trackpad", "driver", "firmware", "bios"
    ]
    
    if any(keyword in t for keyword in sw_keywords):
        return "Software"
    if any(keyword in t for keyword in hw_keywords):
        return "Hardware"
    return "Other"


def _fetch_iter_all(subreddit_name: str, limit: Optional[int] = None):
    reddit = _init_reddit()
    sub = reddit.subreddit(subreddit_name)
    # Prefer new to walk history; for very old items, top(all) is another option
    generator = sub.new(limit=limit)
    for s in generator:
        yield s


def fetch_and_store(db: Session, sleep_between_pages: float = THROTTLE_SECONDS) -> Dict[str, int]:
    """Fetch ALL historical posts across target subreddits, classify, and store.
    De-duplicate by Reddit post ID. Throttle between sub requests to avoid rate limits.
    Fetches from both 'hot', 'new', and 'top' to get comprehensive coverage.
    """
    counts = {"inserted": 0, "skipped": 0, "errors": 0}
    try:
        _validate_reddit()
    except Exception as e:
        print(f"Reddit validation failed: {e}")
        return counts

    # Bound how deep we go per run per sorting method
    try:
        max_per_sub_per_sort = int(os.getenv("REDDIT_MAX_PER_SUB_PER_SORT", "1000"))
    except Exception:
        max_per_sub_per_sort = 1000

    for name in SUBREDDITS:
        print(f"Fetching from r/{name}...")
        try:
            reddit = _init_reddit()
            subreddit = reddit.subreddit(name)
            
            # Fetch from multiple sources for comprehensive coverage
            sources = [
                ("hot", subreddit.hot(limit=max_per_sub_per_sort)),
                ("new", subreddit.new(limit=max_per_sub_per_sort)),
                ("top_all", subreddit.top(time_filter="all", limit=max_per_sub_per_sort))
            ]
            
            for source_name, submissions in sources:
                print(f"  Processing {source_name} posts...")
                processed = 0
                
                for s in submissions:
                    try:
                        assert isinstance(s, Submission)
                        rid = (getattr(s, "id", None) or "").strip()
                        title = (getattr(s, "title", "") or "").strip()
                        body = (getattr(s, "selftext", "") or "").strip()
                        url = (getattr(s, "url", "") or "").strip()
                        created = int(getattr(s, "created_utc", time.time()))
                        
                        if not rid or not title:
                            counts["skipped"] += 1
                            continue
                            
                        # Skip if already in DB by reddit_id
                        exists = (
                            db.query(FetchedProblem.id)
                            .filter(FetchedProblem.reddit_id == rid)
                            .first()
                        )
                        if exists:
                            counts["skipped"] += 1
                            continue

                        # Fast keyword classify
                        category = _classify_keyword(title, body)

                        obj = FetchedProblem(
                            title=title,
                            description=body,
                            subreddit=name,
                            category=category,
                            url=url,
                            reddit_id=rid,
                            created_utc=created,
                        )
                        db.add(obj)
                        db.commit()
                        counts["inserted"] += 1
                        processed += 1
                        
                        # Light throttle every 50 items
                        if processed % 50 == 0:
                            time.sleep(1)
                            print(f"    Processed {processed} posts from {source_name}")
                            
                    except Exception as e:
                        db.rollback()
                        counts["skipped"] += 1
                        counts["errors"] += 1
                        
                # Pause between different sorting methods
                time.sleep(sleep_between_pages)
                
            # Polite pause between subreddits
            time.sleep(sleep_between_pages * 2)
            print(f"  Completed r/{name}")
            
        except Exception as e:
            print(f"Error processing r/{name}: {e}")
            counts["errors"] += 1
            continue

    print(f"Reddit fetch completed: {counts}")
    return counts


def grouped_problems(db: Session) -> Dict[str, List[Dict]]:
    rows = (
        db.query(FetchedProblem)
        .order_by(FetchedProblem.created_utc.desc())
        .all()
    )
    out: Dict[str, List[Dict]] = {"Software": [], "Hardware": [], "Other": []}
    for r in rows:
        out.setdefault(r.category, []).append(
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "subreddit": r.subreddit,
                "category": r.category,
                "url": r.url,
                "created_utc": r.created_utc,
            }
        )
    return out


if __name__ == "__main__":
    print("Testing Reddit fetcher...")
    try:
        _validate_reddit()
        print("✓ Reddit credentials valid")
    except Exception as e:
        print(f"✗ Reddit credentials invalid: {e}")
        exit(1)
    
    with SessionLocal() as db:
        print("Starting Reddit fetch...")
        result = fetch_and_store(db)
        print("Reddit fetch results:", result)
        
        print("\nGrouped problems summary:")
        grouped = grouped_problems(db)
        for category, posts in grouped.items():
            print(f"  {category}: {len(posts)} posts")
            if posts:
                print(f"    Latest: {posts[0]['title'][:50]}...")
