import json
from typing import List, Dict
import os
import snscrape.modules.twitter as sntwitter
import certifi


def fetch_x_posts_snscrape(query: str, limit: int = 20) -> List[Dict]:
    out: List[Dict] = []
    # Ensure requests/certifi uses a proper CA bundle
    ca = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", ca)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ca)
    os.environ.setdefault("CURL_CA_BUNDLE", ca)
    try:
        # Use "since_time" or additional filters in the query if needed
        for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
            if i >= limit:
                break
            out.append({
                "id": str(tweet.id),
                "text": tweet.rawContent,
                "timestamp": tweet.date.isoformat() if getattr(tweet, 'date', None) else None,
                "url": tweet.url,
                "author_id": str(tweet.user.id) if getattr(tweet, 'user', None) else None,
                "username": getattr(tweet.user, 'username', None) if getattr(tweet, 'user', None) else None,
            })
    except Exception as e:
        out.append({"error": "x_scrape_error", "message": str(e)})
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="X scrape via snscrape")
    parser.add_argument("query", nargs="?", default="pain points")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    res = fetch_x_posts_snscrape(args.query, args.limit)
    print(json.dumps(res, indent=2, ensure_ascii=False))
