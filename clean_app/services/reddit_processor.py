#!/usr/bin/env python3
"""
Background Reddit Processor
Pre-processes Reddit posts with NLP before server starts
Caches results for instant serving
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List

# Add current directory to path for imports
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "backend"))

from backend.app.utils.reddit_search import _init_reddit
from backend.app.config.subreddits import PAINPOINT_SUBREDDITS
from backend.app.services.nlp_processor import NLPProcessor, process_post

class BackgroundRedditProcessor:
    """Background processor that pre-fetches and processes Reddit posts"""
    
    def __init__(self):
        self.reddit = _init_reddit()
        self.nlp_processor = NLPProcessor()
        self.cache_file = "processed_reddit_cache.json"
        self.processed_posts = {}
        self.last_update = None
        self.is_processing = False
        
    def truncate_for_nlp(self, text: str, max_chars: int = 800) -> str:
        """Truncate text to prevent token length errors"""
        if len(text) <= max_chars:
            return text
        
        # Try to truncate at sentence boundary
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        if last_period > max_chars * 0.7:
            return truncated[:last_period + 1]
        else:
            return truncated + "..."
    
    def generate_ai_summary(self, title: str, body: str = "") -> str:
        """Generate AI summary using the proven process_post function"""
        try:
            # Combine and clean text
            combined_text = f"{title}. {body}".strip()
            
            # Truncate to prevent token length issues
            safe_text = self.truncate_for_nlp(combined_text)
            
            # Use the proven process_post function
            result = process_post(safe_text)
            
            # Validate result
            if result and len(result.strip()) > 5 and result.strip() != safe_text.strip():
                print(f"✅ AI: {result[:50]}...")
                return result.strip()
            else:
                print("⚠️ AI validation failed, using enhanced fallback...")
                fallback = self.create_enhanced_fallback(title, body)
                print(f"   AI output: {fallback[:50]}...")
                return fallback
                
        except Exception as e:
            print(f"❌ NLP Error for '{title[:50]}...': {e}")
            return self.create_enhanced_fallback(title, body)
    
    def create_enhanced_fallback(self, title: str, body: str) -> str:
        """Create enhanced fallback summary when AI fails"""
        # Extract key technical terms
        text = f"{title} {body}".lower()
        
        # Technical keywords with more comprehensive coverage
        tech_terms = []
        tech_keywords = {
            'languages': ['python', 'javascript', 'java', 'c++', 'c#', 'react', 'angular', 'vue', 'node', 'php'],
            'platforms': ['windows', 'linux', 'mac', 'android', 'ios', 'ubuntu', 'debian', 'centos'],
            'tools': ['docker', 'git', 'vs code', 'postgresql', 'mysql', 'mongodb', 'api', 'aws', 'azure'],
            'issues': ['error', 'crash', 'slow', 'bug', 'fail', 'broken', 'timeout', 'freeze', 'lag'],
            'actions': ['install', 'setup', 'configure', 'deploy', 'build', 'compile', 'debug']
        }
        
        for category, keywords in tech_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    tech_terms.append(keyword)
        
        # Determine the main action/problem type
        if any(word in text for word in ['error', 'crash', 'fail', 'broken']):
            action = "Debug"
            problem_type = "error"
        elif any(word in text for word in ['slow', 'performance', 'lag', 'freeze']):
            action = "Optimize"
            problem_type = "performance"
        elif any(word in text for word in ['install', 'setup', 'configure']):
            action = "Setup"
            problem_type = "configuration"
        elif any(word in text for word in ['deploy', 'build', 'compile']):
            action = "Deploy"
            problem_type = "deployment"
        elif any(word in text for word in ['how to', 'how do', 'help']):
            action = "Implement"
            problem_type = "implementation"
        else:
            action = "Resolve"
            problem_type = "issue"
        
        # Create a meaningful problem statement
        if tech_terms:
            main_tech = tech_terms[0]
            if len(tech_terms) > 1:
                secondary_tech = tech_terms[1]
                statement = f"{action} {main_tech} {problem_type} affecting {secondary_tech} integration"
            else:
                statement = f"{action} {main_tech} {problem_type}"
        else:
            # Extract meaningful words from title
            title_words = []
            skip_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would', 'could', 'should'}
            
            for word in title.lower().split():
                clean_word = ''.join(c for c in word if c.isalnum())
                if clean_word and len(clean_word) > 2 and clean_word not in skip_words:
                    title_words.append(clean_word)
            
            if title_words:
                key_terms = title_words[:2]  # Take first 2 meaningful words
                statement = f"{action} {' '.join(key_terms)} {problem_type}"
            else:
                statement = title[:60] + "..." if len(title) > 60 else title
        
        return statement
    
    def is_valid_problem_post(self, title: str, body: str = "") -> bool:
        """Enhanced problem detection with tech filtering"""
        text = f"{title} {body}".lower()
        
        # FIRST: Check if it's tech-related at all
        tech_keywords = [
            'python', 'javascript', 'java', 'c++', 'c#', 'react', 'angular', 'vue', 'node', 'php', 'html', 'css', 'sql',
            'windows', 'linux', 'mac', 'android', 'ios', 'ubuntu', 'docker', 'kubernetes',
            'git', 'vs code', 'postgresql', 'mysql', 'mongodb', 'api', 'aws', 'azure', 'github',
            'error', 'crash', 'bug', 'fail', 'broken', 'timeout', 'exception',
            'install', 'setup', 'configure', 'deploy', 'build', 'compile', 'debug', 'code', 'programming',
            'software', 'hardware', 'computer', 'laptop', 'server', 'database', 'network', 'wifi'
        ]
        
        # Must have at least one tech keyword
        has_tech = any(keyword in text for keyword in tech_keywords)
        if not has_tech:
            return False
        
        # EXCLUDE non-tech topics completely
        non_tech_exclusions = [
            'relationship', 'dating', 'girlfriend', 'boyfriend', 'marriage', 'divorce',
            'politics', 'election', 'trump', 'biden', 'government', 'voting',
            'religion', 'god', 'church', 'prayer', 'bible',
            'sports', 'football', 'basketball', 'soccer', 'baseball',
            'food', 'recipe', 'cooking', 'restaurant', 'eating',
            'movie', 'netflix', 'tv show', 'celebrity', 'actor',
            'weight loss', 'diet', 'fitness', 'workout', 'gym',
            'medical', 'doctor', 'hospital', 'medicine', 'health',
            'travel', 'vacation', 'tourist', 'trip',
            'money', 'investment', 'stock', 'crypto trading', 'finance',
            'school homework', 'college assignment', 'university project'
        ]
        
        # If contains non-tech content, exclude
        for exclusion in non_tech_exclusions:
            if exclusion in text:
                return False
        
        # Strong problem indicators
        problem_indicators = [
            'help', 'issue', 'problem', 'error', 'bug', 'crash', 'fail', 'broken',
            'not working', "can't", "won't", "doesn't work", 'troubleshoot',
            'fix', 'solve', 'debug', 'stuck', 'struggling'
        ]
        
        # Exclude non-problems
        exclusions = [
            'tutorial', 'guide', 'showcase', 'announcement', 'news',
            'ama', 'discussion', 'what do you think', 'opinion',
            'just wanted to share', 'check out my'
        ]
        
        has_problem = any(indicator in text for indicator in problem_indicators)
        is_excluded = any(exclusion in text for exclusion in exclusions)
        
        # Additional check: posts with questions often indicate problems
        has_question = any(word in text for word in ['how to', 'how do', 'why', 'what', '?'])
        
        return (has_problem or has_question) and not is_excluded
    
    def categorize_post(self, title: str, body: str) -> str:
        """Enhanced categorization"""
        text = f"{title} {body}".lower()
        
        categories = {
            'Web Development': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'nodejs', 'express'],
            'Mobile Development': ['android', 'ios', 'react native', 'flutter', 'swift', 'kotlin'],
            'Software Development': ['python', 'java', 'c++', 'c#', 'programming', 'algorithm'],
            'System Administration': ['linux', 'ubuntu', 'server', 'devops', 'deployment', 'docker'],
            'Database': ['mysql', 'postgresql', 'mongodb', 'sql', 'database'],
            'Hardware/Performance': ['performance', 'slow', 'memory', 'cpu', 'hardware']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'General Tech'
    
    def fetch_and_process_all_posts(self) -> Dict:
        """Fetch and process posts from all subreddits"""
        print("🔄 Starting comprehensive Reddit processing...")
        
        categories = {
            'Web Development': [],
            'Mobile Development': [],
            'Software Development': [],
            'System Administration': [],
            'Database': [],
            'Hardware/Performance': [],
            'General Tech': []
        }
        
        total_attempted = 0
        total_processed = 0
        
        for i, subreddit_name in enumerate(PAINPOINT_SUBREDDITS, 1):
            try:
                print(f"📡 [{i}/{len(PAINPOINT_SUBREDDITS)}] r/{subreddit_name}...", end=" ")
                
                subreddit = self.reddit.subreddit(subreddit_name)
                posts = list(subreddit.hot(limit=50))
                
                problems_found = 0
                
                for post in posts:
                    total_attempted += 1
                    
                    title = post.title.strip()
                    body = post.selftext.strip() if hasattr(post, 'selftext') else ""
                    
                    # Skip if not a problem
                    if not self.is_valid_problem_post(title, body):
                        continue
                    
                    # Generate AI summary with detailed logging
                    ai_statement = self.generate_ai_summary(title, body)
                    
                    # Categorize
                    category = self.categorize_post(title, body)
                    
                    # Create problem object
                    problem = {
                        "title": title,
                        "description": body[:300] + "..." if len(body) > 300 else body,
                        "ai_problem_statement": ai_statement,
                        "subreddit": subreddit_name,
                        "url": f"https://reddit.com{post.permalink}",
                        "created_utc": int(post.created_utc),
                        "processed_at": datetime.now().isoformat(),
                        "score": post.score if hasattr(post, 'score') else 0
                    }
                    
                    categories[category].append(problem)
                    problems_found += 1
                    total_processed += 1
                
                print(f"✅ {problems_found} problems")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        # Prepare final result
        result = {
            "success": True,
            "problems": categories,
            "total_found": total_processed,
            "total_attempted": total_attempted,
            "processed_at": datetime.now().isoformat(),
            "subreddits_processed": len(PAINPOINT_SUBREDDITS)
        }
        
        print(f"\\n🎯 Processing complete:")
        print(f"   📊 Attempted: {total_attempted} posts")
        print(f"   ✅ Processed: {total_processed} problem posts")
        print(f"   🤖 All posts have AI-generated summaries")
        
        return result
    
    def save_cache(self, data: Dict):
        """Save processed data to cache file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Cache saved to {self.cache_file}")
        except Exception as e:
            print(f"❌ Cache save error: {e}")
    
    def load_cache(self) -> Dict:
        """Load processed data from cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Check if cache is still fresh (2 hours)
                cached_time = datetime.fromisoformat(data['processed_at'])
                if datetime.now() - cached_time < timedelta(hours=2):
                    print("📦 Using fresh cache")
                    return data
                else:
                    print("⏰ Cache expired, will refresh")
            
            return None
        except Exception as e:
            print(f"❌ Cache load error: {e}")
            return None
    
    def get_processed_posts(self) -> Dict:
        """Get processed posts (from cache or fresh processing)"""
        # Try cache first
        cached_data = self.load_cache()
        if cached_data:
            return cached_data
        
        # If no valid cache, process fresh
        if not self.is_processing:
            self.is_processing = True
            try:
                fresh_data = self.fetch_and_process_all_posts()
                self.save_cache(fresh_data)
                return fresh_data
            finally:
                self.is_processing = False
        else:
            return {"error": "Processing in progress"}
    
    def start_background_refresh(self):
        """Start background thread to refresh cache periodically"""
        def refresh_loop():
            while True:
                time.sleep(7200)  # Refresh every 2 hours
                print("🔄 Background refresh starting...")
                try:
                    fresh_data = self.fetch_and_process_all_posts()
                    self.save_cache(fresh_data)
                    print("✅ Background refresh complete")
                except Exception as e:
                    print(f"❌ Background refresh error: {e}")
        
        refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
        refresh_thread.start()
        print("🔄 Background refresh thread started")

def main():
    """Test the background processor"""
    processor = BackgroundRedditProcessor()
    
    print("🧪 Testing Background Reddit Processor...")
    results = processor.get_processed_posts()
    
    if results.get("success"):
        print(f"\\n✅ Success! Found {results['total_found']} problems")
        for category, problems in results["problems"].items():
            if problems:
                print(f"\\n📂 {category}: {len(problems)} problems")
                # Show first problem with AI summary
                if problems:
                    first = problems[0]
                    print(f"   📝 Title: {first['title'][:60]}...")
                    print(f"   🤖 AI: {first['ai_problem_statement']}")
                    print(f"   👥 Score: {first['score']}")

if __name__ == "__main__":
    main()
