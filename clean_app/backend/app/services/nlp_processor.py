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
        """Main entry: clean → analyze → return specific technical problem statement"""
        clean = self.clean_text(text)

        # --- Enhanced Flan-T5 with detailed technical analysis ---
        if self.model:
            try:
                # Create a much more detailed prompt for specific analysis
                prompt = (
                    "You are a senior technical engineer. Analyze this problem and create a detailed technical problem statement. "
                    "Be VERY specific about technologies, error types, and technical details. "
                    "Include specific components, error messages, version numbers, and technical context when mentioned. "
                    "Do NOT use vague terms like 'development needed' or 'general issue'. "
                    "Output format: 'Technical Issue: [specific problem] in [specific technology/component] causing [specific symptoms/error]'\n\n"
                    f"User Report:\n{clean}\n\n"
                    "Detailed Technical Analysis:"
                )
                
                result = self.model(prompt, max_new_tokens=120, num_return_sequences=1, do_sample=True, temperature=0.7)
                output = result[0]["generated_text"].strip()

                # Post-process: Clean up the output and ensure it's technical
                output = re.sub(r"^(Technical Analysis|Analysis|Problem|Issue):\s*", "", output, flags=re.IGNORECASE)
                output = re.sub(r"^Technical Issue:\s*", "", output, flags=re.IGNORECASE)
                
                # If we got a good technical response, use it
                if len(output) > 20 and any(tech_word in output.lower() for tech_word in 
                    ['error', 'crash', 'timeout', 'failed', 'bug', 'issue', 'problem', 'configuration', 'build', 'deploy']):
                    return output
                    
            except Exception as e:
                print("Enhanced Flan-T5 error:", e)

        # --- BART fallback with better parameters ---
        if self.fallback_model:
            try:
                result = self.fallback_model(clean, max_length=60, min_length=15, do_sample=False)
                return result[0]["summary_text"].strip()
            except Exception as e:
                print("BART error:", e)

        # --- Much more sophisticated rule-based fallback ---
        return self._enhanced_rule_based_transform(clean)

    def _enhanced_rule_based_transform(self, text: str) -> str:
        """Enhanced rule-based transformation with technical specificity"""
        
        # Extract technical keywords and context
        tech_patterns = {
            'web_frameworks': r'\b(react|angular|vue|django|flask|express|laravel|rails)\b',
            'databases': r'\b(mysql|postgresql|mongodb|redis|sqlite|oracle|sql server)\b',
            'languages': r'\b(python|javascript|java|c\+\+|c#|php|ruby|go|rust|typescript)\b',
            'platforms': r'\b(aws|azure|gcp|docker|kubernetes|heroku|netlify|vercel)\b',
            'tools': r'\b(git|npm|pip|webpack|gradle|maven|composer|yarn)\b',
            'errors': r'\b(error|exception|crash|timeout|failed|broken|bug|issue)\b',
            'actions': r'\b(install|deploy|build|compile|run|start|stop|configure|setup)\b'
        }
        
        found_tech = {}
        for category, pattern in tech_patterns.items():
            matches = re.findall(pattern, text.lower())
            if matches:
                found_tech[category] = matches
        
        # Extract specific error messages or symptoms
        error_indicators = re.findall(r'"([^"]*error[^"]*)"', text, re.IGNORECASE)
        if not error_indicators:
            error_indicators = re.findall(r'(fails?|crashes?|timeouts?|broken|not working)', text.lower())
        
        # Build specific technical statement
        if found_tech:
            statement_parts = []
            
            # Add technology context
            if 'languages' in found_tech:
                statement_parts.append(f"{found_tech['languages'][0].title()} application")
            elif 'web_frameworks' in found_tech:
                statement_parts.append(f"{found_tech['web_frameworks'][0].title()} application")
            
            # Add specific problem
            if 'errors' in found_tech and error_indicators:
                statement_parts.append(f"experiencing {error_indicators[0]}")
            elif 'actions' in found_tech:
                statement_parts.append(f"failing during {found_tech['actions'][0]} process")
            
            # Add technical context
            if 'databases' in found_tech:
                statement_parts.append(f"with {found_tech['databases'][0].upper()} database")
            elif 'platforms' in found_tech:
                statement_parts.append(f"on {found_tech['platforms'][0].upper()} platform")
            elif 'tools' in found_tech:
                statement_parts.append(f"using {found_tech['tools'][0]} tool")
            
            if statement_parts:
                return " ".join(statement_parts) + " requiring technical investigation"
        
        # Fallback: Try to extract the core technical issue
        # Look for specific patterns
        if 'install' in text.lower():
            return "Installation/dependency configuration issue requiring environment setup fix"
        elif any(word in text.lower() for word in ['build', 'compile']):
            return "Build/compilation process failure requiring code or configuration fix"
        elif any(word in text.lower() for word in ['deploy', 'production']):
            return "Deployment/production environment issue requiring infrastructure fix"
        elif any(word in text.lower() for word in ['connection', 'network', 'timeout']):
            return "Network/connection timeout issue requiring connectivity troubleshooting"
        elif any(word in text.lower() for word in ['performance', 'slow', 'speed']):
            return "Performance optimization issue requiring code/infrastructure tuning"
        elif any(word in text.lower() for word in ['auth', 'login', 'permission']):
            return "Authentication/authorization issue requiring security configuration fix"
        else:
            # Extract first technical sentence if possible
            sentences = text.split('.')
            for sentence in sentences:
                if len(sentence.strip()) > 10 and any(tech in sentence.lower() for tech in 
                    ['code', 'app', 'system', 'server', 'data', 'file', 'config']):
                    return sentence.strip()[:100] + "..."
        
        # Ultimate fallback - try to identify problem type
        return "Technical issue requiring analysis and debugging to identify root cause"


