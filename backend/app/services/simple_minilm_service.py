"""
Simple MiniLM Service for PainPoint AI (No TensorFlow Dependencies)
A lightweight version that provides basic text processing without heavy ML dependencies
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimpleMiniLMService:
    """
    Simplified MiniLM service that provides basic text processing
    without requiring TensorFlow or transformers dependencies
    """
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'about', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
            'just', 'don', 'should', 'now', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
            'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
            'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that',
            'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have',
            'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'would', 'could', 'should',
            'may', 'might', 'must', 'shall'
        }
        
        self.problem_keywords = {
            'software': ['app', 'application', 'software', 'program', 'code', 'bug', 'crash', 
                        'error', 'glitch', 'freeze', 'slow', 'update', 'install', 'download',
                        'website', 'browser', 'login', 'password', 'account', 'sync'],
            'hardware': ['computer', 'laptop', 'desktop', 'monitor', 'screen', 'keyboard', 
                        'mouse', 'printer', 'phone', 'tablet', 'battery', 'charging', 'port',
                        'cable', 'wifi', 'bluetooth', 'speaker', 'microphone', 'camera'],
            'performance': ['slow', 'fast', 'speed', 'lag', 'delay', 'timeout', 'loading',
                           'performance', 'memory', 'cpu', 'disk', 'storage', 'ram'],
            'connectivity': ['internet', 'wifi', 'network', 'connection', 'offline', 'online',
                            'router', 'modem', 'signal', 'bandwidth', 'ethernet']
        }
    
    async def generate_problem_statement(self, raw_text: str) -> str:
        """
        Generate a clear, concise problem statement from raw text
        """
        try:
            if not raw_text or not raw_text.strip():
                return "No problem description provided"
            
            # Basic text cleaning
            cleaned_text = self.preprocess_text(raw_text)
            
            # Extract key points
            key_points = self.extract_key_points(cleaned_text)
            
            # Generate problem statement
            problem_statement = self._create_problem_statement(key_points, cleaned_text)
            
            return problem_statement
            
        except Exception as e:
            logger.error(f"Error generating problem statement: {str(e)}")
            return f"Problem processing error: {cleaned_text[:100]}..."
    
    def preprocess_text(self, text: str) -> str:
        """
        Basic text preprocessing
        """
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove URLs
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            
            # Remove special characters but keep basic punctuation
            text = re.sub(r'[^\w\s\.,!?-]', ' ', text)
            
            # Normalize case
            text = text.lower()
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error preprocessing text: {str(e)}")
            return text
    
    def extract_key_points(self, text: str) -> List[str]:
        """
        Extract key points from the text
        """
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            
            key_points = []
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10:  # Ignore very short sentences
                    # Remove stop words and extract meaningful parts
                    words = sentence.split()
                    filtered_words = [word for word in words if word not in self.stop_words and len(word) > 2]
                    
                    if len(filtered_words) >= 3:  # Must have at least 3 meaningful words
                        key_points.append(' '.join(filtered_words))
            
            return key_points[:3]  # Return top 3 key points
            
        except Exception as e:
            logger.error(f"Error extracting key points: {str(e)}")
            return [text[:50] + "..."]
    
    def _create_problem_statement(self, key_points: List[str], original_text: str) -> str:
        """
        Create a structured problem statement
        """
        try:
            if not key_points:
                return f"Issue reported: {original_text[:100]}..."
            
            # Identify problem category
            category = self._identify_category(original_text)
            
            # Create structured statement
            if len(key_points) == 1:
                statement = f"{category} issue: {key_points[0]}"
            else:
                main_issue = key_points[0]
                details = '; '.join(key_points[1:])
                statement = f"{category} problem: {main_issue}. Details: {details}"
            
            # Ensure reasonable length
            if len(statement) > 200:
                statement = statement[:197] + "..."
            
            return statement.capitalize()
            
        except Exception as e:
            logger.error(f"Error creating problem statement: {str(e)}")
            return f"Problem reported: {original_text[:100]}..."
    
    def _identify_category(self, text: str) -> str:
        """
        Identify the problem category based on keywords
        """
        try:
            text_lower = text.lower()
            
            category_scores = {}
            for category, keywords in self.problem_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text_lower)
                if score > 0:
                    category_scores[category] = score
            
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                return best_category.capitalize()
            
            return "General"
            
        except Exception as e:
            logger.error(f"Error identifying category: {str(e)}")
            return "General"
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Placeholder for embedding generation (returns None in simple version)
        """
        # In the simple version, we don't generate actual embeddings
        # This could be implemented later with lighter libraries
        return None
    
    def is_available(self) -> bool:
        """
        Check if the service is available
        """
        return True  # Simple version is always available

# Create a global instance
simple_minilm_service = SimpleMiniLMService()

# Alias for compatibility
MiniLMService = SimpleMiniLMService
