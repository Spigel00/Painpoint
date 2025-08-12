"""
Solutions Controller for PainPoint AI
Handles problem claiming, solution tracking, and collaborative features
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from ..core.database import get_db
from ..controllers.auth_controller import get_current_active_user
from ..models.schemas import SolutionCreate, SolutionUpdate, SolutionResponse, ClaimProblemRequest
from ..models.db_models import User, FetchedProblem, Solution
from ..repositories.problem_repository import ProblemRepository
from ..repositories.solution_repository import SolutionRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/solutions", tags=["solutions"])

@router.post("/claim/{problem_id}", response_model=Dict[str, Any])
async def claim_problem(
    problem_id: int,
    claim_data: ClaimProblemRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Claim a problem to work on
    """
    try:
        logger.info(f"User {current_user.username} attempting to claim problem {problem_id}")
        
        problem_repo = ProblemRepository(db)
        solution_repo = SolutionRepository(db)
        
        # Get the problem
        problem = problem_repo.get_problem_by_id(problem_id)
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem not found"
            )
        
        # Check if problem is already claimed
        if problem.is_claimed:
            existing_solution = solution_repo.get_solution_by_problem_id(problem_id)
            if existing_solution and existing_solution.solver_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Problem is already claimed by another user"
                )
        
        # Create or update solution
        existing_solution = solution_repo.get_solution_by_problem_and_user(problem_id, current_user.id)
        
        if existing_solution:
            # Update existing solution
            existing_solution.github_repo = claim_data.github_repo
            existing_solution.description = claim_data.description
            existing_solution.updated_at = datetime.utcnow()
            solution = solution_repo.update_solution(existing_solution)
        else:
            # Create new solution
            solution_data = Solution(
                problem_id=problem_id,
                solver_id=current_user.id,
                github_repo=claim_data.github_repo,
                description=claim_data.description,
                status='in_progress',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            solution = solution_repo.create_solution(solution_data)
        
        # Mark problem as claimed
        problem.is_claimed = True
        problem.claimed_by = current_user.id
        problem.claimed_at = datetime.utcnow()
        problem_repo.update_problem(problem)
        
        logger.info(f"Problem {problem_id} claimed by user {current_user.username}")
        
        return {
            'success': True,
            'message': 'Problem claimed successfully',
            'solution_id': solution.id,
            'problem_id': problem_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error claiming problem: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to claim problem"
        )

@router.put("/{solution_id}", response_model=SolutionResponse)
async def update_solution(
    solution_id: int,
    solution_update: SolutionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> SolutionResponse:
    """
    Update solution details
    """
    try:
        solution_repo = SolutionRepository(db)
        
        # Get the solution
        solution = solution_repo.get_solution_by_id(solution_id)
        if not solution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solution not found"
            )
        
        # Check if user owns the solution
        if solution.solver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own solutions"
            )
        
        # Update solution
        for field, value in solution_update.dict(exclude_unset=True).items():
            setattr(solution, field, value)
        
        solution.updated_at = datetime.utcnow()
        updated_solution = solution_repo.update_solution(solution)
        
        logger.info(f"Solution {solution_id} updated by user {current_user.username}")
        
        return SolutionResponse(
            id=updated_solution.id,
            problem_id=updated_solution.problem_id,
            solver_id=updated_solution.solver_id,
            solver_username=current_user.username,
            github_repo=updated_solution.github_repo,
            demo_url=updated_solution.demo_url,
            description=updated_solution.description,
            status=updated_solution.status,
            created_at=updated_solution.created_at,
            updated_at=updated_solution.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating solution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update solution"
        )

@router.get("/my-solutions", response_model=List[SolutionResponse])
async def get_my_solutions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[SolutionResponse]:
    """
    Get all solutions by the current user
    """
    try:
        solution_repo = SolutionRepository(db)
        solutions = solution_repo.get_solutions_by_user(current_user.id)
        
        return [
            SolutionResponse(
                id=solution.id,
                problem_id=solution.problem_id,
                solver_id=solution.solver_id,
                solver_username=current_user.username,
                github_repo=solution.github_repo,
                demo_url=solution.demo_url,
                description=solution.description,
                status=solution.status,
                created_at=solution.created_at,
                updated_at=solution.updated_at
            )
            for solution in solutions
        ]
        
    except Exception as e:
        logger.error(f"Error getting user solutions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get solutions"
        )

@router.get("/problem/{problem_id}", response_model=List[SolutionResponse])
async def get_solutions_for_problem(
    problem_id: int,
    db: Session = Depends(get_db)
) -> List[SolutionResponse]:
    """
    Get all solutions for a specific problem
    """
    try:
        solution_repo = SolutionRepository(db)
        solutions = solution_repo.get_solutions_by_problem_id(problem_id)
        
        return [
            SolutionResponse(
                id=solution.id,
                problem_id=solution.problem_id,
                solver_id=solution.solver_id,
                solver_username=solution.solver.username if solution.solver else "Unknown",
                github_repo=solution.github_repo,
                demo_url=solution.demo_url,
                description=solution.description,
                status=solution.status,
                created_at=solution.created_at,
                updated_at=solution.updated_at
            )
            for solution in solutions
        ]
        
    except Exception as e:
        logger.error(f"Error getting problem solutions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get solutions"
        )

@router.delete("/{solution_id}", response_model=Dict[str, Any])
async def delete_solution(
    solution_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a solution (and unclaim the problem)
    """
    try:
        solution_repo = SolutionRepository(db)
        problem_repo = ProblemRepository(db)
        
        # Get the solution
        solution = solution_repo.get_solution_by_id(solution_id)
        if not solution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solution not found"
            )
        
        # Check if user owns the solution
        if solution.solver_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own solutions"
            )
        
        problem_id = solution.problem_id
        
        # Delete the solution
        solution_repo.delete_solution(solution_id)
        
        # Check if there are other solutions for this problem
        remaining_solutions = solution_repo.get_solutions_by_problem_id(problem_id)
        
        # If no more solutions, unclaim the problem
        if not remaining_solutions:
            problem = problem_repo.get_problem_by_id(problem_id)
            if problem:
                problem.is_claimed = False
                problem.claimed_by = None
                problem.claimed_at = None
                problem_repo.update_problem(problem)
        
        logger.info(f"Solution {solution_id} deleted by user {current_user.username}")
        
        return {
            'success': True,
            'message': 'Solution deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting solution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete solution"
        )

@router.get("/stats/user", response_model=Dict[str, Any])
async def get_user_solution_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get solution statistics for the current user
    """
    try:
        solution_repo = SolutionRepository(db)
        
        solutions = solution_repo.get_solutions_by_user(current_user.id)
        
        stats = {
            'total_solutions': len(solutions),
            'in_progress': sum(1 for s in solutions if s.status == 'in_progress'),
            'completed': sum(1 for s in solutions if s.status == 'completed'),
            'with_github': sum(1 for s in solutions if s.github_repo),
            'with_demo': sum(1 for s in solutions if s.demo_url)
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user statistics"
        )