def generate_problem_statement(text: str) -> str:
    """
    Convert raw Reddit or user-submitted text into a clear "problem statement".
    
    Goal: Convert raw Reddit or user-submitted text into a clear "problem statement".
    
    Instructions:
    1. Ignore solution details, tools, or fixes mentioned in the input.
    2. Identify the underlying user struggle or pain point.
    3. Generalize it into a single sentence that starts with "Users ..." or "People ..."
    4. Optionally add a short consequence clause explaining why it matters.
    
    Example:
    Input: "For anyone struggling with TikTok watermarks, I use this free online tool that removes it fast."
    Output: "Users saving TikTok videos end up with watermarks that disrupt content reuse and sharing."
    """
    
    # Clean the text aggressively - remove solutions, tools, and emotional language
    clean_text = _clean_for_problem_extraction(text)
    
    # Try AI-powered problem statement generation first
    if hasattr(generator, '__call__'):
        try:
            problem_statement = _ai_generate_problem_statement(clean_text)
            if _validate_problem_statement(problem_statement):
                return problem_statement
        except Exception as e:
            print(f"AI problem statement generation failed: {e}")
    
    # Fallback to rule-based problem statement generation
    return _rule_based_problem_statement(clean_text)


def _clean_for_problem_extraction(text: str) -> str:
    """Clean text specifically for problem statement extraction"""
    
    # Remove solution indicators and tool mentions
    solution_patterns = [
        r'I use this\s+[^.!?]*',
        r'try this\s+[^.!?]*',
        r'solution[^.!?]*',
        r'fix[^.!?]*',
        r'here\'s how[^.!?]*',
        r'just use[^.!?]*',
        r'simply[^.!?]*',
        r'tool that[^.!?]*',
        r'website that[^.!?]*',
        r'app that[^.!?]*'
    ]
    
    for pattern in solution_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove emotional expressions and help requests
    emotional_patterns = [
        r'WHY|DAMN|SO|HELP|PLEASE|STUPID|FRUSTRATED|DRIVING ME CRAZY',
        r"I'VE BEEN|I'M ABOUT TO|REALLY NEED|PLEASE HELP",
        r'anyone else|does anyone|help me',
        r'[!]{2,}'
    ]
    
    for pattern in emotional_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def _ai_generate_problem_statement(clean_text: str) -> str:
    """Use AI to generate a user-focused problem statement"""
    
    prompt = (
        "Convert this text into a clear problem statement. Follow these rules:\n"
        "1. Start with 'Users' or 'People'\n"
        "2. Focus on the underlying struggle or pain point\n"
        "3. Ignore any solutions mentioned\n"
        "4. Keep it to one sentence\n"
        "5. Add consequences if relevant\n\n"
        "Examples:\n"
        "Input: 'My React app crashes when I deploy to production'\n"
        "Output: 'Users deploying React applications experience crashes that prevent successful production releases.'\n\n"
        "Input: 'Docker containers use too much memory on my server'\n"
        "Output: 'Users running Docker containers face excessive memory consumption that impacts server performance.'\n\n"
        f"Input: {clean_text}\n"
        "Output:"
    )
    
    result = generator(prompt, max_new_tokens=60, do_sample=True, temperature=0.3)[0]["generated_text"]
    
    # Extract the generated statement
    if "Output:" in result:
        statement = result.split("Output:")[-1].strip()
    else:
        # Find the last line that looks like a problem statement
        lines = result.split('\n')
        for line in reversed(lines):
            if line.strip() and (line.strip().startswith(('Users', 'People')) or 
                                line.strip().lower().startswith(('users', 'people'))):
                statement = line.strip()
                break
        else:
            statement = result.strip()
    
    # Clean up artifacts
    statement = re.sub(r'^(Output|Input|Convert):\s*', '', statement, flags=re.IGNORECASE)
    statement = statement.strip()
    
    return statement


