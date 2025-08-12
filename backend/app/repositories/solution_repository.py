"""
Solution Repository for PainPoint AI
Handles database operations for solutions and problem claiming
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from ..models.db_models import Solution, User, FetchedProblem

logger = logging.getLogger(__name__)

class SolutionRepository:
    """
    Repository for solution database operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_solution(self, solution: Solution) -> Solution:
        """
        Create a new solution
        """
        try:
            self.db.add(solution)
            self.db.commit()
            self.db.refresh(solution)
            return solution
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating solution: {str(e)}")
            raise
    
    def get_solution_by_id(self, solution_id: int) -> Optional[Solution]:
        """
        Get solution by ID
        """
        try:
            return self.db.query(Solution).filter(Solution.id == solution_id).first()
        except Exception as e:
            logger.error(f"Error getting solution by ID {solution_id}: {str(e)}")
            return None
    
    def get_solution_by_problem_id(self, problem_id: int) -> Optional[Solution]:
        """
        Get the first solution for a problem (for checking if claimed)
        """
        try:
            return self.db.query(Solution).filter(Solution.problem_id == problem_id).first()
        except Exception as e:
            logger.error(f"Error getting solution by problem ID {problem_id}: {str(e)}")
            return None
    
    def get_solution_by_problem_and_user(self, problem_id: int, user_id: int) -> Optional[Solution]:
        """
        Get solution by problem and user (for checking existing claims)
        """
        try:
            return self.db.query(Solution).filter(
                Solution.problem_id == problem_id,
                Solution.solver_id == user_id
            ).first()
        except Exception as e:
            logger.error(f"Error getting solution by problem {problem_id} and user {user_id}: {str(e)}")
            return None
    
    def get_solutions_by_problem_id(self, problem_id: int) -> List[Solution]:
        """
        Get all solutions for a specific problem
        """
        try:
            return self.db.query(Solution).filter(
                Solution.problem_id == problem_id
            ).order_by(Solution.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting solutions for problem {problem_id}: {str(e)}")
            return []
    
    def get_solutions_by_user(self, user_id: int) -> List[Solution]:
        """
        Get all solutions by a specific user
        """
        try:
            return self.db.query(Solution).filter(
                Solution.solver_id == user_id
            ).order_by(Solution.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting solutions for user {user_id}: {str(e)}")
            return []
    
    def update_solution(self, solution: Solution) -> Solution:
        """
        Update an existing solution
        """
        try:
            solution.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(solution)
            return solution
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating solution {solution.id}: {str(e)}")
            raise
    
    def delete_solution(self, solution_id: int) -> bool:
        """
        Delete a solution
        """
        try:
            solution = self.get_solution_by_id(solution_id)
            if solution:
                self.db.delete(solution)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting solution {solution_id}: {str(e)}")
            raise
    
    def get_recent_solutions(self, days: int = 7, limit: int = 100) -> List[Solution]:
        """
        Get recent solutions
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            return self.db.query(Solution).filter(
                Solution.created_at >= cutoff_date
            ).order_by(Solution.created_at.desc()).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting recent solutions: {str(e)}")
            return []
    
    def get_solutions_with_github(self) -> List[Solution]:
        """
        Get all solutions that have GitHub repositories linked
        """
        try:
            return self.db.query(Solution).filter(
                Solution.github_repo.isnot(None),
                Solution.github_repo != ''
            ).order_by(Solution.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting solutions with GitHub: {str(e)}")
            return []
    
    def get_solutions_by_status(self, status: str) -> List[Solution]:
        """
        Get solutions by status (in_progress, completed, etc.)
        """
        try:
            return self.db.query(Solution).filter(
                Solution.status == status
            ).order_by(Solution.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting solutions by status {status}: {str(e)}")
            return []
    
    def get_solution_stats(self) -> dict:
        """
        Get solution statistics
        """
        try:
            from sqlalchemy import func
            
            total_solutions = self.db.query(func.count(Solution.id)).scalar() or 0
            
            in_progress = self.db.query(func.count(Solution.id)).filter(
                Solution.status == 'in_progress'
            ).scalar() or 0
            
            completed = self.db.query(func.count(Solution.id)).filter(
                Solution.status == 'completed'
            ).scalar() or 0
            
            with_github = self.db.query(func.count(Solution.id)).filter(
                Solution.github_repo.isnot(None),
                Solution.github_repo != ''
            ).scalar() or 0
            
            with_demo = self.db.query(func.count(Solution.id)).filter(
                Solution.demo_url.isnot(None),
                Solution.demo_url != ''
            ).scalar() or 0
            
            unique_solvers = self.db.query(func.count(func.distinct(Solution.solver_id))).scalar() or 0
            
            return {
                'total_solutions': total_solutions,
                'in_progress': in_progress,
                'completed': completed,
                'with_github': with_github,
                'with_demo': with_demo,
                'unique_solvers': unique_solvers
            }
            
        except Exception as e:
            logger.error(f"Error getting solution stats: {str(e)}")
            return {
                'total_solutions': 0,
                'in_progress': 0,
                'completed': 0,
                'with_github': 0,
                'with_demo': 0,
                'unique_solvers': 0
            }
