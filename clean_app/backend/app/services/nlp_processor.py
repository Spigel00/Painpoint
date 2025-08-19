# nlp_processor.py
import re
from transformers import pipeline

# Load the model once (at startup, not inside the loop)
generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"  # or flan-t5-large if GPU is ok
)

class NLPProcessor:
    def __init__(self):
        self.model = None
        self.fallback_model = None

        try:
            print("Loading Flan-T5...")
            self.model = pipeline(
                "text2text-generation",
                model="google/flan-t5-base"
            )
        except Exception as e:
            print("Flan-T5 failed, trying BART:", e)
            try:
                self.fallback_model = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn"
                )
            except Exception as e2:
                print("BART also failed:", e2)
                print("⚠ Falling back to rule-based summarizer only")

    def clean_text(self, text: str) -> str:
        """Remove Reddit/meta noise from text"""
        text = re.sub(r"r/[A-Za-z0-9_]+", "", text)      # remove subreddit refs
        text = re.sub(r"•|👍|📝", "", text)              # remove bullets/emojis
        text = re.sub(r"http\S+", "", text)               # remove URLs
        text = re.sub(r"\s+", " ", text).strip()          # normalize spaces
        return text

    def flan_prompt(self, text: str) -> str:
        """Prompt for Flan-T5 to output dev-style problem statement"""
        return (
            f"Convert the following user text into a concise, developer-style "
            f"problem statement (1-2 lines, technical, no fluff):\n\n{text}"
        )

    def to_problem_statement(self, text: str) -> str:
        """Main entry: clean → summarize → return dev problem statement"""
        clean = self.clean_text(text)

        # --- Flan-T5 first with improved prompt ---
        if self.model:
            try:
                prompt = (
                    "You are a product manager assistant. "
                    "Convert the following user complaint into a concise, developer-ready problem statement. "
                    "Always rewrite it (never copy). Use only 1–2 lines. "
                    "Remove slang, emotions, and filler. Keep technical details (hardware, OS, software). "
                    "Focus on the technical problem, not the story.\n\n"
                    f"Complaint:\n{clean}\n\n"
                    "Problem Statement:"
                )
                result = self.model(prompt, max_new_tokens=60, num_return_sequences=1)
                output = result[0]["generated_text"].strip()

                # Post-clean: remove redundant words like "Problem statement:"
                output = re.sub(r"^Problem statement:\s*", "", output, flags=re.IGNORECASE)
                output = re.sub(r"Complaint:\s*", "", output, flags=re.IGNORECASE)
                
                # Check if result is good
                if len(output) > 10 and len(output) < len(clean) * 0.9:
                    return output
            except Exception as e:
                print("Flan-T5 error:", e)

        # --- BART fallback ---
        if self.fallback_model:
            try:
                result = self.fallback_model(clean, max_length=40, min_length=10, do_sample=False)
                return result[0]["summary_text"].strip()
            except Exception as e:
                print("BART error:", e)

        # --- Enhanced rule-based fallback ---
        return _rule_based_transform(clean)


def process_post(original_text: str) -> str:
    """
    Convert Reddit text into a concise developer-style problem statement.
    Uses improved prompt for better AI-generated results with rule-based fallback.
    """
    
    # Clean the text more aggressively
    clean_text = re.sub(r'[!]{2,}', '.', original_text)  # Replace multiple exclamations
    clean_text = re.sub(r'WHY|DAMN|SO|HELP|PLEASE|STUPID|FRUSTRATED|DRIVING ME CRAZY', '', clean_text, flags=re.IGNORECASE)  # Remove emotional words
    clean_text = re.sub(r"I'VE BEEN|I'M ABOUT TO|REALLY NEED|PLEASE HELP", '', clean_text, flags=re.IGNORECASE)  # Remove emotional phrases
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Normalize spaces
    
    # Try AI with the improved prompt first
    try:
        prompt = (
            "Convert this complaint into a 1-2 line technical problem statement. "
            "Remove emotions (HELP, frustrated, stupid, etc.). "
            "Keep only: technology names, error details, platform info. "
            "Be concise and professional.\n\n"
            f"Input: {clean_text}\n\n"
            "Output:"
        )
        
        result = generator(prompt, max_new_tokens=40, do_sample=False, temperature=0.1)[0]["generated_text"]
        
        # Extract just the problem statement part
        if "Output:" in result:
            statement = result.split("Output:")[-1].strip()
        elif "Problem Statement:" in result:
            statement = result.split("Problem Statement:")[-1].strip()
        else:
            statement = result.strip()
        
        # Clean up any remaining prompt artifacts
        statement = statement.replace("Complaint:", "").replace("Input:", "").strip()
        statement = re.sub(r'^(convert|problem|statement|output):\s*', '', statement, flags=re.IGNORECASE)
        
        # More strict validation for better compression
        if (len(statement) > 15 and 
            len(statement) < min(120, len(clean_text) * 0.6) and  # Much stricter length limit
            not statement.lower().startswith(("complaint", "convert", "you are", "input")) and
            not any(word in statement.lower() for word in ["help", "please", "frustrated", "stupid"])):  # Remove emotional words
            return statement
    
    except Exception as e:
        print(f"AI processing failed: {e}")
    
    # Fall back to rule-based approach if AI fails or produces poor results
    return _rule_based_transform(clean_text)