def _rule_based_problem_statement(text: str) -> str:
    """Generate a rule-based problem statement"""
    
    # Extract key problem indicators
    problem_context = _extract_problem_context(text)
    
    # Determine the core struggle
    if problem_context['performance_issues']:
        return f"Users experience {problem_context['performance_issues'][0]} that impacts productivity and system usability."
    
    elif problem_context['errors']:
        tech = problem_context['technologies'][0] if problem_context['technologies'] else 'applications'
        return f"Users encounter {problem_context['errors'][0]} in {tech} that prevents successful task completion."
    
    elif problem_context['setup_issues']:
        tech = problem_context['technologies'][0] if problem_context['technologies'] else 'software'
        return f"Users struggle with {problem_context['setup_issues'][0]} when configuring {tech} environments."
    
    elif problem_context['compatibility_issues']:
        return f"Users face {problem_context['compatibility_issues'][0]} that disrupts workflow continuity."
    
    elif problem_context['learning_curve']:
        tech = problem_context['technologies'][0] if problem_context['technologies'] else 'new technology'
        return f"Users learning {tech} encounter steep learning curves that slow development progress."
    
    elif problem_context['technologies']:
        # Generic tech-related problem
        tech = problem_context['technologies'][0]
        action = _extract_struggling_action(text)
        return f"Users working with {tech} {action} that requires technical expertise to resolve."
    
    else:
        # Ultimate fallback - extract core struggle from text patterns
        if any(word in text.lower() for word in ['slow', 'performance', 'lag']):
            return "Users experience performance issues that impact productivity and system responsiveness."
        elif any(word in text.lower() for word in ['error', 'crash', 'fail']):
            return "Users encounter technical errors that prevent successful task completion."
        elif any(word in text.lower() for word in ['install', 'setup', 'configure']):
            return "Users struggle with software installation and configuration processes."
        elif any(word in text.lower() for word in ['learn', 'understand', 'beginner']):
            return "Users learning new technology face knowledge gaps that slow their progress."
        else:
            return "Users encounter technical challenges that require specialized knowledge to overcome."


def _extract_problem_context(text: str) -> dict:
    """Extract problem context for rule-based generation"""
    
    context = {
        'technologies': [],
        'errors': [],
        'performance_issues': [],
        'setup_issues': [],
        'compatibility_issues': [],
        'learning_curve': []
    }
    
    text_lower = text.lower()
    
    # Technology extraction
    tech_keywords = [
        'react', 'angular', 'vue', 'javascript', 'python', 'java', 'docker', 
        'kubernetes', 'aws', 'linux', 'windows', 'database', 'api', 'server'
    ]
    for tech in tech_keywords:
        if tech in text_lower:
            context['technologies'].append(tech)
    
    # Performance issues
    performance_patterns = [
        'slow performance', 'memory usage', 'cpu usage', 'lag issues', 
        'timeout problems', 'loading delays', 'response time issues'
    ]
    for pattern in performance_patterns:
        if any(word in text_lower for word in pattern.split()):
            context['performance_issues'].append(pattern)
            break
    
    # Error patterns
    error_patterns = [
        'build errors', 'runtime exceptions', 'deployment failures', 
        'connection timeouts', 'authentication errors', 'configuration issues'
    ]
    for pattern in error_patterns:
        if any(word in text_lower for word in pattern.split()):
            context['errors'].append(pattern)
            break
    
    # Setup issues
    setup_patterns = [
        'installation problems', 'environment setup', 'dependency conflicts',
        'configuration challenges', 'version compatibility'
    ]
    for pattern in setup_patterns:
        if any(word in text_lower for word in pattern.split()):
            context['setup_issues'].append(pattern)
            break
    
    # Compatibility issues
    compatibility_patterns = [
        'browser compatibility', 'version conflicts', 'platform differences',
        'integration problems', 'API changes'
    ]
    for pattern in compatibility_patterns:
        if any(word in text_lower for word in pattern.split()):
            context['compatibility_issues'].append(pattern)
            break
    
    # Learning curve indicators
    learning_patterns = [
        'steep learning curve', 'documentation gaps', 'complex syntax',
        'unclear tutorials', 'beginner challenges'
    ]
    for pattern in learning_patterns:
        if any(word in text_lower for word in pattern.split()):
            context['learning_curve'].append(pattern)
            break
    
    return context


