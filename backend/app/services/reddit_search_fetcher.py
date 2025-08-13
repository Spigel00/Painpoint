"""
Reddit Search Fetcher - Comprehensive Reddit data fetching using search queries
"""
from typing import Dict, List, Any
import logging
import time
from datetime import datetime
from sqlalchemy.orm import Session
from ..utils.reddit_search import fetch_reddit_posts
from ..services.simple_clustering_service import SimpleClusteringService
from ..services.simple_minilm_service import SimpleMiniLMService
from ..models.db_models import FetchedProblem
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


def search_and_classify_reddit_problems(
    db: Session,
    queries: List[str] = None,
    max_per_query: int = 20
) -> Dict[str, int]:
    """
    Search Reddit for problems and classify them using enhanced NLP
    
    Args:
        db: Database session
        queries: List of search queries
        max_per_query: Maximum results per query
    
    Returns:
        Dictionary with counts of inserted, skipped, and errors
    """
    
    if queries is None:
        # Tech problem-focused search queries
        queries = [
            "software bug problem",
            "hardware issue not working",
            "programming error help",
            "computer problem troubleshoot",
            "app crash fix",
            "device malfunction support",
            "code error debugging",
            "system error fix",
            "network problem help",
            "gpu temperature issue",
            "cpu performance problem",
            "database connection error",
            "api not working",
            "docker container issue",
            "react error help",
            "python problem fix"
        ]
    
    counts = {"inserted": 0, "skipped": 0, "errors": 0}
    
    print(f"🔍 Searching Reddit with {len(queries)} problem-focused queries...")
    print(f"⚙️  Max per query: {max_per_query}")
    print("=" * 80)
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔎 Query {i}/{len(queries)}: '{query}'")
        
        try:
            # Use existing reddit search utility
            results = fetch_reddit_posts(query, max_per_query)
            
            if isinstance(results, list) and len(results) > 0:
                # Check if it's an error response
                if len(results) == 1 and isinstance(results[0], dict) and "error" in results[0]:
                    print(f"   ❌ Search failed: {results[0].get('message', 'Unknown error')}")
                    counts["errors"] += 1
                    continue
                
                print(f"   📊 Found {len(results)} posts")
                
                for j, post in enumerate(results, 1):
                    try:
                        if not isinstance(post, dict):
                            continue
                            
                        title = post.get("title", "").strip()
                        body = post.get("selftext", "").strip()
                        subreddit = post.get("subreddit", "unknown")
                        url = post.get("url", "")
                        post_id = post.get("id", f"search_{int(time.time())}_{j}")
                        
                        # Skip if title is too short
                        if len(title) < 10:
                            counts["skipped"] += 1
                            continue
                        
                        # Check if already exists
                        existing = (
                            db.query(FetchedProblem.id)
                            .filter(FetchedProblem.reddit_id == post_id)
                            .first()
                        )
                        
                        if existing:
                            counts["skipped"] += 1
                            continue
                        
                        print(f"   📝 Post {j}: {title[:50]}...")
                        
                        # Classify using enhanced NLP
                        # NLP processing and classification
                        clustering_service = SimpleClusteringService()
                        minilm_service = SimpleMiniLMService()
                        
                        combined_text = f"{title} {body}".strip()
                        processed_problem = minilm_service.process_text(combined_text)
                        category = clustering_service.classify_problem(processed_problem)
                        
                        # Create database entry
                        problem = FetchedProblem(
                            title=title,
                            description=body,
                            subreddit=subreddit,
                            category=category,
                            url=url,
                            reddit_id=post_id,
                            created_utc=int(time.time()),
                        )
                        
                        db.add(problem)
                        db.commit()
                        counts["inserted"] += 1
                        print(f"   ✅ Classified as: {category}")
                        
                        # Small delay between posts
                        time.sleep(0.2)
                        
                    except Exception as e:
                        db.rollback()
                        counts["errors"] += 1
                        print(f"   ❌ Error processing post {j}: {e}")
                        continue
            
            else:
                print("   📭 No results found")
            
            # Delay between queries to respect rate limits
            time.sleep(1)
            
        except Exception as e:
            counts["errors"] += 1
            print(f"❌ Error with query '{query}': {e}")
            continue
    
    print("=" * 80)
    print(f"🎯 Reddit search complete: {counts}")
    return counts


def comprehensive_reddit_search_fetch(db: Session) -> Dict[str, Dict[str, int]]:
    """Comprehensive Reddit search with enhanced NLP classification"""
    
    print(f"🚀 COMPREHENSIVE REDDIT SEARCH FETCH at {datetime.now()}")
    print("Searching Reddit for real problems with enhanced NLP classification")
    print("=" * 80)
    
    # Search with problem-focused queries
    search_results = search_and_classify_reddit_problems(
        db=db,
        max_per_query=15
    )
    
    total_inserted = search_results.get("inserted", 0)
    total_errors = search_results.get("errors", 0)
    
    print(f"\n🎯 TOTAL REDDIT PROBLEMS FOUND: {total_inserted}")
    print(f"⚠️  TOTAL ERRORS: {total_errors}")
    print("=" * 80)
    
    return {
        "search": search_results,
        "summary": {
            "total_inserted": total_inserted,
            "total_errors": total_errors,
            "note": "Reddit search completed with enhanced NLP classification"
        }
    }


if __name__ == "__main__":
    with SessionLocal() as db:
        results = comprehensive_reddit_search_fetch(db)
        print("\n🏁 Final Results:")
        import json
        print(json.dumps(results, indent=2))
