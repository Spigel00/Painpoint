#!/usr/bin/env python3
"""
Pre-processing Script for RAG System
Fetches Reddit posts, processes with NLP, generates embeddings, and stores in vector DB
Run this BEFORE hosting the server
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List

# Add paths for imports
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "backend"))

from backend.app.utils.reddit_search import _init_reddit
from backend.app.config.subreddits import PAINPOINT_SUBREDDITS
from backend.app.services.nlp_processor import process_post
from backend.app.services.vector_store import VectorStore

class RAGPreprocessor:
    """Pre-process Reddit data for RAG system"""
    
    def __init__(self):
        print("🚀 Initializing RAG Preprocessor...")
        
        # Initialize components
        self.reddit = _init_reddit()
        self.vector_store = VectorStore()
        
        # Processing stats
        self.total_attempted = 0
        self.total_processed = 0
        self.processing_errors = 0
        
        print("✅ RAG Preprocessor initialized")
    
    def is_valid_problem_post(self, title: str, body: str = "") -> bool:
        """Enhanced problem detection with tech filtering"""
        text = f"{title} {body}".lower()
        
        # Tech keywords (must have at least one)
        tech_keywords = [
            'python', 'javascript', 'java', 'c++', 'c#', 'react', 'angular', 'vue', 'node', 'php', 'html', 'css', 'sql',
            'windows', 'linux', 'mac', 'android', 'ios', 'ubuntu', 'docker', 'kubernetes',
            'git', 'vs code', 'postgresql', 'mysql', 'mongodb', 'api', 'aws', 'azure', 'github',
            'error', 'crash', 'bug', 'fail', 'broken', 'timeout', 'exception',
            'install', 'setup', 'configure', 'deploy', 'build', 'compile', 'debug', 'code', 'programming',
            'software', 'hardware', 'computer', 'laptop', 'server', 'database', 'network', 'wifi'
        ]
        
        # Must have tech content
        has_tech = any(keyword in text for keyword in tech_keywords)
        if not has_tech:
            return False
        
        # Exclude non-tech topics
        non_tech_exclusions = [
            'relationship', 'dating', 'girlfriend', 'boyfriend', 'marriage', 'divorce',
            'politics', 'election', 'trump', 'biden', 'government', 'voting',
            'religion', 'god', 'church', 'prayer', 'bible',
            'sports', 'football', 'basketball', 'soccer', 'baseball',
            'food', 'recipe', 'cooking', 'restaurant', 'eating',
            'movie', 'netflix', 'tv show', 'celebrity', 'actor',
            'weight loss', 'diet', 'fitness', 'workout', 'gym',
            'medical', 'doctor', 'hospital', 'medicine', 'health',
            'travel', 'vacation', 'tourist', 'trip'
        ]
        
        for exclusion in non_tech_exclusions:
            if exclusion in text:
                return False
        
        # Problem indicators
        problem_indicators = [
            'help', 'issue', 'problem', 'error', 'bug', 'crash', 'fail', 'broken',
            'not working', "can't", "won't", "doesn't work", 'troubleshoot',
            'fix', 'solve', 'debug', 'stuck', 'struggling', 'how to', 'why', 'what'
        ]
        
        # Non-problem exclusions
        exclusions = [
            'tutorial', 'guide', 'showcase', 'announcement', 'news',
            'ama', 'discussion', 'just wanted to share', 'check out my'
        ]
        
        has_problem = any(indicator in text for indicator in problem_indicators)
        is_excluded = any(exclusion in text for exclusion in exclusions)
        
        return has_problem and not is_excluded
    
    def categorize_post(self, title: str, body: str) -> str:
        """Categorize tech posts"""
        text = f"{title} {body}".lower()
        
        categories = {
            'Web Development': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'nodejs', 'express', 'frontend', 'backend'],
            'Mobile Development': ['android', 'ios', 'react native', 'flutter', 'swift', 'kotlin', 'mobile app'],
            'Software Development': ['python', 'java', 'c++', 'c#', 'programming', 'algorithm', 'code', 'git'],
            'System Administration': ['linux', 'ubuntu', 'server', 'devops', 'deployment', 'docker', 'kubernetes'],
            'Database': ['mysql', 'postgresql', 'mongodb', 'sql', 'database', 'db'],
            'Hardware/Performance': ['performance', 'slow', 'memory', 'cpu', 'hardware', 'gpu', 'ram'],
            'Cloud/DevOps': ['aws', 'azure', 'cloud', 'docker', 'kubernetes', 'deployment', 'ci/cd'],
            'Security': ['security', 'auth', 'authentication', 'encryption', 'vulnerability', 'hack']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'General Tech'
    
    def process_single_post(self, post) -> Dict:
        """Process a single Reddit post"""
        try:
            self.total_attempted += 1
            
            title = post.title.strip()
            body = post.selftext.strip() if hasattr(post, 'selftext') else ""
            
            # Skip if not a valid problem
            if not self.is_valid_problem_post(title, body):
                return None
            
            # Generate AI problem statement
            combined_text = f"{title}. {body}".strip()
            ai_statement = process_post(combined_text[:800])  # Truncate for processing
            
            # Categorize
            category = self.categorize_post(title, body)
            
            # Create document
            document = {
                "title": title,
                "description": body[:500] + "..." if len(body) > 500 else body,
                "ai_problem_statement": ai_statement,
                "category": category,
                "subreddit": post.subreddit.display_name if hasattr(post.subreddit, 'display_name') else 'unknown',
                "url": f"https://reddit.com{post.permalink}",
                "created_utc": int(post.created_utc),
                "processed_at": datetime.now().isoformat(),
                "score": post.score if hasattr(post, 'score') else 0,
                "num_comments": post.num_comments if hasattr(post, 'num_comments') else 0
            }
            
            self.total_processed += 1
            return document
            
        except Exception as e:
            self.processing_errors += 1
            print(f"❌ Error processing post: {e}")
            return None
    
    def fetch_and_process_subreddit(self, subreddit_name: str, limit: int = 100) -> List[Dict]:
        """Fetch and process posts from a single subreddit"""
        try:
            print(f"📡 Processing r/{subreddit_name}...", end=" ")
            
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Get posts from different sorting methods
            all_posts = []
            
            try:
                # Hot posts
                hot_posts = list(subreddit.hot(limit=limit//3))
                all_posts.extend(hot_posts)
                
                # New posts
                new_posts = list(subreddit.new(limit=limit//3))
                all_posts.extend(new_posts)
                
                # Top posts (week)
                top_posts = list(subreddit.top(time_filter='week', limit=limit//3))
                all_posts.extend(top_posts)
                
            except Exception as e:
                print(f"Warning: {e}")
                # Fallback to just hot
                all_posts = list(subreddit.hot(limit=limit))
            
            # Process posts
            documents = []
            for post in all_posts:
                doc = self.process_single_post(post)
                if doc:
                    documents.append(doc)
            
            print(f"✅ {len(documents)} problems found")
            return documents
            
        except Exception as e:
            print(f"❌ Error with r/{subreddit_name}: {e}")
            return []
    
    def run_full_preprocessing(self, posts_per_subreddit: int = 100) -> bool:
        """Run complete preprocessing pipeline"""
        try:
            print("🚀 Starting RAG preprocessing pipeline...")
            print(f"📊 Target: {len(PAINPOINT_SUBREDDITS)} subreddits, {posts_per_subreddit} posts each")
            
            start_time = time.time()
            all_documents = []
            
            # Process each subreddit
            for i, subreddit_name in enumerate(PAINPOINT_SUBREDDITS, 1):
                print(f"[{i}/{len(PAINPOINT_SUBREDDITS)}] ", end="")
                
                subreddit_docs = self.fetch_and_process_subreddit(subreddit_name, posts_per_subreddit)
                all_documents.extend(subreddit_docs)
                
                # Brief pause to be nice to Reddit API
                time.sleep(0.5)
            
            # Add to vector store
            if all_documents:
                print(f"\n💾 Adding {len(all_documents)} documents to vector store...")
                success = self.vector_store.add_documents(all_documents)
                
                if success:
                    # Save backup JSON
                    backup_file = f"preprocessed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "documents": all_documents,
                            "stats": {
                                "total_attempted": self.total_attempted,
                                "total_processed": self.total_processed,
                                "processing_errors": self.processing_errors,
                                "subreddits_processed": len(PAINPOINT_SUBREDDITS),
                                "processed_at": datetime.now().isoformat()
                            }
                        }, f, indent=2, ensure_ascii=False)
                    
                    processing_time = time.time() - start_time
                    
                    print(f"\n🎯 RAG Preprocessing Complete!")
                    print(f"   ⏱️ Time: {processing_time:.1f} seconds")
                    print(f"   📊 Attempted: {self.total_attempted} posts")
                    print(f"   ✅ Processed: {self.total_processed} problems")
                    print(f"   ❌ Errors: {self.processing_errors}")
                    print(f"   💾 Vector Store: {len(all_documents)} documents")
                    print(f"   📄 Backup: {backup_file}")
                    
                    # Show vector store stats
                    stats = self.vector_store.get_stats()
                    print(f"   🔍 Categories: {len(stats.get('categories', []))}")
                    
                    return True
                else:
                    print("❌ Failed to add documents to vector store")
                    return False
            else:
                print("❌ No documents processed")
                return False
                
        except Exception as e:
            print(f"❌ Preprocessing failed: {e}")
            return False
    
    def test_search(self, query: str = "React build error"):
        """Test the RAG search functionality"""
        print(f"\n🔍 Testing search: '{query}'")
        
        results = self.vector_store.search_similar(query, n_results=5)
        
        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result['title'][:60]}... (similarity: {result['similarity_score']:.3f})")
                print(f"     Category: {result['category']} | Score: {result['score']}")
        else:
            print("❌ No results found")

def main():
    """Main preprocessing function"""
    print("🤖 RAG Preprocessing Script")
    print("=" * 50)
    
    # Check if we should clear existing data
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        print("🗑️ Clearing existing vector store...")
        vs = VectorStore()
        vs.clear_collection()
    
    # Initialize preprocessor
    preprocessor = RAGPreprocessor()
    
    # Run preprocessing
    success = preprocessor.run_full_preprocessing(posts_per_subreddit=50)  # Reduced for faster testing
    
    if success:
        # Test search
        preprocessor.test_search("React build error")
        preprocessor.test_search("PostgreSQL connection timeout")
        preprocessor.test_search("Docker container crashes")
        
        print("\n✅ RAG system ready for hosting!")
        print("💡 Now run the server with: python app/server.py")
    else:
        print("\n❌ Preprocessing failed")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
