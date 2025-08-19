"""
Centralized Subreddit Configuration for Painpoint.AI

This module contains all subreddit lists used across different Reddit fetching services.
Update this file to modify subreddit targeting across the entire application.
"""

# MAIN SUBREDDIT LIST - Comprehensive problem-solving focused communities
PAINPOINT_SUBREDDITS = [
    # Help & Assistance
    "assistance",
    "AskReddit", 
    "TrueOffMyChest",
    
    # Personal & Financial Issues  
    "personalfinance",
    
    # Technical Support & Development
    "techsupport",
    "softwaregore",
    "webdev", 
    "learnprogramming",
    "sysadmin",
    
    # Design & User Experience
    "UXDesign",
    "userexperience",
    
    # Productivity & Tools
    "productivity",
    "Notion",
    "Trello", 
    "ObsidianMD",
    
    # Professional & Career
    "Workplace",
    "freelance",
    "Teachers",
    "Students",
    
    # Regional Focus (India)
    "india",
    "Chennai",
    "bangalore", 
    "college",
    "indianstartups",
    
    # Business & Entrepreneurship  
    "startups",
    "Entrepreneur",
    "SaaS",
    "SideProject",
    
    # Problem Solving & Innovation
    "ProblemsNeedSolution",
    "Futurology"
]

# TECH-FOCUSED SUBSET - For purely technical problem searches
TECH_SUBREDDITS = [
    "techsupport",
    "softwaregore", 
    "webdev",
    "learnprogramming",
    "sysadmin",
    "UXDesign",
    "userexperience",
    "productivity",
    "Notion",
    "Trello",
    "ObsidianMD"
]

# BUSINESS & STARTUP SUBSET - For entrepreneurial and business problems
BUSINESS_SUBREDDITS = [
    "startups",
    "Entrepreneur", 
    "SaaS",
    "SideProject",
    "freelance",
    "Workplace",
    "indianstartups"
]

# REGIONAL SUBSET - For India-specific problems
INDIA_SUBREDDITS = [
    "india",
    "Chennai", 
    "bangalore",
    "college",
    "indianstartups"
]

# GENERAL HELP SUBSET - For broad assistance and personal problems
HELP_SUBREDDITS = [
    "assistance",
    "AskReddit",
    "TrueOffMyChest", 
    "personalfinance",
    "Teachers",
    "Students"
]

def get_subreddits_by_category(category: str = "all") -> list:
    """
    Get subreddit list by category
    
    Args:
        category: "all", "tech", "business", "india", "help"
        
    Returns:
        List of subreddit names (without r/ prefix)
    """
    category_map = {
        "all": PAINPOINT_SUBREDDITS,
        "tech": TECH_SUBREDDITS,
        "business": BUSINESS_SUBREDDITS, 
        "india": INDIA_SUBREDDITS,
        "help": HELP_SUBREDDITS
    }
    
    return category_map.get(category, PAINPOINT_SUBREDDITS)

def get_all_subreddits() -> list:
    """Get the complete list of all subreddits"""
    return PAINPOINT_SUBREDDITS.copy()

def validate_subreddit_name(name: str) -> bool:
    """
    Validate if a subreddit name is in our target list
    
    Args:
        name: Subreddit name (with or without r/ prefix)
        
    Returns:
        True if valid, False otherwise
    """
    clean_name = name.replace("r/", "").lower()
    return clean_name in [s.lower() for s in PAINPOINT_SUBREDDITS]

def format_subreddit_url(name: str) -> str:
    """
    Format subreddit name into proper Reddit URL
    
    Args:
        name: Subreddit name
        
    Returns:
        Formatted URL
    """
    clean_name = name.replace("r/", "")
    return f"https://reddit.com/r/{clean_name}"

# Search queries optimized for the new subreddit list
SEARCH_QUERIES = [
    # Technical Problems
    "software bug issue",
    "app not working fix",
    "website problem help", 
    "code error debugging",
    "system crash troubleshoot",
    
    # UX/Design Problems
    "bad user interface design",
    "confusing app navigation", 
    "poor user experience",
    "design improvement needed",
    
    # Productivity Issues
    "workflow problem slow",
    "tool not efficient",
    "process improvement needed",
    "automation requirement",
    
    # Business Problems
    "startup challenge problem",
    "business process issue",
    "customer complaint feedback",
    "service improvement needed",
    
    # Regional Problems (India)
    "indian market problem",
    "local business issue",
    "regional service gap",
    "india specific challenge",
    
    # General Help & Assistance
    "need help with problem",
    "looking for solution",
    "how to fix issue",
    "problem solving advice"
]

if __name__ == "__main__":
    print("🎯 PAINPOINT.AI SUBREDDIT CONFIGURATION")
    print("=" * 50)
    print(f"Total subreddits: {len(PAINPOINT_SUBREDDITS)}")
    print(f"Tech-focused: {len(TECH_SUBREDDITS)}")
    print(f"Business-focused: {len(BUSINESS_SUBREDDITS)}")
    print(f"India-focused: {len(INDIA_SUBREDDITS)}")
    print(f"Help-focused: {len(HELP_SUBREDDITS)}")
    
    print("\n📋 All Target Subreddits:")
    for i, subreddit in enumerate(PAINPOINT_SUBREDDITS, 1):
        print(f"{i:2d}. r/{subreddit}")
    
    print(f"\n🔍 Search Queries: {len(SEARCH_QUERIES)} defined")
