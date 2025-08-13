"""
Enhanced RAG Controller for PainPoint AI
Handles enhanced RAG operations, continuous pipeline management, and monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from ..core.database import get_db
from ..controllers.auth_controller import get_current_active_user
from ..services.enhanced_rag_service import get_rag_service
from ..models.db_models import User, ProblemSummary
from ..repositories.problem_repository import ProblemRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rag", tags=["rag_pipeline"])

@router.post("/start", response_model=Dict[str, Any])
async def start_pipeline(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Start the continuous RAG pipeline (admin only)
    """
    try:
        # For now, allow any authenticated user to start/stop
        # In production, you might want to add admin-only checks
        
        rag_service = get_rag_service()
        
        if rag_service.is_running:
            return {
                'success': False,
                'message': 'Pipeline is already running',
                'status': 'running'
            }
        
        await rag_service.start_continuous_pipeline()
        
        logger.info(f"RAG pipeline started by user {current_user.username}")
        
        return {
            'success': True,
            'message': 'RAG pipeline started successfully',
            'status': 'running'
        }
        
    except Exception as e:
        logger.error(f"Error starting RAG pipeline: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start pipeline: {str(e)}"
        )

@router.post("/stop", response_model=Dict[str, Any])
async def stop_pipeline(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Stop the continuous RAG pipeline (admin only)
    """
    try:
        rag_service = get_rag_service()
        
        if not rag_service.is_running:
            return {
                'success': False,
                'message': 'Pipeline is not running',
                'status': 'stopped'
            }
        
        await rag_service.stop_continuous_pipeline()
        
        logger.info(f"RAG pipeline stopped by user {current_user.username}")
        
        return {
            'success': True,
            'message': 'RAG pipeline stopped successfully',
            'status': 'stopped'
        }
        
    except Exception as e:
        logger.error(f"Error stopping RAG pipeline: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop pipeline: {str(e)}"
        )

@router.get("/status", response_model=Dict[str, Any])
async def get_pipeline_status() -> Dict[str, Any]:
    """
    Get the current status of the RAG pipeline
    """
    try:
        rag_service = get_rag_service()
        status = await rag_service.get_pipeline_status()
        
        return {
            'success': True,
            'pipeline_status': status
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pipeline status: {str(e)}"
        )

@router.post("/manual-collection", response_model=Dict[str, Any])
async def trigger_manual_collection(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Manually trigger data collection
    """
    try:
        rag_service = get_rag_service()
        result = await rag_service.manual_data_collection()
        
        logger.info(f"Manual data collection triggered by user {current_user.username}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in manual data collection: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Manual collection failed: {str(e)}"
        )

@router.get("/summaries", response_model=List[Dict[str, Any]])
async def get_recent_summaries(
    days: int = 7,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get recent problem summaries
    """
    try:
        from datetime import datetime, timedelta
        
        # Get summaries from the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        summaries = db.query(ProblemSummary).filter(
            ProblemSummary.created_at >= cutoff_date
        ).order_by(ProblemSummary.created_at.desc()).all()
        
        return [
            {
                'id': summary.id,
                'category': summary.category,
                'summary_text': summary.summary_text,
                'problem_count': summary.problem_count,
                'time_period': summary.time_period,
                'created_at': summary.created_at.isoformat()
            }
            for summary in summaries
        ]
        
    except Exception as e:
        logger.error(f"Error getting summaries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get summaries"
        )

@router.get("/metrics", response_model=Dict[str, Any])
async def get_pipeline_metrics(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get pipeline performance metrics
    """
    try:
        from datetime import datetime, timedelta
        
        problem_repo = ProblemRepository(db)
        
        # Get metrics for different time periods
        now = datetime.utcnow()
        
        metrics = {
            'last_24h': {},
            'last_7d': {},
            'last_30d': {},
            'total': {}
        }
        
        time_periods = [
            ('last_24h', 1),
            ('last_7d', 7),
            ('last_30d', 30)
        ]
        
        for period_name, days in time_periods:
            cutoff_date = now - timedelta(days=days)
            
            # Get problems from this period
            recent_problems = problem_repo.get_recent_problems(days=days, limit=10000)
            
            metrics[period_name] = {
                'total_problems': len(recent_problems),
                'claimed_problems': sum(1 for p in recent_problems if p.is_claimed),
                'unclaimed_problems': sum(1 for p in recent_problems if not p.is_claimed),
                'categories': {}
            }
            
            # Count by category
            for problem in recent_problems:
                category = problem.category or 'Uncategorized'
                if category not in metrics[period_name]['categories']:
                    metrics[period_name]['categories'][category] = 0
                metrics[period_name]['categories'][category] += 1
        
        # Get total metrics (all time)
        all_problems = problem_repo.get_all_problems(limit=50000)
        
        metrics['total'] = {
            'total_problems': len(all_problems),
            'claimed_problems': sum(1 for p in all_problems if p.is_claimed),
            'unclaimed_problems': sum(1 for p in all_problems if not p.is_claimed),
            'categories': {}
        }
        
        for problem in all_problems:
            category = problem.category or 'Uncategorized'
            if category not in metrics['total']['categories']:
                metrics['total']['categories'][category] = 0
            metrics['total']['categories'][category] += 1
        
        return {
            'success': True,
            'metrics': metrics,
            'generated_at': now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get metrics"
        )
