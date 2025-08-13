"""
Enhanced Problems Controller for PainPoint AI
Handles enhanced problem browsing with authentication and collaborative features
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ..core.database import get_db
from ..controllers.auth_controller import get_current_active_user
from ..models.schemas import EnhancedProblemResponse, SolutionResponse
from ..models.db_models import User, FetchedProblem
from ..repositories.problem_repository import ProblemRepository
from ..repositories.solution_repository import SolutionRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/enhanced-problems", tags=["enhanced_problems"])

@router.get("/", response_model=List[EnhancedProblemResponse])
async def get_enhanced_problems(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    claimed_only: bool = False,
    unclaimed_only: bool = False,
    db: Session = Depends(get_db)
) -> List[EnhancedProblemResponse]:
    """
    Get enhanced problems with solution information
    """
    try:
        problem_repo = ProblemRepository(db)
        solution_repo = SolutionRepository(db)
        
        # Get problems based on filters
        if category:
            problems = problem_repo.get_problems_by_category(category, limit + skip)[skip:]
        else:
            problems = problem_repo.get_all_problems(limit + skip)[skip:]
        
        # Filter by claim status if specified
        if claimed_only:
            problems = [p for p in problems if p.is_claimed]
        elif unclaimed_only:
            problems = [p for p in problems if not p.is_claimed]
        
        # Build enhanced responses
        enhanced_problems = []
        for problem in problems:
            # Get solutions for this problem
            solutions = solution_repo.get_solutions_by_problem_id(problem.id)
            
            solution_responses = []
            for solution in solutions:
                solver_username = "Unknown"
                if solution.solver:
                    solver_username = solution.solver.username
                
                solution_responses.append(SolutionResponse(
                    id=solution.id,
                    problem_id=solution.problem_id,
                    solver_id=solution.solver_id,
                    solver_username=solver_username,
                    github_repo=solution.github_repo,
                    demo_url=solution.demo_url,
                    description=solution.description,
                    status=solution.status,
                    created_at=solution.created_at,
                    updated_at=solution.updated_at
                ))
            
            enhanced_problems.append(EnhancedProblemResponse(
                id=problem.id,
                title=problem.title,
                original_content=problem.description,
                processed_content=getattr(problem, 'processed_content', None),
                category=problem.category,
                clustering_confidence=getattr(problem, 'clustering_confidence', None),
                source=problem.subreddit or 'reddit',
                url=problem.url,
                author=problem.author,
                upvotes=problem.upvotes,
                created_at=problem.created_at,
                is_claimed=problem.is_claimed or False,
                claimed_by=getattr(problem, 'claimed_by', None),
                claimed_at=getattr(problem, 'claimed_at', None),
                solutions=solution_responses
            ))
        
        return enhanced_problems[:limit]
        
    except Exception as e:
        logger.error(f"Error getting enhanced problems: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get enhanced problems"
        )

@router.get("/{problem_id}", response_model=EnhancedProblemResponse)
async def get_enhanced_problem(
    problem_id: int,
    db: Session = Depends(get_db)
) -> EnhancedProblemResponse:
    """
    Get a specific enhanced problem with all solution details
    """
    try:
        problem_repo = ProblemRepository(db)
        solution_repo = SolutionRepository(db)
        
        # Get the problem
        problem = problem_repo.get_problem_by_id(problem_id)
        if not problem:
            raise HTTPException(
                status_code=404,
                detail="Problem not found"
            )
        
        # Get solutions for this problem
        solutions = solution_repo.get_solutions_by_problem_id(problem_id)
        
        solution_responses = []
        for solution in solutions:
            solver_username = "Unknown"
            if solution.solver:
                solver_username = solution.solver.username
            
            solution_responses.append(SolutionResponse(
                id=solution.id,
                problem_id=solution.problem_id,
                solver_id=solution.solver_id,
                solver_username=solver_username,
                github_repo=solution.github_repo,
                demo_url=solution.demo_url,
                description=solution.description,
                status=solution.status,
                created_at=solution.created_at,
                updated_at=solution.updated_at
            ))
        
        return EnhancedProblemResponse(
            id=problem.id,
            title=problem.title,
            original_content=problem.description,
            processed_content=getattr(problem, 'processed_content', None),
            category=problem.category,
            clustering_confidence=getattr(problem, 'clustering_confidence', None),
            source=problem.subreddit or 'reddit',
            url=problem.url,
            author=problem.author,
            upvotes=problem.upvotes,
            created_at=problem.created_at,
            is_claimed=problem.is_claimed or False,
            claimed_by=getattr(problem, 'claimed_by', None),
            claimed_at=getattr(problem, 'claimed_at', None),
            solutions=solution_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enhanced problem {problem_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get enhanced problem"
        )

@router.get("/user/claimable", response_model=List[EnhancedProblemResponse])
async def get_claimable_problems(
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[EnhancedProblemResponse]:
    """
    Get problems that the current user can claim (unclaimed problems)
    """
    try:
        problem_repo = ProblemRepository(db)
        
        # Get unclaimed problems
        if category:
            problems = problem_repo.get_problems_by_category(category, limit * 2)
        else:
            problems = problem_repo.get_all_problems(limit * 2)
        
        # Filter to unclaimed only
        unclaimed_problems = [p for p in problems if not (p.is_claimed or False)][:limit]
        
        # Build responses (no solutions since these are unclaimed)
        enhanced_problems = []
        for problem in unclaimed_problems:
            enhanced_problems.append(EnhancedProblemResponse(
                id=problem.id,
                title=problem.title,
                original_content=problem.description,
                processed_content=getattr(problem, 'processed_content', None),
                category=problem.category,
                clustering_confidence=getattr(problem, 'clustering_confidence', None),
                source=problem.subreddit or 'reddit',
                url=problem.url,
                author=problem.author,
                upvotes=problem.upvotes,
                created_at=problem.created_at,
                is_claimed=False,
                claimed_by=None,
                claimed_at=None,
                solutions=[]
            ))
        
        return enhanced_problems
        
    except Exception as e:
        logger.error(f"Error getting claimable problems: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get claimable problems"
        )

@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_problems_overview(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get problems overview statistics
    """
    try:
        problem_repo = ProblemRepository(db)
        solution_repo = SolutionRepository(db)
        
        # Get all problems for stats
        all_problems = problem_repo.get_all_problems(10000)
        
        # Basic stats
        total_problems = len(all_problems)
        claimed_problems = sum(1 for p in all_problems if p.is_claimed or False)
        unclaimed_problems = total_problems - claimed_problems
        
        # Category distribution
        category_stats = {}
        for problem in all_problems:
            category = problem.category or 'Uncategorized'
            category_stats[category] = category_stats.get(category, 0) + 1
        
        # Solution stats
        solution_stats = solution_repo.get_solution_stats()
        
        # Recent activity (last 7 days)
        recent_problems = problem_repo.get_recent_problems(days=7)
        recent_solutions = solution_repo.get_recent_solutions(days=7)
        
        return {
            'total_problems': total_problems,
            'claimed_problems': claimed_problems,
            'unclaimed_problems': unclaimed_problems,
            'categories': category_stats,
            'solutions': solution_stats,
            'recent_activity': {
                'problems_last_7d': len(recent_problems),
                'solutions_last_7d': len(recent_solutions)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting problems overview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get problems overview"
        )
