import os
import time
import json
from typing import List, Dict

import praw
from dotenv import load_dotenv
from praw.models import Submission


def _load_env() -> dict:
    # Load .env into environment for local dev if present
    load_dotenv(override=False)
    # Expect values in standard env keys; strip stray quotes if present
    client_id = (os.getenv("REDDIT_CLIENT_ID") or "").strip('"')
    client_secret = (os.getenv("REDDIT_CLIENT_SECRET") or "").strip('"')
    user_agent = (os.getenv("REDDIT_USER_AGENT") or "").strip('"')

    missing = [k for k, v in {
        'REDDIT_CLIENT_ID': client_id,
    'REDDIT_CLIENT_SECRET': client_secret,
        'REDDIT_USER_AGENT': user_agent,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'user_agent': user_agent,
    }


def _init_reddit() -> praw.Reddit:
    creds = _load_env()
    # Reddit script application for read-only access
    reddit = praw.Reddit(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        user_agent=creds['user_agent'],
        check_for_async=False,
        # Add ratelimit settings to avoid API limits
        ratelimit_seconds=10
    )
    # Ensure read-only context - no user authentication needed for public subreddits
    reddit.read_only = True
    
    # Test the connection with a simple call
    try:
        # This should work without authentication for public content
        test_sub = reddit.subreddit("test")
        _ = test_sub.display_name  # This will trigger API call to verify access
        print(f"✓ Reddit API connection successful")
    except Exception as e:
        print(f"✗ Reddit API connection failed: {e}")
        raise
        
    return reddit


def _submission_to_dict(s: Submission) -> Dict:
    return {
        'id': s.id,
        'title': s.title or '',
        'text': getattr(s, 'selftext', '') or '',
        'url': s.url,
        'timestamp': int(getattr(s, 'created_utc', time.time())),
        'subreddit': str(getattr(s, 'subreddit', '')),
    }


def fetch_reddit_posts(query: str, limit: int) -> List[Dict]:
    """
    Search Reddit for recent posts matching `query`, sorted by newest.
    Returns a list of dicts: id, title, text, url, timestamp, subreddit
    """
    reddit = _init_reddit()
    results: List[Dict] = []
    try:
        # Reddit-wide search using 'all' with 'new' sorting isn't directly supported by PRAW.
        # Workaround: use 'subreddit("all").search' with sort='new'.
        # Note: Reddit search API may not always guarantee pure chronological order.
        for s in reddit.subreddit("all").search(query=query, sort="new", limit=limit):
            try:
                results.append(_submission_to_dict(s))
            except Exception:
                # Skip any problematic submission objects while continuing
                continue
    except Exception as e:
        # Handle API errors gracefully by returning what we have and a message
        results.append({
            'error': 'reddit_api_error',
            'message': str(e),
        })
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reddit search via PRAW")
    parser.add_argument("query", nargs="?", default="pain points", help="search keyword")
    parser.add_argument("--limit", type=int, default=10, help="max results")
    args = parser.parse_args()

    data = fetch_reddit_posts(args.query, args.limit)
    print(json.dumps(data, indent=2, ensure_ascii=False))