def _extract_struggling_action(text: str) -> str:
    """Extract what users are struggling to do"""
    
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['deploy', 'deployment']):
        return "struggle with deployment processes"
    elif any(word in text_lower for word in ['debug', 'troubleshoot']):
        return "face debugging challenges"
    elif any(word in text_lower for word in ['optimize', 'performance']):
        return "encounter optimization difficulties"
    elif any(word in text_lower for word in ['integrate', 'connect']):
        return "have integration problems"
    elif any(word in text_lower for word in ['scale', 'scaling']):
        return "experience scaling issues"
    elif any(word in text_lower for word in ['secure', 'security']):
        return "encounter security implementation challenges"
    elif any(word in text_lower for word in ['test', 'testing']):
        return "face testing implementation difficulties"
    else:
        return "encounter implementation challenges"


def _validate_problem_statement(statement: str) -> bool:
    """Validate that the generated problem statement meets criteria"""
    
    if not statement or len(statement) < 20:
        return False
    
    # Must start with Users or People
    if not statement.strip().lower().startswith(('users', 'people')):
        return False
    
    # Should not contain solution words
    solution_words = ['use this', 'try this', 'solution', 'fix', 'tool that', 'just use']
    if any(word in statement.lower() for word in solution_words):
        return False
    
    # Should not contain emotional words
    emotional_words = ['help', 'please', 'frustrated', 'stupid', 'damn']
    if any(word in statement.lower() for word in emotional_words):
        return False
    
    return True


def process_post(original_text: str) -> str:
    """
    Convert Reddit text into a concise developer-style problem statement.
    Uses improved prompt for better AI-generated results with rule-based fallback.
    
    Note: This function maintains the original behavior for backward compatibility.
    For new problem statement generation, use generate_problem_statement() instead.
    """
    
    # For backward compatibility, use the enhanced problem statement generator
    return generate_problem_statement(original_text)


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

    print("\n🧪 Testing NEW generate_problem_statement function:")
    test_cases = [
        "For anyone struggling with TikTok watermarks, I use this free online tool that removes it fast.",
        "My React app crashes when I deploy to production with this awesome deployment script I found",
        "Docker containers use too much memory on my server but I fixed it with this memory optimization tool",
        "WHY is my laptop SO DAMN SLOW when I try to run multiple programs??? Chrome eats up all my memory!",
        "Need help choosing between PostgreSQL and MongoDB for my new social media project",
        "My build process fails with webpack errors and I can't figure out why the compilation keeps breaking"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        result = generate_problem_statement(test_case)
        print(f"\n{i}. Input: {test_case[:80]}...")
        print(f"   Problem Statement: {result}")

    print("\n🧪 Testing backward compatibility with process_post:")
    reddit_style_text = """
    I'm a complete beginner, and I wanted to know if I should use my laptop as some sort of home server, 
    not for work or anything, but for multiplayer games. I can't afford any new tech, so I wanted to know 
    if I can work with what I have. The laptop has an Intel Core i5-5200U, which clocks around 2.20GHz, 
    and has around 6gb of RAM. If I can turn it into a home server, what OS would be recommended
    """
    
    enhanced_statement = process_post(reddit_style_text)
    print("📝 Original:", reddit_style_text.strip()[:100] + "...")
    print("⚡ Enhanced Problem Statement:", enhanced_statement)
