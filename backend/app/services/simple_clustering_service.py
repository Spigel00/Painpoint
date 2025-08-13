"""
Simple Clustering Service for PainPoint AI (No scikit-learn Dependencies)
A lightweight version that provides basic categorization without ML dependencies
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class SimpleClusteringService:
    """
    Simplified clustering service that provides rule-based categorization
    without requiring scikit-learn or other ML dependencies
    """
    
    def __init__(self):
        # Predefined categories with keywords
        self.categories = {
            'Software Needs': {
                'keywords': [
                    'app', 'application', 'software', 'program', 'tool', 'platform',
                    'website', 'web', 'browser', 'mobile', 'desktop', 'api', 'service',
                    'feature', 'functionality', 'automation', 'integration', 'workflow',
                    'dashboard', 'interface', 'ui', 'ux', 'user experience', 'usability'
                ],
                'patterns': [
                    r'need.*app', r'want.*software', r'looking.*tool', r'build.*platform',
                    r'create.*website', r'develop.*application', r'make.*program'
                ]
            },
            'Hardware Needs': {
                'keywords': [
                    'computer', 'laptop', 'desktop', 'server', 'device', 'hardware',
                    'monitor', 'screen', 'keyboard', 'mouse', 'printer', 'scanner',
                    'phone', 'tablet', 'router', 'network', 'cable', 'connector',
                    'battery', 'power', 'charging', 'port', 'usb', 'hdmi'
                ],
                'patterns': [
                    r'need.*computer', r'want.*laptop', r'looking.*hardware',
                    r'buy.*device', r'purchase.*equipment', r'get.*machine'
                ]
            },
            'Tech Support': {
                'keywords': [
                    'help', 'support', 'fix', 'broken', 'error', 'problem', 'issue',
                    'bug', 'crash', 'freeze', 'slow', 'not working', 'trouble',
                    'troubleshoot', 'repair', 'resolve', 'solution', 'assistance'
                ],
                'patterns': [
                    r'help.*with', r'how.*fix', r'can.*repair', r'need.*support',
                    r'problem.*with', r'issue.*with', r'trouble.*with'
                ]
            },
            'Developer Tools': {
                'keywords': [
                    'code', 'programming', 'development', 'developer', 'coding',
                    'framework', 'library', 'ide', 'editor', 'compiler', 'debugger',
                    'git', 'github', 'version control', 'deployment', 'testing',
                    'database', 'sql', 'api', 'backend', 'frontend', 'full stack'
                ],
                'patterns': [
                    r'need.*code', r'want.*framework', r'looking.*library',
                    r'build.*with', r'develop.*using', r'programming.*language'
                ]
            },
            'Infrastructure': {
                'keywords': [
                    'server', 'cloud', 'hosting', 'deployment', 'infrastructure',
                    'network', 'security', 'backup', 'storage', 'database',
                    'monitoring', 'analytics', 'performance', 'scaling', 'devops'
                ],
                'patterns': [
                    r'need.*server', r'want.*hosting', r'looking.*cloud',
                    r'deploy.*to', r'host.*on', r'infrastructure.*for'
                ]
            }
        }
        
        # Default confidence threshold
        self.min_confidence = 0.3
    
    async def predict_category(self, text: str) -> Tuple[str, float]:
        """
        Predict the category for a given text
        """
        try:
            if not text or not text.strip():
                return 'Other', 0.0
            
            text_lower = text.lower()
            category_scores = {}
            
            # Calculate scores for each category
            for category, config in self.categories.items():
                score = self._calculate_category_score(text_lower, config)
                if score > 0:
                    category_scores[category] = score
            
            # Find best category
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                confidence = min(category_scores[best_category], 1.0)  # Cap at 1.0
                
                if confidence >= self.min_confidence:
                    return best_category, confidence
            
            return 'Other', 0.1  # Default category with low confidence
            
        except Exception as e:
            logger.error(f"Error predicting category: {str(e)}")
            return 'Other', 0.0
    
    def _calculate_category_score(self, text: str, config: Dict[str, List[str]]) -> float:
        """
        Calculate score for a category based on keywords and patterns
        """
        try:
            score = 0.0
            
            # Check keywords
            keywords = config.get('keywords', [])
            keyword_matches = sum(1 for keyword in keywords if keyword in text)
            
            if keyword_matches > 0:
                # Normalize by text length and keyword count
                keyword_score = min(keyword_matches / len(keywords), 0.8)
                score += keyword_score
            
            # Check patterns
            patterns = config.get('patterns', [])
            pattern_matches = 0
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    pattern_matches += 1
            
            if pattern_matches > 0:
                pattern_score = min(pattern_matches / len(patterns), 0.6)
                score += pattern_score
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating category score: {str(e)}")
            return 0.0
    
    async def update_clustering_model(self, texts: List[str]) -> bool:
        """
        Update clustering model (placeholder in simple version)
        """
        try:
            # In the simple version, we don't actually update the model
            # This could be implemented later with actual ML
            logger.info(f"Model update requested for {len(texts)} texts (simple version)")
            return True
            
        except Exception as e:
            logger.error(f"Error updating clustering model: {str(e)}")
            return False
    
    def get_categories(self) -> List[str]:
        """
        Get list of available categories
        """
        return list(self.categories.keys()) + ['Other']
    
    def get_category_info(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific category
        """
        if category in self.categories:
            return {
                'name': category,
                'keywords': self.categories[category]['keywords'][:10],  # Return first 10 keywords
                'keyword_count': len(self.categories[category]['keywords']),
                'pattern_count': len(self.categories[category]['patterns'])
            }
        elif category == 'Other':
            return {
                'name': 'Other',
                'description': 'Problems that don\'t fit into predefined categories',
                'keywords': [],
                'keyword_count': 0,
                'pattern_count': 0
            }
        return None
    
    async def batch_predict(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Predict categories for multiple texts
        """
        results = []
        for text in texts:
            category, confidence = await self.predict_category(text)
            results.append((category, confidence))
        return results
    
    def is_available(self) -> bool:
        """
        Check if the service is available
        """
        return True  # Simple version is always available

# Create a global instance
simple_clustering_service = SimpleClusteringService()

# Alias for compatibility
ClusteringService = SimpleClusteringService
