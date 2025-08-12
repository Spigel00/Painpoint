"""
Real Reddit API fetcher with enhanced NLP classification
Fetches actual data from Reddit subreddits and classifies using improved NLP
"""

import os
import time
import re
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import load_dotenv

import praw
from praw.exceptions import RedditAPIException

from ..core.database import SessionLocal
from ..models.db_models import FetchedProblem

# Load environment variables
load_dotenv()


def _is_actual_problem(title: str, body: str = "") -> bool:
    """
    Determine if a post describes an actual problem/issue that needs solving
    """
    text = f"{title}\n{body}".lower()
    
    # STRONG problem indicators - if any found, it's likely a problem
    problem_indicators = [
        # Direct problem words
        r'\b(problem|issue|trouble|error|bug|broken|failed|failing|crash|stuck|won\'t|can\'t|unable)\b',
        r'\b(not working|doesn\'t work|stops working|keeps crashing|keeps disconnecting)\b',
        r'\b(help|fix|solve|troubleshoot|debug|repair|resolve)\b',
        
        # Question patterns indicating problems
        r'\bwhy (is|does|won\'t|can\'t|isn\'t|doesn\'t|keeps)\b',
        r'\bhow (to fix|do i fix|can i solve|to troubleshoot|to repair)\b',
        r'\bwhat\'s wrong\b',
        
        # Error patterns
        r'\b(exception|traceback|stack trace|error code|exit code)\b',
        r'\b(timeout|connection|refused|denied|forbidden|memory leak)\b',
        r'\b(overheating|thermal|throttling|crashing|freezing)\b',
        
        # Hardware issues
        r'\b(gpu|cpu|ram|memory|disk|ssd|hdd).*(issue|problem|error|failing|broken)\b',
        r'\b(charging|battery|power).*(drain|issue|problem|not working)\b'
    ]
    
    # EXCLUDE general discussions, tutorials, announcements
    exclusion_patterns = [
        r'\b(tutorial|guide|how to setup|tips|best practices|announcement)\b',
        r'\b(review|comparison|vs|versus|better than|recommend|suggestion)\b',
        r'\b(showcase|sharing|built|created|made|completed|finished)\b',
        r'\b(opinion|thoughts|discussion|what do you think|looking for)\b',
        r'\b(advice for choosing|which should i|what should i buy)\b',
        r'\b(celebration|happy|congratulations|achievement)\b'
    ]
    
    # Check for problem indicators
    has_problem_indicator = any(re.search(pattern, text) for pattern in problem_indicators)
    
    # Check for exclusions
    has_exclusion = any(re.search(pattern, text) for pattern in exclusion_patterns)
    
    return has_problem_indicator and not has_exclusion


