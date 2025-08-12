"""
Enhanced RAG (Retrieval-Augmented Generation) Service for PainPoint AI
Handles continuous data collection, MiniLM processing, clustering, and intelligent problem summarization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import threading

from ..core.config import settings
from ..core.database import get_db
from .real_reddit_fetcher import comprehensive_real_reddit_fetch
from .simple_minilm_service import SimpleMiniLMService
from .simple_clustering_service import SimpleClusteringService
from ..models.db_models import FetchedProblem, ProblemSummary, User
from ..repositories.problem_repository import ProblemRepository
import re
import json

logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """
    Enhanced RAG service with continuous background processing and MiniLM integration
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.minilm_service = SimpleMiniLMService()
        self.clustering_service = SimpleClusteringService()
        self.is_running = False
        self.processing_lock = threading.Lock()
        
    async def start_continuous_pipeline(self):
        """
        Start the continuous RAG pipeline that runs in the background
        """
        if self.is_running:
            logger.warning("Continuous pipeline is already running")
            return
            
        try:
            logger.info("Starting continuous RAG pipeline...")
            
            # Schedule data collection every 30 minutes
            self.scheduler.add_job(
                self._collect_and_process_data,
                trigger=IntervalTrigger(minutes=30),
                id='data_collection',
                name='Continuous Data Collection',
                max_instances=1,
                replace_existing=True
            )
            
            # Schedule clustering update every 2 hours
            self.scheduler.add_job(
                self._update_clustering,
                trigger=IntervalTrigger(hours=2),
                id='clustering_update',
                name='Problem Clustering Update',
                max_instances=1,
                replace_existing=True
            )
            
            # Schedule problem summarization every hour
            self.scheduler.add_job(
                self._generate_summaries,
                trigger=IntervalTrigger(hours=1),
                id='summary_generation',
                name='Problem Summary Generation',
                max_instances=1,
                replace_existing=True
            )
            
            self.scheduler.start()
            self.is_running = True
            
            # Run initial collection
            await self._collect_and_process_data()
            
            logger.info("Continuous RAG pipeline started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start continuous pipeline: {str(e)}")
            raise
    
    async def stop_continuous_pipeline(self):
        """
        Stop the continuous RAG pipeline
        """
        if not self.is_running:
            logger.warning("Continuous pipeline is not running")
            return
            
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Continuous RAG pipeline stopped")
        except Exception as e:
            logger.error(f"Error stopping continuous pipeline: {str(e)}")
    
    async def _collect_and_process_data(self):
        """
        Collect new data from Reddit and process with MiniLM
        """
        with self.processing_lock:
            try:
                logger.info("Starting data collection and processing cycle...")
                
                db = next(get_db())
                problem_repo = ProblemRepository(db)
                
                # Collect new Reddit data
                reddit_problems = await self._fetch_reddit_data()
                
                # Process each problem with MiniLM
                processed_count = 0
                for problem_data in reddit_problems:
                    try:
                        # Generate clear problem statement using MiniLM
                        clear_statement = await self.minilm_service.generate_problem_statement(
                            problem_data.get('content', '')
                        )
                        
                        # Get automatic clustering
                        category, confidence = await self.clustering_service.predict_category(
                            clear_statement
                        )
                        
                        # Create enhanced problem record
                        problem = FetchedProblem(
                            source='reddit',
                            original_content=problem_data.get('content', ''),
                            processed_content=clear_statement,
                            title=problem_data.get('title', ''),
                            url=problem_data.get('url', ''),
                            author=problem_data.get('author', ''),
                            created_at=datetime.now(),
                            upvotes=problem_data.get('upvotes', 0),
                            category=category,
                            clustering_confidence=confidence,
                            is_claimed=False
                        )
                        
                        # Save to database
                        saved_problem = problem_repo.create_problem(problem)
                        processed_count += 1
                        
                        logger.debug(f"Processed problem {saved_problem.id}: {category} (confidence: {confidence:.2f})")
                        
                    except Exception as e:
                        logger.error(f"Error processing individual problem: {str(e)}")
                        continue
                
                logger.info(f"Data collection cycle completed. Processed {processed_count} new problems")
                
            except Exception as e:
                logger.error(f"Error in data collection cycle: {str(e)}")
            finally:
                db.close()
    
    async def _fetch_reddit_data(self) -> List[Dict[str, Any]]:
        """
        Fetch new data from Reddit
        """
        try:
            # Use existing Reddit fetcher
            reddit_data = await comprehensive_real_reddit_fetch()
            
            if not reddit_data or not reddit_data.get('success', False):
                logger.warning("Reddit data fetch was not successful")
                return []
            
            problems = reddit_data.get('problems', [])
            logger.info(f"Fetched {len(problems)} problems from Reddit")
            
            return problems
            
        except Exception as e:
            logger.error(f"Error fetching Reddit data: {str(e)}")
            return []
    
    async def _update_clustering(self):
        """
        Update clustering model with new data
        """
        try:
            logger.info("Starting clustering update...")
            
            db = next(get_db())
            problem_repo = ProblemRepository(db)
            
            # Get recent unclustered or low-confidence problems
            recent_problems = problem_repo.get_recent_problems(
                days=7,
                limit=1000
            )
            
            if not recent_problems:
                logger.info("No recent problems found for clustering update")
                return
            
            # Extract processed content for clustering
            problem_texts = [p.processed_content for p in recent_problems if p.processed_content]
            
            if len(problem_texts) < 10:
                logger.info("Not enough problems for meaningful clustering update")
                return
            
            # Update clustering model
            await self.clustering_service.update_clustering_model(problem_texts)
            
            # Re-cluster problems with low confidence
            updated_count = 0
            for problem in recent_problems:
                if problem.clustering_confidence < 0.7:  # Re-cluster low confidence problems
                    try:
                        new_category, new_confidence = await self.clustering_service.predict_category(
                            problem.processed_content
                        )
                        
                        if new_confidence > problem.clustering_confidence:
                            problem.category = new_category
                            problem.clustering_confidence = new_confidence
                            problem_repo.update_problem(problem)
                            updated_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error re-clustering problem {problem.id}: {str(e)}")
                        continue
            
            logger.info(f"Clustering update completed. Updated {updated_count} problems")
            
        except Exception as e:
            logger.error(f"Error in clustering update: {str(e)}")
        finally:
            db.close()
    
    async def _generate_summaries(self):
        """
        Generate problem summaries for trending issues
        """
        try:
            logger.info("Starting summary generation...")
            
            db = next(get_db())
            problem_repo = ProblemRepository(db)
            
            # Get problems from last 24 hours grouped by category
            recent_problems = problem_repo.get_recent_problems(days=1, limit=500)
            
            if not recent_problems:
                logger.info("No recent problems found for summary generation")
                return
            
            # Group by category
            category_groups = {}
            for problem in recent_problems:
                category = problem.category or 'Uncategorized'
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(problem)
            
            # Generate summaries for categories with multiple problems
            summary_count = 0
            for category, problems in category_groups.items():
                if len(problems) >= 3:  # Only summarize if we have multiple problems
                    try:
                        summary = await self._create_category_summary(category, problems)
                        
                        # Save summary to database
                        summary_record = ProblemSummary(
                            category=category,
                            summary_text=summary,
                            problem_count=len(problems),
                            created_at=datetime.now(),
                            time_period='24h'
                        )
                        
                        db.add(summary_record)
                        db.commit()
                        summary_count += 1
                        
                    except Exception as e:
                        logger.error(f"Error generating summary for category {category}: {str(e)}")
                        continue
            
            logger.info(f"Summary generation completed. Generated {summary_count} summaries")
            
        except Exception as e:
            logger.error(f"Error in summary generation: {str(e)}")
        finally:
            db.close()
    
    async def _create_category_summary(self, category: str, problems: List[FetchedProblem]) -> str:
        """
        Create a summary for a category of problems
        """
        try:
            # Extract key themes from problem statements
            problem_texts = [p.processed_content for p in problems if p.processed_content]
            
            # Simple extractive summarization
            common_themes = self._extract_common_themes(problem_texts)
            
            summary = f"Recent trends in {category}:\n\n"
            summary += f"• {len(problems)} problems reported in the last 24 hours\n"
            summary += f"• Common themes: {', '.join(common_themes[:5])}\n"
            
            # Add top problem examples
            top_problems = sorted(problems, key=lambda x: x.upvotes or 0, reverse=True)[:3]
            summary += "\nTop reported issues:\n"
            for i, problem in enumerate(top_problems, 1):
                summary += f"{i}. {problem.processed_content[:100]}...\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating category summary: {str(e)}")
            return f"Summary for {category}: {len(problems)} problems reported"
    
    def _extract_common_themes(self, texts: List[str]) -> List[str]:
        """
        Extract common themes from a list of problem texts
        """
        try:
            # Simple keyword extraction
            word_freq = {}
            
            for text in texts:
                # Extract meaningful words
                words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
                
                # Filter out common words
                stop_words = {'that', 'with', 'have', 'this', 'will', 'your', 'from', 
                             'they', 'know', 'want', 'been', 'good', 'much', 'some',
                             'time', 'very', 'when', 'come', 'here', 'could', 'would'}
                
                for word in words:
                    if word not in stop_words:
                        word_freq[word] = word_freq.get(word, 0) + 1
            
            # Return most common themes
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            return [word for word, freq in sorted_words[:10] if freq >= 2]
            
        except Exception as e:
            logger.error(f"Error extracting themes: {str(e)}")
            return []
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the status of the continuous pipeline
        """
        try:
            status = {
                'is_running': self.is_running,
                'scheduler_running': self.scheduler.running if hasattr(self.scheduler, 'running') else False,
                'jobs': []
            }
            
            if self.is_running:
                for job in self.scheduler.get_jobs():
                    job_info = {
                        'id': job.id,
                        'name': job.name,
                        'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                        'trigger': str(job.trigger)
                    }
                    status['jobs'].append(job_info)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {str(e)}")
            return {'is_running': False, 'error': str(e)}
    
    async def manual_data_collection(self) -> Dict[str, Any]:
        """
        Manually trigger data collection (for testing or immediate updates)
        """
        try:
            logger.info("Manual data collection triggered")
            await self._collect_and_process_data()
            return {
                'success': True,
                'message': 'Manual data collection completed',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Manual data collection failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global instance
enhanced_rag_service = EnhancedRAGService()

async def start_rag_pipeline():
    """
    Start the enhanced RAG pipeline
    """
    await enhanced_rag_service.start_continuous_pipeline()

async def stop_rag_pipeline():
    """
    Stop the enhanced RAG pipeline
    """
    await enhanced_rag_service.stop_continuous_pipeline()

def get_rag_service() -> EnhancedRAGService:
    """
    Get the global RAG service instance
    """
    return enhanced_rag_service
