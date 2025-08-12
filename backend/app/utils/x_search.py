import json
import subprocess
from typing import List, Dict


def fetch_x_posts(query: str, limit: int = 10) -> List[Dict]:
    """
    Search tweets using snscrape instead of the paid X API.
    Returns a list of dicts similar to the old API format.
    """
    try:
        # Run snscrape CLI for Twitter search
        cmd = [
            "snscrape",
            "--jsonl",
            f"--max-results={limit}",
            f"twitter-search:{query}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        out: List[Dict] = []
        for line in result.stdout.splitlines():
            tweet = json.loads(line)
            out.append({
                "id": tweet.get("id"),
                "text": tweet.get("content", ""),
                "timestamp": tweet.get("date"),
                "url": tweet.get("url"),
                "author_id": tweet.get("user", {}).get("username"),
            })
        return out

    except subprocess.CalledProcessError as e:
        return [{"error": "snscrape_error", "message": e.stderr}]
    except Exception as e:
        return [{"error": "snscrape_exception", "message": str(e)}]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="X (Twitter) search via snscrape")
    parser.add_argument("query", nargs="?", default="pain points")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    res = fetch_x_posts(args.query, args.limit)
    print(json.dumps(res, indent=2, ensure_ascii=False))
