import os
import ssl
import time
from typing import Dict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models.db_models import FetchedProblem

# Configure SSL to handle certificate issues
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Prefer python module API for snscrape
try:
    import snscrape.modules.twitter as sntwitter
    # Configure snscrape to use our SSL context
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except Exception:  # pragma: no cover - environment-specific
    sntwitter = None

# Extended queries for comprehensive problem/solution discovery
DEFAULT_X_QUERIES = [
    "pain points",
    "problem with",
    "issue with", 
    "software bug",
    "hardware problem",
    "technical issue",
    "system error",
    "app crash",
    "device malfunction",
    "network problem",
    "server down",
    "website broken",
    "code error",
    "programming problem",
    "tech support needed",
    "help needed",
    "troubleshooting",
    "not working",
    "broken feature",
    "system failure"
]


def _classify_keyword(text: str) -> str:
    """Enhanced keyword classification for comprehensive problem categorization"""
    t = (text or "").lower()
    
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


def fetch_and_store_x(db: Session) -> Dict[str, int]:
    """Fetch historical tweets across target queries, classify, and store.
    De-duplicate by tweet ID. Fetches comprehensive historical data.
    """
    counts = {"inserted": 0, "skipped": 0, "errors": 0}
    if sntwitter is None:
        print("snscrape not available for X fetching")
        return counts

    # Query terms and per-run caps from environment
    raw_queries = os.getenv("X_QUERIES", None)
    if raw_queries:
        queries = [q.strip() for q in raw_queries.split(",") if q.strip()]
    else:
        queries = DEFAULT_X_QUERIES
        
    try:
        max_per_query = int(os.getenv("X_MAX_PER_QUERY", "2000"))
    except Exception:
        max_per_query = 2000

    print(f"Starting X fetch with {len(queries)} queries, max {max_per_query} per query")

    for q in queries:
        print(f"Fetching tweets for query: '{q}'...")
        try:
            processed = 0
            scraper = sntwitter.TwitterSearchScraper(q)
            
            for tweet in scraper.get_items():
                try:
                    # Get tweet content
                    text = getattr(tweet, "rawContent", None) or getattr(tweet, "content", "")
                    if not text or len(text.strip()) < 10:  # Skip very short tweets
                        counts["skipped"] += 1
                        continue
                        
                    x_id = str(getattr(tweet, "id", "") or "").strip()
                    if not x_id:
                        counts["skipped"] += 1
                        continue
                        
                    # Get timestamp
                    tweet_date = getattr(tweet, "date", None)
                    if tweet_date:
                        created_utc = int(tweet_date.timestamp())
                    else:
                        created_utc = int(time.time())
                        
                    url = getattr(tweet, "url", f"https://twitter.com/i/status/{x_id}")

                    # Deduplicate by reuse reddit_id field for X tweet IDs
                    exists = (
                        db.query(FetchedProblem.id)
                        .filter(FetchedProblem.reddit_id == x_id)
                        .first()
                    )
                    if exists:
                        counts["skipped"] += 1
                        continue

                    # Fast keyword classification
                    category = _classify_keyword(text)
                    
                    # Create title from tweet (truncated if needed)
                    title = (text[:97] + "...") if len(text) > 100 else text
                    
                    obj = FetchedProblem(
                        title=title,
                        description=text,
                        subreddit="X",  # Use X as the "subreddit" identifier
                        category=category,
                        url=url,
                        reddit_id=x_id,  # Store tweet ID in reddit_id field
                        created_utc=created_utc,
                    )
                    
                    db.add(obj)
                    db.commit()
                    counts["inserted"] += 1
                    processed += 1
                    
                    # Break if we've hit our limit for this query
                    if processed >= max_per_query:
                        print(f"  Reached limit of {max_per_query} for query '{q}'")
                        break
                        
                    # Light throttle every 100 items
                    if processed % 100 == 0:
                        time.sleep(2)
                        print(f"  Processed {processed} tweets for '{q}'")
                        
                except Exception as e:
                    db.rollback()
                    counts["skipped"] += 1
                    counts["errors"] += 1
                    if processed % 500 == 0:  # Only log occasional errors to avoid spam
                        print(f"    Error processing tweet: {e}")
                        
            # Pause between queries to be respectful
            time.sleep(3)
            print(f"  Completed query '{q}': {processed} tweets processed")
            
        except Exception as e:
            print(f"Error with query '{q}': {e}")
            counts["errors"] += 1
            continue

    print(f"X fetch completed: {counts}")
    return counts


if __name__ == "__main__":
    print("Testing X fetcher...")
    if sntwitter is None:
        print("✗ snscrape not available")
        exit(1)
    else:
        print("✓ snscrape available")
    
    from ..core.database import SessionLocal
    
    with SessionLocal() as db:
        print("Starting X fetch...")
        result = fetch_and_store_x(db)
        print("X fetch results:", result)