def _classify_keyword_enhanced(title: str, body: str = "") -> str:
    """Enhanced keyword classification with detailed logging and word boundary matching"""
    import re
    
    text = f"{title}\n{body}".lower()
    
    software_keywords = [
        # Core software terms
        "bug", "software", "app", "application", "program", "code", "coding",
        "script", "programming", "development", "deploy", "deployment", 
        "crash", "error", "exception", "timeout", "hang", "freeze",
        
        # Web/API terms  
        "api", "rest", "graphql", "endpoint", "http", "https", "ssl", "tls",
        "database", "sql", "nosql", "mongodb", "mysql", "postgresql", "redis",
        "web", "website", "frontend", "backend", "fullstack", "server",
        "client", "browser", "chrome", "firefox", "safari", "edge",
        
        # Languages/frameworks
        "javascript", "typescript", "python", "java", "kotlin", "swift",
        "c\\+\\+", "c#", "golang", "rust", "php", "ruby", "css", "html", "xml", "json",
        "react", "angular", "vue", "svelte", "node", "express", "django",
        "flask", "spring", "laravel", "rails", "framework", "library",
        
        # DevOps/Cloud
        "docker", "kubernetes", "k8s", "container", "microservice", "lambda",
        "cloud", "aws", "azure", "gcp", "heroku", "vercel", "netlify",
        "ci/cd", "jenkins", "github", "gitlab", "git", "version control",
        
        # Security/Auth
        "authentication", "authorization", "oauth", "jwt", "token", "session",
        "security", "vulnerability", "exploit", "encryption", "decryption",
        "ssl certificate", "https certificate", "cors", "csrf",
        
        # Performance/Monitoring
        "performance", "optimization", "slow", "memory leak", "cpu usage",
        "profiling", "monitoring", "logging", "debugging", "trace", "stack trace",
        
        # Build/Package management
        "npm", "pip", "composer", "maven", "gradle", "webpack", "vite",
        "build", "compilation", "syntax error", "runtime error", "compile error"
    ]
    
    hardware_keywords = [
        # Core hardware
        "hardware", "device", "computer", "laptop", "desktop", "workstation",
        "server", "mainframe", "embedded", "iot", "raspberry pi", "arduino",
        
        # Storage
        "hard drive", "hdd", "ssd", "nvme", "storage", "disk", "raid",
        "backup", "external drive", "usb drive", "flash drive", "sd card",
        
        # Processing/Memory
        "cpu", "processor", "intel", "amd", "arm", "gpu", "graphics card",
        "nvidia", "amd radeon", "integrated graphics", "ram", "memory",
        "ddr4", "ddr5", "motherboard", "chipset", "bios", "uefi", "firmware",
        
        # GPU specific
        "rtx", "gtx", "radeon", "geforce", "graphics", "video card", "vram",
        "thermal throttling", "boost clock", "base clock", "overclocking",
        
        # Networking hardware
        "router", "switch", "modem", "ethernet", "wifi", "wireless",
        "network card", "nic", "bluetooth", "antenna", "access point",
        
        # Power/Cooling/Temperature
        "power supply", "psu", "battery", "charging", "charger", "adapter",
        "cooling", "fan", "heatsink", "thermal", "temperature", "overheating",
        "thermal throttling", "thermal paste", "°c", "celsius", "degrees",
        
        # Input/Output
        "keyboard", "mouse", "trackpad", "touchpad", "monitor", "display",
        "screen", "lcd", "led", "oled", "4k", "1080p", "refresh rate",
        "speaker", "headphones", "microphone", "webcam", "camera",
        
        # Connectivity/Ports
        "usb", "usb-c", "thunderbolt", "hdmi", "displayport", "vga", "dvi",
        "audio jack", "ethernet port", "power port", "charging port",
        
        # Peripherals
        "printer", "scanner", "external", "peripheral", "dock", "hub",
        "cable", "connector", "adapter", "dongle"
    ]
    
    # Use word boundary regex for better matching
    def count_word_matches(keywords, text):
        matches = []
        for keyword in keywords:
            # Use word boundaries to avoid partial matches like "go" in "golang"
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text):
                matches.append(keyword)
        return matches
    
    # Count matches for detailed classification
    hardware_matches = count_word_matches(hardware_keywords, text)
    software_matches = count_word_matches(software_keywords, text)
    
    # Detailed logging for classification decision
    if hardware_matches:
        print(f"  🖥️  Hardware classification - matches: {hardware_matches[:3]}...")
        return "Hardware"
    elif software_matches:
        print(f"  💻 Software classification - matches: {software_matches[:3]}...")
        return "Software"
    else:
        print(f"  ❓ Other classification - no clear matches")
        return "Other"


def _init_reddit() -> Optional[praw.Reddit]:
    """Initialize Reddit API client with proper authentication"""
    try:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT")
        
        if not all([client_id, client_secret, user_agent]):
            print("❌ Missing Reddit credentials in environment variables")
            return None
        
        print(f"🔑 Attempting Reddit connection with client_id: {client_id[:8]}...")
        
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            ratelimit_seconds=600,  # 10 minute rate limit for safety
            timeout=32,  # 32 second timeout
        )
        
        # Test basic access to a public subreddit
        try:
            test_sub = reddit.subreddit("test")
            test_posts = list(test_sub.hot(limit=1))
            print("✅ Reddit API connection verified successfully")
            return reddit
        except RedditAPIException as e:
            print(f"❌ Reddit API error: {e}")
            return None
        except Exception as e:
            print(f"❌ Reddit connection failed: {e}")
            return None
        
    except Exception as e:
        print(f"❌ Failed to initialize Reddit client: {e}")
        return None


