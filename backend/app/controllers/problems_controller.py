from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..models.schemas import ProblemCreate, ProblemRead
from ..services import problem_service
from ..core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/problems", tags=["problems"])


@router.post("/", response_model=ProblemRead, summary="Create a problem with AI categorization + embedding")
def create_problem(data: ProblemCreate, db: Session = Depends(get_db)):
	return problem_service.create(db, data)


@router.get("/", response_model=List[ProblemRead])
def list_problems(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
	return problem_service.list_all(db, skip, limit)


@router.get("/{problem_id}", response_model=ProblemRead)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
	obj = problem_service.get(db, problem_id)
	if not obj:
		raise HTTPException(status_code=404, detail="Problem not found")
	return obj


@router.delete("/{problem_id}")
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
	ok = problem_service.delete(db, problem_id)
	if not ok:
		raise HTTPException(status_code=404, detail="Problem not found")
	return {"ok": True}