def _rule_based_transform(text: str) -> str:
    """Enhanced rule-based transformation with specific technical context"""
    
    # Enhanced technical context extraction
    context = _extract_enhanced_context(text)
    problem_type = _identify_problem_type(text)
    
    # Extract key components
    tech_stack = context['technologies'][:2] if context['technologies'] else []
    errors = context['errors'][:1] if context['errors'] else []
    hardware = context['hardware'][:1] if context['hardware'] else []
    platforms = context['platforms'][:1] if context['platforms'] else []
    
    # Extract specific technical field and key terms from text
    technical_field = _extract_technical_field(text)
    key_subject = _extract_key_subject(text)
    
    # Create statement based on problem type and available context
    if problem_type == 'error_bug' and errors:
        base = f"Resolve {errors[0]}"
        if tech_stack:
            base += f" in {tech_stack[0]}"
        elif technical_field:
            base += f" in {technical_field}"
        if platforms:
            base += f" on {platforms[0]}"
    elif problem_type == 'performance' and hardware:
        base = f"Optimize performance"
        if key_subject:
            base += f" for {key_subject}"
        if hardware:
            base += f" on {hardware[0]}"
        elif tech_stack:
            base += f" in {tech_stack[0]}"
    elif problem_type == 'installation_setup' and tech_stack:
        base = f"Set up and configure {tech_stack[0]}"
        if key_subject:
            base += f" for {key_subject}"
        if platforms:
            base += f" on {platforms[0]}"
    elif problem_type == 'how_to' and tech_stack:
        base = f"Implement {tech_stack[0]} solution"
        if key_subject:
            base += f" for {key_subject}"
    elif problem_type == 'technology_choice' and len(tech_stack) >= 2:
        base = f"Choose between {tech_stack[0]} and {tech_stack[1]}"
        if technical_field:
            base += f" for {technical_field}"
    else:
        # Generic fallback with enhanced context
        action = "Address"
        
        # Better action detection
        if any(word in text.lower() for word in ['resolve', 'fix', 'solve', 'debug']):
            action = "Resolve"
        elif any(word in text.lower() for word in ['develop', 'build', 'create', 'implement']):
            action = "Develop"
        elif any(word in text.lower() for word in ['optimize', 'improve', 'enhance', 'speed']):
            action = "Optimize"
        elif any(word in text.lower() for word in ['launch', 'deploy', 'release', 'publish']):
            action = "Deploy"
        elif any(word in text.lower() for word in ['feedback', 'review', 'opinion']):
            action = "Review"
        
        # Determine the main subject
        if tech_stack:
            subject = tech_stack[0]
        else:
            key_concepts = _extract_key_concepts(text)
            subject = key_concepts[0] if key_concepts else 'technical'
        
        # Build the base statement
        if action == "Review" and key_subject:
            base = f"{action} {subject} issue for {key_subject}"
            if technical_field:
                base += f" in the field of {technical_field}"
        elif tech_stack and technical_field:
            base = f"{action} {subject} issue in the field of {technical_field}"
        elif key_subject and technical_field:
            base = f"{action} {subject} issue for {key_subject} in the field of {technical_field}"
        elif technical_field:
            base = f"{action} {subject} issue in the field of {technical_field}"
        elif key_subject:
            base = f"{action} {subject} issue for {key_subject}"
        else:
            base = f"{action} {subject} issue"
        
        # Add platform context if available
        if platforms and not technical_field:
            base += f" on {platforms[0]}"
    
    # Ensure proper sentence structure
    if not base.endswith('.'):
        base += '.'
    
    return base


