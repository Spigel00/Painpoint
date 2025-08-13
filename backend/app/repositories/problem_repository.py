from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from ..models.db_models import Problem, FetchedProblem, ProblemSummary
from ..models.schemas import ProblemCreate
from typing import List, Optional
from datetime import datetime, timedelta


class ProblemRepository:
	"""Repository for problem-related database operations"""
	
	def __init__(self, db: Session):
		self.db = db
	
	def get_problem_by_id(self, problem_id: int) -> Optional[FetchedProblem]:
		"""Get a specific problem by ID"""
		return self.db.query(FetchedProblem).filter(FetchedProblem.id == problem_id).first()
	
	def get_recent_problems(
		self, 
		days: int = 7, 
		limit: int = 100,
		category: Optional[str] = None
	) -> List[FetchedProblem]:
		"""Get recent problems from the last N days"""
		since = datetime.utcnow() - timedelta(days=days)
		since_timestamp = int(since.timestamp())
		
		query = self.db.query(FetchedProblem).filter(FetchedProblem.created_utc >= since_timestamp)
		
		if category:
			query = query.filter(FetchedProblem.category == category)
		
		return query.order_by(desc(FetchedProblem.created_utc)).limit(limit).all()
	
	def get_all_problems(self, limit: int = 10000) -> List[FetchedProblem]:
		"""Get all problems (with limit for performance)"""
		return self.db.query(FetchedProblem).order_by(desc(FetchedProblem.created_utc)).limit(limit).all()
	
	def create_problem(self, problem: FetchedProblem) -> FetchedProblem:
		"""Create a new problem"""
		try:
			self.db.add(problem)
			self.db.commit()
			self.db.refresh(problem)
			return problem
		except Exception as e:
			self.db.rollback()
			raise
	
	def update_problem(self, problem: FetchedProblem) -> FetchedProblem:
		"""Update an existing problem"""
		try:
			self.db.commit()
			self.db.refresh(problem)
			return problem
		except Exception as e:
			self.db.rollback()
			raise
	
	def get_problems_by_category(self, category: str, limit: int = 50) -> List[FetchedProblem]:
		"""Get problems filtered by category"""
		return self.db.query(FetchedProblem).filter(
			FetchedProblem.category == category
		).order_by(desc(FetchedProblem.created_utc)).limit(limit).all()
	
	def get_problems_by_subreddit(self, subreddit: str, limit: int = 50) -> List[FetchedProblem]:
		"""Get problems from a specific subreddit"""
		return self.db.query(FetchedProblem).filter(
			FetchedProblem.subreddit == subreddit
		).order_by(desc(FetchedProblem.created_utc)).limit(limit).all()
	
	def search_problems(self, query: str, limit: int = 50) -> List[FetchedProblem]:
		"""Search problems by title and description"""
		search_term = f"%{query}%"
		return self.db.query(FetchedProblem).filter(
			(FetchedProblem.title.ilike(search_term)) | 
			(FetchedProblem.description.ilike(search_term))
		).order_by(desc(FetchedProblem.created_utc)).limit(limit).all()
	
	def get_category_stats(self) -> dict:
		"""Get statistics about problem categories"""
		stats = self.db.query(
			FetchedProblem.category,
			func.count(FetchedProblem.id).label('count')
		).group_by(FetchedProblem.category).all()
		
		return {category: count for category, count in stats}
	
	def get_subreddit_stats(self) -> dict:
		"""Get statistics about subreddits"""
		stats = self.db.query(
			FetchedProblem.subreddit,
			func.count(FetchedProblem.id).label('count')
		).group_by(FetchedProblem.subreddit).all()
		
		return {subreddit: count for subreddit, count in stats}


# Legacy functions for backward compatibility
def create_problem(db: Session, data: ProblemCreate, embedding: str | None = None) -> Problem:
	obj = Problem(
		title=data.title,
		description=data.description,
		category=data.category,
		embedding=embedding,
	)
	db.add(obj)
	db.commit()
	db.refresh(obj)
	return obj


def list_problems(db: Session, skip: int = 0, limit: int = 50) -> List[Problem]:
	return db.query(Problem).offset(skip).limit(limit).all()


def get_problem(db: Session, problem_id: int) -> Optional[Problem]:
	return db.query(Problem).filter(Problem.id == problem_id).first()


def delete_problem(db: Session, problem_id: int) -> bool:
	obj = get_problem(db, problem_id)
	if not obj:
		return False
	db.delete(obj)
	db.commit()
	return True