def fetch_real_reddit_data(
    db: Session,
    subreddits: List[str] = None,
    max_per_subreddit: int = 50,
    time_filter: str = "day"
) -> Dict[str, int]:
    """
    Fetch real data from Reddit subreddits with NLP classification
    
    Args:
        db: Database session
        subreddits: List of subreddit names (without r/)
        max_per_subreddit: Maximum posts to fetch per subreddit
        time_filter: Time filter for posts ("hour", "day", "week", "month", "year", "all")
    
    Returns:
        Dictionary with counts of inserted, skipped, and errors
    """
    
    if subreddits is None:
        # PROBLEM-SOLVING FOCUSED subreddits - only contain actual issues to solve
        subreddits = [
            # Technical Support & Troubleshooting
            "techsupport", "24hoursupport", "computer_help", "pchelp",
            "ITCareerQuestions", "sysadmin", "linuxquestions", "linuxsupport",
            
            # Hardware Problems
            "buildapc", "pcgamingtechsupport", "nvidia", "AMDHelp", 
            "hardware", "overclocking", "monitors", "peripherals",
            
            # Software Issues  
            "windows10", "windows11", "MacOSBug", "androidapps", "iosbeta",
            "webdev", "learnprogramming", "reacthelp", "node", "javascript",
            
            # Network & Infrastructure
            "homenetworking", "wifi", "networking", "HomeServer", 
            "selfhosted", "docker", "kubernetes", "devops",
            
            # Database & Backend Issues
            "PostgreSQL", "mysql", "mongodb", "redis", "database"
        ]
    
    reddit = _init_reddit()
    if not reddit:
        print("❌ Cannot fetch Reddit data - API not available")
        return {"inserted": 0, "skipped": 0, "errors": 1}
    
    counts = {"inserted": 0, "skipped": 0, "errors": 0}
    
    print(f"🚀 Fetching real Reddit data from {len(subreddits)} subreddits...")
    print(f"⚙️  Max per subreddit: {max_per_subreddit}, Time filter: {time_filter}")
    print("=" * 80)
    
    for subreddit_name in subreddits:
        print(f"\n📡 Fetching from r/{subreddit_name}...")
        
        try:
            subreddit = reddit.subreddit(subreddit_name)
            
            # Fetch top posts from the specified time period
            submissions = list(subreddit.top(time_filter=time_filter, limit=max_per_subreddit))
            
            print(f"   Found {len(submissions)} posts")
            
            for i, submission in enumerate(submissions, 1):
                try:
                    # Skip if already exists (check by Reddit ID)
                    existing = (
                        db.query(FetchedProblem.id)
                        .filter(FetchedProblem.reddit_id == submission.id)
                        .first()
                    )
                    
                    if existing:
                        counts["skipped"] += 1
                        continue
                    
                    # Get post content
                    title = submission.title.strip()
                    body = submission.selftext.strip() if hasattr(submission, 'selftext') else ""
                    
                    # Skip if title is too short or generic
                    if len(title) < 10:
                        counts["skipped"] += 1
                        continue
                    
                    # 🔍 CRITICAL: Check if this is actually a problem to solve
                    if not _is_actual_problem(title, body):
                        print(f"   ⏭️  Skipped - Not a problem: {title[:50]}...")
                        counts["skipped"] += 1
                        continue
                    
                    print(f"   📝 Problem detected: {title[:60]}...")
                    
                    # Classify using enhanced NLP
                    category = _classify_keyword_enhanced(title, body)
                    
                    # Create database entry
                    problem = FetchedProblem(
                        title=title,
                        description=body,
                        subreddit=subreddit_name,
                        category=category,
                        url=f"https://reddit.com{submission.permalink}",
                        reddit_id=submission.id,
                        created_utc=int(submission.created_utc),
                    )
                    
                    db.add(problem)
                    db.commit()
                    counts["inserted"] += 1
                    print(f"   ✅ Classified as: {category}")
                    
                    # Small delay to respect rate limits
                    time.sleep(0.1)
                    
                except Exception as e:
                    db.rollback()
                    counts["errors"] += 1
                    print(f"   ❌ Error processing post {i}: {e}")
                    continue
                    
        except Exception as e:
            counts["errors"] += 1
            print(f"❌ Error accessing r/{subreddit_name}: {e}")
            continue
    
    print("=" * 80)
    print(f"🎯 Real Reddit fetch complete: {counts}")
    return counts


def comprehensive_real_reddit_fetch(
    db: Session, 
    max_per_subreddit: int = 15,
    time_filter: str = "day"
) -> Dict[str, Dict[str, int]]:
    """Comprehensive real Reddit data fetch with PROBLEM-FOCUSED filtering"""
    
    print(f"🚀 COMPREHENSIVE PROBLEM-FOCUSED REDDIT FETCH at {datetime.now()}")
    print("Fetching ONLY actual problems from Reddit with enhanced NLP classification")
    print("=" * 80)
    
    # Fetch recent posts with problem filtering
    recent_results = fetch_real_reddit_data(
        db, 
        max_per_subreddit=max_per_subreddit,
        time_filter=time_filter
    )
    
    print(f"🎯 PROBLEM-FOCUSED RESULTS: {recent_results}")
    
    total_inserted = recent_results.get("inserted", 0)
    total_errors = recent_results.get("errors", 0)
    
    print(f"\n🎯 TOTAL PROBLEMS COLLECTED: {total_inserted}")
    print(f"⚠️  TOTAL ERRORS: {total_errors}")
    print("=" * 80)
    
    return {
        "recent": recent_results,
        "summary": {
            "total_inserted": total_inserted,
            "total_errors": total_errors,
            "note": "Problem-focused Reddit data fetched with enhanced filtering"
        }
    }


if __name__ == "__main__":
    with SessionLocal() as db:
        results = comprehensive_real_reddit_fetch(db)
        print("\n🏁 Final Results:")
        import json
        print(json.dumps(results, indent=2))