def _extract_technical_field(text: str) -> str:
    """Extract the specific technical field or domain from text"""
    text_lower = text.lower()
    
    # Field mapping with more specific keywords
    fields = {
        'web development': ['webdev', 'frontend', 'backend', 'fullstack', 'ui', 'ux', 'website', 'html', 'css', 'responsive'],
        'mobile development': ['mobile', 'android', 'ios', 'app development', 'mobile app', 'flutter', 'react native'],
        'devops': ['devops', 'deployment', 'ci/cd', 'infrastructure', 'cloud', 'container', 'docker', 'kubernetes'],
        'database': ['database', 'sql', 'nosql', 'data storage', 'db', 'postgresql', 'mongodb', 'mysql'],
        'api development': ['api', 'rest api', 'graphql', 'endpoint', 'microservice', 'web service'],
        'performance optimization': ['performance', 'optimization', 'slow', 'speed', 'memory', 'cpu'],
        'networking': ['network', 'networking', 'connectivity', 'internet', 'protocol', 'wifi'],
        'security': ['security', 'authentication', 'authorization', 'encryption', 'cybersecurity'],
        'system administration': ['sysadmin', 'server', 'linux admin', 'system admin', 'ubuntu', 'centos']
    }
    
    # Score each field based on keyword matches
    field_scores = {}
    for field, keywords in fields.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            field_scores[field] = score
    
    # Return the field with highest score
    if field_scores:
        return max(field_scores, key=field_scores.get)
    
    return ""


def _extract_key_subject(text: str) -> str:
    """Extract the key subject/project name from text"""
    import re
    
    # Look for specific patterns first
    patterns = [
        r'(\w+\.page)',  # domain names like inspo.page
        r'(\w+\.com)',   # .com domains
        r'(\w+\.io)',    # .io domains
        r'my (\w+) (?:app|project|website|tool)',  # "my X app/project"
        r'(\w+) (?:app|application)',  # "X app"
        r'(\w+) (?:project|tool|library)',  # "X project"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            subject = matches[0].lower()
            # Filter out common words
            if subject not in ['the', 'my', 'this', 'that', 'web', 'mobile']:
                return subject
    
    # Look for capitalized words that might be project names
    words = text.split()
    for word in words[:10]:  # Check first 10 words
        clean_word = re.sub(r'[^\w]', '', word)
        if (clean_word and len(clean_word) > 2 and 
            clean_word[0].isupper() and 
            clean_word.lower() not in ['the', 'my', 'this', 'that', 'help', 'need', 'having', 'getting']):
            return clean_word.lower()
    
    return ""


def _extract_enhanced_context(text: str) -> dict:
    """Extract technical context from Reddit text"""
    context = {
        'technologies': [],
        'errors': [],
        'versions': [],
        'hardware': [],
        'platforms': []
    }
    
    text_lower = text.lower()
    
    # Technology detection patterns
    tech_patterns = {
        'web_dev': ['react', 'angular', 'vue', 'javascript', 'css', 'html', 'nodejs', 'express', 'webpack'],
        'backend': ['python', 'java', 'django', 'flask', 'spring', 'api', 'microservices'],
        'database': ['mysql', 'postgresql', 'mongodb', 'sqlite', 'redis', 'database'],
        'devops': ['docker', 'kubernetes', 'aws', 'azure', 'jenkins', 'heroku', 'deployment'],
        'mobile': ['android', 'ios', 'react native', 'flutter', 'swift', 'kotlin'],
        'system': ['linux', 'ubuntu', 'centos', 'server', 'networking', 'wifi', 'windows']
    }
    
    for category, techs in tech_patterns.items():
        for tech in techs:
            if tech in text_lower:
                context['technologies'].append(tech)
    
    # Error extraction
    error_patterns = [
        r'error\s*:\s*([^.!?\n]+)',
        r'exception\s*:\s*([^.!?\n]+)',
        r'failed\s+to\s+([^.!?\n]+)',
        r'cannot\s+([^.!?\n]+)',
        r"can't\s+([^.!?\n]+)"
    ]
    for pattern in error_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        context['errors'].extend(matches[:2])
    
    # Hardware extraction
    hardware_patterns = [
        r'(\d+)\s*gb\s*ram',
        r'intel\s+core\s+(i[3-9]-?\d+\w*)',
        r'(gtx|rtx)\s*(\d+)',
        r'(\d+)\s*core\s*cpu'
    ]
    for pattern in hardware_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            context['hardware'].extend([' '.join(match) if isinstance(match, tuple) else match for match in matches])
    
    # Platform extraction
    platform_patterns = [
        r'(windows|mac|linux|ubuntu|centos|fedora)\s*(\d+(?:\.\d+)*)?',
        r'(android|ios)\s*(\d+(?:\.\d+)*)?'
    ]
    for pattern in platform_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            context['platforms'].extend([' '.join(match).strip() if isinstance(match, tuple) else match for match in matches])
    
    return context


def _identify_problem_type(text: str) -> str:
    """Identify the type of problem from Reddit text"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['install', 'setup', 'configure', 'deployment']):
        return 'installation_setup'
    elif any(word in text_lower for word in ['slow', 'performance', 'lag', 'freeze', 'timeout']):
        return 'performance'
    elif any(word in text_lower for word in ['error', 'crash', 'fail', 'bug', 'exception']):
        return 'error_bug'
    elif any(word in text_lower for word in ['how to', 'how do', 'implement', 'add feature']):
        return 'how_to'
    elif any(word in text_lower for word in ['choose', 'better', 'vs', 'compare', 'recommend']):
        return 'technology_choice'
    else:
        return 'general'


def _extract_key_concepts(text: str) -> list:
    """Extract key technical concepts from text"""
    tech_keywords = [
        'server', 'database', 'api', 'application', 'service', 'container',
        'network', 'security', 'authentication', 'deployment', 'backup',
        'monitoring', 'logging', 'testing', 'integration', 'migration'
    ]
    
    found_concepts = []
    text_lower = text.lower()
    
    for keyword in tech_keywords:
        if keyword in text_lower:
            found_concepts.append(keyword)
    
    return found_concepts[:3]


def process_reddit_posts_example():
    """
    Example function showing how to process Reddit posts and save to DB
    """
    # This is an example - would need actual reddit instance and db connection
    # for post in reddit.subreddit("some_sub").hot(limit=10):
    #     original_text = post.title + "\n" + post.selftext
    #     problem_statement = process_post(original_text)
    # 
    #     # Save to DB instead of original text
    #     db.save({
    #         "reddit_id": post.id,
    #         "problem_statement": problem_statement,
    #         "url": post.url
    #     })
    pass


if __name__ == "__main__":
    processor = NLPProcessor()

    sample_text = """
    I need someone to give me a hand to get my docker On ubuntu 24.04 
    released by cloudflare. I've been coming up with this for days and I can't get it. 
    I have a public domain.
    """

    print("🧪 Testing NLPProcessor class:")
    problem_statement = processor.to_problem_statement(sample_text)
    print("📝 Problem Statement (Class Method):", problem_statement)

    print("\n🧪 Testing process_post function:")
    reddit_style_text = """
    I'm a complete beginner, and I wanted to know if I should use my laptop as some sort of home server, 
    not for work or anything, but for multiplayer games. I can't afford any new tech, so I wanted to know 
    if I can work with what I have. The laptop has an Intel Core i5-5200U, which clocks around 2.20GHz, 
    and has around 6gb of RAM. If I can turn it into a home server, what OS would be recommended
    """
    
    enhanced_statement = process_post(reddit_style_text)
    print("📝 Original:", reddit_style_text.strip()[:100] + "...")
    print("⚡ Enhanced Problem Statement:", enhanced_statement)
    
    print("\n🧪 Testing more Reddit posts:")
    test_posts = [
        "WHY is my laptop SO DAMN SLOW when I try to run multiple programs??? I've got 8GB RAM and an i5 processor but it takes forever to load anything. Chrome eats up all my memory and VS Code becomes unresponsive.",
        "My Docker container keeps crashing on startup. Error says port 8080 already in use but netstat shows nothing. Running Ubuntu 22.04. This is driving me crazy!!!",
        "Need help choosing between PostgreSQL and MongoDB for my new project. It's a social media app expecting around 10k users. Not sure which one scales better."
    ]
    
    for i, post in enumerate(test_posts, 1):
        result = process_post(post)
        print(f"\n{i}. Original: {post[:80]}...")
        print(f"   Problem Statement: {result}")
